"""FastAPI application factory with CORS, error handling, and routers."""

from __future__ import annotations

import asyncio
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
            "[STARTUP] Chartora API starting — cache_ttl=%ds, debug=%s",
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

        # Auto-refresh data in background if no scores exist yet
        app.state.refresh_task = asyncio.create_task(_initial_data_refresh(settings))

    async def _initial_data_refresh(settings: Settings) -> None:
        """Run data refresh if data is missing, stale, or forced."""
        try:
            from datetime import date, timedelta

            from sqlalchemy import text as sa_text
            from sqlalchemy.ext.asyncio import (
                async_sessionmaker,
                create_async_engine,
            )

            engine = create_async_engine(settings.database_url)
            factory = async_sessionmaker(engine, expire_on_commit=False)

            needs_refresh = False
            reason = ""

            async with factory() as session:
                # Check if scores exist at all
                result = await session.execute(sa_text("SELECT COUNT(*) FROM scores"))
                score_count = result.scalar() or 0

                if score_count == 0:
                    needs_refresh = True
                    reason = "no scores in database"
                else:
                    # Check if stock data is sufficient (need >30 days for charts)
                    result = await session.execute(
                        sa_text("SELECT COUNT(*) FROM stock_prices")
                    )
                    stock_count = result.scalar() or 0

                    if stock_count < 100:
                        needs_refresh = True
                        reason = f"insufficient stock data ({stock_count} rows)"
                    else:
                        # Check if stock data is stale (latest price > 2 days old,
                        # accounting for weekends)
                        result = await session.execute(
                            sa_text("SELECT MAX(price_date) FROM stock_prices")
                        )
                        latest_date = result.scalar()
                        if latest_date is not None:
                            stale_threshold = date.today() - timedelta(days=3)
                            if latest_date < stale_threshold:
                                needs_refresh = True
                                reason = (
                                    f"stock data is stale "
                                    f"(latest: {latest_date}, "
                                    f"threshold: {stale_threshold})"
                                )

            await engine.dispose()

            if settings.force_refresh:
                needs_refresh = True
                reason = "CHARTORA_FORCE_REFRESH=true"

            if not needs_refresh:
                logger.info(
                    "[STARTUP] Data looks healthy (%d scores, stock data up to date) "
                    "— skipping refresh",
                    score_count,
                )
                return

            logger.info(
                "[STARTUP] Data refresh needed: %s — running in background...",
                reason,
            )
            from scripts.refresh_data import run_refresh

            await run_refresh(settings)
            logger.info("[STARTUP] Initial data refresh complete")
        except Exception:
            logger.exception(
                "[STARTUP] Initial data refresh failed — will retry on next cron run"
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

    @app.get("/api/v1/debug/stock-counts")
    async def debug_stock_counts(request: Request) -> dict[str, Any]:
        """Diagnostic: show stock price counts per company in the DB."""
        from sqlalchemy import func, select

        from src.infrastructure.database import CompanyTable, StockPriceTable

        factory = getattr(request.app.state, "session_factory", None)
        if factory is None:
            from src.adapters.api.dependencies import get_settings, init_db

            s = get_settings(request)
            factory = init_db(s)
            request.app.state.session_factory = factory

        async with factory() as session:
            # Total count
            total_result = await session.execute(
                select(func.count()).select_from(StockPriceTable)
            )
            total = total_result.scalar() or 0

            # Per-company counts with date range
            stmt = (
                select(
                    CompanyTable.name,
                    CompanyTable.id,
                    func.count(StockPriceTable.id).label("count"),
                    func.min(StockPriceTable.price_date).label("min_date"),
                    func.max(StockPriceTable.price_date).label("max_date"),
                )
                .join(
                    StockPriceTable,
                    CompanyTable.id == StockPriceTable.company_id,
                )
                .group_by(CompanyTable.name, CompanyTable.id)
                .order_by(CompanyTable.name)
            )
            result = await session.execute(stmt)
            rows = result.all()

        companies = [
            {
                "name": row.name,
                "company_id": row.id,
                "stock_price_count": row.count,
                "earliest_date": str(row.min_date) if row.min_date else None,
                "latest_date": str(row.max_date) if row.max_date else None,
            }
            for row in rows
        ]

        return {
            "total_stock_prices": total,
            "companies": companies,
            "database_url_host": settings.database_url.split("@")[-1]
            if "@" in settings.database_url
            else "(unknown)",
        }

    return app


app = create_app()
