"""/v2/turfs — Layer 5 Turf Booking Engine.

Routes:
  GET  /v2/turfs                           — list (city, format, lat/lng filter)
  GET  /v2/turfs/{turf_id}                 — detail
  GET  /v2/turfs/{turf_id}/availability    — slot availability for a date
  POST /v2/turfs/{turf_id}/book            — atomic booking w/ SETNX hold lock
                                             + idempotency-key + Razorpay order
  POST /v2/payments/razorpay/webhook       — webhook ingest (HMAC-SHA256)
  POST /v2/bookings/{booking_id}/verify    — client-side verify after Checkout
  GET  /v2/bookings/me                     — user's own bookings
"""
from __future__ import annotations

import logging
import math
import secrets
import uuid as uuidlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.cache.client import CacheClient, get_cache
from app.cache.keys import MATCH, MISC, TURF
from app.db import get_db
from app.models.match import Booking, Match
from app.models.turf import Turf
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
from app.services.razorpay import (
    DEV_MODE as RZP_DEV_MODE,
    create_order as rzp_create_order,
    public_key_id as rzp_public_key_id,
    sign_order_payment,
    verify_payment_signature,
    verify_webhook_signature,
)

log = logging.getLogger("footbail.turfs")
router = APIRouter(prefix="/v2", tags=["turfs"])


# ─────────────────────────── Schemas ───────────────────────────
class TurfListItem(BaseModel):
    id: str
    name: str
    city: str
    address: str
    pincode: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    base_price_paise: int
    peak_price_paise: int
    rating: int
    image_urls: list
    amenities: list
    formats_supported: list
    has_camera: bool
    distance_km: Optional[float] = None


class BookSlotIn(BaseModel):
    slot_start: datetime
    slot_end: datetime
    format: str = Field(default="5v5")
    home_team_name: str = Field(min_length=2, max_length=120)
    away_team_name: str = Field(default="TBD", max_length=120)
    use_wallet_paise: int = Field(default=0, ge=0)


class VerifyPaymentIn(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# ─────────────────────────── Helpers ───────────────────────────
def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lng2 - lng1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * r * math.asin(math.sqrt(a))


def _slot_iso(dt: datetime) -> str:
    """Canonical ISO key for SETNX lock — avoid microsecond mismatches."""
    return dt.replace(microsecond=0).isoformat()


def _is_peak(slot_start: datetime) -> bool:
    """18:00–22:00 IST is peak. slot_start is UTC; convert to IST then check hour."""
    ist = slot_start + timedelta(hours=5, minutes=30)
    return 18 <= ist.hour < 22


def _turf_to_card(t: Turf, distance_km: Optional[float] = None) -> dict:
    return {
        "id": str(t.id), "name": t.name, "city": t.city, "address": t.address,
        "pincode": t.pincode,
        "lat": float(t.lat) if t.lat is not None else None,
        "lng": float(t.lng) if t.lng is not None else None,
        "base_price_paise": t.base_price_paise_per_slot,
        "peak_price_paise": t.peak_price_paise_per_slot,
        "rating": t.rating, "image_urls": t.image_urls or [],
        "amenities": t.amenities or [],
        "formats_supported": t.formats_supported or [],
        "has_camera": t.has_camera,
        "distance_km": round(distance_km, 2) if distance_km is not None else None,
    }


# ─────────────────────────── Routes ───────────────────────────
@router.get("/turfs")
async def list_turfs(
    city: Optional[str] = None,
    format: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = Query(default=15, ge=0.5, le=50),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    cache_key = TURF.CITY_LIST.format(city=city or "ALL")
    if not (lat and lng):
        cached = await cache.get_json(cache_key)
        if cached:
            return cached

    stmt = select(Turf).where(Turf.is_listed.is_(True), Turf.deleted_at.is_(None))
    if city:
        stmt = stmt.where(Turf.city == city)
    rows = (await db.execute(stmt.limit(200))).scalars().all()

    out: list[dict] = []
    for t in rows:
        if format and format not in (t.formats_supported or []):
            continue
        d_km: Optional[float] = None
        if lat is not None and lng is not None and t.lat is not None and t.lng is not None:
            d_km = _haversine_km(lat, lng, float(t.lat), float(t.lng))
            if d_km > radius_km:
                continue
        out.append(_turf_to_card(t, d_km))
    if not (lat and lng):
        out.sort(key=lambda x: x["rating"], reverse=True)
        await cache.set_json(cache_key, out, ttl=TURF.CITY_LIST_TTL)
    else:
        out.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else 1e9))
    return out


