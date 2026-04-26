"""Match, Turf, and MatchEvent Pydantic v2 schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TurfCreate(BaseModel):
    name: str
    address: str
    city: str
    latitude: float | None = None
    longitude: float | None = None
    contact_phone: str | None = None
    has_cameras: bool = False


class TurfOut(TurfCreate):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchCreate(BaseModel):
    home_team: str
    away_team: str
    scheduled_at: datetime
    turf_id: uuid.UUID | None = None
    city: str | None = None
    description: str | None = None
    max_players: int = 22


class MatchOut(BaseModel):
    id: uuid.UUID
    home_team: str
    away_team: str
    scheduled_at: datetime
    status: str
    home_score: int
    away_score: int
    city: str | None
    turf_id: uuid.UUID | None
    referee_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchListOut(BaseModel):
    items: list[MatchOut]
    total: int
    page: int
    limit: int


class MatchEventCreate(BaseModel):
    event_type: str
    player_id: uuid.UUID | None = None
    team: str | None = None
    minute: int | None = None
    metadata: dict[str, Any] | None = None


class MatchEventOut(BaseModel):
    id: uuid.UUID
    match_id: uuid.UUID
    event_type: str
    player_id: uuid.UUID | None
    team: str | None
    minute: int | None
    metadata: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
