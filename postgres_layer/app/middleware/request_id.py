"""Stamps a UUID4 X-Request-ID on every request/response (mounted FIRST)."""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # stash on scope for downstream handlers
        request.scope["request_id"] = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
