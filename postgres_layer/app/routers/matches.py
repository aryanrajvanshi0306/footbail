"""/v2/matches — 10 routes: list, detail, last-minute, near-me, lineup, score,
motm-vote, live-event, ticket, live-state."""
from __future__ import annotations

import json
import math
import uuid as uuidlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.cache.client import CacheClient, get_cache
from app.cache.keys import MATCH, PUBSUB
from app.celery_app import celery_app
from app.db import get_db
from app.models.match import (
    Booking, Match, MatchEvent, MatchLineup, MatchPlayer,
)
from app.models.player_stats import PlayerMatchRating
from app.models.turf import Turf
from app.models.user import User

router = APIRouter(prefix="/v2/matches", tags=["matches"])


# ─────── Schemas ───────
class LineupSlot(BaseModel):
    user_id: uuidlib.UUID
    position: str
    jersey: Optional[int] = None
    is_starter: bool = True
    team: str = Field(pattern="^(home|away)$")

class LineupIn(BaseModel):
    formation: str = "4-3-3"
    players: list[LineupSlot]

class ScoreIn(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)

class MotmVoteIn(BaseModel):
    voted_for_user_id: uuidlib.UUID

class LiveEventIn(BaseModel):
    type: str = Field(pattern="^(goal|card|save|foul|substitution)$")
    team: str = Field(pattern="^(home|away)$")
    player_id: Optional[uuidlib.UUID] = None
    minute: int = Field(ge=0, le=200)
    note: Optional[str] = None


# ─────── Helpers ───────
def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lng2 - lng1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * r * math.asin(math.sqrt(a))


# ─────── Routes ───────
@router.get("/")
async def list_user_matches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User's upcoming + recent matches (calendar data)."""
    rows = (await db.execute(
        select(Match).join(MatchPlayer, MatchPlayer.match_id == Match.id)
        .where(MatchPlayer.user_id == user.id, Match.deleted_at.is_(None))
        .order_by(desc(Match.scheduled_at)).limit(60)
    )).scalars().all()
    return [_match_summary(m) for m in rows]


