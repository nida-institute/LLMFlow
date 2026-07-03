"""Debug output directory utilities."""

import shutil
from pathlib import Path
from typing import Any, Dict

from llmflow.utils.context import resolve


def _get_debug_dir(pipeline_config: Dict[str, Any], context: Dict[str, Any], pipeline_name: str = "pipeline") -> str:
    """Return the debug output directory path."""
    import os
    raw = pipeline_config.get("intermediate_file_directory")
    if raw:
        resolved = resolve(str(raw), context)
        return str(Path(str(resolved)) / "debug" / pipeline_name)
    return str(Path(os.getcwd()) / "outputs" / "debug" / pipeline_name)


def _clear_debug_dir(pipeline_config: Dict[str, Any], context: Dict[str, Any], dry_run: bool, pipeline_name: str = "pipeline") -> None:
    """Clear this pipeline's debug subdirectory at pipeline start (skipped on dry_run)."""
    if dry_run:
        return
    debug_dir = Path(_get_debug_dir(pipeline_config, context, pipeline_name))
    if debug_dir.exists():
        shutil.rmtree(debug_dir)
    debug_dir.mkdir(parents=True, exist_ok=True)
