"""XPath plugin for extracting data from XML files."""

from lxml import etree


def execute(step_config):
    """
    Execute XPath query on XML file.

    Args:
        step_config: Dictionary containing:
            - path: Path to XML file
            - xpath: XPath expression
            - namespaces: Optional namespace mappings
            - output_format: 'text' or 'xml-string' (default: 'xml-string')

    Returns:
        Generator yielding extracted data
    """
    path = step_config["path"]
    xpath_expr = step_config["xpath"]
    output_format = step_config.get("output_format", "xml-string")
    nsmap = step_config.get("namespaces", {})

    with open(path, "rb") as f:
        tree = etree.parse(f)

    nodes = tree.xpath(xpath_expr, namespaces=nsmap)

    for node in nodes:
        if output_format == "xml-string":
            # Check if it's an element or already a string (attribute/text)
            if hasattr(node, 'tag'):
                yield etree.tostring(node, encoding="unicode")
            else:
                yield str(node)
        elif output_format == "text":
            # Handle elements vs. strings (attributes, text nodes)
            if hasattr(node, 'text'):
                yield (node.text or "").strip()
            else:
                yield str(node).strip()
        else:
            raise ValueError(f"Unsupported output_format: {output_format}")


def register():
    """Register the xpath plugin."""
    return {
        "xpath": execute
    }
"""Tests for XPath plugin."""

from pathlib import Path

import llmflow.plugins
from llmflow.plugins.loader import discover_plugins

# Ensure plugins are loaded
discover_plugins()


class TestXPathPlugin:
    """Test the XPath plugin."""

    def test_xpath_plugin_text_extraction(self, tmp_path):
        """Test extracting text from XML using XPath."""
        # Create a test XML file
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item>First</item>
    <item>Second</item>
    <item>Third</item>
</root>
"""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content)

        # Configure the xpath step
        step_config = {
            "path": str(xml_file),
            "xpath": "//item",
            "output_format": "text",
        }

        # Execute the plugin
        plugin_func = llmflow.plugins.plugin_registry["xpath"]
        results = list(plugin_func(step_config))

        # Verify results
        assert len(results) == 3
        assert results[0] == "First"
        assert results[1] == "Second"
        assert results[2] == "Third"

    def test_xpath_plugin_xml_string_extraction(self, tmp_path):
        """Test extracting XML strings using XPath."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item id="1">First</item>
    <item id="2">Second</item>
</root>
"""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content)

        step_config = {
            "path": str(xml_file),
            "xpath": "//item",
            "output_format": "xml-string",
        }

        plugin_func = llmflow.plugins.plugin_registry["xpath"]
        results = list(plugin_func(step_config))

        assert len(results) == 2
        assert 'id="1"' in results[0]
        assert 'id="2"' in results[1]
        assert "First" in results[0]
        assert "Second" in results[1]

    def test_xpath_plugin_with_namespaces(self, tmp_path):
        """Test XPath with XML namespaces."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<tei:root xmlns:tei="http://www.tei-c.org/ns/1.0">
    <tei:entry key="alpha">Alpha entry</tei:entry>
    <tei:entry key="beta">Beta entry</tei:entry>
</tei:root>
"""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content)

        step_config = {
            "path": str(xml_file),
            "xpath": "//tei:entry/@key",
            "output_format": "text",
            "namespaces": {"tei": "http://www.tei-c.org/ns/1.0"},
        }

        plugin_func = llmflow.plugins.plugin_registry["xpath"]
        results = list(plugin_func(step_config))

        assert len(results) == 2
        assert "alpha" in results
        assert "beta" in results
