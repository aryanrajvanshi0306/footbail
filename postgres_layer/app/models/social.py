"""Section G — Social (5 tables).
27. social_posts
28. post_reactions
29. post_comments
30. communities
31. community_members
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
from app.models.enums import (
    POST_TYPES, REACTION_TYPES, COMMUNITY_TYPES, COMMUNITY_MEMBER_ROLES,
    CITIES, in_check,
)


# ─────────────────────────── 27. social_posts ───────────────────────────
class SocialPost(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "social_posts"

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_type: Mapped[str] = mapped_column(String(16), default="text", nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    match_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("matches.id", ondelete="SET NULL"), nullable=True, index=True)
    community_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("communities.id", ondelete="SET NULL"), nullable=True, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    mention_user_ids: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    reaction_counts: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    reactions: Mapped[List["PostReaction"]] = relationship(back_populates="post", lazy="selectin", cascade="all, delete-orphan")
    comments: Mapped[List["PostComment"]] = relationship(back_populates="post", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(in_check("post_type", POST_TYPES), name="post_type_valid"),
        CheckConstraint(f"city IS NULL OR {in_check('city', CITIES)}", name="city_valid"),
        Index("ix_social_posts_user_created", "user_id", "created_at"),
        Index("ix_social_posts_match_type", "match_id", "post_type"),
    )

    def __repr__(self) -> str:
        return f"<SocialPost id={self.id} user={self.user_id} type={self.post_type}>"


# ─────────────────────────── 28. post_reactions ───────────────────────────
class PostReaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "post_reactions"

    post_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reaction: Mapped[str] = mapped_column(String(12), nullable=False)

    post: Mapped["SocialPost"] = relationship(back_populates="reactions", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_user_reaction"),
        CheckConstraint(in_check("reaction", REACTION_TYPES), name="reaction_valid"),
    )

    def __repr__(self) -> str:
        return f"<PostReaction post={self.post_id} user={self.user_id} r={self.reaction}>"


# ─────────────────────────── 29. post_comments ───────────────────────────
class PostComment(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "post_comments"

    post_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_comment_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("post_comments.id", ondelete="CASCADE"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    post: Mapped["SocialPost"] = relationship(back_populates="comments", lazy="selectin")

    def __repr__(self) -> str:
        return f"<PostComment post={self.post_id} user={self.user_id}>"


# ─────────────────────────── 30. communities ───────────────────────────
class Community(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "communities"

    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(16), default="city", nullable=False, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    club_id: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True), ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True)
    accent_color: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    privacy: Mapped[str] = mapped_column(String(16), default="public", nullable=False)
    created_by: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    members: Mapped[List["CommunityMember"]] = relationship(back_populates="community", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(in_check("type", COMMUNITY_TYPES), name="type_valid"),
        CheckConstraint(f"city IS NULL OR {in_check('city', CITIES)}", name="city_valid"),
        CheckConstraint("privacy IN ('public','private','invite_only')", name="privacy_valid"),
    )

    def __repr__(self) -> str:
        return f"<Community id={self.id} slug={self.slug} type={self.type}>"


# ─────────────────────────── 31. community_members ───────────────────────────
class CommunityMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "community_members"

    community_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), default="member", nullable=False)
    notifications_muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    community: Mapped["Community"] = relationship(back_populates="members", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("community_id", "user_id", name="uq_community_user"),
        CheckConstraint(in_check("role", COMMUNITY_MEMBER_ROLES), name="role_valid"),
    )

    def __repr__(self) -> str:
        return f"<CommunityMember c={self.community_id} u={self.user_id} role={self.role}>"
