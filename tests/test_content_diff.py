"""
Tests for sp content diff command.
"""

import json
import pytest
from pathlib import Path

from llmflow.utils.content_diff import diff_content


class TestContentDiff:
    """Test content diff functionality."""

    @pytest.fixture
    def content_structure(self, tmp_path):
        """Create a test content structure with different versions."""
        # Create directories
        for stage in ["generated", "editing", "published"]:
            (tmp_path / stage).mkdir()

        # Create file in generated stage (original)
        gen_file = tmp_path / "generated" / "mark-1.md"
        gen_file.write_text("""# Mark 1:1-13 Leader's Guide

## Introduction
This is the generated content.

## Section 1
Original section content.
""", encoding="utf-8")

        # Create file in editing stage (modified)
        edit_file = tmp_path / "editing" / "mark-1.md"
        edit_file.write_text("""# Mark 1:1-13 Leader's Guide

## Introduction
This is the edited content with improvements.

## Section 1
Modified section content with more details.

## Section 2
Added new section.
""", encoding="utf-8")

        return tmp_path

    def test_diff_shows_differences(self, content_structure):
        """Test that diff shows actual differences."""
        result = diff_content(
            path="mark-1",
            from_stage="generated",
            to_stage="editing",
            content_root=content_structure
        )

        assert result["success"] is True
        assert result["from_stage"] == "generated"
        assert result["to_stage"] == "editing"
        assert result["has_differences"] is True

    def test_diff_identical_files(self, content_structure):
        """Test diff of identical files."""
        # Copy generated to published
        import shutil
        src = content_structure / "generated" / "mark-1.md"
        dst = content_structure / "published" / "mark-1.md"
        shutil.copy(src, dst)

        result = diff_content(
            path="mark-1",
            from_stage="generated",
            to_stage="published",
            content_root=content_structure
        )

        assert result["success"] is True
        assert result["has_differences"] is False

    def test_diff_file_missing_in_source(self, content_structure):
        """Test diff when file missing in source stage."""
        result = diff_content(
            path="mark-1",
            from_stage="published",  # File doesn't exist here
            to_stage="editing",
            content_root=content_structure
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_diff_file_missing_in_dest(self, content_structure):
        """Test diff when file missing in destination stage."""
        result = diff_content(
            path="mark-1",
            from_stage="generated",
            to_stage="published",  # File doesn't exist here
            content_root=content_structure
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_diff_nonexistent_file(self, content_structure):
        """Test diff for non-existent file."""
        result = diff_content(
            path="nonexistent",
            from_stage="generated",
            to_stage="editing",
            content_root=content_structure
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_diff_with_subdirectory(self, content_structure):
        """Test diff for file in subdirectory."""
        # Create files in subdirectory
        (content_structure / "generated" / "john").mkdir()
        (content_structure / "editing" / "john").mkdir()

        (content_structure / "generated" / "john" / "john-1.md").write_text(
            "# John 1\n\nOriginal.", encoding="utf-8"
        )
        (content_structure / "editing" / "john" / "john-1.md").write_text(
            "# John 1\n\nModified.", encoding="utf-8"
        )

        result = diff_content(
            path="john/john-1",
            from_stage="generated",
            to_stage="editing",
            content_root=content_structure
        )

        assert result["success"] is True
        assert result["has_differences"] is True

    def test_diff_invalid_stage(self, content_structure):
        """Test diff with invalid stage name."""
        result = diff_content(
            path="mark-1",
            from_stage="nonexistent",
            to_stage="editing",
            content_root=content_structure
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_diff_output_includes_paths(self, content_structure):
        """Test that diff result includes file paths."""
        result = diff_content(
            path="mark-1",
            from_stage="generated",
            to_stage="editing",
            content_root=content_structure
        )

        assert result["success"] is True
        assert "from_file" in result
        assert "to_file" in result
        assert "generated/mark-1.md" in result["from_file"]
        assert "editing/mark-1.md" in result["to_file"]


class TestDiffOutput:
    """Test diff output and formatting."""

    @pytest.fixture
    def diff_structure(self, tmp_path):
        """Create test structure for diff output testing."""
        for stage in ["generated", "editing"]:
            (tmp_path / stage).mkdir()

        (tmp_path / "generated" / "test.txt").write_text("line1\nline2\nline3\n", encoding="utf-8")
        (tmp_path / "editing" / "test.txt").write_text("line1\nmodified\nline3\nnew line\n", encoding="utf-8")

        return tmp_path

    def test_diff_outputs_to_stdout(self, diff_structure, capsys):
        """Test that diff outputs directly to stdout."""
        result = diff_content(
            path="test",
            from_stage="generated",
            to_stage="editing",
            content_root=diff_structure,
            output_to_console=True
        )

        assert result["success"] is True

        # Capture output
        captured = capsys.readouterr()
        output = captured.out

        # Should contain diff markers
        assert "---" in output or "+++" in output or "@@ " in output
