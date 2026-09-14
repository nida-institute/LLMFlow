"""`type: alignment` — the translation's text for a span named by source word ids.

The step resolves a declared pair, reads its three files, and returns one result per span in
the order asked. Design: `project/plans/design-scripture-alignments.md`.
"""
import importlib.resources
import json
from pathlib import Path
from typing import Any, Dict

from llmflow.modules.logger import Logger
from llmflow.utils.alignment import aligned_text_for_spans, load_pair
from llmflow.utils.context import resolve
from llmflow.utils.step_outputs import handle_step_outputs

logger = Logger()

PATH_KEYS = ("alignment_file", "source_file", "target_file")


def pairs_path() -> Path:
    """Locate `data/alignment-pairs.json`, installed wheel or dev checkout."""
    try:
        ref = importlib.resources.files("llmflow").joinpath("data/alignment-pairs.json")
        path = Path(str(ref))
        if path.exists():
            return path
    except Exception:
        pass
    return Path(__file__).parent.parent.parent.parent / "data" / "alignment-pairs.json"


def declared_pairs() -> Dict[str, Any]:
    """The supported alignments, and the dataset their paths are relative to."""
    path = pairs_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"alignment pairs not declared at {path}. The file states which alignments are "
            "supported and where each one's three files sit inside the alignment corpus."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_pair(source_docid: str, target_docid: str) -> Dict[str, Any]:
    """The declared pair, with its three paths resolved under the registered dataset.

    A path in the declaration is relative to one repository, and the datasets store says where
    that repository is on this machine, so neither half carries a path the other's machine
    cannot use.
    """
    from llmflow import resources

    declaration = declared_pairs()
    dataset = declaration["dataset"]

    registration = resources.dataset_registration(dataset)
    if not registration or not registration.get("path"):
        raise ValueError(
            f"alignment pairs are declared relative to dataset {dataset!r}, which is not "
            f"registered on this machine, so {source_docid!r} -> {target_docid!r} cannot be "
            f"located. Register the alignment corpus under that id."
        )

    for row in declaration["pairs"]:
        if row.get("source") == source_docid and row.get("target") == target_docid:
            resolved = dict(row)
            for key in PATH_KEYS:
                resolved[key] = resources.resolve_declared_path(
                    f"{dataset}/{row[key]}", {"id": f"{source_docid}->{target_docid}"}
                )
            return resolved

    available = sorted(f"{p.get('source')}->{p.get('target')}" for p in declaration["pairs"])
    raise ValueError(
        f"no declared alignment for {source_docid!r} -> {target_docid!r}. "
        f"Declared: {', '.join(available) if available else 'none'}"
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

    pair = load_pair(resolve_pair(source_docid, target_docid))
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
