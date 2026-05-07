"""Section A — Identity & Profiles (6 tables).
1. users
2. player_profiles
3. coach_profiles
4. referee_profiles
5. referee_training_modules
6. referee_training_completions
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, Date, ForeignKey, Index, Integer, JSON,
    String, Text, UniqueConstraint, Boolean, SmallInteger,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import (
    USER_ROLES, CITIES, PLAYER_POSITIONS, SKILL_BRACKETS, CARD_TIERS,
    COACH_LICENSE_LEVELS, REFEREE_TIERS, in_check,
)


# ─────────────────────────── 1. users ───────────────────────────
class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)  # +91XXXXXXXXXX
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(40), nullable=False, default="Mumbai", index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    locale: Mapped[str] = mapped_column(String(8), default="en-IN", nullable=False)

    # Relationships
    player_profile: Mapped[Optional["PlayerProfile"]] = relationship(back_populates="user", lazy="selectin", uselist=False, cascade="all, delete-orphan")
    coach_profile: Mapped[Optional["CoachProfile"]] = relationship(back_populates="user", lazy="selectin", uselist=False, cascade="all, delete-orphan")
    referee_profile: Mapped[Optional["RefereeProfile"]] = relationship(back_populates="user", lazy="selectin", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(in_check("role", USER_ROLES), name="role_valid"),
        CheckConstraint(in_check("city", CITIES), name="city_valid"),
        CheckConstraint("phone ~ '^\\+91[0-9]{10}$'", name="phone_e164_india"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} role={self.role} name={self.name!r}>"


# ─────────────────────────── 2. player_profiles ───────────────────────────
class PlayerProfile(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "player_profiles"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(8), nullable=False, default="CM")
    secondary_position: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    preferred_foot: Mapped[str] = mapped_column(String(8), default="right", nullable=False)
    height_cm: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    weight_kg: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    jersey_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    # FIFA card stats — INT 0-99
    overall: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    pac: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    sho: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    pas: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    dri: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    defn: Mapped[int] = mapped_column("def", SmallInteger, default=60, nullable=False)
    phy: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)

    card_tier: Mapped[str] = mapped_column(String(8), default="bronze", nullable=False, index=True)
    skill_bracket: Mapped[str] = mapped_column(String(16), default="intermediate", nullable=False, index=True)

    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_to_next: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    consistency: Mapped[int] = mapped_column(SmallInteger, default=70, nullable=False)
    streak_days: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    is_looking_for_game: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    play_style_dna: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # {"box-to-box": 84, ...}
    public_card_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    user: Mapped["User"] = relationship(back_populates="player_profile", lazy="selectin")

    __table_args__ = (
        CheckConstraint(in_check("position", PLAYER_POSITIONS), name="position_valid"),
        CheckConstraint(in_check("card_tier", CARD_TIERS), name="card_tier_valid"),
        CheckConstraint(in_check("skill_bracket", SKILL_BRACKETS), name="skill_bracket_valid"),
        CheckConstraint("overall BETWEEN 0 AND 99", name="overall_range"),
        CheckConstraint("pac BETWEEN 0 AND 99 AND sho BETWEEN 0 AND 99 AND pas BETWEEN 0 AND 99", name="attrs_range_1"),
        CheckConstraint("dri BETWEEN 0 AND 99 AND \"def\" BETWEEN 0 AND 99 AND phy BETWEEN 0 AND 99", name="attrs_range_2"),
        CheckConstraint("xp >= 0", name="xp_non_negative"),
        Index("ix_player_profiles_skill_city", "skill_bracket", "user_id"),
        Index("ix_player_profiles_lfg_user", "is_looking_for_game", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<PlayerProfile user_id={self.user_id} OVR={self.overall} {self.position} tier={self.card_tier}>"


# ─────────────────────────── 3. coach_profiles ───────────────────────────
class CoachProfile(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "coach_profiles"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    license_level: Mapped[str] = mapped_column(String(16), default="none", nullable=False)
    specialisations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    years_experience: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hourly_rate_paise: Mapped[int] = mapped_column(Integer, default=80000, nullable=False)  # ₹800
    rating: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)  # 0-50 (×0.1 in UI)
    sessions_delivered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_accepting_bookings: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    payout_method: Mapped[str] = mapped_column(String(16), default="upi", nullable=False)
    upi_handle: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_aiff_certified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="coach_profile", lazy="selectin")

    __table_args__ = (
        CheckConstraint(in_check("license_level", COACH_LICENSE_LEVELS), name="license_level_valid"),
        CheckConstraint("hourly_rate_paise >= 0", name="hourly_rate_non_neg"),
        CheckConstraint("rating BETWEEN 0 AND 50", name="rating_range"),
    )

    def __repr__(self) -> str:
        return f"<CoachProfile user_id={self.user_id} license={self.license_level} sessions={self.sessions_delivered}>"


# ─────────────────────────── 4. referee_profiles ───────────────────────────
class RefereeProfile(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "referee_profiles"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    aiff_id: Mapped[Optional[str]] = mapped_column(String(40), unique=True, nullable=True)
    tier: Mapped[str] = mapped_column(String(8), default="L1", nullable=False, index=True)
    matches_officiated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)  # 0-50
    base_match_fee_paise: Mapped[int] = mapped_column(Integer, default=120000, nullable=False)  # ₹1,200
    is_accepting_bookings: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    upi_handle: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_match_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="referee_profile", lazy="selectin")
    completions: Mapped[List["RefereeTrainingCompletion"]] = relationship(back_populates="referee", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(in_check("tier", REFEREE_TIERS), name="tier_valid"),
        CheckConstraint("rating BETWEEN 0 AND 50", name="rating_range"),
        CheckConstraint("base_match_fee_paise >= 0", name="fee_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<RefereeProfile user_id={self.user_id} tier={self.tier} matches={self.matches_officiated}>"


# ─────────────────────────── 5. referee_training_modules ───────────────────────────
class RefereeTrainingModule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "referee_training_modules"

    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tier_required: Mapped[str] = mapped_column(String(8), default="L1", nullable=False)
    duration_min: Mapped[int] = mapped_column(SmallInteger, default=20, nullable=False)
    video_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    quiz: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # {questions: [...]}
    passing_score: Mapped[int] = mapped_column(SmallInteger, default=70, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    completions: Mapped[List["RefereeTrainingCompletion"]] = relationship(back_populates="module", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(in_check("tier_required", REFEREE_TIERS), name="tier_required_valid"),
        CheckConstraint("passing_score BETWEEN 0 AND 100", name="passing_score_range"),
    )

    def __repr__(self) -> str:
        return f"<RefereeTrainingModule code={self.code} tier={self.tier_required}>"


# ─────────────────────────── 6. referee_training_completions ───────────────────────────
class RefereeTrainingCompletion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "referee_training_completions"

    referee_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("referee_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("referee_training_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0-100
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    attempts: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(nullable=False)
    certificate_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    referee: Mapped["RefereeProfile"] = relationship(back_populates="completions", lazy="selectin")
    module: Mapped["RefereeTrainingModule"] = relationship(back_populates="completions", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("referee_id", "module_id", name="uq_referee_module"),
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
    )

    def __repr__(self) -> str:
        return f"<RefereeTrainingCompletion ref={self.referee_id} module={self.module_id} score={self.score}>"
