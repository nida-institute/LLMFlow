"""JSON step handler — assemble a structured value from context variables."""

from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def run_json_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    """Resolve `value` and bind it to `output`, applying `saveas` and `append_to`."""
    name = step.get("name", "unnamed")
    output_var = step.get("output")
    if not output_var:
        raise ValueError(f"json step '{name}' requires an 'outputs' key")
    handle_step_outputs(step, resolve(step.get("value"), context), context)
    logger.info(f"✅ json step '{name}': stored in context['{output_var}']")
