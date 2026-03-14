"""Tests for the affiliate link click-tracking endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.adapters.api.main import create_app
from src.config.settings import Settings


@pytest.fixture
def client():
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    return TestClient(app)


def test_affiliate_click_returns_destination(client):
    response = client.get(
        "/api/affiliate/click",
        params={"broker": "ibkr", "ticker": "IONQ", "company": "ionq"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "destination" in data
    assert "IONQ" in data["destination"]
    assert data["broker"] == "ibkr"
    assert data["ticker"] == "IONQ"


def test_affiliate_click_etoro(client):
    response = client.get(
        "/api/affiliate/click",
        params={"broker": "etoro", "ticker": "QBTS", "company": "d-wave"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "QBTS" in data["destination"]
    assert "etoro" in data["destination"]


def test_affiliate_click_unknown_broker(client):
    response = client.get(
        "/api/affiliate/click",
        params={"broker": "unknown", "ticker": "IONQ", "company": "ionq"},
    )
    assert response.status_code == 404
    data = response.json()
    assert "Unknown broker" in data["detail"]


def test_affiliate_click_missing_params(client):
    response = client.get("/api/affiliate/click")
    assert response.status_code == 422
