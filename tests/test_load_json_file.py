"""
Test the load_json_file function from llmflow.utils.data.

This function is used by pipelines to load JSON data from files,
such as scene lists or other structured data.
"""
import json
import sys
import uuid
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llmflow.utils.data import load_json_file


class TestLoadJsonFile:
    """Test cases for load_json_file function"""

    def test_load_simple_dict(self, tmp_path):
        """Test loading a simple JSON dictionary"""
        test_data = {"name": "Test", "value": 42, "active": True}
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(test_data, indent=2))

        result = load_json_file(str(test_file))
        assert result == test_data
        assert isinstance(result, dict)

    def test_load_list(self, tmp_path):
        """Test loading a JSON array"""
        test_data = [
            {"id": 1, "name": "First"},
            {"id": 2, "name": "Second"},
            {"id": 3, "name": "Third"},
        ]
        test_file = tmp_path / "list.json"
        test_file.write_text(json.dumps(test_data, indent=2))

        result = load_json_file(str(test_file))
        assert result == test_data
        assert isinstance(result, list)
        assert len(result) == 3

    def test_load_nested_structure(self, tmp_path):
        """Test loading a complex nested JSON structure"""
        test_data = {
            "scenes": [
                {
                    "Scene": 1,
                    "Citation": "Psalm 23:1",
                    "Title": "The Lord as Shepherd",
                    "Text": {
                        "WLC": "יְהוָה רֹעִי לֹא אֶחְסָר",
                        "BSB": "The LORD is my shepherd; I shall not want.",
                    },
                }
            ],
            "metadata": {"passage": "Psalm 23", "total_scenes": 1},
        }
        test_file = tmp_path / "complex.json"
        test_file.write_text(json.dumps(test_data, indent=2))

        result = load_json_file(str(test_file))
        assert result == test_data
        assert len(result["scenes"]) == 1
        assert result["scenes"][0]["Scene"] == 1
        assert "WLC" in result["scenes"][0]["Text"]

    def test_load_empty_dict(self, tmp_path):
        """Test loading an empty JSON object"""
        test_file = tmp_path / "empty.json"
        test_file.write_text("{}")

        result = load_json_file(str(test_file))
        assert result == {}
        assert isinstance(result, dict)

    def test_load_empty_list(self, tmp_path):
        """Test loading an empty JSON array"""
        test_file = tmp_path / "empty_list.json"
        test_file.write_text("[]")

        result = load_json_file(str(test_file))
        assert result == []
        assert isinstance(result, list)

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent files"""
        nonexistent_file = tmp_path / "does_not_exist.json"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_json_file(str(nonexistent_file))

        assert "JSON file not found" in str(exc_info.value)
        assert str(nonexistent_file) in str(exc_info.value)

    def test_invalid_json_syntax(self, tmp_path):
        """Test that JSONDecodeError is raised for malformed JSON"""
        test_file = tmp_path / "invalid.json"
        test_file.write_text('{"name": "Test", invalid syntax}')

        with pytest.raises(json.JSONDecodeError):
            load_json_file(str(test_file))

    def test_load_with_unicode(self, tmp_path):
        """Test loading JSON with Unicode characters (Hebrew, Greek, etc.)"""
        test_data = {
            "hebrew": "יְהוָה רֹעִי לֹא אֶחְסָר",
            "greek": "Κύριος ποιμαίνει με",
            "chinese": "耶和华是我的牧者",
        }
        test_file = tmp_path / "unicode.json"
        test_file.write_text(json.dumps(test_data, ensure_ascii=False, indent=2))

        result = load_json_file(str(test_file))
        assert result == test_data
        assert result["hebrew"] == "יְהוָה רֹעִי לֹא אֶחְסָר"
        assert result["greek"] == "Κύριος ποιμαίνει με"

    def test_load_with_pathlib_path(self, tmp_path):
        """Test that the function works with pathlib.Path objects"""
        test_data = {"using": "pathlib", "works": True}
        test_file = tmp_path / "pathlib_test.json"
        test_file.write_text(json.dumps(test_data))

        # Pass a Path object instead of string
        result = load_json_file(test_file)
        assert result == test_data

    def test_load_scene_list_format(self, tmp_path):
        """Test loading a scene list in the StoryFlow format"""
        test_data = [
            {
                "Scene": 1,
                "Citation": "Psalm 23:1",
                "Title": "The Lord as Shepherd",
                "Text": {
                    "WLC": "יְהוָה רֹעִי לֹא אֶחְסָר",
                    "BSB": "The LORD is my shepherd; I shall not want.",
                },
            },
            {
                "Scene": 2,
                "Citation": "Psalm 23:2-3",
                "Title": "Comfort and Restoration",
                "Text": {
                    "WLC": "בִּנְאוֹת דֶּשֶׁא יַרְבִּיצֵנִי",
                    "BSB": "He makes me lie down in green pastures.",
                },
            },
        ]
        test_file = tmp_path / "Psalm_23.json"
        test_file.write_text(json.dumps(test_data, ensure_ascii=False, indent=2))

        result = load_json_file(str(test_file))
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["Scene"] == 1
        assert result[1]["Scene"] == 2
        assert "WLC" in result[0]["Text"]
        assert "BSB" in result[1]["Text"]

    def test_load_with_numeric_values(self, tmp_path):
        """Test loading JSON with various numeric types"""
        test_data = {
            "integer": 42,
            "float": 3.14159,
            "negative": -17,
            "zero": 0,
            "large": 1234567890,
        }
        test_file = tmp_path / "numbers.json"
        test_file.write_text(json.dumps(test_data))

        result = load_json_file(str(test_file))
        assert result == test_data
        assert isinstance(result["integer"], int)
        assert isinstance(result["float"], float)

    def test_load_with_boolean_and_null(self, tmp_path):
        """Test loading JSON with boolean and null values"""
        test_data = {
            "is_active": True,
            "is_deleted": False,
            "optional_field": None,
        }
        test_file = tmp_path / "special_values.json"
        test_file.write_text(json.dumps(test_data))

        result = load_json_file(str(test_file))
        assert result == test_data
        assert result["is_active"] is True
        assert result["is_deleted"] is False
        assert result["optional_field"] is None

    def test_load_maintains_order(self, tmp_path):
        """Test that dictionary key order is preserved"""
        test_data = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
        }
        test_file = tmp_path / "ordered.json"
        test_file.write_text(json.dumps(test_data))

        result = load_json_file(str(test_file))
        keys = list(result.keys())
        assert keys == ["first", "second", "third", "fourth", "fifth"]

    def test_concurrent_file_access(self, tmp_path):
        """Test loading the same file multiple times (simulating pipeline re-use)"""
        test_data = {"shared": "resource", "count": 0}
        test_file = tmp_path / "shared.json"
        test_file.write_text(json.dumps(test_data))

        # Load the same file multiple times
        result1 = load_json_file(str(test_file))
        result2 = load_json_file(str(test_file))
        result3 = load_json_file(str(test_file))

        assert result1 == test_data
        assert result2 == test_data
        assert result3 == test_data
        # Ensure they're independent copies
        result1["count"] = 1
        assert result2["count"] == 0

    def test_uuid_filename_cleanup_pattern(self, tmp_path):
        """Test loading JSON with UUID-based filenames (common pattern in tests)"""
        # Use UUID for unique filename to avoid conflicts
        unique_id = uuid.uuid4()
        test_data = {"test_id": str(unique_id), "data": "test"}
        test_file = tmp_path / f"{unique_id}.json"

        try:
            test_file.write_text(json.dumps(test_data))
            result = load_json_file(str(test_file))
            assert result["test_id"] == str(unique_id)
        finally:
            # Clean up UUID file
            if test_file.exists():
                test_file.unlink()
