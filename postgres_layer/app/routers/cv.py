"""/v2/cv — public Digital CV. No auth guard. WeasyPrint PDF."""
from __future__ import annotations

import uuid as uuidlib
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import optional_user, get_current_user
from app.cache.client import CacheClient, get_cache
from app.db import get_db
from app.models.ai_data import OypProfile
from app.models.club import Club, ClubMember
from app.models.gamification import Achievement, PlayerAchievement
from app.models.match import MatchPlayerStat
from app.models.user import PlayerProfile, User
from app.models.video import VideoClip

router = APIRouter(prefix="/v2/cv", tags=["cv"])


@router.get("/{user_id}")
async def public_cv(
    user_id: uuidlib.UUID,
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
    _: Optional[User] = Depends(optional_user),  # auth NOT required
):
    cache_key = f"cv:{user_id}"
    cached = await cache.get_json(cache_key)
    if cached:
        return cached

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user or user.deleted_at is not None:
        raise HTTPException(404, "Player not found")
    profile = (await db.execute(select(PlayerProfile).where(PlayerProfile.user_id == user_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Player profile not found")
    oyp = (await db.execute(select(OypProfile).where(OypProfile.user_id == user_id))).scalar_one_or_none()

    # Career stats
    stats = (await db.execute(select(MatchPlayerStat).where(MatchPlayerStat.user_id == user_id))).scalars().all()
    career = {
        "matches": len(stats),
        "goals": sum(s.goals for s in stats),
        "assists": sum(s.assists for s in stats),
        "minutes": sum(s.minutes_played for s in stats),
        "clean_sheets": sum(1 for s in stats if s.clean_sheet),
    }

    # Achievements (top 6)
    ach_rows = (await db.execute(
        select(Achievement, PlayerAchievement)
        .join(PlayerAchievement, PlayerAchievement.achievement_id == Achievement.id)
        .where(PlayerAchievement.user_id == user_id)
        .order_by(desc(PlayerAchievement.unlocked_at))
        .limit(6)
    )).all()
    top_achievements = [
        {"code": a.code, "name": a.name, "rarity": a.rarity,
         "unlocked_at": pa.unlocked_at.isoformat()} for a, pa in ach_rows
    ]

    # Club history
    club_rows = (await db.execute(
        select(Club, ClubMember)
        .join(ClubMember, ClubMember.club_id == Club.id)
        .where(ClubMember.user_id == user_id, ClubMember.deleted_at.is_(None))
        .order_by(desc(ClubMember.created_at))
    )).all()
    club_history = [
        {"club_id": str(c.id), "name": c.name, "city": c.city, "logo_url": c.logo_url,
         "role": cm.role, "jersey_number": cm.jersey_number} for c, cm in club_rows
    ]

    # Public clips
    clips = (await db.execute(
        select(VideoClip).where(VideoClip.primary_user_id == user_id).order_by(desc(VideoClip.created_at)).limit(8)
    )).scalars().all()
    public_clips = [
        {"id": str(v.id), "type": v.type, "title": v.title, "thumbnail_url": v.thumbnail_url,
         "clip_url": v.clip_url, "share_count": v.share_count} for v in clips
    ]

    payload = {
        "profile": {
            "id": str(user.id), "name": user.name, "city": user.city,
            "avatar_url": user.avatar_url, "bio": user.bio,
            "aiff_player_id": getattr(profile, "aiff_player_id", None),
        },
        "fifa_card": {
            "overall": profile.overall, "position": profile.position,
            "tier": profile.card_tier,
            "attributes": {"pac": profile.pac, "sho": profile.sho, "pas": profile.pas,
                           "dri": profile.dri, "def": profile.defn, "phy": profile.phy},
        },
        "oyp": {"archetype": oyp.archetype_label, "confidence": oyp.confidence} if oyp else None,
        "dna": (oyp.style_dna if oyp else {}),
        "stats": career,
        "radar_data": {"pac": profile.pac, "sho": profile.sho, "pas": profile.pas,
                       "dri": profile.dri, "def": profile.defn, "phy": profile.phy},
        "form_indicator": {"streak_days": profile.streak_days, "consistency": profile.consistency},
        "top_achievements": top_achievements,
        "club_history": club_history,
        "public_clips": public_clips,
    }
    await cache.set_json(cache_key, payload, ttl=600)
    return payload


@router.get("/{user_id}/generate-pdf")
async def generate_pdf(
    user_id: uuidlib.UUID,
    me: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    if str(me.id) != str(user_id) and me.role != "admin":
        raise HTTPException(403, "Cannot generate another player's CV")

    cv = await public_cv(user_id, db, cache, None)  # type: ignore[arg-type]

    # WeasyPrint render — best-effort; degrade to placeholder URL if not available
    try:
        from weasyprint import HTML, CSS  # type: ignore
        import boto3, io, os, time
        html = _render_cv_html(cv)
        pdf_bytes = HTML(string=html).write_pdf()
        bucket = os.environ.get("S3_BUCKET_CV", "footbail-cv")
        key = f"cv/{user_id}/{int(time.time())}.pdf"
        boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=pdf_bytes, ContentType="application/pdf")
        url = boto3.client("s3").generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=3600,
        )
        return {"pdf_url": url}
    except Exception:
        return {"pdf_url": f"/v2/cv/{user_id}.pdf", "deferred": True}


def _render_cv_html(cv: dict) -> str:
    """Minimal A4 HTML for WeasyPrint. Dark navy bg, white text."""
    p = cv["profile"]; card = cv["fifa_card"]; stats = cv["stats"]
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>
    @page {{ size: A4; margin: 16mm; background:#0A0F1E; }}
    body {{ font-family: 'DM Sans', sans-serif; color:#F1F5F9; background:#0A0F1E; }}
    h1 {{ font-size: 28pt; margin-bottom: 0; }}
    .meta {{ color:#94A3B8; font-size: 10pt; }}
    .ovr {{ font-size: 48pt; font-weight: 800; color:#00E676; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8mm; }}
    .stat {{ border: 1px solid rgba(255,255,255,0.1); padding: 4mm; }}
    </style></head><body>
      <h1>{p['name']}</h1>
      <div class='meta'>{p['city']} · {card['position']} · footbAIl.in Digital CV</div>
      <div style='margin-top:6mm;'><span class='ovr'>{card['overall']}</span> · {card['tier'].upper()}</div>
      <div class='grid' style='margin-top: 8mm;'>
        <div class='stat'><b>{stats['matches']}</b><br>MATCHES</div>
        <div class='stat'><b>{stats['goals']}</b><br>GOALS</div>
        <div class='stat'><b>{stats['assists']}</b><br>ASSISTS</div>
      </div>
    </body></html>"""
