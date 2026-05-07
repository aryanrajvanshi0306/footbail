"""FastAPI auth dependencies — cache-first user load, role/membership/flag gates."""
from __future__ import annotations

import json
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_token
from app.cache.client import CacheClient, get_cache
from app.cache.keys import USER, AUTH
from app.db import get_db
from app.models.user import User


async def _bearer(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    return authorization[7:].strip()


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
) -> User:
    token = await _bearer(authorization)
    try:
        payload = decode_token(token, expected_type="access")
    except ValueError as e:
        raise HTTPException(401, str(e))

    jti = payload.get("jti")
    if jti and await cache.exists(AUTH.REFRESH_BLOCKLIST.format(jti=jti)):
        raise HTTPException(401, "Token revoked")

    user_id = payload["sub"]
    cache_key = USER.PROFILE.format(user_id=user_id)

    cached = await cache.get_json(cache_key)
    if cached is None:
        user = (await db.execute(select(User).where(User.id == UUID(user_id)))).scalar_one_or_none()
        if not user:
            raise HTTPException(401, "User not found")
        if not user.is_active or user.deleted_at is not None:
            raise HTTPException(403, "Account deactivated")
        await cache.set_json(cache_key, {
            "id": str(user.id), "phone": user.phone, "role": user.role,
            "name": user.name, "city": user.city, "is_active": user.is_active,
        }, ttl=USER.PROFILE_TTL)
        return user

    if not cached.get("is_active"):
        raise HTTPException(403, "Account deactivated")
    user = (await db.execute(select(User).where(User.id == UUID(user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found")
    return user


def require_role(*roles: str):
    async def _gate(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, f"Requires role: {' or '.join(roles)}")
        return user
    return _gate


def require_membership(*tiers: str):
    async def _gate(
        user: User = Depends(get_current_user),
        cache: CacheClient = Depends(get_cache),
    ) -> User:
        # Read tier from active membership pass cache mirror; default 'free'
        tier_raw = await cache.get_str(f"user:membership:{user.id}")
        tier = tier_raw or "free"
        if tier not in tiers:
            raise HTTPException(403, {"error": "upgrade_required", "current_tier": tier, "required": list(tiers)})
        return user
    return _gate


def require_feature_flag(key: str):
    async def _gate(
        authorization: Optional[str] = Header(default=None),
        user: User = Depends(get_current_user),
    ) -> User:
        # Read from JWT payload only — zero Redis calls
        token = await _bearer(authorization)
        try:
            payload = decode_token(token, expected_type="access")
        except ValueError as e:
            raise HTTPException(401, str(e))
        flags = payload.get("feature_flags") or {}
        flag_val = flags.get(key)
        truthy = bool(flag_val) if not isinstance(flag_val, str) else flag_val not in ("", "off", "false", "disabled")
        if not truthy:
            raise HTTPException(403, {"error": "feature_disabled", "flag": key, "current_value": flag_val})
        return user
    return _gate


async def optional_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
) -> Optional[User]:
    if not authorization:
        return None
    try:
        return await get_current_user(authorization=authorization, db=db, cache=cache)
    except HTTPException:
        return None


async def get_feature_flags(authorization: Optional[str] = Header(default=None)) -> dict:
    """Pure JWT-payload read — never hits Redis. Used by feature-aware UI endpoints."""
    if not authorization:
        return {}
    try:
        token = await _bearer(authorization)
        payload = decode_token(token, expected_type="access")
        return dict(payload.get("feature_flags") or {})
    except (ValueError, HTTPException):
        return {}