@router.get("/last-minute")
async def last_minute(
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Open matches starting < 3hrs with spots remaining."""
    horizon = datetime.now(timezone.utc) + timedelta(hours=3)
    stmt = select(Match).where(
        Match.status == "scheduled",
        Match.scheduled_at <= horizon,
        Match.scheduled_at >= datetime.now(timezone.utc),
        Match.deleted_at.is_(None),
    )
    if city:
        stmt = stmt.join(Turf, Turf.id == Match.turf_id).where(Turf.city == city)
    matches = (await db.execute(stmt.order_by(Match.scheduled_at).limit(40))).scalars().all()
    return [_match_summary(m) for m in matches]


@router.get("/near-me")
async def near_me(
    city: Optional[str] = None,
    format: Optional[str] = None,
    skill_bracket: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = Query(10, ge=0.5, le=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Match, Turf).join(Turf, Turf.id == Match.turf_id).where(Match.status == "scheduled")
    if city: stmt = stmt.where(Turf.city == city)
    if format: stmt = stmt.where(Match.format == format)
    if skill_bracket: stmt = stmt.where(Match.skill_bracket == skill_bracket)
    rows = (await db.execute(stmt.limit(200))).all()
    out: list[dict] = []
    for m, t in rows:
        d_km: Optional[float] = None
        if lat is not None and lng is not None and t.lat is not None and t.lng is not None:
            d_km = _haversine_km(lat, lng, float(t.lat), float(t.lng))
            if d_km > radius_km:
                continue
        item = _match_summary(m)
        item["distance_km"] = round(d_km, 2) if d_km is not None else None
        out.append(item)
    out.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else 1e9))
    return out


@router.get("/{match_id}")
async def get_match(
    match_id: uuidlib.UUID,
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    cached = await cache.get_json(MATCH.DETAIL.format(match_id=match_id))
    if cached: return cached
    m = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not m: raise HTTPException(404, "Match not found")
    lineups = (await db.execute(select(MatchLineup).where(MatchLineup.match_id == match_id))).scalars().all()
    players = (await db.execute(select(MatchPlayer).where(MatchPlayer.match_id == match_id))).scalars().all()
    payload = {
        **_match_summary(m),
        "referee_id": str(m.referee_id) if m.referee_id else None,
        "lineups": [{"side": l.side, "formation": l.formation, "positions": l.positions, "bench": l.bench, "locked": l.locked} for l in lineups],
        "attendance": [{"user_id": str(p.user_id), "side": p.side, "jersey": p.jersey_number} for p in players],
        "broadcast_active": m.broadcast_active,
        "camera_recording_url": m.camera_recording_url,
    }
    await cache.set_json(MATCH.DETAIL.format(match_id=match_id), payload, ttl=MATCH.DETAIL_TTL)
    return payload


@router.post("/{match_id}/lineup")
async def submit_lineup(
    match_id: uuidlib.UUID,
    body: LineupIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    m = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not m: raise HTTPException(404, "Match not found")
    if m.creator_id != user.id and user.role not in {"admin", "team_admin"}:
        raise HTTPException(403, "Only match creator or team admin can submit lineup")
    side = body.players[0].team if body.players else "home"
    existing = (await db.execute(select(MatchLineup).where(MatchLineup.match_id == match_id, MatchLineup.side == side))).scalar_one_or_none()
    positions = [{"user_id": str(p.user_id), "position": p.position, "jersey": p.jersey, "is_starter": p.is_starter} for p in body.players]
    if existing:
        existing.formation = body.formation; existing.positions = positions
    else:
        db.add(MatchLineup(match_id=match_id, side=side, formation=body.formation, positions=positions, set_by=user.id))
    if m.status == "scheduled":
        m.status = "scheduled"  # remain scheduled; lineup_submitted is a sub-flag in PRD
    await db.commit()
    await cache.delete(MATCH.DETAIL.format(match_id=match_id))
    return {"ok": True, "side": side, "formation": body.formation}


@router.post("/{match_id}/score")
async def submit_score(
    match_id: uuidlib.UUID,
    body: ScoreIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    m = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not m: raise HTTPException(404, "Match not found")
    m.score_home = body.home_score; m.score_away = body.away_score
    m.status = "complete"; m.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await cache.delete(MATCH.DETAIL.format(match_id=match_id))
    # Dispatch post-match Celery tasks (chained downstream)
    celery_app.send_task("app.tasks.match_tasks.finalise_motm", args=[str(match_id)])
    celery_app.send_task("app.tasks.match_tasks.compute_match_impact", args=[str(match_id)])
    celery_app.send_task("app.tasks.match_tasks.generate_match_story", args=[str(match_id)])
    return {"ok": True, "status": "complete"}


@router.post("/{match_id}/motm-vote")
async def motm_vote(
    match_id: uuidlib.UUID,
    body: MotmVoteIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    is_player = (await db.execute(select(MatchPlayer).where(MatchPlayer.match_id == match_id, MatchPlayer.user_id == user.id))).scalar_one_or_none()
    if not is_player:
        raise HTTPException(403, "Only match players can vote")
    vote_key = f"motm:vote:{match_id}:{user.id}"
    if await cache.exists(vote_key):
        raise HTTPException(409, "Already voted")
    await cache.set_str(vote_key, str(body.voted_for_user_id), ttl=24 * 60 * 60)
    await cache.zincrby(f"motm:tally:{match_id}", str(body.voted_for_user_id), 1.0)
    return {"ok": True}


@router.post("/{match_id}/live-event")
async def live_event(
    match_id: uuidlib.UUID,
    body: LiveEventIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    m = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not m: raise HTTPException(404, "Match not found")
    if user.role not in {"admin", "referee"} and m.creator_id != user.id:
        raise HTTPException(403, "Not authorised to log events")

    ev = MatchEvent(
        match_id=match_id, type=_normalise_event_type(body.type), minute=body.minute,
        side=body.team, primary_user_id=body.player_id, notes=body.note,
        auto_detected=False, logged_by=user.id,
    )
    db.add(ev); await db.flush()

    # Score increment on goal
    if body.type == "goal":
        if body.team == "home": m.score_home += 1
        else: m.score_away += 1

    # Momentum recalc
    deltas = {"goal": 15, "save": 8, "foul": -3, "card": -5, "substitution": 0}
    delta = deltas.get(body.type, 0)
    if body.team == "away": delta = -delta
    cur_raw = await cache.get_str(f"match:momentum:{match_id}") or "50"
    momentum = max(0, min(100, int(cur_raw) + delta))
    await cache.set_str(f"match:momentum:{match_id}", str(momentum), ttl=MATCH.LIVE_STATE_TTL)

    # Append to events list (LPUSH capped at 200)
    payload = {"id": str(ev.id), "type": ev.type, "team": body.team,
               "player_id": str(body.player_id) if body.player_id else None,
               "minute": body.minute, "note": body.note,
               "ts": datetime.now(timezone.utc).isoformat()}
    await cache.lpush(MATCH.EVENTS_LIST.format(match_id=match_id),
                      json.dumps(payload, separators=(",", ":")),
                      ttl=MATCH.EVENTS_LIST_TTL, max_len=200)

    # Pub/sub for WS gateways
    await cache.publish(PUBSUB.MATCH_LIVE.format(match_id=match_id),
                        {"event": payload, "score": {"home": m.score_home, "away": m.score_away},
                         "momentum_score": momentum})
    await db.commit()
    return {"ok": True, "momentum_score": momentum}


@router.get("/{match_id}/ticket")
async def get_ticket(
    match_id: uuidlib.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = (await db.execute(
        select(Booking, Match, Turf)
        .join(Match, Match.id == Booking.match_id)
        .join(Turf, Turf.id == Match.turf_id)
        .where(Booking.match_id == match_id, Booking.user_id == user.id, Booking.payment_status.in_(["paid", "wallet_paid"]))
    )).first()
    if not booking:
        raise HTTPException(403, "No paid booking for this match")
    b, m, t = booking
    ist = (m.scheduled_at + timedelta(hours=5, minutes=30)).isoformat()
    return {
        "qr_token": b.qr_token or str(b.id),
        "turf_name": t.name, "address": t.address,
        "scheduled_at_ist": ist, "format": m.format,
        "match_id": str(m.id),
    }


@router.get("/{match_id}/live-state")
async def live_state(
    match_id: uuidlib.UUID,
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    cached = await cache.get_json(f"match:live_state:{match_id}")
    if cached: return cached
    m = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not m: raise HTTPException(404, "Match not found")
    momentum_raw = await cache.get_str(f"match:momentum:{match_id}")
    momentum = int(momentum_raw) if momentum_raw and momentum_raw.isdigit() else 50
    recent_raw = await cache.lrange(MATCH.EVENTS_LIST.format(match_id=match_id), 0, 4)
    recent = [json.loads(r) for r in recent_raw]
    elapsed = 0
    if m.started_at:
        elapsed = int((datetime.now(timezone.utc) - m.started_at).total_seconds() // 60)
    tip_raw = await cache.get_json(f"match:ai_tip:{match_id}")
    payload = {
        "score": {"home": m.score_home, "away": m.score_away},
        "status": m.status, "momentum_score": momentum,
        "elapsed_minutes": elapsed,
        "recent_events": recent,
        "live_tip": tip_raw,
    }
    await cache.set_json(f"match:live_state:{match_id}", payload, ttl=30)
    return payload


# ─────── Internals ───────
def _normalise_event_type(t: str) -> str:
    if t == "card": return "yellow_card"
    return t


def _match_summary(m: Match) -> dict:
    return {
        "id": str(m.id),
        "home_team": m.home_team_name, "away_team": m.away_team_name,
        "turf_id": str(m.turf_id),
        "scheduled_at": m.scheduled_at.isoformat(),
        "scheduled_at_ist": (m.scheduled_at + timedelta(hours=5, minutes=30)).isoformat(),
        "status": m.status, "format": m.format, "skill_bracket": m.skill_bracket,
        "score": {"home": m.score_home, "away": m.score_away},
    }
