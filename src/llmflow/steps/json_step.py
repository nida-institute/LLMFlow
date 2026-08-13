"""JSON step handler — assemble a structured value from context variables."""

from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve

logger = Logger()


def run_json_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    """Resolve value and store in context under outputs."""
    name = step.get("name", "unnamed")
    output_var = step.get("output")
    if not output_var:
        raise ValueError(f"json step '{name}' requires an 'outputs' key")
    value = step.get("value")
    context[output_var] = resolve(value, context)
    logger.info(f"✅ json step '{name}': stored in context['{output_var}']")
