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
                    "primaryDocument": ["annual.htm"],
                }
            }
        }
        filings = SecEdgarAdapter._parse_filings(data)
        parsed = json.loads(filings[0].data_json)
        assert parsed["form"] == "10-K"
        assert parsed["accession"] == "acc-123"
        assert parsed["primary_document"] == "annual.htm"


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


class TestParseForm4Xml:
    """Tests for Form 4 XML parsing."""

    SAMPLE_FORM4_XML = """\
<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerName>John Smith</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <officerTitle>Chief Executive Officer</officerTitle>
      <isOfficer>1</isOfficer>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-10</value></transactionDate>
      <transactionCoding>
        <transactionCode>P</transactionCode>
      </transactionCoding>
      <transactionAmounts>
        <transactionShares><value>10000</value></transactionShares>
        <transactionPricePerShare><value>5.25</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

    def test_parses_insider_name(self):
        result = SecEdgarAdapter._parse_form4_xml(self.SAMPLE_FORM4_XML)
        assert result is not None
        assert result["insider_name"] == "John Smith"

    def test_parses_insider_title(self):
        result = SecEdgarAdapter._parse_form4_xml(self.SAMPLE_FORM4_XML)
        assert result is not None
        assert result["insider_title"] == "Chief Executive Officer"

    def test_parses_transaction_details(self):
        result = SecEdgarAdapter._parse_form4_xml(self.SAMPLE_FORM4_XML)
        assert result is not None
        txns = result["transactions"]
        assert len(txns) == 1
        assert txns[0]["type"] == "P"
        assert txns[0]["shares"] == 10000.0
        assert txns[0]["price"] == 5.25
        assert txns[0]["acquired_disposed"] == "A"
        assert txns[0]["date"] == "2026-03-10"

    def test_returns_none_for_invalid_xml(self):
        result = SecEdgarAdapter._parse_form4_xml("not xml")
        assert result is None

    def test_returns_none_for_empty_document(self):
        result = SecEdgarAdapter._parse_form4_xml(
            "<ownershipDocument></ownershipDocument>"
        )
        assert result is None

    def test_handles_namespace(self):
        xml = """\
<?xml version="1.0"?>
<ownershipDocument xmlns="http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany">
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerName>Ns Test</rptOwnerName>
    </reportingOwnerId>
  </reportingOwner>
</ownershipDocument>"""
        result = SecEdgarAdapter._parse_form4_xml(xml)
        assert result is not None
        assert result["insider_name"] == "Ns Test"

    def test_handles_multiple_transactions(self):
        xml = """\
<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerName>Jane Doe</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <officerTitle>CFO</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-10</value></transactionDate>
      <transactionCoding><transactionCode>S</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>5000</value></transactionShares>
        <transactionPricePerShare><value>12.50</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-11</value></transactionDate>
      <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>2000</value></transactionShares>
        <transactionPricePerShare><value>11.00</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""
        result = SecEdgarAdapter._parse_form4_xml(xml)
        assert result is not None
        assert result["insider_name"] == "Jane Doe"
        assert len(result["transactions"]) == 2
        assert result["transactions"][0]["type"] == "S"
        assert result["transactions"][0]["shares"] == 5000.0
        assert result["transactions"][1]["type"] == "P"
        assert result["transactions"][1]["shares"] == 2000.0


