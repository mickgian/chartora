"""Unit tests for sector API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.adapters.api.main import create_app
from src.config.settings import Settings


@pytest.fixture
def client():
    app = create_app(Settings(database_url="sqlite+aiosqlite:///test.db"))
    return TestClient(app)


class TestSectorsAPI:
    def test_list_sectors(self, client):
        response = client.get("/api/v1/sectors")
        assert response.status_code == 200
        data = response.json()
        assert "sectors" in data
        assert "total" in data
        assert data["total"] >= 1
        sector = data["sectors"][0]
        assert sector["name"] == "quantum_computing"
        assert sector["display_name"] == "Quantum Computing"
        assert "score_weights" in sector

    def test_get_sector_by_slug(self, client):
        response = client.get("/api/v1/sectors/quantum-computing")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "quantum_computing"
        assert data["enabled"] is True

    def test_get_sector_not_found(self, client):
        response = client.get("/api/v1/sectors/nonexistent")
        assert response.status_code == 404

    def test_sector_weights_sum_to_one(self, client):
        response = client.get("/api/v1/sectors/quantum-computing")
        data = response.json()
        total = sum(data["score_weights"].values())
        assert abs(total - 1.0) < 0.01


class TestApiDocsAPI:
    def test_list_endpoints(self, client):
        response = client.get("/api/v1/docs/endpoints")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        assert len(data["endpoints"]) > 0
        endpoint = data["endpoints"][0]
        assert "method" in endpoint
        assert "path" in endpoint
        assert "summary" in endpoint

    def test_list_schemas(self, client):
        response = client.get("/api/v1/docs/schemas")
        assert response.status_code == 200
        data = response.json()
        assert "schemas" in data
        schema_names = [s["name"] for s in data["schemas"]]
        assert "Company" in schema_names
        assert "QuantumPowerScore" in schema_names

    def test_get_rate_limits(self, client):
        response = client.get("/api/v1/docs/rate-limits")
        assert response.status_code == 200
        data = response.json()
        assert "tiers" in data
        assert "headers" in data
        tier_names = [t["tier"] for t in data["tiers"]]
        assert "anonymous" in tier_names
        assert "pro" in tier_names


class TestCacheStats:
    def test_cache_stats_endpoint(self, client):
        response = client.get("/api/v1/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "size" in data
        assert "default_ttl_seconds" in data
