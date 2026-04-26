"""Player profile and dashboard Pydantic v2 schemas."""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel


class PlayerProfileUpdate(BaseModel):
    position: str | None = None
    dominant_foot: str | None = None
    jersey_number: int | None = None
    bio: str | None = None


class PlayerProfileOut(BaseModel):
    user_id: uuid.UUID
    position: str | None
    dominant_foot: str | None
    jersey_number: int | None
    rating: float | None
    total_goals: int
    total_assists: int
    total_matches: int
    bio: str | None
    highlight_video_url: str | None

    model_config = {"from_attributes": True}


# ─── Dashboard schemas ────────────────────────────────────────────────────────

class StatCard(BaseModel):
    val: str
    label: str
    delta: str | None = None
    color: str | None = None


class MatchRecord(BaseModel):
    date: str
    opponent: str
    result: str
    score: str
    rating: float
    goals: int
    assists: int


class PlayerDashboard(BaseModel):
    stats: list[StatCard]
    recent_matches: list[MatchRecord]
    ai_insight: str
    heatmap_data: list[float]
    sparkline: list[float]


class PlayerRow(BaseModel):
    name: str
    pos: str
    rating: float
    form: Literal["↑", "→", "↓"]
    goals: int
    fatigue_pct: int


class CoachDashboard(BaseModel):
    stats: list[StatCard]
    squad: list[PlayerRow]
    next_session: dict
    ai_suggestion: str


class VARIncident(BaseModel):
    match: str
    type: str
    minute: int
    confidence_pct: float
    status: Literal["Pending", "Reviewed", "Dismissed"]


class RefereeDashboard(BaseModel):
    stats: list[StatCard]
    incidents: list[VARIncident]
    ai_status: str


class ServiceHealth(BaseModel):
    name: str
    status: str
    color: str


class AdminDashboard(BaseModel):
    stats: list[StatCard]
    recent_users: list
    aws_health: list[ServiceHealth]
    security_log: list[str]
