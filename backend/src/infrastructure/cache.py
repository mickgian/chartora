"""In-memory TTL-based cache for API response caching."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _CacheEntry:
    """A single cache entry with expiration."""

    value: Any
    expires_at: float


class InMemoryCache:
    """Thread-safe in-memory cache with TTL-based expiration.

    Uses asyncio.Lock to ensure safe concurrent access.
    """

    def __init__(self, default_ttl: int = 300) -> None:
        self._store: dict[str, _CacheEntry] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        self._default_ttl: int = default_ttl

    async def get(self, key: str) -> Any | None:
        """Retrieve a value by key, returning None if missing or expired."""
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value with a TTL (defaults to the cache's default_ttl)."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expires_at = time.monotonic() + ttl
        async with self._lock:
            self._store[key] = _CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        """Remove a single key from the cache."""
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        """Remove all entries from the cache."""
        async with self._lock:
            self._store.clear()

    async def _evict_expired(self) -> int:
        """Remove all expired entries and return the count of evicted items."""
        now = time.monotonic()
        async with self._lock:
            expired_keys = [
                k for k, v in self._store.items() if now > v.expires_at
            ]
            for k in expired_keys:
                del self._store[k]
            return len(expired_keys)

    @property
    def size(self) -> int:
        """Return the current number of entries (including possibly expired)."""
        return len(self._store)


# Module-level singleton
cache: InMemoryCache = InMemoryCache()
