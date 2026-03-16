"""Repository interfaces (ports) for the Chartora domain layer.

These define the contracts that infrastructure adapters must implement.
Domain and use case layers depend only on these interfaces,
never on concrete implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.models.entities import (
        AlertPreference,
        ApiKey,
        Company,
        Filing,
        GovernmentContract,
        NewsArticle,
        Patent,
        QuantumPowerScore,
        StockPrice,
        User,
    )
    from src.domain.models.value_objects import DateRange


class CompanyRepository(ABC):
    """Port for persisting and retrieving Company entities."""

    @abstractmethod
    async def get_by_id(self, company_id: int) -> Company | None:
        """Retrieve a company by its ID."""

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Company | None:
        """Retrieve a company by its URL slug."""

    @abstractmethod
    async def get_all(self) -> list[Company]:
        """Retrieve all tracked companies."""

    @abstractmethod
    async def save(self, company: Company) -> Company:
        """Persist a company entity. Returns the saved entity with ID set."""

    @abstractmethod
    async def delete(self, company_id: int) -> None:
        """Delete a company by ID."""


class StockRepository(ABC):
    """Port for persisting and retrieving stock price data."""

    @abstractmethod
    async def get_latest(self, company_id: int) -> StockPrice | None:
        """Get the most recent stock price for a company."""

    @abstractmethod
    async def get_by_date_range(
        self, company_id: int, date_range: DateRange
    ) -> list[StockPrice]:
        """Get stock prices for a company within a date range."""

    @abstractmethod
    async def save(self, stock_price: StockPrice) -> StockPrice:
        """Persist a stock price record."""

    @abstractmethod
    async def save_many(self, stock_prices: list[StockPrice]) -> list[StockPrice]:
        """Persist multiple stock price records."""


class PatentRepository(ABC):
    """Port for persisting and retrieving patent data."""

    @abstractmethod
    async def get_by_company(self, company_id: int) -> list[Patent]:
        """Get all patents for a company."""

    @abstractmethod
    async def get_by_date_range(
        self, company_id: int, date_range: DateRange
    ) -> list[Patent]:
        """Get patents filed within a date range for a company."""

    @abstractmethod
    async def count_by_date_range(self, company_id: int, date_range: DateRange) -> int:
        """Count patents filed within a date range for a company."""

    @abstractmethod
    async def save(self, patent: Patent) -> Patent:
        """Persist a patent record."""

    @abstractmethod
    async def save_many(self, patents: list[Patent]) -> list[Patent]:
        """Persist multiple patent records."""


class ScoreRepository(ABC):
    """Port for persisting and retrieving Quantum Power Scores."""

    @abstractmethod
    async def get_latest(self, company_id: int) -> QuantumPowerScore | None:
        """Get the most recent score for a company."""

    @abstractmethod
    async def get_latest_all(self) -> list[QuantumPowerScore]:
        """Get the most recent scores for all companies."""

    @abstractmethod
    async def get_by_date_range(
        self, company_id: int, date_range: DateRange
    ) -> list[QuantumPowerScore]:
        """Get scores for a company within a date range."""

    @abstractmethod
    async def save(self, score: QuantumPowerScore) -> QuantumPowerScore:
        """Persist a score record."""

    @abstractmethod
    async def save_many(
        self, scores: list[QuantumPowerScore]
    ) -> list[QuantumPowerScore]:
        """Persist multiple score records."""


class NewsRepository(ABC):
    """Port for persisting and retrieving news articles."""

    @abstractmethod
    async def get_by_company(
        self, company_id: int, limit: int = 20
    ) -> list[NewsArticle]:
        """Get recent news articles for a company, ordered by date descending."""

    @abstractmethod
    async def get_by_date_range(
        self, company_id: int, date_range: DateRange
    ) -> list[NewsArticle]:
        """Get news articles within a date range for a company."""

    @abstractmethod
    async def save(self, article: NewsArticle) -> NewsArticle:
        """Persist a news article."""

    @abstractmethod
    async def save_many(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        """Persist multiple news articles."""


class FilingRepository(ABC):
    """Port for persisting and retrieving SEC filings."""

    @abstractmethod
    async def get_by_company(self, company_id: int) -> list[Filing]:
        """Get all filings for a company."""

    @abstractmethod
    async def get_by_type(self, company_id: int, filing_type: str) -> list[Filing]:
        """Get filings of a specific type for a company."""

    @abstractmethod
    async def save(self, filing: Filing) -> Filing:
        """Persist a filing record."""

    @abstractmethod
    async def save_many(self, filings: list[Filing]) -> list[Filing]:
        """Persist multiple filing records."""


class GovernmentContractRepository(ABC):
    """Port for persisting and retrieving government contracts."""

    @abstractmethod
    async def get_by_company(self, company_id: int) -> list[GovernmentContract]:
        """Get all government contracts for a company."""

    @abstractmethod
    async def get_total_value(self, company_id: int) -> float:
        """Get total contract value for a company."""

    @abstractmethod
    async def save(self, contract: GovernmentContract) -> GovernmentContract:
        """Persist a government contract."""

    @abstractmethod
    async def save_many(
        self, contracts: list[GovernmentContract]
    ) -> list[GovernmentContract]:
        """Persist multiple government contracts."""


class UserRepository(ABC):
    """Port for persisting and retrieving User entities."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by ID."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by email address."""

    @abstractmethod
    async def get_by_stripe_customer_id(self, customer_id: str) -> User | None:
        """Retrieve a user by Stripe customer ID."""

    @abstractmethod
    async def get_by_stripe_subscription_id(self, subscription_id: str) -> User | None:
        """Retrieve a user by Stripe subscription ID."""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Create or update a user entity."""

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user entity."""

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        """Delete a user by ID."""


class AlertPreferenceRepository(ABC):
    """Port for persisting and retrieving alert preferences."""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[AlertPreference]:
        """Get all alert preferences for a user."""

    @abstractmethod
    async def get_enabled_by_type(self, alert_type: str) -> list[AlertPreference]:
        """Get all enabled preferences for a given alert type."""

    @abstractmethod
    async def save(self, pref: AlertPreference) -> AlertPreference:
        """Create or update an alert preference."""

    @abstractmethod
    async def delete(self, pref_id: int) -> None:
        """Delete an alert preference by ID."""


class ApiKeyRepository(ABC):
    """Port for persisting and retrieving API keys."""

    @abstractmethod
    async def get_by_key_hash(self, key_hash: str) -> ApiKey | None:
        """Retrieve an API key by its hash."""

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[ApiKey]:
        """Get all API keys for a user."""

    @abstractmethod
    async def save(self, api_key: ApiKey) -> ApiKey:
        """Create a new API key."""

    @abstractmethod
    async def update(self, api_key: ApiKey) -> ApiKey:
        """Update an API key (e.g. last_used_at)."""

    @abstractmethod
    async def delete(self, key_id: int) -> None:
        """Delete an API key by ID."""
