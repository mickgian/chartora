"""Unit tests for the SEC EDGAR adapter."""

from datetime import date

import httpx
import pytest

from src.domain.models.value_objects import FilingType
from src.infrastructure.sec_edgar import SecEdgarAdapter


class TestParseFilings:
    def test_parses_valid_filings(self):
        data = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "4", "8-K", "13F-HR"],
                    "filingDate": [
                        "2025-03-15",
                        "2025-06-15",
                        "2025-07-01",
                        "2025-08-01",
                        "2025-09-01",
                    ],
                    "primaryDocDescription": [
                        "Annual Report",
                        "Quarterly Report",
                        "Statement of Changes",
                        "Current Report",
                        "Institutional Holdings",
                    ],
                    "accessionNumber": [
                        "0001-23-000001",
                        "0001-23-000002",
                        "0001-23-000003",
                        "0001-23-000004",
                        "0001-23-000005",
                    ],
                }
            }
        }

        filings = SecEdgarAdapter._parse_filings(data)

        # 8-K is not in our FORM_TYPE_MAP, so only 4 filings should parse
        assert len(filings) == 4
        assert filings[0].filing_type == FilingType.FORM_10K
        assert filings[0].filing_date == date(2025, 3, 15)
        assert filings[0].description == "Annual Report"
        assert filings[1].filing_type == FilingType.FORM_10Q
        assert filings[2].filing_type == FilingType.FORM_4
        assert filings[3].filing_type == FilingType.FORM_13F

    def test_filters_by_filing_type(self):
        data = {
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q", "4"],
                    "filingDate": ["2025-03-15", "2025-06-15", "2025-07-01"],
                    "primaryDocDescription": ["Annual", "Quarterly", "Insider"],
                    "accessionNumber": ["acc1", "acc2", "acc3"],
                }
            }
        }

        filings = SecEdgarAdapter._parse_filings(data, filing_types=["10-K"])
        assert len(filings) == 1
        assert filings[0].filing_type == FilingType.FORM_10K

    def test_empty_recent_data(self):
        data = {"filings": {"recent": {}}}
        filings = SecEdgarAdapter._parse_filings(data)
        assert filings == []

    def test_no_filings_key(self):
        data = {}
        filings = SecEdgarAdapter._parse_filings(data)
        assert filings == []

    def test_skips_invalid_dates(self):
        data = {
            "filings": {
                "recent": {
                    "form": ["10-K"],
                    "filingDate": ["not-a-date"],
                    "primaryDocDescription": ["Annual"],
                    "accessionNumber": ["acc1"],
                }
            }
        }
        filings = SecEdgarAdapter._parse_filings(data)
        assert filings == []

    def test_filing_url_construction(self):
        data = {
            "filings": {
                "recent": {
                    "form": ["10-K"],
                    "filingDate": ["2025-03-15"],
                    "primaryDocDescription": ["Annual Report"],
                    "accessionNumber": ["0001234567-25-000001"],
                }
            }
        }
        filings = SecEdgarAdapter._parse_filings(data)
        assert len(filings) == 1
        assert "sec.gov" in filings[0].url
        assert filings[0].company_id == 0

    def test_data_json_includes_form_and_accession(self):
        import json

        data = {
            "filings": {
                "recent": {
                    "form": ["10-K"],
                    "filingDate": ["2025-03-15"],
                    "primaryDocDescription": ["Annual"],
                    "accessionNumber": ["acc-123"],
                }
            }
        }
        filings = SecEdgarAdapter._parse_filings(data)
        parsed = json.loads(filings[0].data_json)
        assert parsed["form"] == "10-K"
        assert parsed["accession"] == "acc-123"


class TestResolveCik:
    @pytest.mark.asyncio
    async def test_resolve_cik_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "0": {"cik_str": 1234567, "ticker": "IONQ", "title": "IonQ Inc"},
                "1": {"cik_str": 7654321, "ticker": "QBTS", "title": "D-Wave"},
            },
            request=httpx.Request(
                "GET", "https://www.sec.gov/files/company_tickers.json"
            ),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = SecEdgarAdapter(http_client=mock_client)

        cik = await adapter._resolve_cik("IONQ")
        assert cik == "0001234567"

    @pytest.mark.asyncio
    async def test_resolve_cik_not_found(self):
        mock_response = httpx.Response(
            200,
            json={"0": {"cik_str": 1234567, "ticker": "AAPL", "title": "Apple"}},
            request=httpx.Request(
                "GET", "https://www.sec.gov/files/company_tickers.json"
            ),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = SecEdgarAdapter(http_client=mock_client)

        cik = await adapter._resolve_cik("IONQ")
        assert cik is None

    @pytest.mark.asyncio
    async def test_resolve_cik_cached(self):
        call_count = 0

        def transport(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(
                200,
                json={"0": {"cik_str": 123, "ticker": "IONQ", "title": "IonQ"}},
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        cik1 = await adapter._resolve_cik("IONQ")
        cik2 = await adapter._resolve_cik("IONQ")
        assert cik1 == cik2
        assert call_count == 1  # Only one HTTP call due to caching


class TestFetchFilings:
    @pytest.mark.asyncio
    async def test_fetch_filings_full_flow(self):
        def transport(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if "company_tickers" in url:
                return httpx.Response(
                    200,
                    json={"0": {"cik_str": 123, "ticker": "IONQ", "title": "IonQ"}},
                    request=request,
                )
            return httpx.Response(
                200,
                json={
                    "filings": {
                        "recent": {
                            "form": ["10-K"],
                            "filingDate": ["2025-03-15"],
                            "primaryDocDescription": ["Annual Report"],
                            "accessionNumber": ["acc-1"],
                        }
                    }
                },
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        filings = await adapter.fetch_filings("IONQ")
        assert len(filings) == 1
        assert filings[0].filing_type == FilingType.FORM_10K

    @pytest.mark.asyncio
    async def test_fetch_insider_trades(self):
        def transport(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if "company_tickers" in url:
                return httpx.Response(
                    200,
                    json={"0": {"cik_str": 123, "ticker": "IONQ", "title": "IonQ"}},
                    request=request,
                )
            return httpx.Response(
                200,
                json={
                    "filings": {
                        "recent": {
                            "form": ["4", "10-K"],
                            "filingDate": ["2025-07-01", "2025-03-15"],
                            "primaryDocDescription": ["Insider", "Annual"],
                            "accessionNumber": ["acc-1", "acc-2"],
                        }
                    }
                },
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        filings = await adapter.fetch_insider_trades("IONQ")
        assert len(filings) == 1
        assert filings[0].filing_type == FilingType.FORM_4

    @pytest.mark.asyncio
    async def test_fetch_filings_cik_not_found(self):
        mock_response = httpx.Response(
            200,
            json={"0": {"cik_str": 123, "ticker": "OTHER", "title": "Other"}},
            request=httpx.Request(
                "GET", "https://www.sec.gov/files/company_tickers.json"
            ),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = SecEdgarAdapter(http_client=mock_client)

        filings = await adapter.fetch_filings("IONQ")
        assert filings == []
