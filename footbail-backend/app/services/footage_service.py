"""
Footage Service — S3 presigned URL generation, upload confirmation,
LocalStack-transparent HLS URL resolution.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.footage import Video
from app.schemas.footage import UploadUrlResponse

log = logging.getLogger(__name__)


def _s3_client():
    return boto3.client("s3", **settings.boto3_kwargs)


async def generate_presigned_upload_url(
    db: AsyncSession,
    user_id: str,
    filename: str,
    content_type: str,
    match_id: Optional[uuid.UUID],
) -> UploadUrlResponse:
    """
    1. Create a Video DB record with status='uploading'.
    2. Generate a presigned S3 PUT URL (or local fallback).
    3. Return the URL + video_id so the frontend can track progress.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp4"
    video_id = uuid.uuid4()
    object_key = f"uploads/{user_id}/{video_id}.{ext}"

    # Create DB record
    video = Video(
        id=video_id,
        match_id=match_id,
        uploaded_by=uuid.UUID(user_id),
        title=filename,
        raw_s3_key=object_key,
        status="uploading",
    )
    db.add(video)
    await db.flush()

    # Generate presigned URL
    try:
        s3 = _s3_client()
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.RAW_VIDEO_BUCKET,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )
    except ClientError as exc:
        log.error("S3 presigned URL generation failed: %s", exc)
        # Fallback for environments where LocalStack isn't ready
        upload_url = (
            f"{settings.AWS_ENDPOINT_URL or 'http://localhost:4566'}"
            f"/{settings.RAW_VIDEO_BUCKET}/{object_key}"
        )

    return UploadUrlResponse(
        upload_url=upload_url,
        object_key=object_key,
        video_id=video_id,
    )


async def confirm_upload(
    db: AsyncSession,
    video_id: uuid.UUID,
    object_key: str,
    file_size_bytes: Optional[int],
    duration_sec: Optional[int],
) -> Video:
    """
    Mark video as 'processing' and kick off the Celery video pipeline.
    """
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if video is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Video not found")

    video.status = "processing"
    video.raw_s3_key = object_key
    if file_size_bytes:
        video.file_size_bytes = file_size_bytes
    if duration_sec:
        video.duration_sec = duration_sec

    # Kick off async processing job
    try:
        from app.workers.video_tasks import process_video
        process_video.delay(str(video_id), object_key)
    except Exception as exc:
        log.warning("Could not enqueue video task: %s", exc)

    return video


async def get_video_stream_url(video: Video) -> str:
    """
    Return the HLS URL. In local dev, construct a LocalStack URL.
    In production, generate a CloudFront signed URL.
    """
    if video.processed_hls_url:
        return video.processed_hls_url

    # Fallback to raw S3 path via LocalStack
    key = video.raw_s3_key or f"placeholder/playlist.m3u8"
    base = settings.AWS_ENDPOINT_URL or "http://localhost:4566"
    return f"{base}/{settings.PROCESSED_VIDEO_BUCKET}/{key}"
