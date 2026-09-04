"""Plugin step handler."""

import types
from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.plugins import plugin_registry
from llmflow.utils.context import resolve

logger = Logger()


def run_plugin_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> Any:
    """Execute a plugin step."""
    name = step.get("name", "unnamed")
    step_type = step.get("type")

    logger.info(f"🔌 Starting plugin step: {name}")

    if step_type is None:
        raise ValueError(f"Plugin step '{name}' has no type")

    try:
        plugin_func = plugin_registry[step_type]
        plugin_config = {k: resolve(v, context) for k, v in step.items()}

        results = plugin_func(plugin_config)

        if isinstance(results, types.GeneratorType):
            results = list(results)

        if isinstance(results, str) and (
            results.endswith('.md') or results.endswith('.usx')
            or results.endswith('.json') or '/' in results
        ):
            logger.info(f"📄 Created file: {results}")

        logger.info(f"✅ Completed plugin step: {name}")
        return results

    except Exception as e:
        logger.error(f"❌ Error in {step_type} step '{name}': {e}")
        raise
