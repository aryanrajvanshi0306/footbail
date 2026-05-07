"""/v2/oyp — One Year Player profile (Play Style DNA)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.cache.client import CacheClient, get_cache
from app.cache.keys import USER
from app.celery_app import celery_app
from app.db import get_db
from app.models.ai_data import OypProfile
from app.models.user import User

router = APIRouter(prefix="/v2/oyp", tags=["oyp"])


@router.get("/my-profile")
async def my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    cache_key = USER.OYP_PROFILE.format(user_id=user.id)
    cached = await cache.get_json(cache_key)
    if cached:
        return cached
    oyp = (await db.execute(select(OypProfile).where(OypProfile.user_id == user.id))).scalar_one_or_none()
    if not oyp:
        return {"status": "not_computed", "user_id": str(user.id)}
    payload = {
        "user_id": str(user.id),
        "archetype": oyp.archetype_label,
        "style_dna": oyp.style_dna,
        "top_strengths": oyp.top_strengths,
        "development_areas": oyp.development_areas,
        "confidence": oyp.confidence,
        "matches_analyzed": oyp.matches_analyzed,
        "last_generated_at": oyp.last_generated_at.isoformat() if oyp.last_generated_at else None,
    }
    await cache.set_json(cache_key, payload, ttl=USER.OYP_PROFILE_TTL)
    return payload


@router.post("/recompute")
async def recompute(user: User = Depends(get_current_user)):
    # NEVER compute inline — dispatch to Celery worker
    celery_app.send_task("app.tasks.match_tasks.compute_oyp_profile", args=[str(user.id)])
    return {"status": "computing"}
