"""
Referees Router — /referees/*

GET  /referees/var/{match_id}   → VAR replay clips for a match
POST /referees/report           → submit official match report
GET  /referees/dashboard        → referee-specific dashboard
"""
from __future__ import annotations

import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.models.match import Match, MatchEvent
from app.models.user import RoleEnum, User
from app.schemas.match import MatchEventOut

log = logging.getLogger(__name__)
router = APIRouter()

DBDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("/var/{match_id}")
async def get_var_clips(
    match_id: uuid.UUID,
    db: DBDep,
    _user: Annotated[User, Depends(require_role(RoleEnum.referee, RoleEnum.admin))],
):
    """Return all VAR-relevant events (OFFSIDE, FOUL, HANDBALL) for a match."""
    var_types = {"OFFSIDE", "FOUL", "HANDBALL", "PENALTY", "RED_CARD"}
    result = await db.execute(
        select(MatchEvent)
        .where(MatchEvent.match_id == match_id, MatchEvent.event_type.in_(var_types))
        .order_by(MatchEvent.created_at)
    )
    events = result.scalars().all()

    # In production, each event has a clip_url from MediaConvert.
    # Locally we return a placeholder HLS URL.
    from app.core.config import settings
    placeholder_hls = f"http://localhost:4566/{settings.PROCESSED_VIDEO_BUCKET}/placeholder/playlist.m3u8"

    return {
        "match_id": str(match_id),
        "var_events": [
            {
                **MatchEventOut.model_validate(e).model_dump(),
                "clip_hls_url": placeholder_hls,
                "confidence": 0.97,
            }
            for e in events
        ],
    }


@router.post("/report")
async def submit_report(
    body: dict,
    _user: Annotated[User, Depends(require_role(RoleEnum.referee))],
):
    """Submit official post-match report. In production: writes to S3 + PostgreSQL."""
    return {"message": "Report submitted", "report_id": str(uuid.uuid4()), "data": body}


@router.get("/dashboard")
async def referee_dashboard(
    db: DBDep,
    user: Annotated[User, Depends(require_role(RoleEnum.referee, RoleEnum.admin))],
):
    from app.services.dashboard_service import get_referee_dashboard
    return await get_referee_dashboard(user, db)
