"""Section E — Player Stats (3 tables).
21. player_match_ratings
22. player_performance_snapshots
23. player_drill_assignments
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, Date, ForeignKey, Index, Integer,
    SmallInteger, String, Text, Boolean, UniqueConstraint, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


# ─────────────────────────── 21. player_match_ratings ───────────────────────────
class PlayerMatchRating(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "player_match_ratings"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0-100 (×0.1 in UI: 86 -> 8.6)
    is_motm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    component_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    coach_overrides: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_user_rating"),
        CheckConstraint("overall_rating BETWEEN 0 AND 100", name="rating_range"),
    )

    def __repr__(self) -> str:
        return f"<PlayerMatchRating match={self.match_id} user={self.user_id} r={self.overall_rating}>"


# ─────────────────────────── 22. player_performance_snapshots ───────────────────────────
class PlayerPerformanceSnapshot(Base, UUIDMixin, TimestampMixin):
    """Daily/weekly snapshot — used for form graph & peer percentile."""
    __tablename__ = "player_performance_snapshots"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(12), default="weekly", nullable=False)
    matches_played: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    avg_rating: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)  # 0-100
    goals: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    assists: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    minutes_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pass_accuracy_pct: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    form_score: Mapped[int] = mapped_column(SmallInteger, default=50, nullable=False)  # 0-100
    peer_percentile: Mapped[int] = mapped_column(SmallInteger, default=50, nullable=False)
    overall_at_snapshot: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    xp_earned_in_period: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", "period", name="uq_user_snapshot"),
        CheckConstraint("period IN ('daily','weekly','monthly','seasonal')", name="period_valid"),
        CheckConstraint("form_score BETWEEN 0 AND 100 AND peer_percentile BETWEEN 0 AND 100", name="score_ranges"),
        Index("ix_perf_snapshots_user_date", "user_id", "snapshot_date"),
    )

    def __repr__(self) -> str:
        return f"<PerformanceSnapshot user={self.user_id} date={self.snapshot_date} form={self.form_score}>"


# ─────────────────────────── 23. player_drill_assignments ───────────────────────────
class PlayerDrillAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "player_drill_assignments"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    drill_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("drill_library.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_coach_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("coach_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    coach_session_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("coach_sessions.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="assigned", nullable=False)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_video_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    coach_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)  # 0-100

    __table_args__ = (
        CheckConstraint("status IN ('assigned','in_progress','submitted','reviewed','skipped')", name="status_valid"),
        CheckConstraint("rating IS NULL OR rating BETWEEN 0 AND 100", name="rating_range"),
    )

    def __repr__(self) -> str:
        return f"<PlayerDrillAssignment user={self.user_id} drill={self.drill_id} status={self.status}>"
