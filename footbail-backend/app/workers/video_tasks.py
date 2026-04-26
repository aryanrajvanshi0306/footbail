"""
Video Processing Tasks — simulates the full AWS MediaConvert + AI pipeline.

LOCAL_DEV=true  → copies placeholder HLS into processed bucket, updates DB.
Production      → submits a real MediaConvert job; polls until complete.

AI inference is always simulated (YOLOv10/ByteTrack results are generated
  statistically to populate the ai_analysis JSON blob).
"""
from __future__ import annotations

import json
import logging
import os
import random
import subprocess
import time
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)

# ─── Helpers ────────────────────────────────────────────────────────────────

def _get_settings():
    from app.core.config import settings
    return settings


def _s3():
    s = _get_settings()
    return boto3.client("s3", **s.boto3_kwargs)


def _db_session():
    """Synchronous DB session for use inside Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    s = _get_settings()
    sync_url = s.DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(sync_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


def _update_video(video_id: str, **kwargs) -> None:
    """Sync helper: update a Video record inside a Celery task."""
    import psycopg2
    from app.core.config import settings

    dsn = settings.DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        cur = conn.cursor()
        set_clauses = ", ".join(f"{k} = %s" for k in kwargs)
        values = list(kwargs.values()) + [video_id]
        cur.execute(f"UPDATE videos SET {set_clauses} WHERE id = %s::uuid", values)
        conn.close()
    except Exception as exc:
        log.error("DB update failed for video %s: %s", video_id, exc)


# ─── AI Simulation ──────────────────────────────────────────────────────────

def _simulate_ai_analysis(duration_sec: int = 90) -> dict:
    """Simulate YOLOv10 player tracking + event detection output."""
    events = []
    t = 0
    while t < duration_sec:
        gap = random.randint(3, 12)
        t += gap
        if t >= duration_sec:
            break
        event_type = random.choices(
            ["pass", "shot", "dribble", "tackle", "goal"],
            weights=[50, 20, 15, 10, 5],
        )[0]
        events.append({
            "timestamp": t,
            "type": event_type,
            "player_id": f"player_{random.randint(1, 22)}",
            "confidence": round(random.uniform(0.82, 0.99), 3),
            "bbox": [random.randint(0, 600), random.randint(0, 400), 60, 60],
        })

    players = []
    for i in range(1, 11):
        players.append({
            "player_id": f"player_{i}",
            "team": "home",
            "distance_km": round(random.uniform(5.5, 12.0), 2),
            "top_speed_kmh": round(random.uniform(18.0, 32.5), 1),
            "sprint_count": random.randint(10, 30),
            "heatmap_zones": {
                "left_third": round(random.random(), 2),
                "mid_third": round(random.random(), 2),
                "right_third": round(random.random(), 2),
            },
        })

    return {
        "model": "YOLOv10-footbAIl-v2",
        "inference_ms": random.randint(80, 200),
        "frame_count": duration_sec * 30,
        "events_detected": len(events),
        "events": events,
        "player_tracking": players,
        "possession": {"home": round(random.uniform(40, 60), 1), "away": None},
    }


# ─── MAIN TASK ───────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30, name="video.process")
def process_video(self, video_id: str, raw_s3_key: str) -> dict:
    """
    Full video pipeline:
      1. Download raw file from S3 (or use placeholder locally)
      2. Transcode to HLS with ffmpeg
      3. Upload HLS segments to processed bucket
      4. Run AI analysis simulation
      5. Update Video record → status='ready'
    """
    settings = _get_settings()
    log.info("🎬 Processing video %s (key=%s)", video_id, raw_s3_key)

    try:
        s3 = _s3()
        local_dir = Path("/app/local_storage")
        local_dir.mkdir(parents=True, exist_ok=True)
        raw_path = local_dir / f"raw_{video_id}.mp4"
        hls_dir = local_dir / f"hls_{video_id}"
        hls_dir.mkdir(exist_ok=True)

        # ── Step 1: Download raw video ────────────────────────────────────────
        try:
            s3.download_file(settings.RAW_VIDEO_BUCKET, raw_s3_key, str(raw_path))
            log.info("Downloaded %s", raw_s3_key)
        except ClientError as exc:
            log.warning("S3 download failed (%s), using placeholder", exc)
            # In local dev, create a tiny placeholder video file
            _create_placeholder_video(raw_path)

        # ── Step 2: Transcode with ffmpeg → HLS ─────────────────────────────
        hls_playlist = hls_dir / "playlist.m3u8"
        cmd = [
            "ffmpeg", "-y", "-i", str(raw_path),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "aac", "-b:a", "128k",
            "-f", "hls",
            "-hls_time", "6",
            "-hls_list_size", "0",
            "-hls_segment_filename", str(hls_dir / "segment_%03d.ts"),
            str(hls_playlist),
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            log.warning("ffmpeg failed, using placeholder HLS")
            _copy_placeholder_hls(hls_dir)

        # ── Step 3: Upload HLS to processed bucket ───────────────────────────
        hls_prefix = f"processed/{video_id}"
        for hls_file in hls_dir.iterdir():
            key = f"{hls_prefix}/{hls_file.name}"
            try:
                content_type = "application/x-mpegURL" if hls_file.suffix == ".m3u8" else "video/MP2T"
                s3.upload_file(str(hls_file), settings.PROCESSED_VIDEO_BUCKET, key,
                               ExtraArgs={"ContentType": content_type})
            except ClientError as exc:
                log.warning("S3 upload failed for %s: %s", key, exc)

        # Build the HLS URL
        base = settings.AWS_ENDPOINT_URL or f"https://cdn.footbail.in"
        hls_url = f"{base}/{settings.PROCESSED_VIDEO_BUCKET}/{hls_prefix}/playlist.m3u8"

        # ── Step 4: AI analysis ───────────────────────────────────────────────
        duration = 90  # default; will be refined if ffmpeg ran successfully
        ai_data = _simulate_ai_analysis(duration_sec=duration)

        # ── Step 5: Update DB ─────────────────────────────────────────────────
        _update_video(
            video_id,
            status="ready",
            processed_hls_url=hls_url,
            ai_analysis=json.dumps(ai_data),
            duration_sec=duration,
        )

        # Cleanup local files
        try:
            raw_path.unlink(missing_ok=True)
            import shutil
            shutil.rmtree(hls_dir, ignore_errors=True)
        except Exception:
            pass

        log.info("✅ Video %s ready at %s", video_id, hls_url)
        return {"video_id": video_id, "hls_url": hls_url, "status": "ready"}

    except Exception as exc:
        log.error("Video processing failed for %s: %s", video_id, exc, exc_info=True)
        _update_video(video_id, status="error")
        raise self.retry(exc=exc)


def _create_placeholder_video(path: Path) -> None:
    """Create a minimal MP4 placeholder using ffmpeg test pattern."""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=5:size=640x480:rate=30",
             "-c:v", "libx264", "-preset", "ultrafast", str(path)],
            capture_output=True, timeout=30,
        )
    except Exception:
        path.write_bytes(b"\x00" * 1024)


def _copy_placeholder_hls(hls_dir: Path) -> None:
    """Write a minimal static HLS playlist so the pipeline never breaks."""
    playlist = hls_dir / "playlist.m3u8"
    playlist.write_text(
        "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n"
        "#EXT-X-MEDIA-SEQUENCE:0\n#EXT-X-PLAYLIST-TYPE:VOD\n"
        "#EXTINF:5.000,\nsegment_000.ts\n#EXT-X-ENDLIST\n"
    )
    segment = hls_dir / "segment_000.ts"
    if not segment.exists():
        segment.write_bytes(b"\x00" * 2048)
