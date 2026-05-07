"""/v2/matches/{id}/pre-match-brief — Module 03 Pre-Match Intelligence."""
from __future__ import annotations

import uuid as uuidlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_feature_flag
from app.cache.client import CacheClient, get_cache
from app.cache.keys import MATCH
from app.db import get_db
from app.models.match import Match, MatchPlayer
from app.models.user import User

router = APIRouter(prefix="/v2/matches", tags=["pre-match"])


@router.get("/{match_id}/pre-match-brief")
async def pre_match_brief(
    match_id: uuidlib.UUID,
    user: User = Depends(require_feature_flag("pre_match_intelligence")),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    m = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not m: raise HTTPException(404, "Match not found")

    # Confirmed participant only
    is_player = (await db.execute(
        select(MatchPlayer).where(MatchPlayer.match_id == match_id, MatchPlayer.user_id == user.id)
    )).scalar_one_or_none()
    if not is_player and m.creator_id != user.id:
        raise HTTPException(403, "Confirmed participants only")

    # Available within 24hrs of scheduled_at
    delta = m.scheduled_at - datetime.now(timezone.utc)
    if delta > timedelta(hours=24):
        raise HTTPException(403, {"error": "too_early", "available_in_hours": int(delta.total_seconds() // 3600)})

    cached = await cache.get_json(MATCH.BRIEF.format(match_id=match_id))
    if cached: return cached
    return {"status": "computing", "match_id": str(match_id),
            "message": "AI brief is being generated — refresh in a moment."}
