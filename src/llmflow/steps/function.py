"""Function step handler."""

import importlib
import inspect
from typing import Any, Dict, Optional

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def run_function_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> Any:
    """Execute a function step and return its result."""
    name = step.get("name", "unnamed")
    function_name = step["function"]
    inputs = step.get("inputs", {})

    logger.info(f"🔧 Starting function step: {name}")

    module_name, func_name = function_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    func = getattr(module, func_name)

    sig = inspect.signature(func)

    if isinstance(inputs, dict):
        resolved_inputs = {key: resolve(value, context) for key, value in inputs.items()}
        result = func(**resolved_inputs, context=context) if "context" in sig.parameters else func(**resolved_inputs)
    elif isinstance(inputs, list):
        resolved_args = [resolve(value, context) for value in inputs]
        result = func(*resolved_args, context=context) if "context" in sig.parameters else func(*resolved_args)
    else:
        result = func(context=context) if "context" in sig.parameters else func()

    handle_step_outputs(step, result, context)

    logger.info(f"✅ Completed function step: {name}")
    return result
