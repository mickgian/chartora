"""Monitoring utilities: Sentry integration and database query logging."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry error tracking if SENTRY_DSN is set."""
    dsn = os.environ.get("SENTRY_DSN", "")
    if not dsn:
        logger.info("Sentry DSN not configured, error tracking disabled")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=os.environ.get("CHARTORA_ENVIRONMENT", "production"),
        )
        logger.info("Sentry error tracking initialized")
    except ImportError:
        logger.warning("sentry-sdk not installed, error tracking disabled")


def setup_db_query_logging(echo: bool = False) -> None:
    """Enable SQLAlchemy query event logging for performance monitoring.

    Logs queries that take longer than 500ms as warnings.
    """
    import time

    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        start_times: list[float] = conn.info.get("query_start_time", [])
        if not start_times:
            return
        duration_ms = (time.perf_counter() - start_times.pop()) * 1000

        if duration_ms > 500:
            logger.warning(
                "Slow query: duration_ms=%.1f statement=%s",
                duration_ms,
                statement[:200],
            )
        elif echo:
            logger.debug(
                "Query: duration_ms=%.1f statement=%s",
                duration_ms,
                statement[:200],
            )
