"""Save step handler — write content to disk."""

from typing import Any, Dict, Optional

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.file_io import _record_written_file, save_content_to_file

logger = Logger()


def run_save_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> None:
    """Execute a save step to write content to a file."""
    name = step.get("name", "unnamed")
    logger.info(f"💾 Starting save step: {name}")

    path = resolve(step.get("path", "output.txt"), context)
    content_value = step.get("content")
    content = resolve(content_value, context) if content_value else context.get("content", "")

    saved_path = save_content_to_file(content, str(path))
    _record_written_file(saved_path)

    logger.info(f"✅ Completed save step: {name}")
