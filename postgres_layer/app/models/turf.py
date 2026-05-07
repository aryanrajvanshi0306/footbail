"""Section B — Turfs (2 tables).
7. turfs
8. turf_reviews
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, ForeignKey, Index, Integer, Numeric,
    SmallInteger, String, Text, Boolean, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import CITIES, in_check


# ─────────────────────────── 7. turfs ───────────────────────────
class Turf(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "turfs"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    pincode: Mapped[Optional[str]] = mapped_column(String(8), nullable=True, index=True)
    lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    image_urls: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    amenities: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # ["floodlights","parking","showers"]
    surface_type: Mapped[str] = mapped_column(String(20), default="artificial_grass", nullable=False)
    formats_supported: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # ["5v5","7v7"]
    base_price_paise_per_slot: Mapped[int] = mapped_column(Integer, default=120000, nullable=False)  # ₹1200
    peak_price_paise_per_slot: Mapped[int] = mapped_column(Integer, default=180000, nullable=False)  # ₹1800
    rating: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)  # 0-50
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_listed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_camera: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    camera_stream_key: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    operating_hours: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)  # {"mon": ["06:00","23:00"]}

    reviews: Mapped[List["TurfReview"]] = relationship(back_populates="turf", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(in_check("city", CITIES), name="city_valid"),
        CheckConstraint("base_price_paise_per_slot >= 0 AND peak_price_paise_per_slot >= 0", name="price_non_neg"),
        CheckConstraint("rating BETWEEN 0 AND 50", name="rating_range"),
    )

    def __repr__(self) -> str:
        return f"<Turf id={self.id} name={self.name!r} city={self.city}>"


# ─────────────────────────── 8. turf_reviews ───────────────────────────
class TurfReview(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "turf_reviews"

    turf_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("turfs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photos: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    is_verified_booking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    turf: Mapped["Turf"] = relationship(back_populates="reviews", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("turf_id", "user_id", name="uq_turf_user_review"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating_1_5"),
    )

    def __repr__(self) -> str:
        return f"<TurfReview turf={self.turf_id} user={self.user_id} rating={self.rating}>"
