"""Auth Service — user upsert, token issuance, Google OAuth exchange."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.auth import create_access_token, create_refresh_token
from app.core.config import settings
from app.models.user import RefreshToken, RoleEnum, User
from app.schemas.auth import TokenPair

log = logging.getLogger(__name__)


async def get_or_create_user(
    db: AsyncSession,
    *,
    phone: str | None = None,
    email: str | None = None,
    name: str,
    role: RoleEnum,
    cognito_sub: str | None = None,
) -> User:
    """Look up user by phone/email; create if missing. Updates last_login."""
    user: User | None = None

    if phone:
        result = await db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
    elif email:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user is None:
        user = User(
            name=name,
            phone=phone,
            email=email,
            role=role,
            cognito_sub=cognito_sub,
            is_verified=True,
        )
        db.add(user)
        await db.flush()
        log.info("New user created: %s [%s]", user.name, user.role)
    else:
        if cognito_sub and not user.cognito_sub:
            user.cognito_sub = cognito_sub

    user.last_login = datetime.now(timezone.utc)
    return user


async def issue_token_pair(db: AsyncSession, user: User) -> TokenPair:
    """Mint access + refresh tokens; persist the refresh token hash."""
    access = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        name=user.name,
    )
    refresh_raw, refresh_hash = create_refresh_token(str(user.id))

    rt = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)

    return TokenPair(
        access_token=access,
        refresh_token=refresh_raw,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked = True


async def exchange_google_code(code: str) -> dict:
    """Exchange Cognito/Google auth code for user claims."""
    if not settings.cognito_configured:
        # Dev stub — return a fake Google profile
        return {
            "sub": "google-dev-sub-001",
            "name": "Dev User (Google)",
            "email": "dev@gmail.com",
            "email_verified": True,
        }

    token_url = f"https://{settings.COGNITO_DOMAIN}/oauth2/token"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.COGNITO_APP_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": "https://app.footbail.in/callback",
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        tokens = resp.json()

    from app.core.auth import decode_cognito_token
    return await decode_cognito_token(tokens["id_token"])
