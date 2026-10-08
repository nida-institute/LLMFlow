"""Which resources a pipeline needs, and which of them this machine cannot open yet (#261).

The same move `schema_preflight` made for structured-output schemas, applied to a different
dependency: what failed part-way through a run, after earlier steps had been paid for, is found by
lint before anything runs.

Pure: reads the pipeline and the registry and writes nothing. Offering to install what is missing
is the command line's, because only a command knows whether there is a person to ask.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

#: The `include:` families that read a path the registration must name, and the
#: `sp resource set` option that names it.
FAMILY_PATHS = {
    "syntax": ("lowfat_path", "--lowfat-path"),
    "discourse": ("discourse_path", "--discourse-path"),
}

#: Step types whose `resource:` names a registered resource.
RESOURCE_STEPS = ("scripture", "parallel-passages")


@dataclass
class Finding:
    """One thing a pipeline needs that this machine does not have.

    `kind` is `unregistered`, `missing-path`, `no-terms`, `dataset` or `unresolved`. Only the
    first two and `dataset` are errors; a resource with no licence record opens, and a resource
    named by a variable lint cannot resolve is checked when the run resolves it.
    """

    kind: str
    resource: str
    message: str
    in_catalog: bool = False
    family: Optional[str] = None
    fix: Optional[str] = None
    #: Named only by steps under a `condition:`, which lint cannot evaluate. The run may never
    #: reach them, so the run can succeed without the resource: reported and offered, not refused.
    conditional: bool = False

    @property
    def is_error(self) -> bool:
        return self.kind in ("unregistered", "missing-path", "dataset") and not self.conditional


@dataclass
class Needs:
    """What the pipeline names: resources with the families each is asked for, and datasets.

    `unconditional` holds the resources, and `(resource, family)` pairs, that at least one step
    names outside any `condition:` — a resource can be needed always and one of its families only
    in a branch.
    """

    resources: Dict[str, set] = field(default_factory=dict)
    unconditional: set = field(default_factory=set)
    unresolved: List[str] = field(default_factory=list)
    datasets: List[str] = field(default_factory=list)


def _walk(steps: Iterable[Any], conditional: bool = False) -> Iterable[tuple]:
    """`(step, conditional)` for every step, nested ones included; a step is conditional when it
    or a step enclosing it carries a `condition:`."""
    for step in steps or []:
        if not isinstance(step, Mapping):
            continue
        guarded = conditional or bool(step.get("condition"))
        yield step, guarded
        if isinstance(step.get("steps"), list):
            yield from _walk(step["steps"], guarded)


def needs(steps: Iterable[Any], context: Mapping[str, Any]) -> Needs:
    """Every resource and dataset *steps* name, with `${var}` resolved against *context*."""
    from llmflow.utils.context import resolve

    found = Needs()
    for step, conditional in _walk(steps):
        kind = step.get("type")
        if kind in RESOURCE_STEPS and step.get("resource"):
            raw = step["resource"]
            try:
                name = resolve(raw, dict(context))
            except Exception:
                name = raw
            name = str(name)
            if "${" in name:
                if str(raw) not in found.unresolved:
                    found.unresolved.append(str(raw))
                continue
            families = found.resources.setdefault(name, set())
            if not conditional:
                found.unconditional.add(name)
            include = step.get("include")
            if kind == "scripture" and isinstance(include, list):
                families.update(str(member) for member in include)
                if not conditional:
                    found.unconditional.update((name, str(member)) for member in include)
        elif kind == "alignment":
            from llmflow.steps.alignment import declared_pairs

            try:
                dataset = declared_pairs().get("dataset")
            except (FileNotFoundError, ValueError):
                continue
            if dataset and dataset not in found.datasets:
                found.datasets.append(str(dataset))
    return found


def check(steps: Iterable[Any], context: Mapping[str, Any]) -> List[Finding]:
    """What the pipeline needs and this machine cannot yet supply, in the order it is named."""
    from llmflow import resources as _resources

    wanted = needs(steps, context)
    registered = _resources.load_registered()
    readable = _resources.readable()
    findings: List[Finding] = []

    for name, families in wanted.resources.items():
        conditional = name not in wanted.unconditional
        only_if = " It is named only under a `condition:`, so it is needed only if that holds." if conditional else ""
        if name not in registered:
            in_catalog = name in readable
            fix = f"sp resource add {name}" if in_catalog else f"sp resource add {name} --path <where it is>"
            known = ", ".join(sorted(registered)) or "(none registered)"
            findings.append(Finding(
                "unregistered", name,
                f"Resource {name!r} is not registered (registered: {known}). Register it: "
                f"`{fix}`.{only_if}",
                in_catalog=in_catalog, fix=fix, conditional=conditional,
            ))
            continue
        entry = registered[name]
        for family in sorted(families & set(FAMILY_PATHS)):
            key, option = FAMILY_PATHS[family]
            if _names_a_path(entry, key):
                continue
            family_conditional = (name, family) not in wanted.unconditional
            fix = f"sp resource set {name} {option} <dataset-relative path, or a dataset id/subpath>"
            findings.append(Finding(
                "missing-path", name,
                f"Resource {name!r} is asked for `{family}`, and its registration names no "
                f"{key} that exists. Record it: `{fix}`."
                + (" It is asked for only under a `condition:`, so it is needed only if that "
                   "holds." if family_conditional else ""),
                family=family, fix=fix, conditional=family_conditional,
            ))
        if not isinstance(entry.get("terms"), Mapping) and name in readable:
            findings.append(Finding(
                "no-terms", name,
                f"Resource {name!r} has no record of its licence — registered before licences "
                f"were recorded. `sp lint` offers it; `--accept-terms` records it without asking.",
                in_catalog=True,
            ))

    for dataset in wanted.datasets:
        if not _resources.dataset_registration(dataset):
            fix = f"sp dataset add {dataset} --path <where it is>"
            findings.append(Finding(
                "dataset", dataset,
                f"The alignment corpus {dataset!r} is not registered as a dataset. Register it: `{fix}`",
                fix=fix,
            ))

    for raw in wanted.unresolved:
        findings.append(Finding(
            "unresolved", raw,
            f"A resource is named by {raw}, which lint cannot resolve; the run checks it when it "
            f"resolves.",
        ))
    return findings


def _names_a_path(entry: Mapping[str, Any], key: str) -> bool:
    from llmflow import resources as _resources

    if not entry.get(key):
        return False
    try:
        return _resources.resolve_declared_path(entry[key], entry).exists()
    except ValueError:
        return False


def table(findings: Iterable[Finding]) -> str:
    """The resources a pipeline needs and cannot yet use, one line per finding."""
    lines = ["Resources this pipeline needs:"]
    for finding in findings:
        if finding.kind == "unregistered":
            status = "NOT REGISTERED" + (" — needed only if its condition holds" if finding.conditional else "")
        elif finding.kind == "missing-path":
            status = f"{finding.family} — no {FAMILY_PATHS[str(finding.family)][0]}"
        elif finding.kind == "no-terms":
            status = "registered, no licence recorded"
        elif finding.kind == "dataset":
            status = "dataset NOT REGISTERED"
        else:
            status = "named by a variable; checked at run time"
        lines.append(f"  {finding.resource:<12} {status}")
        if finding.fix and finding.kind != "unregistered":
            lines.append(f"  {'':<12} {finding.fix}")
    return "\n".join(lines)
