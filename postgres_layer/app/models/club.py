"""Section C — Clubs (3 tables).
9. clubs
10. club_members
11. club_turfs
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, ForeignKey, Index, Integer, SmallInteger,
    String, Text, Boolean, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import CITIES, CLUB_MEMBER_ROLES, in_check


# ─────────────────────────── 9. clubs ───────────────────────────
class Club(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "clubs"

    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False, index=True)
    founder_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    accent_color: Mapped[str] = mapped_column(String(8), default="#00E676", nullable=False)
    founded_year: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    trophies_won: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    aiff_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    privacy: Mapped[str] = mapped_column(String(16), default="public", nullable=False)  # public | invite_only

    members: Mapped[List["ClubMember"]] = relationship(back_populates="club", lazy="selectin", cascade="all, delete-orphan")
    home_turfs: Mapped[List["ClubTurf"]] = relationship(back_populates="club", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(in_check("city", CITIES), name="city_valid"),
        CheckConstraint("privacy IN ('public','invite_only')", name="privacy_valid"),
    )

    def __repr__(self) -> str:
        return f"<Club id={self.id} name={self.name!r} city={self.city}>"


# ─────────────────────────── 10. club_members ───────────────────────────
class ClubMember(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "club_members"

    club_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), default="member", nullable=False)
    jersey_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    joined_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    monthly_dues_paid_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    club: Mapped["Club"] = relationship(back_populates="members", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_club_user_member"),
        UniqueConstraint("club_id", "jersey_number", name="uq_club_jersey"),
        CheckConstraint(in_check("role", CLUB_MEMBER_ROLES), name="role_valid"),
        CheckConstraint("jersey_number IS NULL OR jersey_number BETWEEN 1 AND 99", name="jersey_range"),
    )

    def __repr__(self) -> str:
        return f"<ClubMember club={self.club_id} user={self.user_id} role={self.role}>"


# ─────────────────────────── 11. club_turfs ───────────────────────────
class ClubTurf(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "club_turfs"

    club_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False, index=True)
    turf_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("turfs.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary_home: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    discount_pct: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    club: Mapped["Club"] = relationship(back_populates="home_turfs", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("club_id", "turf_id", name="uq_club_turf"),
        CheckConstraint("discount_pct BETWEEN 0 AND 100", name="discount_pct_range"),
    )

    def __repr__(self) -> str:
        return f"<ClubTurf club={self.club_id} turf={self.turf_id} home={self.is_primary_home}>"
