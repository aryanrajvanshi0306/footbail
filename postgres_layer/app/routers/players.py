"""/v2/players — 10 routes: dashboard, profile, search, stats, form-timeline,
play-style, impact-summary, profile patch, lfg-activate, lfg-deactivate."""
from __future__ import annotations

import time
import uuid as uuidlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, optional_user, require_role
from app.cache.client import CacheClient, get_cache
from app.cache.keys import LFG, USER
from app.db import get_db
from app.models.user import PlayerProfile, User
from app.models.match import Match, MatchPlayer, MatchPlayerStat
from app.models.player_stats import (
    PlayerMatchRating, PlayerPerformanceSnapshot,
)
from app.models.gamification import (
    Achievement, PlayerAchievement, PlayerChallenge, Challenge, XpEvent,
)
from app.models.ai_data import MatchImpactScore, OypProfile

router = APIRouter(prefix="/v2/players", tags=["players"])


# ─────── Schemas ───────
class LFGActivateIn(BaseModel):
    format: str = Field(default="5v5")
    note: Optional[str] = None


class ProfilePatchIn(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    avatar_url: Optional[str] = None
    position: Optional[str] = None
    secondary_position: Optional[str] = None
    preferred_foot: Optional[str] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    jersey_number: Optional[int] = None
    skill_bracket: Optional[str] = None


# ─────── Helpers ───────
async def _get_player_profile(db: AsyncSession, user_id) -> Optional[PlayerProfile]:
    return (await db.execute(select(PlayerProfile).where(PlayerProfile.user_id == user_id))).scalar_one_or_none()


def _public_user(user: User, profile: Optional[PlayerProfile]) -> dict:
    return {
        "id": str(user.id), "name": user.name, "city": user.city, "role": user.role,
        "avatar_url": user.avatar_url,
        "position": profile.position if profile else None,
        "card_tier": profile.card_tier if profile else None,
        "overall": profile.overall if profile else None,
    }


# ─────── Routes ───────
@router.get("/dashboard")
async def dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    """Full dashboard payload for the authed player. Cached USER_PROFILE 300s."""
    cache_key = f"dashboard:{user.id}"
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    profile = await _get_player_profile(db, user.id)
    if not profile:
        raise HTTPException(404, "Player profile not found")

    # Form last 10 ratings
    form_rows = (await db.execute(
        select(PlayerMatchRating, Match)
        .join(Match, Match.id == PlayerMatchRating.match_id)
        .where(PlayerMatchRating.user_id == user.id)
        .order_by(desc(Match.scheduled_at))
        .limit(10)
    )).all()
    form_graph = [
        {"match_id": str(r.match_id), "match_date": m.scheduled_at.isoformat(),
         "rating": r.overall_rating, "is_motm": r.is_motm}
        for r, m in form_rows
    ]

    # Season stats aggregate
    season_rows = (await db.execute(
        select(MatchPlayerStat).where(MatchPlayerStat.user_id == user.id)
    )).scalars().all()
    season = {
        "matches": len(season_rows),
        "goals": sum(s.goals for s in season_rows),
        "assists": sum(s.assists for s in season_rows),
        "minutes": sum(s.minutes_played for s in season_rows),
        "clean_sheets": sum(1 for s in season_rows if s.clean_sheet),
    }

    # OYP
    oyp = (await db.execute(select(OypProfile).where(OypProfile.user_id == user.id))).scalar_one_or_none()

    # Achievements
    ach_rows = (await db.execute(
        select(Achievement, PlayerAchievement)
        .join(PlayerAchievement, PlayerAchievement.achievement_id == Achievement.id)
        .where(PlayerAchievement.user_id == user.id)
        .order_by(desc(PlayerAchievement.unlocked_at))
        .limit(6)
    )).all()
    recent_achievements = [
        {"id": str(a.id), "code": a.code, "name": a.name, "rarity": a.rarity,
         "unlocked_at": pa.unlocked_at.isoformat()} for a, pa in ach_rows
    ]

    # Active challenges
    chal_rows = (await db.execute(
        select(Challenge, PlayerChallenge)
        .join(PlayerChallenge, PlayerChallenge.challenge_id == Challenge.id)
        .where(PlayerChallenge.user_id == user.id, PlayerChallenge.status == "active")
        .limit(8)
    )).all()
    active_challenges = [
        {"id": str(c.id), "title": c.title, "type": c.type, "target": c.target,
         "progress": pc.progress, "xp_reward": c.xp_reward}
        for c, pc in chal_rows
    ]

    payload = {
        "profile": _public_user(user, profile),
        "fifa_card": {
            "overall": profile.overall, "position": profile.position,
            "tier": profile.card_tier, "name": user.name,
            "attributes": {"pac": profile.pac, "sho": profile.sho, "pas": profile.pas,
                           "dri": profile.dri, "def": profile.defn, "phy": profile.phy},
        },
        "oyp": {
            "archetype": oyp.archetype_label if oyp else None,
            "confidence": oyp.confidence if oyp else 0,
            "matches_analyzed": oyp.matches_analyzed if oyp else 0,
        } if oyp else None,
        "play_style_dna": (oyp.style_dna if oyp else {}),
        "stats_season": season,
        "form_graph": form_graph,
        "career": {"matches": season["matches"], "goals": season["goals"], "assists": season["assists"]},
        "consistency_score": profile.consistency,
        "xp": profile.xp, "xp_to_next": profile.xp_to_next,
        "streak": profile.streak_days,
        "recent_achievements": recent_achievements,
        "active_challenges": active_challenges,
    }
    await cache.set_json(cache_key, payload, ttl=USER.PROFILE_TTL)
    return payload


@router.get("/search")
async def search_players(
    q: Optional[str] = Query(default=None),
    city: Optional[str] = None,
    position: Optional[str] = None,
    skill_bracket: Optional[str] = None,
    is_lfg: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _: Optional[User] = Depends(optional_user),
):
    stmt = select(User, PlayerProfile).join(PlayerProfile, PlayerProfile.user_id == User.id).where(User.role == "player", User.deleted_at.is_(None))
    if q:
        stmt = stmt.where(User.name.ilike(f"%{q}%"))
    if city:
        stmt = stmt.where(User.city == city)
    if position:
        stmt = stmt.where(PlayerProfile.position == position)
    if skill_bracket:
        stmt = stmt.where(PlayerProfile.skill_bracket == skill_bracket)
    if is_lfg is not None:
        stmt = stmt.where(PlayerProfile.is_looking_for_game == is_lfg)
    stmt = stmt.order_by(desc(PlayerProfile.overall)).limit(50)
    rows = (await db.execute(stmt)).all()
    return [_public_user(u, p) for u, p in rows]


@router.get("/{player_id}")
async def get_player(
    player_id: uuidlib.UUID,
    db: AsyncSession = Depends(get_db),
    me: Optional[User] = Depends(optional_user),
):
    user = (await db.execute(select(User).where(User.id == player_id))).scalar_one_or_none()
    if not user or user.deleted_at is not None:
        raise HTTPException(404, "Player not found")
    profile = await _get_player_profile(db, player_id)
    own = me is not None and me.id == player_id
    base = _public_user(user, profile)
    if own and profile:
        base.update({
            "phone": user.phone, "bio": user.bio,
            "attributes": {"pac": profile.pac, "sho": profile.sho, "pas": profile.pas,
                           "dri": profile.dri, "def": profile.defn, "phy": profile.phy},
            "xp": profile.xp, "xp_to_next": profile.xp_to_next,
            "consistency": profile.consistency, "skill_bracket": profile.skill_bracket,
            "is_looking_for_game": profile.is_looking_for_game,
        })
    return base


@router.get("/{player_id}/stats")
async def player_stats(
    player_id: uuidlib.UUID,
    period: str = Query("season", pattern="^(season|career|last_10|last_30)$"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MatchPlayerStat, Match).join(Match, Match.id == MatchPlayerStat.match_id).where(MatchPlayerStat.user_id == player_id)
    if period == "last_10":
        stmt = stmt.order_by(desc(Match.scheduled_at)).limit(10)
    elif period == "last_30":
        stmt = stmt.where(Match.scheduled_at >= datetime.now(timezone.utc) - timedelta(days=30))
    rows = (await db.execute(stmt)).all()
    if not rows:
        return {"period": period, "matches": 0}
    stats = [s for s, _m in rows]
    profile = await _get_player_profile(db, player_id)
    pos = profile.position if profile else None
    base = {
        "matches": len(stats),
        "goals": sum(s.goals for s in stats),
        "assists": sum(s.assists for s in stats),
        "minutes": sum(s.minutes_played for s in stats),
    }
    if pos == "GK":
        base.update({"saves": sum(s.saves for s in stats), "clean_sheets": sum(1 for s in stats if s.clean_sheet)})
    elif pos in {"CB", "LB", "RB", "CDM"}:
        base.update({"tackles": sum(s.tackles for s in stats), "interceptions": sum(s.interceptions for s in stats)})
    elif pos in {"CM", "CAM", "LM", "RM"}:
        base.update({"key_passes": sum(s.key_passes for s in stats),
                     "passes_completed": sum(s.passes_completed for s in stats),
                     "passes_attempted": sum(s.passes_attempted for s in stats)})
    elif pos in {"LW", "RW", "ST", "CF"}:
        base.update({"shots": sum(s.shots for s in stats), "shots_on_target": sum(s.shots_on_target for s in stats)})
    return {"period": period, "position": pos, **base}


@router.get("/{player_id}/form-timeline")
async def form_timeline(
    player_id: uuidlib.UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (await db.execute(
        select(PlayerMatchRating, Match, MatchPlayerStat, MatchImpactScore)
        .join(Match, Match.id == PlayerMatchRating.match_id)
        .outerjoin(MatchPlayerStat, and_(MatchPlayerStat.match_id == Match.id, MatchPlayerStat.user_id == player_id))
        .outerjoin(MatchImpactScore, and_(MatchImpactScore.match_id == Match.id, MatchImpactScore.user_id == player_id))
        .where(PlayerMatchRating.user_id == player_id, Match.scheduled_at >= since)
        .order_by(desc(Match.scheduled_at))
    )).all()
    return [{
        "match_date": m.scheduled_at.isoformat(),
        "opponent": m.away_team_name if r else None,
        "rating": r.overall_rating, "goals": s.goals if s else 0,
        "assists": s.assists if s else 0,
        "match_impact_index": mi.score if mi else None,
        "is_motm": r.is_motm,
    } for r, m, s, mi in rows]


@router.get("/{player_id}/play-style")
async def play_style(
    player_id: uuidlib.UUID,
    db: AsyncSession = Depends(get_db),
):
    oyp = (await db.execute(select(OypProfile).where(OypProfile.user_id == player_id))).scalar_one_or_none()
    if not oyp:
        return {"label": None, "traits": {}, "archetype": None, "peer_archetype_pct": 0, "computed_at": None}
    return {
        "label": oyp.archetype_label, "traits": oyp.style_dna,
        "archetype": oyp.archetype_label, "peer_archetype_pct": oyp.confidence,
        "computed_at": oyp.last_generated_at.isoformat() if oyp.last_generated_at else None,
    }


@router.get("/{player_id}/impact-summary")
async def impact_summary(
    player_id: uuidlib.UUID,
    period: str = Query("season"),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(MatchImpactScore, Match).join(Match, Match.id == MatchImpactScore.match_id)
        .where(MatchImpactScore.user_id == player_id)
        .order_by(desc(Match.scheduled_at))
    )).all()
    if not rows:
        return {"period": period, "avg_impact_index": 0, "best_match": None, "worst_match": None, "impact_by_match": []}
    impacts = [{"match_id": str(mi.match_id), "score": mi.score,
                "match_date": m.scheduled_at.isoformat()} for mi, m in rows]
    avg = round(sum(i["score"] for i in impacts) / len(impacts))
    best = max(impacts, key=lambda x: x["score"])
    worst = min(impacts, key=lambda x: x["score"])
    return {"period": period, "avg_impact_index": avg, "best_match": best, "worst_match": worst, "impact_by_match": impacts[:30]}


@router.patch("/profile")
async def patch_profile(
    body: ProfilePatchIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    if user.role != "player":
        raise HTTPException(403, "Players only")
    profile = await _get_player_profile(db, user.id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    if body.name: user.name = body.name
    if body.bio is not None: user.bio = body.bio
    if body.city: user.city = body.city
    if body.avatar_url is not None: user.avatar_url = body.avatar_url
    for fld in ("position", "secondary_position", "preferred_foot", "height_cm",
                "weight_kg", "jersey_number", "skill_bracket"):
        v = getattr(body, fld)
        if v is not None:
            setattr(profile, fld, v)
    await db.commit()
    await cache.delete(USER.PROFILE.format(user_id=user.id))
    await cache.delete(f"dashboard:{user.id}")
    return {"ok": True}


@router.post("/lfg-activate")
async def lfg_activate(
    body: LFGActivateIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    if user.role != "player":
        raise HTTPException(403, "Players only")
    profile = await _get_player_profile(db, user.id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    expires_at = datetime.now(timezone.utc) + timedelta(hours=3)
    profile.is_looking_for_game = True
    await db.commit()

    zset_key = f"lfg:players:{user.city}:{body.format}"
    score = expires_at.timestamp()
    await cache.zadd(zset_key, {str(user.id): score}, ttl=4 * 60 * 60)
    await cache.set_str(LFG.USER_ACTIVE.format(user_id=user.id), zset_key, ttl=LFG.USER_ACTIVE_TTL)
    # IST display
    ist_iso = (expires_at + timedelta(hours=5, minutes=30)).isoformat()
    return {"expires_at_ist": ist_iso, "format": body.format, "city": user.city}


@router.post("/lfg-deactivate")
async def lfg_deactivate(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    profile = await _get_player_profile(db, user.id)
    if profile:
        profile.is_looking_for_game = False
        await db.commit()
    zset_key = await cache.get_str(LFG.USER_ACTIVE.format(user_id=user.id))
    if zset_key:
        await cache.zrem(zset_key, str(user.id))
        await cache.delete(LFG.USER_ACTIVE.format(user_id=user.id))
    return {"ok": True}


@router.get("/")
async def upcoming_dashboard_alias(user: User = Depends(get_current_user)):
    """Defensive alias for `/v2/players/` — same as /dashboard but minimal payload."""
    return {"id": str(user.id), "name": user.name, "city": user.city, "role": user.role}
