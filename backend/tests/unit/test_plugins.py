"""Unit tests for plugin protocol and registry."""

import pytest

from src.domain.interfaces.plugins import DataSourcePlugin, PluginRegistry


class MockPlugin:
    """A mock data source plugin for testing."""

    def __init__(self, name: str, data_types: list[str] | None = None) -> None:
        self._name = name
        self._version = "1.0.0"
        self._supported_data_types = data_types or ["stock"]
        self._initialized = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def supported_data_types(self) -> list[str]:
        return self._supported_data_types

    async def initialize(self, config: dict[str, str]) -> None:
        self._initialized = True

    async def health_check(self) -> bool:
        return True

    async def shutdown(self) -> None:
        self._initialized = False


class TestDataSourcePlugin:
    def test_mock_implements_protocol(self):
        plugin = MockPlugin("test")
        assert isinstance(plugin, DataSourcePlugin)

    async def test_plugin_lifecycle(self):
        plugin = MockPlugin("test")
        await plugin.initialize({})
        assert plugin._initialized
        assert await plugin.health_check()
        await plugin.shutdown()
        assert not plugin._initialized


class TestPluginRegistry:
    def test_register_and_get(self):
        registry = PluginRegistry()
        plugin = MockPlugin("yahoo")
        registry.register(plugin)
        assert registry.get("yahoo") is plugin

    def test_get_returns_none_for_unknown(self):
        registry = PluginRegistry()
        assert registry.get("unknown") is None

    def test_duplicate_registration_raises(self):
        registry = PluginRegistry()
        plugin = MockPlugin("yahoo")
        registry.register(plugin)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(MockPlugin("yahoo"))

    def test_get_all(self):
        registry = PluginRegistry()
        registry.register(MockPlugin("a"))
        registry.register(MockPlugin("b"))
        assert len(registry.get_all()) == 2

    def test_get_by_data_type(self):
        registry = PluginRegistry()
        registry.register(MockPlugin("stock_plugin", ["stock"]))
        registry.register(MockPlugin("news_plugin", ["news"]))
        registry.register(MockPlugin("multi_plugin", ["stock", "news"]))

        stock_plugins = registry.get_by_data_type("stock")
        assert len(stock_plugins) == 2

        news_plugins = registry.get_by_data_type("news")
        assert len(news_plugins) == 2

        patent_plugins = registry.get_by_data_type("patent")
        assert len(patent_plugins) == 0
