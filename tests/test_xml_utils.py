"""Tests for src/llmflow/utils/xml.py — xpath_get helper."""

import pytest
from lxml import etree

from llmflow.utils.xml import xpath_get


SIMPLE_XML = """<root>
  <item id="1">hello</item>
  <item id="2">world</item>
  <child>inner</child>
</root>"""

NAMESPACED_XML = """<root xmlns:tei="http://www.tei-c.org/ns/1.0">
  <tei:entry key="test">value</tei:entry>
</root>"""


class TestXpathGet:

    def test_single_text_result(self):
        """Single matching element returns its text."""
        result = xpath_get(SIMPLE_XML, "//child/text()")
        assert result == "inner"

    def test_multiple_results_returns_list(self):
        """Multiple matches return a list of text values."""
        result = xpath_get(SIMPLE_XML, "//item/text()")
        assert isinstance(result, list)
        assert result == ["hello", "world"]

    def test_single_element_returns_text(self):
        """Single element result extracts .text attribute."""
        result = xpath_get(SIMPLE_XML, "//child")
        assert result == "inner"

    def test_attribute_xpath(self):
        """XPath returning an attribute value (string) passes through."""
        result = xpath_get(SIMPLE_XML, "//item[@id='1']/@id")
        assert result == "1"

    def test_namespaced_xpath(self):
        """Namespaced XPath with explicit namespace map works."""
        result = xpath_get(
            NAMESPACED_XML,
            "//tei:entry/text()",
            namespaces={"tei": "http://www.tei-c.org/ns/1.0"},
        )
        assert result == "value"

    def test_no_match_returns_empty_list(self):
        """XPath that matches nothing returns an empty list."""
        result = xpath_get(SIMPLE_XML, "//nonexistent")
        assert result == []

    def test_invalid_xml_raises(self):
        """Malformed XML should raise."""
        with pytest.raises(etree.XMLSyntaxError):
            xpath_get("<bad xml", "//anything")
