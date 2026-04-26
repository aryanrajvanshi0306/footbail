"""
Configuration — all settings loaded from environment variables.
Pydantic BaseSettings handles .env parsing, type coercion, and validation.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    ENV: str = "development"
    LOCAL_DEV: bool = True
    SECRET_KEY: str = "local-dev-secret-change-in-prod-minimum-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://app.footbail.in",
    ]

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://footbail:footbail@localhost:5432/footbail"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    OTP_TTL_SECONDS: int = 300
    OTP_MAX_ATTEMPTS: int = 3

    # ── Celery ────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── AWS / LocalStack ──────────────────────────────────────────────────────
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_ENDPOINT_URL: str = ""  # empty = real AWS; "http://localstack:4566" for local

    RAW_VIDEO_BUCKET: str = "footbail-raw-videos"
    PROCESSED_VIDEO_BUCKET: str = "footbail-processed-videos"

    # ── Cognito ───────────────────────────────────────────────────────────────
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_APP_CLIENT_ID: str = ""
    COGNITO_DOMAIN: str = ""

    # ── Google OAuth ──────────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ── SNS ───────────────────────────────────────────────────────────────────
    SNS_SENDER_ID: str = "footbAIl"

    # ── Feature flags ─────────────────────────────────────────────────────────
    DEV_OTP_BYPASS: bool = True

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def cognito_configured(self) -> bool:
        return bool(self.COGNITO_USER_POOL_ID and self.COGNITO_APP_CLIENT_ID)

    @property
    def aws_real(self) -> bool:
        """True when pointing at real AWS (not LocalStack)."""
        return not self.LOCAL_DEV and not self.AWS_ENDPOINT_URL

    @property
    def boto3_kwargs(self) -> dict:
        """Common kwargs for all boto3 clients — handles LocalStack transparently."""
        kw: dict = {
            "region_name": self.AWS_REGION,
            "aws_access_key_id": self.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": self.AWS_SECRET_ACCESS_KEY,
        }
        if self.AWS_ENDPOINT_URL:
            kw["endpoint_url"] = self.AWS_ENDPOINT_URL
        return kw


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
