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
