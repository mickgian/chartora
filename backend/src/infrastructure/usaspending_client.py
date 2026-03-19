"""USASpending.gov adapter for fetching government contract data.

Implements the GovernmentContractDataSource interface using the
USASpending.gov REST API.
"""

from __future__ import annotations

import contextlib
import logging
import re
from datetime import date
from decimal import Decimal
from typing import Any

import httpx

from src.domain.interfaces.data_sources import GovernmentContractDataSource
from src.domain.models.entities import GovernmentContract

logger = logging.getLogger(__name__)

USASPENDING_SEARCH_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

# Keywords that indicate a contract is quantum-computing related.
# Used to tag contracts for big-tech companies that have many non-quantum awards.
QUANTUM_KEYWORDS: re.Pattern[str] = re.compile(
    r"quantum|qubit|superconducting\s+processor|cryogenic|topological\s+computing"
    r"|trapped.ion|photonic\s+computing|error.correction\s+code"
    r"|NISQ|QPU|quantum\s+advantage|quantum\s+supremacy",
    re.IGNORECASE,
)

# Alternate / legal entity names for USASpending.gov searches.
# Keys are the company names as stored in the DB (from seed_companies.py).
# Values are additional search terms to try — these are the legal entity
# names that appear as recipients in USASpending.gov federal award records.
ALTERNATE_SEARCH_NAMES: dict[str, list[str]] = {
    # Pure-play quantum — legal entity names verified via USASpending / SAM.gov
    "IonQ": ["IONQ, INC."],
    "D-Wave Quantum": ["D-WAVE SYSTEMS", "D-WAVE SYSTEMS INC"],
    "Rigetti Computing": ["RIGETTI & CO, LLC", "RIGETTI & CO"],
    "Quantum Computing Inc": ["QUANTUM COMPUTING INC"],
    "Arqit Quantum": ["ARQIT LIMITED", "ARQIT"],
    "Zapata Computing": ["ZAPATA COMPUTING, INC.", "ZAPATA AI"],
    # Big tech — DB names won't match; use verified USASpending recipient names
    "IBM": [
        "INTERNATIONAL BUSINESS MACHINES CORPORATION",
    ],
    "Alphabet (Google)": [
        "GOOGLE LLC",
    ],
    "Microsoft": ["MICROSOFT CORPORATION"],
    "Amazon (AWS)": [
        "AMAZON WEB SERVICES, INC.",
        "AMAZON.COM SERVICES LLC",
        "AMAZON.COM, INC.",
    ],
    "Intel": ["INTEL CORPORATION", "INTEL FEDERAL LLC"],
    "Honeywell (Quantinuum)": [
        "QUANTINUUM LLC",
        "HONEYWELL INTERNATIONAL INC.",
        "HONEYWELL FEDERAL MANUFACTURING & TECHNOLOGIES, LLC",
    ],
}


class UsaSpendingAdapter(GovernmentContractDataSource):
    """Fetches government contract data from USASpending.gov."""

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

    async def search_contracts(
        self, company_name: str, limit: int = 50
    ) -> list[GovernmentContract]:
        """Search for government contracts awarded to a company."""
        try:
            client = await self._get_client()
            payload = self._build_search_payload(company_name, limit)
            response = await client.post(
                USASPENDING_SEARCH_URL,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_contracts(data)
        except httpx.HTTPStatusError as e:
            logger.error(
                "USASpending API HTTP error for %s: %s",
                company_name,
                e.response.status_code,
            )
            return []
        except Exception:
            logger.exception(
                "Error searching government contracts for %s",
                company_name,
            )
            return []

    async def search_contracts_multi(
        self, search_names: list[str], limit: int = 50
    ) -> list[GovernmentContract]:
        """Search using multiple name variants and deduplicate by award_id."""
        seen_award_ids: set[str] = set()
        all_contracts: list[GovernmentContract] = []

        for name in search_names:
            contracts = await self.search_contracts(name, limit=limit)
            for c in contracts:
                if c.award_id not in seen_award_ids:
                    seen_award_ids.add(c.award_id)
                    all_contracts.append(c)

        # Sort by amount descending
        all_contracts.sort(key=lambda c: c.amount, reverse=True)
        return all_contracts[:limit]

    async def get_total_contract_value(self, company_name: str) -> float:
        """Get total value of government contracts for a company."""
        contracts = await self.search_contracts(company_name, limit=100)
        return sum(float(c.amount) for c in contracts)

    @staticmethod
    def is_quantum_related(contract: GovernmentContract) -> bool:
        """Check if a contract description or title suggests quantum relevance."""
        text = f"{contract.title} {contract.description or ''}"
        return bool(QUANTUM_KEYWORDS.search(text))

    @staticmethod
    def _build_search_payload(company_name: str, limit: int) -> dict[str, Any]:
        """Build USASpending.gov search API payload."""
        return {
            "filters": {
                "recipient_search_text": [company_name],
                "award_type_codes": ["A", "B", "C", "D"],
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Award Amount",
                "Awarding Agency",
                "Start Date",
                "End Date",
                "Description",
            ],
            "limit": limit,
            "page": 1,
            "sort": "Award Amount",
            "order": "desc",
        }

    @staticmethod
    def _parse_contracts(data: dict[str, Any]) -> list[GovernmentContract]:
        """Parse USASpending.gov response into GovernmentContract entities."""
        results = data.get("results", [])
        contracts: list[GovernmentContract] = []

        for item in results:
            award_id = item.get("Award ID", "")
            if not award_id:
                continue

            amount_raw = item.get("Award Amount", 0)
            try:
                amount = Decimal(str(amount_raw))
            except (ValueError, TypeError):
                amount = Decimal("0")

            if amount < 0:
                continue

            start_date_str = item.get("Start Date")
            try:
                start_date = date.fromisoformat(start_date_str)
            except (ValueError, TypeError):
                continue

            end_date = None
            end_date_str = item.get("End Date")
            if end_date_str:
                with contextlib.suppress(ValueError, TypeError):
                    end_date = date.fromisoformat(end_date_str)

            title = item.get("Recipient Name", "Unknown")
            agency = item.get("Awarding Agency", "Unknown")
            description = item.get("Description")

            contracts.append(
                GovernmentContract(
                    company_id=0,  # Caller must set
                    award_id=award_id,
                    title=title,
                    amount=amount,
                    awarding_agency=agency,
                    start_date=start_date,
                    end_date=end_date,
                    description=description,
                )
            )

        return contracts
