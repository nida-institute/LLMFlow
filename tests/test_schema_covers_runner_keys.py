"""Third-loop guard (project/plans/design-schema-single-source.md).

`PIPELINE_SCHEMA` must declare every step-config key the engine actually reads. The drift test
(`test_pipeline_model.py`) guards schema ↔ object-model; this guards schema ↔ runner — the loop
a key missing from *both* the schema and the model would otherwise hide (looks like agreement).
Reported by ears-to-hear, 2026-08-12.
"""
import pathlib
import re

from llmflow.pipeline_schema import PIPELINE_SCHEMA

# Top-level `step.get(...)` reads that are NOT step-config vocabulary — engine internals,
# pipeline-level keys, or a nested structure read directly by one handler.
_NOT_STEP_KEYS = {
    "pipeline",   # pipeline-level, not a step key
    "variables",  # pipeline-level
    "_tag",       # engine-internal marker set by the runner, never written in YAML
    "step",       # the inner `step:` of a !window_advance tagged item, not a top-level key
    "cursor",     # ditto — a key of the tagged sub-item, not of a step
}

# Hyphens included: `group-by` / `order-by` are real step keys, and a `[a-zA-Z_]`-only
# pattern silently skips them — exactly the blind spot this guard exists to close.
_STEP_READ = re.compile(r"\b(?:step|step_config)\.get\(\s*['\"]([a-zA-Z_][\w-]*)['\"]")


def _declared_step_keys() -> set:
    """Property names declared for a step — common properties plus any per-type branch
    (``allOf``/``if``/``then`` …) properties. Does not descend into a property's own value
    schema, so nested keys like ``saveas.path`` are not counted as top-level step keys.
    """
    keys: set = set()

    def collect(node) -> None:
        if not isinstance(node, dict):
            return
        props = node.get("properties")
        if isinstance(props, dict):
            keys.update(props)
        for kw in ("allOf", "anyOf", "oneOf"):
            for sub in node.get(kw, []) or []:
                collect(sub)
        for kw in ("if", "then", "else", "not"):
            if kw in node:
                collect(node[kw])

    collect(PIPELINE_SCHEMA["properties"]["steps"]["items"])
    return keys


def _keys_engine_reads() -> dict:
    """Every step key read anywhere in the engine, mapped to the files that read it.

    ``utils/`` and ``modules/`` are scanned as well as ``steps/``, ``runner.py`` and
    ``plugins/``: step handlers hand the step dict to helpers (``utils/data.py`` reads the
    loader filters ``key``/``where``/``limit``/``offset``/``columns``/``xpath``/
    ``namespaces``/``output_format``; ``modules/mcp.py`` reads ``mcp``). Scanning only the
    handlers is what let those keys stay out of the schema in the first place.
    """
    keys: dict = {}
    roots = (
        list(pathlib.Path("src/llmflow/steps").glob("*.py"))
        + [pathlib.Path("src/llmflow/runner.py")]
        + list(pathlib.Path("src/llmflow/plugins").glob("*.py"))
        + list(pathlib.Path("src/llmflow/utils").glob("*.py"))
        + list(pathlib.Path("src/llmflow/modules").glob("*.py"))
    )
    for f in roots:
        for m in _STEP_READ.finditer(f.read_text(encoding="utf-8")):
            keys.setdefault(m.group(1), set()).add(f.name)
    return keys


def test_schema_declares_every_step_key_the_engine_reads():
    declared = _declared_step_keys()
    read = _keys_engine_reads()
    missing = {
        k: v for k, v in read.items()
        if k not in declared and k not in _NOT_STEP_KEYS
    }
    assert not missing, (
        "Step keys the engine reads but PIPELINE_SCHEMA does not declare:\n"
        + "\n".join(f"  {k:22} <- {', '.join(sorted(v))}" for k, v in sorted(missing.items()))
    )
