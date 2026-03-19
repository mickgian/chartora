"""Tests for the Leaderboard API endpoints."""

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
from src.domain.models.entities import Company, QuantumPowerScore
from src.domain.models.value_objects import Sector, Ticker


def _make_company(
    id: int,
    name: str,
    slug: str,
    ticker: str | None = None,
    sector: Sector = Sector.PURE_PLAY,
    is_etf: bool = False,
) -> Company:
    return Company(
        id=id,
        name=name,
        slug=slug,
        sector=sector,
        ticker=Ticker(ticker) if ticker else None,
        is_etf=is_etf,
    )


def _make_score(
    company_id: int,
    total: float = 50.0,
    rank: int | None = None,
) -> QuantumPowerScore:
    return QuantumPowerScore(
        company_id=company_id,
        score_date=date(2026, 3, 14),
        stock_momentum=total,
        patent_velocity=total,
        qubit_progress=total,
        funding_strength=total,
        news_sentiment=total,
        rank=rank,
    )


@pytest.fixture
def mock_company_repo() -> AsyncMock:
    all_companies = [
        _make_company(1, "IonQ", "ionq", "IONQ"),
        _make_company(2, "D-Wave", "d-wave", "QBTS"),
        _make_company(3, "Rigetti", "rigetti", "RGTI"),
        _make_company(4, "Defiance Quantum ETF", "defiance-quantum-etf", "QTUM", sector=Sector.ETF, is_etf=True),
    ]
    repo = AsyncMock()
    repo.get_all = AsyncMock(return_value=all_companies)

    async def _get_by_sector(sector: str) -> list[Company]:
        return [c for c in all_companies if c.sector.value == sector]

    repo.get_by_sector = AsyncMock(side_effect=_get_by_sector)
    return repo


@pytest.fixture
def mock_score_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_latest_all = AsyncMock(
        return_value=[
            _make_score(1, total=80.0),
            _make_score(2, total=60.0),
            _make_score(3, total=40.0),
            _make_score(4, total=50.0),
        ]
    )
    return repo


@pytest.fixture
def client(mock_company_repo: AsyncMock, mock_score_repo: AsyncMock) -> TestClient:
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    app.dependency_overrides[get_company_repo] = lambda: mock_company_repo
    app.dependency_overrides[get_score_repo] = lambda: mock_score_repo
    return TestClient(app)


def test_leaderboard_returns_ranked_companies(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "total_score"
    assert data["count"] == 4
    assert len(data["entries"]) == 4
    # First entry should be highest score
    assert data["entries"][0]["rank"] == 1
    assert data["entries"][0]["company"]["name"] == "IonQ"


def test_leaderboard_sort_by_metric(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/leaderboard?sort_by=stock_momentum")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "stock_momentum"


def test_leaderboard_with_limit(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/leaderboard?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["entries"]) == 2


def test_leaderboard_invalid_sort_by(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/leaderboard?sort_by=invalid")
    assert response.status_code == 422


def test_leaderboard_empty_scores(
    mock_company_repo: AsyncMock,
) -> None:
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    empty_score_repo = AsyncMock()
    empty_score_repo.get_latest_all = AsyncMock(return_value=[])
    app.dependency_overrides[get_company_repo] = lambda: mock_company_repo
    app.dependency_overrides[get_score_repo] = lambda: empty_score_repo
    client = TestClient(app)

    response = client.get("/api/v1/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["entries"] == []


def test_leaderboard_entry_has_all_fields(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/leaderboard")
    data = response.json()
    entry = data["entries"][0]
    assert "rank" in entry
    assert "company" in entry
    assert "score" in entry
    assert "trend" in entry
    assert "metric_value" in entry
    # Company fields
    company = entry["company"]
    assert "id" in company
    assert "name" in company
    assert "slug" in company
    assert "sector" in company
    assert "ticker" in company
    # Score fields
    score = entry["score"]
    assert "total_score" in score
    assert "stock_momentum" in score
    assert "patent_velocity" in score
    assert "score_date" in score


def test_leaderboard_filter_by_sector_etf(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/leaderboard?sector=etf")
    assert response.status_code == 200
    data = response.json()
    assert data["sector"] == "etf"
    assert data["count"] == 1
    assert data["entries"][0]["company"]["name"] == "Defiance Quantum ETF"
    assert data["entries"][0]["company"]["is_etf"] is True


def test_leaderboard_filter_by_sector_pure_play(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/leaderboard?sector=pure_play")
    assert response.status_code == 200
    data = response.json()
    assert data["sector"] == "pure_play"
    assert data["count"] == 3
    for entry in data["entries"]:
        assert entry["company"]["sector"] == "pure_play"


def test_leaderboard_no_sector_returns_all(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert data["sector"] is None
    assert data["count"] == 4
