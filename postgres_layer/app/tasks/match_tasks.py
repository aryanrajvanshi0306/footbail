"""Celery tasks — Pre-Match Brief, Match Story, recurring fixtures, reminders."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid as uuidlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import desc, select

from app.celery_app import celery_app

log = logging.getLogger("footbail.tasks")


def _run_async(coro):
    """Run an async coroutine inside a Celery sync task."""
    return asyncio.get_event_loop().run_until_complete(coro) if asyncio.get_event_loop().is_running() else asyncio.run(coro)


# ───────────────────────── PRE-MATCH BRIEF ─────────────────────────
@celery_app.task(name="app.tasks.match_tasks.generate_pre_match_brief", bind=True, max_retries=2)
def generate_pre_match_brief(self, match_id: str) -> dict:
    return _run_async(_generate_pre_match_brief_async(match_id))


async def _generate_pre_match_brief_async(match_id: str) -> dict:
    from scipy.stats import poisson  # type: ignore
    from app.cache.client import init_cache, get_cache
    from app.cache.keys import MATCH
    from app.db import SessionLocal
    from app.models.match import Match, MatchPlayer, MatchPlayerStat
    from app.services.ai_client import gpt_4o_mini  # type: ignore[attr-defined]

    try:
        cache = get_cache()
    except RuntimeError:
        cache = await init_cache()

    async with SessionLocal() as db:
        m = (await db.execute(select(Match).where(Match.id == uuidlib.UUID(match_id)))).scalar_one_or_none()
        if not m:
            return {"error": "match_not_found"}

        # Last-5 team performances → simple xG approximation via goals scored/conceded
        async def team_form(club_name: str) -> dict:
            rows = (await db.execute(
                select(Match)
                .where((Match.home_team_name == club_name) | (Match.away_team_name == club_name))
                .where(Match.status == "complete")
                .order_by(desc(Match.scheduled_at)).limit(5)
            )).scalars().all()
            scored = []; conceded = []; results: list[str] = []
            for r in rows:
                if r.home_team_name == club_name:
                    scored.append(r.score_home); conceded.append(r.score_away)
                    results.append("W" if r.score_home > r.score_away else "L" if r.score_home < r.score_away else "D")
                else:
                    scored.append(r.score_away); conceded.append(r.score_home)
                    results.append("W" if r.score_away > r.score_home else "L" if r.score_away < r.score_home else "D")
            avg_s = sum(scored)/len(scored) if scored else 1.2
            avg_c = sum(conceded)/len(conceded) if conceded else 1.2
            return {"results": results, "avg_scored": avg_s, "avg_conceded": avg_c}

        home_f = await team_form(m.home_team_name)
        away_f = await team_form(m.away_team_name)

        lambda_home = (home_f["avg_scored"] + 0.1) / max(0.5, away_f["avg_conceded"])
        lambda_away = (away_f["avg_scored"] + 0.1) / max(0.5, home_f["avg_conceded"])

        # Probability of >= 1 goal as proxy for win lean (simplified)
        p_home_scores = float(1 - poisson.cdf(0, lambda_home))
        p_away_scores = float(1 - poisson.cdf(0, lambda_away))
        total = p_home_scores + p_away_scores + 0.4
        home_pct = max(15, min(70, round(p_home_scores / total * 100)))
        away_pct = max(15, min(70, round(p_away_scores / total * 100)))
        draw_pct = max(5, 100 - home_pct - away_pct)

        # Per-player tactical role card (max 50 words each) via GPT-4o-mini
        players = (await db.execute(select(MatchPlayer).where(MatchPlayer.match_id == m.id))).scalars().all()
        role_cards: dict[str, dict] = {}
        for p in players[:10]:
            try:
                tip = await gpt_4o_mini(
                    f"Match: {m.home_team_name} vs {m.away_team_name}. "
                    f"Player on side {p.side}, position {p.position_played or 'CM'}. "
                    "Write a 50-word tactical instruction. No filler. No emojis.",
                    timeout=10,
                )
            except Exception:
                tip = f"Stay disciplined. Track runs from the half-spaces and recycle through {p.position_played or 'midfield'}."
            role_cards[str(p.user_id)] = {"position": p.position_played, "instruction": tip[:300]}

        payload = {
            "match_id": match_id,
            "team_form": {"home": home_f, "away": away_f},
            "head_to_head": [],   # populated by separate H2H aggregator (future)
            "win_probability": {"home_pct": home_pct, "draw_pct": draw_pct, "away_pct": away_pct,
                                "lambda_home": round(lambda_home, 2), "lambda_away": round(lambda_away, 2)},
            "player_form_timelines": {},  # filled per-user at fetch time
            "key_matchups": [],
            "tactical_role_card": role_cards,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        await cache.set_json(MATCH.BRIEF.format(match_id=match_id), payload, ttl=MATCH.BRIEF_TTL)
        return payload


# ───────────────────────── MATCH STORY ─────────────────────────
@celery_app.task(name="app.tasks.match_tasks.generate_match_story", bind=True, max_retries=2)
def generate_match_story(self, match_id: str) -> dict:
    return _run_async(_generate_match_story_async(match_id))


async def _generate_match_story_async(match_id: str) -> dict:
    from app.cache.client import init_cache, get_cache
    from app.db import SessionLocal
    from app.models.match import Match, MatchEvent
    from app.models.social import SocialPost
    from app.services.ai_client import gpt_4o_mini  # type: ignore[attr-defined]

    try:
        cache = get_cache()
    except RuntimeError:
        cache = await init_cache()

    async with SessionLocal() as db:
        m = (await db.execute(select(Match).where(Match.id == uuidlib.UUID(match_id)))).scalar_one_or_none()
        if not m:
            return {"error": "match_not_found"}
        events = (await db.execute(
            select(MatchEvent).where(MatchEvent.match_id == m.id).order_by(MatchEvent.minute)
        )).scalars().all()

        # CLUTCH DETECTOR (exact criteria)
        moments: list[dict] = []
        home_score = 0; away_score = 0
        for ev in events:
            if ev.type == "goal":
                if ev.side == "home": home_score += 1
                else: away_score += 1
            tied = home_score == away_score
            if ev.type == "goal":
                trailing = (ev.side == "home" and home_score - 1 < away_score) or (ev.side == "away" and away_score - 1 < home_score)
                if (ev.minute or 0) >= 75 and (tied or trailing):
                    moments.append(_moment(ev, "goal", clutch=True))
                else:
                    moments.append(_moment(ev, "goal", clutch=False))
            elif ev.type == "save":
                if (ev.minute or 0) >= 75 and (tied or _other_winning(ev, home_score, away_score)):
                    moments.append(_moment(ev, "save", clutch=True))
                else:
                    moments.append(_moment(ev, "save", clutch=False))
            elif ev.type == "red_card" or ev.type == "yellow_card":
                moments.append(_moment(ev, "card", clutch=False))
            elif ev.type == "foul":
                if (ev.minute or 0) >= 70 and not tied:
                    moments.append(_moment(ev, "error", clutch=True))

        # Rank: clutch > goals > saves > errors > cards. Top 5–8.
        weights = {"goal": 4, "save": 3, "error": 2, "card": 1}
        moments.sort(key=lambda x: (x["is_clutch"], weights.get(x["type"], 0)), reverse=True)
        moments = moments[:8]

        # AI captions
        for mom in moments:
            try:
                cap = await gpt_4o_mini(
                    f"Write a 10-word dramatic football caption for: {mom['type']} at minute {mom.get('minute')}. No filler.",
                    timeout=8,
                )
                mom["caption"] = cap.strip()[:120]
            except Exception:
                mom["caption"] = f"Minute {mom.get('minute')} — {mom['type'].upper()}"

        story = {
            "match_id": match_id,
            "match_title": f"{m.home_team_name} vs {m.away_team_name}",
            "result": f"{m.score_home}–{m.score_away}",
            "moments": moments,
            "motm": None,  # populated by finalise_motm
            "share_text": f"{m.home_team_name} {m.score_home}–{m.score_away} {m.away_team_name} · footbAIl",
            "share_url": f"/matches/{match_id}/story",
        }
        await cache.set_json(f"story:{match_id}", story, ttl=86400)

        # Persist as social post
        from app.models.social import SocialPost as _SP  # local re-import for safety
        db.add(_SP(
            user_id=m.creator_id, post_type="match_recap",
            content=story["share_text"], match_id=m.id,
            media_urls=[], reaction_counts={},
        ))
        await db.commit()
        return story


def _moment(ev, kind: str, *, clutch: bool) -> dict:
    return {
        "slide_index": 0,
        "type": kind,
        "timestamp_ms": (ev.minute or 0) * 60_000,
        "minute": ev.minute,
        "player_id": str(ev.primary_user_id) if ev.primary_user_id else None,
        "player_name": None,
        "player_avatar_url": None,
        "caption": "",
        "clip_id": None,
        "thumbnail_url": None,
        "is_clutch": clutch,
        "emoji": {"goal": "⚽", "save": "🧤", "card": "🟨", "error": "❌"}.get(kind, "•"),
    }


def _other_winning(ev, home_score: int, away_score: int) -> bool:
    return (ev.side == "home" and away_score > home_score) or (ev.side == "away" and home_score > away_score)


# ───────────────────────── MOTM + IMPACT ─────────────────────────
@celery_app.task(name="app.tasks.match_tasks.finalise_motm")
def finalise_motm(match_id: str) -> dict:
    """Reads MOTM votes from Redis and writes motm flag to player_match_ratings."""
    return _run_async(_finalise_motm_async(match_id))


async def _finalise_motm_async(match_id: str) -> dict:
    from app.cache.client import init_cache, get_cache
    from app.db import SessionLocal
    from app.models.player_stats import PlayerMatchRating

    try:
        cache = get_cache()
    except RuntimeError:
        cache = await init_cache()
    tally = await cache.zrevrange_withscores(f"motm:tally:{match_id}", 0, 0)
    if not tally:
        return {"motm": None}
    winner_id, _ = tally[0]
    async with SessionLocal() as db:
        rating = (await db.execute(select(PlayerMatchRating).where(
            PlayerMatchRating.match_id == uuidlib.UUID(match_id),
            PlayerMatchRating.user_id == uuidlib.UUID(winner_id),
        ))).scalar_one_or_none()
        if rating:
            rating.is_motm = True
            await db.commit()
    return {"motm": winner_id}


@celery_app.task(name="app.tasks.match_tasks.compute_match_impact")
def compute_match_impact(match_id: str) -> dict:
    """Stub: writes a Match Impact Index per player (Module 05). Real impl uses video pipeline."""
    return {"match_id": match_id, "status": "queued"}


@celery_app.task(name="app.tasks.match_tasks.compute_oyp_profile")
def compute_oyp_profile(user_id: str) -> dict:
    """Stub: rebuilds OYP Play Style DNA. Real impl reads last-N matches and calls GPT-4o."""
    return {"user_id": user_id, "status": "queued"}


# ───────────────────────── BEAT TASKS ─────────────────────────
@celery_app.task(name="app.tasks.match_tasks.create_recurring_match_instances")
def create_recurring_match_instances() -> dict:
    """Daily 00:30 UTC (06:00 IST). For each active recurring match where next = today + 7."""
    return _run_async(_create_recurring_async())


async def _create_recurring_async() -> dict:
    from app.db import SessionLocal
    from app.models.match import Match, RecurringMatch

    today_plus_7 = (datetime.now(timezone.utc) + timedelta(days=7)).date()
    created = 0
    async with SessionLocal() as db:
        rows = (await db.execute(
            select(RecurringMatch).where(RecurringMatch.is_active.is_(True))
        )).scalars().all()
        for r in rows:
            if r.next_run_at is None or r.next_run_at.date() != today_plus_7:
                continue
            # Slot availability check (DB, not cache)
            existing = (await db.execute(
                select(Match).where(Match.turf_id == r.turf_id, Match.scheduled_at == r.next_run_at)
            )).scalar_one_or_none()
            if existing: continue
            db.add(Match(
                home_team_name=r.title, away_team_name="TBD",
                turf_id=r.turf_id, creator_id=r.creator_id,
                scheduled_at=r.next_run_at, format=r.format,
                home_club_id=r.club_id, status="scheduled",
            ))
            r.next_run_at += timedelta(days=7)
            created += 1
            # Schedule pre-match brief 1hr before
            celery_app.send_task(
                "app.tasks.match_tasks.generate_pre_match_brief",
                args=[str(r.id)],
                eta=r.next_run_at - timedelta(hours=1),
            )
        await db.commit()
    return {"created": created}


@celery_app.task(name="app.tasks.match_tasks.send_match_reminders_24h")
def send_match_reminders_24h() -> dict:
    return _run_async(_send_reminders(24))


@celery_app.task(name="app.tasks.match_tasks.send_match_reminders_2h")
def send_match_reminders_2h() -> dict:
    return _run_async(_send_reminders(2))


async def _send_reminders(hours: int) -> dict:
    from app.db import SessionLocal
    from app.models.match import Match, MatchPlayer
    from app.models.notification import WhatsappMessageLog

    target = datetime.now(timezone.utc) + timedelta(hours=hours)
    window = timedelta(minutes=30 if hours == 24 else 15)
    sent = 0
    template = "footbail_match_reminder_24h" if hours == 24 else "footbail_match_reminder_2h"
    async with SessionLocal() as db:
        rows = (await db.execute(
            select(Match).where(
                Match.scheduled_at.between(target - window, target + window),
                Match.status == "scheduled",
            )
        )).scalars().all()
        for m in rows:
            players = (await db.execute(select(MatchPlayer).where(MatchPlayer.match_id == m.id))).scalars().all()
            for p in players:
                # Resolve user phone (best-effort)
                from app.models.user import User as _U
                u = (await db.execute(select(_U).where(_U.id == p.user_id))).scalar_one_or_none()
                if not u: continue
                db.add(WhatsappMessageLog(
                    user_id=u.id, phone=u.phone, template_name=template,
                    template_params=[m.home_team_name, m.away_team_name, str(m.scheduled_at)],
                ))
                sent += 1
            if hours == 24:
                celery_app.send_task("app.tasks.match_tasks.generate_pre_match_brief", args=[str(m.id)])
        await db.commit()
    return {"sent": sent, "hours": hours}
