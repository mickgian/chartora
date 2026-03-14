"""Cache utilities for FastAPI route handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from src.infrastructure.cache import cache

if TYPE_CHECKING:
    from starlette.requests import Request


def cache_key_for_request(request: Request) -> str:
    """Build a deterministic cache key from the HTTP method, path, and query params.

    Query parameters are sorted to ensure consistent keys regardless of order.
    """
    sorted_params = urlencode(sorted(request.query_params.items()))
    path = request.url.path
    method = request.method.upper()
    if sorted_params:
        return f"{method}:{path}?{sorted_params}"
    return f"{method}:{path}"


async def get_cached_or_none(key: str) -> Any | None:
    """Return a cached value for the given key, or None if not found/expired."""
    return await cache.get(key)


async def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """Store a value in the cache with the specified TTL in seconds."""
    await cache.set(key, value, ttl_seconds=ttl)
