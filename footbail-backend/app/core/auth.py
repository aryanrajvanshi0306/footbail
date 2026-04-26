"""
Auth Core — JWT encode/decode + RBAC dependency factory.

Two modes (selected automatically):
  LOCAL_DEV=true  → HS256 JWTs issued by this server; Cognito not needed.
  LOCAL_DEV=false → RS256 Cognito tokens validated via JWKS endpoint.

Both modes produce the same normalised payload dict with keys:
  sub, role, name, cognito:groups
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db

log = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=True)

# ─── LOCAL JWT (HS256) ────────────────────────────────────────────────────────


def create_access_token(user_id: str, role: str, name: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "name": name,
        "cognito:groups": [role.capitalize() + "s"],
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iss": "footbail-local",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Returns (raw_token, sha256_hash_for_db_storage)."""
    raw = str(uuid.uuid4())
    token = jwt.encode(
        {
            "sub": user_id,
            "jti": raw,
            "type": "refresh",
            "exp": datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


def decode_local_token(token: str) -> dict:
    """Decode a locally-issued HS256 token. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ─── COGNITO JWT (RS256) ──────────────────────────────────────────────────────

_cognito_jwks: dict | None = None


async def _fetch_cognito_jwks() -> dict:
    global _cognito_jwks
    if _cognito_jwks:
        return _cognito_jwks
    url = (
        f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com"
        f"/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    _cognito_jwks = resp.json()
    log.info("Cognito JWKS fetched and cached")
    return _cognito_jwks


async def decode_cognito_token(token: str) -> dict:
    jwks = await _fetch_cognito_jwks()
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    key_data = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if not key_data:
        raise JWTError("Public key not found in Cognito JWKS")
    public_key = jwk.construct(key_data)
    message, encoded_sig = token.rsplit(".", 1)
    decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))
    if not public_key.verify(message.encode("utf-8"), decoded_sig):
        raise JWTError("Token signature verification failed")
    claims = jwt.get_unverified_claims(token)
    issuer = (
        f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com"
        f"/{settings.COGNITO_USER_POOL_ID}"
    )
    if claims.get("iss") != issuer:
        raise JWTError("Invalid token issuer")
    if claims.get("client_id") != settings.COGNITO_APP_CLIENT_ID:
        raise JWTError("Invalid token audience")
    if datetime.fromtimestamp(claims["exp"], tz=timezone.utc) < datetime.now(timezone.utc):
        raise JWTError("Token expired")
    return claims


# ─── UNIFIED DECODER ─────────────────────────────────────────────────────────


async def decode_token(token: str) -> dict:
    """Try Cognito RS256 first (if configured), fallback to local HS256."""
    if settings.cognito_configured:
        try:
            claims = await decode_cognito_token(token)
            groups = claims.get("cognito:groups", [])
            role = groups[0].rstrip("s").lower() if groups else "player"
            claims["role"] = role
            return claims
        except JWTError:
            pass
    return decode_local_token(token)


def extract_role(claims: dict) -> str:
    groups = claims.get("cognito:groups", [])
    if groups:
        return groups[0].rstrip("s").lower()
    return claims.get("role", "player")


# ─── FASTAPI DEPENDENCIES ─────────────────────────────────────────────────────


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    FastAPI dependency: validate Bearer token → return User ORM object.
    Import User here to avoid circular imports at module level.
    """
    from app.models.user import User

    token = credentials.credentials
    try:
        claims = await decode_token(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing sub claim")

    try:
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID")

    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(*allowed_roles):
    """Dependency factory that enforces one or more allowed roles."""

    async def _check(user=Depends(get_current_user)):
        from app.models.user import RoleEnum

        role_values = [r.value if hasattr(r, "value") else r for r in allowed_roles]
        user_role = user.role.value if hasattr(user.role, "value") else user.role
        if user_role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required: {role_values}",
            )
        return user

    return _check


# Convenience typed aliases
CurrentUser = Annotated[object, Depends(get_current_user)]
