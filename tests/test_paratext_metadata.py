"""Tests for Paratext project metadata loading."""

import json
import pytest
from pathlib import Path
from lxml import etree

from llmflow.utils.data import load_project_file, xpath_text


# Test fixtures path
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "paratext"


class TestLoadProjectFile:
    """Tests for load_project_file() function."""

    def test_load_json_returns_dict(self):
        """Load metadata.json returns parsed dict."""
        result = load_project_file(
            base_dir=str(FIXTURES_DIR),
            project_name="TestProject",
            file="metadata.json"
        )

        assert isinstance(result, dict)
        assert result["identification"]["name"]["en"] == "Test Project Full Name"
        assert result["languages"][0]["tag"] == "tst"
        assert result["languages"][0]["name"]["en"] == "Test Language"

    def test_load_xml_returns_element(self):
        """Load Settings.xml returns lxml Element."""
        result = load_project_file(
            base_dir=str(FIXTURES_DIR),
            project_name="TestProject",
            file="Settings.xml"
        )

        assert isinstance(result, etree._Element)
        assert result.tag == "ScriptureText"

        # Verify we can query it
        lang = result.find(".//LanguageName")
        assert lang is not None
        assert lang.text == "Test Language"

    def test_project_not_found_raises(self):
        """FileNotFoundError when project directory doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_project_file(
                base_dir=str(FIXTURES_DIR),
                project_name="NonExistentProject",
                file="Settings.xml"
            )

        assert "NonExistentProject" in str(exc_info.value)

    def test_file_not_found_raises(self):
        """FileNotFoundError when file doesn't exist in project."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_project_file(
                base_dir=str(FIXTURES_DIR),
                project_name="TestProject",
                file="NonExistent.xml"
            )

        assert "NonExistent.xml" in str(exc_info.value)

    def test_invalid_extension_raises(self):
        """ValueError for unsupported file extension."""
        # Create a .txt file to test with
        test_file = FIXTURES_DIR / "TestProject" / "test.txt"
        test_file.write_text("test content")

        try:
            with pytest.raises(ValueError) as exc_info:
                load_project_file(
                    base_dir=str(FIXTURES_DIR),
                    project_name="TestProject",
                    file="test.txt"
                )

            assert ".txt" in str(exc_info.value)
            assert "json" in str(exc_info.value).lower() or "xml" in str(exc_info.value).lower()
        finally:
            test_file.unlink()


class TestXPathText:
    """Tests for xpath_text() helper function."""

    def test_extract_text_from_element(self):
        """Extract text content using XPath."""
        element = load_project_file(
            base_dir=str(FIXTURES_DIR),
            project_name="TestProject",
            file="Settings.xml"
        )

        language = xpath_text(element, ".//LanguageName/text()")
        assert language == "Test Language"

        iso = xpath_text(element, ".//LanguageIsoCode/text()")
        assert iso == "tst"

        full_name = xpath_text(element, ".//FullName/text()")
        assert full_name == "Test Project Full Name"

    def test_missing_path_returns_none(self):
        """Return None when XPath finds no match."""
        element = load_project_file(
            base_dir=str(FIXTURES_DIR),
            project_name="TestProject",
            file="Settings.xml"
        )

        result = xpath_text(element, ".//NonExistentField/text()")
        assert result is None

    def test_multiple_matches_returns_first(self):
        """When XPath matches multiple nodes, return first."""
        # Create XML with multiple matching elements
        xml_str = """
        <root>
            <item>First</item>
            <item>Second</item>
            <item>Third</item>
        </root>
        """
        element = etree.fromstring(xml_str.encode('utf-8'))

        result = xpath_text(element, ".//item/text()")
        assert result == "First"

    def test_absolute_path(self):
        """XPath with absolute path works."""
        element = load_project_file(
            base_dir=str(FIXTURES_DIR),
            project_name="TestProject",
            file="Settings.xml"
        )

        language = xpath_text(element, "/ScriptureText/LanguageName/text()")
        assert language == "Test Language"