class TestFetchFilingsErrorPaths:
    @pytest.mark.asyncio
    async def test_fetch_filings_http_error(self):
        """Lines 93-100: HTTP error returns empty list."""

        def transport(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if "company_tickers" in url:
                return httpx.Response(
                    200,
                    json={"0": {"cik_str": 123, "ticker": "IONQ", "title": "IonQ"}},
                    request=request,
                )
            return httpx.Response(500, request=request)

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        filings = await adapter.fetch_filings("IONQ")
        assert filings == []

    @pytest.mark.asyncio
    async def test_fetch_filings_generic_exception(self):
        """Lines 98-100: generic exception returns empty list."""

        def transport(request: httpx.Request) -> httpx.Response:
            raise RuntimeError("network down")

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        filings = await adapter.fetch_filings("IONQ")
        assert filings == []


class TestFetchInstitutionalHoldings:
    @pytest.mark.asyncio
    async def test_fetch_institutional_holdings_success(self):
        """Lines 114-123."""

        def transport(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if "company_tickers" in url:
                return httpx.Response(
                    200,
                    json={"0": {"cik_str": 123, "ticker": "IONQ", "title": "IonQ"}},
                    request=request,
                )
            if "submissions" in url:
                return httpx.Response(
                    200,
                    json={
                        "filings": {
                            "recent": {
                                "form": ["13F-HR"],
                                "filingDate": ["2025-09-01"],
                                "primaryDocDescription": ["13F"],
                                "accessionNumber": ["0001-25-000001"],
                                "primaryDocument": ["primary.xml"],
                            }
                        }
                    },
                    request=request,
                )
            # 13F enrichment doc request
            return httpx.Response(
                200,
                text="<filingManager><name>Big Fund LP</name></filingManager>",
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        filings = await adapter.fetch_institutional_holdings("IONQ")
        assert len(filings) == 1
        assert filings[0].filing_type == FilingType.FORM_13F


class TestEnrichForm4:
    @pytest.mark.asyncio
    async def test_enrich_form4_builds_description(self):
        """Lines 302-342: builds human-readable description."""
        import json

        from src.domain.models.entities import Filing

        form4_xml = """\
<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId><rptOwnerName>Jane Doe</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship><officerTitle>CFO</officerTitle></reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-10</value></transactionDate>
      <transactionCoding><transactionCode>S</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>5000</value></transactionShares>
        <transactionPricePerShare><value>12.50</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text=form4_xml, request=request)

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        filing = Filing(
            company_id=0,
            filing_type=FilingType.FORM_4,
            filing_date=date(2026, 3, 10),
            description="Form 4",
            url="https://sec.gov/test",
            data_json=json.dumps(
                {"accession": "0001-26-000001", "primary_document": "doc.xml"}
            ),
        )

        await adapter._enrich_form4(filing, "0000000123", mock_client)
        assert "Jane Doe" in filing.description
        assert "CFO" in filing.description
        assert "Sale" in filing.description
        assert "5,000 shares" in filing.description
        assert "@ $12.50" in filing.description

    @pytest.mark.asyncio
    async def test_enrich_form4_no_accession(self):
        """Returns early when accession is missing."""
        import json

        from src.domain.models.entities import Filing

        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, request=req))
        )
        adapter = SecEdgarAdapter(http_client=mock_client)

        filing = Filing(
            company_id=0,
            filing_type=FilingType.FORM_4,
            filing_date=date(2026, 3, 10),
            description="Original",
            url="https://sec.gov/test",
            data_json=json.dumps({}),
        )

        await adapter._enrich_form4(filing, "123", mock_client)
        assert filing.description == "Original"

    @pytest.mark.asyncio
    async def test_enrich_form4_http_404(self):
        """Handles non-200 response gracefully."""
        import json

        from src.domain.models.entities import Filing

        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, request=request)

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        filing = Filing(
            company_id=0,
            filing_type=FilingType.FORM_4,
            filing_date=date(2026, 3, 10),
            description="Original",
            url="https://sec.gov/test",
            data_json=json.dumps(
                {"accession": "0001-26-000001", "primary_document": "doc.xml"}
            ),
        )

        await adapter._enrich_form4(filing, "123", mock_client)
        assert filing.description == "Original"

    @pytest.mark.asyncio
    async def test_enrich_form4_gift_transaction(self):
        """Tests Gift code path in description."""
        import json

        from src.domain.models.entities import Filing

        form4_xml = """\
<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId><rptOwnerName>Bob Gift</rptOwnerName></reportingOwnerId>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2026-03-10</value></transactionDate>
      <transactionCoding><transactionCode>G</transactionCode></transactionCoding>
      <transactionAmounts>
        <transactionShares><value>1000</value></transactionShares>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text=form4_xml, request=request)

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        filing = Filing(
            company_id=0,
            filing_type=FilingType.FORM_4,
            filing_date=date(2026, 3, 10),
            description="Form 4",
            url=None,
            data_json=json.dumps({"accession": "acc-1", "primary_document": "doc.xml"}),
        )

        await adapter._enrich_form4(filing, "123", mock_client)
        assert "Gift" in filing.description
        assert "Bob Gift" in filing.description

    @pytest.mark.asyncio
    async def test_enrich_form4_name_only_no_transactions(self):
        """Tests description when no transactions but name+title exist."""
        import json

        from src.domain.models.entities import Filing

        form4_xml = """\
<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId><rptOwnerName>Alice No-Trade</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship><officerTitle>Director</officerTitle></reportingOwnerRelationship>
  </reportingOwner>
</ownershipDocument>"""

        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text=form4_xml, request=request)

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        filing = Filing(
            company_id=0,
            filing_type=FilingType.FORM_4,
            filing_date=date(2026, 3, 10),
            description="Form 4",
            url=None,
            data_json=json.dumps({"accession": "acc-1", "primary_document": "doc.xml"}),
        )

        await adapter._enrich_form4(filing, "123", mock_client)
        assert filing.description == "Alice No-Trade (Director)"


class TestEnrich13f:
    @pytest.mark.asyncio
    async def test_enrich_13f_with_filing_manager(self):
        """Lines 425-459: extracts institution name from filingManager XML."""
        import json

        from src.domain.models.entities import Filing

        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                text="<filingManager><name>Vanguard Group</name></filingManager>",
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        filing = Filing(
            company_id=0,
            filing_type=FilingType.FORM_13F,
            filing_date=date(2025, 9, 1),
            description="13F",
            url=None,
            data_json=json.dumps(
                {"accession": "0001-25-000001", "primary_document": "report.xml"}
            ),
        )

        await adapter._enrich_13f(filing, "0000000123", mock_client)
        assert "Vanguard Group" in filing.description

    @pytest.mark.asyncio
    async def test_enrich_13f_fallback_company_name(self):
        """Falls back to COMPANY CONFORMED NAME regex."""
        import json

        from src.domain.models.entities import Filing

        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                text="COMPANY CONFORMED NAME:		BlackRock Inc",
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        filing = Filing(
            company_id=0,
            filing_type=FilingType.FORM_13F,
            filing_date=date(2025, 9, 1),
            description="13F",
            url=None,
            data_json=json.dumps(
                {"accession": "acc-1", "primary_document": "report.htm"}
            ),
        )

        await adapter._enrich_13f(filing, "123", mock_client)
        assert "BlackRock Inc" in filing.description

    @pytest.mark.asyncio
    async def test_enrich_13f_no_accession(self):
        """Returns early when accession missing."""
        import json

        from src.domain.models.entities import Filing

        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, request=req))
        )
        adapter = SecEdgarAdapter(http_client=mock_client)

        filing = Filing(
            company_id=0,
            filing_type=FilingType.FORM_13F,
            filing_date=date(2025, 9, 1),
            description="Original",
            url=None,
            data_json=json.dumps({}),
        )

        await adapter._enrich_13f(filing, "123", mock_client)
        assert filing.description == "Original"

    @pytest.mark.asyncio
    async def test_enrich_13f_404(self):
        """Handles non-200 gracefully."""
        import json

        from src.domain.models.entities import Filing

        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, request=request)

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)

        filing = Filing(
            company_id=0,
            filing_type=FilingType.FORM_13F,
            filing_date=date(2025, 9, 1),
            description="Original",
            url=None,
            data_json=json.dumps(
                {"accession": "acc-1", "primary_document": "report.xml"}
            ),
        )

        await adapter._enrich_13f(filing, "123", mock_client)
        assert filing.description == "Original"


