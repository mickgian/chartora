"""Tests for the SectorPipeline use case."""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

# Mock yfinance before any transitive import pulls it in
if "yfinance" not in sys.modules:
    sys.modules["yfinance"] = MagicMock()

from datetime import datetime

from src.domain.models.entities import Company, NewsArticle, Patent, StockPrice
from src.domain.models.sector_config import SectorConfig
from src.domain.models.value_objects import (
    PatentSource,
    Sector,
    SentimentLabel,
    Ticker,
)
from src.usecases.sector_pipeline import (
    PipelineRepositories,
    RefreshResult,
    SectorPipeline,
)


def _make_config() -> SectorConfig:
    return SectorConfig(
        name="quantum_computing",
        display_name="Quantum Computing",
        slug="quantum-computing",
        description="Test sector",
        score_weights={
            "stock_momentum": 0.20,
            "patent_velocity": 0.25,
            "qubit_progress": 0.20,
            "funding_strength": 0.20,
            "news_sentiment": 0.15,
        },
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


def _make_repos() -> PipelineRepositories:
    return PipelineRepositories(
        stock_repo=AsyncMock(),
        patent_repo=AsyncMock(),
        news_repo=AsyncMock(),
        score_repo=AsyncMock(),
    )


# --- RefreshResult tests ---


def test_refresh_result_defaults() -> None:
    result = RefreshResult()
    assert result.companies_processed == 0
    assert result.errors == []
    assert result.duration_seconds == 0.0
    assert result.has_errors is False


def test_refresh_result_has_errors() -> None:
    result = RefreshResult(errors=["Something went wrong"])
    assert result.has_errors is True


def test_refresh_result_no_errors() -> None:
    result = RefreshResult(companies_processed=3, errors=[])
    assert result.has_errors is False


# --- PipelineRepositories tests ---


def test_pipeline_repositories_creation() -> None:
    repos = _make_repos()
    assert repos.stock_repo is not None
    assert repos.patent_repo is not None
    assert repos.news_repo is not None
    assert repos.score_repo is not None


# --- SectorPipeline.refresh_company tests ---


@pytest.mark.asyncio
async def test_refresh_company_with_ticker() -> None:
    """Stock data is fetched and saved when company has a ticker."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    price = StockPrice(
        company_id=1,
        price_date=date(2026, 3, 18),
        close_price=Decimal("32.50"),
    )
    stock_source.fetch_current_price = AsyncMock(return_value=price)
    patent_source.search_patents = AsyncMock(return_value=[])
    news_source.fetch_articles = AsyncMock(return_value=[])

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    await pipeline.refresh_company(_make_company(), repos)

    stock_source.fetch_current_price.assert_called_once_with("IONQ")
    repos.stock_repo.save.assert_called_once_with(price)


@pytest.mark.asyncio
async def test_refresh_company_no_ticker() -> None:
    """Stock fetch is skipped when company has no ticker."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    patent_source.search_patents = AsyncMock(return_value=[])
    news_source.fetch_articles = AsyncMock(return_value=[])

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    await pipeline.refresh_company(_make_company(ticker=None), repos)

    stock_source.fetch_current_price.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_company_stock_returns_none() -> None:
    """Nothing is saved when stock source returns None."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    stock_source.fetch_current_price = AsyncMock(return_value=None)
    patent_source.search_patents = AsyncMock(return_value=[])
    news_source.fetch_articles = AsyncMock(return_value=[])

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    await pipeline.refresh_company(_make_company(), repos)

    repos.stock_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_company_saves_patents() -> None:
    """Patents are saved when patent source returns results."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    stock_source.fetch_current_price = AsyncMock(return_value=None)
    patents = [
        Patent(
            company_id=1,
            patent_number="US1234567",
            title="Quantum Error Correction",
            filing_date=date(2026, 3, 1),
            source=PatentSource.USPTO,
        )
    ]
    patent_source.search_patents = AsyncMock(return_value=patents)
    news_source.fetch_articles = AsyncMock(return_value=[])

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    await pipeline.refresh_company(_make_company(), repos)

    repos.patent_repo.save_many.assert_called_once_with(patents)


@pytest.mark.asyncio
async def test_refresh_company_empty_patents() -> None:
    """Patent repo is not called when no patents found."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    stock_source.fetch_current_price = AsyncMock(return_value=None)
    patent_source.search_patents = AsyncMock(return_value=[])
    news_source.fetch_articles = AsyncMock(return_value=[])

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    await pipeline.refresh_company(_make_company(), repos)

    repos.patent_repo.save_many.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_company_news_with_sentiment() -> None:
    """News articles are analysed and saved with sentiment."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    stock_source.fetch_current_price = AsyncMock(return_value=None)
    patent_source.search_patents = AsyncMock(return_value=[])

    articles = [
        NewsArticle(
            company_id=1,
            title="IonQ Announces Breakthrough",
            url="https://example.com/1",
            published_at=datetime(2026, 3, 18),
            source_name="TechCrunch",
        ),
        NewsArticle(
            company_id=1,
            title="Quantum Market Dips",
            url="https://example.com/2",
            published_at=datetime(2026, 3, 17),
            source_name="Bloomberg",
        ),
    ]
    news_source.fetch_articles = AsyncMock(return_value=articles)
    sentiment.analyze_batch = AsyncMock(
        return_value=[("bullish", 0.85), ("bearish", 0.60)]
    )

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    await pipeline.refresh_company(_make_company(), repos)

    sentiment.analyze_batch.assert_called_once_with(
        ["IonQ Announces Breakthrough", "Quantum Market Dips"]
    )
    repos.news_repo.save_many.assert_called_once_with(articles)
    assert articles[0].sentiment == SentimentLabel.BULLISH
    assert articles[0].sentiment_score == Decimal("0.85")
    assert articles[1].sentiment == SentimentLabel.BEARISH
    assert articles[1].sentiment_score == Decimal("0.6")


@pytest.mark.asyncio
async def test_refresh_company_news_sentiment_none_skipped() -> None:
    """Articles with None sentiment result are left unscored."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    stock_source.fetch_current_price = AsyncMock(return_value=None)
    patent_source.search_patents = AsyncMock(return_value=[])

    articles = [
        NewsArticle(
            company_id=1,
            title="Some Article",
            url="https://example.com/1",
            published_at=datetime(2026, 3, 18),
            source_name="Reuters",
        ),
    ]
    news_source.fetch_articles = AsyncMock(return_value=articles)
    sentiment.analyze_batch = AsyncMock(return_value=[None])

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    await pipeline.refresh_company(_make_company(), repos)

    repos.news_repo.save_many.assert_called_once()
    assert articles[0].sentiment is None


@pytest.mark.asyncio
async def test_refresh_company_no_news() -> None:
    """News repo is not called when no articles found."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    stock_source.fetch_current_price = AsyncMock(return_value=None)
    patent_source.search_patents = AsyncMock(return_value=[])
    news_source.fetch_articles = AsyncMock(return_value=[])

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    await pipeline.refresh_company(_make_company(), repos)

    sentiment.analyze_batch.assert_not_called()
    repos.news_repo.save_many.assert_not_called()


# --- SectorPipeline.refresh_all tests ---


@pytest.mark.asyncio
async def test_refresh_all_success() -> None:
    """All companies are processed successfully."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    stock_source.fetch_current_price = AsyncMock(return_value=None)
    patent_source.search_patents = AsyncMock(return_value=[])
    news_source.fetch_articles = AsyncMock(return_value=[])

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    companies = [
        _make_company(id=1, name="IonQ", slug="ionq"),
        _make_company(id=2, name="Rigetti", slug="rigetti", ticker="RGTI"),
    ]

    result = await pipeline.refresh_all(companies, repos)

    assert result.companies_processed == 2
    assert result.has_errors is False
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_refresh_all_partial_failure() -> None:
    """One company failure doesn't prevent others from processing."""
    config = _make_config()
    stock_source = AsyncMock()
    patent_source = AsyncMock()
    news_source = AsyncMock()
    sentiment = AsyncMock()

    call_count = 0

    async def _fetch_price(ticker: str) -> StockPrice | None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("API timeout")
        return None

    stock_source.fetch_current_price = _fetch_price
    patent_source.search_patents = AsyncMock(return_value=[])
    news_source.fetch_articles = AsyncMock(return_value=[])

    pipeline = SectorPipeline(
        config, stock_source, patent_source, news_source, sentiment
    )
    repos = _make_repos()

    companies = [
        _make_company(id=1, name="IonQ", slug="ionq"),
        _make_company(id=2, name="Rigetti", slug="rigetti", ticker="RGTI"),
    ]

    result = await pipeline.refresh_all(companies, repos)

    assert result.companies_processed == 1
    assert result.has_errors is True
    assert len(result.errors) == 1
    assert "IonQ" in result.errors[0]
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_refresh_all_empty_list() -> None:
    """Empty company list returns zero-result."""
    config = _make_config()
    pipeline = SectorPipeline(
        config, AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock()
    )
    repos = _make_repos()

    result = await pipeline.refresh_all([], repos)

    assert result.companies_processed == 0
    assert result.has_errors is False
