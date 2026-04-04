"""
Content lifecycle transition implementation.

Handles transitioning content between stages (copy/move operations,
permission management, metadata tracking).
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib

from llmflow.utils.content_stages_loader import (
    ContentStagesConfigLoader,
    get_content_stages_config,
)
from llmflow.modules.logger import Logger

logger = Logger()


class TransitionError(Exception):
    """Exception raised when transition fails."""

    pass


def _create_sentinel_file(content_root: Path) -> None:
    """
    Create the .sp-permissions sentinel file.

    This file is used to detect git clones (where file permissions are reset).
    The file is created once and never modified.

    Args:
        content_root: Root directory for content/
    """
    sentinel = content_root / ".sp-permissions"

    if sentinel.exists():
        return  # Already exists, don't recreate

    # Create minimal marker
    sentinel.write_text(json.dumps({"_marker": "sp"}), encoding="utf-8")

    # Make read-only
    os.chmod(sentinel, 0o444)

    logger.info(f"Created sentinel file: {sentinel}")


def _create_or_update_gitattributes(content_root: Path) -> None:
    """
    Create or update .gitattributes with merge strategy for sentinel.

    Args:
        content_root: Root directory for content/
    """
    gitattributes = content_root / ".gitattributes"
    merge_rule = ".sp-permissions merge=ours\n"

    if gitattributes.exists():
        # Check if rule already exists
        content = gitattributes.read_text(encoding="utf-8")
        if ".sp-permissions merge=ours" in content:
            return  # Rule already present

        # Append rule
        if not content.endswith("\n"):
            content += "\n"
        content += merge_rule
        gitattributes.write_text(content, encoding="utf-8")
        logger.info("Added .sp-permissions merge rule to .gitattributes")
    else:
        # Create new .gitattributes
        gitattributes.write_text(
            "# LLMFlow content lifecycle management\n" + merge_rule, encoding="utf-8"
        )
        logger.info(f"Created .gitattributes with sentinel merge rule")


def _reapply_all_permissions(
    content_root: Path, config_path: Optional[Path] = None
) -> None:
    """
    Reapply file permissions to all content based on current configuration.

    This is called when the sentinel file is detected as writable (indicating
    a git clone or checkout that reset permissions).

    Args:
        content_root: Root directory for content/
        config_path: Optional path to content-stages.yaml
    """
    loader = ContentStagesConfigLoader(config_path)
    config = loader.config

    logger.info("🔧 Reapplying file permissions across all stages...")

    files_updated = 0

    for stage in config.stages:
        stage_dir = content_root / stage.name
        if not stage_dir.exists():
            continue

        # Get expected permissions for this stage
        stage_perms = int(stage.file_permissions, 8)

        # Apply to all files in this stage (except hidden files)
        for file_path in stage_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    os.chmod(file_path, stage_perms)
                    files_updated += 1
                except Exception as e:
                    logger.warning(f"Failed to set permissions on {file_path}: {e}")

        # Also check for files that should have special permissions based on transitions
        # (e.g., files in draft/ that have been copied to review/ should be read-only)
        for trans in config.transitions:
            if (
                trans.from_stage == stage.name
                and trans.action == "copy"
                and trans.source_file_permissions
            ):
                # Find files that exist in destination stage
                to_stage_dir = content_root / trans.to_stage
                if not to_stage_dir.exists():
                    continue

                for dest_file in to_stage_dir.rglob("*"):
                    if dest_file.is_file() and not dest_file.name.startswith("."):
                        # Check if corresponding source file exists
                        rel_path = dest_file.relative_to(to_stage_dir)
                        source_file = stage_dir / rel_path

                        if source_file.exists():
                            # Apply source permissions from transition config
                            source_perms = int(trans.source_file_permissions, 8)
                            try:
                                os.chmod(source_file, source_perms)
                                files_updated += 1
                            except Exception as e:
                                logger.warning(
                                    f"Failed to set source permissions on {source_file}: {e}"
                                )

    logger.info(f"✓ Updated permissions on {files_updated} files")


def _ensure_sentinel_and_permissions(
    content_root: Path, config_path: Optional[Path] = None
) -> None:
    """
    Ensure sentinel file exists and check if permissions need reapplication.

    This should be called at the beginning of every content operation.

    Args:
        content_root: Root directory for content/
        config_path: Optional path to content-stages.yaml
    """
    sentinel = content_root / ".sp-permissions"

    if not sentinel.exists():
        # First run - create sentinel and gitattributes
        content_root.mkdir(parents=True, exist_ok=True)
        _create_sentinel_file(content_root)
        _create_or_update_gitattributes(content_root)
        return

    # Check if sentinel is writable (indicates git clone/checkout)
    if os.access(sentinel, os.W_OK):
        logger.info(
            "Detected writable sentinel file - repository was likely cloned or checked out"
        )
        _reapply_all_permissions(content_root, config_path)

        # Make sentinel read-only again
        os.chmod(sentinel, 0o444)

    # Ensure .gitattributes has merge rule
    _create_or_update_gitattributes(content_root)


def transition_content(
    from_stage: str,
    to_stage: str,
    path: str,
    config_path: Optional[Path] = None,
    content_root: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Transition content between stages.

    Args:
        from_stage: Source stage name
        to_stage: Destination stage name
        path: Relative path to content (without extension)
        config_path: Optional path to content-stages.yaml
        content_root: Root directory for content/ (default: ./content)
        dry_run: If True, only validate without making changes

    Returns:
        Dict with 'success' (bool) and either 'result' or 'error' key
    """
    try:
        # Determine content root first
        if content_root is None:
            content_root = Path.cwd() / "content"

        # Ensure sentinel exists and check permissions (before any operations)
        _ensure_sentinel_and_permissions(content_root, config_path)

        # Load configuration
        loader = ContentStagesConfigLoader(config_path)
        config = loader.config

        # Validate stages exist
        from_stage_config = loader.get_stage(from_stage)
        to_stage_config = loader.get_stage(to_stage)

        if not from_stage_config:
            return {"success": False, "error": f"Source stage '{from_stage}' not found"}

        if not to_stage_config:
            return {
                "success": False,
                "error": f"Destination stage '{to_stage}' not found",
            }

        # Validate transition is allowed
        transition_config = loader.get_transition(from_stage, to_stage)
        if not transition_config:
            return {
                "success": False,
                "error": f"Transition from '{from_stage}' to '{to_stage}' is not allowed",
            }

        # Find source files
        from_dir = content_root / from_stage
        to_dir = content_root / to_stage

        # Find all files matching the path pattern
        source_files = _find_files(from_dir, path)
        if not source_files:
            return {
                "success": False,
                "error": f"No files found for '{path}' in {from_stage} stage",
            }

        # Validate requirements
        if transition_config.requirements:
            req_result = _check_requirements(
                transition_config.requirements,
                from_dir,
                path,
                source_files,
            )
            if not req_result["success"]:
                return req_result

        if dry_run:
            return {
                "success": True,
                "result": {
                    "action": transition_config.action,
                    "files": [str(f.relative_to(from_dir)) for f in source_files],
                    "dry_run": True,
                },
            }

        # Perform transition
        result = _perform_transition(
            source_files=source_files,
            from_dir=from_dir,
            to_dir=to_dir,
            path=path,
            from_stage_config=from_stage_config,
            to_stage_config=to_stage_config,
            transition_config=transition_config,
        )

        return {"success": True, "result": result}

    except TransitionError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error during transition: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


