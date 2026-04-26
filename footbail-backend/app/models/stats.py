"""Player profile and per-match stats ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PlayerProfile(Base):
    __tablename__ = "player_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[str | None] = mapped_column(String(32))
    dominant_foot: Mapped[str | None] = mapped_column(String(5))
    jersey_number: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None] = mapped_column(Numeric(4, 2))
    total_goals: Mapped[int] = mapped_column(Integer, default=0)
    total_assists: Mapped[int] = mapped_column(Integer, default=0)
    total_matches: Mapped[int] = mapped_column(Integer, default=0)
    bio: Mapped[str | None] = mapped_column(String(500))
    highlight_video_url: Mapped[str | None] = mapped_column(String(512))

    user: Mapped["User"] = relationship("User", back_populates="profile")  # type: ignore[name-defined]


class PlayerStats(Base):
    __tablename__ = "player_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="SET NULL"), index=True
    )
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float | None] = mapped_column(Float)
    distance_km: Mapped[float | None] = mapped_column(Float)
    sprint_count: Mapped[int] = mapped_column(Integer, default=0)
    duel_wins: Mapped[int] = mapped_column(Integer, default=0)
    duel_losses: Mapped[int] = mapped_column(Integer, default=0)
    heatmap_data: Mapped[str | None] = mapped_column(String(2048))  # JSON blob
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
