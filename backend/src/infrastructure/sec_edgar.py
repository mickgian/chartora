"""SEC EDGAR adapter for fetching company filings.

Implements the FilingDataSource interface using the SEC EDGAR REST API.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

import httpx

from src.domain.interfaces.data_sources import FilingDataSource
from src.domain.models.entities import Filing
from src.domain.models.value_objects import FilingType

logger = logging.getLogger(__name__)

# SEC EDGAR API base URLs
EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
EDGAR_COMPANY_SEARCH_URL = (
    "https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom"
    "&startdt={start}&enddt={end}&forms={forms}"
)
EDGAR_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# SEC requires a User-Agent header
DEFAULT_USER_AGENT = "Chartora/1.0 (chartora@example.com)"

# Mapping from SEC form types to our FilingType enum
FORM_TYPE_MAP: dict[str, FilingType] = {
    "10-K": FilingType.FORM_10K,
    "10-Q": FilingType.FORM_10Q,
    "4": FilingType.FORM_4,
    "13F-HR": FilingType.FORM_13F,
}


class SecEdgarAdapter(FilingDataSource):
    """Fetches SEC filing data from the EDGAR REST API."""

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = 30.0,
    ) -> None:
        self._client = http_client
        self._user_agent = user_agent
        self._timeout = timeout
        self._cik_cache: dict[str, str] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client with required headers."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers={"User-Agent": self._user_agent},
            )
        return self._client

    async def fetch_filings(
        self, ticker: str, filing_types: list[str] | None = None
    ) -> list[Filing]:
        """Fetch SEC filings for a company."""
        try:
            cik = await self._resolve_cik(ticker)
            if not cik:
                logger.warning("Could not resolve CIK for ticker %s", ticker)
                return []

            client = await self._get_client()
            url = EDGAR_SUBMISSIONS_URL.format(cik=cik)
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            return self._parse_filings(data, filing_types)
        except httpx.HTTPStatusError as e:
            logger.error(
                "SEC EDGAR HTTP error for %s: %s", ticker, e.response.status_code
            )
            return []
        except Exception:
            logger.exception("Error fetching filings for %s", ticker)
            return []

    async def fetch_insider_trades(self, ticker: str) -> list[Filing]:
        """Fetch Form 4 insider trading filings."""
        return await self.fetch_filings(ticker, filing_types=["4"])

    async def fetch_institutional_holdings(self, ticker: str) -> list[Filing]:
        """Fetch 13F institutional ownership filings."""
        return await self.fetch_filings(ticker, filing_types=["13F-HR"])

    async def _resolve_cik(self, ticker: str) -> str | None:
        """Resolve a ticker symbol to a CIK number."""
        if ticker in self._cik_cache:
            return self._cik_cache[ticker]

        try:
            client = await self._get_client()
            response = await client.get(EDGAR_COMPANY_TICKERS_URL)
            response.raise_for_status()
            data = response.json()

            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    cik = str(entry["cik_str"]).zfill(10)
                    self._cik_cache[ticker] = cik
                    return cik
        except Exception:
            logger.exception("Error resolving CIK for %s", ticker)

        return None

    @staticmethod
    def _parse_filings(
        data: dict[str, Any],
        filing_types: list[str] | None = None,
    ) -> list[Filing]:
        """Parse EDGAR submissions JSON into Filing entities."""
        filings: list[Filing] = []
        recent = data.get("filings", {}).get("recent", {})
        if not recent:
            return filings

        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        descriptions = recent.get("primaryDocDescription", [])
        accession_numbers = recent.get("accessionNumber", [])

        for i, form_type in enumerate(forms):
            # Filter by requested filing types
            if filing_types and form_type not in filing_types:
                continue

            # Map to our FilingType enum
            mapped_type = FORM_TYPE_MAP.get(form_type)
            if mapped_type is None:
                continue

            filing_date_str = dates[i] if i < len(dates) else ""
            try:
                filing_date = date.fromisoformat(filing_date_str)
            except (ValueError, TypeError, IndexError):
                continue

            description = descriptions[i] if i < len(descriptions) else None
            accession = accession_numbers[i] if i < len(accession_numbers) else ""
            url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{accession.replace('-', '')}/{accession}-index.htm"
                if accession
                else None
            )

            filings.append(
                Filing(
                    company_id=0,  # Caller must set
                    filing_type=mapped_type,
                    filing_date=filing_date,
                    description=description,
                    url=url,
                    data_json=json.dumps({"form": form_type, "accession": accession}),
                )
            )

        return filings
