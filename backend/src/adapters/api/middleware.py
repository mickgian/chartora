"""Middleware for API request/response logging and monitoring."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Logs response time, query params, and content length for every request."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start = time.perf_counter()
        query = str(request.query_params) if request.query_params else ""

        logger.info(
            "[REQUEST] %s %s%s",
            request.method,
            request.url.path,
            f"?{query}" if query else "",
        )

        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        content_length = response.headers.get("content-length", "unknown")
        logger.info(
            "[RESPONSE] %s %s -> status=%d content_length=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            content_length,
            duration_ms,
        )

        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
        return response
