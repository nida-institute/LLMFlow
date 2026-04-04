"""
Tests for content lifecycle transition command.

Tests the sp transition command that moves/copies files between stages.
"""

import pytest
from pathlib import Path
import os
import json

from llmflow.utils.content_stages_loader import ContentStagesConfigLoader


@pytest.fixture
def test_config(tmp_path):
    """Create a test content-stages.yaml configuration."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    config_file = config_dir / "content-stages.yaml"
    config_file.write_text("""
stages:
  - name: draft
    protected: false
    file_permissions: "644"
    git_tracked: false
    auto_create_metadata: false

  - name: review
    protected: true
    file_permissions: "644"
    git_tracked: true
    auto_create_metadata: true

  - name: final
    protected: true
    immutable: true
    file_permissions: "444"
    git_tracked: true
    auto_create_metadata: true

transitions:
  - from: draft
    to: review
    action: copy
    source_file_permissions: "444"
    destination_file_permissions: "644"
    copy_metadata: false
    metadata_fields_to_set:
      transitioned_at: "{timestamp}"
      source_stage: draft
    git_add_destination: true
    requirements: []

  - from: review
    to: final
    action: move
    destination_file_permissions: "444"
    copy_metadata: true
    git_add_destination: true
    git_remove_source: true
    requirements:
      - type: metadata_present
        fields: [reviewer]
        message: "Reviewer field required"
