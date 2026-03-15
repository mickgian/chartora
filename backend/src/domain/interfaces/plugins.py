"""Plugin protocol and registry for extensible data sources."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DataSourcePlugin(Protocol):
    """Protocol defining the interface for pluggable data sources.

    Plugins provide a standardised way to add new data sources to the
    system without modifying existing code.  Each plugin declares the
    data types it supports and exposes lifecycle hooks for
    initialisation, health checking, and graceful shutdown.
    """

    @property
    def name(self) -> str:
        """Unique identifier for this plugin."""
        ...

    @property
    def version(self) -> str:
        """Semantic version string of this plugin."""
        ...

    @property
    def supported_data_types(self) -> list[str]:
        """Data types this plugin can provide (e.g. 'stock', 'patent', 'news')."""
        ...

    async def initialize(self, config: dict[str, str]) -> None:
        """Perform any async setup required before the plugin is used.

        Args:
            config: Key-value configuration for the plugin.
        """
        ...

    async def health_check(self) -> bool:
        """Return True if the plugin is healthy and ready to serve requests."""
        ...

    async def shutdown(self) -> None:
        """Gracefully release resources held by the plugin."""
        ...


class PluginRegistry:
    """Thread-safe registry for managing data source plugins.

    Plugins are stored by their unique name and can be queried
    individually, listed in bulk, or filtered by supported data type.
    """

    def __init__(self) -> None:
        """Initialise an empty plugin registry."""
        self._plugins: dict[str, DataSourcePlugin] = {}

    def register(self, plugin: DataSourcePlugin) -> None:
        """Register a plugin, keyed by its name.

        Args:
            plugin: The data source plugin to register.

        Raises:
            ValueError: If a plugin with the same name is already registered.
        """
        if plugin.name in self._plugins:
            msg = f"Plugin '{plugin.name}' is already registered"
            raise ValueError(msg)
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> DataSourcePlugin | None:
        """Retrieve a plugin by name, or None if not found.

        Args:
            name: The unique name of the plugin.

        Returns:
            The plugin instance, or None if no plugin with that name exists.
        """
        return self._plugins.get(name)

    def get_all(self) -> list[DataSourcePlugin]:
        """Return all registered plugins.

        Returns:
            A list of all registered plugin instances.
        """
        return list(self._plugins.values())

    def get_by_data_type(self, data_type: str) -> list[DataSourcePlugin]:
        """Return all plugins that support a given data type.

        Args:
            data_type: The data type to filter by (e.g. 'stock').

        Returns:
            A list of plugins whose supported_data_types include *data_type*.
        """
        return [
            plugin
            for plugin in self._plugins.values()
            if data_type in plugin.supported_data_types
        ]
