"""Async DB session — yields AsyncSession bound to the global engine."""
from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://localhost/footbail")

# SQLite (test harness) doesn't accept `pool_size` / `max_overflow`.
_engine_kwargs: dict = {"echo": False, "pool_pre_ping": True}
if not DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(pool_size=10, max_overflow=10, pool_recycle=1800)

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency — opens an async session per request."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
