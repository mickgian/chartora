"""Data source interfaces (ports) for external data providers.

These abstract classes define the contracts for fetching data from
external APIs (Yahoo Finance, USPTO, NewsAPI, SEC EDGAR, etc.).
Infrastructure adapters implement these.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.models.entities import (
        Filing,
        GovernmentContract,
        NewsArticle,
        Patent,
        StockPrice,
    )
    from src.domain.models.value_objects import DateRange


class StockDataSource(ABC):
    """Port for fetching stock price data from an external provider."""

    @abstractmethod
    async def fetch_current_price(self, ticker: str) -> StockPrice | None:
        """Fetch the most recent stock price for a ticker."""

    @abstractmethod
    async def fetch_history(
        self, ticker: str, date_range: DateRange
    ) -> list[StockPrice]:
        """Fetch historical stock prices for a ticker within a date range."""

    @abstractmethod
    async def fetch_market_cap(self, ticker: str) -> int | None:
        """Fetch the current market capitalization for a ticker."""

    @abstractmethod
    async def fetch_performance(self, ticker: str, days: int) -> float | None:
        """Fetch stock performance (% change) over a given number of days."""


class PatentDataSource(ABC):
    """Port for fetching patent data from patent offices."""

    @abstractmethod
    async def search_patents(
        self, company_name: str, date_range: DateRange
    ) -> list[Patent]:
        """Search for patents filed by a company within a date range."""

    @abstractmethod
    async def get_patent_count(self, company_name: str, date_range: DateRange) -> int:
        """Get the count of patents filed by a company within a date range."""


class NewsDataSource(ABC):
    """Port for fetching news articles from a news provider."""

    @abstractmethod
    async def fetch_articles(
        self, company_name: str, ticker: str | None = None, limit: int = 10
    ) -> list[NewsArticle]:
        """Fetch recent news articles about a company."""


class FilingDataSource(ABC):
    """Port for fetching SEC filings."""

    @abstractmethod
    async def fetch_filings(
        self, ticker: str, filing_types: list[str] | None = None
    ) -> list[Filing]:
        """Fetch SEC filings for a company."""

    @abstractmethod
    async def fetch_insider_trades(self, ticker: str) -> list[Filing]:
        """Fetch Form 4 insider trading filings."""

    @abstractmethod
    async def fetch_institutional_holdings(self, ticker: str) -> list[Filing]:
        """Fetch 13F institutional ownership filings."""


class GovernmentContractDataSource(ABC):
    """Port for fetching government contract data."""

    @abstractmethod
    async def search_contracts(
        self, company_name: str, limit: int = 50
    ) -> list[GovernmentContract]:
        """Search for government contracts awarded to a company."""

    @abstractmethod
    async def get_total_contract_value(self, company_name: str) -> float:
        """Get total value of government contracts for a company."""


class FundingDataSource(ABC):
    """Port for fetching funding and financial data from SEC EDGAR XBRL."""

    @abstractmethod
    async def fetch_total_funding(self, ticker: str) -> float | None:
        """Fetch total assets or equity as a proxy for funding strength."""

    @abstractmethod
    async def fetch_rd_spending(self, ticker: str) -> dict[str, float | None]:
        """Fetch R&D spending data.

        Returns:
            A dict with keys 'rd_expense', 'total_revenue', 'rd_ratio'.
        """


class SentimentAnalyzer(ABC):
    """Port for analyzing sentiment of news articles."""

    @abstractmethod
    async def analyze(self, text: str) -> tuple[str, float]:
        """Analyze sentiment of text.

        Returns:
            A tuple of (sentiment_label, confidence_score) where
            sentiment_label is one of 'bullish', 'bearish', 'neutral'
            and confidence_score is between 0.0 and 1.0.
        """

    @abstractmethod
    async def analyze_batch(self, texts: list[str]) -> list[tuple[str, float]]:
        """Analyze sentiment of multiple texts."""
