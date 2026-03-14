"""Tests for health endpoints, request timing middleware, and monitoring setup."""

import pytest
from fastapi.testclient import TestClient

from src.adapters.api.main import create_app
from src.config.settings import Settings


@pytest.fixture
def client():
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_healthy(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_includes_version(self, client):
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_health_includes_uptime(self, client):
        response = client.get("/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], float)
        assert data["uptime_seconds"] >= 0


class TestReadinessEndpoint:
    def test_readiness_without_db_returns_not_ready(self, client):
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["database"] == "unavailable"


class TestRequestTimingMiddleware:
    def test_response_includes_timing_header(self, client):
        response = client.get("/health")
        assert "X-Response-Time" in response.headers
        timing = response.headers["X-Response-Time"]
        assert timing.endswith("ms")
        # Verify it's a valid number
        value = float(timing.replace("ms", ""))
        assert value >= 0


class TestMonitoringModule:
    def test_init_sentry_no_dsn(self):
        """init_sentry should not fail when no DSN is set."""
        import os

        os.environ.pop("SENTRY_DSN", None)
        from src.infrastructure.monitoring import init_sentry

        # Should not raise
        init_sentry()

    def test_setup_db_query_logging(self):
        """setup_db_query_logging should not fail."""
        from src.infrastructure.monitoring import setup_db_query_logging

        # Should not raise
        setup_db_query_logging(echo=False)