def _find_files(directory: Path, path: str) -> List[Path]:
    """
    Find all files matching the path pattern.

    Args:
        directory: Directory to search in
        path: Base path without extension

    Returns:
        List of matching file paths
    """
    import glob

    # Try exact matches with common extensions
    files = []
    for ext in ["md", "json", "html", "txt", "yaml", "xml"]:
        file_path = directory / f"{path}.{ext}"
        if file_path.exists():
            files.append(file_path)

    # Also try glob pattern
    glob_pattern = str(directory / f"{path}.*")
    for file_str in glob.glob(glob_pattern):
        file_path = Path(file_str)
        if file_path not in files and file_path.is_file():
            files.append(file_path)

    return files


def _check_requirements(
    requirements: List,
    from_dir: Path,
    path: str,
    source_files: List[Path],
) -> Dict[str, Any]:
    """
    Check if all requirements are satisfied.

    Args:
        requirements: List of requirement configurations
        from_dir: Source directory
        path: Content path
        source_files: List of source files

    Returns:
        Dict with 'success' (bool) and 'error' if failed
    """
    for req in requirements:
        if req.type == "metadata_present":
            # Check that metadata file exists and has required fields
            metadata_file = from_dir / ".metadata.json"
            if not metadata_file.exists():
                return {
                    "success": False,
                    "error": f"{req.message}: Metadata file not found",
                }

            metadata = json.loads(metadata_file.read_text())
            item_metadata = metadata.get(path)

            if not item_metadata:
                return {
                    "success": False,
                    "error": f"{req.message}: No metadata for '{path}'",
                }

            for field in req.fields:
                if field not in item_metadata:
                    return {
                        "success": False,
                        "error": f"{req.message}: Missing field '{field}'",
                    }

        elif req.type == "not_empty":
            # Check that files are not empty
            for file_path in source_files:
                if file_path.stat().st_size == 0:
                    return {
                        "success": False,
                        "error": f"{req.message}: File {file_path.name} is empty",
                    }

        # Add more requirement type implementations here
        # (git_committed, schema_valid, etc.)

    return {"success": True}


