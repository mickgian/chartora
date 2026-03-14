"""Value objects for the Chartora domain layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


class Sector(StrEnum):
    """Company sector classification."""

    PURE_PLAY = "pure_play"
    BIG_TECH = "big_tech"
    ETF = "etf"


class SentimentLabel(StrEnum):
    """Sentiment classification for news articles."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class FilingType(StrEnum):
    """SEC filing types."""

    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_4 = "Form4"
    FORM_13F = "13F"


class PatentSource(StrEnum):
    """Patent data source."""

    USPTO = "USPTO"
    EPO = "EPO"


class TrendDirection(StrEnum):
    """Rank change direction."""

    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class SubscriptionStatus(StrEnum):
    """User subscription status."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    INACTIVE = "inactive"


@dataclass(frozen=True)
class Ticker:
    """A stock ticker symbol."""

    symbol: str

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("Ticker symbol cannot be empty")
        if not self.symbol.isalpha():
            raise ValueError(
                f"Ticker symbol must contain only letters, got '{self.symbol}'"
            )
        # Ensure uppercase via object.__setattr__ since frozen
        object.__setattr__(self, "symbol", self.symbol.upper())

    def __str__(self) -> str:
        return self.symbol


@dataclass(frozen=True)
class ScoreComponent:
    """A single component of the Quantum Power Score (0-100 scale)."""

    name: str
    raw_value: float
    normalized_value: float
    weight: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.normalized_value <= 100.0:
            raise ValueError(
                "Normalized value must be between 0 and 100, "
                f"got {self.normalized_value}"
            )
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be between 0 and 1, got {self.weight}")

    @property
    def weighted_value(self) -> float:
        """Calculate the weighted contribution to the total score."""
        return self.normalized_value * self.weight


@dataclass(frozen=True)
class DateRange:
    """An inclusive date range."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError(
                f"Start date ({self.start}) must not be after end date ({self.end})"
            )

    @property
    def days(self) -> int:
        """Number of days in the range (inclusive)."""
        return (self.end - self.start).days + 1

    def contains(self, d: date) -> bool:
        """Check whether a date falls within this range."""
        return self.start <= d <= self.end
