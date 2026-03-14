"""Tests for the premium gate middleware."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.adapters.api.premium_gate import require_premium


@pytest.fixture
def client():
    app = FastAPI()

    premium_dep = Depends(require_premium)

    @app.get("/premium-endpoint")
    async def premium_route(
        premium_info: dict = premium_dep,
    ):
        return {"access": "granted", "premium": premium_info["premium"]}

    return TestClient(app)


def test_premium_gate_rejects_without_token(client):
    response = client.get("/premium-endpoint")
    assert response.status_code == 403
    assert "Premium subscription required" in response.json()["detail"]


def test_premium_gate_accepts_with_token(client):
    response = client.get(
        "/premium-endpoint",
        headers={"X-Premium-Token": "test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access"] == "granted"
    assert data["premium"] is True
