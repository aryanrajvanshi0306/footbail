"""Section M — AI Data (3 tables).
48. ai_analysis_jobs
49. match_impact_scores
50. oyp_profiles
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
from app.models.mixins import UUIDMixin, TimestampMixin
from app.models.enums import AI_JOB_TYPES, AI_JOB_STATUSES, in_check


# ─────────────────────────── 48. ai_analysis_jobs ───────────────────────────
class AiAnalysisJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_analysis_jobs"

    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(12), default="queued", nullable=False, index=True)
    video_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    match_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    requested_by: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    sagemaker_job_arn: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    openai_request_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    cost_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    output_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    retry_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint(in_check("type", AI_JOB_TYPES), name="type_valid"),
        CheckConstraint(in_check("status", AI_JOB_STATUSES), name="status_valid"),
        CheckConstraint("cost_paise >= 0", name="cost_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<AiAnalysisJob id={self.id} type={self.type} status={self.status}>"


# ─────────────────────────── 49. match_impact_scores ───────────────────────────
class MatchImpactScore(Base, UUIDMixin, TimestampMixin):
    """Module 05 — Match Impact Index (0-100 per player)."""
    __tablename__ = "match_impact_scores"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0-100
    is_impact_hero: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    component_offense: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    component_defense: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    component_creativity: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    component_workrate: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    component_clutch: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    breakdown: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_user_impact"),
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
    )

    def __repr__(self) -> str:
        return f"<MatchImpactScore match={self.match_id} user={self.user_id} score={self.score}>"


# ─────────────────────────── 50. oyp_profiles ───────────────────────────
class OypProfile(Base, UUIDMixin, TimestampMixin):
    """One Year Player AI profile — Play Style DNA, top strengths, dev areas."""
    __tablename__ = "oyp_profiles"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    style_dna: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # {"box-to-box":84,"poacher":62,...}
    top_strengths: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # ["passing_under_pressure", ...]
    development_areas: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    archetype_label: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)  # "Box-to-Box CM"
    confidence: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)  # 0-100
    matches_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_refresh_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    public_url_slug: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True)

    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 100", name="confidence_range"),
    )

    def __repr__(self) -> str:
        return f"<OypProfile user={self.user_id} archetype={self.archetype_label}>"
