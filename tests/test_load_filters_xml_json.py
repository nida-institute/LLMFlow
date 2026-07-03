"""Tests for xpath: on load_xml and key: on load_json/load_yaml."""
import json
import pytest
from pathlib import Path
from llmflow.runner import run_load_step
from llmflow.utils.data import apply_xml_xpath, apply_key_extract


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

XML_CONTENT = """\
<?xml version="1.0" encoding="utf-8"?>
<book code="MRK">
  <pericope id="MRK-001" title="Baptism of Jesus">
    <verse ref="MRK 1:9">And it came to pass</verse>
    <verse ref="MRK 1:10">And immediately coming up</verse>
  </pericope>
  <pericope id="MRK-002" title="Temptation of Jesus">
    <verse ref="MRK 1:12">And immediately the Spirit drove him</verse>
  </pericope>
</book>
"""

JSON_CONTENT = {
    "book": "Mark",
    "pericopes": [
        {"id": "MRK-001", "title": "Baptism of Jesus", "verse_count": 2},
        {"id": "MRK-002", "title": "Temptation of Jesus", "verse_count": 1},
    ],
    "meta": {
        "language": "en",
        "version": "1.0",
    },
}


@pytest.fixture
def xml_file(tmp_path):
    p = tmp_path / "book.xml"
    p.write_text(XML_CONTENT)
    return p


@pytest.fixture
def json_file(tmp_path):
    p = tmp_path / "book.json"
    p.write_text(json.dumps(JSON_CONTENT))
    return p


@pytest.fixture
def yaml_file(tmp_path):
    import yaml
    p = tmp_path / "book.yaml"
    p.write_text(yaml.dump(JSON_CONTENT))
    return p


# ---------------------------------------------------------------------------
# Unit tests: apply_xml_xpath
# ---------------------------------------------------------------------------

class TestApplyXmlXpath:
    def _load_element(self, xml_file):
        from llmflow.utils.data import load_xml_file
        return load_xml_file(str(xml_file))

    def test_no_xpath_returns_root_element(self, xml_file):
        from lxml import etree
        element = self._load_element(xml_file)
        result = apply_xml_xpath(element, {})
        assert isinstance(result, etree._Element)
        assert result.tag == "book"

    def test_xpath_returns_list_of_elements(self, xml_file):
        element = self._load_element(xml_file)
        result = apply_xml_xpath(element, {"xpath": "//pericope"})
        assert isinstance(result, list)
        assert len(result) == 2

    def test_xpath_attribute_filter(self, xml_file):
        element = self._load_element(xml_file)
        result = apply_xml_xpath(element, {"xpath": "//pericope[@id='MRK-001']"})
        assert len(result) == 1
        assert result[0].get("id") == "MRK-001"

    def test_xpath_output_format_xml_string(self, xml_file):
        element = self._load_element(xml_file)
        result = apply_xml_xpath(element, {
            "xpath": "//verse",
            "output_format": "xml-string",
        })
        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)
        assert all("<verse" in s for s in result)

    def test_xpath_output_format_text(self, xml_file):
        element = self._load_element(xml_file)
        result = apply_xml_xpath(element, {
            "xpath": "//verse",
            "output_format": "text",
        })
        assert isinstance(result, list)
        assert "And it came to pass" in result

    def test_xpath_output_format_element_default(self, xml_file):
        from lxml import etree
        element = self._load_element(xml_file)
        result = apply_xml_xpath(element, {"xpath": "//pericope"})
        assert all(isinstance(e, etree._Element) for e in result)

    def test_xpath_no_matches_returns_empty_list(self, xml_file):
        element = self._load_element(xml_file)
        result = apply_xml_xpath(element, {"xpath": "//nonexistent"})
        assert result == []


# ---------------------------------------------------------------------------
# Unit tests: apply_key_extract
# ---------------------------------------------------------------------------

class TestApplyKeyExtract:
    def test_no_key_returns_full_data(self):
        data = {"a": 1, "b": 2}
        assert apply_key_extract(data, {}) == {"a": 1, "b": 2}

    def test_top_level_key(self):
        assert apply_key_extract(JSON_CONTENT, {"key": "book"}) == "Mark"

    def test_nested_dot_path(self):
        result = apply_key_extract(JSON_CONTENT, {"key": "meta.language"})
        assert result == "en"

    def test_deeply_nested(self):
        result = apply_key_extract(JSON_CONTENT, {"key": "meta.version"})
        assert result == "1.0"

    def test_key_returning_list(self):
        result = apply_key_extract(JSON_CONTENT, {"key": "pericopes"})
        assert isinstance(result, list)
        assert len(result) == 2

    def test_missing_key_raises(self):
        with pytest.raises(KeyError, match="nonexistent"):
            apply_key_extract(JSON_CONTENT, {"key": "nonexistent"})

    def test_missing_nested_key_raises(self):
        with pytest.raises(KeyError, match="missing"):
            apply_key_extract(JSON_CONTENT, {"key": "meta.missing"})


# ---------------------------------------------------------------------------
# Integration tests via run_load_step
# ---------------------------------------------------------------------------

class TestLoadXmlWithXpath:
    def test_load_xml_no_xpath(self, xml_file):
        from lxml import etree
        step = {"name": "load", "type": "load_xml", "path": str(xml_file), "output": "doc"}
        ctx = {}
        run_load_step(step, ctx)
        assert isinstance(ctx["doc"], etree._Element)

    def test_load_xml_with_xpath(self, xml_file):
        step = {"name": "load", "type": "load_xml", "path": str(xml_file),
                "xpath": "//pericope", "output": "pericopes"}
        ctx = {}
        run_load_step(step, ctx)
        assert isinstance(ctx["pericopes"], list)
        assert len(ctx["pericopes"]) == 2

    def test_load_xml_xpath_text(self, xml_file):
        step = {"name": "load", "type": "load_xml", "path": str(xml_file),
                "xpath": "//verse/text()", "output": "texts", "output_format": "text"}
        ctx = {}
        run_load_step(step, ctx)
        assert isinstance(ctx["texts"], list)
        assert "And it came to pass" in ctx["texts"]


class TestLoadJsonWithKey:
    def test_load_json_no_key(self, json_file):
        step = {"name": "load", "type": "load_json", "path": str(json_file), "output": "data"}
        ctx = {}
        run_load_step(step, ctx)
        assert ctx["data"]["book"] == "Mark"

    def test_load_json_top_level_key(self, json_file):
        step = {"name": "load", "type": "load_json", "path": str(json_file),
                "key": "pericopes", "output": "pericopes"}
        ctx = {}
        run_load_step(step, ctx)
        assert isinstance(ctx["pericopes"], list)
        assert len(ctx["pericopes"]) == 2

    def test_load_json_nested_key(self, json_file):
        step = {"name": "load", "type": "load_json", "path": str(json_file),
                "key": "meta.language", "output": "lang"}
        ctx = {}
        run_load_step(step, ctx)
        assert ctx["lang"] == "en"


class TestLoadYamlWithKey:
    def test_load_yaml_with_key(self, yaml_file):
        step = {"name": "load", "type": "load_yaml", "path": str(yaml_file),
                "key": "book", "output": "title"}
        ctx = {}
        run_load_step(step, ctx)
        assert ctx["title"] == "Mark"

    def test_load_yaml_nested_key(self, yaml_file):
        step = {"name": "load", "type": "load_yaml", "path": str(yaml_file),
                "key": "meta.language", "output": "lang"}
        ctx = {}
        run_load_step(step, ctx)
        assert ctx["lang"] == "en"
