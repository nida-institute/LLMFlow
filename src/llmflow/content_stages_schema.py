"""
Schema definitions for content lifecycle management system.

Defines configurable stages and transitions for managing content through
its lifecycle (e.g., generated → editing → published).
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StageConfig(BaseModel):
    """Configuration for a content lifecycle stage."""

    model_config = ConfigDict(extra="forbid")

    # Identity
    name: str = Field(..., description="Unique stage name")
    description: Optional[str] = Field(None, description="Human-readable description")

    # Protection settings
    protected: bool = Field(
        False, description="Whether pipeline can write to this stage"
    )
    immutable: bool = Field(
        False, description="Whether files can be modified after creation"
    )
    allow_direct_edits: bool = Field(
        True, description="Whether users should edit files directly"
    )

    # File management
    file_permissions: str = Field(
        default="644", description="Unix permissions in octal format (e.g., '644', '444')"
    )
    auto_create_metadata: bool = Field(
        default=False, description="Create .metadata.json on file creation"
    )
    metadata_schema: Optional[str] = Field(
        default=None, description="Path to JSON schema for metadata validation"
    )
    metadata_fields: Optional[List[str]] = Field(
        default=None, description="Required metadata fields"
    )

    # Version control
    git_tracked: bool = Field(default=True, description="Include files in git commits")
    auto_commit: bool = Field(default=False, description="Auto-commit on file creation")
    commit_message_template: Optional[str] = Field(
        default=None, description="Template for auto-commit messages"
    )
    create_git_tag: bool = Field(default=False, description="Create git tag on file creation")
    git_tag_template: Optional[str] = Field(
        default=None, description="Template for git tag names"
    )

    # Content validation
    require_schema_validation: bool = Field(
        default=False, description="Validate content against schema on write"
    )
    validation_schemas: Optional[Dict[str, str]] = Field(
        default=None, description="Schema paths by file extension"
    )
    allowed_formats: Optional[List[str]] = Field(
        default=None, description="Allowed file extensions (e.g., ['json', 'md'])"
    )

    # Visual indicators
    readme_template: Optional[str] = Field(
        default=None, description="Template for auto-generated README"
    )
    status_emoji: Optional[str] = Field(default=None, description="Emoji for status display")

    # Warnings
    warn_on_stale: bool = Field(default=False, description="Warn about old unchanged files")
    stale_threshold_days: Optional[int] = Field(
        default=None, description="Days before file considered stale"
    )

    # Archive behavior
    create_archive_copy: bool = Field(
        default=False, description="Create timestamped backup copies"
    )
    archive_path_template: Optional[str] = Field(
        default=None, description="Path template for archives"
    )

    @field_validator("file_permissions")
    @classmethod
    def validate_file_permissions(cls, v: str) -> str:
        """Validate Unix permissions are in valid octal format."""
        if not v.isdigit() or len(v) != 3:
            raise ValueError(f"Invalid file permissions: {v} (must be 3-digit octal)")
        for digit in v:
            if not (0 <= int(digit) <= 7):
                raise ValueError(f"Invalid octal digit in permissions: {digit}")
        return v


class RequirementConfig(BaseModel):
    """Configuration for a transition requirement."""

    model_config = ConfigDict(extra="allow")

    type: str = Field(..., description="Requirement type (e.g., 'git_committed')")
    message: str = Field(..., description="Error message if requirement not met")

    # Optional fields depending on type
    fields: Optional[List[str]] = None
    stages: Optional[List[str]] = None
    validation_schema: Optional[str] = None  # Renamed from 'schema' to avoid BaseModel.schema() conflict
    schemas: Optional[Dict[str, str]] = None
    files: Optional[List[str]] = None
    stage: Optional[str] = None
    checks: Optional[List[str]] = None
    approvers: Optional[List[str]] = None


class PostTransitionAction(BaseModel):
    """Configuration for post-transition actions."""

    model_config = ConfigDict(extra="allow")

    action: str = Field(
        ...,
        description="Action type (e.g., 'create_archive_copy', 'regenerate_index')",
    )

    # Optional fields depending on action
    path_template: Optional[str] = None
    index_file: Optional[str] = None
    url: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class TransitionConfig(BaseModel):
    """Configuration for a stage transition."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Identity
    from_stage: str = Field(description="Source stage name", alias="from")
    to_stage: str = Field(description="Destination stage name", alias="to")

    # File operations
    action: Literal["copy", "move", "symlink"] = Field(
        default="copy", description="File operation type"
    )
    source_file_permissions: Optional[str] = Field(
        default=None, description="Permissions for source after transition"
    )
    destination_file_permissions: Optional[str] = Field(
        default=None, description="Permissions for destination"
    )
    preserve_timestamps: bool = Field(default=True, description="Keep original file timestamps")

    # Metadata operations
    copy_metadata: bool = Field(default=False, description="Copy metadata from source")
    metadata_fields_to_set: Optional[Dict[str, str]] = Field(
        default=None, description="Metadata fields to set/update"
    )
    merge_metadata_from_source: bool = Field(
        default=False, description="Merge source metadata into destination"
    )

    # Content transformation
    bidirectional_sync: bool = Field(
        default=False, description="Sync Markdown edits back to JSON"
    )
    regenerate_derivatives: bool = Field(
        default=False, description="Generate derivative formats"
    )
    derivative_formats: Optional[List[str]] = Field(
        default=None, description="Formats to generate (e.g., ['html', 'docx'])"
    )

    # Git operations
    git_add_source: bool = Field(default=False, description="Stage source files in git")
    git_add_destination: bool = Field(default=True, description="Stage destination files in git")
    git_remove_source: bool = Field(
        default=False, description="Remove source from git (for move)"
    )
    auto_commit: bool = Field(default=False, description="Auto-commit after transition")
    commit_message_template: Optional[str] = Field(
        default=None, description="Template for commit message"
    )

    # Validation
    requirements: List[RequirementConfig] = Field(
        default_factory=list, description="Pre-conditions for transition"
    )

    # Post-transition actions
    post_transition: List[PostTransitionAction] = Field(
        default_factory=list, description="Actions after successful transition"
    )

    # Notifications
    notify: bool = Field(default=False, description="Send notification on completion")
    notification_template: Optional[str] = Field(
        default=None, description="Template for notification message"
    )

    @field_validator("source_file_permissions", "destination_file_permissions")
    @classmethod
    def validate_permissions(cls, v: Optional[str]) -> Optional[str]:
        """Validate file permissions if provided."""
        if v is None:
            return v
        if not v.isdigit() or len(v) != 3:
            raise ValueError(f"Invalid file permissions: {v} (must be 3-digit octal)")
        for digit in v:
            if not (0 <= int(digit) <= 7):
                raise ValueError(f"Invalid octal digit in permissions: {digit}")
        return v


