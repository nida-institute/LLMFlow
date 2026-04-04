"""
Tests for content stages configuration loader.
"""

import pytest
from pathlib import Path
import tempfile
import os

from llmflow.content_stages_schema import (
    ContentStagesConfig,
    StageConfig,
    TransitionConfig,
    DEFAULT_CONTENT_STAGES,
)
from llmflow.utils.content_stages_loader import (
    ContentStagesConfigLoader,
    get_content_stages_config,
)


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset global config singleton before each test for proper isolation."""
    import llmflow.utils.content_stages_loader as loader_module
    loader_module._config_loader = None
    yield
    loader_module._config_loader = None


class TestContentStagesSchema:
    """Test Pydantic schema validation."""

    def test_minimal_valid_config(self):
        """Test that minimal valid configuration is accepted."""
        config = ContentStagesConfig(
            stages=[
                StageConfig(name="stage1"),
                StageConfig(name="stage2", protected=True),
            ],
            transitions=[],
        )
        assert len(config.stages) == 2
        assert config.stages[0].name == "stage1"
        assert config.stages[1].name == "stage2"

    def test_duplicate_stage_names_rejected(self):
        """Test that duplicate stage names are rejected."""
        with pytest.raises(ValueError, match="Duplicate stage names"):
            ContentStagesConfig(
                stages=[
                    StageConfig(name="stage1"),
                    StageConfig(name="stage1"),  # Duplicate
                ],
                transitions=[],
            )

    def test_all_protected_stages_rejected(self):
        """Test that config with all protected stages is rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ContentStagesConfig(
                stages=[
                    StageConfig(name="stage1", protected=True),
                    StageConfig(name="stage2", protected=True),
                ],
                transitions=[],
            )

    def test_invalid_file_permissions_rejected(self):
        """Test that invalid file permissions are rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Invalid octal digit"):
            StageConfig(name="stage1", file_permissions="999")  # Invalid

        with pytest.raises(ValidationError, match="Invalid file permissions"):
            StageConfig(name="stage1", file_permissions="12")  # Too short

    def test_valid_transition(self):
        """Test that valid transition configuration is accepted."""
        config = ContentStagesConfig(
            stages=[
                StageConfig(name="stage1"),
                StageConfig(name="stage2", protected=True),
            ],
            transitions=[
                TransitionConfig(from_stage="stage1", to_stage="stage2", action="copy")
            ],
        )
        config.validate_transitions()  # Should not raise

    def test_transition_to_undefined_stage_rejected(self):
        """Test that transition to undefined stage is rejected."""
        config = ContentStagesConfig(
            stages=[
                StageConfig(name="stage1"),
            ],
            transitions=[
                TransitionConfig(
                    from_stage="stage1", to_stage="undefined", action="copy"
                )
            ],
        )
        with pytest.raises(ValueError, match="undefined destination stage"):
            config.validate_transitions()

    def test_immutable_stage_as_source_rejected(self):
        """Test that immutable stage cannot be transition source."""
        config = ContentStagesConfig(
            stages=[
                StageConfig(name="stage1", immutable=True),
                StageConfig(name="stage2"),
            ],
            transitions=[
                TransitionConfig(from_stage="stage1", to_stage="stage2", action="copy")
            ],
        )
        with pytest.raises(ValueError, match="Immutable stage .* cannot be transition source"):
            config.validate_transitions()

    def test_default_config_valid(self):
        """Test that default configuration is valid."""
        assert len(DEFAULT_CONTENT_STAGES.stages) == 3
        assert DEFAULT_CONTENT_STAGES.stages[0].name == "generated"
        assert DEFAULT_CONTENT_STAGES.stages[1].name == "editing"
        assert DEFAULT_CONTENT_STAGES.stages[2].name == "published"

        assert len(DEFAULT_CONTENT_STAGES.transitions) == 2
        DEFAULT_CONTENT_STAGES.validate_transitions()  # Should not raise


class TestContentStagesConfigLoader:
    """Test configuration file loading."""

    def test_load_default_when_no_file_exists(self, tmp_path, monkeypatch):
        """Test that default config is used when no file exists."""
        monkeypatch.chdir(tmp_path)
        loader = ContentStagesConfigLoader()

        config = loader.config
        assert len(config.stages) == 3
        assert config.stages[0].name == "generated"
        assert config.stages[1].name == "editing"
        assert config.stages[2].name == "published"

    def test_load_valid_config_file(self, tmp_path, monkeypatch):
        """Test loading a valid configuration file."""
        monkeypatch.chdir(tmp_path)

        # Create config directory and file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "content-stages.yaml"

        config_file.write_text(
            """
