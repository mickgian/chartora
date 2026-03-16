"""Unit tests for the SEC EDGAR XBRL adapter."""

import httpx
import pytest

from src.infrastructure.sec_edgar_xbrl import SecEdgarXbrlAdapter


class TestGetLatestValue:
    def test_returns_latest_10k_value(self):
        us_gaap = {
            "StockholdersEquity": {
                "units": {
                    "USD": [
                        {"val": 1000000, "form": "10-K", "end": "2024-12-31"},
                        {"val": 800000, "form": "10-K", "end": "2023-12-31"},
                        {"val": 900000, "form": "10-Q", "end": "2025-03-31"},
                    ]
                }
            }
        }
        result = SecEdgarXbrlAdapter._get_latest_value(
            us_gaap, "StockholdersEquity"
        )
        assert result == 1000000.0

    def test_falls_back_to_10q(self):
        us_gaap = {
            "Assets": {
                "units": {
                    "USD": [
                        {"val": 500000, "form": "10-Q", "end": "2025-03-31"},
                        {"val": 400000, "form": "10-Q", "end": "2024-09-30"},
                    ]
                }
            }
        }
        result = SecEdgarXbrlAdapter._get_latest_value(us_gaap, "Assets")
        assert result == 500000.0

    def test_falls_back_to_any_value(self):
        us_gaap = {
            "Assets": {
                "units": {
                    "USD": [
                        {"val": 300000, "form": "other", "end": "2025-01-01"},
                    ]
                }
            }
        }
        result = SecEdgarXbrlAdapter._get_latest_value(us_gaap, "Assets")
        assert result == 300000.0

    def test_returns_none_for_missing_concept(self):
        result = SecEdgarXbrlAdapter._get_latest_value({}, "Assets")
        assert result is None

    def test_returns_none_for_empty_units(self):
        us_gaap = {"Assets": {"units": {}}}
        result = SecEdgarXbrlAdapter._get_latest_value(us_gaap, "Assets")
        assert result is None

    def test_returns_none_for_no_usd(self):
        us_gaap = {
            "Assets": {
                "units": {
                    "EUR": [
                        {"val": 100, "form": "10-K", "end": "2024-12-31"}
                    ]
                }
            }
        }
        result = SecEdgarXbrlAdapter._get_latest_value(
            us_gaap, "Assets"
        )
        assert result is None


class TestResolveCik:
    @pytest.mark.asyncio
    async def test_resolve_cik_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "0": {"cik_str": 1234567, "ticker": "IONQ", "title": "IonQ Inc"},
            },
            request=httpx.Request(
                "GET", "https://www.sec.gov/files/company_tickers.json"
            ),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = SecEdgarXbrlAdapter(http_client=mock_client)

        cik = await adapter._resolve_cik("IONQ")
        assert cik == "0001234567"

    @pytest.mark.asyncio
    async def test_resolve_cik_not_found(self):
        mock_response = httpx.Response(
            200,
            json={"0": {"cik_str": 123, "ticker": "AAPL", "title": "Apple"}},
            request=httpx.Request(
                "GET", "https://www.sec.gov/files/company_tickers.json"
            ),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = SecEdgarXbrlAdapter(http_client=mock_client)

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
        adapter = SecEdgarXbrlAdapter(http_client=mock_client)

        cik1 = await adapter._resolve_cik("IONQ")
        cik2 = await adapter._resolve_cik("IONQ")
        assert cik1 == cik2
        assert call_count == 1


class TestFetchTotalFunding:
    @pytest.mark.asyncio
    async def test_fetch_total_funding_equity(self):
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
                    "facts": {
                        "us-gaap": {
                            "StockholdersEquity": {
                                "units": {
                                    "USD": [
                                        {
                                            "val": 2000000,
                                            "form": "10-K",
                                            "end": "2024-12-31",
                                        },
                                    ]
                                }
                            }
                        }
                    }
                },
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarXbrlAdapter(http_client=mock_client)

        result = await adapter.fetch_total_funding("IONQ")
        assert result == 2000000.0

    @pytest.mark.asyncio
    async def test_fetch_total_funding_fallback_to_assets(self):
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
                    "facts": {
                        "us-gaap": {
                            "Assets": {
                                "units": {
                                    "USD": [
                                        {
                                            "val": 5000000,
                                            "form": "10-K",
                                            "end": "2024-12-31",
                                        },
                                    ]
                                }
                            }
                        }
                    }
                },
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarXbrlAdapter(http_client=mock_client)

        result = await adapter.fetch_total_funding("IONQ")
        assert result == 5000000.0


class TestFetchRdSpending:
    @pytest.mark.asyncio
    async def test_fetch_rd_spending_with_ratio(self):
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
                    "facts": {
                        "us-gaap": {
                            "ResearchAndDevelopmentExpense": {
                                "units": {
                                    "USD": [
                                        {
                                            "val": 50000000,
                                            "form": "10-K",
                                            "end": "2024-12-31",
                                        },
                                    ]
                                }
                            },
                            "Revenues": {
                                "units": {
                                    "USD": [
                                        {
                                            "val": 100000000,
                                            "form": "10-K",
                                            "end": "2024-12-31",
                                        },
                                    ]
                                }
                            },
                        }
                    }
                },
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarXbrlAdapter(http_client=mock_client)

        result = await adapter.fetch_rd_spending("IONQ")
        assert result["rd_expense"] == 50000000.0
        assert result["total_revenue"] == 100000000.0
        assert result["rd_ratio"] == 0.5

    @pytest.mark.asyncio
    async def test_fetch_rd_spending_no_data(self):
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
                json={"facts": {"us-gaap": {}}},
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarXbrlAdapter(http_client=mock_client)

        result = await adapter.fetch_rd_spending("IONQ")
        assert result["rd_expense"] is None
        assert result["total_revenue"] is None
        assert result["rd_ratio"] is None

    @pytest.mark.asyncio
    async def test_fetch_rd_spending_cik_not_found(self):
        mock_response = httpx.Response(
            200,
            json={"0": {"cik_str": 123, "ticker": "AAPL", "title": "Apple"}},
            request=httpx.Request(
                "GET", "https://www.sec.gov/files/company_tickers.json"
            ),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = SecEdgarXbrlAdapter(http_client=mock_client)

        result = await adapter.fetch_rd_spending("IONQ")
        assert result["rd_expense"] is None
