"""Section D — Matches & Bookings (9 tables).
12. matches
13. bookings
14. match_players
15. match_player_stats
16. match_events
17. squad_polls
18. poll_responses
19. recurring_matches
20. match_lineups (Module 14 lineup builder — completes 52)
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, ForeignKey, Index, Integer, SmallInteger,
    String, Text, Boolean, UniqueConstraint, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import (
    MATCH_FORMATS, MATCH_STATUSES, MATCH_EVENT_TYPES, SIDES,
    PAYMENT_STATUSES, PAYMENT_METHODS, SKILL_BRACKETS,
    POLL_RESPONSE_TYPES, RECURRING_PATTERNS, in_check,
)


# ─────────────────────────── 12. matches ───────────────────────────
class Match(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "matches"

    home_team_name: Mapped[str] = mapped_column(String(120), nullable=False)
    away_team_name: Mapped[str] = mapped_column(String(120), nullable=False)
    home_club_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True, index=True)
    away_club_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True, index=True)
    turf_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("turfs.id", ondelete="RESTRICT"), nullable=False, index=True)
    referee_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("referee_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    creator_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_min: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    format: Mapped[str] = mapped_column(String(8), default="5v5", nullable=False)
    skill_bracket: Mapped[str] = mapped_column(String(16), default="intermediate", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="scheduled", nullable=False, index=True)
    privacy: Mapped[str] = mapped_column(String(16), default="public", nullable=False)

    score_home: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    score_away: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    broadcast_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    camera_status: Mapped[str] = mapped_column(String(12), default="idle", nullable=False)
    camera_recording_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    bookings: Mapped[List["Booking"]] = relationship(back_populates="match", lazy="selectin", cascade="all, delete-orphan")
    players: Mapped[List["MatchPlayer"]] = relationship(back_populates="match", lazy="selectin", cascade="all, delete-orphan")
    events: Mapped[List["MatchEvent"]] = relationship(back_populates="match", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(in_check("format", MATCH_FORMATS), name="format_valid"),
        CheckConstraint(in_check("status", MATCH_STATUSES), name="status_valid"),
        CheckConstraint(in_check("skill_bracket", SKILL_BRACKETS), name="skill_bracket_valid"),
        CheckConstraint("camera_status IN ('idle','recording','stopped','error')", name="camera_status_valid"),
        CheckConstraint("score_home >= 0 AND score_away >= 0", name="scores_non_neg"),
        Index("ix_matches_turf_scheduled", "turf_id", "scheduled_at"),
        Index("ix_matches_club_status", "home_club_id", "status"),
        Index("ix_matches_status_skill", "status", "skill_bracket"),
    )

    def __repr__(self) -> str:
        return f"<Match id={self.id} {self.home_team_name} v {self.away_team_name} status={self.status}>"


# ─────────────────────────── 13. bookings ───────────────────────────
class Booking(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "bookings"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    turf_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("turfs.id", ondelete="RESTRICT"), nullable=False, index=True)
    slot_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    slot_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(12), default="pending", nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    qr_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)

    match: Mapped["Match"] = relationship(back_populates="bookings", lazy="selectin")

    __table_args__ = (
        CheckConstraint(in_check("payment_status", PAYMENT_STATUSES), name="payment_status_valid"),
        CheckConstraint(f"payment_method IS NULL OR {in_check('payment_method', PAYMENT_METHODS)}", name="payment_method_valid"),
        CheckConstraint("amount_paise >= 0 AND final_amount_paise >= 0 AND discount_paise >= 0", name="amounts_non_neg"),
        Index("ix_bookings_match_user", "match_id", "user_id"),
        Index("ix_bookings_user_payment", "user_id", "payment_status"),
    )

    def __repr__(self) -> str:
        return f"<Booking id={self.id} match={self.match_id} user={self.user_id} status={self.payment_status}>"


# ─────────────────────────── 14. match_players ───────────────────────────
class MatchPlayer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "match_players"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    is_starter: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_captain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    jersey_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    minute_in: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    minute_out: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    position_played: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    match: Mapped["Match"] = relationship(back_populates="players", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_user_player"),
        CheckConstraint(in_check("side", SIDES), name="side_valid"),
    )

    def __repr__(self) -> str:
        return f"<MatchPlayer match={self.match_id} user={self.user_id} side={self.side}>"


# ─────────────────────────── 15. match_player_stats ───────────────────────────
class MatchPlayerStat(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "match_player_stats"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    minutes_played: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    goals: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    assists: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    shots: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    shots_on_target: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    passes_attempted: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    passes_completed: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    key_passes: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    tackles: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    interceptions: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    fouls_committed: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    fouls_won: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    yellow_cards: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    red_cards: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    saves: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    clean_sheet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    distance_km: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # ×100 (so 5.42km = 542)
    sprint_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    heatmap_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_user_stat"),
        Index("ix_match_player_stats_match_user", "match_id", "user_id"),
        Index("ix_match_player_stats_user_created", "user_id", "created_at"),
        CheckConstraint("goals >= 0 AND assists >= 0 AND shots >= 0", name="non_neg_basics"),
    )

    def __repr__(self) -> str:
        return f"<MatchPlayerStat match={self.match_id} user={self.user_id} G={self.goals} A={self.assists}>"


# ─────────────────────────── 16. match_events ───────────────────────────
class MatchEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "match_events"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    minute: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    second: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    side: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    primary_user_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    secondary_user_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auto_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)  # 0-100
    video_clip_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    logged_by: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    match: Mapped["Match"] = relationship(back_populates="events", lazy="selectin")

    __table_args__ = (
        CheckConstraint(in_check("type", MATCH_EVENT_TYPES), name="type_valid"),
        CheckConstraint(f"side IS NULL OR {in_check('side', SIDES)}", name="side_valid"),
        CheckConstraint("minute IS NULL OR (minute >= 0 AND minute <= 200)", name="minute_range"),
        CheckConstraint("confidence IS NULL OR confidence BETWEEN 0 AND 100", name="confidence_range"),
    )

    def __repr__(self) -> str:
        return f"<MatchEvent match={self.match_id} type={self.type} minute={self.minute}>"


# ─────────────────────────── 17. squad_polls ───────────────────────────
class SquadPoll(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "squad_polls"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    club_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("clubs.id", ondelete="CASCADE"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(String(280), nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    yes_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    no_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    maybe_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    responses: Mapped[List["PollResponse"]] = relationship(back_populates="poll", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SquadPoll match={self.match_id} closed={self.closed}>"


# ─────────────────────────── 18. poll_responses ───────────────────────────
class PollResponse(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "poll_responses"

    poll_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("squad_polls.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    response: Mapped[str] = mapped_column(String(8), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    poll: Mapped["SquadPoll"] = relationship(back_populates="responses", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("poll_id", "user_id", name="uq_poll_user_response"),
        CheckConstraint(in_check("response", POLL_RESPONSE_TYPES), name="response_valid"),
    )

    def __repr__(self) -> str:
        return f"<PollResponse poll={self.poll_id} user={self.user_id} resp={self.response}>"


# ─────────────────────────── 19. recurring_matches ───────────────────────────
class RecurringMatch(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "recurring_matches"

    club_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("clubs.id", ondelete="CASCADE"), nullable=True, index=True)
    creator_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    turf_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("turfs.id", ondelete="RESTRICT"), nullable=False, index=True)
    pattern: Mapped[str] = mapped_column(String(12), default="weekly", nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0=Mon
    time_of_day: Mapped[str] = mapped_column(String(8), nullable=False)  # "19:30"
    duration_min: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    format: Mapped[str] = mapped_column(String(8), default="5v5", nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    skip_dates: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    __table_args__ = (
        CheckConstraint(in_check("pattern", RECURRING_PATTERNS), name="pattern_valid"),
        CheckConstraint(in_check("format", MATCH_FORMATS), name="format_valid"),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="day_of_week_range"),
    )

    def __repr__(self) -> str:
        return f"<RecurringMatch id={self.id} title={self.title!r} pattern={self.pattern}>"


# ─────────────────────────── 20. match_lineups (52nd table) ───────────────────────────
class MatchLineup(Base, UUIDMixin, TimestampMixin):
    """Lineup builder data — Module 14 club management. Stores formation + position assignments per side."""
    __tablename__ = "match_lineups"

    match_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    formation: Mapped[str] = mapped_column(String(16), default="4-3-3", nullable=False)
    captain_user_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    set_by: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    positions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # [{user_id, slot, x_pct, y_pct}]
    bench: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("match_id", "side", name="uq_match_side_lineup"),
        CheckConstraint(in_check("side", SIDES), name="side_valid"),
    )

    def __repr__(self) -> str:
        return f"<MatchLineup match={self.match_id} side={self.side} formation={self.formation}>"
