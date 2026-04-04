"""
Tests for sentinel file and permission management.

Tests the .sp-permissions sentinel file that detects git clones
and automatically reapplies file permissions.
"""

import pytest
from pathlib import Path
import os
import json


@pytest.fixture
def test_config(tmp_path):
    """Create a test content-stages.yaml configuration."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    config_file = config_dir / "content-stages.yaml"
    config_file.write_text(
        """
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
""",
        encoding="utf-8",
    )

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


class TestSentinelFile:
    """Test sentinel file creation and detection."""

    def test_sentinel_created_on_first_run(self, tmp_path, test_config, content_structure, monkeypatch):
        """Test that sentinel file is created on first transition."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Sentinel should not exist yet
        sentinel = content_structure["content_dir"] / ".sp-permissions"
        assert not sentinel.exists()

        # Perform transition
        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"],
        )

        assert result["success"]

        # Sentinel should now exist
        assert sentinel.exists()

        # Verify contents
        sentinel_data = json.loads(sentinel.read_text())
        assert sentinel_data == {"_marker": "sp"}

        # Sentinel should be read-only
        sentinel_mode = os.stat(sentinel).st_mode & 0o777
        assert sentinel_mode == 0o444

    def test_sentinel_not_modified_on_subsequent_runs(
        self, tmp_path, test_config, content_structure, monkeypatch
    ):
        """Test that sentinel is never modified after creation."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        sentinel = content_structure["content_dir"] / ".sp-permissions"

        # First transition - creates sentinel
        transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"],
        )

        original_mtime = sentinel.stat().st_mtime
        original_content = sentinel.read_text()

        # Create another test file in draft
        test_file2 = content_structure["draft_dir"] / "test-doc2.md"
        test_file2.write_text("# Test 2", encoding="utf-8")

        # Second transition
        transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc2",
            config_path=test_config,
            content_root=content_structure["content_dir"],
        )

        # Sentinel should NOT have been modified
        assert sentinel.read_text() == original_content
        # Note: mtime might change due to permission reapply, so we check content only


class TestPermissionReapplication:
    """Test automatic permission reapplication after git clone."""

    def test_writable_sentinel_triggers_reapplication(
        self, tmp_path, test_config, content_structure, monkeypatch
    ):
        """Test that writable sentinel triggers permission reapplication."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Create initial state with read-only files
        test_file = content_structure["draft_dir"] / "test-doc.md"
        test_file.write_text("# Test", encoding="utf-8")

        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"],
        )
        assert result["success"]

        # After transition, source should be read-only
        source_file = content_structure["draft_dir"] / "test-doc.md"
        source_mode = os.stat(source_file).st_mode & 0o777
        assert source_mode == 0o444

        # Simulate git clone by making everything writable
        sentinel = content_structure["content_dir"] / ".sp-permissions"
        os.chmod(sentinel, 0o644)  # Make sentinel writable
        os.chmod(source_file, 0o644)  # Make source writable too

        # Verify files are writable now
        assert os.access(sentinel, os.W_OK)
        assert os.access(source_file, os.W_OK)

        # Run another transition - should detect writable sentinel and reapply permissions
        test_file2 = content_structure["draft_dir"] / "test-doc2.md"
        test_file2.write_text("# Test 2", encoding="utf-8")

        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc2",
            config_path=test_config,
            content_root=content_structure["content_dir"],
        )
        assert result["success"]

        # Sentinel should be read-only again
        sentinel_mode = os.stat(sentinel).st_mode & 0o777
        assert sentinel_mode == 0o444

        # Original source file should have permissions reapplied
        source_mode = os.stat(source_file).st_mode & 0o777
        assert source_mode == 0o444

    def test_reapplication_uses_current_config(
        self, tmp_path, monkeypatch
    ):
        """Test that permission reapplication uses current config, not old config."""
        monkeypatch.chdir(tmp_path)

        # Create initial config with 444 for source
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "content-stages.yaml"
        config_file.write_text(
            """
stages:
  - name: draft
    protected: false
    file_permissions: "644"

  - name: review
    protected: true
    file_permissions: "644"

transitions:
  - from: draft
    to: review
    action: copy
    source_file_permissions: "444"
    destination_file_permissions: "644"
""",
            encoding="utf-8",
        )

        # Create content structure
        content_dir = tmp_path / "content"
        draft_dir = content_dir / "draft"
        review_dir = content_dir / "review"
        draft_dir.mkdir(parents=True)
        review_dir.mkdir(parents=True)

        test_file = draft_dir / "test.md"
        test_file.write_text("# Test", encoding="utf-8")

        from llmflow.utils.content_transition import transition_content

        # Initial transition
        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test",
            config_path=config_file,
            content_root=content_dir,
        )
        assert result["success"]

        # File should be 444
        source_mode = os.stat(test_file).st_mode & 0o777
        assert source_mode == 0o444

        # Change config to use 400 instead
        config_file.write_text(
            """
stages:
  - name: draft
    protected: false
    file_permissions: "644"

  - name: review
    protected: true
    file_permissions: "644"

transitions:
  - from: draft
    to: review
    action: copy
    source_file_permissions: "400"
    destination_file_permissions: "644"
""",
            encoding="utf-8",
        )

        # Simulate git clone
        sentinel = content_dir / ".sp-permissions"
        os.chmod(sentinel, 0o644)
        os.chmod(test_file, 0o644)

        # Create another file and transition - triggers reapplication
        test_file2 = draft_dir / "test2.md"
        test_file2.write_text("# Test 2", encoding="utf-8")

        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test2",
            config_path=config_file,
            content_root=content_dir,
        )
        assert result["success"]

        # Original file should now have NEW config's permissions (400)
        source_mode = os.stat(test_file).st_mode & 0o777
        assert source_mode == 0o400


