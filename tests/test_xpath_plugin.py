import llmflow.plugins
import importlib
from llmflow.plugins.loader import load_plugins

def test_xpath_extracts_entries():
    importlib.import_module("llmflow.plugins.contrib.xpath")
    load_plugins()
    xpath = llmflow.plugins.plugin_registry["xpath"]
    assert callable(xpath)
