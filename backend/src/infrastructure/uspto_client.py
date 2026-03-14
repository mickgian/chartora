"""USPTO Patent API adapter for fetching patent data.

Implements the PatentDataSource interface using the USPTO PatentsView API.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx

from src.domain.interfaces.data_sources import PatentDataSource
from src.domain.models.entities import Patent
from src.domain.models.value_objects import DateRange, PatentSource

logger = logging.getLogger(__name__)

# USPTO PatentsView API base URL
PATENTSVIEW_API_URL = "https://api.patentsview.org/patents/query"


class UsptoPatentAdapter(PatentDataSource):
    """Fetches patent data from the USPTO PatentsView API."""

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._client = http_client
        self._timeout = timeout

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def search_patents(
        self, company_name: str, date_range: DateRange
    ) -> list[Patent]:
        """Search for patents filed by a company within a date range."""
        try:
            client = await self._get_client()
            query = self._build_query(company_name, date_range)
            fields = [
                "patent_number",
                "patent_title",
                "patent_date",
                "patent_abstract",
                "patent_type",
            ]
            payload: dict[str, Any] = {
                "q": query,
                "f": fields,
                "o": {"per_page": 100},
            }
            response = await client.post(
                PATENTSVIEW_API_URL,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_patents(data)
        except httpx.HTTPStatusError as e:
            logger.error(
                "USPTO API HTTP error for %s: %s", company_name, e.response.status_code
            )
            return []
        except Exception:
            logger.exception("Error searching patents for %s", company_name)
            return []

    async def get_patent_count(self, company_name: str, date_range: DateRange) -> int:
        """Get the count of patents filed by a company within a date range."""
        try:
            client = await self._get_client()
            query = self._build_query(company_name, date_range)
            payload: dict[str, Any] = {
                "q": query,
                "f": ["patent_number"],
                "o": {"per_page": 1},
            }
            response = await client.post(
                PATENTSVIEW_API_URL,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            count: int = data.get("total_patent_count", 0)
            return count
        except Exception:
            logger.exception("Error getting patent count for %s", company_name)
            return 0

    @staticmethod
    def _build_query(company_name: str, date_range: DateRange) -> dict[str, Any]:
        """Build a PatentsView API query."""
        return {
            "_and": [
                {"_contains": {"assignee_organization": company_name}},
                {"_gte": {"patent_date": date_range.start.isoformat()}},
                {"_lte": {"patent_date": date_range.end.isoformat()}},
            ]
        }

    @staticmethod
    def _parse_patents(data: dict[str, Any]) -> list[Patent]:
        """Parse PatentsView API response into Patent entities."""
        patents_data = data.get("patents")
        if not patents_data:
            return []

        patents: list[Patent] = []
        for item in patents_data:
            patent_number = item.get("patent_number", "")
            title = item.get("patent_title", "")
            if not patent_number or not title:
                continue

            patent_date_str = item.get("patent_date", "")
            try:
                filing_date = date.fromisoformat(patent_date_str)
            except (ValueError, TypeError):
                continue

            patents.append(
                Patent(
                    company_id=0,  # Caller must set
                    patent_number=patent_number,
                    title=title,
                    filing_date=filing_date,
                    source=PatentSource.USPTO,
                    abstract=item.get("patent_abstract"),
                    classification=item.get("patent_type"),
                )
            )
        return patents
