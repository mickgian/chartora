"""FastAPI application factory with CORS, error handling, and routers."""

from __future__ import annotations

import logging
import sys
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.adapters.api.middleware import RequestTimingMiddleware
from src.adapters.api.routers import (
    affiliate,
    api_docs,
    auth,
    companies,
    leaderboard,
    payments,
    premium,
    rankings,
    sectors,
)
from src.config.settings import Settings
from src.infrastructure.cache import cache

# Configure structured logging on module load
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    force=True,
)

logger = logging.getLogger(__name__)

_start_time: float = time.time()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title=settings.app_name,
        description="Quantum Computing Company Leaderboard API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Store settings on app state for dependency injection
    app.state.settings = settings

    # Request timing middleware (added first so it wraps everything)
    app.add_middleware(RequestTimingMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)},
        )

    # Health check with monitoring details
    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        uptime_seconds = time.time() - _start_time
        return {
            "status": "healthy",
            "version": "0.1.0",
            "uptime_seconds": round(uptime_seconds, 1),
        }

    # Readiness probe — checks database connectivity
    @app.get("/ready", response_class=JSONResponse)
    async def readiness_check(request: Request) -> JSONResponse:
        db_ok = False
        factory = getattr(request.app.state, "session_factory", None)
        if factory is not None:
            try:
                from sqlalchemy import text

                async with factory() as session:
                    await session.execute(text("SELECT 1"))
                    db_ok = True
            except Exception:
                logger.warning("Readiness check: database unavailable")

        status = "ready" if db_ok else "not_ready"
        status_code = 200 if db_ok else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "status": status,
                "database": "connected" if db_ok else "unavailable",
            },
        )

    # Register routers
    app.include_router(leaderboard.router)
    app.include_router(companies.router)
    app.include_router(rankings.router)
    app.include_router(affiliate.router)
    app.include_router(payments.router)
    app.include_router(auth.router)
    app.include_router(premium.router)
    app.include_router(api_docs.router)
    app.include_router(sectors.router)

    @app.on_event("startup")
    async def _startup_cache() -> None:
        logger.info(
            "[STARTUP] Chartora API starting — "
            "cache_ttl=%ds, debug=%s",
            settings.cache_ttl_seconds,
            settings.debug,
        )
        logger.info(
            "[STARTUP] Database URL: %s",
            settings.database_url.split("@")[-1]
            if "@" in settings.database_url
            else "(not configured)",
        )
        logger.info(
            "[STARTUP] NewsAPI key configured: %s",
            bool(settings.news_api_key),
        )
        logger.info(
            "[STARTUP] Claude API key configured: %s",
            bool(settings.claude_api_key),
        )

    @app.get("/api/v1/cache/stats")
    async def cache_stats() -> dict[str, Any]:
        """Return current cache statistics for monitoring."""
        evicted = await cache._evict_expired()
        return {
            "size": cache.size,
            "evicted": evicted,
            "default_ttl_seconds": settings.cache_ttl_seconds,
        }

    return app


app = create_app()
