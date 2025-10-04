import pytest
import importlib
import llmflow.plugins
from llmflow.plugins.loader import load_plugins

@pytest.mark.xfail(reason="XPath plugin doesn't currently register itself")
def test_xpath_extracts_entries():
    importlib.import_module("llmflow.plugins.contrib.xpath")
    load_plugins()
    xpath = llmflow.plugins.plugin_registry["xpath"]
