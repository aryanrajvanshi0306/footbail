"""OTP Service — generate, store, deliver, verify 6-digit codes via Redis."""
from __future__ import annotations

import logging
import random
import string

from app.core.config import settings
from app.core.redis import get_redis

log = logging.getLogger(__name__)


def _otp_key(phone: str) -> str:
    return f"footbail:otp:{phone}"


def _attempt_key(phone: str) -> str:
    return f"footbail:otp_attempts:{phone}"


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=6))


async def send_otp(phone: str) -> str:
    """Generate, store, and deliver an OTP. Returns the code (logged in dev)."""
    r = await get_redis()
    code = _generate_code()
    await r.setex(_otp_key(phone), settings.OTP_TTL_SECONDS, code)
    await r.delete(_attempt_key(phone))

    if settings.ENV == "development" or not settings.aws_real:
        log.warning("DEV OTP for %s → %s", phone, code)
    else:
        await _send_sms_sns(phone, code)

    return code


async def _send_sms_sns(phone: str, code: str) -> None:
    import boto3

    sns = boto3.client("sns", **settings.boto3_kwargs)
    sns.publish(
        PhoneNumber=phone,
        Message=f"Your footbAIl OTP is {code}. Valid 5 mins. Do not share.",
        MessageAttributes={
            "AWS.SNS.SMS.SenderID": {"DataType": "String", "StringValue": settings.SNS_SENDER_ID},
            "AWS.SNS.SMS.SMSType": {"DataType": "String", "StringValue": "Transactional"},
        },
    )
    log.info("OTP SMS sent to %s via SNS", phone)


async def verify_otp(phone: str, code: str) -> bool:
    """
    Returns True if code matches. Raises ValueError on lockout.
    DEV_OTP_BYPASS=true → any 6-digit code passes.
    """
    if settings.DEV_OTP_BYPASS and settings.ENV != "production":
        return len(code) == 6 and code.isdigit()

    r = await get_redis()
    attempts_raw = await r.get(_attempt_key(phone))
    attempts = int(attempts_raw) if attempts_raw else 0
    if attempts >= settings.OTP_MAX_ATTEMPTS:
        raise ValueError("Too many incorrect attempts. Request a new OTP.")

    stored = await r.get(_otp_key(phone))
    if stored is None:
        return False

    if stored == code:
        await r.delete(_otp_key(phone))
        await r.delete(_attempt_key(phone))
        return True

    await r.incr(_attempt_key(phone))
    await r.expire(_attempt_key(phone), settings.OTP_TTL_SECONDS)
    return False
