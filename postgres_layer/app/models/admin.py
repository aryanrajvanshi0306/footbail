"""Section N — Admin (2 tables).
51. admin_invitations
52. analytics_events
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, ForeignKey, Index, Integer, SmallInteger,
    String, Text, Boolean, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin
from app.models.enums import USER_ROLES, ADMIN_INVITATION_STATUSES, in_check


# ─────────────────────────── 51. admin_invitations ───────────────────────────
class AdminInvitation(Base, UUIDMixin, TimestampMixin):
    """Used when an admin manually creates a turf_owner / referee / coach / team_admin account."""
    __tablename__ = "admin_invitations"

    invited_phone: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, index=True)
    invited_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    intended_role: Mapped[str] = mapped_column(String(16), nullable=False)
    invited_by: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    accepted_user_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    token: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(12), default="pending", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # prefill values for the new account

    __table_args__ = (
        CheckConstraint(in_check("intended_role", USER_ROLES), name="intended_role_valid"),
        CheckConstraint(in_check("status", ADMIN_INVITATION_STATUSES), name="status_valid"),
        CheckConstraint("invited_phone IS NOT NULL OR invited_email IS NOT NULL", name="phone_or_email_required"),
    )

    def __repr__(self) -> str:
        return f"<AdminInvitation role={self.intended_role} status={self.status}>"


# ─────────────────────────── 52. analytics_events ───────────────────────────
class AnalyticsEvent(Base, UUIDMixin, TimestampMixin):
    """Generic product analytics event log — feeds dashboards & funnels."""
    __tablename__ = "analytics_events"

    user_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    anonymous_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    event_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    surface: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # ios | android | web | api
    app_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_analytics_event_occurred", "event_name", "occurred_at"),
        Index("ix_analytics_user_occurred", "user_id", "occurred_at"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsEvent name={self.event_name} user={self.user_id}>"
