"""Tests for the data refresh orchestrator.

Uses mocks to avoid importing yfinance (which may not
be installable in all environments).
"""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

# Mock yfinance before importing refresh_data
if "yfinance" not in sys.modules:
    sys.modules["yfinance"] = MagicMock()

from scripts.refresh_data import (
    recalculate_scores,
    refresh_news_data,
    refresh_patent_data,
    refresh_stock_data,
)

# Import Company separately to avoid circular issues
from src.domain.models.entities import (
    Company,
    NewsArticle,
    Patent,
    StockPrice,
)
from src.domain.models.value_objects import (
    PatentSource,
    Sector,
    Ticker,
)


def _make_company(
    id: int = 1,
    name: str = "IonQ",
    slug: str = "ionq",
    ticker: str | None = "IONQ",
) -> Company:
    return Company(
        id=id,
        name=name,
        slug=slug,
        sector=Sector.PURE_PLAY,
        ticker=Ticker(ticker) if ticker else None,
    )


@pytest.mark.asyncio
async def test_refresh_stock_data() -> None:
    company = _make_company()
    stock_adapter = AsyncMock()
    stock_adapter.fetch_history = AsyncMock(
        return_value=[
            StockPrice(
                company_id=0,
                price_date=date(2026, 3, 14),
                close_price=Decimal("25.00"),
            ),
        ]
    )
    stock_repo = AsyncMock()
    stock_repo.save_many = AsyncMock(return_value=[])

    await refresh_stock_data(company, stock_adapter, stock_repo)

    stock_adapter.fetch_history.assert_called_once()
    stock_repo.save_many.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_stock_data_no_ticker() -> None:
    company = _make_company(ticker=None)
    stock_adapter = AsyncMock()
    stock_repo = AsyncMock()

    await refresh_stock_data(company, stock_adapter, stock_repo)

    stock_adapter.fetch_history.assert_not_called()
    stock_repo.save_many.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_stock_data_no_results() -> None:
    company = _make_company()
    stock_adapter = AsyncMock()
    stock_adapter.fetch_history = AsyncMock(return_value=[])
    stock_repo = AsyncMock()

    await refresh_stock_data(company, stock_adapter, stock_repo)

    stock_repo.save_many.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_patent_data() -> None:
    company = _make_company()
    patent_adapter = AsyncMock()
    patent_adapter.search_patents = AsyncMock(
        return_value=[
            Patent(
                company_id=0,
                patent_number="US123",
                title="Test Patent",
                filing_date=date(2026, 3, 1),
                source=PatentSource.USPTO,
            ),
        ]
    )
    patent_repo = AsyncMock()
    patent_repo.save_many = AsyncMock(return_value=[])

    await refresh_patent_data(company, patent_adapter, patent_repo)

    patent_adapter.search_patents.assert_called_once()
    patent_repo.save_many.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_patent_data_no_results() -> None:
    company = _make_company()
    patent_adapter = AsyncMock()
    patent_adapter.search_patents = AsyncMock(return_value=[])
    patent_repo = AsyncMock()

    await refresh_patent_data(company, patent_adapter, patent_repo)

    patent_repo.save_many.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_news_data() -> None:
    company = _make_company()
    news_adapter = AsyncMock()
    news_adapter._api_key = "test-key"
    news_adapter.fetch_articles = AsyncMock(
        return_value=[
            NewsArticle(
                company_id=0,
                title="Test article",
                url="https://example.com",
                published_at=datetime(2026, 3, 14, tzinfo=UTC),
            ),
        ]
    )
    sentiment = AsyncMock()
    sentiment._api_key = ""  # No sentiment analysis
    news_repo = AsyncMock()
    news_repo.save_many = AsyncMock(return_value=[])

    await refresh_news_data(company, news_adapter, sentiment, news_repo)

    news_adapter.fetch_articles.assert_called_once()
    news_repo.save_many.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_news_data_no_api_key() -> None:
    company = _make_company()
    news_adapter = AsyncMock()
    news_adapter._api_key = ""
    sentiment = AsyncMock()
    news_repo = AsyncMock()

    await refresh_news_data(company, news_adapter, sentiment, news_repo)

    news_adapter.fetch_articles.assert_not_called()


@pytest.mark.asyncio
async def test_recalculate_scores() -> None:
    companies = [
        _make_company(id=1),
        _make_company(
            id=2,
            name="D-Wave",
            slug="d-wave",
            ticker="QBTS",
        ),
    ]
    stock_repo = AsyncMock()
    patent_repo = AsyncMock()
    patent_repo.count_by_date_range = AsyncMock(return_value=5)
    news_repo = AsyncMock()
    news_repo.get_by_company = AsyncMock(return_value=[])
    score_repo = AsyncMock()
    score_repo.save_many = AsyncMock(return_value=[])
    stock_adapter = AsyncMock()
    stock_adapter.fetch_performance = AsyncMock(return_value=10.0)

    await recalculate_scores(
        companies,
        stock_repo,
        patent_repo,
        news_repo,
        score_repo,
        stock_adapter,
    )

    score_repo.save_many.assert_called_once()
    saved_scores = score_repo.save_many.call_args[0][0]
    assert len(saved_scores) == 2
    # Both should have ranks assigned
    ranks = {s.rank for s in saved_scores}
    assert ranks == {1, 2}
