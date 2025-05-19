# tests/test_plugin_loader.py

from llmflow.plugins import plugin_registry
from llmflow.plugins.loader import load_plugins

def test_load_plugins_registers_expected():
    # Clear plugin registry before test if needed (use with caution in shared envs)
    plugin_registry.clear()

    # Load all plugins
    load_plugins()

    # Check that the registry is not empty
    assert plugin_registry, "Plugin registry should not be empty after loading."

    # Check that the 'xpath' plugin was registered
    assert "xpath" in plugin_registry, "'xpath' plugin should be registered."

    # Check that it's callable
    assert callable(plugin_registry["xpath"]), "'xpath' plugin should be a function."

