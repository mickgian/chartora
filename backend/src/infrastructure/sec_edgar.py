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
    "D": FilingType.FORM_D,
}

# SEC EDGAR full-text search API for Form D filings
EDGAR_EFTS_URL = (
    "https://efts.sec.gov/LATEST/search-index?"
    "q=%22{company}%22&forms=D&dateRange=custom"
    "&startdt={start}&enddt={end}"
)


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

    async def fetch_form_d_filings(self, company_name: str) -> list[Filing]:
        """Fetch Form D filings (private placement fundraising via Reg D).

        Form D filings are submitted when companies raise capital through
        exempt securities offerings. They contain the total offering amount,
        amount sold, and remaining amount.

        Uses EDGAR full-text search since Form D filers may not have a
        standard CIK/ticker mapping.
        """
        try:
            client = await self._get_client()
            today = date.today()
            start = today.replace(year=today.year - 3)

            url = EDGAR_EFTS_URL.format(
                company=company_name.replace(" ", "+"),
                start=start.isoformat(),
                end=today.isoformat(),
            )
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            hits = data.get("hits", {}).get("hits", [])
            filings: list[Filing] = []
            for hit in hits:
                source = hit.get("_source", {})
                filing_date_str = source.get("file_date", "")
                try:
                    filing_date = date.fromisoformat(filing_date_str)
                except (ValueError, TypeError):
                    continue

                accession = source.get("accession_no", "")
                entity_name = source.get("entity_name", "")
                display_name = source.get("display_names", [entity_name])
                label = display_name[0] if display_name else entity_name
                description = f"Form D — {label}"

                file_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{accession.replace('-', '')}/{accession}-index.htm"
                    if accession
                    else None
                )

                filings.append(
                    Filing(
                        company_id=0,
                        filing_type=FilingType.FORM_D,
                        filing_date=filing_date,
                        description=description,
                        url=file_url,
                        data_json=json.dumps({
                            "form": "D",
                            "accession": accession,
                            "entity_name": entity_name,
                        }),
                    )
                )

            logger.info(
                "Found %d Form D filings for %s", len(filings), company_name
            )
            return filings
        except httpx.HTTPStatusError as e:
            logger.error(
                "SEC EDGAR HTTP error for Form D search '%s': %s",
                company_name,
                e.response.status_code,
            )
            return []
        except Exception:
            logger.exception(
                "Error fetching Form D filings for %s", company_name
            )
            return []

    async def fetch_form_d_total_raised(self, ticker: str) -> float | None:
        """Fetch total amount raised from Form D filings via XBRL/submissions.

        Parses the Form D filing data from EDGAR submissions to extract
        the totalOfferingAmount and totalAmountSold fields.
        """
        try:
            cik = await self._resolve_cik(ticker)
            if not cik:
                return None

            client = await self._get_client()
            url = EDGAR_SUBMISSIONS_URL.format(cik=cik)
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            primary_docs = recent.get("primaryDocument", [])
            accession_numbers = recent.get("accessionNumber", [])

            total_raised = 0.0
            seen_accessions: set[str] = set()

            for i, form_type in enumerate(forms):
                if form_type not in ("D", "D/A"):
                    continue
                accession = accession_numbers[i] if i < len(accession_numbers) else ""
                if accession in seen_accessions:
                    continue
                seen_accessions.add(accession)

                # Try to fetch the Form D XML for offering amount
                if accession and i < len(primary_docs):
                    amount = await self._extract_form_d_amount(
                        client, cik, accession, primary_docs[i]
                    )
                    if amount is not None:
                        total_raised += amount

            return total_raised if total_raised > 0 else None
        except Exception:
            logger.exception(
                "Error fetching Form D total raised for %s", ticker
            )
            return None

    async def _extract_form_d_amount(
        self,
        client: httpx.AsyncClient,
        cik: str,
        accession: str,
        primary_doc: str,
    ) -> float | None:
        """Extract totalAmountSold from a Form D XML filing."""
        try:
            clean_accession = accession.replace("-", "")
            # Form D primary documents are XML
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik.lstrip('0')}/{clean_accession}/{primary_doc}"
            )
            response = await client.get(doc_url)
            if response.status_code != 200:
                return None

            text = response.text
            # Parse totalAmountSold from Form D XML
            # The field is <totalAmountSold>123456</totalAmountSold>
            import re

            match = re.search(r"<totalAmountSold>(\d+\.?\d*)</totalAmountSold>", text)
            if match:
                return float(match.group(1))

            # Fallback: try totalOfferingAmount
            match = re.search(
                r"<totalOfferingAmount>(\d+\.?\d*)</totalOfferingAmount>", text
            )
            if match:
                return float(match.group(1))

            return None
        except Exception:
            logger.debug(
                "Could not extract Form D amount from %s/%s", cik, accession
            )
            return None

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
