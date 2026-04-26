"""
footbAIl — FastAPI Backend
Entry point: lifespan, all routers, CORS, exception handlers.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis import close_redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
log = logging.getLogger("footbail")


# ─── LIFESPAN ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup; clean up on shutdown."""
    # Import all models so SQLAlchemy registers them before create_all
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("✅  Database tables verified")
    yield
    await engine.dispose()
    await close_redis()
    log.info("⛔  Connections closed")


# ─── APP ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="footbAIl API",
    description="India's first AI-powered digital football club platform",
    version="2.0.0",
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
    lifespan=lifespan,
)

# ─── CORS ────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── GLOBAL EXCEPTION HANDLER ────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ─── ROUTERS ─────────────────────────────────────────────────────────────────

from app.routers import auth, matches, players, footage, coaches, referees, admin  # noqa: E402
from app.websocket.live_match import router as ws_router  # noqa: E402

app.include_router(auth.router,      prefix="/auth",      tags=["Auth"])
app.include_router(matches.router,   prefix="/matches",   tags=["Matches"])
app.include_router(players.router,   prefix="/players",   tags=["Players"])
app.include_router(footage.router,   prefix="/footage",   tags=["Footage"])
app.include_router(coaches.router,   prefix="/coaches",   tags=["Coaches"])
app.include_router(referees.router,  prefix="/referees",  tags=["Referees"])
app.include_router(admin.router,     prefix="/admin",     tags=["Admin"])
app.include_router(ws_router,        prefix="/ws",        tags=["WebSocket"])


# ─── HEALTH ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "env": settings.ENV, "version": "2.0.0", "local_dev": settings.LOCAL_DEV}
