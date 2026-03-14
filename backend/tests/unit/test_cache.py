"""Unit tests for in-memory cache."""

import asyncio

import pytest

from src.infrastructure.cache import InMemoryCache


@pytest.fixture
def cache():
    return InMemoryCache(default_ttl=1)


class TestInMemoryCache:
    async def test_get_returns_none_for_missing_key(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    async def test_set_and_get(self, cache):
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    async def test_set_with_custom_ttl(self, cache):
        await cache.set("key1", "value1", ttl_seconds=10)
        result = await cache.get("key1")
        assert result == "value1"

    async def test_expired_entry_returns_none(self, cache):
        await cache.set("key1", "value1", ttl_seconds=0)
        # Entry should be expired immediately (ttl=0 means expires_at = now)
        await asyncio.sleep(0.01)
        result = await cache.get("key1")
        assert result is None

    async def test_delete(self, cache):
        await cache.set("key1", "value1")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    async def test_delete_nonexistent_key(self, cache):
        # Should not raise
        await cache.delete("nonexistent")

    async def test_clear(self, cache):
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        assert cache.size == 2
        await cache.clear()
        assert cache.size == 0

    async def test_size(self, cache):
        assert cache.size == 0
        await cache.set("key1", "value1")
        assert cache.size == 1
        await cache.set("key2", "value2")
        assert cache.size == 2

    async def test_evict_expired(self, cache):
        await cache.set("key1", "value1", ttl_seconds=0)
        await cache.set("key2", "value2", ttl_seconds=100)
        await asyncio.sleep(0.01)
        evicted = await cache._evict_expired()
        assert evicted == 1
        assert cache.size == 1

    async def test_stores_any_value_type(self, cache):
        await cache.set("dict", {"a": 1})
        await cache.set("list", [1, 2, 3])
        await cache.set("int", 42)
        assert await cache.get("dict") == {"a": 1}
        assert await cache.get("list") == [1, 2, 3]
        assert await cache.get("int") == 42
