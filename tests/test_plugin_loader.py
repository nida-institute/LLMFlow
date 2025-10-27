import pytest

import llmflow.plugins
from llmflow.plugins.loader import load_plugins


def test_load_plugins_registers_expected():
    """Test that plugins are registered correctly"""
    llmflow.plugins.plugin_registry.clear()
    load_plugins()
    assert (
        llmflow.plugins.plugin_registry
    ), "Plugin registry should not be empty after loading."
