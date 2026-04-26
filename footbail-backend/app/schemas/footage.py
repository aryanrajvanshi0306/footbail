"""Footage and Annotation Pydantic v2 schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str = "video/mp4"
    match_id: uuid.UUID | None = None


class UploadUrlResponse(BaseModel):
    upload_url: str
    object_key: str
    video_id: uuid.UUID


class VideoConfirmRequest(BaseModel):
    video_id: uuid.UUID
    object_key: str
    file_size_bytes: int | None = None
    duration_sec: int | None = None


class VideoOut(BaseModel):
    id: uuid.UUID
    match_id: uuid.UUID | None
    uploaded_by: uuid.UUID | None
    title: str | None
    raw_s3_key: str | None
    processed_hls_url: str | None
    thumbnail_url: str | None
    status: str
    ai_analysis: dict[str, Any] | None
    duration_sec: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnnotationCreate(BaseModel):
    video_id: uuid.UUID
    timestamp_sec: int
    comment: str | None = None
    drawing_data: dict[str, Any] | None = None


class AnnotationOut(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    user_id: uuid.UUID
    timestamp_sec: int
    comment: str | None
    drawing_data: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
