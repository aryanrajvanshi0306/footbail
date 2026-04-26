"""
Players Router — /players/*

GET  /players/dashboard     → role-specific dashboard data
GET  /players/{id}/stats    → player stats
GET  /players/{id}/profile  → public profile (Digital CV)
PUT  /players/profile       → update own profile
"""
from __future__ import annotations

import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.models.user import RoleEnum, User
from app.models.stats import PlayerProfile
from app.schemas.player import (
    PlayerProfileOut, PlayerProfileUpdate,
    PlayerDashboard, CoachDashboard, RefereeDashboard,
)
from app.schemas.auth import UserOut
from app.services.dashboard_service import (
    get_player_dashboard, get_coach_dashboard,
    get_referee_dashboard, get_admin_dashboard,
)

log = logging.getLogger(__name__)
router = APIRouter()

DBDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/dashboard")
async def get_dashboard(user: CurrentUser, db: DBDep):
    """Return role-appropriate dashboard data."""
    role = user.role.value
    if role == "player":
        return await get_player_dashboard(user, db)
    elif role == "coach":
        return await get_coach_dashboard(user, db)
    elif role == "referee":
        return await get_referee_dashboard(user, db)
    elif role == "admin":
        return await get_admin_dashboard(user, db)
    raise HTTPException(status_code=400, detail="Unknown role")


@router.get("/{player_id}/stats")
async def get_player_stats(player_id: uuid.UUID, db: DBDep, _user: CurrentUser):
    result = await db.execute(select(User).where(User.id == player_id))
    player = result.scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return await get_player_dashboard(player, db)


@router.get("/{player_id}/profile", response_model=PlayerProfileOut)
async def get_player_profile(player_id: uuid.UUID, db: DBDep, _user: CurrentUser):
    result = await db.execute(select(PlayerProfile).where(PlayerProfile.user_id == player_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return PlayerProfileOut.model_validate(profile)


@router.put("/profile", response_model=PlayerProfileOut)
async def update_profile(
    body: PlayerProfileUpdate,
    db: DBDep,
    user: Annotated[User, Depends(require_role(RoleEnum.player, RoleEnum.admin))],
):
    result = await db.execute(select(PlayerProfile).where(PlayerProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = PlayerProfile(user_id=user.id)
        db.add(profile)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    await db.flush()
    return PlayerProfileOut.model_validate(profile)


@router.get("/list", response_model=list[UserOut])
async def list_players(
    db: DBDep,
    _user: Annotated[User, Depends(require_role(RoleEnum.coach, RoleEnum.admin))],
):
    result = await db.execute(select(User).where(User.role == RoleEnum.player, User.is_active == True))  # noqa: E712
    return [UserOut.model_validate(u) for u in result.scalars().all()]
