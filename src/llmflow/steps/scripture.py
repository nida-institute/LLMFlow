"""Scripture step handler — a named resource and a passage in, the requested shape out.

The resource is named, not a path: the engine resolves where it lives. A resource is a readable
text inside a dataset, carrying a reader and a versification. See
project/plans/design-resource-vocabulary.md.
"""

from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.scripture import load_registry_resources, resource_text
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def run_scripture_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> None:
    """Fetch one passage from one resource, in the format the step asks for."""
    name = step.get("name", "unnamed")
    logger.info(f"📖 Starting scripture step: {name}")

    resource = step.get("resource")
    if not resource:
        raise ValueError(f"scripture step '{name}' requires 'resource'")
    passage = step.get("passage")
    if not passage:
        raise ValueError(f"scripture step '{name}' requires 'passage'")

    resource = str(resolve(resource, context))
    passage = str(resolve(passage, context))
    fmt = str(resolve(step.get("format", "milestones"), context))

    # Absent, the resource's own scheme governs and nothing is mapped.
    scheme = step.get("versification")
    scheme = str(resolve(scheme, context)) if scheme else None

    # A list, never a single word: `check_include` rejects a bare string by name.
    include = step.get("include") or ()
    if isinstance(include, (list, tuple)):
        include = [str(resolve(member, context)) for member in include]

    # The registrations directory is overridable so tests need not write to a real ~/.sp.
    registrations_dir = (pipeline_config or {}).get("_resources_dir")
    resources = load_registry_resources(registrations_dir)

    result = resource_text(
        resource, passage, fmt=fmt, resources=resources, versification=scheme, include=include
    )
    size = (
        f"{len(result.get('content') or [])} nodes"
        if isinstance(result, dict)
        else f"{len(result)} chars"
    )
    logger.debug(f"   {resource} {passage}: {size} ({fmt})")

    handle_step_outputs(step, result, context)
    logger.info(f"✅ Completed scripture step: {name}")
