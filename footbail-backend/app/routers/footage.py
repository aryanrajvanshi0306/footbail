"""
Footage Router — /footage/*

POST /footage/upload-url    → generate S3 presigned PUT URL (Player/Admin)
POST /footage/confirm       → notify backend upload complete → trigger processing
GET  /footage/{id}          → get video info + HLS URL
GET  /footage/{id}/stream   → return (signed) HLS URL
POST /footage/{id}/annotate → add timestamped annotation (Coach/Admin)
GET  /footage/{id}/annotations → list annotations
GET  /footage/my            → list authenticated user's videos
"""
from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.models.footage import Annotation, Video
from app.models.user import RoleEnum, User
from app.schemas.footage import (
    AnnotationCreate, AnnotationOut,
    UploadUrlRequest, UploadUrlResponse,
    VideoConfirmRequest, VideoOut,
)
from app.services.footage_service import (
    generate_presigned_upload_url,
    get_video_stream_url,
    confirm_upload,
)

log = logging.getLogger(__name__)
router = APIRouter()

DBDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    body: UploadUrlRequest,
    db: DBDep,
    user: Annotated[User, Depends(require_role(RoleEnum.player, RoleEnum.admin))],
):
    """Generate a presigned S3 URL for direct browser upload."""
    result = await generate_presigned_upload_url(
        db=db,
        user_id=str(user.id),
        filename=body.filename,
        content_type=body.content_type,
        match_id=body.match_id,
    )
    return result


@router.post("/confirm", response_model=VideoOut)
async def confirm_upload_endpoint(
    body: VideoConfirmRequest,
    db: DBDep,
    user: Annotated[User, Depends(require_role(RoleEnum.player, RoleEnum.admin))],
):
    """
    Called after the browser successfully PUTs the file to S3.
    Updates the DB record and kicks off the Celery processing job.
    """
    video = await confirm_upload(
        db=db,
        video_id=body.video_id,
        object_key=body.object_key,
        file_size_bytes=body.file_size_bytes,
        duration_sec=body.duration_sec,
    )
    return VideoOut.model_validate(video)


@router.get("/my", response_model=list[VideoOut])
async def my_videos(db: DBDep, user: CurrentUser, limit: int = Query(20, ge=1, le=100)):
    result = await db.execute(
        select(Video).where(Video.uploaded_by == user.id)
        .order_by(Video.created_at.desc()).limit(limit)
    )
    return [VideoOut.model_validate(v) for v in result.scalars().all()]


@router.get("/{video_id}", response_model=VideoOut)
async def get_video(video_id: uuid.UUID, db: DBDep, _user: CurrentUser):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoOut.model_validate(video)


@router.get("/{video_id}/stream")
async def stream_video(video_id: uuid.UUID, db: DBDep, _user: CurrentUser):
    """Return a (signed/direct) HLS playlist URL."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != "ready":
        raise HTTPException(status_code=409, detail=f"Video not ready (status: {video.status})")
    url = await get_video_stream_url(video)
    return {"hls_url": url, "video_id": str(video_id)}


@router.post("/{video_id}/annotate", response_model=AnnotationOut, status_code=201)
async def annotate_video(
    video_id: uuid.UUID,
    body: AnnotationCreate,
    db: DBDep,
    user: Annotated[User, Depends(require_role(RoleEnum.coach, RoleEnum.admin))],
):
    """Add a timestamped annotation (Coach/Admin only)."""
    ann = Annotation(
        video_id=video_id,
        user_id=user.id,
        timestamp_sec=body.timestamp_sec,
        comment=body.comment,
        drawing_data=body.drawing_data,
    )
    db.add(ann)
    await db.flush()
    return AnnotationOut.model_validate(ann)


@router.get("/{video_id}/annotations", response_model=list[AnnotationOut])
async def get_annotations(video_id: uuid.UUID, db: DBDep, _user: CurrentUser):
    result = await db.execute(
        select(Annotation).where(Annotation.video_id == video_id)
        .order_by(Annotation.timestamp_sec)
    )
    return [AnnotationOut.model_validate(a) for a in result.scalars().all()]