class TestGitAttributes:
    """Test .gitattributes file creation."""

    def test_gitattributes_created_with_sentinel(
        self, tmp_path, test_config, content_structure, monkeypatch
    ):
        """Test that .gitattributes is created alongside sentinel."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        gitattributes = content_structure["content_dir"] / ".gitattributes"
        assert not gitattributes.exists()

        # Perform transition
        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"],
        )

        assert result["success"]

        # .gitattributes should exist
        assert gitattributes.exists()

        # Verify contents
        content = gitattributes.read_text()
        assert ".sp-permissions merge=ours" in content

    def test_gitattributes_not_recreated_if_exists(
        self, tmp_path, test_config, content_structure, monkeypatch
    ):
        """Test that .gitattributes is not overwritten if it exists."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Create custom .gitattributes
        gitattributes = content_structure["content_dir"] / ".gitattributes"
        gitattributes.write_text("# Custom rules\n*.md linguist-documentation\n")

        original_content = gitattributes.read_text()

        # Perform transition
        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"],
        )

        assert result["success"]

        # .gitattributes should still have original content
        # (or have merge=ours rule appended, depending on implementation)
        content = gitattributes.read_text()
        assert "# Custom rules" in content
        assert ".sp-permissions merge=ours" in content


class TestPermissionStateTracking:
    """Test that permission state is tracked correctly."""

    def test_state_tracking_across_stages(
        self, tmp_path, test_config, content_structure, monkeypatch
    ):
        """Test that permissions are tracked and applied correctly across all stages."""
        monkeypatch.chdir(tmp_path)

        from llmflow.utils.content_transition import transition_content

        # Create file and transition through all stages
        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test-doc",
            config_path=test_config,
            content_root=content_structure["content_dir"],
        )
        assert result["success"]

        # Simulate git clone
        sentinel = content_structure["content_dir"] / ".sp-permissions"
        os.chmod(sentinel, 0o644)

        # Make all files writable (simulate post-clone state)
        for stage_dir in [
            content_structure["draft_dir"],
            content_structure["review_dir"],
        ]:
            for f in stage_dir.glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    os.chmod(f, 0o644)

        # Transition another file - triggers reapplication
        test_file2 = content_structure["draft_dir"] / "test2.md"
        test_file2.write_text("# Test 2", encoding="utf-8")

        result = transition_content(
            from_stage="draft",
            to_stage="review",
            path="test2",
            config_path=test_config,
            content_root=content_structure["content_dir"],
        )
        assert result["success"]

        # Verify original file in draft (should be 444 after transition)
        draft_file = content_structure["draft_dir"] / "test-doc.md"
        draft_mode = os.stat(draft_file).st_mode & 0o777
        assert draft_mode == 0o444

        # Verify file in review (should be 644)
        review_file = content_structure["review_dir"] / "test-doc.md"
        review_mode = os.stat(review_file).st_mode & 0o777
        assert review_mode == 0o644
