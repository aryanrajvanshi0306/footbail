"""Section J — Referee (3 unique tables; training_completions canonical in user.py).
40. referee_bookings
41. referee_reports
42. referee_var_reviews
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, ForeignKey, Index, Integer, SmallInteger,
    String, Text, Boolean, DateTime, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import REFEREE_BOOKING_STATUSES, in_check


# ─────────────────────────── 40. referee_bookings ───────────────────────────
class RefereeBooking(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "referee_bookings"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    referee_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("referee_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)
    requested_by: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    fee_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    travel_allowance_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_payout_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="offered", nullable=False, index=True)
    offered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    declined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    razorpay_payout_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    paid_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("match_id", "referee_id", name="uq_match_referee"),
        CheckConstraint(in_check("status", REFEREE_BOOKING_STATUSES), name="status_valid"),
        CheckConstraint("fee_paise >= 0 AND travel_allowance_paise >= 0 AND total_payout_paise >= 0", name="payouts_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<RefereeBooking match={self.match_id} ref={self.referee_id} status={self.status}>"


# ─────────────────────────── 41. referee_reports ───────────────────────────
class RefereeReport(Base, UUIDMixin, TimestampMixin):
    """AIFF-style match report."""
    __tablename__ = "referee_reports"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    referee_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("referee_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    incidents: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    cards_issued: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    weather: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    pitch_condition: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    aiff_form_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # full AIFF-style payload
    pdf_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    signed_off: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    signature_data_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("match_id", "referee_id", name="uq_match_referee_report"),
    )

    def __repr__(self) -> str:
        return f"<RefereeReport match={self.match_id} ref={self.referee_id} signed={self.signed_off}>"


# ─────────────────────────── 42. referee_var_reviews ───────────────────────────
class RefereeVarReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "referee_var_reviews"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    referee_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("referee_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)
    event_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("match_events.id", ondelete="SET NULL"), nullable=True)
    video_clip_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("video_clips.id", ondelete="SET NULL"), nullable=True)
    decision_type: Mapped[str] = mapped_column(String(20), nullable=False)
    ai_recommendation: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ai_confidence: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    final_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    overturned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_seconds: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("decision_type IN ('offside','goal_check','penalty','red_card','foul','handball')", name="decision_type_valid"),
        CheckConstraint("ai_confidence IS NULL OR ai_confidence BETWEEN 0 AND 100", name="ai_confidence_range"),
    )

    def __repr__(self) -> str:
        return f"<RefereeVarReview match={self.match_id} type={self.decision_type} final={self.final_decision}>"
