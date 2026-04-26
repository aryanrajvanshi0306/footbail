"""Auth-related Pydantic v2 schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

from app.models.user import RoleEnum


class OTPSendRequest(BaseModel):
    phone: str
    role: RoleEnum

    @field_validator("phone")
    @classmethod
    def normalise_phone(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) == 10:
            return f"+91{digits}"
        if len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        raise ValueError("Invalid Indian phone number. Provide 10 digits.")


class OTPSendResponse(BaseModel):
    message: str
    dev_otp: str | None = None


class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str
    role: RoleEnum

    @field_validator("phone")
    @classmethod
    def normalise_phone(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) == 10:
            return f"+91{digits}"
        if len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        raise ValueError("Invalid Indian phone number.")


class GoogleAuthRequest(BaseModel):
    code: str
    role: RoleEnum


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str | None
    email: str | None
    role: RoleEnum
    avatar_url: str | None = None
    city: str | None = None
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    user: UserOut
    role: RoleEnum
