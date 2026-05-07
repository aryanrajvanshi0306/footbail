"""Tests for /v2/turfs — booking pipeline + Razorpay HMAC + SETNX hold lock."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def turf(db):
    """Insert a single Mumbai turf for booking tests."""
    from app.models.turf import Turf
    t = Turf(
        name="Powai Turf Arena", owner_id=uuid4(),  # FK is RESTRICT but we don't enforce in sqlite
        city="Mumbai", address="Hiranandani Gardens, Powai",
        image_urls=["https://example.com/turf.jpg"], amenities=["floodlights", "parking"],
        formats_supported=["5v5", "7v7"], base_price_paise_per_slot=120000,
        peak_price_paise_per_slot=180000, rating=46, total_reviews=120,
        is_listed=True, has_camera=True, operating_hours={"mon": ["06:00", "23:00"]},
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


async def test_list_turfs_filters_by_city(client, turf):
    r = await client.get("/v2/turfs?city=Mumbai")
    assert r.status_code == 200, r.text
    rows = r.json()
    assert len(rows) >= 1
    assert rows[0]["name"] == "Powai Turf Arena"
    assert rows[0]["base_price_paise"] == 120000

    r2 = await client.get("/v2/turfs?city=Bangalore")
    assert r2.status_code == 200
    assert r2.json() == []


async def test_get_turf_detail(client, turf, cache):
    r = await client.get(f"/v2/turfs/{turf.id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Powai Turf Arena"
    assert body["formats_supported"] == ["5v5", "7v7"]
    # Cached on second call
    r2 = await client.get(f"/v2/turfs/{turf.id}")
    assert r2.status_code == 200


async def test_book_turf_full_flow(client, turf, make_user, auth_header, db, cache):
    """Atomic booking: SETNX lock + Razorpay order + DB rows."""
    from sqlalchemy import select
    from app.models.match import Booking, Match

    user = await make_user(phone="+919876600001", role="player", city="Mumbai")
    hdr = await auth_header(user)

    # 14:00 IST tomorrow → off-peak base price
    slot_start = (datetime.now(timezone.utc).replace(hour=8, minute=30, second=0, microsecond=0)
                  + timedelta(days=1))
    slot_end = slot_start + timedelta(minutes=60)

    r = await client.post(
        f"/v2/turfs/{turf.id}/book",
        json={
            "slot_start": slot_start.isoformat(),
            "slot_end": slot_end.isoformat(),
            "format": "5v5",
            "home_team_name": "FC Powai", "away_team_name": "Andheri United",
        },
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["payment_status"] == "pending"
    assert body["amount_paise"] == 120000   # base price (not peak)
    assert body["razorpay_order_id"].startswith("order_dev_") or body["razorpay_order_id"].startswith("order_")
    assert "booking_id" in body and "match_id" in body

    # DB rows actually written
    bk = (await db.execute(select(Booking).where(Booking.id == UUID(body["booking_id"])))).scalar_one_or_none()
    assert bk is not None
    assert bk.amount_paise == 120000
    m = (await db.execute(select(Match).where(Match.id == UUID(body["match_id"])))).scalar_one_or_none()
    assert m is not None and m.format == "5v5"


async def test_book_turf_setnx_hold_lock_prevents_race(client, turf, make_user, auth_header, cache):
    """Second concurrent booking on the same slot → 409 slot_locked."""
    user = await make_user(phone="+919876600002", role="player")
    hdr = await auth_header(user)

    slot_start = (datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
                  + timedelta(days=2))
    slot_end = slot_start + timedelta(minutes=60)

    payload = {
        "slot_start": slot_start.isoformat(), "slot_end": slot_end.isoformat(),
        "format": "5v5", "home_team_name": "FC A", "away_team_name": "FC B",
    }

    r1 = await client.post(f"/v2/turfs/{turf.id}/book", json=payload, headers=hdr)
    assert r1.status_code == 201, r1.text

    # Lock should still be live for 5 min — second attempt collides
    user2 = await make_user(phone="+919876600003", role="player")
    hdr2 = await auth_header(user2)
    r2 = await client.post(f"/v2/turfs/{turf.id}/book", json=payload, headers=hdr2)
    assert r2.status_code == 409
    assert "slot_locked" in r2.text


async def test_book_turf_idempotency_key_replays_response(client, turf, make_user, auth_header):
    user = await make_user(phone="+919876600004", role="player")
    hdr = {**(await auth_header(user)), "Idempotency-Key": "abc-123-xyz"}
    slot_start = (datetime.now(timezone.utc).replace(hour=11, minute=0, second=0, microsecond=0)
                  + timedelta(days=3))
    slot_end = slot_start + timedelta(minutes=60)
    payload = {
        "slot_start": slot_start.isoformat(), "slot_end": slot_end.isoformat(),
        "format": "5v5", "home_team_name": "Idempo FC", "away_team_name": "Replay FC",
    }
    r1 = await client.post(f"/v2/turfs/{turf.id}/book", json=payload, headers=hdr)
    assert r1.status_code == 201
    booking1 = r1.json()
    r2 = await client.post(f"/v2/turfs/{turf.id}/book", json=payload, headers=hdr)
    assert r2.status_code == 201   # replay
    assert r2.json()["booking_id"] == booking1["booking_id"]


async def test_peak_pricing_after_18_ist(client, turf, make_user, auth_header):
    user = await make_user(phone="+919876600005", role="player")
    hdr = await auth_header(user)
    # 19:00 IST = 13:30 UTC → is_peak true
    slot_start = (datetime.now(timezone.utc).replace(hour=13, minute=30, second=0, microsecond=0)
                  + timedelta(days=4))
    slot_end = slot_start + timedelta(minutes=60)
    r = await client.post(
        f"/v2/turfs/{turf.id}/book",
        json={"slot_start": slot_start.isoformat(), "slot_end": slot_end.isoformat(),
              "format": "5v5", "home_team_name": "Peak FC", "away_team_name": "Off Peak FC"},
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    assert r.json()["amount_paise"] == 180000   # peak price


async def test_verify_payment_signature_via_route(client, turf, make_user, auth_header, db):
    from sqlalchemy import select
    from app.models.match import Booking
    from app.services.razorpay import sign_order_payment

    user = await make_user(phone="+919876600006", role="player")
    hdr = await auth_header(user)
    slot_start = (datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
                  + timedelta(days=5))
    slot_end = slot_start + timedelta(minutes=60)
    r = await client.post(
        f"/v2/turfs/{turf.id}/book",
        json={"slot_start": slot_start.isoformat(), "slot_end": slot_end.isoformat(),
              "format": "5v5", "home_team_name": "FC Sig", "away_team_name": "FC Verify"},
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    booking_id = r.json()["booking_id"]
    order_id = r.json()["razorpay_order_id"]

    payment_id = "pay_test_abc123"
    sig = sign_order_payment(order_id, payment_id)
    rv = await client.post(
        f"/v2/bookings/{booking_id}/verify",
        json={"razorpay_order_id": order_id, "razorpay_payment_id": payment_id,
              "razorpay_signature": sig},
        headers=hdr,
    )
    assert rv.status_code == 200, rv.text
    assert rv.json()["status"] == "paid"
    assert rv.json()["qr_token"]

    # Tampered signature
    bk = (await db.execute(select(Booking).where(Booking.id == UUID(booking_id)))).scalar_one()
    assert bk.payment_status == "paid"


async def test_verify_payment_rejects_bad_signature(client, turf, make_user, auth_header):
    user = await make_user(phone="+919876600007", role="player")
    hdr = await auth_header(user)
    slot_start = (datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
                  + timedelta(days=6))
    slot_end = slot_start + timedelta(minutes=60)
    r = await client.post(
        f"/v2/turfs/{turf.id}/book",
        json={"slot_start": slot_start.isoformat(), "slot_end": slot_end.isoformat(),
              "format": "5v5", "home_team_name": "FC Bad", "away_team_name": "FC Sig"},
        headers=hdr,
    )
    booking_id = r.json()["booking_id"]
    order_id = r.json()["razorpay_order_id"]
    rv = await client.post(
        f"/v2/bookings/{booking_id}/verify",
        json={"razorpay_order_id": order_id, "razorpay_payment_id": "pay_tampered",
              "razorpay_signature": "deadbeef" * 8},
        headers=hdr,
    )
    assert rv.status_code == 400


async def test_razorpay_webhook_signature_verification():
    """Direct unit test of webhook HMAC."""
    from app.services.razorpay import verify_webhook_signature, _webhook_secret
    import hmac as _hmac, hashlib

    body = json.dumps({"event": "payment.captured", "id": "evt_xyz"}).encode()
    expected_sig = _hmac.new(_webhook_secret(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(body, expected_sig)
    assert not verify_webhook_signature(body, "x" * 64)


async def test_razorpay_webhook_payment_captured_marks_booking_paid(client, turf, make_user, auth_header, db):
    """End-to-end webhook → booking flips to 'paid'."""
    from sqlalchemy import select
    from app.models.match import Booking
    from app.services.razorpay import _webhook_secret
    import hmac as _hmac, hashlib

    user = await make_user(phone="+919876600008", role="player")
    hdr = await auth_header(user)
    slot_start = (datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
                  + timedelta(days=7))
    slot_end = slot_start + timedelta(minutes=60)
    r = await client.post(
        f"/v2/turfs/{turf.id}/book",
        json={"slot_start": slot_start.isoformat(), "slot_end": slot_end.isoformat(),
              "format": "5v5", "home_team_name": "FC Hook", "away_team_name": "FC Cap"},
        headers=hdr,
    )
    booking_id = r.json()["booking_id"]
    order_id = r.json()["razorpay_order_id"]

    body = json.dumps({
        "id": "evt_hook_001", "event": "payment.captured",
        "payload": {"payment": {"entity": {"order_id": order_id, "id": "pay_hook_xyz"}}},
    }).encode()
    sig = _hmac.new(_webhook_secret(), body, hashlib.sha256).hexdigest()
    rw = await client.post(
        "/v2/payments/razorpay/webhook",
        content=body,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
    )
    assert rw.status_code == 200, rw.text
    bk = (await db.execute(select(Booking).where(Booking.id.in_([booking_id])))).scalar_one()
    assert bk.payment_status == "paid"
    assert bk.qr_token is not None


async def test_book_turf_requires_auth(client, turf):
    slot_start = datetime.now(timezone.utc) + timedelta(days=1)
    slot_end = slot_start + timedelta(minutes=60)
    r = await client.post(
        f"/v2/turfs/{turf.id}/book",
        json={"slot_start": slot_start.isoformat(), "slot_end": slot_end.isoformat(),
              "format": "5v5", "home_team_name": "X", "away_team_name": "Y"},
    )
    assert r.status_code == 401


async def test_book_turf_unsupported_format_rejected(client, turf, make_user, auth_header):
    user = await make_user(phone="+919876600010", role="player")
    hdr = await auth_header(user)
    slot_start = (datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)
                  + timedelta(days=8))
    slot_end = slot_start + timedelta(minutes=60)
    r = await client.post(
        f"/v2/turfs/{turf.id}/book",
        json={"slot_start": slot_start.isoformat(), "slot_end": slot_end.isoformat(),
              "format": "11v11",  # turf only supports 5v5/7v7
              "home_team_name": "A", "away_team_name": "B"},
        headers=hdr,
    )
    assert r.status_code == 409
