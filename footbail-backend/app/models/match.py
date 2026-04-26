"""Match, Turf, and MatchEvent ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Turf(Base):
    __tablename__ = "turfs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    has_cameras: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    matches: Mapped[list[Match]] = relationship(back_populates="turf")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turf_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("turfs.id", ondelete="SET NULL")
    )
    home_team: Mapped[str] = mapped_column(String(80), nullable=False)
    away_team: Mapped[str] = mapped_column(String(80), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="scheduled")
    referee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    home_score: Mapped[int] = mapped_column(Integer, default=0)
    away_score: Mapped[int] = mapped_column(Integer, default=0)
    city: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    max_players: Mapped[int] = mapped_column(Integer, default=22)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    turf: Mapped[Turf | None] = relationship(back_populates="matches")
    videos: Mapped[list[Video]] = relationship(  # type: ignore[name-defined]
        "Video", back_populates="match"
    )
    events: Mapped[list[MatchEvent]] = relationship(back_populates="match", cascade="all, delete-orphan")


class MatchEvent(Base):
    """Real-time match events stored in PostgreSQL (mirrors DynamoDB in production)."""
    __tablename__ = "match_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(32))  # GOAL, FOUL, OFFSIDE, etc.
    player_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    team: Mapped[str | None] = mapped_column(String(10))  # home | away
    minute: Mapped[int | None] = mapped_column(Integer)
    metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    match: Mapped[Match] = relationship(back_populates="events")


# Avoid circular import
from app.models.footage import Video  # noqa: E402