def _perform_transition(
    source_files: List[Path],
    from_dir: Path,
    to_dir: Path,
    path: str,
    from_stage_config,
    to_stage_config,
    transition_config,
) -> Dict[str, Any]:
    """
    Perform the actual file transition.

    Args:
        source_files: List of source file paths
        from_dir: Source directory
        to_dir: Destination directory
        path: Content path
        from_stage_config: Source stage configuration
        to_stage_config: Destination stage configuration
        transition_config: Transition configuration

    Returns:
        Dict with transition results
    """
    # Ensure destination directory exists
    to_dir.mkdir(parents=True, exist_ok=True)

    copied_files = []
    moved_files = []

    for source_file in source_files:
        dest_file = to_dir / source_file.name

        # Perform copy or move
        if transition_config.action == "copy":
            shutil.copy2(source_file, dest_file)
            copied_files.append(dest_file)
        elif transition_config.action == "move":
            shutil.move(str(source_file), str(dest_file))
            moved_files.append(dest_file)

        # Set destination permissions
        if transition_config.destination_file_permissions:
            perms = int(transition_config.destination_file_permissions, 8)
            os.chmod(dest_file, perms)

    # Set source permissions if copy and source_file_permissions specified
    if transition_config.action == "copy" and transition_config.source_file_permissions:
        perms = int(transition_config.source_file_permissions, 8)
        for source_file in source_files:
            if source_file.exists():  # Still exists after copy
                os.chmod(source_file, perms)

    # Handle metadata
    if to_stage_config.auto_create_metadata:
        _update_metadata(
            to_dir=to_dir,
            path=path,
            from_stage=from_stage_config.name,
            from_dir=from_dir,
            transition_config=transition_config,
        )

    return {
        "action": transition_config.action,
        "files_copied": [str(f.name) for f in copied_files],
        "files_moved": [str(f.name) for f in moved_files],
        "from_stage": from_stage_config.name,
        "to_stage": to_stage_config.name,
    }


def _update_metadata(
    to_dir: Path,
    path: str,
    from_stage: str,
    from_dir: Path,
    transition_config,
) -> None:
    """
    Create or update metadata in destination directory.

    Args:
        to_dir: Destination directory
        path: Content path
        from_stage: Source stage name
        from_dir: Source directory
        transition_config: Transition configuration
    """
    metadata_file = to_dir / ".metadata.json"

    # Load existing metadata if it exists
    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text())
    else:
        metadata = {}

    # Get source metadata if copy_metadata is True
    if transition_config.copy_metadata:
        source_metadata_file = from_dir / ".metadata.json"
        if source_metadata_file.exists():
            source_metadata = json.loads(source_metadata_file.read_text())
            if path in source_metadata:
                metadata[path] = source_metadata[path].copy()

    # Initialize item metadata if not present
    if path not in metadata:
        metadata[path] = {}

    # Set fields from metadata_fields_to_set
    if transition_config.metadata_fields_to_set:
        for key, value in transition_config.metadata_fields_to_set.items():
            # Handle template substitution
            if value == "{timestamp}":
                value = datetime.now().isoformat()
            elif value == "{user}":
                import getpass

                value = getpass.getuser()

            metadata[path][key] = value

    # Write metadata back
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
