"""
Matches Router — /matches/*

GET  /matches           → list with filters
POST /matches           → create (Admin)
GET  /matches/{id}      → detail
PUT  /matches/{id}      → update status/score (Admin/Referee)
POST /matches/{id}/events → add live event (Referee/Admin)
GET  /matches/{id}/events → SSE stream of live events
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.match import Match, MatchEvent
from app.models.user import RoleEnum, User
from app.schemas.match import MatchCreate, MatchEventCreate, MatchEventOut, MatchListOut, MatchOut

log = logging.getLogger(__name__)
router = APIRouter()

DBDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=MatchListOut)
async def list_matches(
    db: DBDep,
    _user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    city: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
):
    q = select(Match)
    if city:
        q = q.where(Match.city.ilike(f"%{city}%"))
    if status_filter:
        q = q.where(Match.status == status_filter)

    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    q = q.order_by(Match.scheduled_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    items = result.scalars().all()

    return MatchListOut(
        items=[MatchOut.model_validate(m) for m in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=MatchOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(RoleEnum.admin))])
async def create_match(body: MatchCreate, db: DBDep, user: CurrentUser):
    match = Match(
        home_team=body.home_team,
        away_team=body.away_team,
        scheduled_at=body.scheduled_at,
        turf_id=body.turf_id,
        city=body.city,
        description=body.description,
        max_players=body.max_players,
        created_by=user.id,
    )
    db.add(match)
    await db.flush()
    return MatchOut.model_validate(match)


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(match_id: uuid.UUID, db: DBDep, _user: CurrentUser):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return MatchOut.model_validate(match)


@router.put("/{match_id}", response_model=MatchOut)
async def update_match(
    match_id: uuid.UUID,
    body: dict,
    db: DBDep,
    user: Annotated[User, Depends(require_role(RoleEnum.admin, RoleEnum.referee))],
):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    for field in ("status", "home_score", "away_score"):
        if field in body:
            setattr(match, field, body[field])
    return MatchOut.model_validate(match)


@router.post("/{match_id}/events", response_model=MatchEventOut, status_code=201)
async def add_match_event(
    match_id: uuid.UUID,
    body: MatchEventCreate,
    db: DBDep,
    _user: Annotated[User, Depends(require_role(RoleEnum.referee, RoleEnum.admin))],
):
    event = MatchEvent(
        match_id=match_id,
        event_type=body.event_type,
        player_id=body.player_id,
        team=body.team,
        minute=body.minute,
        metadata=body.metadata,
    )
    db.add(event)
    await db.flush()

    # Publish to Redis for SSE subscribers
    r = await get_redis()
    channel = f"match:{match_id}:events"
    payload = json.dumps({
        "id": str(event.id),
        "match_id": str(match_id),
        "event_type": body.event_type,
        "team": body.team,
        "minute": body.minute,
    })
    await r.publish(channel, payload)

    return MatchEventOut.model_validate(event)


@router.get("/{match_id}/events/stream")
async def stream_match_events(match_id: uuid.UUID, _user: CurrentUser):
    """Server-Sent Events stream for live match events via Redis pub/sub."""

    async def event_generator() -> AsyncGenerator[str, None]:
        r = await get_redis()
        pubsub = r.pubsub()
        channel = f"match:{match_id}:events"
        await pubsub.subscribe(channel)
        try:
            yield f"data: {json.dumps({'type': 'connected', 'match_id': str(match_id)})}\n\n"
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
                else:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/{match_id}/events", response_model=list[MatchEventOut])
async def get_match_events(match_id: uuid.UUID, db: DBDep, _user: CurrentUser):
    """Get historical events for a match."""
    result = await db.execute(
        select(MatchEvent).where(MatchEvent.match_id == match_id).order_by(MatchEvent.created_at)
    )
    return [MatchEventOut.model_validate(e) for e in result.scalars().all()]
