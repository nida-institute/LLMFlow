"""`type: parallel-passages` — which groups in the UBS database a passage takes part in.

A group states that several passages are parallel, or that one quotes another. That is a
relation *between* passages rather than an analysis of one passage's words, which is why this
is a step of its own and not an `include:` family on `type: scripture` (#258).

The reading and the payload are `utils.parallel_passages`; this module resolves the named
resource and puts the answer in the context.
"""

from typing import Any, Dict, List

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.parallel_passages import parallel_passages_payload
from llmflow.utils.scripture import load_registry_resources, resolve_resource
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()

#: What a result may carry. `words` is declared so the language names the whole surface and a
#: misspelling is a lint error, and refused at run time until the identifier join exists.
RETURNS = ("references", "words")


def run_parallel_passages_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> None:
    name = step.get("name", "unnamed")
    logger.info(f"🔗 Starting parallel-passages step: {name}")

    resource = resolve(step.get("resource"), context)
    passage = resolve(step.get("passage"), context)
    if not resource or not passage:
        raise ValueError(
            f"parallel-passages step '{name}' requires both 'resource' and 'passage'. "
            "The resource says which text the answer is expressed against; the passage is "
            "what parallels are sought for."
        )

    returns: List[str] = list(step.get("returns") or ["references"])
    unknown = [item for item in returns if item not in RETURNS]
    if unknown:
        raise ValueError(
            f"parallel-passages step '{name}': {', '.join(unknown)} is not something this "
            f"step returns. Choose from {', '.join(RETURNS)}."
        )
    if "words" in returns:
        raise ValueError(
            f"parallel-passages step '{name}' asked for 'words', and the word-level join is "
            "not built. The database's digits index UBSGNT5, so matching them to this "
            "resource's words needs the MARBLE identifier mapping; counting positions "
            "instead is wrong about one row in eleven, and silently. Ask for 'references' "
            "until the mapping ships (#258)."
        )

    registrations_dir = (pipeline_config or {}).get("_resources_dir")
    definition = resolve_resource(resource, load_registry_resources(registrations_dir))

    result = parallel_passages_payload(
        definition,
        passage,
        resource,
        versification=resolve(step.get("versification"), context) or None,
    )

    logger.info(
        f"   {'no source registered' if result is None else f'{len(result)} groups'} "
        f"for {passage} in {resource}"
    )
    handle_step_outputs(step, result, context)
