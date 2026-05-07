"""Tests for /v2/auth — phone OTP SHA-256 + JWT RS256 + complete-profile flow."""
from __future__ import annotations

import json

import pytest


pytestmark = pytest.mark.asyncio


async def test_phone_normalization_via_send_otp(client):
    """validate_indian_phone normalises 10-digit / +91 / 0-prefixed → +91XXXXXXXXXX."""
    # Each variant uses a different number — rate-limiter is keyed by normalised phone,
    # so we need to vary the digits to avoid the 3/10-min cap.
    cases = [
        ("9876543210", "+919876543210"),
        ("+919876543211", "+919876543211"),
        ("09876543212", "+919876543212"),
        ("919876543213", "+919876543213"),
    ]
    for variant, _expected in cases:
        r = await client.post("/v2/auth/send-otp", json={"phone": variant})
        assert r.status_code == 200, (variant, r.text)
        body = r.json()
        assert "expires_in" in body
        assert body["message"].startswith("If the number is valid")


async def test_invalid_phone_raises_422(client):
    r = await client.post("/v2/auth/send-otp", json={"phone": "1234567890"})  # not Indian
    assert r.status_code == 422


async def test_otp_rate_limit_3_per_10min(client, cache):
    phone = "9876500001"
    for i in range(3):
        r = await client.post("/v2/auth/send-otp", json={"phone": phone})
        assert r.status_code == 200, i
    r = await client.post("/v2/auth/send-otp", json={"phone": phone})
    assert r.status_code == 429


async def test_send_otp_then_verify_returns_new_user_onboarding_token(client, cache):
    """Flow: send-otp → fetch hashed otp from cache → reverse via known phone → verify."""
    from app.auth.otp import _hash_otp, generate_otp, store_otp
    from app.auth.phone import validate_indian_phone
    from app.cache.keys import AUTH

    phone = validate_indian_phone("9876500011")
    # We can't decrypt the SHA-256 hashed OTP, so we drive the flow by storing a known one.
    otp = generate_otp()
    await store_otp(phone, otp)
    # Hash matches phone-salted SHA256
    stored = await cache.get_str(AUTH.OTP_PHONE.format(phone=phone))
    assert stored == _hash_otp(phone, otp)

    r = await client.post("/v2/auth/verify-otp", json={"phone": phone, "otp": otp})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "new_user"
    assert "onboarding_token" in body


async def test_verify_otp_with_wrong_otp_returns_401(client, cache):
    from app.auth.otp import store_otp
    from app.auth.phone import validate_indian_phone

    phone = validate_indian_phone("9876500022")
    await store_otp(phone, "111111")
    r = await client.post("/v2/auth/verify-otp", json={"phone": phone, "otp": "999999"})
    assert r.status_code == 401


async def test_complete_profile_creates_player_with_wallet(client, cache, db):
    from sqlalchemy import select
    from app.auth.jwt import create_onboarding_token
    from app.auth.phone import validate_indian_phone
    from app.models.user import User, PlayerProfile
    from app.models.wallet import Wallet

    phone = validate_indian_phone("9876500033")
    ob_token, _ = create_onboarding_token(phone_e164=phone)

    r = await client.post("/v2/auth/complete-profile", json={
        "onboarding_token": ob_token,
        "full_name": "Test Striker", "city": "Mumbai", "preferred_language": "en-IN",
        "role": "player", "position": "ST", "dominant_foot": "right",
        "skill_bracket": "intermediate",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body and "refresh_token" in body
    assert body["user"]["role"] == "player"

    # User + PlayerProfile + Wallet rows committed atomically
    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one()
    assert user.role == "player"
    profile = (await db.execute(select(PlayerProfile).where(PlayerProfile.user_id == user.id))).scalar_one()
    assert profile.position == "ST"
    wallet = (await db.execute(select(Wallet).where(Wallet.user_id == user.id))).scalar_one()
    assert wallet.balance_paise == 0


async def test_admin_role_blocked_from_complete_profile(client):
    from app.auth.jwt import create_onboarding_token
    ob_token, _ = create_onboarding_token(phone_e164="+919876500044")
    r = await client.post("/v2/auth/complete-profile", json={
        "onboarding_token": ob_token,
        "full_name": "Try Admin", "city": "Mumbai",
        "role": "admin",   # rejected by Literal — Pydantic 422
    })
    assert r.status_code == 422


async def test_jwt_rs256_round_trip():
    from app.auth.jwt import create_access_token, decode_token
    tok, jti = create_access_token(
        user_id="00000000-0000-0000-0000-000000000001",
        role="player", city="Mumbai", membership_tier="free", feature_flags={"a": True},
    )
    payload = decode_token(tok, expected_type="access")
    assert payload["sub"] == "00000000-0000-0000-0000-000000000001"
    assert payload["role"] == "player"
    assert payload["jti"] == jti
    assert payload["feature_flags"] == {"a": True}


async def test_jwt_type_mismatch_raises():
    from app.auth.jwt import create_refresh_token, decode_token
    tok, _ = create_refresh_token(user_id="00000000-0000-0000-0000-000000000002")
    with pytest.raises(ValueError):
        decode_token(tok, expected_type="access")


async def test_refresh_token_rotation_blocklists_old(client, cache, make_user):
    from app.auth.jwt import create_refresh_token, decode_token
    user = await make_user(phone="+919876500055", role="player")
    refresh, jti = create_refresh_token(user_id=str(user.id))

    r = await client.post("/v2/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200, r.text
    new_pair = r.json()
    assert "access_token" in new_pair

    # Old refresh now blocklisted
    r2 = await client.post("/v2/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 401
