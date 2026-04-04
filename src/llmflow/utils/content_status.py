"""
Content status reporting.

Shows where a content file exists across stages, metadata, and suggests next actions.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from llmflow.utils.content_stages_loader import (
    ContentStagesConfigLoader,
    get_content_stages_config,
)
from llmflow.modules.logger import Logger

logger = Logger()


def get_content_status(
    path: str,
    content_root: Optional[Path] = None,
    config_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Get status of a content file across all stages.

    Args:
        path: Relative path to content (without extension)
        content_root: Root directory for content/ (default: ./content)
        config_path: Optional path to content-stages.yaml

    Returns:
        Dict with status information across all stages
    """
    try:
        # Determine content root
        if content_root is None:
            content_root = Path.cwd() / "content"

        # Load configuration
        loader = ContentStagesConfigLoader(config_path)
        config = loader.config

        # Normalize path
        path = path.replace("\\", "/")

        # Check each stage
        stage_info = []
        for stage_config in config.stages:
            stage_name = stage_config.name
            stage_dir = content_root / stage_name

            # Try to find file with various extensions
            found_file = None
            for ext in [".md", ".json", ".txt", ""]:
                candidate = stage_dir / f"{path}{ext}"
                if candidate.exists() and candidate.is_file():
                    found_file = candidate
                    break

            if found_file:
                # Get file stats
                stat = found_file.stat()

                info = {
                    "name": stage_name,
                    "exists": True,
                    "file_path": str(found_file),
                    "file_size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }

                # Load metadata if available
                metadata_file = stage_dir / ".metadata.json"
                if metadata_file.exists():
                    try:
                        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                        # Get metadata for this specific file (try both with and without subdir)
                        file_key = path.replace("/", "/")  # Keep slashes
                        if file_key in metadata:
                            info["metadata"] = metadata[file_key]
                    except (json.JSONDecodeError, KeyError):
                        pass

                stage_info.append(info)
            else:
                # File doesn't exist in this stage
                stage_info.append({
                    "name": stage_name,
                    "exists": False,
                })

        # Determine authoritative stage (most advanced stage with the file)
        authoritative_stage = None
        for stage_config in reversed(config.stages):  # Check from end (most advanced)
            stage_name = stage_config.name
            if any(s["name"] == stage_name and s["exists"] for s in stage_info):
                authoritative_stage = stage_name
                break

        # Suggest next actions
        next_actions = []
        if authoritative_stage:
            # Find possible transitions from authoritative stage
            for transition in config.transitions:
                if transition.from_stage == authoritative_stage:
                    next_actions.append({
                        "from": transition.from_stage,
                        "to": transition.to_stage,
                        "action": transition.action,
                        "command": f"sp transition {transition.from_stage} {transition.to_stage} {path}"
                    })

        return {
            "success": True,
            "path": path,
            "stages": stage_info,
            "authoritative_stage": authoritative_stage,
            "next_actions": next_actions,
        }

    except Exception as e:
        logger.error(f"Failed to get content status: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def format_status(status: Dict[str, Any], json_output: bool = False) -> str:
    """
    Format status information for display.

    Args:
        status: Status dict from get_content_status()
        json_output: If True, return JSON; otherwise human-readable

    Returns:
        Formatted string
    """
    if json_output:
        return json.dumps(status, ensure_ascii=False, indent=2)

    # Human-readable format
    if not status.get("success"):
        return f"❌ Error: {status.get('error', 'Unknown error')}"

    output = []
    path = status.get("path", "unknown")
    output.append(f"Content Status: {path}")
    output.append("=" * 60)

    stages = status.get("stages", [])
    authoritative = status.get("authoritative_stage")

    for stage in stages:
        name = stage["name"]
        exists = stage.get("exists", False)

        if exists:
            marker = "✓"
            if name == authoritative:
                marker = "★"  # Authoritative version

            file_path = stage.get("file_path", "")
            file_size = stage.get("file_size", 0)
            modified = stage.get("modified", "")

            output.append(f"\n{marker} {name}")
            output.append(f"  Path: {file_path}")
            output.append(f"  Size: {file_size} bytes")
            output.append(f"  Modified: {modified}")

            # Show metadata if available
            metadata = stage.get("metadata")
            if metadata:
                output.append("  Metadata:")
                for key, value in metadata.items():
                    output.append(f"    {key}: {value}")
        else:
            output.append(f"\n✗ {name}")
            output.append(f"  (File not present)")

    # Show next actions
    next_actions = status.get("next_actions", [])
    if next_actions:
        output.append("\nNext Actions:")
        for action in next_actions:
            from_stage = action["from"]
            to_stage = action["to"]
            action_type = action["action"]
            command = action["command"]
            output.append(f"  • {from_stage} → {to_stage} ({action_type})")
            output.append(f"    {command}")

    if authoritative:
        output.append(f"\n★ Authoritative version: {authoritative}")

    return "\n".join(output)
