"""Section H — Gamification (6 tables).
32. xp_events
33. achievements
34. player_achievements
35. challenges
36. player_challenges
37. leaderboard_snapshots
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, Date, ForeignKey, Index, Integer,
    SmallInteger, String, Text, Boolean, UniqueConstraint, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import (
    XP_EVENT_TYPES, ACHIEVEMENT_RARITIES,
    CHALLENGE_TYPES, CHALLENGE_STATUSES,
    LEADERBOARD_SCOPES, LEADERBOARD_METRICS, in_check,
)


# ─────────────────────────── 32. xp_events ───────────────────────────
class XpEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "xp_events"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    multiplier: Mapped[int] = mapped_column(SmallInteger, default=100, nullable=False)  # 100 = 1.0x
    source_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    season_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    __table_args__ = (
        CheckConstraint(in_check("event_type", XP_EVENT_TYPES), name="event_type_valid"),
        Index("ix_xp_events_user_created", "user_id", "created_at"),
        Index("ix_xp_events_user_type", "user_id", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<XpEvent user={self.user_id} type={self.event_type} amount={self.amount}>"


# ─────────────────────────── 33. achievements ───────────────────────────
class Achievement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "achievements"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rarity: Mapped[str] = mapped_column(String(12), default="common", nullable=False, index=True)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    icon_key: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    criteria: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # {type, threshold, ...}
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint(in_check("rarity", ACHIEVEMENT_RARITIES), name="rarity_valid"),
        CheckConstraint("xp_reward >= 0", name="xp_reward_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<Achievement code={self.code} rarity={self.rarity}>"


# ─────────────────────────── 34. player_achievements ───────────────────────────
class PlayerAchievement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "player_achievements"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    progress: Mapped[int] = mapped_column(SmallInteger, default=100, nullable=False)  # 0-100
    shared_to_feed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="progress_range"),
    )

    def __repr__(self) -> str:
        return f"<PlayerAchievement user={self.user_id} ach={self.achievement_id}>"


# ─────────────────────────── 35. challenges ───────────────────────────
class Challenge(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "challenges"

    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(16), default="daily", nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(40), nullable=False)  # eg "goals_scored"
    target: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    bonus_reward: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # {wallet_paise, achievement_id}
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    icon_key: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    __table_args__ = (
        CheckConstraint(in_check("type", CHALLENGE_TYPES), name="type_valid"),
        CheckConstraint("target > 0", name="target_positive"),
        CheckConstraint("xp_reward >= 0", name="xp_reward_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<Challenge code={self.code} type={self.type}>"


# ─────────────────────────── 36. player_challenges ───────────────────────────
class PlayerChallenge(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "player_challenges"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", "started_at", name="uq_user_challenge_start"),
        CheckConstraint(in_check("status", CHALLENGE_STATUSES), name="status_valid"),
        CheckConstraint("progress >= 0", name="progress_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<PlayerChallenge user={self.user_id} ch={self.challenge_id} status={self.status}>"


# ─────────────────────────── 37. leaderboard_snapshots ───────────────────────────
class LeaderboardSnapshot(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "leaderboard_snapshots"

    scope: Mapped[str] = mapped_column(String(16), default="city", nullable=False)
    scope_id: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)  # city name | club_id | "global"
    metric: Mapped[str] = mapped_column(String(16), default="xp", nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[str] = mapped_column(String(12), default="weekly", nullable=False)
    rankings: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # [{user_id,rank,value}]
    total_participants: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("scope", "scope_id", "metric", "snapshot_date", "period", name="uq_leaderboard_snapshot"),
        CheckConstraint(in_check("scope", LEADERBOARD_SCOPES), name="scope_valid"),
        CheckConstraint(in_check("metric", LEADERBOARD_METRICS), name="metric_valid"),
        CheckConstraint("period IN ('daily','weekly','monthly','seasonal','all_time')", name="period_valid"),
        Index("ix_leaderboard_scope_metric_date", "scope", "metric", "snapshot_date"),
    )

    def __repr__(self) -> str:
        return f"<LeaderboardSnapshot scope={self.scope} metric={self.metric} date={self.snapshot_date}>"
