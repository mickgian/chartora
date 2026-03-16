"""SEC EDGAR XBRL adapter for fetching financial data.

Fetches company financial facts (funding, R&D spending) from the
SEC EDGAR XBRL companyfacts API.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.domain.interfaces.data_sources import FundingDataSource

logger = logging.getLogger(__name__)

EDGAR_XBRL_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
EDGAR_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

DEFAULT_USER_AGENT = "Chartora/1.0 (chartora@example.com)"


class SecEdgarXbrlAdapter(FundingDataSource):
    """Fetches financial data from the SEC EDGAR XBRL API."""

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

    async def fetch_total_funding(self, ticker: str) -> float | None:
        """Fetch total stockholders' equity as a proxy for funding strength.

        Falls back to total assets if equity is not available.
        """
        try:
            facts = await self._fetch_company_facts(ticker)
            if facts is None:
                return None

            us_gaap = facts.get("facts", {}).get("us-gaap", {})

            # Try stockholders' equity first
            equity = self._get_latest_value(us_gaap, "StockholdersEquity")
            if equity is not None:
                return equity

            # Fallback to total assets
            return self._get_latest_value(us_gaap, "Assets")
        except Exception:
            logger.exception("Error fetching total funding for %s", ticker)
            return None

    async def fetch_rd_spending(self, ticker: str) -> dict[str, float | None]:
        """Fetch R&D spending data from XBRL filings.

        Returns:
            A dict with 'rd_expense', 'total_revenue', 'rd_ratio'.
        """
        result: dict[str, float | None] = {
            "rd_expense": None,
            "total_revenue": None,
            "rd_ratio": None,
        }

        try:
            facts = await self._fetch_company_facts(ticker)
            if facts is None:
                return result

            us_gaap = facts.get("facts", {}).get("us-gaap", {})

            rd_expense = self._get_latest_value(
                us_gaap, "ResearchAndDevelopmentExpense"
            )
            total_revenue = self._get_latest_value(
                us_gaap, "Revenues"
            ) or self._get_latest_value(
                us_gaap, "RevenueFromContractWithCustomerExcludingAssessedTax"
            )

            result["rd_expense"] = rd_expense
            result["total_revenue"] = total_revenue

            if rd_expense is not None and total_revenue and total_revenue > 0:
                result["rd_ratio"] = round(rd_expense / total_revenue, 4)

            return result
        except Exception:
            logger.exception("Error fetching R&D spending for %s", ticker)
            return result

    async def _fetch_company_facts(self, ticker: str) -> dict[str, Any] | None:
        """Fetch XBRL company facts for a ticker."""
        cik = await self._resolve_cik(ticker)
        if not cik:
            logger.warning("Could not resolve CIK for ticker %s", ticker)
            return None

        client = await self._get_client()
        url = EDGAR_XBRL_URL.format(cik=cik)
        response = await client.get(url)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    async def _resolve_cik(self, ticker: str) -> str | None:
        """Resolve a ticker symbol to a zero-padded CIK number."""
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
    def _get_latest_value(us_gaap: dict[str, Any], concept: str) -> float | None:
        """Extract the most recent value for an XBRL concept.

        Prefers 10-K (annual) filings, falls back to 10-Q.
        """
        concept_data = us_gaap.get(concept, {})
        units = concept_data.get("units", {})

        # Financial values are typically in USD
        values = units.get("USD", [])
        if not values:
            return None

        # Filter for 10-K filings (annual), prefer most recent
        annual = [
            v for v in values if v.get("form") == "10-K" and v.get("val") is not None
        ]
        if annual:
            latest = max(annual, key=lambda v: v.get("end", ""))
            return float(latest["val"])

        # Fallback to 10-Q
        quarterly = [
            v for v in values if v.get("form") == "10-Q" and v.get("val") is not None
        ]
        if quarterly:
            latest = max(quarterly, key=lambda v: v.get("end", ""))
            return float(latest["val"])

        # Fallback to any value
        with_val = [v for v in values if v.get("val") is not None]
        if with_val:
            latest = max(with_val, key=lambda v: v.get("end", ""))
            return float(latest["val"])

        return None
