"""footbAIl.in SQLAlchemy 2.1 async models — Layer 1A.

ALL 52 tables. Mapped[T] only. UUID PKs via gen_random_uuid().
INT paise for money. TIMESTAMPTZ UTC. CHECK constraints (no separate ENUM types).
Soft deletes on all user-facing tables.
"""

# Foundation
from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models import enums

# Section A — Identity & Profiles (6)
from app.models.user import (
    User,
    PlayerProfile,
    CoachProfile,
    RefereeProfile,
    RefereeTrainingModule,
    RefereeTrainingCompletion,
)

# Section B — Turfs (2)
from app.models.turf import Turf, TurfReview

# Section C — Clubs (3)
from app.models.club import Club, ClubMember, ClubTurf

# Section D — Matches & Bookings (9)
from app.models.match import (
    Match,
    Booking,
    MatchPlayer,
    MatchPlayerStat,
    MatchEvent,
    SquadPoll,
    PollResponse,
    RecurringMatch,
    MatchLineup,
)

# Section E — Player Stats (3)
from app.models.player_stats import (
    PlayerMatchRating,
    PlayerPerformanceSnapshot,
    PlayerDrillAssignment,
)

# Section F — Video Intelligence (3)
from app.models.video import Video, VideoClip, VideoAnnotation

# Section G — Social (5)
from app.models.social import (
    SocialPost,
    PostReaction,
    PostComment,
    Community,
    CommunityMember,
)

# Section H — Gamification (6)
from app.models.gamification import (
    XpEvent,
    Achievement,
    PlayerAchievement,
    Challenge,
    PlayerChallenge,
    LeaderboardSnapshot,
)

# Section I — Marketplace (2)
from app.models.coach import CoachSession, DrillLibrary

# Section J — Referee (3) — training_completions canonical in user.py
from app.models.referee import RefereeBooking, RefereeReport, RefereeVarReview

# Section K — Wallet & Payments (3)
from app.models.wallet import Wallet, WalletTransaction, MembershipPass

# Section L — Notifications (2)
from app.models.notification import NotificationLog, WhatsappMessageLog

# Section M — AI Data (3)
from app.models.ai_data import AiAnalysisJob, MatchImpactScore, OypProfile

# Section N — Admin (2)
from app.models.admin import AdminInvitation, AnalyticsEvent

__all__ = [
    "Base", "UUIDMixin", "TimestampMixin", "SoftDeleteMixin", "enums",
    # 52 tables
    "User", "PlayerProfile", "CoachProfile", "RefereeProfile",
    "RefereeTrainingModule", "RefereeTrainingCompletion",
    "Turf", "TurfReview",
    "Club", "ClubMember", "ClubTurf",
    "Match", "Booking", "MatchPlayer", "MatchPlayerStat", "MatchEvent",
    "SquadPoll", "PollResponse", "RecurringMatch", "MatchLineup",
    "PlayerMatchRating", "PlayerPerformanceSnapshot", "PlayerDrillAssignment",
    "Video", "VideoClip", "VideoAnnotation",
    "SocialPost", "PostReaction", "PostComment", "Community", "CommunityMember",
    "XpEvent", "Achievement", "PlayerAchievement",
    "Challenge", "PlayerChallenge", "LeaderboardSnapshot",
    "CoachSession", "DrillLibrary",
    "RefereeBooking", "RefereeReport", "RefereeVarReview",
    "Wallet", "WalletTransaction", "MembershipPass",
    "NotificationLog", "WhatsappMessageLog",
    "AiAnalysisJob", "MatchImpactScore", "OypProfile",
    "AdminInvitation", "AnalyticsEvent",
]
