"""Unit tests for the USASpending.gov adapter."""

from datetime import date
from decimal import Decimal

import httpx
import pytest

from src.infrastructure.usaspending_client import UsaSpendingAdapter


class TestParseContracts:
    def test_parses_valid_contracts(self):
        data = {
            "results": [
                {
                    "Award ID": "AWD-001",
                    "Recipient Name": "IonQ Inc",
                    "Award Amount": 1500000.00,
                    "Awarding Agency": "Department of Defense",
                    "Start Date": "2025-01-15",
                    "End Date": "2026-01-15",
                    "Description": "Quantum computing research",
                },
                {
                    "Award ID": "AWD-002",
                    "Recipient Name": "IonQ Inc",
                    "Award Amount": 500000.00,
                    "Awarding Agency": "Department of Energy",
                    "Start Date": "2025-06-01",
                    "End Date": None,
                    "Description": None,
                },
            ]
        }

        contracts = UsaSpendingAdapter._parse_contracts(data)

        assert len(contracts) == 2
        assert contracts[0].award_id == "AWD-001"
        assert contracts[0].amount == Decimal("1500000.00")
        assert contracts[0].awarding_agency == "Department of Defense"
        assert contracts[0].start_date == date(2025, 1, 15)
        assert contracts[0].end_date == date(2026, 1, 15)
        assert contracts[0].description == "Quantum computing research"
        assert contracts[1].end_date is None

    def test_empty_results(self):
        data = {"results": []}
        contracts = UsaSpendingAdapter._parse_contracts(data)
        assert contracts == []

    def test_no_results_key(self):
        data = {}
        contracts = UsaSpendingAdapter._parse_contracts(data)
        assert contracts == []

    def test_skips_entries_without_award_id(self):
        data = {
            "results": [
                {
                    "Award ID": "",
                    "Recipient Name": "Test",
                    "Award Amount": 100,
                    "Awarding Agency": "DOD",
                    "Start Date": "2025-01-01",
                },
            ]
        }
        contracts = UsaSpendingAdapter._parse_contracts(data)
        assert contracts == []

    def test_skips_negative_amounts(self):
        data = {
            "results": [
                {
                    "Award ID": "AWD-001",
                    "Recipient Name": "Test",
                    "Award Amount": -500,
                    "Awarding Agency": "DOD",
                    "Start Date": "2025-01-01",
                },
            ]
        }
        contracts = UsaSpendingAdapter._parse_contracts(data)
        assert contracts == []

    def test_skips_invalid_start_date(self):
        data = {
            "results": [
                {
                    "Award ID": "AWD-001",
                    "Recipient Name": "Test",
                    "Award Amount": 100,
                    "Awarding Agency": "DOD",
                    "Start Date": "not-a-date",
                },
            ]
        }
        contracts = UsaSpendingAdapter._parse_contracts(data)
        assert contracts == []

    def test_company_id_defaults_to_zero(self):
        data = {
            "results": [
                {
                    "Award ID": "AWD-001",
                    "Recipient Name": "Test",
                    "Award Amount": 100,
                    "Awarding Agency": "DOD",
                    "Start Date": "2025-01-01",
                },
            ]
        }
        contracts = UsaSpendingAdapter._parse_contracts(data)
        assert contracts[0].company_id == 0


class TestBuildSearchPayload:
    def test_builds_payload(self):
        payload = UsaSpendingAdapter._build_search_payload("IonQ", 25)
        assert payload["filters"]["recipient_search_text"] == ["IonQ"]
        assert payload["limit"] == 25
        assert payload["sort"] == "Award Amount"
        assert payload["order"] == "desc"


class TestSearchContracts:
    @pytest.mark.asyncio
    async def test_search_contracts_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "Award ID": "AWD-001",
                        "Recipient Name": "IonQ",
                        "Award Amount": 1000000,
                        "Awarding Agency": "DOD",
                        "Start Date": "2025-01-01",
                        "End Date": "2026-01-01",
                        "Description": "Research",
                    }
                ]
            },
            request=httpx.Request("POST", "https://api.usaspending.gov/api/v2/search/spending_by_award/"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = UsaSpendingAdapter(http_client=mock_client)

        contracts = await adapter.search_contracts("IonQ")
        assert len(contracts) == 1
        assert contracts[0].award_id == "AWD-001"

    @pytest.mark.asyncio
    async def test_search_contracts_http_error(self):
        mock_response = httpx.Response(
            500,
            request=httpx.Request("POST", "https://api.usaspending.gov/api/v2/search/spending_by_award/"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = UsaSpendingAdapter(http_client=mock_client)

        contracts = await adapter.search_contracts("IonQ")
        assert contracts == []

    @pytest.mark.asyncio
    async def test_get_total_contract_value(self):
        mock_response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "Award ID": "AWD-001",
                        "Recipient Name": "IonQ",
                        "Award Amount": 1000000,
                        "Awarding Agency": "DOD",
                        "Start Date": "2025-01-01",
                    },
                    {
                        "Award ID": "AWD-002",
                        "Recipient Name": "IonQ",
                        "Award Amount": 500000,
                        "Awarding Agency": "DOE",
                        "Start Date": "2025-02-01",
                    },
                ]
            },
            request=httpx.Request("POST", "https://api.usaspending.gov/api/v2/search/spending_by_award/"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = UsaSpendingAdapter(http_client=mock_client)

        total = await adapter.get_total_contract_value("IonQ")
        assert total == 1500000.0
