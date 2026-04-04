"""
Tests for sp content list command.
"""

import json
import pytest
from pathlib import Path

from llmflow.utils.content_list import list_content, format_content_list


class TestContentList:
    """Test content listing."""

    @pytest.fixture
    def content_structure(self, tmp_path):
        """Create a test content structure."""
        # Create directories
        for stage in ["generated", "editing", "published"]:
            (tmp_path / stage).mkdir()

        # Create multiple files in generated
        for i in range(3):
            file = tmp_path / "generated" / f"mark-{i+1}.md"
            file.write_text(f"# Mark {i+1}\n\nContent {i+1}.", encoding="utf-8")

        # Create files with subdirectories
        (tmp_path / "generated" / "john").mkdir()
        (tmp_path / "generated" / "john" / "john-1.md").write_text("# John 1", encoding="utf-8")

        # Create file in editing
        (tmp_path / "editing" / "mark-1.md").write_text("# Mark 1 - Edited", encoding="utf-8")

        # Create metadata for editing
        metadata = {
            "mark-1": {
                "editor": "jane@example.com",
                "last_modified": "2026-04-03T11:30:00"
            }
        }
        (tmp_path / "editing" / ".metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        return tmp_path

    def test_list_stage_with_files(self, content_structure):
        """Test listing files in stage."""
        result = list_content(
            stage="generated",
            content_root=content_structure
        )

        assert result["success"] is True
        assert result["stage"] == "generated"
        assert len(result["files"]) >= 3

        # Check files are listed
        paths = [f["path"] for f in result["files"]]
        assert "mark-1.md" in paths
        assert "mark-2.md" in paths
        assert "mark-3.md" in paths

    def test_list_empty_stage(self, content_structure):
        """Test listing empty stage."""
        result = list_content(
            stage="published",
            content_root=content_structure
        )

        assert result["success"] is True
        assert result["stage"] == "published"
        assert len(result["files"]) == 0

    def test_list_with_subdirectories(self, content_structure):
        """Test listing includes subdirectories."""
        result = list_content(
            stage="generated",
            content_root=content_structure
        )

        assert result["success"] is True

        # Find file in subdirectory
        john_file = next((f for f in result["files"] if "john" in f["path"]), None)
        assert john_file is not None
        assert john_file["path"] == "john/john-1.md"

    def test_list_with_metadata(self, content_structure):
        """Test listing includes metadata when requested."""
        result = list_content(
            stage="editing",
            content_root=content_structure,
            with_metadata=True
        )

        assert result["success"] is True

        # Find mark-1 file
        mark_file = next((f for f in result["files"] if "mark-1" in f["path"]), None)
        assert mark_file is not None

        # Check metadata is included
        metadata = mark_file.get("metadata")
        assert metadata is not None
        assert metadata["editor"] == "jane@example.com"

    def test_list_without_metadata(self, content_structure):
        """Test listing excludes metadata by default."""
        result = list_content(
            stage="editing",
            content_root=content_structure,
            with_metadata=False
        )

        assert result["success"] is True

        # Check metadata is not included
        for file_info in result["files"]:
            assert "metadata" not in file_info or file_info["metadata"] is None

    def test_list_nonexistent_stage(self, content_structure):
        """Test listing non-existent stage."""
        result = list_content(
            stage="nonexistent",
            content_root=content_structure
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_list_shows_file_stats(self, content_structure):
        """Test that file stats are included."""
        result = list_content(
            stage="generated",
            content_root=content_structure
        )

        assert result["success"] is True

        # Check first file has stats
        first_file = result["files"][0]
        assert "size" in first_file
        assert "modified" in first_file
        assert first_file["size"] > 0

    def test_summary_stats(self, content_structure):
        """Test summary statistics."""
        result = list_content(
            stage="generated",
            content_root=content_structure
        )

        assert result["success"] is True

        # Check summary
        assert "summary" in result
        summary = result["summary"]
        assert summary["total_files"] >= 4
        assert summary["total_size"] > 0


class TestContentListFormatting:
    """Test list output formatting."""

    @pytest.fixture
    def sample_list(self):
        """Sample list result."""
        return {
            "success": True,
            "stage": "editing",
            "files": [
                {
                    "path": "mark-1.md",
                    "size": 1024,
                    "modified": "2026-04-03T10:00:00",
                    "metadata": {
                        "editor": "jane@example.com"
                    }
                },
                {
                    "path": "mark-2.md",
                    "size": 2048,
                    "modified": "2026-04-03T11:00:00"
                }
            ],
            "summary": {
                "total_files": 2,
                "total_size": 3072
            }
        }

    def test_format_list_human_readable(self, sample_list):
        """Test formatting list for human consumption."""
        output = format_content_list(sample_list, json_output=False)

        assert "editing" in output
        assert "mark-1.md" in output
        assert "mark-2.md" in output
        assert "2 files" in output.lower() or "total: 2" in output.lower()

    def test_format_list_json(self, sample_list):
        """Test formatting list as JSON."""
        output = format_content_list(sample_list, json_output=True)

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["stage"] == "editing"
        assert len(parsed["files"]) == 2
