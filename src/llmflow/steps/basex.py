"""BaseX step handler."""

from typing import Any, Dict, Optional

from llmflow.modules.logger import Logger
from llmflow.plugins.basex import run_basex
from llmflow.utils.context import resolve
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def run_basex_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> None:
    """Execute a basex step: run XQuery against a local BaseX database."""
    name = step.get("name", "unnamed")
    logger.info(f"🗄️  Starting basex step: {name}")

    raw_inputs = step.get("inputs", {})
    resolved_inputs = {k: resolve(v, context) for k, v in raw_inputs.items()} if raw_inputs else None

    if "query_file" not in step:
        raise ValueError(f"basex step '{name}' requires 'query_file'")
    query_file = resolve(step["query_file"], context)

    timeout = step.get("timeout_seconds", 120)

    result = run_basex(str(query_file), inputs=resolved_inputs, timeout=timeout)
    handle_step_outputs(step, result, context)

    logger.info(f"✅ Completed basex step: {name}")
