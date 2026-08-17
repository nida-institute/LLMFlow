"""Scripture step handler — a named edition and a passage, in, running text out.

Why a step rather than `type: function`: an edition is *named*, and the engine resolves where
it lives. Absolute paths written into pipeline YAML are why the `ears-to-hear` and
`discourse-flow` pipelines run on one laptop, and a source chosen in code is a source chosen
by whoever wrote the code — which is the Captain's decision, expressed as configuration.

See project/plans/design-scripture-editions.md and LLMFlow#200.
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
    """Fetch running text for one passage in one edition."""
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

    # The editions directory is overridable so tests need not write to a real ~/.sp.
    editions_dir = (pipeline_config or {}).get("_editions_dir")
    editions = load_registry_editions(editions_dir)

    text = edition_text(edition, passage, fmt=fmt, editions=editions)
    logger.debug(f"   {edition} {passage}: {len(text)} chars ({fmt})")

    handle_step_outputs(step, text, context)
    logger.info(f"✅ Completed scripture step: {name}")