class ContentStagesConfig(BaseModel):
    """Root configuration for content lifecycle management."""

    model_config = ConfigDict(extra="forbid")

    stages: List[StageConfig] = Field(
        ..., description="List of content lifecycle stages"
    )
    transitions: List[TransitionConfig] = Field(
        default_factory=list, description="List of allowed stage transitions"
    )

    @field_validator("stages")
    @classmethod
    def validate_stage_names_unique(cls, stages: List[StageConfig]) -> List[StageConfig]:
        """Ensure stage names are unique."""
        names = [s.name for s in stages]
        if len(names) != len(set(names)):
            duplicates = [n for n in names if names.count(n) > 1]
            raise ValueError(f"Duplicate stage names: {', '.join(set(duplicates))}")
        return stages

    @field_validator("stages")
    @classmethod
    def validate_at_least_one_non_protected(
        cls, stages: List[StageConfig]
    ) -> List[StageConfig]:
        """Ensure at least one stage is not protected (for pipeline output)."""
        if all(s.protected for s in stages):
            raise ValueError(
                "At least one stage must be non-protected (for pipeline output)"
            )
        return stages

    def validate_transitions(self) -> None:
        """Validate that all transitions reference defined stages."""
        stage_names = {s.name for s in self.stages}

        for trans in self.transitions:
            if trans.from_stage not in stage_names:
                raise ValueError(
                    f"Transition references undefined source stage: {trans.from_stage}"
                )
            if trans.to_stage not in stage_names:
                raise ValueError(
                    f"Transition references undefined destination stage: {trans.to_stage}"
                )

            # Validate immutable stages cannot be transition sources
            from_stage = next(s for s in self.stages if s.name == trans.from_stage)
            if from_stage.immutable:
                raise ValueError(
                    f"Immutable stage '{trans.from_stage}' cannot be transition source"
                )

            # Validate protected stages cannot be pipeline targets
            to_stage = next(s for s in self.stages if s.name == trans.to_stage)
            if to_stage.protected and trans.action != "move":
                # Protected stages can receive moved files, but not copies
                pass


