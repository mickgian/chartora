"""Tests for the premium API endpoints (W7.2, W7.3)."""

import pytest
from fastapi.testclient import TestClient

from src.adapters.api.main import create_app
from src.config.settings import Settings


@pytest.fixture
def client():
    settings = Settings(
        database_url="sqlite+aiosqlite:///test.db",
        jwt_secret_key="test-secret",
        stripe_secret_key="sk_test_fake",
        stripe_webhook_secret="whsec_fake",
    )
    app = create_app(settings)
    return TestClient(app)


def test_historical_scores_requires_auth(client):
    response = client.get("/api/v1/pro/historical-scores/ionq")
    assert response.status_code == 401


def test_full_patent_history_requires_auth(client):
    response = client.get("/api/v1/pro/patents/ionq/full-history")
    assert response.status_code == 401


def test_insider_trading_requires_auth(client):
    response = client.get("/api/v1/pro/insider-trading/ionq")
    assert response.status_code == 401


def test_institutional_ownership_requires_auth(client):
    response = client.get("/api/v1/pro/institutional-ownership/ionq")
    assert response.status_code == 401


def test_alerts_requires_auth(client):
    response = client.get("/api/v1/pro/alerts")
    assert response.status_code == 401


def test_export_csv_requires_auth(client):
    response = client.get("/api/v1/pro/export/csv")
    assert response.status_code == 401


def test_export_json_requires_auth(client):
    response = client.get("/api/v1/pro/export/json")
    assert response.status_code == 401


def test_api_keys_list_requires_auth(client):
    response = client.get("/api/v1/pro/api-keys")
    assert response.status_code == 401


def test_api_keys_create_requires_auth(client):
    response = client.post(
        "/api/v1/pro/api-keys",
        json={"name": "Test Key"},
    )
    assert response.status_code == 401


def test_api_keys_delete_requires_auth(client):
    response = client.delete("/api/v1/pro/api-keys/1")
    assert response.status_code == 401
