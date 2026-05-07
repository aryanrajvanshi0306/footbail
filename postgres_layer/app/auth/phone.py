"""Phone normalisation — India-only, E.164."""
from __future__ import annotations

import re

from fastapi import HTTPException

# Matches +91 followed by an Indian mobile number (starts 6-9, 10 digits total)
_E164_INDIA = re.compile(r"^\+91[6-9]\d{9}$")


def validate_indian_phone(phone: str) -> str:
    """Normalise to E.164: +91XXXXXXXXXX. Raises 422 on invalid.

    Accepts: '9876543210' | '+919876543210' | '09876543210' | '919876543210'
    """
    if not isinstance(phone, str):
        raise HTTPException(422, {"field": "phone", "message": "Enter a valid Indian mobile number"})

    digits = re.sub(r"[\s\-()]", "", phone.strip())

    if digits.startswith("+91") and len(digits) == 13:
        candidate = digits
    elif digits.startswith("91") and len(digits) == 12:
        candidate = f"+{digits}"
    elif digits.startswith("0") and len(digits) == 11:
        candidate = f"+91{digits[1:]}"
    elif len(digits) == 10:
        candidate = f"+91{digits}"
    else:
        raise HTTPException(422, {"field": "phone", "message": "Enter a valid Indian mobile number"})

    if not _E164_INDIA.match(candidate):
        raise HTTPException(422, {"field": "phone", "message": "Enter a valid Indian mobile number"})
    return candidate


def mask_phone(phone: str) -> str:
    """For logs — shows only last 4 digits. '+919876543210' → '+91*****3210'."""
    if not phone or len(phone) < 4:
        return "****"
    return f"{phone[:3]}*****{phone[-4:]}"
