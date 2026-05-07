"""Smoke tests — DB schema creates cleanly, models register, basic queries work."""
from __future__ import annotations

import pytest


pytestmark = pytest.mark.asyncio


async def test_schema_creates_all_52_tables(engine):
    """Base.metadata.create_all should produce every table from the models."""
    from app.models.base import Base
    table_names = set(Base.metadata.tables.keys())
    # Spot-check a few critical tables across all sections
    assert "users" in table_names
    assert "turfs" in table_names
    assert "matches" in table_names
    assert "bookings" in table_names
    assert "wallets" in table_names
    assert "match_lineups" in table_names
    assert "player_match_ratings" in table_names
    # Hand-counted: 52 tables (Layer 1A spec)
    assert len(table_names) == 52, f"Expected 52, got {len(table_names)}: {sorted(table_names)}"


async def test_feature_flags_seeded(cache):
    """seed_feature_flags creates 12 flags in the FF hash."""
    from app.services.feature_flags import get_all_flags
    flags = await get_all_flags(cache=cache)
    assert len(flags) == 12
    assert "pre_match_intelligence" in flags
    assert "ai_coach_chat" in flags
    assert "story_mode" in flags


async def test_healthz(client):
    # Smoke: healthz only mounted on the real app, not test-app.
    # Instead hit one of our routers.
    r = await client.get("/v2/turfs?city=NoSuch")
    assert r.status_code == 200
    assert r.json() == []
