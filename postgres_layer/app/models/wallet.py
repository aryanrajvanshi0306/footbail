"""Section K — Wallet & Payments (3 tables).
43. wallets
44. wallet_transactions
45. membership_passes
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, ForeignKey, Index, Integer, SmallInteger,
    String, Text, Boolean, DateTime, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.enums import (
    WALLET_TXN_TYPES, MEMBERSHIP_TIERS, MEMBERSHIP_STATUSES, in_check,
)


# ─────────────────────────── 43. wallets ───────────────────────────
class Wallet(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wallets"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    balance_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cashback_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    held_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_credits_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_debits_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_txn_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    transactions: Mapped[List["WalletTransaction"]] = relationship(back_populates="wallet", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("balance_paise >= 0 AND cashback_paise >= 0 AND held_paise >= 0", name="balances_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<Wallet user={self.user_id} balance={self.balance_paise}>"


# ─────────────────────────── 44. wallet_transactions ───────────────────────────
class WalletTransaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wallet_transactions"

    wallet_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    running_balance_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    source_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    razorpay_ref: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    wallet: Mapped["Wallet"] = relationship(back_populates="transactions", lazy="selectin")

    __table_args__ = (
        CheckConstraint(in_check("type", WALLET_TXN_TYPES), name="type_valid"),
        CheckConstraint("amount_paise >= 0", name="amount_non_neg"),
        Index("ix_wallet_txn_wallet_created", "wallet_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<WalletTransaction wallet={self.wallet_id} type={self.type} amount={self.amount_paise}>"


# ─────────────────────────── 45. membership_passes ───────────────────────────
class MembershipPass(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "membership_passes"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(12), default="active", nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    razorpay_subscription_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    razorpay_plan_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    monthly_price_paise: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    __table_args__ = (
        CheckConstraint(in_check("tier", MEMBERSHIP_TIERS), name="tier_valid"),
        CheckConstraint(in_check("status", MEMBERSHIP_STATUSES), name="status_valid"),
        CheckConstraint("monthly_price_paise >= 0", name="price_non_neg"),
    )

    def __repr__(self) -> str:
        return f"<MembershipPass user={self.user_id} tier={self.tier} status={self.status}>"