# Default configuration (built-in fallback)
DEFAULT_CONTENT_STAGES = ContentStagesConfig(
    stages=[
        StageConfig(
            name="generated",
            description="Pipeline output - can be regenerated at any time",
            protected=False,
            immutable=False,
            allow_direct_edits=True,
            file_permissions="644",
            auto_create_metadata=False,
            git_tracked=False,
            auto_commit=False,
            require_schema_validation=False,
            allowed_formats=["json", "md", "html", "txt"],
            readme_template=(
                "# Generated Content\n\n"
                "⚠️ **DO NOT EDIT FILES HERE**\n\n"
                "This directory contains pipeline-generated content that can be\n"
                "overwritten at any time. To edit a file:\n\n"
                "1. Check status: `sp content status <filename>`\n"
                "2. Send to editing: `sp transition generated editing <filename>`\n"
                "3. Edit in: `content/editing/<filename>`\n"
            ),
            status_emoji="🔄",
        ),
        StageConfig(
            name="editing",
            description="Human editor workspace - protected from pipeline",
            protected=True,
            immutable=False,
            allow_direct_edits=True,
            file_permissions="644",
            auto_create_metadata=True,
            git_tracked=True,
            auto_commit=False,
            require_schema_validation=False,
            allowed_formats=["md", "json"],
            readme_template=(
                "# Editing Workspace\n\n"
                "✏️ Edit files in this directory freely.\n\n"
                "Files here are protected from pipeline regeneration.\n"
                "Commit your changes regularly.\n\n"
                "When ready to publish:\n"
                "  sp transition editing published <filename>\n"
            ),
            status_emoji="✏️",
            warn_on_stale=True,
            stale_threshold_days=30,
        ),
        StageConfig(
            name="published",
            description="Published content - immutable",
            protected=True,
            immutable=True,
            allow_direct_edits=False,
            file_permissions="444",
            auto_create_metadata=True,
            git_tracked=True,
            auto_commit=True,
            commit_message_template="chore: publish {path} [{editor}]",
            create_git_tag=True,
            git_tag_template="published/{path}/{timestamp}",
            require_schema_validation=True,
            allowed_formats=["md", "json", "html", "docx", "pdf"],
            readme_template=(
                "# Published Content\n\n"
                "✅ This directory contains published, immutable content.\n\n"
                "Files are read-only. To edit:\n"
                "1. Transition back: sp transition published editing <filename>\n"
                "2. Make edits in: content/editing/<filename>\n"
                "3. Republish: sp transition editing published <filename>\n"
            ),
            status_emoji="✅",
            create_archive_copy=True,
            archive_path_template="published/archive/{path}/{timestamp}",
        ),
    ],
    transitions=[
        TransitionConfig(**{
            "from": "generated",
            "to": "editing",
            "action": "copy",
            "source_file_permissions": "444",
            "destination_file_permissions": "644",
            "preserve_timestamps": True,
            "copy_metadata": False,
            "metadata_fields_to_set": {
                "source_stage": "generated",
                "source_path": "generated/{path}",
                "transitioned_at": "{timestamp}",
                "transitioned_by": "{user}",
            },
            "git_add_source": False,
            "git_add_destination": True,
            "auto_commit": False,
            "requirements": [],
        }),
        TransitionConfig(**{
            "from": "editing",
            "to": "published",
            "action": "move",
            "destination_file_permissions": "444",
            "preserve_timestamps": False,
            "copy_metadata": True,
            "metadata_fields_to_set": {
                "published_at": "{timestamp}",
                "published_by": "{user}",
                "source_stage": "editing",
            },
            "merge_metadata_from_source": True,
            "bidirectional_sync": True,
            "regenerate_derivatives": True,
            "derivative_formats": ["html", "docx"],
            "git_add_destination": True,
            "git_remove_source": True,
            "auto_commit": True,
            "commit_message_template": (
                "chore: publish {path}\n\n"
                "Editor: {metadata.editor}\n"
                "Last modified: {metadata.last_modified}\n"
            ),
            "requirements": [
                RequirementConfig(
                    type="git_committed",
                    message="All edits must be committed before publishing",
                    stages=["editing"],
                ),
                RequirementConfig(
                    type="metadata_present",
                    fields=["editor", "last_modified"],
                    message="Metadata must track who edited and when",
                ),
                RequirementConfig(
                    type="schema_valid",
                    message="Content must validate against schema",
                ),
                RequirementConfig(
                    type="no_uncommitted_changes",
                    stages=["editing"],
                    message="Cannot publish with uncommitted edits",
                ),
            ],
            "post_transition": [
                PostTransitionAction(
                    action="create_archive_copy",
                    path_template="published/archive/{path}/{timestamp}",
                ),
                PostTransitionAction(
                    action="regenerate_index", index_file="published/index.json"
                ),
            ],
        }),
    ],
)
