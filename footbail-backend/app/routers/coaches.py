"""Coaches Router — /coaches/*"""
from __future__ import annotations

import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.models.user import RoleEnum, User
from app.schemas.auth import UserOut

log = logging.getLogger(__name__)
router = APIRouter()

DBDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=list[UserOut])
async def list_coaches(db: DBDep, _user: CurrentUser):
    """Public: list all active coaches."""
    result = await db.execute(
        select(User).where(User.role == RoleEnum.coach, User.is_active == True)  # noqa: E712
    )
    return [UserOut.model_validate(u) for u in result.scalars().all()]


@router.get("/{coach_id}", response_model=UserOut)
async def get_coach(coach_id: uuid.UUID, db: DBDep, _user: CurrentUser):
    result = await db.execute(select(User).where(User.id == coach_id, User.role == RoleEnum.coach))
    coach = result.scalar_one_or_none()
    if coach is None:
        raise HTTPException(status_code=404, detail="Coach not found")
    return UserOut.model_validate(coach)


@router.get("/dashboard/data")
async def coach_dashboard(
    db: DBDep,
    user: Annotated[User, Depends(require_role(RoleEnum.coach, RoleEnum.admin))],
):
    """Return coach-specific dashboard."""
    from app.services.dashboard_service import get_coach_dashboard
    return await get_coach_dashboard(user, db)