""", encoding="utf-8")

    return config_file


@pytest.fixture
def content_structure(tmp_path):
    """Create content directory structure with test files."""
    content_dir = tmp_path / "content"

    # Create stage directories
    draft_dir = content_dir / "draft"
    review_dir = content_dir / "review"
    final_dir = content_dir / "final"

    draft_dir.mkdir(parents=True)
    review_dir.mkdir(parents=True)
    final_dir.mkdir(parents=True)

    # Create test file in draft
    test_file = draft_dir / "test-doc.md"
    test_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

    test_json = draft_dir / "test-doc.json"
    test_json.write_text('{"title": "Test Document"}', encoding="utf-8")

    return {
        "content_dir": content_dir,
        "draft_dir": draft_dir,
        "review_dir": review_dir,
        "final_dir": final_dir,
        "test_file": test_file,
        "test_json": test_json,
    }


class TestTransitionBasics:
    """Test basic transition functionality."""

    def test_copy_transition_creates_files(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that copy transition creates files in destination."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Perform transition: draft → review (copy)
        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"]
        )

        assert result["success"]

        # Source files should still exist
        assert (content_structure["draft_dir"] / "test-doc.md").exists()
        assert (content_structure["draft_dir"] / "test-doc.json").exists()

        # Destination files should exist
        assert (content_structure["review_dir"] / "test-doc.md").exists()
        assert (content_structure["review_dir"] / "test-doc.json").exists()

        # Verify content was copied
        dest_content = (content_structure["review_dir"] / "test-doc.md").read_text()
        assert "This is a test" in dest_content

    def test_move_transition_removes_source(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that move transition removes source files."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Put files in review first
        review_file = content_structure["review_dir"] / "test-doc.md"
        review_file.write_text("# Test Document\n\nReviewed.", encoding="utf-8")

        review_json = content_structure["review_dir"] / "test-doc.json"
        review_json.write_text('{"title": "Test", "reviewer": "Jane"}', encoding="utf-8")

        # Create metadata so requirement passes
        metadata_file = content_structure["review_dir"] / ".metadata.json"
        metadata_file.write_text(json.dumps({
            "test-doc": {"reviewer": "Jane"}
        }), encoding="utf-8")

        # Perform transition: review → final (move)
        result = transition_content(
            from_stage="review",
            to_stage="final",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"]
        )

        assert result["success"]

        # Source files should NOT exist
        assert not (content_structure["review_dir"] / "test-doc.md").exists()
        assert not (content_structure["review_dir"] / "test-doc.json").exists()

        # Destination files should exist
        assert (content_structure["final_dir"] / "test-doc.md").exists()
        assert (content_structure["final_dir"] / "test-doc.json").exists()


class TestFilePermissions:
    """Test file permission management during transitions."""

    def test_source_permissions_changed_on_copy(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that source file permissions change after copy."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        source_file = content_structure["draft_dir"] / "test-doc.md"

        # Verify initial permissions (should be default)
        initial_mode = os.stat(source_file).st_mode & 0o777

        # Perform transition
        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"]
        )

        assert result["success"]

        # Source should now be read-only (444)
        source_mode = os.stat(source_file).st_mode & 0o777
        assert source_mode == 0o444

    def test_destination_permissions_set_correctly(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that destination file permissions are set correctly."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"]
        )

        assert result["success"]

        # Destination should be writable (644)
        dest_file = content_structure["review_dir"] / "test-doc.md"
        dest_mode = os.stat(dest_file).st_mode & 0o777
        assert dest_mode == 0o644


class TestMetadata:
    """Test metadata handling during transitions."""

    def test_metadata_created_when_auto_create_enabled(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that metadata is created in stages with auto_create_metadata: true."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"]
        )

        assert result["success"]

        # Metadata file should exist in review
        metadata_file = content_structure["review_dir"] / ".metadata.json"
        assert metadata_file.exists()

        # Verify metadata content
        metadata = json.loads(metadata_file.read_text())
        assert "test-doc" in metadata
        assert metadata["test-doc"]["source_stage"] == "draft"
        assert "transitioned_at" in metadata["test-doc"]

    def test_metadata_not_created_when_disabled(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that metadata is not created when auto_create_metadata: false."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # draft has auto_create_metadata: false
        # So when we create files there, no metadata should be created

        # Metadata file should not exist in draft
        metadata_file = content_structure["draft_dir"] / ".metadata.json"
        assert not metadata_file.exists()


class TestRequirements:
    """Test requirement validation during transitions."""

    def test_transition_fails_when_requirement_not_met(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that transition fails when requirement is not satisfied."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Put files in review without required metadata
        review_file = content_structure["review_dir"] / "test-doc.md"
        review_file.write_text("# Test Document", encoding="utf-8")

        review_json = content_structure["review_dir"] / "test-doc.json"
        review_json.write_text('{"title": "Test"}', encoding="utf-8")  # Missing reviewer

        # Attempt transition: review → final (should fail - reviewer field missing)
        result = transition_content(
            from_stage="review",
            to_stage="final",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"]
        )

        assert not result["success"]
        assert "Reviewer field required" in result["error"]

    def test_transition_succeeds_when_requirement_met(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that transition succeeds when all requirements are satisfied."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Put files in review WITH required metadata
        review_file = content_structure["review_dir"] / "test-doc.md"
        review_file.write_text("# Test Document", encoding="utf-8")

        review_json = content_structure["review_dir"] / "test-doc.json"
        review_json.write_text('{"title": "Test"}', encoding="utf-8")

        # Create metadata with reviewer field
        metadata_file = content_structure["review_dir"] / ".metadata.json"
        metadata_file.write_text(json.dumps({
            "test-doc": {"reviewer": "Jane"}
        }), encoding="utf-8")

        # Attempt transition: review → final (should succeed)
        result = transition_content(
            from_stage="review",
            to_stage="final",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"]
        )

        assert result["success"]


class TestTransitionValidation:
    """Test validation of transition requests."""

    def test_undefined_transition_rejected(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that undefined transitions are rejected."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Attempt undefined transition: draft → final (not in config)
        result = transition_content(
            from_stage="draft",
            to_stage="final",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"]
        )

        assert not result["success"]
        assert "not allowed" in result["error"].lower()

    def test_nonexistent_file_rejected(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that transition of nonexistent file is rejected."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Attempt transition of nonexistent file
        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="nonexistent",
            config_path=test_config,
            content_root=content_structure["content_dir"]
        )

        assert not result["success"]
        assert "no files found" in result["error"].lower()
