"""OTP generation, hashing, send (Firebase primary → MSG91 fallback), verify."""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from typing import Optional

import httpx

from app.auth.phone import mask_phone
from app.cache.client import get_cache
from app.cache.keys import AUTH

log = logging.getLogger("footbail.otp")

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
FIREBASE_OTP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:sendVerificationCode"
MSG91_AUTH_KEY = os.environ.get("MSG91_AUTH_KEY", "")
MSG91_TEMPLATE_ID = os.environ.get("MSG91_OTP_TEMPLATE_ID", "")
MSG91_URL = "https://control.msg91.com/api/v5/otp"


def generate_otp() -> str:
    """6-digit OTP using `secrets` (cryptographically secure)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_otp(phone: str, otp: str) -> str:
    """SHA-256 with phone as salt — never store plaintext OTPs."""
    digest = hashlib.sha256(f"{phone}:{otp}".encode("utf-8")).hexdigest()
    return digest


async def store_otp(phone: str, otp: str) -> None:
    cache = get_cache()
    await cache.set_str(AUTH.OTP_PHONE.format(phone=phone), _hash_otp(phone, otp), ttl=AUTH.OTP_PHONE_TTL)
    # Reset failure counter for this phone
    await cache.delete(AUTH.OTP_ATTEMPTS.format(phone=phone))


async def verify_otp(phone: str, otp_input: str) -> bool:
    """Constant-time comparison via hmac.compare_digest. Increments fail counter on mismatch."""
    cache = get_cache()
    stored = await cache.get_str(AUTH.OTP_PHONE.format(phone=phone))
    if stored is None:
        return False
    expected = _hash_otp(phone, otp_input)
    is_match = hmac.compare_digest(stored, expected)
    if is_match:
        # Single-use: clear after success
        await cache.delete(AUTH.OTP_PHONE.format(phone=phone))
        await cache.delete(AUTH.OTP_ATTEMPTS.format(phone=phone))
    else:
        await cache.increment(AUTH.OTP_ATTEMPTS.format(phone=phone), by=1, ttl=AUTH.OTP_ATTEMPTS_TTL)
    return is_match


async def get_fail_count(phone: str) -> int:
    cache = get_cache()
    raw = await cache.get_str(AUTH.OTP_ATTEMPTS.format(phone=phone))
    return int(raw) if raw and raw.isdigit() else 0


async def _send_via_firebase(phone: str, otp: str) -> bool:
    if not FIREBASE_API_KEY:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.post(
                f"{FIREBASE_OTP_URL}?key={FIREBASE_API_KEY}",
                json={"phoneNumber": phone, "recaptchaToken": "skip"},
            )
            r.raise_for_status()
            return True
    except Exception as e:  # pragma: no cover
        log.warning("Firebase OTP failed phone=%s err=%s", mask_phone(phone), e)
        return False


async def _send_via_msg91(phone: str, otp: str) -> bool:
    if not MSG91_AUTH_KEY or not MSG91_TEMPLATE_ID:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.post(
                MSG91_URL,
                headers={"authkey": MSG91_AUTH_KEY, "Content-Type": "application/json"},
                json={
                    "template_id": MSG91_TEMPLATE_ID,
                    "mobile": phone.lstrip("+"),
                    "otp": otp,
                    "otp_length": 6,
                    "otp_expiry": 5,
                },
            )
            r.raise_for_status()
            return True
    except Exception as e:  # pragma: no cover
        log.warning("MSG91 OTP failed phone=%s err=%s", mask_phone(phone), e)
        return False


async def send_otp(phone: str, otp: str) -> bool:
    """Primary Firebase → MSG91 fallback. Never raises. Logs only masked phone."""
    if await _send_via_firebase(phone, otp):
        return True
    if await _send_via_msg91(phone, otp):
        return True
    log.warning("OTP send completely failed phone=%s", mask_phone(phone))
    return False
