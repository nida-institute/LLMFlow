"""BaseX step handler."""

from typing import Any, Dict

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

    raw_inputs = step.get("inputs", {}) or {}
    resolved_inputs = {k: resolve(v, context) for k, v in raw_inputs.items()}

    # `database:` binds $database in the query — the keyword and the XQuery variable are
    # deliberately the same word (LLMFlow#189). Before this, `database:` was required by
    # the linter and then discarded, so queries hardcoded the database name and changing
    # the pipeline changed nothing.
    #
    # A collision is an error, not a precedence rule: BaseX accepts duplicate -b flags for
    # one variable, silently takes the last, and exits 0 (verified on 12.3). Guessing here
    # would let the YAML name one database while the query read another, and report
    # success. Lint catches this earlier; this guard covers --skip-lint and the Python API.
    if "database" in step:
        if "database" in resolved_inputs:
            raise ValueError(
                f"basex step '{name}': 'database' is set both as a step key and in "
                f"'inputs' — both bind $database. Remove the 'inputs' entry."
            )
        resolved_inputs["database"] = resolve(step["database"], context)

    if "query_file" not in step:
        raise ValueError(f"basex step '{name}' requires 'query_file'")
    query_file = resolve(step["query_file"], context)

    timeout = step.get("timeout_seconds", 120)

    result = run_basex(str(query_file), inputs=resolved_inputs or None, timeout=timeout)
    handle_step_outputs(step, result, context)

    logger.info(f"✅ Completed basex step: {name}")
