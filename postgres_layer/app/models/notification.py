"""Section L — Notifications (2 tables).
46. notification_logs
47. whatsapp_message_logs
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
from app.models.enums import (
    NOTIFICATION_CHANNELS, NOTIFICATION_TYPES, NOTIFICATION_STATUSES,
    WHATSAPP_TEMPLATES, in_check,
)


# ─────────────────────────── 46. notification_logs ───────────────────────────
class NotificationLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notification_logs"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(12), default="queued", nullable=False, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)

    __table_args__ = (
        CheckConstraint(in_check("channel", NOTIFICATION_CHANNELS), name="channel_valid"),
        CheckConstraint(in_check("type", NOTIFICATION_TYPES), name="type_valid"),
        CheckConstraint(in_check("status", NOTIFICATION_STATUSES), name="status_valid"),
        Index("ix_notif_user_created", "user_id", "created_at"),
        Index("ix_notif_status_channel", "status", "channel"),
    )

    def __repr__(self) -> str:
        return f"<NotificationLog user={self.user_id} channel={self.channel} status={self.status}>"


# ─────────────────────────── 47. whatsapp_message_logs ───────────────────────────
class WhatsappMessageLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "whatsapp_message_logs"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    template_name: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    template_language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    template_params: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    meta_message_id: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(12), default="queued", nullable=False, index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cost_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint(in_check("template_name", WHATSAPP_TEMPLATES), name="template_valid"),
        CheckConstraint(in_check("status", NOTIFICATION_STATUSES), name="status_valid"),
        CheckConstraint("phone ~ '^\\+91[0-9]{10}$'", name="phone_e164_india"),
        CheckConstraint("cost_paise >= 0", name="cost_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<WhatsappLog user={self.user_id} tpl={self.template_name} status={self.status}>"
