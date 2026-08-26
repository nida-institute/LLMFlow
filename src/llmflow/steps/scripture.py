"""Scripture step handler — a named edition and a passage in, the requested shape out.

The edition is named, not a path: the engine resolves where it lives. See
project/plans/design-scripture-editions.md.
"""

from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.scripture import edition_text, load_registry_editions
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def run_scripture_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> None:
    """Fetch one passage from one edition, in the format the step asks for."""
    name = step.get("name", "unnamed")
    logger.info(f"📖 Starting scripture step: {name}")

    edition = step.get("edition")
    if not edition:
        raise ValueError(f"scripture step '{name}' requires 'edition'")
    passage = step.get("passage")
    if not passage:
        raise ValueError(f"scripture step '{name}' requires 'passage'")

    edition = str(resolve(edition, context))
    passage = str(resolve(passage, context))
    fmt = str(resolve(step.get("format", "milestones"), context))

    # Absent, the edition's own scheme governs and nothing is mapped.
    scheme = step.get("versification")
    scheme = str(resolve(scheme, context)) if scheme else None

    # The editions directory is overridable so tests need not write to a real ~/.sp.
    editions_dir = (pipeline_config or {}).get("_editions_dir")
    editions = load_registry_editions(editions_dir)

    result = edition_text(
        edition, passage, fmt=fmt, editions=editions, versification=scheme
    )
    size = (
        f"{len(result.get('content') or [])} nodes"
        if isinstance(result, dict)
        else f"{len(result)} chars"
    )
    logger.debug(f"   {edition} {passage}: {size} ({fmt})")

    handle_step_outputs(step, result, context)
    logger.info(f"✅ Completed scripture step: {name}")
