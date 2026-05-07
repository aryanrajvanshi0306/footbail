"""String enum constants for CHECK constraints.
NEVER use as Postgres ENUM types — only as Python tuples for CheckConstraint().
"""
from typing import Final, Tuple


# ── Roles ────────────────────────────────────────────────────────────
USER_ROLES: Final[Tuple[str, ...]] = ("player", "coach", "referee", "team_admin", "admin")

# ── Cities (8 anime-coded) ───────────────────────────────────────────
CITIES: Final[Tuple[str, ...]] = (
    "Mumbai", "Delhi", "Bangalore", "Hyderabad",
    "Chennai", "Kolkata", "Pune", "Kochi",
)

# ── Player ───────────────────────────────────────────────────────────
PLAYER_POSITIONS: Final[Tuple[str, ...]] = (
    "GK", "CB", "LB", "RB", "LWB", "RWB",
    "CDM", "CM", "CAM", "LM", "RM",
    "LW", "RW", "ST", "CF",
)
SKILL_BRACKETS: Final[Tuple[str, ...]] = ("casual", "intermediate", "competitive", "elite")
CARD_TIERS: Final[Tuple[str, ...]] = ("bronze", "silver", "gold", "toty")
MATCH_FORMATS: Final[Tuple[str, ...]] = ("5v5", "7v7", "9v9", "11v11")

# ── Match lifecycle ──────────────────────────────────────────────────
MATCH_STATUSES: Final[Tuple[str, ...]] = ("scheduled", "live", "complete", "cancelled", "postponed")
MATCH_EVENT_TYPES: Final[Tuple[str, ...]] = (
    "kickoff", "goal", "assist", "foul", "yellow_card", "red_card",
    "offside", "onside", "substitution", "save", "corner",
    "penalty", "var_review", "camera_on", "camera_off", "complete",
)
SIDES: Final[Tuple[str, ...]] = ("home", "away")

# ── Booking & Payment ────────────────────────────────────────────────
PAYMENT_STATUSES: Final[Tuple[str, ...]] = ("pending", "paid", "failed", "refunded", "partial")
PAYMENT_METHODS: Final[Tuple[str, ...]] = ("upi", "card", "netbanking", "wallet", "cashback", "razorpay")
WALLET_TXN_TYPES: Final[Tuple[str, ...]] = ("credit", "debit", "hold", "release", "cashback", "refund")

# ── Membership tiers ─────────────────────────────────────────────────
MEMBERSHIP_TIERS: Final[Tuple[str, ...]] = ("free", "pro", "academy")
MEMBERSHIP_STATUSES: Final[Tuple[str, ...]] = ("active", "cancelled", "expired", "trialing")

# ── Coach / Referee ──────────────────────────────────────────────────
COACH_LICENSE_LEVELS: Final[Tuple[str, ...]] = ("none", "AIFF_D", "AIFF_C", "AIFF_B", "AIFF_A", "AFC", "UEFA")
REFEREE_TIERS: Final[Tuple[str, ...]] = ("L1", "L2", "L3", "AIFF", "FIFA")
REFEREE_BOOKING_STATUSES: Final[Tuple[str, ...]] = ("offered", "accepted", "declined", "completed", "no_show")
COACH_SESSION_TYPES: Final[Tuple[str, ...]] = ("async_video", "live_zoom", "drill_pack", "playbook")
COACH_SESSION_STATUSES: Final[Tuple[str, ...]] = ("requested", "accepted", "in_progress", "delivered", "rated", "cancelled")
DRILL_DIFFICULTIES: Final[Tuple[str, ...]] = ("beginner", "intermediate", "advanced", "elite")

# ── Video pipeline ───────────────────────────────────────────────────
VIDEO_STATUSES: Final[Tuple[str, ...]] = ("uploading", "queued", "processing", "ready", "failed")
VIDEO_CLIP_TYPES: Final[Tuple[str, ...]] = ("goal", "assist", "save", "skill", "foul", "highlight", "lowlight")
AI_JOB_TYPES: Final[Tuple[str, ...]] = ("offside_detect", "heatmap", "highlights", "oyp_update", "match_report", "impact_score")
AI_JOB_STATUSES: Final[Tuple[str, ...]] = ("queued", "running", "complete", "failed", "cancelled")

# ── Social ──────────────────────────────────────────────────────────
POST_TYPES: Final[Tuple[str, ...]] = ("text", "match_invite", "match_recap", "highlight", "achievement", "lfg")
REACTION_TYPES: Final[Tuple[str, ...]] = ("boot", "gloves", "whistle", "fire", "hundred")
COMMUNITY_TYPES: Final[Tuple[str, ...]] = ("city", "club", "topic", "tournament")
COMMUNITY_MEMBER_ROLES: Final[Tuple[str, ...]] = ("member", "moderator", "admin")

# ── Gamification ─────────────────────────────────────────────────────
XP_EVENT_TYPES: Final[Tuple[str, ...]] = (
    "match_played", "goal_scored", "assist", "clean_sheet", "motm",
    "streak_bonus", "achievement_unlock", "challenge_complete",
    "first_win", "city_derby_contribution",
)
ACHIEVEMENT_RARITIES: Final[Tuple[str, ...]] = ("common", "rare", "epic", "legendary")
CHALLENGE_TYPES: Final[Tuple[str, ...]] = ("daily", "weekly", "seasonal", "city_derby")
CHALLENGE_STATUSES: Final[Tuple[str, ...]] = ("active", "completed", "expired", "abandoned")
LEADERBOARD_SCOPES: Final[Tuple[str, ...]] = ("global", "city", "club", "community")
LEADERBOARD_METRICS: Final[Tuple[str, ...]] = ("xp", "goals", "assists", "rating", "matches", "impact")

# ── Club ────────────────────────────────────────────────────────────
CLUB_MEMBER_ROLES: Final[Tuple[str, ...]] = ("captain", "vice_captain", "member", "manager")

# ── Squad polls ─────────────────────────────────────────────────────
POLL_RESPONSE_TYPES: Final[Tuple[str, ...]] = ("yes", "no", "maybe")

# ── Notifications ───────────────────────────────────────────────────
NOTIFICATION_CHANNELS: Final[Tuple[str, ...]] = ("push", "whatsapp", "sms", "email", "in_app")
NOTIFICATION_TYPES: Final[Tuple[str, ...]] = (
    "match_reminder", "match_invite", "goal_share", "card_upgrade",
    "challenge_unlock", "lfg_match", "coach_session", "payment_receipt",
    "referee_offer", "system",
)
NOTIFICATION_STATUSES: Final[Tuple[str, ...]] = ("queued", "sent", "delivered", "read", "failed")
WHATSAPP_TEMPLATES: Final[Tuple[str, ...]] = (
    "match_confirmed", "match_reminder", "post_match_recap",
    "card_upgrade", "weekly_digest", "lfg_alert", "otp",
)

# ── Recurring fixtures ──────────────────────────────────────────────
RECURRING_PATTERNS: Final[Tuple[str, ...]] = ("weekly", "biweekly", "monthly")

# ── Admin ───────────────────────────────────────────────────────────
ADMIN_INVITATION_STATUSES: Final[Tuple[str, ...]] = ("pending", "accepted", "expired", "revoked")


def in_check(col: str, values: Tuple[str, ...]) -> str:
    """Helper: builds a Postgres CHECK clause string."""
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{col} IN ({quoted})"
