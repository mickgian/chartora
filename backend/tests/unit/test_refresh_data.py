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


@pytest.mark.asyncio
async def test_recalculate_scores_with_xbrl_funding() -> None:
    """SEC EDGAR XBRL funding replaces hardcoded values."""
    companies = [_make_company(id=1)]
    stock_repo = AsyncMock()
    patent_repo = AsyncMock()
    patent_repo.count_by_date_range = AsyncMock(return_value=5)
    news_repo = AsyncMock()
    news_repo.get_by_company = AsyncMock(return_value=[])
    score_repo = AsyncMock()
    score_repo.save_many = AsyncMock(return_value=[])
    stock_adapter = AsyncMock()
    stock_adapter.fetch_performance = AsyncMock(return_value=10.0)
    xbrl_adapter = AsyncMock()
    xbrl_adapter.fetch_total_funding = AsyncMock(return_value=900_000_000.0)

    await recalculate_scores(
        companies,
        stock_repo,
        patent_repo,
        news_repo,
        score_repo,
        stock_adapter,
        xbrl_adapter=xbrl_adapter,
    )

    xbrl_adapter.fetch_total_funding.assert_called_once_with("IONQ")
    score_repo.save_many.assert_called_once()


@pytest.mark.asyncio
async def test_recalculate_scores_xbrl_fallback() -> None:
    """Falls back to KNOWN_FUNDING_USD when XBRL returns None."""
    companies = [_make_company(id=1)]
    stock_repo = AsyncMock()
    patent_repo = AsyncMock()
    patent_repo.count_by_date_range = AsyncMock(return_value=5)
    news_repo = AsyncMock()
    news_repo.get_by_company = AsyncMock(return_value=[])
    score_repo = AsyncMock()
    score_repo.save_many = AsyncMock(return_value=[])
    stock_adapter = AsyncMock()
    stock_adapter.fetch_performance = AsyncMock(return_value=10.0)
    xbrl_adapter = AsyncMock()
    xbrl_adapter.fetch_total_funding = AsyncMock(return_value=None)

    await recalculate_scores(
        companies,
        stock_repo,
        patent_repo,
        news_repo,
        score_repo,
        stock_adapter,
        xbrl_adapter=xbrl_adapter,
    )

    # Should still produce scores (using fallback funding)
    score_repo.save_many.assert_called_once()


@pytest.mark.asyncio
async def test_recalculate_scores_qubit_from_news() -> None:
    """Qubit count extracted from news via Claude API."""
    companies = [_make_company(id=1, name="IBM", slug="ibm", ticker="IBM")]
    stock_repo = AsyncMock()
    patent_repo = AsyncMock()
    patent_repo.count_by_date_range = AsyncMock(return_value=5)
    news_repo = AsyncMock()
    news_repo.get_by_company = AsyncMock(
        return_value=[
            NewsArticle(
                id=1,
                company_id=1,
                title="IBM unveils 1121-qubit Condor processor",
                url="https://example.com",
                published_at=datetime(2026, 3, 14, tzinfo=UTC),
            ),
        ]
    )
    score_repo = AsyncMock()
    score_repo.save_many = AsyncMock(return_value=[])
    stock_adapter = AsyncMock()
    stock_adapter.fetch_performance = AsyncMock(return_value=10.0)
    sentiment_analyzer = AsyncMock()
    sentiment_analyzer._api_key = "test-key"
    sentiment_analyzer.extract_qubit_count = AsyncMock(return_value=1121)

    await recalculate_scores(
        companies,
        stock_repo,
        patent_repo,
        news_repo,
        score_repo,
        stock_adapter,
        sentiment_analyzer=sentiment_analyzer,
    )

    sentiment_analyzer.extract_qubit_count.assert_called_once()
    score_repo.save_many.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_news_data_with_sentiment() -> None:
    """Articles get sentiment scores when Claude API key is set."""
    company = _make_company()
    news_adapter = AsyncMock()
    news_adapter._api_key = "test-key"
    news_adapter.fetch_articles = AsyncMock(
        return_value=[
            NewsArticle(
                company_id=0,
                title="IonQ announces major quantum breakthrough",
                url="https://example.com/1",
                published_at=datetime(2026, 3, 14, tzinfo=UTC),
            ),
        ]
    )
    sentiment = AsyncMock()
    sentiment._api_key = "test-claude-key"
    sentiment.analyze = AsyncMock(return_value=("bullish", 0.85))
    news_repo = AsyncMock()
    news_repo.save_many = AsyncMock(return_value=[])

    await refresh_news_data(company, news_adapter, sentiment, news_repo)

    sentiment.analyze.assert_called_once()
    saved = news_repo.save_many.call_args[0][0]
    assert saved[0].sentiment is not None
    assert saved[0].sentiment_score is not None


