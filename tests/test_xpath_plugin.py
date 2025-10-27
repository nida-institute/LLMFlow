import importlib

import pytest

import llmflow.plugins
from llmflow.plugins.loader import load_plugins


def test_xpath_extracts_entries():
    """Test XPath extraction functionality"""
    importlib.import_module("llmflow.plugins.contrib.xpath")
    load_plugins()
    llmflow.plugins.plugin_registry["xpath"]
