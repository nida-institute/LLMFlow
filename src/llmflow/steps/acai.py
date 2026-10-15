"""`type: acai` — the people, places and things ACAI names in a passage (#272).

ACAI is an analysis of SBLGNT and WLC. Asked against another resource the step answers `null`
and says why, because its alignment to one text's words does not carry over to another's.

The reading and the payload are `utils.acai`; this module resolves the named resource, finds the
registered dataset, and puts the answer in the context.
"""

from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.context import resolve
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def run_acai_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> None:
    from llmflow import resources as _resources
    from llmflow.utils.acai import acai_payload, declaration
    from llmflow.utils.scripture import load_registry_resources, resolve_resource

    name = step.get("name", "unnamed")
    logger.info(f"🗺️  Starting acai step: {name}")

    resource = resolve(step.get("resource"), context)
    passage = resolve(step.get("passage"), context)
    if not resource or not passage:
        raise ValueError(
            f"acai step '{name}' requires both 'resource' and 'passage'. The resource says which "
            "text ACAI is read against — SBLGNT or WLC; the passage is what entities are sought for."
        )

    declared = declaration()
    if resource not in declared["resources"]:
        logger.warning(
            f"acai step '{name}': ACAI is an analysis of {' and '.join(declared['resources'])}, "
            f"not of {resource!r}, so the step answers null. Name one of those as the resource."
        )
        handle_step_outputs(step, None, context)
        return

    dataset = declared["dataset"]
    registration = _resources.dataset_registration(dataset)
    root = registration.get("path") if registration else None
    if not root:
        raise ValueError(
            f"acai step '{name}' reads ACAI from the dataset {dataset!r}, which is not registered "
            f"on this machine. Register a clone of BibleAquifer/ACAI: "
            f"`sp dataset add {dataset} --path <clone>`."
        )

    registrations_dir = (pipeline_config or {}).get("_resources_dir")
    definition = resolve_resource(resource, load_registry_resources(registrations_dir))
    versification = resolve(step.get("versification"), context) or (
        definition.get("versification_scheme") if isinstance(definition, dict) else None
    ) or declared["versification"]

    result = acai_payload(passage, root, versification)
    logger.info(f"   {len(result['entities'])} entities in {passage}")
    handle_step_outputs(step, result, context)
