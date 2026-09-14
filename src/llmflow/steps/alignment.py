"""`type: alignment` — the translation's text for a span named by source word ids.

The step resolves a registered pair, reads its three files, and returns one result per span in
the order asked. Rulings are in `project/plans/design-scripture-alignments.md`.
"""
from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.alignment import aligned_text_for_spans, load_pair
from llmflow.utils.context import resolve
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()


def _registered_pair(source_docid: str, target_docid: str) -> Dict[str, Any]:
    """The registration for this pair, or a loud error naming what is registered.

    Pairs resolve through the same store `type: scripture` uses, so a pipeline names a pair and
    the engine decides where it lives — the reason the scripture step exists rather than a path
    written into YAML.
    """
    from llmflow.utils.scripture import load_registry_resources

    registered = load_registry_resources()
    for definition in registered.values():
        if str(definition.get("kind", "")).lower() != "alignment":
            continue
        if definition.get("source") == source_docid and definition.get("target") == target_docid:
            return definition

    available = sorted(
        f"{d.get('source')}->{d.get('target')}"
        for d in registered.values()
        if str(d.get("kind", "")).lower() == "alignment"
    )
    raise ValueError(
        f"no registered alignment for {source_docid!r} -> {target_docid!r}. "
        f"Registered: {', '.join(available) if available else 'none'}"
    )


def run_alignment_step(
    step: Dict[str, Any],
    context: Dict[str, Any],
    pipeline_config: Dict[str, Any] | None = None,
) -> None:
    name = step.get("name", "unnamed")
    logger.info(f"🔗 Starting alignment step: {name}")

    source_docid = step.get("source")
    target_docid = step.get("target")
    if not source_docid or not target_docid:
        raise ValueError(
            f"alignment step '{name}' requires both 'source' and 'target'. "
            "An alignment is directional and neither side is inferred."
        )

    spans = resolve(step.get("spans"), context) if step.get("spans") else []
    if not spans:
        raise ValueError(f"alignment step '{name}' requires 'spans'")

    pair = load_pair(_registered_pair(source_docid, target_docid))
    results = aligned_text_for_spans(
        spans,
        pair["document"],
        pair["source"],
        pair["target"],
        order=tuple(step.get("order") or ("target",)),
        returns=tuple(step.get("returns") or ("text",)),
    )

    logger.info(f"   {len(results)} spans, {source_docid} -> {target_docid}")
    handle_step_outputs(step, results, context)
