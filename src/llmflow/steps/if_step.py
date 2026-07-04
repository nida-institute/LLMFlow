"""If step handler — condition already evaluated by run_step dispatcher."""

from typing import Any, Callable, Dict, Optional

from llmflow.modules.logger import Logger

logger = Logger()


def run_if_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None,
    run_step_fn: Callable,
) -> Optional[str]:
    """Execute an if step — condition already evaluated true by run_step dispatcher."""
    nested_steps = step.get("steps", [])
    name = step.get("name", "unnamed")

    logger.debug(f"✅ Condition true for '{name}', running nested steps")

    if nested_steps:
        logger.debug(f"   Running {len(nested_steps)} nested steps")
        for nested_step in nested_steps:
            after_action = run_step_fn(nested_step, context, pipeline_config)
            if after_action in ["exit", "continue"]:
                logger.debug(f"   Propagating after action: {after_action}")
                return after_action

    return None
