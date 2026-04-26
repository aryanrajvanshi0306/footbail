"""Footage endpoint tests."""
import pytest


@pytest.mark.asyncio
async def test_upload_url_requires_player(client, player_token, admin_token):
    """Both player and admin can request an upload URL."""
    for tok in (player_token, admin_token):
        auth = {"Authorization": f"Bearer {tok}"}
        r = await client.post("/footage/upload-url", json={
            "filename": "match_clip.mp4",
            "content_type": "video/mp4",
        }, headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert "upload_url" in data
        assert "video_id" in data


@pytest.mark.asyncio
async def test_my_videos_empty(client, player_token):
    auth = {"Authorization": f"Bearer {player_token}"}
    r = await client.get("/footage/my", headers=auth)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_confirm_upload_flow(client, player_token):
    auth = {"Authorization": f"Bearer {player_token}"}
    # 1. Get presigned URL
    r1 = await client.post("/footage/upload-url", json={
        "filename": "test_video.mp4",
        "content_type": "video/mp4",
    }, headers=auth)
    assert r1.status_code == 200
    vid_id = r1.json()["video_id"]
    obj_key = r1.json()["object_key"]

    # 2. Confirm upload
    r2 = await client.post("/footage/confirm", json={
        "video_id": vid_id,
        "object_key": obj_key,
        "file_size_bytes": 1024000,
        "duration_sec": 90,
    }, headers=auth)
    assert r2.status_code == 200
    assert r2.json()["status"] == "processing"


@pytest.mark.asyncio
async def test_coach_cannot_get_upload_url(client):
    """Coach role should be rejected from upload-url endpoint."""
    from app.core.auth import create_access_token
    import uuid
    coach_tok = create_access_token(str(uuid.uuid4()), "coach", "Coach Bob")
    auth = {"Authorization": f"Bearer {coach_tok}"}
    r = await client.post("/footage/upload-url", json={
        "filename": "test.mp4", "content_type": "video/mp4"
    }, headers=auth)
    assert r.status_code == 403
