"""Tests for src/llmflow/plugins/xml_entry_to_base_json.py."""

import pytest
from lxml import etree

from llmflow.plugins.xml_entry_to_base_json import xml_entry_to_base_json, run


# Minimal TEI entry with one sense containing a foreign word and gloss
SIMPLE_ENTRY = """<entry xmlns="http://www.tei-c.org/ns/1.0" key="test.001">
  <sense n="1">
    <foreign>λόγος</foreign>
    <gloss>word</gloss>
  </sense>
</entry>"""

ENTRY_NO_NS = """<entry key="nons.001">
  <sense n="1">
    <foreign>word</foreign>
    <gloss>translation</gloss>
  </sense>
</entry>"""

ENTRY_NO_KEY = """<entry xmlns="http://www.tei-c.org/ns/1.0">
  <sense n="1">
    <foreign>λόγος</foreign>
    <gloss>word</gloss>
  </sense>
</entry>"""

MULTI_SENSE_ENTRY = """<entry xmlns="http://www.tei-c.org/ns/1.0" key="multi.001">
  <sense n="1">
    <foreign>πιστεύω</foreign>
    <gloss>believe</gloss>
  </sense>
  <sense n="2">
    <foreign>πιστεύω</foreign>
    <gloss>trust</gloss>
  </sense>
</entry>"""


class TestXmlEntryToBaseJson:

    def test_returns_dict(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        assert isinstance(result, dict)

    def test_entry_key_is_preserved(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        assert result["lemma"] == "test.001"

    def test_missing_key_is_none(self):
        result = xml_entry_to_base_json(ENTRY_NO_KEY)
        assert result["lemma"] is None

    def test_segments_list_present(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        assert "rawEntry" in result
        assert "segments" in result["rawEntry"]
        assert isinstance(result["rawEntry"]["segments"], list)

    def test_foreign_segment_captured(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        segs = result["rawEntry"]["segments"]
        foreign_segs = [s for s in segs if s["type"] == "foreign"]
        assert len(foreign_segs) >= 1
        assert foreign_segs[0]["text"] == "λόγος"

    def test_gloss_segment_captured(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        segs = result["rawEntry"]["segments"]
        gloss_segs = [s for s in segs if s["type"] == "gloss"]
        assert len(gloss_segs) >= 1
        assert gloss_segs[0]["text"] == "word"

    def test_sense_path_set_on_segments(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        segs = result["rawEntry"]["segments"]
        for seg in segs:
            assert "sensePath" in seg

    def test_multi_sense_produces_multiple_foreign_segments(self):
        result = xml_entry_to_base_json(MULTI_SENSE_ENTRY)
        segs = result["rawEntry"]["segments"]
        foreign_segs = [s for s in segs if s["type"] == "foreign"]
        assert len(foreign_segs) == 2

    def test_segment_indices_are_sequential(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        segs = result["rawEntry"]["segments"]
        indices = [s["index"] for s in segs]
        assert indices == list(range(len(indices)))

    def test_xml_snippet_stored(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        assert "xmlSnippet" in result["rawEntry"]
        assert "λόγος" in result["rawEntry"]["xmlSnippet"]

    def test_senses_list_present(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        assert "senses" in result
        assert isinstance(result["senses"], list)

    def test_top_level_keys_present(self):
        result = xml_entry_to_base_json(SIMPLE_ENTRY)
        for key in ("lemma", "rawEntry", "senses", "forms", "warnings", "notes"):
            assert key in result, f"Missing key: {key}"

    def test_entry_without_namespace(self):
        """Entries without TEI namespace are handled gracefully."""
        result = xml_entry_to_base_json(ENTRY_NO_NS)
        assert result["lemma"] == "nons.001"

    def test_invalid_xml_raises(self):
        with pytest.raises(etree.XMLSyntaxError):
            xml_entry_to_base_json("<broken xml")

    def test_entry_with_an_encoding_declaration_parses(self):
        """lxml rejects a str carrying an encoding declaration, so the plugin parses bytes."""
        declared = '<?xml version="1.0" encoding="utf-8"?>\n' + SIMPLE_ENTRY
        assert xml_entry_to_base_json(declared)["lemma"] == "test.001"


class TestRunWrapper:

    def test_run_accepts_kwargs(self):
        result = run(entry_xml=SIMPLE_ENTRY)
        assert isinstance(result, dict)
        assert result["lemma"] == "test.001"

    def test_run_returns_segments(self):
        result = run(entry_xml=SIMPLE_ENTRY)
        assert len(result["rawEntry"]["segments"]) > 0
