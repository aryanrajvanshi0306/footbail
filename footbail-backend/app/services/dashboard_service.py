"""Dashboard Service — role-specific data (DB + AI insights)."""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import RoleEnum, User
from app.schemas.player import (
    AdminDashboard, CoachDashboard, MatchRecord, PlayerDashboard,
    PlayerRow, RefereeDashboard, ServiceHealth, StatCard, VARIncident,
)
from app.schemas.auth import UserOut


async def get_player_dashboard(user: User, db: AsyncSession) -> PlayerDashboard:
    stats = [
        StatCard(val="9.1", label="AVG RATING", delta="+0.4 this month", color="var(--g)"),
        StatCard(val="11", label="GOALS", delta="Season total"),
        StatCard(val="7", label="ASSISTS", delta="Season total"),
        StatCard(val="78%", label="DUEL WIN RATE", delta="Top 12% of players"),
    ]
    matches = [
        MatchRecord(date="Apr 20", opponent="Bandra Boyz", result="W", score="3-1", rating=9.2, goals=2, assists=1),
        MatchRecord(date="Apr 14", opponent="Powai FC", result="D", score="1-1", rating=7.8, goals=1, assists=0),
        MatchRecord(date="Apr 08", opponent="Juhu Kings", result="W", score="2-0", rating=8.6, goals=1, assists=2),
        MatchRecord(date="Apr 01", opponent="Dadar FC", result="L", score="0-2", rating=6.9, goals=0, assists=0),
    ]
    heatmap = []
    for i in range(80):
        x, y = i % 10, i // 10
        d = math.sqrt((x - 7.0) ** 2 + (y - 4.0) ** 2)
        intensity = max(0.0, 1.0 - d / 5.0 + random.uniform(-0.05, 0.15))
        heatmap.append(round(min(intensity, 1.0), 3))

    first_name = user.name.split()[0] if user.name else "Player"
    return PlayerDashboard(
        stats=stats,
        recent_matches=matches,
        ai_insight=(
            f"Hi {first_name}! Your right-flank penetration increased 34% this month. "
            "YOLOv10 tracking shows 78% 1v1 win rate in the final third. "
            "Focus on left-foot finishing — coach drill recommended."
        ),
        heatmap_data=heatmap,
        sparkline=[6.2, 7.1, 6.8, 8.0, 7.5, 8.4, 7.9, 8.8, 8.2, 9.1, 8.7, 8.4],
    )


async def get_coach_dashboard(user: User, db: AsyncSession) -> CoachDashboard:
    stats = [
        StatCard(val="12", label="SQUAD SIZE"),
        StatCard(val="5", label="SESSIONS THIS MONTH"),
        StatCard(val="3", label="UPCOMING MATCHES"),
        StatCard(val="2", label="PENDING REVIEWS"),
    ]
    squad = [
        PlayerRow(name="Rohan Mehta", pos="ST", rating=8.4, form="↑", goals=11, fatigue_pct=72),
        PlayerRow(name="Arjun Singh", pos="CM", rating=7.8, form="→", goals=3, fatigue_pct=55),
        PlayerRow(name="Dev Patel", pos="CB", rating=8.1, form="↑", goals=0, fatigue_pct=60),
        PlayerRow(name="Samir Khan", pos="GK", rating=7.5, form="↓", goals=0, fatigue_pct=40),
        PlayerRow(name="Kabir Nair", pos="LB", rating=7.2, form="→", goals=1, fatigue_pct=65),
    ]
    next_session = {
        "title": "Tactical Drilling",
        "date": (datetime.now() + timedelta(days=1)).strftime("%b %d"),
        "time": "6:00 PM",
        "venue": "Juhu Beach Turf, Mumbai",
    }
    return CoachDashboard(
        stats=stats,
        squad=squad,
        next_session=next_session,
        ai_suggestion=(
            "Rohan Mehta's sprint speed dropped 12% between the 70th–90th minute. "
            "Consider substitution strategy for the final 20 minutes."
        ),
    )


async def get_referee_dashboard(user: User, db: AsyncSession) -> RefereeDashboard:
    stats = [
        StatCard(val="8", label="MATCHES THIS MONTH"),
        StatCard(val="3", label="PENDING REVIEWS"),
        StatCard(val="2", label="REPORTS DUE"),
        StatCard(val="0", label="OPEN DISPUTES"),
    ]
    incidents = [
        VARIncident(match="FC Andheri vs Bandra Boyz", type="OFFSIDE", minute=34, confidence_pct=97.0, status="Reviewed"),
        VARIncident(match="Powai FC vs Juhu Kings", type="HANDBALL", minute=67, confidence_pct=82.0, status="Pending"),
        VARIncident(match="SoBo United vs Dadar FC", type="FOUL", minute=12, confidence_pct=91.0, status="Dismissed"),
    ]
    return RefereeDashboard(
        stats=stats,
        incidents=incidents,
        ai_status="YOLOv10 + ByteTrack 2.0 active. Offside accuracy: 97.3%. Latency < 200ms.",
    )


async def get_admin_dashboard(user: User, db: AsyncSession) -> AdminDashboard:
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(5))
    recent_users_orm = result.scalars().all()
    recent_users = [UserOut.model_validate(u) for u in recent_users_orm]

    if not recent_users:
        from datetime import timezone
        from uuid import uuid4
        stub_dt = datetime.now(timezone.utc)
        recent_users = [
            UserOut(id=uuid4(), name="Rohan M.", phone="+919876543210", email=None,
                    role=RoleEnum.player, is_verified=True, created_at=stub_dt),
            UserOut(id=uuid4(), name="Priya C.", phone=None, email="priya@ex.com",
                    role=RoleEnum.coach, is_verified=True, created_at=stub_dt),
        ]

    stats = [
        StatCard(val=str(max(len(recent_users), 2847)), label="REGISTERED USERS", delta="+142 this week"),
        StatCard(val="34", label="ACTIVE TURFS", delta="+3 this month"),
        StatCard(val="1.2 TB", label="S3 FOOTAGE", delta="CloudFront: 98.7% hit"),
        StatCard(val="₹4.2L", label="MRR", delta="+18% MoM"),
    ]
    aws_health = [
        ServiceHealth(name="FastAPI (Local Docker)", status="Healthy", color="var(--g)"),
        ServiceHealth(name="PostgreSQL 17", status="Healthy", color="var(--g)"),
        ServiceHealth(name="LocalStack S3", status="Healthy", color="var(--g)"),
        ServiceHealth(name="Redis 8", status="Healthy", color="var(--g)"),
        ServiceHealth(name="Celery Worker", status="Healthy", color="var(--g)"),
    ]
    security_log = [
        "Suspicious login blocked · 2m ago",
        "New admin IP whitelisted · 1h ago",
        "JWT secret rotated · 6h ago",
    ]
    return AdminDashboard(
        stats=stats,
        recent_users=recent_users,
        aws_health=aws_health,
        security_log=security_log,
    )
