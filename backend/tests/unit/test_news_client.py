"""Unit tests for the News API adapter."""

import httpx
import pytest

from src.infrastructure.news_client import NewsApiAdapter


@pytest.fixture
def adapter():
    return NewsApiAdapter(api_key="test-api-key")


class TestBuildQuery:
    def test_builds_query_with_name_only(self):
        query = NewsApiAdapter._build_query("IonQ")
        assert query == '"IonQ"'

    def test_builds_query_with_ticker(self):
        query = NewsApiAdapter._build_query("IonQ", "IONQ")
        assert '"IonQ"' in query
        assert '"IONQ"' in query
        assert "OR" in query

    def test_builds_query_with_quantum_keywords_for_big_tech(self):
        query = NewsApiAdapter._build_query("IBM", "IBM", sector="big_tech")
        # Should have company part AND quantum keywords
        assert "AND" in query
        assert '"IBM"' in query
        assert "quantum" in query.lower()

    def test_builds_query_without_quantum_keywords_for_pure_play(self):
        query = NewsApiAdapter._build_query("IonQ", "IONQ", sector="pure_play")
        # Pure-play should NOT get quantum AND clause
        assert "AND" not in query
        assert '"IonQ"' in query

    def test_builds_query_without_quantum_keywords_for_none_sector(self):
        query = NewsApiAdapter._build_query("IonQ", "IONQ", sector=None)
        assert "AND" not in query

    def test_builds_query_with_ticker_and_quantum_keywords(self):
        query = NewsApiAdapter._build_query(
            "Alphabet (Google)", "GOOGL", sector="big_tech"
        )
        assert '"Alphabet (Google)"' in query
        assert '"GOOGL"' in query
        assert "OR" in query
        assert "AND" in query
        assert "quantum" in query.lower()


class TestParseArticles:
    def test_parses_valid_articles(self):
        data = {
            "articles": [
                {
                    "title": "IonQ Announces Breakthrough",
                    "url": "https://example.com/ionq-breakthrough",
                    "publishedAt": "2025-06-15T10:30:00Z",
                    "source": {"id": "techcrunch", "name": "TechCrunch"},
                },
                {
                    "title": "Quantum Computing Progress",
                    "url": "https://example.com/quantum",
                    "publishedAt": "2025-06-14T08:00:00Z",
                    "source": {"id": None, "name": "Reuters"},
                },
            ]
        }

        articles = NewsApiAdapter._parse_articles(data)

        assert len(articles) == 2
        assert articles[0].title == "IonQ Announces Breakthrough"
        assert articles[0].url == "https://example.com/ionq-breakthrough"
        assert articles[0].source_name == "TechCrunch"
        assert articles[0].company_id == 0
        assert articles[0].published_at.year == 2025

    def test_skips_removed_articles(self):
        data = {
            "articles": [
                {
                    "title": "[Removed]",
                    "url": "https://example.com/removed",
                    "publishedAt": "2025-06-15T10:30:00Z",
                    "source": {"name": "Unknown"},
                },
            ]
        }
        articles = NewsApiAdapter._parse_articles(data)
        assert articles == []

    def test_skips_empty_title(self):
        data = {
            "articles": [
                {
                    "title": "",
                    "url": "https://example.com/test",
                    "publishedAt": "2025-06-15T10:30:00Z",
                },
            ]
        }
        articles = NewsApiAdapter._parse_articles(data)
        assert articles == []

    def test_skips_empty_url(self):
        data = {
            "articles": [
                {
                    "title": "Valid Title",
                    "url": "",
                    "publishedAt": "2025-06-15T10:30:00Z",
                },
            ]
        }
        articles = NewsApiAdapter._parse_articles(data)
        assert articles == []

    def test_handles_invalid_date(self):
        data = {
            "articles": [
                {
                    "title": "Valid Title",
                    "url": "https://example.com/test",
                    "publishedAt": "not-a-date",
                    "source": {"name": "Test"},
                },
            ]
        }
        articles = NewsApiAdapter._parse_articles(data)
        assert len(articles) == 1
        # Falls back to now
        assert articles[0].published_at is not None

    def test_empty_articles_list(self):
        data = {"articles": []}
        articles = NewsApiAdapter._parse_articles(data)
        assert articles == []

    def test_handles_source_without_name(self):
        data = {
            "articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "publishedAt": "2025-06-15T10:30:00Z",
                    "source": None,
                },
            ]
        }
        articles = NewsApiAdapter._parse_articles(data)
        assert len(articles) == 1
        assert articles[0].source_name is None


