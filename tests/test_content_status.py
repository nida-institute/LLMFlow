"""
Tests for sp content status command.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from llmflow.utils.content_status import get_content_status


class TestContentStatus:
    """Test content status reporting."""

    @pytest.fixture
    def content_structure(self, tmp_path):
        """Create a test content structure."""
        # Create directories
        for stage in ["generated", "editing", "published"]:
            (tmp_path / stage).mkdir()

        # Create file in generated stage
        gen_file = tmp_path / "generated" / "mark-1-1-13.md"
        gen_file.write_text("# Mark 1:1-13 Leader's Guide\n\nGenerated content.", encoding="utf-8")

        # Create file in editing stage (copied from generated)
        edit_file = tmp_path / "editing" / "mark-1-1-13.md"
        edit_file.write_text("# Mark 1:1-13 Leader's Guide\n\nEdited content.", encoding="utf-8")

        # Create metadata for editing stage
        metadata = {
            "mark-1-1-13": {
                "source_stage": "generated",
                "transitioned_at": "2026-04-03T10:00:00",
                "transitioned_by": "jane",
                "editor": "jane@example.com",
                "last_modified": "2026-04-03T11:30:00"
            }
        }
        (tmp_path / "editing" / ".metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        return tmp_path

    def test_file_in_single_stage(self, content_structure):
        """Test status for file in only one stage."""
        result = get_content_status(
            path="mark-1-1-13",
            content_root=content_structure
        )

        assert result["success"] is True
        assert result["path"] == "mark-1-1-13"
        assert len(result["stages"]) >= 1

        # Should find file in generated
        gen_stage = next((s for s in result["stages"] if s["name"] == "generated"), None)
        assert gen_stage is not None
        assert gen_stage["exists"] is True
        assert gen_stage["file_path"].endswith("generated/mark-1-1-13.md")

    def test_file_in_multiple_stages(self, content_structure):
        """Test status for file present in multiple stages."""
        result = get_content_status(
            path="mark-1-1-13",
            content_root=content_structure
        )

        assert result["success"] is True

        # Should find file in both generated and editing
        stage_names = [s["name"] for s in result["stages"] if s["exists"]]
        assert "generated" in stage_names
        assert "editing" in stage_names

    def test_file_not_found(self, content_structure):
        """Test status for non-existent file."""
        result = get_content_status(
            path="nonexistent-file",
            content_root=content_structure
        )

        assert result["success"] is True
        assert result["path"] == "nonexistent-file"

        # Should show all stages but none exist
        all_exist = all(s["exists"] for s in result["stages"])
        assert all_exist is False

    def test_metadata_reported(self, content_structure):
        """Test that metadata is reported correctly."""
        result = get_content_status(
            path="mark-1-1-13",
            content_root=content_structure
        )

        # Find editing stage
        edit_stage = next((s for s in result["stages"] if s["name"] == "editing"), None)
        assert edit_stage is not None
        assert edit_stage["exists"] is True

        # Check metadata
        metadata = edit_stage.get("metadata")
        assert metadata is not None
        assert metadata["editor"] == "jane@example.com"
        assert metadata["source_stage"] == "generated"

    def test_authoritative_stage_identified(self, content_structure):
        """Test that authoritative stage is correctly identified."""
        result = get_content_status(
            path="mark-1-1-13",
            content_root=content_structure
        )

        # Editing should be authoritative (most advanced stage with file)
        assert result.get("authoritative_stage") == "editing"

    def test_next_actions_suggested(self, content_structure):
        """Test that next actions are suggested."""
        result = get_content_status(
            path="mark-1-1-13",
            content_root=content_structure
        )

        # Should suggest next possible transitions
        actions = result.get("next_actions", [])
        assert len(actions) > 0

        # Should suggest editing -> published transition
        published_action = next((a for a in actions if a.get("to") == "published"), None)
        assert published_action is not None
        assert published_action["from"] == "editing"

    def test_file_with_subdirectory(self, content_structure):
        """Test status for file in subdirectory."""
        # Create subdirectory structure
        (content_structure / "generated" / "mark").mkdir()
        (content_structure / "generated" / "mark" / "mark-1-14-20.md").write_text(
            "# Mark 1:14-20", encoding="utf-8"
        )

        result = get_content_status(
            path="mark/mark-1-14-20",
            content_root=content_structure
        )

        assert result["success"] is True
        assert result["path"] == "mark/mark-1-14-20"

        gen_stage = next((s for s in result["stages"] if s["name"] == "generated"), None)
        assert gen_stage is not None
        assert gen_stage["exists"] is True
        assert "mark/mark-1-14-20.md" in gen_stage["file_path"]

    def test_custom_config_path(self, content_structure, tmp_path):
        """Test using custom config file."""
        # Create custom config
        config_file = tmp_path / "custom-config.yaml"
        config_file.write_text("""
stages:
  - name: draft
    file_permissions: "644"
  - name: review
    file_permissions: "644"

transitions:
  - from: draft
    to: review
    action: copy
""", encoding="utf-8")

        # Create file in draft stage
        (content_structure / "draft").mkdir()
        (content_structure / "draft" / "test.md").write_text("Test", encoding="utf-8")

        result = get_content_status(
            path="test",
            content_root=content_structure,
            config_path=config_file
        )

        assert result["success"] is True

        # Should use custom stages
        stage_names = [s["name"] for s in result["stages"]]
        assert "draft" in stage_names
        assert "review" in stage_names


class TestStatusFormatting:
    """Test status output formatting."""

    @pytest.fixture
    def sample_status(self):
        """Sample status result."""
        return {
            "success": True,
            "path": "mark-1-1-13",
            "stages": [
                {
                    "name": "generated",
                    "exists": True,
                    "file_path": "/content/generated/mark-1-1-13.md",
                    "file_size": 1024,
                    "modified": "2026-04-03T09:00:00"
                },
                {
                    "name": "editing",
                    "exists": True,
                    "file_path": "/content/editing/mark-1-1-13.md",
                    "file_size": 1150,
                    "modified": "2026-04-03T11:30:00",
                    "metadata": {
                        "editor": "jane@example.com",
                        "source_stage": "generated",
                        "last_modified": "2026-04-03T11:30:00"
                    }
                },
                {
                    "name": "published",
                    "exists": False
                }
            ],
            "authoritative_stage": "editing",
            "next_actions": [
                {
                    "from": "editing",
                    "to": "published",
                    "action": "move",
                    "command": "sp transition editing published mark-1-1-13"
                }
            ]
        }

    def test_format_status_human_readable(self, sample_status):
        """Test formatting status for human consumption."""
        from llmflow.utils.content_status import format_status

        output = format_status(sample_status, json_output=False)

        assert "mark-1-1-13" in output
        assert "generated" in output
        assert "editing" in output
        assert "published" in output
        assert "jane@example.com" in output
        assert "editing → published" in output or "editing -> published" in output

    def test_format_status_json(self, sample_status):
        """Test formatting status as JSON."""
        from llmflow.utils.content_status import format_status

        output = format_status(sample_status, json_output=True)

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["path"] == "mark-1-1-13"
        assert parsed["authoritative_stage"] == "editing"
