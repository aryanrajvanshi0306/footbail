"""Structlog JSON request logger — never logs auth headers, OTPs, full phones, card data."""
from __future__ import annotations

import logging
import time
from typing import Iterable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# Configure structlog to emit JSON
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    cache_logger_on_first_use=True,
)
log = structlog.get_logger("footbail.access")

# Headers that must NEVER hit logs
_REDACT_HEADERS: frozenset[str] = frozenset({"authorization", "cookie", "x-razorpay-signature"})
_REDACT_BODY_KEYS: Iterable[str] = ("otp", "password", "card_number", "cvv", "razorpay_payment_id")


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        rid = request.headers.get("X-Request-ID", "-")
        ip = (request.client.host if request.client else "-")
        # do NOT read body; do NOT include Authorization header
        try:
            response: Response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)
            user_id = response.headers.get("X-User-Id", "-")
            log.info(
                "request",
                request_id=rid,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                ip=ip,
            )
            return response
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            log.error(
                "request_error",
                request_id=rid,
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                ip=ip,
                error=type(exc).__name__,
            )
            raise