stages:
  - name: draft
    protected: false
    file_permissions: "644"
  - name: published
    protected: true
    immutable: true
    file_permissions: "444"

transitions:
  - from: draft
    to: published
    action: move
""",
            encoding="utf-8",
        )

        loader = ContentStagesConfigLoader()
        config = loader.config

        assert len(config.stages) == 2
        assert config.stages[0].name == "draft"
        assert config.stages[1].name == "published"
        assert len(config.transitions) == 1
        assert config.transitions[0].from_stage == "draft"
        assert config.transitions[0].to_stage == "published"

    def test_load_invalid_yaml_rejected(self, tmp_path, monkeypatch):
        """Test that invalid YAML is rejected."""
        monkeypatch.chdir(tmp_path)

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "content-stages.yaml"

        config_file.write_text(
            """
stages:
  - name: draft
    protected: [invalid yaml structure
""",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Failed to parse"):
            ContentStagesConfigLoader()

    def test_get_stage_by_name(self, tmp_path, monkeypatch):
        """Test getting stage configuration by name."""
        monkeypatch.chdir(tmp_path)
        loader = ContentStagesConfigLoader()

        generated_stage = loader.get_stage("generated")
        assert generated_stage is not None
        assert generated_stage.name == "generated"
        assert not generated_stage.protected

        nonexistent_stage = loader.get_stage("nonexistent")
        assert nonexistent_stage is None

    def test_get_transition(self, tmp_path, monkeypatch):
        """Test getting transition configuration."""
        monkeypatch.chdir(tmp_path)
        loader = ContentStagesConfigLoader()

        trans = loader.get_transition("generated", "editing")
        assert trans is not None
        assert trans.from_stage == "generated"
        assert trans.to_stage == "editing"

        nonexistent = loader.get_transition("generated", "nonexistent")
        assert nonexistent is None

    def test_is_transition_allowed(self, tmp_path, monkeypatch):
        """Test checking if transition is allowed."""
        monkeypatch.chdir(tmp_path)
        loader = ContentStagesConfigLoader()

        assert loader.is_transition_allowed("generated", "editing")
        assert loader.is_transition_allowed("editing", "published")
        assert not loader.is_transition_allowed("generated", "published")

    def test_get_protected_stages(self, tmp_path, monkeypatch):
        """Test getting list of protected stages."""
        monkeypatch.chdir(tmp_path)
        loader = ContentStagesConfigLoader()

        protected = loader.get_protected_stages()
        assert "editing" in protected
        assert "published" in protected
        assert "generated" not in protected

    def test_validate_config_warnings(self, tmp_path, monkeypatch):
        """Test configuration validation warnings."""
        monkeypatch.chdir(tmp_path)

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "content-stages.yaml"

        # Create config with stage that has no transitions
        config_file.write_text(
            """
stages:
  - name: draft
    protected: false
  - name: orphan
    protected: true
  - name: published
    protected: true

transitions:
  - from: draft
    to: published
""",
            encoding="utf-8",
        )

        loader = ContentStagesConfigLoader()
        issues = loader.validate_config()

        # Should warn about orphan stage
        assert any("orphan" in issue for issue in issues)


class TestGlobalConfigAccess:
    """Test global configuration access functions."""

    def test_get_content_stages_config(self, tmp_path, monkeypatch):
        """Test global config getter."""
        monkeypatch.chdir(tmp_path)

        config = get_content_stages_config()
        assert config is not None
        assert len(config.stages) == 3  # Default config

    def test_config_reload(self, tmp_path, monkeypatch):
        """Test forcing config reload."""
        monkeypatch.chdir(tmp_path)

        # Get default config
        config1 = get_content_stages_config()
        assert len(config1.stages) == 3

        # Create custom config
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "content-stages.yaml"

        config_file.write_text(
            """
stages:
  - name: single
    protected: false

transitions: []
""",
            encoding="utf-8",
        )

        # Reload should pick up new config
        config2 = get_content_stages_config(reload=True)
        assert len(config2.stages) == 1
        assert config2.stages[0].name == "single"
