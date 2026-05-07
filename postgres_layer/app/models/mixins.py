"""Reusable mixins — UUID PK, timestamps, soft-delete."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """Primary key — UUID v4 via Postgres gen_random_uuid() (pgcrypto).
    Python-side `uuid4` default is also set so the same model works under
    SQLite (test harness) where gen_random_uuid() is unavailable. SQLAlchemy
    prefers `server_default` when present, so on Postgres the DB still owns ID
    generation; on SQLite the Python default fires."""
    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )


class TimestampMixin:
    """All timestamps stored in TIMESTAMPTZ UTC — displayed as IST in UI."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )


class SoftDeleteMixin:
    """Required on all user-facing tables. NULL = active."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
