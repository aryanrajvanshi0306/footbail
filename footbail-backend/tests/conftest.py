"""pytest fixtures — full async test setup with SQLite in-memory DB."""
from __future__ import annotations

import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

# Use SQLite for tests — no Postgres required
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        import app.models  # noqa: F401  ← register models
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """Async HTTP client with DB dependency overridden to the test session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()


# ─── Auth helpers ─────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def player_token(client, db_session):
    """Register a player, return bearer token."""
    # Send OTP
    r = await client.post("/auth/otp/send", json={"phone": "9000000001", "role": "player"})
    assert r.status_code == 200
    otp = r.json().get("dev_otp", "123456")

    # Verify OTP → token pair
    r2 = await client.post("/auth/verify-otp", json={
        "phone": "9000000001", "otp": otp, "role": "player"
    })
    assert r2.status_code == 200
    return r2.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client, db_session):
    """Register an admin, return bearer token."""
    r = await client.post("/auth/otp/send", json={"phone": "9000000002", "role": "admin"})
    otp = r.json().get("dev_otp", "123456")
    r2 = await client.post("/auth/verify-otp", json={
        "phone": "9000000002", "otp": otp, "role": "admin"
    })
    return r2.json()["access_token"]
