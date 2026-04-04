"""
Content diff functionality.

Compare content versions across stages.
"""

import difflib
from pathlib import Path
from typing import Dict, Any, Optional

from llmflow.utils.content_stages_loader import ContentStagesConfigLoader
from llmflow.modules.logger import Logger

logger = Logger()


def diff_content(
    path: str,
    from_stage: str,
    to_stage: str,
    content_root: Optional[Path] = None,
    config_path: Optional[Path] = None,
    output_to_console: bool = True,
) -> Dict[str, Any]:
    """
    Compare content versions across stages.

    Args:
        path: Relative path to content (without extension)
        from_stage: Source stage name
        to_stage: Destination stage name
        content_root: Root directory for content/ (default: ./content)
        config_path: Optional path to content-stages.yaml
        output_to_console: If True, print diff to console

    Returns:
        Dict with diff result
    """
    try:
        # Determine content root
        if content_root is None:
            content_root = Path.cwd() / "content"

        # Load configuration
        loader = ContentStagesConfigLoader(config_path)

        # Validate stages exist
        from_stage_config = loader.get_stage(from_stage)
        to_stage_config = loader.get_stage(to_stage)

        if not from_stage_config:
            return {
                "success": False,
                "error": f"Source stage '{from_stage}' not found",
            }

        if not to_stage_config:
            return {
                "success": False,
                "error": f"Destination stage '{to_stage}' not found",
            }

        # Normalize path
        path = path.replace("\\", "/")

        # Find files in both stages
        from_dir = content_root / from_stage
        to_dir = content_root / to_stage

        from_file = None
        to_file = None

        # Try to find files with various extensions
        for ext in [".md", ".json", ".txt", ""]:
            candidate_from = from_dir / f"{path}{ext}"
            candidate_to = to_dir / f"{path}{ext}"

            if candidate_from.exists() and candidate_from.is_file():
                from_file = candidate_from
            if candidate_to.exists() and candidate_to.is_file():
                to_file = candidate_to

            if from_file and to_file:
                break

        if not from_file:
            return {
                "success": False,
                "error": f"File '{path}' not found in {from_stage} stage",
            }

        if not to_file:
            return {
                "success": False,
                "error": f"File '{path}' not found in {to_stage} stage",
            }

        # Read file contents
        from_content = from_file.read_text(encoding="utf-8").splitlines(keepends=True)
        to_content = to_file.read_text(encoding="utf-8").splitlines(keepends=True)

        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            from_content,
            to_content,
            fromfile=f"{from_stage}/{from_file.name}",
            tofile=f"{to_stage}/{to_file.name}",
            lineterm=""
        ))

        has_differences = len(diff_lines) > 0

        # Output to console if requested
        if output_to_console:
            if has_differences:
                print(f"\nDiff: {from_stage} → {to_stage}")
                print(f"Path: {path}")
                print("=" * 60)
                for line in diff_lines:
                    print(line)
            else:
                print(f"\n✓ Files are identical")
                print(f"  {from_stage}/{from_file.name}")
                print(f"  {to_stage}/{to_file.name}")

        return {
            "success": True,
            "from_stage": from_stage,
            "to_stage": to_stage,
            "from_file": str(from_file),
            "to_file": str(to_file),
            "has_differences": has_differences,
            "diff_lines": diff_lines if not output_to_console else [],
        }

    except Exception as e:
        logger.error(f"Failed to diff content: {e}")
        return {
            "success": False,
            "error": str(e),
        }
