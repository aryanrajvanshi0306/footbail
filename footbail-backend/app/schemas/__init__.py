"""Pydantic v2 schemas — re-export everything for convenience."""
from app.schemas.auth import (
    OTPSendRequest, OTPSendResponse, OTPVerifyRequest,
    GoogleAuthRequest, TokenPair, RefreshRequest, UserOut, MeResponse,
)
from app.schemas.match import (
    MatchCreate, MatchOut, MatchListOut,
    TurfCreate, TurfOut,
    MatchEventCreate, MatchEventOut,
)
from app.schemas.footage import (
    UploadUrlRequest, UploadUrlResponse,
    VideoConfirmRequest, VideoOut,
    AnnotationCreate, AnnotationOut,
)
from app.schemas.player import (
    PlayerProfileUpdate, PlayerProfileOut,
    StatCard, MatchRecord, PlayerDashboard,
    PlayerRow, CoachDashboard,
    VARIncident, RefereeDashboard,
    ServiceHealth, AdminDashboard,
)

__all__ = [
    "OTPSendRequest", "OTPSendResponse", "OTPVerifyRequest",
    "GoogleAuthRequest", "TokenPair", "RefreshRequest", "UserOut", "MeResponse",
    "MatchCreate", "MatchOut", "MatchListOut", "TurfCreate", "TurfOut",
    "MatchEventCreate", "MatchEventOut",
    "UploadUrlRequest", "UploadUrlResponse", "VideoConfirmRequest",
    "VideoOut", "AnnotationCreate", "AnnotationOut",
    "PlayerProfileUpdate", "PlayerProfileOut",
    "StatCard", "MatchRecord", "PlayerDashboard",
    "PlayerRow", "CoachDashboard",
    "VARIncident", "RefereeDashboard",
    "ServiceHealth", "AdminDashboard",
]
