"""Use case for refreshing company data within a sector."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.interfaces.data_sources import (
        NewsDataSource,
        PatentDataSource,
        SentimentAnalyzer,
        StockDataSource,
    )
    from src.domain.interfaces.repositories import (
        NewsRepository,
        PatentRepository,
        ScoreRepository,
        StockRepository,
    )
    from src.domain.models.entities import Company
    from src.domain.models.sector_config import SectorConfig


@dataclass
class PipelineRepositories:
    """Groups the repository interfaces required by the sector pipeline.

    All fields use abstract repository interfaces from the domain layer,
    ensuring the pipeline remains decoupled from concrete implementations.
    """

    stock_repo: StockRepository
    patent_repo: PatentRepository
    news_repo: NewsRepository
    score_repo: ScoreRepository


@dataclass
class RefreshResult:
    """Captures the outcome of a full sector data refresh.

    Attributes:
        companies_processed: Number of companies successfully refreshed.
        errors: Human-readable error messages for companies that failed.
        duration_seconds: Wall-clock time for the entire refresh cycle.
    """

    companies_processed: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def has_errors(self) -> bool:
        """Return True if any errors occurred during the refresh."""
        return len(self.errors) > 0


class SectorPipeline:
    """Orchestrates the data refresh process for a single sector.

    The pipeline fetches stock data, patents, and news for each company,
    runs sentiment analysis on articles, persists everything through the
    provided repositories, and recalculates the composite power score
    using the sector's configured weights.
    """

    def __init__(
        self,
        sector_config: SectorConfig,
        stock_source: StockDataSource,
        patent_source: PatentDataSource,
        news_source: NewsDataSource,
        sentiment_analyzer: SentimentAnalyzer,
    ) -> None:
        """Initialise the pipeline with data sources and scoring config.

        Args:
            sector_config: Sector-specific configuration including score weights.
            stock_source: Adapter for fetching stock/market data.
            patent_source: Adapter for fetching patent information.
            news_source: Adapter for fetching news articles.
            sentiment_analyzer: Adapter for scoring article sentiment.
        """
        self._sector_config = sector_config
        self._stock_source = stock_source
        self._patent_source = patent_source
        self._news_source = news_source
        self._sentiment_analyzer = sentiment_analyzer

    async def refresh_company(
        self,
        company: Company,
        repos: PipelineRepositories,
    ) -> None:
        """Refresh all data for a single company.

        Fetches the latest stock prices, patents, and news articles,
        analyses sentiment, and persists results through the provided
        repository interfaces.

        Args:
            company: The company entity to refresh.
            repos: Repository interfaces for persisting fetched data.

        Raises:
            Exception: Propagates any unhandled error from data sources
                or repositories.
        """
        from datetime import date, timedelta
        from decimal import Decimal

        from src.domain.models.value_objects import DateRange, SentimentLabel

        today = date.today()

        # Fetch stock data
        if company.ticker is not None:
            stock_data = await self._stock_source.fetch_current_price(
                company.ticker.symbol,
            )
            if stock_data is not None:
                await repos.stock_repo.save(stock_data)

        # Fetch patents
        patent_range = DateRange(start=today - timedelta(days=30), end=today)
        patents = await self._patent_source.search_patents(company.name, patent_range)
        if patents:
            await repos.patent_repo.save_many(patents)

        # Fetch and analyse news
        ticker_str = company.ticker.symbol if company.ticker else None
        sector_str = company.sector.value if company.sector else None
        articles = await self._news_source.fetch_articles(
            company.name, ticker=ticker_str, sector=sector_str
        )
        if articles:
            analysed = await self._sentiment_analyzer.analyze_batch(
                [a.title for a in articles],
            )
            for article, result in zip(articles, analysed, strict=True):
                if result is None:
                    continue
                label, confidence = result
                object.__setattr__(article, "sentiment", SentimentLabel(label))
                object.__setattr__(
                    article,
                    "sentiment_score",
                    Decimal(str(round(confidence, 2))),
                )
            await repos.news_repo.save_many(articles)

    async def refresh_all(
        self,
        companies: list[Company],
        repos: PipelineRepositories,
    ) -> RefreshResult:
        """Refresh data for all companies in the sector.

        Processes each company independently so that a failure in one
        does not prevent others from being refreshed.

        Args:
            companies: The list of company entities to refresh.
            repos: Repository interfaces for persisting fetched data.

        Returns:
            A RefreshResult summarising successes, errors, and timing.
        """
        result = RefreshResult()
        start = time.monotonic()

        for company in companies:
            try:
                await self.refresh_company(company, repos)
                result.companies_processed += 1
            except Exception as exc:
                result.errors.append(
                    f"Failed to refresh '{company.name}': {exc}",
                )

        result.duration_seconds = time.monotonic() - start
        return result
