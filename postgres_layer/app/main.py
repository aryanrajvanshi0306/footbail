"""FastAPI app entrypoint with lifespan — Layer 1B.

Startup: PING Redis, seed feature flags, log readiness.
Shutdown: close Redis pool gracefully.

Routes are mounted in Layer 2+ — this layer only exposes /healthz.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.cache.client import init_cache, close_cache, get_cache
from app.services.feature_flags import seed_feature_flags

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("footbail.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan — startup/shutdown hooks."""
    # ── STARTUP ──
    log.info("footbAIl.in API starting · env=%s", os.environ.get("APP_ENV", "dev"))

    # 1. Connect Redis (singleton)
    cache = await init_cache()
    pong = await cache.ping()
    if not pong:
        raise RuntimeError("Redis PING failed at startup — refusing to start")
    log.info("✓ Redis connected")

    # 2. Seed feature flags (idempotent — only adds missing entries)
    seeded = await seed_feature_flags(cache)
    log.info("✓ Feature flags ready · %d new (12 total)", seeded)

    log.info("footbAIl.in API READY")

    try:
        yield
    finally:
        # ── SHUTDOWN ──
        log.info("footbAIl.in API shutting down")
        await close_cache()
        log.info("✓ Redis pool closed")


app = FastAPI(
    title="footbAIl.in API",
    description="India's AI-powered digital football OS",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/healthz", tags=["meta"])
async def healthz() -> dict:
    """Liveness + readiness probe."""
    cache = get_cache()
    redis_ok = await cache.ping()
    return {
        "status": "ok" if redis_ok else "degraded",
        "redis": redis_ok,
        "version": app.version,
    }


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "name": "footbAIl.in",
        "tagline": "India's AI-powered digital football OS",
        "docs": "/docs",
    }


# Routes for Layer 2+ are imported here later, e.g.:
#   from app.api.v2 import auth, users, matches, ...
#   app.include_router(auth.router, prefix="/v2/auth", tags=["auth"])
