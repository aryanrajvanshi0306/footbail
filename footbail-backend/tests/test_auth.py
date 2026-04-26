"""Auth endpoint tests."""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_send_otp(client):
    r = await client.post("/auth/otp/send", json={"phone": "9876543210", "role": "player"})
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    # dev_otp present because DEV_OTP_BYPASS=true in test env
    assert "dev_otp" in data or data["dev_otp"] is None


@pytest.mark.asyncio
async def test_verify_otp_and_me(client):
    r = await client.post("/auth/otp/send", json={"phone": "9111111111", "role": "player"})
    otp = r.json().get("dev_otp", "111111")

    r2 = await client.post("/auth/verify-otp", json={
        "phone": "9111111111", "otp": otp, "role": "player"
    })
    assert r2.status_code == 200
    token = r2.json()["access_token"]
    assert token

    r3 = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    me = r3.json()
    assert me["user"]["role"] == "player"


@pytest.mark.asyncio
async def test_invalid_otp(client):
    await client.post("/auth/otp/send", json={"phone": "9222222222", "role": "player"})
    r = await client.post("/auth/verify-otp", json={
        "phone": "9222222222", "otp": "000", "role": "player"
    })
    # DEV_OTP_BYPASS=true → 3-digit OTP rejected
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_role_guard(client, player_token):
    """Player must not access admin endpoints."""
    r = await client.get("/admin/users", headers={"Authorization": f"Bearer {player_token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_me_no_token(client):
    r = await client.get("/auth/me")
    assert r.status_code == 403