class TestFetchFormDFilings:
    @pytest.mark.asyncio
    async def test_fetch_form_d_success(self):
        """Lines 135-200."""

        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "hits": {
                        "hits": [
                            {
                                "_source": {
                                    "file_date": "2025-06-15",
                                    "accession_no": "0001-25-000010",
                                    "entity_name": "IonQ Inc",
                                    "display_names": ["IonQ, Inc."],
                                }
                            }
                        ]
                    }
                },
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        filings = await adapter.fetch_form_d_filings("IonQ")
        assert len(filings) == 1
        assert filings[0].filing_type == FilingType.FORM_D
        assert "IonQ, Inc." in filings[0].description

    @pytest.mark.asyncio
    async def test_fetch_form_d_invalid_date_skipped(self):
        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "hits": {
                        "hits": [
                            {
                                "_source": {
                                    "file_date": "bad-date",
                                    "accession_no": "a1",
                                }
                            },
                            {
                                "_source": {
                                    "file_date": "2025-01-01",
                                    "accession_no": "a2",
                                    "entity_name": "Good Co",
                                }
                            },
                        ]
                    }
                },
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        filings = await adapter.fetch_form_d_filings("Test")
        assert len(filings) == 1

    @pytest.mark.asyncio
    async def test_fetch_form_d_http_error(self):
        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, request=request)

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        filings = await adapter.fetch_form_d_filings("Test")
        assert filings == []

    @pytest.mark.asyncio
    async def test_fetch_form_d_generic_exception(self):
        def transport(request: httpx.Request) -> httpx.Response:
            raise RuntimeError("boom")

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        filings = await adapter.fetch_form_d_filings("Test")
        assert filings == []

    @pytest.mark.asyncio
    async def test_fetch_form_d_empty_accession_no_url(self):
        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "hits": {
                        "hits": [
                            {
                                "_source": {
                                    "file_date": "2025-06-15",
                                    "accession_no": "",
                                    "entity_name": "No Acc Co",
                                }
                            }
                        ]
                    }
                },
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        filings = await adapter.fetch_form_d_filings("Test")
        assert len(filings) == 1
        assert filings[0].url is None


