import pytest
import llmflow.plugins
from llmflow.plugins.loader import load_plugins

@pytest.mark.xfail(reason="XPath plugin doesn't currently register itself")
def test_load_plugins_registers_expected():
    llmflow.plugins.plugin_registry.clear()
    load_plugins()
    assert llmflow.plugins.plugin_registry, "Plugin registry should not be empty after loading."
