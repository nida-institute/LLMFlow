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

import tempfile
from pathlib import Path

import pytest
from lxml import etree

from llmflow.plugins.xpath import execute


class TestXPathPlugin:
    """Test XPath plugin functionality."""

    @pytest.fixture
    def sample_xml(self, tmp_path):
        """Create a sample XML file for testing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item id="1">First</item>
    <item id="2">Second</item>
    <item id="3">Third</item>
</root>
"""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content)
        return xml_file

    @pytest.fixture
    def namespaced_xml(self, tmp_path):
        """Create XML with namespaces for testing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<tei:root xmlns:tei="http://www.tei-c.org/ns/1.0">
    <tei:entry key="alpha">Alpha entry</tei:entry>
    <tei:entry key="beta">Beta entry</tei:entry>
</tei:root>
"""
        xml_file = tmp_path / "test_ns.xml"
        xml_file.write_text(xml_content)
        return xml_file

    def test_extract_text_from_elements(self, sample_xml):
        """Test extracting text content from XML elements."""
        config = {
            "path": str(sample_xml),
            "xpath": "//item",
            "output_format": "text",
        }

        results = list(execute(config))

        assert len(results) == 3
        assert results[0] == "First"
        assert results[1] == "Second"
        assert results[2] == "Third"

    def test_extract_xml_strings(self, sample_xml):
        """Test extracting XML strings from elements."""
        config = {
            "path": str(sample_xml),
            "xpath": "//item",
            "output_format": "xml-string",
        }

        results = list(execute(config))

        assert len(results) == 3
        assert '<item id="1">First</item>' in results[0]
        assert '<item id="2">Second</item>' in results[1]
        assert '<item id="3">Third</item>' in results[2]

    def test_extract_attribute_values(self, sample_xml):
        """Test extracting attribute values using XPath."""
        config = {
            "path": str(sample_xml),
            "xpath": "//item/@id",
            "output_format": "text",
        }

        results = list(execute(config))

        assert len(results) == 3
        assert "1" in results
        assert "2" in results
        assert "3" in results

    def test_xpath_with_namespaces(self, namespaced_xml):
        """Test XPath queries on XML with namespaces."""
        config = {
            "path": str(namespaced_xml),
            "xpath": "//tei:entry/@key",
            "output_format": "text",
            "namespaces": {"tei": "http://www.tei-c.org/ns/1.0"},
        }

        results = list(execute(config))

        assert len(results) == 2
        assert "alpha" in results
        assert "beta" in results

    def test_xpath_with_namespaces_element_text(self, namespaced_xml):
        """Test extracting text from namespaced elements."""
        config = {
            "path": str(namespaced_xml),
            "xpath": "//tei:entry",
            "output_format": "text",
            "namespaces": {"tei": "http://www.tei-c.org/ns/1.0"},
        }

        results = list(execute(config))

        assert len(results) == 2
        assert "Alpha entry" in results
        assert "Beta entry" in results

    def test_nested_inputs_config(self, sample_xml):
        """Test plugin with nested 'inputs' config structure."""
        config = {
            "inputs": {
                "path": str(sample_xml),
                "xpath": "//item",
                "output_format": "text",
            }
        }

        results = list(execute(config))

        assert len(results) == 3
        assert results[0] == "First"

    def test_flat_config_structure(self, sample_xml):
        """Test plugin with flat config structure (no nested inputs)."""
        config = {
            "path": str(sample_xml),
            "xpath": "//item",
            "output_format": "text",
        }

        results = list(execute(config))

        assert len(results) == 3
        assert results[0] == "First"

    def test_from_keyword_instead_of_path(self, sample_xml):
        """Test using 'from' keyword instead of 'path'."""
        config = {
            "from": str(sample_xml),
            "xpath": "//item",
            "output_format": "text",
        }

        results = list(execute(config))

        assert len(results) == 3
        assert results[0] == "First"

    def test_default_output_format_is_xml_string(self, sample_xml):
        """Test that default output format is xml-string."""
        config = {
            "path": str(sample_xml),
            "xpath": "//item[@id='1']",
        }

        results = list(execute(config))

        assert len(results) == 1
        assert '<item id="1">First</item>' in results[0]

    def test_empty_results(self, sample_xml):
        """Test XPath that returns no results."""
        config = {
            "path": str(sample_xml),
            "xpath": "//nonexistent",
            "output_format": "text",
        }

        results = list(execute(config))

        assert len(results) == 0

    def test_complex_xpath_expression(self, sample_xml):
        """Test complex XPath expression with predicates."""
        config = {
            "path": str(sample_xml),
            "xpath": "//item[@id='2']",
            "output_format": "text",
        }

        results = list(execute(config))

        assert len(results) == 1
        assert results[0] == "Second"

    def test_missing_path_raises_error(self):
        """Test that missing path raises ValueError."""
        config = {
            "xpath": "//item",
            "output_format": "text",
        }

        with pytest.raises(ValueError, match="xpath requires 'path' or 'from' key"):
            list(execute(config))

    def test_missing_xpath_raises_error(self, sample_xml):
        """Test that missing xpath key raises KeyError."""
        config = {
            "path": str(sample_xml),
            "output_format": "text",
        }

        with pytest.raises(KeyError):
            list(execute(config))

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        config = {
            "path": "/nonexistent/file.xml",
            "xpath": "//item",
            "output_format": "text",
        }

        with pytest.raises((FileNotFoundError, OSError)):
            list(execute(config))

    def test_malformed_xml(self, tmp_path):
        """Test handling of malformed XML."""
        xml_file = tmp_path / "malformed.xml"
        xml_file.write_text("This is not valid XML")

        config = {
            "path": str(xml_file),
            "xpath": "//item",
            "output_format": "text",
        }

        with pytest.raises(etree.XMLSyntaxError):
            list(execute(config))

    def test_invalid_xpath_expression(self, sample_xml):
        """Test handling of invalid XPath expression."""
        config = {
            "path": str(sample_xml),
            "xpath": "//item[[[invalid",
            "output_format": "text",
        }

        with pytest.raises(etree.XPathEvalError):
            list(execute(config))

    def test_element_with_no_text(self, tmp_path):
        """Test extracting text from element with no text content."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <empty></empty>
    <also-empty/>
</root>
"""
        xml_file = tmp_path / "empty.xml"
        xml_file.write_text(xml_content)

        config = {
            "path": str(xml_file),
            "xpath": "//empty",
            "output_format": "text",
        }

        results = list(execute(config))

        assert len(results) == 1
        assert results[0] == ""

    def test_mixed_content_extraction(self, tmp_path):
        """Test extracting from elements with mixed content."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <mixed>Text <emphasis>emphasized</emphasis> more text</mixed>
</root>
"""
        xml_file = tmp_path / "mixed.xml"
        xml_file.write_text(xml_content)

        config = {
            "path": str(xml_file),
            "xpath": "//mixed",
            "output_format": "text",
        }

        results = list(execute(config))

        # Only the direct text of the element, not child text
        assert len(results) == 1
        assert results[0] == "Text "

    def test_xpath_returns_generator(self, sample_xml):
        """Test that execute returns a generator."""
        config = {
            "path": str(sample_xml),
            "xpath": "//item",
            "output_format": "text",
        }

        result = execute(config)

        # Should be a generator, not a list
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')

    def test_multiple_namespace_prefixes(self, tmp_path):
        """Test XPath with multiple namespace prefixes."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:a="http://example.com/a" xmlns:b="http://example.com/b">
    <a:item>Item A</a:item>
    <b:item>Item B</b:item>
</root>
"""
        xml_file = tmp_path / "multi_ns.xml"
        xml_file.write_text(xml_content)

        config = {
            "path": str(xml_file),
            "xpath": "//a:item | //b:item",
            "output_format": "text",
            "namespaces": {
                "a": "http://example.com/a",
                "b": "http://example.com/b",
            },
        }

        results = list(execute(config))

        assert len(results) == 2
        assert "Item A" in results
        assert "Item B" in results

    def test_register_function(self):
        """Test the register function returns correct dict."""
        from llmflow.plugins.xpath import register

        plugins = register()

        assert "xpath" in plugins
        assert callable(plugins["xpath"])
        assert plugins["xpath"] == execute
