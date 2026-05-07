"""POST /v2/auth — 6 routes: send-otp, verify-otp, complete-profile, refresh, logout, accept-invite."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import (
    create_access_token, create_refresh_token, create_onboarding_token,
    decode_token,
)
from app.auth.otp import generate_otp, get_fail_count, send_otp, store_otp, verify_otp as verify_otp_async
from app.auth.phone import mask_phone, validate_indian_phone
from app.cache.client import CacheClient, get_cache
from app.cache.keys import AUTH, USER
from app.db import get_db
from app.models.user import User, PlayerProfile, CoachProfile, RefereeProfile
from app.models.wallet import Wallet
from app.models.admin import AdminInvitation
from app.services.feature_flags import get_all_flags

router = APIRouter(prefix="/v2/auth", tags=["auth"])
log = logging.getLogger("footbail.auth")

OTP_RATE_LIMIT_MAX = 3
OTP_RATE_LIMIT_WINDOW = 10 * 60   # 10 min
MAX_FAIL_ATTEMPTS = 5


# ─────── Schemas ───────
class SendOtpIn(BaseModel):
    phone: str

class VerifyOtpIn(BaseModel):
    phone: str
    otp: str = Field(min_length=6, max_length=6)

class CompleteProfileIn(BaseModel):
    onboarding_token: str
    full_name: str = Field(min_length=2, max_length=120)
    city: str
    date_of_birth: Optional[str] = None
    preferred_language: str = "en-IN"
    role: Literal["player", "coach", "referee", "team_admin"]   # admin BLOCKED
    position: Optional[str] = None
    dominant_foot: Optional[str] = None
    skill_bracket: Optional[str] = None

class RefreshIn(BaseModel):
    refresh_token: str

class AcceptInviteIn(BaseModel):
    invite_token: str
    full_name: str
    city: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    user: dict
    feature_flags: dict


# ─────── Helpers ───────
async def _user_to_card(user: User, cache: CacheClient) -> dict:
    membership_raw = await cache.get_str(f"user:membership:{user.id}")
    return {
        "id": str(user.id), "name": user.name, "phone": user.phone,
        "role": user.role, "city": user.city, "avatar_url": user.avatar_url,
        "membership_tier": membership_raw or "free",
    }


async def _flags_for_tier(tier: str, cache: CacheClient) -> dict:
    """Compute the flag values that apply for this tier, ready to embed into the access token."""
    all_flags = await get_all_flags(cache=cache)
    out: dict = {}
    for code, cfg in all_flags.items():
        out[code] = cfg.get("tiers", {}).get(tier, False)
    return out


async def _issue_token_pair(user: User, cache: CacheClient) -> TokenPair:
    membership = await cache.get_str(f"user:membership:{user.id}") or "free"
    flags = await _flags_for_tier(membership, cache)
    access, _ = create_access_token(
        user_id=str(user.id), role=user.role, city=user.city,
        membership_tier=membership, feature_flags=flags,
    )
    refresh, _ = create_refresh_token(user_id=str(user.id))
    return TokenPair(
        access_token=access, refresh_token=refresh,
        user=await _user_to_card(user, cache), feature_flags=flags,
    )


# ─────── Routes ───────
@router.post("/send-otp", status_code=200)
async def send_otp_route(
    body: SendOtpIn,
    cache: CacheClient = Depends(get_cache),
):
    phone = validate_indian_phone(body.phone)
    rl_key = AUTH.LOGIN_RATELIMIT_PHONE.format(phone=phone)
    count = await cache.increment(rl_key, by=1, ttl=OTP_RATE_LIMIT_WINDOW)
    if count > OTP_RATE_LIMIT_MAX:
        raise HTTPException(429, "Too many OTP requests. Try again in 10 minutes.")
    otp = generate_otp()
    await store_otp(phone, otp)
    sent = await send_otp(phone, otp)
    log.info("OTP issued phone=%s sent=%s", mask_phone(phone), sent)
    # Never reveal whether the phone exists
    return {"message": "If the number is valid we have sent an OTP.", "expires_in": AUTH.OTP_PHONE_TTL}


@router.post("/verify-otp")
async def verify_otp_route(
    body: VerifyOtpIn,
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    phone = validate_indian_phone(body.phone)
    fails = await get_fail_count(phone)
    if fails >= MAX_FAIL_ATTEMPTS:
        raise HTTPException(429, "Too many failed attempts. Request a fresh OTP.")

    if not await verify_otp_async(phone, body.otp):
        raise HTTPException(401, "Invalid or expired OTP")

    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    if user is None:
        ob_token, _ = create_onboarding_token(phone_e164=phone)
        return {"status": "new_user", "onboarding_token": ob_token}
    if user.deleted_at is not None or not user.is_active:
        raise HTTPException(403, "Account deactivated")
    user.last_seen_at = datetime.now(timezone.utc)
    await db.commit()
    pair = await _issue_token_pair(user, cache)
    return pair.model_dump()


@router.post("/complete-profile")
async def complete_profile_route(
    body: CompleteProfileIn,
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    if body.role == "admin":   # belt-and-suspenders — Literal already excludes
        raise HTTPException(403, "Admin role cannot self-register")
    try:
        payload = decode_token(body.onboarding_token, expected_type="onboarding")
    except ValueError as e:
        raise HTTPException(401, str(e))
    phone: str = payload["sub"]

    if (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none():
        raise HTTPException(409, "Account already exists for this phone")

    # ATOMIC: user + role profile + wallet in one transaction
    user = User(
        phone=phone, role=body.role, name=body.full_name, city=body.city,
        locale=body.preferred_language, is_active=True,
        phone_verified_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()

    if body.role == "player":
        db.add(PlayerProfile(
            user_id=user.id,
            position=body.position or "CM",
            preferred_foot=body.dominant_foot or "right",
            skill_bracket=body.skill_bracket or "intermediate",
        ))
    elif body.role == "coach":
        db.add(CoachProfile(user_id=user.id))
    elif body.role == "referee":
        db.add(RefereeProfile(user_id=user.id))
    # team_admin has no role-specific profile table

    db.add(Wallet(user_id=user.id, balance_paise=0))
    await db.commit()
    await db.refresh(user)

    log.info("Account created phone=%s role=%s", mask_phone(phone), body.role)
    pair = await _issue_token_pair(user, cache)
    return pair.model_dump()


@router.post("/refresh")
async def refresh_route(
    body: RefreshIn,
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    try:
        payload = decode_token(body.refresh_token, expected_type="refresh")
    except ValueError as e:
        raise HTTPException(401, str(e))
    old_jti = payload["jti"]
    if await cache.exists(AUTH.REFRESH_BLOCKLIST.format(jti=old_jti)):
        raise HTTPException(401, "Refresh token revoked")

    user_id = payload["sub"]
    user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user or user.deleted_at is not None or not user.is_active:
        raise HTTPException(401, "User unavailable")

    # Atomic rotation: blocklist OLD jti BEFORE issuing new tokens
    await cache.set_str(AUTH.REFRESH_BLOCKLIST.format(jti=old_jti), "1", ttl=AUTH.REFRESH_BLOCKLIST_TTL)
    pair = await _issue_token_pair(user, cache)
    return pair.model_dump()


@router.post("/logout", status_code=204)
async def logout_route(
    body: RefreshIn,
    cache: CacheClient = Depends(get_cache),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(body.refresh_token, expected_type="refresh")
    except ValueError:
        return None
    await cache.set_str(
        AUTH.REFRESH_BLOCKLIST.format(jti=payload["jti"]), "1",
        ttl=AUTH.REFRESH_BLOCKLIST_TTL,
    )
    user_id = payload.get("sub")
    if user_id:
        # Clear FCM token (column may not exist in older models — defensive UPDATE)
        try:
            user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one_or_none()
            if user is not None and hasattr(user, "fcm_token"):
                user.fcm_token = None
                await db.commit()
        except Exception:
            await db.rollback()
        await cache.delete(USER.PROFILE.format(user_id=user_id))
    return None


@router.post("/accept-invite")
async def accept_invite_route(
    body: AcceptInviteIn,
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    try:
        payload = decode_token(body.invite_token, expected_type="invite")
    except ValueError as e:
        raise HTTPException(401, str(e))
    phone = validate_indian_phone(payload["sub"])
    role = payload.get("role")
    if role == "admin":
        raise HTTPException(403, "Admin invitations cannot be redeemed via this route")

    inv = (await db.execute(
        select(AdminInvitation).where(AdminInvitation.token == payload["jti"], AdminInvitation.status == "pending")
    )).scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Invitation not found or already redeemed")
    if inv.expires_at < datetime.now(timezone.utc):
        raise HTTPException(410, "Invitation expired")

    if (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none():
        raise HTTPException(409, "Account already exists for this phone")

    user = User(phone=phone, role=role, name=body.full_name, city=body.city,
                phone_verified_at=datetime.now(timezone.utc), is_active=True)
    db.add(user); await db.flush()
    if role == "player":
        db.add(PlayerProfile(user_id=user.id))
    elif role == "coach":
        db.add(CoachProfile(user_id=user.id))
    elif role == "referee":
        db.add(RefereeProfile(user_id=user.id))
    db.add(Wallet(user_id=user.id, balance_paise=0))

    inv.status = "accepted"
    inv.accepted_at = datetime.now(timezone.utc)
    inv.accepted_user_id = user.id
    await db.commit()
    await db.refresh(user)

    pair = await _issue_token_pair(user, cache)
    return pair.model_dump()
