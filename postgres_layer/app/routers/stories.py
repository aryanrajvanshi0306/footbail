"""/v2/matches/{id}/story — Match Story Mode (Module 07)."""
from __future__ import annotations

import uuid as uuidlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_feature_flag
from app.cache.client import CacheClient, get_cache
from app.db import get_db
from app.models.match import Match
from app.models.user import User

router = APIRouter(prefix="/v2/matches", tags=["stories"])


@router.get("/{match_id}/story")
async def get_match_story(
    match_id: uuidlib.UUID,
    user: User = Depends(require_feature_flag("story_mode")),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    m = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not m: raise HTTPException(404, "Match not found")
    if m.status != "complete":
        raise HTTPException(409, "Story available after match completion")

    cached = await cache.get_json(f"story:{match_id}")
    if cached: return cached
    return {"status": "computing", "match_id": str(match_id),
            "message": "AI is composing your match story…"}
