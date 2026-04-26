"""
Admin Router — /admin/*

GET  /admin/metrics         → platform health dashboard
GET  /admin/users           → list all users (paginated)
PUT  /admin/users/{id}/role → change user role
DELETE /admin/users/{id}    → deactivate user
GET  /admin/turfs           → list turfs
POST /admin/turfs           → create turf
"""
from __future__ import annotations

import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.models.match import Turf
from app.models.user import RoleEnum, User
from app.schemas.auth import UserOut
from app.schemas.match import TurfCreate, TurfOut

log = logging.getLogger(__name__)
router = APIRouter()

DBDep = Annotated[AsyncSession, Depends(get_db)]
AdminOnly = Annotated[User, Depends(require_role(RoleEnum.admin))]


@router.get("/metrics")
async def get_metrics(db: DBDep, _user: AdminOnly):
    from app.services.dashboard_service import get_admin_dashboard
    # Fake admin user for dashboard
    result = await db.execute(select(User).where(User.role == RoleEnum.admin).limit(1))
    admin = result.scalar_one_or_none()
    if admin is None:
        admin = User(name="Admin", role=RoleEnum.admin, is_active=True)
    return await get_admin_dashboard(admin, db)


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: DBDep,
    _user: AdminOnly,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    role: str | None = None,
):
    q = select(User)
    if role:
        q = q.where(User.role == role)
    q = q.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    return [UserOut.model_validate(u) for u in result.scalars().all()]


@router.put("/users/{user_id}/role", response_model=UserOut)
async def change_role(user_id: uuid.UUID, body: dict, db: DBDep, _user: AdminOnly):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        target.role = RoleEnum(body["role"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=422, detail="Invalid role value")
    return UserOut.model_validate(target)


@router.delete("/users/{user_id}", status_code=204)
async def deactivate_user(user_id: uuid.UUID, db: DBDep, _user: AdminOnly):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_active = False


@router.get("/turfs", response_model=list[TurfOut])
async def list_turfs(db: DBDep, _user: AdminOnly):
    result = await db.execute(select(Turf).order_by(Turf.name))
    return [TurfOut.model_validate(t) for t in result.scalars().all()]


@router.post("/turfs", response_model=TurfOut, status_code=201)
async def create_turf(body: TurfCreate, db: DBDep, _user: AdminOnly):
    turf = Turf(**body.model_dump())
    db.add(turf)
    await db.flush()
    return TurfOut.model_validate(turf)