@pytest.mark.asyncio
async def test_refresh_news_data_skips_failed_sentiment() -> None:
    """Articles without successful sentiment analysis have no score."""
    company = _make_company()
    news_adapter = AsyncMock()
    news_adapter._api_key = "test-key"
    news_adapter.fetch_articles = AsyncMock(
        return_value=[
            NewsArticle(
                company_id=0,
                title="Some article",
                url="https://example.com/1",
                published_at=datetime(2026, 3, 14, tzinfo=UTC),
            ),
        ]
    )
    sentiment = AsyncMock()
    sentiment._api_key = "test-claude-key"
    sentiment.analyze = AsyncMock(return_value=None)  # API error
    news_repo = AsyncMock()
    news_repo.save_many = AsyncMock(return_value=[])

    await refresh_news_data(company, news_adapter, sentiment, news_repo)

    saved = news_repo.save_many.call_args[0][0]
    # Article saved but without sentiment
    assert saved[0].sentiment is None
    assert saved[0].sentiment_score is None


@pytest.mark.asyncio
async def test_recalculate_scores_with_sentiment() -> None:
    """Scored articles produce differentiated sentiment values."""
    from src.domain.models.value_objects import SentimentLabel

    companies = [
        _make_company(id=1, name="IBM", slug="ibm", ticker="IBM"),
        _make_company(id=2, name="Arqit", slug="arqit-quantum", ticker="ARQQ"),
    ]
    stock_repo = AsyncMock()
    patent_repo = AsyncMock()
    patent_repo.count_by_date_range = AsyncMock(return_value=0)

    # IBM: bullish articles; Arqit: bearish articles
    ibm_articles = [
        NewsArticle(
            id=i,
            company_id=1,
            title=f"IBM bullish news {i}",
            url=f"https://example.com/{i}",
            published_at=datetime(2026, 3, 14, tzinfo=UTC),
            sentiment=SentimentLabel.BULLISH,
            sentiment_score=Decimal("0.80"),
        )
        for i in range(10)
    ]
    arqit_articles = [
        NewsArticle(
            id=i + 100,
            company_id=2,
            title=f"Arqit bearish news {i}",
            url=f"https://example.com/{i + 100}",
            published_at=datetime(2026, 3, 14, tzinfo=UTC),
            sentiment=SentimentLabel.BEARISH,
            sentiment_score=Decimal("0.70"),
        )
        for i in range(10)
    ]

    async def mock_get_by_company(
        company_id: int, limit: int = 20
    ) -> list[NewsArticle]:
        if company_id == 1:
            return ibm_articles
        return arqit_articles

    news_repo = AsyncMock()
    news_repo.get_by_company = AsyncMock(side_effect=mock_get_by_company)
    score_repo = AsyncMock()
    score_repo.save_many = AsyncMock(return_value=[])
    stock_adapter = AsyncMock()
    stock_adapter.fetch_performance = AsyncMock(return_value=0.0)

    await recalculate_scores(
        companies,
        stock_repo,
        patent_repo,
        news_repo,
        score_repo,
        stock_adapter,
    )

    saved_scores = score_repo.save_many.call_args[0][0]
    score_by_company = {s.company_id: s for s in saved_scores}
    ibm_news = score_by_company[1].news_sentiment
    arqit_news = score_by_company[2].news_sentiment
    # IBM (bullish) should score much higher than Arqit (bearish)
    assert ibm_news > 50.0
    assert arqit_news < 50.0
    assert ibm_news > arqit_news
