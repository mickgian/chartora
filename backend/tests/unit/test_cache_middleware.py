"""Unit tests for cache middleware utilities."""

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from src.adapters.api.cache_middleware import (
    cache_key_for_request,
    get_cached_or_none,
    set_cache,
)


class TestCacheKeyForRequest:
    def test_simple_path(self):
        """Build a cache key from a simple request."""
        app = Starlette()

        @app.route("/api/test")
        async def handler(request: Request):
            key = cache_key_for_request(request)
            return PlainTextResponse(key)

        client = TestClient(app)
        response = client.get("/api/test")
        assert response.text == "GET:/api/test"

    def test_with_query_params_sorted(self):
        """Query params should be sorted for deterministic keys."""
        app = Starlette()

        @app.route("/api/test")
        async def handler(request: Request):
            key = cache_key_for_request(request)
            return PlainTextResponse(key)

        client = TestClient(app)
        response = client.get("/api/test?b=2&a=1")
        assert "a=1" in response.text
        assert response.text.index("a=1") < response.text.index("b=2")


class TestCacheHelpers:
    async def test_get_and_set(self):
        await set_cache("test_key", {"data": "hello"}, ttl=60)
        result = await get_cached_or_none("test_key")
        assert result == {"data": "hello"}

    async def test_get_missing_key(self):
        result = await get_cached_or_none("missing_key_12345")
        assert result is None
