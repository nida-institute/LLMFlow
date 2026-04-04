"""
Configuration loader for content lifecycle management system.

Loads and validates content-stages.yaml configuration, providing
access to stage and transition definitions.
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from llmflow.content_stages_schema import (
    ContentStagesConfig,
    DEFAULT_CONTENT_STAGES,
    StageConfig,
    TransitionConfig,
)
from llmflow.modules.logger import Logger

logger = Logger()


class ContentStagesConfigLoader:
    """Loads and provides access to content stages configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            config_path: Path to content-stages.yaml. If None, searches in:
                1. ./config/content-stages.yaml
                2. ../config/content-stages.yaml (for tests)
                3. Falls back to DEFAULT_CONTENT_STAGES
        """
        self.config_path = config_path
        self._config: Optional[ContentStagesConfig] = None
        self._load_config()

    def _find_config_file(self) -> Optional[Path]:
        """Search for content-stages.yaml in standard locations."""
        search_paths = [
            Path.cwd() / "config" / "content-stages.yaml",
            Path.cwd().parent / "config" / "content-stages.yaml",
        ]

        # Also check in project root if we're in a subdirectory
        if "project" in str(Path.cwd()):
            project_root = Path.cwd()
            while project_root.name != "project" and project_root.parent != project_root:
                project_root = project_root.parent
            if project_root.name == "project":
                search_paths.append(project_root / "config" / "content-stages.yaml")

        for path in search_paths:
            if path.exists():
                return path

        return None

    def _load_config(self) -> None:
        """Load configuration from file or use defaults."""
        # Use provided path if given
        if self.config_path:
            if not self.config_path.exists():
                raise FileNotFoundError(
                    f"Content stages config not found: {self.config_path}"
                )
            config_file = self.config_path
        else:
            # Search for config file
            config_file = self._find_config_file()

        if config_file is None:
            logger.info(
                "No content-stages.yaml found, using default configuration "
                "(generated → editing → published)"
            )
            self._config = DEFAULT_CONTENT_STAGES
            return

        # Load and parse YAML
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if config_data is None:
                raise ValueError("Content stages config file is empty")

            # Validate with Pydantic
            self._config = ContentStagesConfig(**config_data)

            # Additional validation
            self._config.validate_transitions()

            logger.info(f"Loaded content stages config from {config_file}")
            logger.info(
                f"  Stages: {', '.join(s.name for s in self._config.stages)}"
            )

        except ValidationError as e:
            raise ValueError(
                f"Invalid content-stages.yaml configuration:\n{e}"
            ) from e
        except yaml.YAMLError as e:
            raise ValueError(
                f"Failed to parse content-stages.yaml:\n{e}"
            ) from e
        except Exception as e:
            raise ValueError(
                f"Error loading content-stages.yaml: {e}"
            ) from e

    @property
    def config(self) -> ContentStagesConfig:
        """Get the loaded configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config

    def get_stage(self, name: str) -> Optional[StageConfig]:
        """Get stage configuration by name."""
        for stage in self.config.stages:
            if stage.name == name:
                return stage
        return None

    def get_transition(
        self, from_stage: str, to_stage: str
    ) -> Optional[TransitionConfig]:
        """Get transition configuration between two stages."""
        for trans in self.config.transitions:
            if trans.from_stage == from_stage and trans.to_stage == to_stage:
                return trans
        return None

    def is_transition_allowed(self, from_stage: str, to_stage: str) -> bool:
        """Check if a transition is allowed."""
        return self.get_transition(from_stage, to_stage) is not None

    def get_stage_names(self) -> list[str]:
        """Get list of all stage names."""
        return [s.name for s in self.config.stages]

    def get_protected_stages(self) -> list[str]:
        """Get list of protected stage names (pipeline cannot write)."""
        return [s.name for s in self.config.stages if s.protected]

    def get_immutable_stages(self) -> list[str]:
        """Get list of immutable stage names (files cannot be modified)."""
        return [s.name for s in self.config.stages if s.immutable]

    def validate_config(self) -> list[str]:
        """
        Validate configuration and return list of warnings/issues.

        Returns:
            List of warning/error messages. Empty list if valid.
        """
        issues = []

        # Check for stages with no transitions
        stages_with_transitions = set()
        for trans in self.config.transitions:
            stages_with_transitions.add(trans.from_stage)
            stages_with_transitions.add(trans.to_stage)

        for stage in self.config.stages:
            if stage.name not in stages_with_transitions:
                issues.append(
                    f"Warning: Stage '{stage.name}' has no transitions defined"
                )

        # Check for unreachable stages
        reachable = set()
        # Start from non-protected stages (where pipeline writes)
        for stage in self.config.stages:
            if not stage.protected:
                reachable.add(stage.name)

        # BFS to find all reachable stages
        to_visit = list(reachable)
        while to_visit:
            current = to_visit.pop(0)
            for trans in self.config.transitions:
                if trans.from_stage == current and trans.to_stage not in reachable:
                    reachable.add(trans.to_stage)
                    to_visit.append(trans.to_stage)

        for stage in self.config.stages:
            if stage.name not in reachable:
                issues.append(
                    f"Warning: Stage '{stage.name}' is not reachable from pipeline output"
                )

        # Check for schema files that don't exist
        for stage in self.config.stages:
            if stage.metadata_schema and not Path(stage.metadata_schema).exists():
                issues.append(
                    f"Warning: Metadata schema not found: {stage.metadata_schema}"
                )

            if stage.validation_schemas:
                for ext, schema_path in stage.validation_schemas.items():
                    if not Path(schema_path).exists():
                        issues.append(
                            f"Warning: Validation schema not found: {schema_path} (for {ext} files)"
                        )

        return issues


# Global config loader instance
_config_loader: Optional[ContentStagesConfigLoader] = None


def get_content_stages_config(
    config_path: Optional[Path] = None, reload: bool = False
) -> ContentStagesConfig:
    """
    Get the content stages configuration.

    Args:
        config_path: Optional path to config file. If None, uses standard search.
        reload: Force reload of configuration.

    Returns:
        ContentStagesConfig instance.
    """
    global _config_loader

    if _config_loader is None or reload:
        _config_loader = ContentStagesConfigLoader(config_path)

    return _config_loader.config


def get_stage_config(stage_name: str) -> Optional[StageConfig]:
    """Get configuration for a specific stage."""
    loader = _config_loader or ContentStagesConfigLoader()
    return loader.get_stage(stage_name)


def get_transition_config(
    from_stage: str, to_stage: str
) -> Optional[TransitionConfig]:
    """Get configuration for a specific transition."""
    loader = _config_loader or ContentStagesConfigLoader()
    return loader.get_transition(from_stage, to_stage)
