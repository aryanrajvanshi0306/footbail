"""JWT — RS256, 5 token types, no per-request Redis call for feature flags."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional, TypedDict

from jose import jwt, JWTError

JWT_ALGO = "RS256"
PRIVATE_KEY = os.environ.get("JWT_PRIVATE_KEY_PEM", "")
PUBLIC_KEY = os.environ.get("JWT_PUBLIC_KEY_PEM", "")

ACCESS_MIN = 15
REFRESH_DAYS = 30
ONBOARDING_MIN = 30
INVITE_DAYS = 7
SHARE_HOURS = 48

TokenType = Literal["access", "refresh", "onboarding", "invite", "share"]


class TokenPayload(TypedDict, total=False):
    sub: str
    role: str
    city: str
    membership_tier: str
    feature_flags: dict
    video_id: str
    club_id: str
    jti: str
    type: str
    exp: int
    iat: int


def _encode(payload: dict) -> str:
    if not PRIVATE_KEY:
        raise RuntimeError("JWT_PRIVATE_KEY_PEM env var not set")
    payload = dict(payload)
    payload["iat"] = int(datetime.now(timezone.utc).timestamp())
    return jwt.encode(payload, PRIVATE_KEY, algorithm=JWT_ALGO)


def _decode(token: str) -> dict:
    if not PUBLIC_KEY:
        raise RuntimeError("JWT_PUBLIC_KEY_PEM env var not set")
    return jwt.decode(token, PUBLIC_KEY, algorithms=[JWT_ALGO])


def create_access_token(*, user_id: str, role: str, city: str, membership_tier: str, feature_flags: dict) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_MIN)
    return _encode({
        "sub": str(user_id), "role": role, "city": city,
        "membership_tier": membership_tier, "feature_flags": feature_flags,
        "jti": jti, "type": "access", "exp": int(exp.timestamp()),
    }), jti


def create_refresh_token(*, user_id: str) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    exp = datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS)
    return _encode({"sub": str(user_id), "jti": jti, "type": "refresh", "exp": int(exp.timestamp())}), jti


def create_onboarding_token(*, phone_e164: str) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    exp = datetime.now(timezone.utc) + timedelta(minutes=ONBOARDING_MIN)
    return _encode({"sub": phone_e164, "jti": jti, "type": "onboarding", "exp": int(exp.timestamp())}), jti


def create_invite_token(*, phone: str, role: str, club_id: Optional[str] = None) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    exp = datetime.now(timezone.utc) + timedelta(days=INVITE_DAYS)
    payload = {"sub": phone, "role": role, "jti": jti, "type": "invite", "exp": int(exp.timestamp())}
    if club_id:
        payload["club_id"] = str(club_id)
    return _encode(payload), jti


def create_share_token(*, user_id: str, video_id: str) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    exp = datetime.now(timezone.utc) + timedelta(hours=SHARE_HOURS)
    return _encode({"sub": str(user_id), "video_id": str(video_id), "jti": jti,
                    "type": "share", "exp": int(exp.timestamp())}), jti


def decode_token(token: str, *, expected_type: Optional[TokenType] = None) -> dict:
    """Decodes & validates expiry. Raises ValueError on tamper/expiry/type mismatch."""
    try:
        payload = _decode(token)
    except JWTError as e:
        raise ValueError(f"invalid token: {e}")
    if expected_type and payload.get("type") != expected_type:
        raise ValueError(f"expected token type {expected_type}, got {payload.get('type')}")
    return payload
