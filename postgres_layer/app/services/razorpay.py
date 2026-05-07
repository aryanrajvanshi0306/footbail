"""Razorpay payment service — HMAC-SHA256 webhook verification + order creation.

DEV bypass: when RAZORPAY_KEY_SECRET is unset OR set to '*_dev_*', the service
accepts a deterministic mock signature so the full flow remains testable without
hitting the live Razorpay API. Production must set RAZORPAY_KEY_SECRET.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from typing import Optional

import httpx

log = logging.getLogger("footbail.razorpay")

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
RAZORPAY_API = "https://api.razorpay.com/v1"

DEV_MODE = (
    not RAZORPAY_KEY_ID or
    not RAZORPAY_KEY_SECRET or
    "_dev_" in (RAZORPAY_KEY_SECRET or "")
)
_DEV_FALLBACK_SECRET = "dev_secret_footbail_v2"


def _secret() -> bytes:
    return (RAZORPAY_KEY_SECRET or _DEV_FALLBACK_SECRET).encode("utf-8")


def _webhook_secret() -> bytes:
    return (RAZORPAY_WEBHOOK_SECRET or _DEV_FALLBACK_SECRET).encode("utf-8")


def sign_order_payment(order_id: str, payment_id: str) -> str:
    """Razorpay's standard signature: HMAC-SHA256(`{order}|{payment}`) hex."""
    msg = f"{order_id}|{payment_id}".encode("utf-8")
    return hmac.new(_secret(), msg, hashlib.sha256).hexdigest()


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Constant-time HMAC verification."""
    expected = sign_order_payment(order_id, payment_id)
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(raw_body: bytes, x_razorpay_signature: str) -> bool:
    """Razorpay webhook: HMAC-SHA256 of the raw body with the dashboard webhook secret."""
    expected = hmac.new(_webhook_secret(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, x_razorpay_signature)


async def create_order(*, amount_paise: int, receipt: str, notes: Optional[dict] = None) -> dict:
    """Returns Razorpay order dict. In DEV mode, returns a deterministic mock."""
    if DEV_MODE:
        return {
            "id": f"order_dev_{secrets.token_hex(8)}",
            "amount": amount_paise, "currency": "INR",
            "receipt": receipt, "status": "created",
            "notes": notes or {}, "_dev_mode": True,
        }
    async with httpx.AsyncClient(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET), timeout=10) as c:
        r = await c.post(
            f"{RAZORPAY_API}/orders",
            json={"amount": amount_paise, "currency": "INR",
                  "receipt": receipt, "notes": notes or {}},
        )
        r.raise_for_status()
        return r.json()


def public_key_id() -> str:
    return RAZORPAY_KEY_ID or "rzp_test_dev_key"
