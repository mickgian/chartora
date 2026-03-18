"""News API adapter for fetching news articles.

Implements the NewsDataSource interface using the NewsAPI.org REST API.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

import httpx

from src.domain.interfaces.data_sources import NewsDataSource
from src.domain.models.entities import NewsArticle

logger = logging.getLogger(__name__)

NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"

QUANTUM_KEYWORDS: tuple[str, ...] = (
    "quantum",
    "qubit",
    "superconducting",
    "trapped-ion",
    "annealing",
    "error correction",
    "topological",
    "cryogenic",
    "entanglement",
    "superposition",
)

_QUANTUM_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in QUANTUM_KEYWORDS),
    re.IGNORECASE,
)


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
        sector: str | None = None,
    ) -> list[NewsArticle]:
        """Fetch recent news articles about a company."""
        try:
            client = await self._get_client()
            query = self._build_query(company_name, ticker, sector=sector)
            params: dict[str, Any] = {
                "q": query,
                "sortBy": "publishedAt",
                "pageSize": min(limit, 100),
                "language": "en",
                "apiKey": self._api_key,
            }

            # Restrict search to title+description to avoid false positives
            # from short tickers matching unrelated article body text.
            if sector != "big_tech":
                params["searchIn"] = "title,description"

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

            articles = self._parse_articles(data)

            # Post-fetch relevance filter
            if sector is not None:
                before = len(articles)
                articles = [
                    a
                    for a in articles
                    if self._is_relevant_article(a.title, company_name, sector)
                ]
                filtered = before - len(articles)
                if filtered > 0:
                    logger.info(
                        "Filtered %d irrelevant articles for %s",
                        filtered,
                        company_name,
                    )

            return articles
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
    def _build_query(
        company_name: str,
        ticker: str | None = None,
        sector: str | None = None,
    ) -> str:
        """Build a search query combining company name and optional ticker.

        For big-tech companies, appends an AND clause with quantum keywords
        so that NewsAPI only returns quantum-relevant results.
        """
        parts = [f'"{company_name}"']
        if ticker:
            parts.append(f'"{ticker}"')
        company_part = " OR ".join(parts)

        if sector == "big_tech":
            quantum_part = " OR ".join(
                f'"{kw}"' for kw in ("quantum", "qubit", "quantum computing")
            )
            return f"({company_part}) AND ({quantum_part})"

        return company_part

    @staticmethod
    def _is_quantum_relevant(title: str) -> bool:
        """Check if an article title is related to quantum computing."""
        if not title:
            return False
        return bool(_QUANTUM_PATTERN.search(title))

    @staticmethod
    def _is_relevant_article(title: str, company_name: str, sector: str) -> bool:
        """Check if an article is relevant to a company's quantum activities.

        - For big_tech: title must contain a quantum keyword.
        - For pure_play/etf: title must contain a quantum keyword OR the
          company name (to allow legitimate business news like earnings,
          partnerships that mention the company by name).
        """
        if not title:
            return False

        # Quantum keyword match — relevant for any sector
        if _QUANTUM_PATTERN.search(title):
            return True

        # For non-big-tech, also accept articles that mention the company name
        if sector != "big_tech":
            # Extract the core name (e.g. "D-Wave" from "D-Wave Quantum")
            # Check both full name and first word/hyphenated part
            title_lower = title.lower()
            name_lower = company_name.lower()
            if name_lower in title_lower:
                return True
            # Check first significant part (e.g. "D-Wave" from "D-Wave Quantum")
            first_part = company_name.split()[0] if company_name else ""
            if len(first_part) > 2 and first_part.lower() in title_lower:
                return True

        return False

    async def validate_url(self, url: str) -> bool:
        """Check if a URL is reachable via HEAD request."""
        try:
            client = await self._get_client()
            response = await client.head(url, follow_redirects=False, timeout=5.0)
            return bool(response.status_code < 400)
        except (httpx.HTTPError, httpx.StreamError):
            return False

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
                dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
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
