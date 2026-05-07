"""Section I — Marketplace (2 tables).
38. coach_sessions
39. drill_library
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, ForeignKey, Index, Integer, SmallInteger,
    String, Text, Boolean, DateTime, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import (
    COACH_SESSION_TYPES, COACH_SESSION_STATUSES, DRILL_DIFFICULTIES, in_check,
)


# ─────────────────────────── 38. coach_sessions ───────────────────────────
class CoachSession(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "coach_sessions"

    coach_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("coach_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)
    player_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    session_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    brief: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="requested", nullable=False, index=True)
    fee_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_fee_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coach_payout_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    razorpay_payout_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    paid_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    related_video_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    deliverables: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # {annotations:[], drills:[], voice_url}
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)  # 1-5
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(in_check("session_type", COACH_SESSION_TYPES), name="session_type_valid"),
        CheckConstraint(in_check("status", COACH_SESSION_STATUSES), name="status_valid"),
        CheckConstraint("fee_paise >= 0 AND platform_fee_paise >= 0 AND coach_payout_paise >= 0", name="fees_non_neg"),
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="rating_1_5"),
        Index("ix_coach_sessions_coach_status", "coach_id", "status"),
        Index("ix_coach_sessions_player_created", "player_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CoachSession id={self.id} coach={self.coach_id} player={self.player_id} status={self.status}>"


# ─────────────────────────── 39. drill_library ───────────────────────────
class DrillLibrary(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "drill_library"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    focus_area: Mapped[str] = mapped_column(String(40), nullable=False, index=True)  # passing/dribbling/shooting/defending/fitness
    difficulty: Mapped[str] = mapped_column(String(16), default="intermediate", nullable=False, index=True)
    duration_min: Mapped[int] = mapped_column(SmallInteger, default=15, nullable=False)
    equipment_needed: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    video_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    instructions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # ordered steps
    target_attributes: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # ["pac","sho"]
    created_by_coach_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("coach_profiles.id", ondelete="SET NULL"), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    avg_rating: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)  # 0-50
    times_assigned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint(in_check("difficulty", DRILL_DIFFICULTIES), name="difficulty_valid"),
        CheckConstraint("duration_min > 0", name="duration_positive"),
        CheckConstraint("avg_rating BETWEEN 0 AND 50", name="rating_range"),
    )

    def __repr__(self) -> str:
        return f"<DrillLibrary code={self.code} focus={self.focus_area}>"
