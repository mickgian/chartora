"""Domain entities for the Chartora domain layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.domain.models.value_objects import (
    FilingType,
    PatentSource,
    Sector,
    SentimentLabel,
    SubscriptionStatus,
    Ticker,
    TrendDirection,
)

if TYPE_CHECKING:
    from datetime import date, datetime
    from decimal import Decimal


@dataclass
class Company:
    """A quantum computing company tracked by Chartora."""

    name: str
    slug: str
    sector: Sector
    ticker: Ticker | None = None
    description: str | None = None
    is_etf: bool = False
    website: str | None = None
    logo_url: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Company name cannot be empty")
        if not self.slug:
            raise ValueError("Company slug cannot be empty")


@dataclass
class StockPrice:
    """A single day's stock price data for a company."""

    company_id: int
    price_date: date
    close_price: Decimal
    open_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    volume: int | None = None
    market_cap: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if self.close_price < 0:
            raise ValueError("Close price cannot be negative")


@dataclass
class Patent:
    """A patent filing associated with a company."""

    company_id: int
    patent_number: str
    title: str
    filing_date: date
    source: PatentSource = PatentSource.USPTO
    abstract: str | None = None
    grant_date: date | None = None
    classification: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.patent_number:
            raise ValueError("Patent number cannot be empty")
        if not self.title:
            raise ValueError("Patent title cannot be empty")


@dataclass
class FundingRound:
    """A funding round for a company (extracted from SEC filings)."""

    company_id: int
    round_date: date
    amount: Decimal
    round_type: str | None = None
    lead_investor: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Funding amount cannot be negative")


@dataclass
class NewsArticle:
    """A news article about a company."""

    company_id: int
    title: str
    url: str
    published_at: datetime
    source_name: str | None = None
    sentiment: SentimentLabel | None = None
    sentiment_score: Decimal | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("Article title cannot be empty")
        if not self.url:
            raise ValueError("Article URL cannot be empty")


@dataclass
class Filing:
    """An SEC filing associated with a company."""

    company_id: int
    filing_type: FilingType
    filing_date: date
    description: str | None = None
    url: str | None = None
    data_json: str | None = None
    id: int | None = None


@dataclass
class QuantumPowerScore:
    """The composite Quantum Power Score for a company on a given date."""

    company_id: int
    score_date: date
    stock_momentum: float
    patent_velocity: float
    qubit_progress: float
    funding_strength: float
    news_sentiment: float
    total_score: float = field(init=False)
    rank: int | None = None
    rank_change: int | None = None
    id: int | None = None

    # Weights per CLAUDE.md spec
    WEIGHT_STOCK_MOMENTUM: float = 0.20
    WEIGHT_PATENT_VELOCITY: float = 0.25
    WEIGHT_QUBIT_PROGRESS: float = 0.20
    WEIGHT_FUNDING_STRENGTH: float = 0.20
    WEIGHT_NEWS_SENTIMENT: float = 0.15

    def __post_init__(self) -> None:
        for name, value in [
            ("stock_momentum", self.stock_momentum),
            ("patent_velocity", self.patent_velocity),
            ("qubit_progress", self.qubit_progress),
            ("funding_strength", self.funding_strength),
            ("news_sentiment", self.news_sentiment),
        ]:
            if not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be between 0 and 100, got {value}")
        self.total_score = self._calculate_total()

    def _calculate_total(self) -> float:
        """Calculate weighted total score."""
        return round(
            self.stock_momentum * self.WEIGHT_STOCK_MOMENTUM
            + self.patent_velocity * self.WEIGHT_PATENT_VELOCITY
            + self.qubit_progress * self.WEIGHT_QUBIT_PROGRESS
            + self.funding_strength * self.WEIGHT_FUNDING_STRENGTH
            + self.news_sentiment * self.WEIGHT_NEWS_SENTIMENT,
            2,
        )

    @property
    def trend(self) -> TrendDirection:
        """Determine trend direction from rank change."""
        if self.rank_change is None or self.rank_change == 0:
            return TrendDirection.FLAT
        return TrendDirection.UP if self.rank_change > 0 else TrendDirection.DOWN


@dataclass
class User:
    """A registered user with optional premium subscription."""

    email: str
    subscription_status: SubscriptionStatus = SubscriptionStatus.INACTIVE
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.email or "@" not in self.email:
            raise ValueError("A valid email address is required")

    @property
    def is_premium(self) -> bool:
        """Check whether user has an active premium subscription."""
        return self.subscription_status == SubscriptionStatus.ACTIVE
