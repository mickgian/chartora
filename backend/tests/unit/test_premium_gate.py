"""Tests for the premium gate middleware."""

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.api.main import create_app
from src.config.settings import Settings
from src.infrastructure.database import Base


@pytest.fixture
def client():
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        jwt_secret_key="test-secret-32-chars-long-enough!",
        stripe_secret_key="sk_test_fake",
        stripe_webhook_secret="whsec_fake",
    )
    app = create_app(settings)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)

    asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
        _create_tables(engine)
    )
    app.state.session_factory = factory

    return TestClient(app)


async def _create_tables(engine):  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def test_premium_gate_rejects_without_auth(client):
    """Premium endpoints require authentication."""
    response = client.get("/api/v1/pro/export/json")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


def test_premium_gate_rejects_invalid_bearer(client):
    """Invalid JWT tokens are rejected."""
    response = client.get(
        "/api/v1/pro/export/json",
        headers={"Authorization": "Bearer invalid.token"},
    )
    assert response.status_code == 401


def test_premium_gate_rejects_invalid_api_key(client):
    """Invalid API keys are rejected."""
    response = client.get(
        "/api/v1/pro/export/json",
        headers={"X-API-Key": "invalid_key"},
    )
    assert response.status_code == 401
