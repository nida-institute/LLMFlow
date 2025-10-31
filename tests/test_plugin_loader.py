"""Tests for plugin loader."""

import pytest
from llmflow.plugins.loader import discover_plugins, plugin_registry


class TestPluginLoader:
    """Test the plugin loading system."""

    def test_discover_plugins_loads_builtin_plugins(self):
        """Test that built-in plugins are loaded."""
        # Plugins are already loaded at module import time
        assert "xpath" in plugin_registry
        assert "tsv" in plugin_registry
        assert "csv" in plugin_registry

    def test_plugin_registry_is_dict(self):
        """Test that plugin_registry is a dictionary."""
        assert isinstance(plugin_registry, dict)

    def test_plugins_are_callable(self):
        """Test that registered plugins are callable."""
        for plugin_name, plugin_func in plugin_registry.items():
            assert callable(plugin_func), f"Plugin '{plugin_name}' is not callable"

    def test_discover_plugins_can_be_called_multiple_times(self):
        """Test that discover_plugins is idempotent."""
        initial_count = len(plugin_registry)

        # Call discover_plugins again
        discover_plugins()

        # Should have same number of plugins (not duplicates)
        assert len(plugin_registry) == initial_count
