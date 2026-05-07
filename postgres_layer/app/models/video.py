"""Section F — Video Intelligence (3 tables).
24. videos
25. video_clips
26. video_annotations
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, ForeignKey, Index, Integer, SmallInteger,
    String, Text, Boolean, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import VIDEO_STATUSES, VIDEO_CLIP_TYPES, in_check


# ─────────────────────────── 24. videos ───────────────────────────
class Video(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "videos"

    match_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="uploading", nullable=False, index=True)
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    s3_raw_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    hls_master_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    poster_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    mediaconvert_job_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    sagemaker_job_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    upload_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    clips: Mapped[List["VideoClip"]] = relationship(back_populates="video", lazy="selectin", cascade="all, delete-orphan")
    annotations: Mapped[List["VideoAnnotation"]] = relationship(back_populates="video", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(in_check("status", VIDEO_STATUSES), name="status_valid"),
        CheckConstraint("duration_sec IS NULL OR duration_sec >= 0", name="duration_non_neg"),
        Index("ix_videos_match_status", "match_id", "status"),
        Index("ix_videos_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Video id={self.id} match={self.match_id} status={self.status}>"


# ─────────────────────────── 25. video_clips ───────────────────────────
class VideoClip(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "video_clips"

    video_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    start_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    end_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    primary_user_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    confidence: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    clip_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    video: Mapped["Video"] = relationship(back_populates="clips", lazy="selectin")

    __table_args__ = (
        CheckConstraint(in_check("type", VIDEO_CLIP_TYPES), name="type_valid"),
        CheckConstraint("end_sec > start_sec", name="clip_duration_positive"),
        CheckConstraint("confidence IS NULL OR confidence BETWEEN 0 AND 100", name="confidence_range"),
    )

    def __repr__(self) -> str:
        return f"<VideoClip video={self.video_id} type={self.type} {self.start_sec}-{self.end_sec}>"


# ─────────────────────────── 26. video_annotations ───────────────────────────
class VideoAnnotation(Base, UUIDMixin, TimestampMixin):
    """7-tool annotation canvas (arrow, freehand, ellipse, rect, text, spotlight, freeze)."""
    __tablename__ = "video_annotations"

    video_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    coach_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    tool: Mapped[str] = mapped_column(String(16), nullable=False)
    drawing_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_note_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    target_user_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    video: Mapped["Video"] = relationship(back_populates="annotations", lazy="selectin")

    __table_args__ = (
        CheckConstraint("tool IN ('arrow','freehand','ellipse','rect','text','spotlight','freeze')", name="tool_valid"),
        CheckConstraint("timestamp_sec >= 0", name="timestamp_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<VideoAnnotation video={self.video_id} t={self.timestamp_sec}s tool={self.tool}>"
