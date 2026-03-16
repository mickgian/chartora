"""News API adapter for fetching news articles.

Implements the NewsDataSource interface using the NewsAPI.org REST API.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from src.domain.interfaces.data_sources import NewsDataSource
from src.domain.models.entities import NewsArticle

logger = logging.getLogger(__name__)

NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"


class NewsApiAdapter(NewsDataSource):
    """Fetches news articles from the NewsAPI.org API."""

    def __init__(
        self,
        api_key: str,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._client = http_client
        self._timeout = timeout

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def fetch_articles(
        self,
        company_name: str,
        ticker: str | None = None,
        limit: int = 10,
    ) -> list[NewsArticle]:
        """Fetch recent news articles about a company."""
        try:
            client = await self._get_client()
            query = self._build_query(company_name, ticker)
            params: dict[str, Any] = {
                "q": query,
                "sortBy": "publishedAt",
                "pageSize": min(limit, 100),
                "language": "en",
                "apiKey": self._api_key,
            }

            response = await client.get(NEWSAPI_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                logger.error(
                    "NewsAPI error for %s: %s",
                    company_name,
                    data.get("message", "Unknown error"),
                )
                return []

            return self._parse_articles(data)
        except httpx.HTTPStatusError as e:
            logger.error(
                "NewsAPI HTTP error for %s: %s",
                company_name,
                e.response.status_code,
            )
            return []
        except Exception:
            logger.exception("Error fetching news for %s", company_name)
            return []

    @staticmethod
    def _build_query(company_name: str, ticker: str | None = None) -> str:
        """Build a search query combining company name and optional ticker."""
        parts = [f'"{company_name}"']
        if ticker:
            parts.append(f'"{ticker}"')
        return " OR ".join(parts)

    @staticmethod
    def _parse_articles(data: dict[str, Any]) -> list[NewsArticle]:
        """Parse NewsAPI response into NewsArticle entities."""
        articles: list[NewsArticle] = []
        for item in data.get("articles", []):
            title = item.get("title", "")
            url = item.get("url", "")
            if not title or not url or title == "[Removed]":
                continue

            published_str = item.get("publishedAt", "")
            try:
                dt = datetime.fromisoformat(
                    published_str.replace("Z", "+00:00")
                )
                # Convert to UTC then strip tzinfo for naive-timestamp DB column
                published_at = dt.astimezone(UTC).replace(tzinfo=None)
            except (ValueError, TypeError):
                published_at = datetime.utcnow()

            source_name = None
            source = item.get("source")
            if isinstance(source, dict):
                source_name = source.get("name")

            articles.append(
                NewsArticle(
                    company_id=0,  # Caller must set
                    title=title,
                    url=url,
                    published_at=published_at,
                    source_name=source_name,
                )
            )
        return articles
