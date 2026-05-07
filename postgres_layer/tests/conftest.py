"""pytest fixtures for Postgres Layer 2-5 tests.

Strategy:
- Postgres → swap to **SQLite in-memory** with aiosqlite. The Mapped[T] model
  surface is portable; PostgreSQL-specific JSONB / UUID columns are tested via
  type-flex fixtures (UUIDs become string-typed at sqlite level via TypeDecorator
  in `app.models.mixins`).
- Redis → swap to **fakeredis-py** which speaks the full `redis.asyncio` API
  (SETNX, ZSET, HASH, pipelines).
- HTTP   → use `httpx.AsyncClient` against the FastAPI app (no live network).

A single fixture rebuilds schema for each test (autouse=True).
"""
from __future__ import annotations

import asyncio
import os
import secrets

# Wire env BEFORE app modules import — JWT keys must exist at module-load.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")  # overridden by fakeredis
os.environ.setdefault("RAZORPAY_KEY_ID", "rzp_test_dev_key")
os.environ.setdefault("RAZORPAY_KEY_SECRET", "rzp_test_dev_secret")
os.environ.setdefault("RAZORPAY_WEBHOOK_SECRET", "rzp_test_webhook_secret")

# Generate ephemeral RSA keypair for JWT RS256 (dev only).
def _ensure_jwt_keys() -> None:
    if os.environ.get("JWT_PRIVATE_KEY_PEM") and os.environ.get("JWT_PUBLIC_KEY_PEM"):
        return
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    pk = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = pk.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    pub_pem = pk.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    os.environ["JWT_PRIVATE_KEY_PEM"] = priv_pem
    os.environ["JWT_PUBLIC_KEY_PEM"] = pub_pem


_ensure_jwt_keys()


# ─── SQLAlchemy compatibility shim: JSONB → JSON on SQLite ─────────────────
# Postgres-only types must compile to portable equivalents under the test DB.
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):  # noqa: D401
    return "JSON"


# Strip Postgres-specific regex `~` CHECK constraints when running against SQLite
# (they're enforced at app-level via app.auth.phone.validate_indian_phone too).
from sqlalchemy import event, Table


@event.listens_for(Table, "before_create")
def _strip_pg_regex_checks(target, connection, **kw):
    if connection.dialect.name != "sqlite":
        return
    from sqlalchemy import CheckConstraint
    drop = [c for c in list(target.constraints)
            if isinstance(c, CheckConstraint) and " ~ " in str(c.sqltext)]
    for c in drop:
        target.constraints.discard(c)


import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
import app.models  # noqa: F401 — register all models


# ─────────────────────────── DB ───────────────────────────
@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(
        os.environ["DATABASE_URL"],
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def db(session_factory):
    async with session_factory() as s:
        yield s


# ─────────────────────────── Cache (fakeredis) ───────────────────────────
@pytest_asyncio.fixture
async def cache():
    import fakeredis.aioredis as fr_aio
    from app.cache.client import CacheClient
    import app.cache.client as client_mod

    fake = fr_aio.FakeRedis(decode_responses=True)
    cc = CacheClient(fake)
    # Inject as the singleton
    client_mod._client = cc
    try:
        yield cc
    finally:
        client_mod._client = None
        await fake.aclose()


# ─────────────────────────── App / HTTP client ───────────────────────────
@pytest_asyncio.fixture
async def app(db, cache, session_factory):
    """Build a FastAPI app with overridden DB + cache deps; routers attached."""
    from fastapi import FastAPI
    from app.cache.client import get_cache as _get_cache_dep
    from app.db import get_db as _get_db_dep
    from app.routers import (
        auth as auth_r, players as players_r, matches as matches_r,
        pre_match as pre_match_r, oyp as oyp_r, cv as cv_r, turfs as turfs_r,
    )
    from app.services.feature_flags import seed_feature_flags

    a = FastAPI()
    a.include_router(auth_r.router)
    a.include_router(players_r.router)
    a.include_router(matches_r.router)
    a.include_router(pre_match_r.router)
    a.include_router(oyp_r.router)
    a.include_router(cv_r.router)
    a.include_router(turfs_r.router)

    async def _get_db_override():
        async with session_factory() as s:
            yield s

    a.dependency_overrides[_get_db_dep] = _get_db_override
    a.dependency_overrides[_get_cache_dep] = lambda: cache
    await seed_feature_flags(cache)
    return a


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c


# ─────────────────────────── Convenience builders ───────────────────────────
@pytest_asyncio.fixture
async def make_user(db):
    """Factory: returns coroutine that creates and returns a User row."""
    from app.models.user import User, PlayerProfile
    from app.models.wallet import Wallet
    from datetime import datetime, timezone
    from uuid import uuid4

    async def _factory(*, phone: str = None, role: str = "player", city: str = "Mumbai", name: str = "Test Player"):
        u = User(
            phone=phone or f"+9198{secrets.token_hex(4)[:8]}",
            role=role, name=name, city=city, is_active=True,
            phone_verified_at=datetime.now(timezone.utc),
        )
        db.add(u)
        await db.flush()
        if role == "player":
            db.add(PlayerProfile(user_id=u.id, position="CM", preferred_foot="right", skill_bracket="intermediate"))
        db.add(Wallet(user_id=u.id, balance_paise=0))
        await db.commit()
        await db.refresh(u)
        return u

    return _factory


@pytest_asyncio.fixture
async def issue_access_token(cache):
    """Returns a callable (user) → access_token for use in Authorization header."""
    async def _issue(user):
        from app.auth.jwt import create_access_token
        from app.services.feature_flags import get_all_flags
        flags = await get_all_flags(cache=cache)
        flag_vals = {k: v.get("tiers", {}).get("free", False) for k, v in flags.items()}
        token, _ = create_access_token(
            user_id=str(user.id), role=user.role, city=user.city,
            membership_tier="free", feature_flags=flag_vals,
        )
        return token
    return _issue


@pytest_asyncio.fixture
async def auth_header(issue_access_token):
    async def _hdr(user):
        token = await issue_access_token(user)
        return {"Authorization": f"Bearer {token}"}
    return _hdr


@pytest.fixture
def event_loop():
    """Per-test event loop — required for sqlite + fakeredis cleanup."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