@router.get("/turfs/{turf_id}")
async def get_turf(
    turf_id: uuidlib.UUID,
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    cache_key = TURF.DETAIL.format(turf_id=turf_id)
    cached = await cache.get_json(cache_key)
    if cached:
        return cached
    t = (await db.execute(select(Turf).where(Turf.id == turf_id))).scalar_one_or_none()
    if not t or t.deleted_at is not None:
        raise HTTPException(404, "Turf not found")
    payload = {
        **_turf_to_card(t),
        "operating_hours": t.operating_hours or {},
        "surface_type": t.surface_type,
        "total_reviews": t.total_reviews,
    }
    await cache.set_json(cache_key, payload, ttl=TURF.DETAIL_TTL)
    return payload


@router.get("/turfs/{turf_id}/availability")
async def turf_availability(
    turf_id: uuidlib.UUID,
    date: str = Query(..., description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    """30-min slot grid 06:00–23:00 IST. A slot is 'taken' if a non-cancelled booking
       overlaps with it OR a SETNX hold lock is active."""
    cache_key = TURF.AVAILABILITY.format(turf_id=turf_id, date=date)
    try:
        day = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(422, "Date must be YYYY-MM-DD")
    # IST window for the day
    ist_start = day - timedelta(hours=5, minutes=30) + timedelta(hours=6)   # 06:00 IST in UTC
    ist_end = ist_start + timedelta(hours=17)                                # 23:00 IST in UTC

    bookings = (await db.execute(
        select(Booking).where(
            Booking.turf_id == turf_id,
            Booking.payment_status.in_(["paid", "wallet_paid", "pending"]),
            Booking.deleted_at.is_(None),
            Booking.slot_start < ist_end,
            Booking.slot_end > ist_start,
        )
    )).scalars().all()
    booked_ranges = [(b.slot_start, b.slot_end, b.payment_status) for b in bookings]

    grid: list[dict] = []
    cur = ist_start
    while cur < ist_end:
        slot_end = cur + timedelta(minutes=30)
        # Locked? SETNX hold for this exact slot
        locked = await cache.exists(MATCH.SLOT_LOCK.format(turf_id=turf_id, slot_iso=_slot_iso(cur)))
        # Overlapping booking?
        clash = next((s for s in booked_ranges if s[0] < slot_end and s[1] > cur), None)
        grid.append({
            "slot_start_utc": cur.isoformat(),
            "slot_start_ist": (cur + timedelta(hours=5, minutes=30)).isoformat(),
            "slot_end_utc": slot_end.isoformat(),
            "is_peak": _is_peak(cur),
            "available": not locked and clash is None,
            "locked_until_checkout": bool(locked),
            "clash_status": clash[2] if clash else None,
        })
        cur = slot_end

    out = {"turf_id": str(turf_id), "date": date, "slots": grid}
    await cache.set_json(cache_key, out, ttl=TURF.AVAILABILITY_TTL)
    return out


@router.post("/turfs/{turf_id}/book", status_code=status.HTTP_201_CREATED)
async def book_turf(
    turf_id: uuidlib.UUID,
    body: BookSlotIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    """Atomic booking pipeline:
        1. Idempotency-Key replay-cache (24h)
        2. SETNX hold-lock on (turf_id, slot_start) — 5 min TTL
        3. Validate slot vs existing bookings & turf operating hours
        4. Compute price (peak vs base)
        5. Apply wallet credit if requested (running_balance, FIFO debit)
        6. Create Match + Booking rows (one transaction)
        7. Create Razorpay order — stash order_id + lock value into booking
        8. Return checkout payload — UI hands off to Razorpay Checkout JS
    """
    # 1) Idempotency
    if idempotency_key:
        idem_key = MISC.IDEMPOTENCY.format(key=f"turf-book:{user.id}:{idempotency_key}")
        cached = await cache.get_json(idem_key)
        if cached:
            return cached

    # 0) Fetch turf
    t = (await db.execute(select(Turf).where(Turf.id == turf_id))).scalar_one_or_none()
    if not t or t.deleted_at is not None or not t.is_listed:
        raise HTTPException(404, "Turf not found")
    if body.slot_end <= body.slot_start:
        raise HTTPException(422, "slot_end must be after slot_start")
    if (body.slot_end - body.slot_start).total_seconds() < 30 * 60:
        raise HTTPException(422, "Minimum slot duration is 30 minutes")
    if body.format not in (t.formats_supported or ["5v5", "7v7", "11v11"]):
        raise HTTPException(409, "Format not supported at this turf")

    # 2) SETNX hold-lock — prevents two users from racing the same slot
    lock_key = MATCH.SLOT_LOCK.format(turf_id=turf_id, slot_iso=_slot_iso(body.slot_start))
    lock_value = secrets.token_hex(8)
    if not await cache.setnx(lock_key, lock_value, ttl=MATCH.SLOT_LOCK_TTL):
        raise HTTPException(409, {"error": "slot_locked", "message": "Someone is checking out this slot — try in 5 min."})

    try:
        # 3) Validate against existing bookings (DB truth source)
        clash = (await db.execute(
            select(Booking).where(
                Booking.turf_id == turf_id,
                Booking.payment_status.in_(["paid", "wallet_paid"]),
                Booking.deleted_at.is_(None),
                Booking.slot_start < body.slot_end,
                Booking.slot_end > body.slot_start,
            )
        )).scalar_one_or_none()
        if clash:
            raise HTTPException(409, "Slot already booked")

        # 4) Pricing
        price = t.peak_price_paise_per_slot if _is_peak(body.slot_start) else t.base_price_paise_per_slot
        wallet_used = 0
        wallet: Optional[Wallet] = None
        if body.use_wallet_paise > 0:
            wallet = (await db.execute(
                select(Wallet).where(Wallet.user_id == user.id)
            )).scalar_one_or_none()
            if not wallet:
                raise HTTPException(404, "Wallet not found — onboard via /v2/auth/complete-profile")
            wallet_used = min(body.use_wallet_paise, wallet.balance_paise, price)
        final_amount = price - wallet_used

        # 5) Atomic write — Match + Booking. Wallet debit also in same txn.
        match = Match(
            home_team_name=body.home_team_name,
            away_team_name=body.away_team_name,
            turf_id=turf_id,
            creator_id=user.id,
            scheduled_at=body.slot_start,
            duration_min=int((body.slot_end - body.slot_start).total_seconds() // 60),
            format=body.format,
        )
        db.add(match)
        await db.flush()

        booking = Booking(
            match_id=match.id, user_id=user.id, turf_id=turf_id,
            slot_start=body.slot_start, slot_end=body.slot_end,
            amount_paise=price, discount_paise=wallet_used,
            final_amount_paise=final_amount,
            payment_status="wallet_paid" if final_amount == 0 else "pending",
        )
        db.add(booking)
        await db.flush()

        if wallet_used > 0 and wallet is not None:
            wallet.balance_paise -= wallet_used
            wallet.lifetime_debits_paise += wallet_used
            wallet.last_txn_at = datetime.now(timezone.utc)
            db.add(WalletTransaction(
                wallet_id=wallet.id, type="debit",
                amount_paise=wallet_used,
                running_balance_paise=wallet.balance_paise,
                source_type="booking", source_id=booking.id,
                description=f"Turf booking · {t.name}",
            ))

        # 6) Razorpay order (skip if fully paid by wallet)
        order_payload: dict = {}
        if final_amount > 0:
            try:
                order = await rzp_create_order(
                    amount_paise=final_amount,
                    receipt=str(booking.id),
                    notes={"turf_id": str(turf_id), "user_id": str(user.id),
                           "slot_start": body.slot_start.isoformat()},
                )
            except Exception as e:
                # Release lock + bail
                await cache.release_lock(lock_key, lock_value)
                await db.rollback()
                log.warning("razorpay order failed user=%s turf=%s err=%s", user.id, turf_id, e)
                raise HTTPException(502, "Payment gateway unavailable, try again")
            booking.razorpay_order_id = order["id"]
            order_payload = order

        await db.commit()
        await db.refresh(booking)

        out = {
            "booking_id": str(booking.id), "match_id": str(match.id),
            "amount_paise": final_amount, "currency": "INR",
            "razorpay_order_id": booking.razorpay_order_id,
            "razorpay_key_id": rzp_public_key_id(),
            "dev_mode": bool(order_payload.get("_dev_mode") or RZP_DEV_MODE),
            "wallet_used_paise": wallet_used,
            "qr_token": booking.qr_token,
            "payment_status": booking.payment_status,
            "lock_token": lock_value,   # client returns this on /verify to release atomically
        }
        # Bust availability cache for this date
        await cache.delete(TURF.AVAILABILITY.format(
            turf_id=turf_id, date=body.slot_start.strftime("%Y-%m-%d"),
        ))
        if idempotency_key:
            await cache.set_json(idem_key, out, ttl=MISC.IDEMPOTENCY_TTL)
        return out
    except IntegrityError as e:
        await db.rollback()
        await cache.release_lock(lock_key, lock_value)
        raise HTTPException(409, f"Booking conflict: {e.orig}")
    except HTTPException:
        # Don't release lock for 409 slot_locked — let it expire naturally
        raise
    except Exception:
        await db.rollback()
        await cache.release_lock(lock_key, lock_value)
        raise


@router.post("/bookings/{booking_id}/verify")
async def verify_booking_payment(
    booking_id: uuidlib.UUID,
    body: VerifyPaymentIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
):
    """Client posts the success payload from Razorpay Checkout JS. We HMAC-verify."""
    booking = (await db.execute(
        select(Booking).where(Booking.id == booking_id, Booking.user_id == user.id)
    )).scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")
    if booking.payment_status == "paid":
        return {"status": "already_paid", "qr_token": booking.qr_token}
    if booking.razorpay_order_id != body.razorpay_order_id:
        raise HTTPException(400, "order_id mismatch")
    if not verify_payment_signature(body.razorpay_order_id, body.razorpay_payment_id, body.razorpay_signature):
        raise HTTPException(400, "Invalid payment signature")

    booking.payment_status = "paid"
    booking.razorpay_payment_id = body.razorpay_payment_id
    booking.payment_method = "razorpay"
    booking.paid_at = datetime.now(timezone.utc)
    booking.qr_token = secrets.token_urlsafe(16)
    await db.commit()
    await db.refresh(booking)

    # Bust caches
    await cache.delete(TURF.AVAILABILITY.format(
        turf_id=booking.turf_id, date=booking.slot_start.strftime("%Y-%m-%d"),
    ))
    return {"status": "paid", "booking_id": str(booking.id), "qr_token": booking.qr_token}


@router.post("/payments/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    cache: CacheClient = Depends(get_cache),
    x_razorpay_signature: Optional[str] = Header(default=None, alias="X-Razorpay-Signature"),
):
    """Razorpay → /v2/payments/razorpay/webhook
    Events handled: payment.captured, payment.failed, refund.processed.
    Idempotent on `event.id` (Razorpay-supplied) cached 24h.
    """
    raw = await request.body()
    if not x_razorpay_signature or not verify_webhook_signature(raw, x_razorpay_signature):
        raise HTTPException(400, "Invalid webhook signature")

    import json
    try:
        evt = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(400, "Malformed webhook body")

    event_id = evt.get("id") or evt.get("event_id")
    event_type = evt.get("event")
    if event_id:
        if await cache.exists(MISC.IDEMPOTENCY.format(key=f"rzp-webhook:{event_id}")):
            return {"ok": True, "replayed": True}
        await cache.set_str(MISC.IDEMPOTENCY.format(key=f"rzp-webhook:{event_id}"),
                            "1", ttl=MISC.IDEMPOTENCY_TTL)

    if event_type == "payment.captured":
        pay = (evt.get("payload") or {}).get("payment", {}).get("entity", {})
        order_id = pay.get("order_id"); payment_id = pay.get("id")
        if order_id and payment_id:
            booking = (await db.execute(
                select(Booking).where(Booking.razorpay_order_id == order_id)
            )).scalar_one_or_none()
            if booking and booking.payment_status != "paid":
                booking.payment_status = "paid"
                booking.razorpay_payment_id = payment_id
                booking.payment_method = "razorpay"
                booking.paid_at = datetime.now(timezone.utc)
                booking.qr_token = secrets.token_urlsafe(16)
                await db.commit()
                log.info("Webhook: booking %s marked paid via webhook", booking.id)
    elif event_type == "payment.failed":
        pay = (evt.get("payload") or {}).get("payment", {}).get("entity", {})
        order_id = pay.get("order_id")
        if order_id:
            booking = (await db.execute(
                select(Booking).where(Booking.razorpay_order_id == order_id)
            )).scalar_one_or_none()
            if booking and booking.payment_status == "pending":
                booking.payment_status = "failed"
                await db.commit()
    elif event_type == "refund.processed":
        ref = (evt.get("payload") or {}).get("refund", {}).get("entity", {})
        payment_id = ref.get("payment_id")
        if payment_id:
            booking = (await db.execute(
                select(Booking).where(Booking.razorpay_payment_id == payment_id)
            )).scalar_one_or_none()
            if booking:
                booking.payment_status = "refunded"
                booking.refunded_at = datetime.now(timezone.utc)
                await db.commit()
    return {"ok": True, "event": event_type}


@router.get("/bookings/me")
async def my_bookings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Booking).where(Booking.user_id == user.id, Booking.deleted_at.is_(None))
        .order_by(Booking.created_at.desc()).limit(100)
    )).scalars().all()
    return [{
        "id": str(b.id), "match_id": str(b.match_id), "turf_id": str(b.turf_id),
        "slot_start": b.slot_start.isoformat(),
        "slot_start_ist": (b.slot_start + timedelta(hours=5, minutes=30)).isoformat(),
        "slot_end": b.slot_end.isoformat(),
        "amount_paise": b.amount_paise, "final_amount_paise": b.final_amount_paise,
        "payment_status": b.payment_status, "qr_token": b.qr_token,
        "created_at": b.created_at.isoformat(),
    } for b in rows]


# Convenience for tests + SDK introspection
__all__ = ["router"]