class TestFetchFormDTotalRaised:
    @pytest.mark.asyncio
    async def test_fetch_form_d_total_raised_success(self):
        """Lines 208-246."""

        def transport(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if "company_tickers" in url:
                return httpx.Response(
                    200,
                    json={"0": {"cik_str": 123, "ticker": "IONQ", "title": "IonQ"}},
                    request=request,
                )
            if "submissions" in url:
                return httpx.Response(
                    200,
                    json={
                        "filings": {
                            "recent": {
                                "form": ["D", "D/A", "10-K"],
                                "primaryDocument": ["d1.xml", "d2.xml", "10k.htm"],
                                "accessionNumber": ["acc-1", "acc-2", "acc-3"],
                            }
                        }
                    },
                    request=request,
                )
            # Form D XML docs
            return httpx.Response(
                200,
                text="<totalAmountSold>5000000</totalAmountSold>",
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        total = await adapter.fetch_form_d_total_raised("IONQ")
        assert total == 10000000.0

    @pytest.mark.asyncio
    async def test_fetch_form_d_total_raised_no_cik(self):
        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"0": {"cik_str": 123, "ticker": "OTHER", "title": "Other"}},
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        result = await adapter.fetch_form_d_total_raised("IONQ")
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_form_d_total_raised_no_d_filings(self):
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
                            "primaryDocument": ["10k.htm"],
                            "accessionNumber": ["acc-1"],
                        }
                    }
                },
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        result = await adapter.fetch_form_d_total_raised("IONQ")
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_form_d_total_raised_exception(self):
        def transport(request: httpx.Request) -> httpx.Response:
            raise RuntimeError("network error")

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        result = await adapter.fetch_form_d_total_raised("IONQ")
        assert result is None


class TestExtractFormDAmount:
    @pytest.mark.asyncio
    async def test_extracts_total_amount_sold(self):
        """Lines 256-286."""

        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                text="<totalAmountSold>1500000.50</totalAmountSold>",
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        amount = await adapter._extract_form_d_amount(
            mock_client, "0000000123", "0001-25-000001", "form.xml"
        )
        assert amount == 1500000.50

    @pytest.mark.asyncio
    async def test_falls_back_to_total_offering_amount(self):
        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                text="<totalOfferingAmount>2000000</totalOfferingAmount>",
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        amount = await adapter._extract_form_d_amount(
            mock_client, "123", "acc-1", "form.xml"
        )
        assert amount == 2000000.0

    @pytest.mark.asyncio
    async def test_returns_none_on_404(self):
        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, request=request)

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        amount = await adapter._extract_form_d_amount(
            mock_client, "123", "acc-1", "form.xml"
        )
        assert amount is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_match(self):
        def transport(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, text="<noRelevantField>123</noRelevantField>", request=request
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        amount = await adapter._extract_form_d_amount(
            mock_client, "123", "acc-1", "form.xml"
        )
        assert amount is None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        def transport(request: httpx.Request) -> httpx.Response:
            raise RuntimeError("fail")

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        amount = await adapter._extract_form_d_amount(
            mock_client, "123", "acc-1", "form.xml"
        )
        assert amount is None


class TestResolveCikError:
    @pytest.mark.asyncio
    async def test_resolve_cik_exception(self):
        """Lines 480-481."""

        def transport(request: httpx.Request) -> httpx.Response:
            raise RuntimeError("network error")

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = SecEdgarAdapter(http_client=mock_client)
        result = await adapter._resolve_cik("IONQ")
        assert result is None
