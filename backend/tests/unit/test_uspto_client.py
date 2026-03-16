"""Unit tests for the USPTO Patent API adapter."""

from datetime import date

import httpx
import pytest

from src.domain.models.value_objects import DateRange, PatentSource
from src.infrastructure.uspto_client import PATENTSVIEW_API_URL, UsptoPatentAdapter


@pytest.fixture
def adapter():
    return UsptoPatentAdapter()


class TestBuildQuery:
    def test_builds_correct_query_structure(self):
        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))
        query = UsptoPatentAdapter._build_query("IonQ", date_range)

        assert "_and" in query
        conditions = query["_and"]
        assert len(conditions) == 3
        assert {
            "_contains": {"assignees_at_grant.assignee_organization": "IonQ"}
        } in conditions
        assert {"_gte": {"patent_date": "2025-01-01"}} in conditions
        assert {"_lte": {"patent_date": "2025-12-31"}} in conditions


class TestParsePatents:
    def test_parses_valid_response(self):
        data = {
            "patents": [
                {
                    "patent_id": "US12345678",
                    "patent_title": "Quantum Error Correction",
                    "patent_date": "2025-06-15",
                    "patent_abstract": "A method for correcting errors...",
                    "patent_type": "utility",
                },
                {
                    "patent_id": "US87654321",
                    "patent_title": "Ion Trap System",
                    "patent_date": "2025-08-20",
                    "patent_abstract": None,
                    "patent_type": "utility",
                },
            ],
            "total_patent_count": 2,
        }

        patents = UsptoPatentAdapter._parse_patents(data)

        assert len(patents) == 2
        assert patents[0].patent_number == "US12345678"
        assert patents[0].title == "Quantum Error Correction"
        assert patents[0].filing_date == date(2025, 6, 15)
        assert patents[0].source == PatentSource.USPTO
        assert patents[0].abstract == "A method for correcting errors..."
        assert patents[0].classification == "utility"
        assert patents[0].company_id == 0

        assert patents[1].patent_number == "US87654321"
        assert patents[1].abstract is None

    def test_parses_empty_response(self):
        data = {"patents": None, "total_patent_count": 0}
        patents = UsptoPatentAdapter._parse_patents(data)
        assert patents == []

    def test_skips_entries_without_patent_id(self):
        data = {
            "patents": [
                {
                    "patent_id": "",
                    "patent_title": "Some Patent",
                    "patent_date": "2025-01-01",
                },
            ]
        }
        patents = UsptoPatentAdapter._parse_patents(data)
        assert patents == []

    def test_skips_entries_without_title(self):
        data = {
            "patents": [
                {
                    "patent_id": "US111",
                    "patent_title": "",
                    "patent_date": "2025-01-01",
                },
            ]
        }
        patents = UsptoPatentAdapter._parse_patents(data)
        assert patents == []

    def test_skips_entries_with_invalid_date(self):
        data = {
            "patents": [
                {
                    "patent_id": "US111",
                    "patent_title": "Valid Title",
                    "patent_date": "not-a-date",
                },
            ]
        }
        patents = UsptoPatentAdapter._parse_patents(data)
        assert patents == []


class TestSearchPatents:
    @pytest.mark.asyncio
    async def test_search_patents_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "patents": [
                    {
                        "patent_id": "US12345",
                        "patent_title": "Quantum Computing Method",
                        "patent_date": "2025-06-01",
                        "patent_abstract": "Abstract text",
                        "patent_type": "utility",
                    }
                ],
                "total_patent_count": 1,
            },
            request=httpx.Request("GET", PATENTSVIEW_API_URL),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = UsptoPatentAdapter(http_client=mock_client)
        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))

        result = await adapter.search_patents("IonQ", date_range)

        assert len(result) == 1
        assert result[0].patent_number == "US12345"

    @pytest.mark.asyncio
    async def test_search_patents_with_api_key(self):
        """Verify API key is sent in X-Api-Key header."""
        captured_request = None

        def capture_request(request: httpx.Request) -> httpx.Response:
            nonlocal captured_request
            captured_request = request
            return httpx.Response(
                200,
                json={"patents": [], "total_patent_count": 0},
                request=request,
            )

        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(capture_request)
        )
        adapter = UsptoPatentAdapter(http_client=mock_client, api_key="test-key-123")
        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))

        await adapter.search_patents("IonQ", date_range)

        assert captured_request is not None
        assert captured_request.headers.get("X-Api-Key") == "test-key-123"

    @pytest.mark.asyncio
    async def test_search_patents_uses_get_method(self):
        """Verify the new API uses GET instead of POST."""
        captured_request = None

        def capture_request(request: httpx.Request) -> httpx.Response:
            nonlocal captured_request
            captured_request = request
            return httpx.Response(
                200,
                json={"patents": [], "total_patent_count": 0},
                request=request,
            )

        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(capture_request)
        )
        adapter = UsptoPatentAdapter(http_client=mock_client)
        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))

        await adapter.search_patents("IonQ", date_range)

        assert captured_request is not None
        assert captured_request.method == "GET"

    @pytest.mark.asyncio
    async def test_search_patents_http_error(self):
        mock_response = httpx.Response(
            500,
            json={"error": "Internal Server Error"},
            request=httpx.Request("GET", PATENTSVIEW_API_URL),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = UsptoPatentAdapter(http_client=mock_client)
        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))

        result = await adapter.search_patents("IonQ", date_range)
        assert result == []

    @pytest.mark.asyncio
    async def test_search_patents_network_error(self):
        async def raise_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection failed")

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(raise_error))
        adapter = UsptoPatentAdapter(http_client=mock_client)
        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))

        result = await adapter.search_patents("IonQ", date_range)
        assert result == []


class TestGetPatentCount:
    @pytest.mark.asyncio
    async def test_get_patent_count_success(self):
        mock_response = httpx.Response(
            200,
            json={"patents": [{"patent_id": "1"}], "total_patent_count": 42},
            request=httpx.Request("GET", PATENTSVIEW_API_URL),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = UsptoPatentAdapter(http_client=mock_client)
        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))

        count = await adapter.get_patent_count("IonQ", date_range)
        assert count == 42

    @pytest.mark.asyncio
    async def test_get_patent_count_error(self):
        async def raise_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection failed")

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(raise_error))
        adapter = UsptoPatentAdapter(http_client=mock_client)
        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))

        count = await adapter.get_patent_count("IonQ", date_range)
        assert count == 0
