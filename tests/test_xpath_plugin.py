# tests/test_xpath_plugin.py

from llmflow.plugins import plugin_registry
from llmflow.plugins.loader import load_plugins
import os

def test_xpath_extracts_entries():
    load_plugins()
    xpath = plugin_registry["xpath"]

    input_spec = {
        "path": os.path.join(os.path.dirname(__file__), "data", "sample.xml"),
        "xpath": "//entry",
        "output_format": "xml-string"
    }

    entries = list(xpath(input_spec))
    assert len(entries) == 2
    assert "λόγος" in entries[0]
    assert "ἀγάπη" in entries[1]
