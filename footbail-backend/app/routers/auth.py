"""
Auth Router — /auth/*

POST /auth/otp/send     → send OTP
POST /auth/verify-otp   → verify OTP → token pair
POST /auth/google       → Google OAuth code → token pair
POST /auth/refresh      → rotate tokens
POST /auth/logout       → revoke refresh token
GET  /auth/me           → current user profile
"""
from __future__ import annotations

import hashlib
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.auth import create_access_token, create_refresh_token, decode_local_token, get_current_user
from app.core.database import get_db
from app.models.user import RefreshToken, RoleEnum, User
from app.schemas.auth import (
    GoogleAuthRequest, MeResponse, OTPSendRequest, OTPSendResponse,
    OTPVerifyRequest, RefreshRequest, TokenPair, UserOut,
)
from app.services.auth_service import (
    exchange_google_code, get_or_create_user, issue_token_pair, revoke_refresh_token,
)
from app.services.otp_service import send_otp, verify_otp

log = logging.getLogger(__name__)
router = APIRouter()

DBDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


# ─── OTP ─────────────────────────────────────────────────────────────────────

@router.post("/otp/send", response_model=OTPSendResponse)
async def send_otp_endpoint(body: OTPSendRequest, request: Request):
    """Generate and send a 6-digit OTP to the provided phone number."""
    from app.core.config import settings
    code = await send_otp(body.phone)
    response = OTPSendResponse(message=f"OTP sent to {body.phone}")
    if settings.ENV != "production" and settings.DEV_OTP_BYPASS:
        response.dev_otp = code
    log.info("OTP send: %s from %s", body.phone, request.client.host if request.client else "unknown")
    return response


@router.post("/verify-otp", response_model=TokenPair)
async def verify_otp_endpoint(body: OTPVerifyRequest, db: DBDep, request: Request):
    """Verify OTP and issue token pair (upserts user on first login)."""
    try:
        valid = await verify_otp(body.phone, body.otp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))

    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")

    name = f"User {body.phone[-4:]}"
    user = await get_or_create_user(db, phone=body.phone, name=name, role=body.role)
    tokens = await issue_token_pair(db, user)
    log.info("Phone login: %s [%s]", body.phone, body.role)
    return tokens


# ─── GOOGLE OAUTH ─────────────────────────────────────────────────────────────

@router.post("/google", response_model=TokenPair)
async def google_auth(body: GoogleAuthRequest, db: DBDep, request: Request):
    """Exchange Cognito-issued auth code for our token pair."""
    try:
        claims = await exchange_google_code(body.code)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth error: {exc}")

    email = claims.get("email") or claims.get("sub")
    name = claims.get("name", email)
    user = await get_or_create_user(
        db, email=email, name=name, role=body.role, cognito_sub=claims.get("sub")
    )
    tokens = await issue_token_pair(db, user)
    log.info("Google login: %s [%s]", email, user.role)
    return tokens


# ─── REFRESH ─────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(body: RefreshRequest, db: DBDep):
    """Accept a valid refresh token, return a new rotated token pair."""
    try:
        claims = decode_local_token(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if claims.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    token_hash = hashlib.sha256(body.refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
        )
    )
    rt = result.scalar_one_or_none()
    if rt is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    rt.revoked = True

    result2 = await db.execute(select(User).where(User.id == rt.user_id))
    user = result2.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return await issue_token_pair(db, user)


# ─── LOGOUT ──────────────────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: DBDep, _user: CurrentUser):
    """Revoke the provided refresh token."""
    await revoke_refresh_token(db, body.refresh_token)


# ─── ME ──────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser):
    """Return the authenticated user's profile."""
    return MeResponse(user=UserOut.model_validate(user), role=user.role)