class TestFetchArticles:
    @pytest.mark.asyncio
    async def test_fetch_articles_success(self):
        mock_response = httpx.Response(
            200,
            json={
                "status": "ok",
                "totalResults": 1,
                "articles": [
                    {
                        "title": "IonQ News",
                        "url": "https://example.com/ionq",
                        "publishedAt": "2025-06-15T10:30:00Z",
                        "source": {"name": "Reuters"},
                    }
                ],
            },
            request=httpx.Request("GET", "https://newsapi.org/v2/everything"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        articles = await adapter.fetch_articles("IonQ", "IONQ", limit=5)

        assert len(articles) == 1
        assert articles[0].title == "IonQ News"

    @pytest.mark.asyncio
    async def test_fetch_articles_api_error_status(self):
        mock_response = httpx.Response(
            200,
            json={"status": "error", "message": "Rate limit exceeded"},
            request=httpx.Request("GET", "https://newsapi.org/v2/everything"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        articles = await adapter.fetch_articles("IonQ")
        assert articles == []

    @pytest.mark.asyncio
    async def test_fetch_articles_http_error(self):
        mock_response = httpx.Response(
            401,
            json={"error": "Unauthorized"},
            request=httpx.Request("GET", "https://newsapi.org/v2/everything"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = NewsApiAdapter(api_key="bad-key", http_client=mock_client)

        articles = await adapter.fetch_articles("IonQ")
        assert articles == []

    @pytest.mark.asyncio
    async def test_fetch_articles_network_error(self):
        async def raise_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection failed")

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(raise_error))
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        articles = await adapter.fetch_articles("IonQ")
        assert articles == []

    @pytest.mark.asyncio
    async def test_fetch_articles_limits_page_size(self):
        """Verify limit is capped at 100 (NewsAPI max)."""
        captured_params = {}

        def transport(request: httpx.Request) -> httpx.Response:
            captured_params.update(dict(request.url.params))
            return httpx.Response(
                200,
                json={"status": "ok", "articles": []},
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        await adapter.fetch_articles("IonQ", limit=200)
        assert captured_params.get("pageSize") == "100"

    @pytest.mark.asyncio
    async def test_fetch_filters_irrelevant_for_big_tech(self):
        """Big-tech sector should filter out non-quantum articles."""
        mock_response = httpx.Response(
            200,
            json={
                "status": "ok",
                "articles": [
                    {
                        "title": "IBM unveils 1000-qubit quantum processor",
                        "url": "https://example.com/ibm-quantum",
                        "publishedAt": "2025-06-15T10:30:00Z",
                        "source": {"name": "Reuters"},
                    },
                    {
                        "title": "IBM reports Q3 earnings beat",
                        "url": "https://example.com/ibm-earnings",
                        "publishedAt": "2025-06-14T08:00:00Z",
                        "source": {"name": "CNBC"},
                    },
                ],
            },
            request=httpx.Request("GET", "https://newsapi.org/v2/everything"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        articles = await adapter.fetch_articles(
            "IBM", "IBM", limit=10, sector="big_tech"
        )

        assert len(articles) == 1
        assert "qubit" in articles[0].title.lower()

    @pytest.mark.asyncio
    async def test_fetch_keeps_company_name_articles_for_pure_play(self):
        """Pure-play sector keeps articles mentioning the company name."""
        mock_response = httpx.Response(
            200,
            json={
                "status": "ok",
                "articles": [
                    {
                        "title": "IonQ announces partnership with Hyundai",
                        "url": "https://example.com/ionq-hyundai",
                        "publishedAt": "2025-06-15T10:30:00Z",
                        "source": {"name": "Reuters"},
                    },
                    {
                        "title": "IonQ stock surges on earnings",
                        "url": "https://example.com/ionq-earnings",
                        "publishedAt": "2025-06-14T08:00:00Z",
                        "source": {"name": "CNBC"},
                    },
                    {
                        "title": (
                            "GraniteShares Announces Weekly "
                            "Distributions for ETFs"
                        ),
                        "url": "https://example.com/graniteshares",
                        "publishedAt": "2025-06-13T08:00:00Z",
                        "source": {"name": "GlobeNewswire"},
                    },
                ],
            },
            request=httpx.Request("GET", "https://newsapi.org/v2/everything"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        articles = await adapter.fetch_articles(
            "IonQ", "IONQ", limit=10, sector="pure_play"
        )

        # IonQ articles kept (company name in title), GraniteShares filtered out
        assert len(articles) == 2
        assert all("IonQ" in a.title for a in articles)

    @pytest.mark.asyncio
    async def test_fetch_filters_etf_roundup_for_pure_play(self):
        """Pure-play sector should filter out ETF roundup articles."""
        mock_response = httpx.Response(
            200,
            json={
                "status": "ok",
                "articles": [
                    {
                        "title": (
                            "D-Wave Keeps Delivering Good News"
                            "\u2014So Why Is It Falling?"
                        ),
                        "url": "https://example.com/dwave-news",
                        "publishedAt": "2025-06-15T10:30:00Z",
                        "source": {"name": "MarketBeat"},
                    },
                    {
                        "title": (
                            "Tidal Financial Group and Defiance ETFs "
                            "Announce Reverse Stock Splits for Select ETFs"
                        ),
                        "url": "https://example.com/tidal-etf",
                        "publishedAt": "2025-06-14T08:00:00Z",
                        "source": {"name": "GlobeNewswire"},
                    },
                ],
            },
            request=httpx.Request("GET", "https://newsapi.org/v2/everything"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        articles = await adapter.fetch_articles(
            "D-Wave Quantum", "QBTS", limit=10, sector="pure_play"
        )

        assert len(articles) == 1
        assert "D-Wave" in articles[0].title

    @pytest.mark.asyncio
    async def test_fetch_uses_search_in_for_non_big_tech(self):
        """Non-big-tech sectors should use searchIn=title,description."""
        captured_params: dict[str, str] = {}

        def transport(request: httpx.Request) -> httpx.Response:
            captured_params.update(dict(request.url.params))
            return httpx.Response(
                200,
                json={"status": "ok", "articles": []},
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        await adapter.fetch_articles(
            "D-Wave Quantum", "QBTS", limit=10, sector="pure_play"
        )
        assert captured_params.get("searchIn") == "title,description"

    @pytest.mark.asyncio
    async def test_fetch_no_search_in_for_big_tech(self):
        """Big-tech sectors should NOT set searchIn (query has AND clause)."""
        captured_params: dict[str, str] = {}

        def transport(request: httpx.Request) -> httpx.Response:
            captured_params.update(dict(request.url.params))
            return httpx.Response(
                200,
                json={"status": "ok", "articles": []},
                request=request,
            )

        mock_client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        await adapter.fetch_articles("IBM", "IBM", limit=10, sector="big_tech")
        assert "searchIn" not in captured_params


class TestIsQuantumRelevant:
    """Tests for the low-level _is_quantum_relevant static method."""

    def test_quantum_title_is_relevant(self):
        assert NewsApiAdapter._is_quantum_relevant(
            "IBM advances quantum computing roadmap"
        )

    def test_generic_title_is_not_relevant(self):
        assert not NewsApiAdapter._is_quantum_relevant(
            "Google reports record Q3 advertising revenue"
        )

    def test_case_insensitive(self):
        assert NewsApiAdapter._is_quantum_relevant(
            "QUANTUM COMPUTING Breakthrough at Google"
        )

    def test_qubit_keyword(self):
        assert NewsApiAdapter._is_quantum_relevant(
            "IBM announces 1000-qubit processor milestone"
        )

    def test_superconducting_keyword(self):
        assert NewsApiAdapter._is_quantum_relevant(
            "New superconducting chip design from Intel"
        )

    def test_entanglement_keyword(self):
        assert NewsApiAdapter._is_quantum_relevant(
            "Scientists achieve long-distance entanglement"
        )

    def test_error_correction_keyword(self):
        assert NewsApiAdapter._is_quantum_relevant(
            "Google demonstrates error correction at scale"
        )

    def test_empty_title(self):
        assert not NewsApiAdapter._is_quantum_relevant("")


class TestIsRelevantArticle:
    """Tests for the sector-aware _is_relevant_article method."""

    def test_quantum_keyword_relevant_for_any_sector(self):
        assert NewsApiAdapter._is_relevant_article(
            "D-Wave advances quantum annealing", "D-Wave Quantum", "pure_play"
        )

    def test_company_name_relevant_for_pure_play(self):
        assert NewsApiAdapter._is_relevant_article(
            "D-Wave Keeps Delivering Good News", "D-Wave Quantum", "pure_play"
        )

    def test_etf_roundup_rejected_for_pure_play(self):
        assert not NewsApiAdapter._is_relevant_article(
            "GraniteShares Announces Weekly Distributions for ETFs",
            "D-Wave Quantum",
            "pure_play",
        )

    def test_stock_split_rejected_for_pure_play(self):
        assert not NewsApiAdapter._is_relevant_article(
            "Tidal Financial Group and Defiance ETFs Announce Reverse Stock Splits",
            "D-Wave Quantum",
            "pure_play",
        )

    def test_company_name_not_relevant_for_big_tech(self):
        # For big-tech, only quantum keywords count
        assert not NewsApiAdapter._is_relevant_article(
            "IBM reports Q3 earnings beat", "IBM", "big_tech"
        )

    def test_quantum_keyword_relevant_for_big_tech(self):
        assert NewsApiAdapter._is_relevant_article(
            "IBM unveils 1000-qubit quantum processor", "IBM", "big_tech"
        )

    def test_first_part_of_name_matches(self):
        # "D-Wave" is the first part of "D-Wave Quantum"
        assert NewsApiAdapter._is_relevant_article(
            "D-Wave Keeps Delivering Good News", "D-Wave Quantum", "pure_play"
        )

    def test_empty_title_rejected(self):
        assert not NewsApiAdapter._is_relevant_article(
            "", "D-Wave Quantum", "pure_play"
        )


class TestValidateUrl:
    @pytest.mark.asyncio
    async def test_valid_url_returns_true(self):
        mock_response = httpx.Response(
            200,
            request=httpx.Request("HEAD", "https://example.com/article"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        result = await adapter.validate_url("https://example.com/article")
        assert result is True

    @pytest.mark.asyncio
    async def test_404_returns_false(self):
        mock_response = httpx.Response(
            404,
            request=httpx.Request("HEAD", "https://example.com/missing"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        result = await adapter.validate_url("https://example.com/missing")
        assert result is False

    @pytest.mark.asyncio
    async def test_timeout_returns_false(self):
        async def raise_timeout(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Timed out")

        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(raise_timeout)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        result = await adapter.validate_url("https://example.com/slow")
        assert result is False

    @pytest.mark.asyncio
    async def test_redirect_returns_true(self):
        mock_response = httpx.Response(
            301,
            headers={"Location": "https://example.com/new-url"},
            request=httpx.Request("HEAD", "https://example.com/old"),
        )
        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda req: mock_response)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        result = await adapter.validate_url("https://example.com/old")
        assert result is True

    @pytest.mark.asyncio
    async def test_connection_error_returns_false(self):
        async def raise_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection failed")

        mock_client = httpx.AsyncClient(
            transport=httpx.MockTransport(raise_error)
        )
        adapter = NewsApiAdapter(api_key="test-key", http_client=mock_client)

        result = await adapter.validate_url("https://example.com/down")
        assert result is False
