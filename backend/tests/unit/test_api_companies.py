"""Tests for the Company detail API endpoints."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.adapters.api.dependencies import (
    get_company_repo,
    get_filing_repo,
    get_news_repo,
    get_patent_repo,
    get_score_repo,
    get_stock_data_source,
    get_stock_repo,
)
from src.adapters.api.main import create_app
from src.config.settings import Settings
from src.domain.models.entities import (
    Company,
    Filing,
    IntradayPrice,
    NewsArticle,
    Patent,
    QuantumPowerScore,
    StockPrice,
)
from src.domain.models.value_objects import (
    FilingType,
    PatentSource,
    Sector,
    SentimentLabel,
    Ticker,
)


def _make_company(id: int = 1) -> Company:
    return Company(
        id=id,
        name="IonQ",
        slug="ionq",
        sector=Sector.PURE_PLAY,
        ticker=Ticker("IONQ"),
        description="Trapped ion quantum computing",
    )


@pytest.fixture
def mock_company_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_slug = AsyncMock(return_value=_make_company())
    return repo


@pytest.fixture
def mock_score_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_latest = AsyncMock(
        return_value=QuantumPowerScore(
            company_id=1,
            score_date=date(2026, 3, 14),
            stock_momentum=75.0,
            patent_velocity=60.0,
            qubit_progress=50.0,
            funding_strength=80.0,
            news_sentiment=65.0,
            rank=1,
        )
    )
    return repo


@pytest.fixture
def _stock_prices() -> list[StockPrice]:
    return [
        StockPrice(
            company_id=1,
            price_date=date(2026, 3, 13),
            close_price=Decimal("25.50"),
            open_price=Decimal("25.00"),
            high_price=Decimal("26.00"),
            low_price=Decimal("24.50"),
            volume=1000000,
        ),
    ]


@pytest.fixture
def mock_stock_repo(_stock_prices: list[StockPrice]) -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_date_range = AsyncMock(return_value=_stock_prices)
    repo.get_all_for_company = AsyncMock(return_value=_stock_prices)
    return repo


@pytest.fixture
def mock_stock_data_source() -> AsyncMock:
    source = AsyncMock()
    source.fetch_intraday = AsyncMock(
        return_value=[
            IntradayPrice(
                timestamp=datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC),
                price=Decimal("25.30"),
                volume=150000,
            ),
            IntradayPrice(
                timestamp=datetime(2026, 3, 15, 11, 0, 0, tzinfo=UTC),
                price=Decimal("25.50"),
                volume=200000,
            ),
        ]
    )
    return source


@pytest.fixture
def mock_patent_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_company = AsyncMock(
        return_value=[
            Patent(
                company_id=1,
                patent_number="US12345678",
                title="Quantum Error Correction",
                filing_date=date(2026, 1, 15),
                source=PatentSource.USPTO,
            ),
        ]
    )
    return repo


@pytest.fixture
def mock_news_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_company = AsyncMock(
        return_value=[
            NewsArticle(
                company_id=1,
                title="IonQ hits milestone",
                url="https://example.com/ionq",
                published_at=datetime(2026, 3, 14, 10, 0, 0, tzinfo=UTC),
                source_name="TechCrunch",
                sentiment=SentimentLabel.BULLISH,
                sentiment_score=Decimal("0.85"),
            ),
        ]
    )
    return repo


@pytest.fixture
def mock_filing_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_company = AsyncMock(
        return_value=[
            Filing(
                company_id=1,
                filing_type=FilingType.FORM_10K,
                filing_date=date(2026, 2, 28),
                description="Annual Report",
                url="https://sec.gov/filing/123",
            ),
        ]
    )
    return repo


@pytest.fixture
def client(
    mock_company_repo: AsyncMock,
    mock_score_repo: AsyncMock,
    mock_stock_repo: AsyncMock,
    mock_stock_data_source: AsyncMock,
    mock_patent_repo: AsyncMock,
    mock_news_repo: AsyncMock,
    mock_filing_repo: AsyncMock,
) -> TestClient:
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    app.dependency_overrides[get_company_repo] = lambda: mock_company_repo
    app.dependency_overrides[get_score_repo] = lambda: mock_score_repo
    app.dependency_overrides[get_stock_repo] = lambda: mock_stock_repo
    app.dependency_overrides[get_stock_data_source] = lambda: mock_stock_data_source
    app.dependency_overrides[get_patent_repo] = lambda: mock_patent_repo
    app.dependency_overrides[get_news_repo] = lambda: mock_news_repo
    app.dependency_overrides[get_filing_repo] = lambda: mock_filing_repo
    return TestClient(app)


def test_get_company_detail(client: TestClient) -> None:
    response = client.get("/api/v1/companies/ionq")
    assert response.status_code == 200
    data = response.json()
    assert data["company"]["name"] == "IonQ"
    assert data["company"]["slug"] == "ionq"
    assert data["company"]["ticker"] == "IONQ"
    assert data["score"]["total_score"] > 0
    assert data["score"]["rank"] == 1


def test_get_company_not_found() -> None:
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    repo = AsyncMock()
    repo.get_by_slug = AsyncMock(return_value=None)
    app.dependency_overrides[get_company_repo] = lambda: repo
    client = TestClient(app)

    response = client.get("/api/v1/companies/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_company_stock(client: TestClient) -> None:
    response = client.get("/api/v1/companies/ionq/stock")
    assert response.status_code == 200
    data = response.json()
    assert data["company_slug"] == "ionq"
    assert data["count"] == 1
    assert data["prices"][0]["close_price"] == 25.50


def test_get_company_stock_with_days(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/companies/ionq/stock?days=30")
    assert response.status_code == 200


def test_get_company_patents(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/companies/ionq/patents")
    assert response.status_code == 200
    data = response.json()
    assert data["company_slug"] == "ionq"
    assert data["count"] == 1
    assert data["patents"][0]["patent_number"] == "US12345678"


def test_get_company_news(client: TestClient) -> None:
    response = client.get("/api/v1/companies/ionq/news")
    assert response.status_code == 200
    data = response.json()
    assert data["company_slug"] == "ionq"
    assert data["count"] == 1
    assert data["articles"][0]["sentiment"] == "bullish"


def test_get_company_news_with_limit(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/companies/ionq/news?limit=5")
    assert response.status_code == 200


def test_get_company_filings(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/companies/ionq/filings")
    assert response.status_code == 200
    data = response.json()
    assert data["company_slug"] == "ionq"
    assert data["count"] == 1
    assert data["filings"][0]["filing_type"] == "10-K"


def test_get_company_intraday(client: TestClient) -> None:
    response = client.get("/api/v1/companies/ionq/stock/intraday")
    assert response.status_code == 200
    data = response.json()
    assert data["company_slug"] == "ionq"
    assert data["count"] == 2
    assert data["prices"][0]["price"] == 25.30
    assert "timestamp" in data["prices"][0]
    assert data["prices"][1]["price"] == 25.50


def test_company_stock_not_found() -> None:
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    repo = AsyncMock()
    repo.get_by_slug = AsyncMock(return_value=None)
    app.dependency_overrides[get_company_repo] = lambda: repo
    client = TestClient(app)

    response = client.get("/api/v1/companies/nonexistent/stock")
    assert response.status_code == 404
