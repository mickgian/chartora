"""Tests for the Rankings API endpoints."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.adapters.api.dependencies import (
    get_company_repo,
    get_score_repo,
)
from src.adapters.api.main import create_app
from src.config.settings import Settings
from src.domain.models.entities import (
    Company,
    QuantumPowerScore,
)
from src.domain.models.value_objects import Sector, Ticker


def _make_company(id: int, name: str, slug: str, ticker: str) -> Company:
    return Company(
        id=id,
        name=name,
        slug=slug,
        sector=Sector.PURE_PLAY,
        ticker=Ticker(ticker),
    )


def _make_score(
    company_id: int,
    stock: float = 50.0,
    patent: float = 50.0,
    funding: float = 50.0,
    sentiment: float = 50.0,
) -> QuantumPowerScore:
    return QuantumPowerScore(
        company_id=company_id,
        score_date=date(2026, 3, 14),
        stock_momentum=stock,
        patent_velocity=patent,
        qubit_progress=50.0,
        funding_strength=funding,
        news_sentiment=sentiment,
    )


@pytest.fixture
def mock_company_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_all = AsyncMock(
        return_value=[
            _make_company(1, "IonQ", "ionq", "IONQ"),
            _make_company(2, "D-Wave", "d-wave", "QBTS"),
        ]
    )
    return repo


@pytest.fixture
def mock_score_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_latest_all = AsyncMock(
        return_value=[
            _make_score(
                1,
                stock=90.0,
                patent=30.0,
                funding=70.0,
                sentiment=80.0,
            ),
            _make_score(
                2,
                stock=40.0,
                patent=85.0,
                funding=50.0,
                sentiment=60.0,
            ),
        ]
    )
    return repo


@pytest.fixture
def client(
    mock_company_repo: AsyncMock,
    mock_score_repo: AsyncMock,
) -> TestClient:
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    app.dependency_overrides[get_company_repo] = lambda: mock_company_repo
    app.dependency_overrides[get_score_repo] = lambda: mock_score_repo
    return TestClient(app)


def test_patent_rankings(client: TestClient) -> None:
    response = client.get("/api/v1/rankings/patents")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "patent_velocity"
    assert data["count"] == 2
    # D-Wave has higher patent score
    assert data["entries"][0]["company"]["name"] == "D-Wave"
    assert data["entries"][0]["metric_value"] == 85.0


def test_stock_performance_rankings(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/rankings/stock-performance")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "stock_momentum"
    # IonQ has higher stock score
    assert data["entries"][0]["company"]["name"] == "IonQ"
    assert data["entries"][0]["metric_value"] == 90.0


def test_funding_rankings(client: TestClient) -> None:
    response = client.get("/api/v1/rankings/funding")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "funding_strength"
    assert data["entries"][0]["company"]["name"] == "IonQ"


def test_sentiment_rankings(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/rankings/sentiment")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "news_sentiment"
    assert data["entries"][0]["company"]["name"] == "IonQ"


def test_rankings_empty() -> None:
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    empty_score = AsyncMock()
    empty_score.get_latest_all = AsyncMock(return_value=[])
    company_repo = AsyncMock()
    company_repo.get_all = AsyncMock(return_value=[])
    app.dependency_overrides[get_company_repo] = lambda: company_repo
    app.dependency_overrides[get_score_repo] = lambda: empty_score
    client = TestClient(app)

    response = client.get("/api/v1/rankings/patents")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_ranking_entry_fields(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/rankings/patents")
    data = response.json()
    entry = data["entries"][0]
    assert "rank" in entry
    assert "company" in entry
    assert "metric_value" in entry
    assert "trend" in entry
