"""Match endpoint tests."""
import pytest
from datetime import datetime, timezone


MATCH_PAYLOAD = {
    "home_team": "FC Andheri",
    "away_team": "Bandra Boyz",
    "scheduled_at": datetime.now(timezone.utc).isoformat(),
    "city": "Mumbai",
    "max_players": 22,
}


@pytest.mark.asyncio
async def test_list_matches_requires_auth(client):
    r = await client.get("/matches")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_and_list_matches(client, admin_token):
    auth = {"Authorization": f"Bearer {admin_token}"}

    r = await client.post("/matches", json=MATCH_PAYLOAD, headers=auth)
    assert r.status_code == 201
    match = r.json()
    assert match["home_team"] == "FC Andheri"
    match_id = match["id"]

    r2 = await client.get("/matches", headers=auth)
    assert r2.status_code == 200
    data = r2.json()
    assert data["total"] >= 1
    assert any(m["id"] == match_id for m in data["items"])


@pytest.mark.asyncio
async def test_get_match_detail(client, admin_token):
    auth = {"Authorization": f"Bearer {admin_token}"}
    r = await client.post("/matches", json=MATCH_PAYLOAD, headers=auth)
    match_id = r.json()["id"]

    r2 = await client.get(f"/matches/{match_id}", headers=auth)
    assert r2.status_code == 200
    assert r2.json()["id"] == match_id


@pytest.mark.asyncio
async def test_player_cannot_create_match(client, player_token):
    auth = {"Authorization": f"Bearer {player_token}"}
    r = await client.post("/matches", json=MATCH_PAYLOAD, headers=auth)
    assert r.status_code == 403
