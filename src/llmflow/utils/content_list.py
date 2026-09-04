"""
Content listing functionality.

Lists all files in a content stage with optional metadata.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from llmflow.modules.logger import Logger
from llmflow.utils.content_stages_loader import (
    ContentStagesConfigLoader,
)

logger = Logger()


def list_content(
    stage: str,
    content_root: Optional[Path] = None,
    config_path: Optional[Path] = None,
    with_metadata: bool = False,
) -> Dict[str, Any]:
    """
    List all content files in a stage.

    Args:
        stage: Stage name
        content_root: Root directory for content/ (default: ./content)
        config_path: Optional path to content-stages.yaml
        with_metadata: If True, include metadata for each file

    Returns:
        Dict with file list and summary statistics
    """
    try:
        # Determine content root
        if content_root is None:
            content_root = Path.cwd() / "content"

        # Load configuration
        loader = ContentStagesConfigLoader(config_path)

        # Validate stage exists
        stage_config = loader.get_stage(stage)
        if not stage_config:
            return {
                "success": False,
                "error": f"Stage '{stage}' not found",
            }

        # Get stage directory
        stage_dir = content_root / stage
        if not stage_dir.exists():
            return {
                "success": True,
                "stage": stage,
                "files": [],
                "summary": {
                    "total_files": 0,
                    "total_size": 0,
                }
            }

        # Load metadata if requested
        metadata_map = {}
        if with_metadata:
            metadata_file = stage_dir / ".metadata.json"
            if metadata_file.exists():
                try:
                    metadata_map = json.loads(metadata_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, KeyError):
                    logger.warning(f"Failed to load metadata from {metadata_file}")

        # Collect all files (excluding metadata files)
        files = []
        total_size = 0

        for file_path in sorted(stage_dir.rglob("*")):
            if file_path.is_file() and file_path.name != ".metadata.json" and not file_path.name.startswith("."):
                # Get relative path from stage directory
                rel_path = file_path.relative_to(stage_dir)

                # Get file stats
                stat = file_path.stat()

                file_info = {
                    "path": str(rel_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }

                # Add metadata if available
                if with_metadata:
                    # Try path without extension
                    path_key = str(rel_path.with_suffix(""))
                    if path_key in metadata_map:
                        file_info["metadata"] = metadata_map[path_key]
                    else:
                        file_info["metadata"] = None

                files.append(file_info)
                total_size += stat.st_size

        return {
            "success": True,
            "stage": stage,
            "files": files,
            "summary": {
                "total_files": len(files),
                "total_size": total_size,
            }
        }

    except Exception as e:
        logger.error(f"Failed to list content: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def format_content_list(result: Dict[str, Any], json_output: bool = False) -> str:
    """
    Format content list for display.

    Args:
        result: Result dict from list_content()
        json_output: If True, return JSON; otherwise human-readable

    Returns:
        Formatted string
    """
    if json_output:
        return json.dumps(result, ensure_ascii=False, indent=2)

    # Human-readable format
    if not result.get("success"):
        return f"❌ Error: {result.get('error', 'Unknown error')}"

    output = []
    stage = result.get("stage", "unknown")
    files = result.get("files", [])
    summary = result.get("summary", {})

    output.append(f"Content in Stage: {stage}")
    output.append("=" * 60)

    if not files:
        output.append("\n(No files in this stage)")
    else:
        output.append(f"\nTotal: {summary.get('total_files', 0)} files, {summary.get('total_size', 0)} bytes\n")

        for file_info in files:
            path = file_info["path"]
            size = file_info["size"]
            modified = file_info["modified"]

            output.append(f"• {path}")
            output.append(f"  Size: {size} bytes, Modified: {modified}")

            # Show metadata if included
            metadata = file_info.get("metadata")
            if metadata:
                output.append("  Metadata:")
                for key, value in metadata.items():
                    output.append(f"    {key}: {value}")

    return "\n".join(output)
