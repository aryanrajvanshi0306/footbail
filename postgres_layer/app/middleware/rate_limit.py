"""Redis-backed sliding-window rate limit. Unauth: 60/min/IP. Auth: 300/min/user."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.auth.jwt import decode_token
from app.cache.client import get_cache

log = logging.getLogger("footbail.ratelimit")

UNAUTH_LIMIT = 60
AUTH_LIMIT = 300
WINDOW_SEC = 60

# Paths excluded from rate limit (probes, webhooks have their own protection)
_EXEMPT = ("/healthz", "/v2/webhooks/")


def _bearer_user_id(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    try:
        payload = decode_token(auth[7:].strip(), expected_type="access")
        return payload.get("sub")
    except Exception:
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in _EXEMPT):
            return await call_next(request)

        cache = None
        try:
            cache = get_cache()
        except RuntimeError:
            return await call_next(request)  # pre-startup; allow

        user_id = _bearer_user_id(request)
        if user_id:
            key = f"rl:auth:{user_id}"
            limit = AUTH_LIMIT
        else:
            ip = request.client.host if request.client else "anon"
            key = f"rl:ip:{ip}"
            limit = UNAUTH_LIMIT

        try:
            count = await cache.increment(key, by=1, ttl=WINDOW_SEC)
        except Exception as e:
            log.warning("rate-limit redis error: %s — allowing", e)
            return await call_next(request)

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "limit": limit, "window_sec": WINDOW_SEC},
                headers={"Retry-After": str(WINDOW_SEC)},
            )
        return await call_next(request)
