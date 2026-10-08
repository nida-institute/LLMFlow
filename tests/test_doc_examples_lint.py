"""Guardrail: YAML examples in documentation must use real step keywords.

This catches the class of bug where a doc example uses a key that the runtime
silently ignores — e.g. `group_by:` (should be `group-by:`) or a removed alias
like `item_var:`/`input:` (should be `for:`/`in:`). Such examples teach users
to write pipelines that fail silently, and they are never otherwise linted.

Validation is intentionally *key-level only* (not full-pipeline structure) so
that partial snippets — a lone step with no `name`/`steps` — do not
false-positive. A block can opt out with a `# lint-doc: skip` marker.
"""
import re
from pathlib import Path

import pytest

from llmflow.pipeline_schema import allowed_step_keys, declared_step_types
from llmflow.utils.linter import COMMON_TYPOS, validate_output_members

REPO_ROOT = Path(__file__).resolve().parent.parent

# Dicts whose `type` is one of these are treated as pipeline steps and key-checked.
KNOWN_STEP_TYPES = declared_step_types()

# Files whose ```yaml fenced blocks we validate: all docs, the shipped project
# documentation templates, and the embedded help/tutorial YAML in cli_utils.py.
_FENCE_RE = re.compile(r"```ya?ml\n(.*?)```", re.DOTALL)


def _iter_yaml_blocks():
    sources = list((REPO_ROOT / "docs").rglob("*.md"))
    sources += list((REPO_ROOT / "src" / "llmflow" / "templates" / "project" / "docs").rglob("*.md"))
    sources.append(REPO_ROOT / "src" / "llmflow" / "cli_utils.py")
    for path in sources:
        text = path.read_text(encoding="utf-8")
        for block in _FENCE_RE.findall(text):
            if "lint-doc: skip" in block:
                continue
            yield path, block


def _walk_steps(node):
    """Yield every dict that looks like a pipeline step (type in KNOWN_STEP_TYPES).

    `type` is not always a step type or even a string: the docs also contain JSON Schema
    fragments, where `type: ["string", "null"]` is the documented way to spell an optional
    field under OpenAI strict mode. Guard the membership test, or an unhashable list
    raises TypeError here.
    """
    if isinstance(node, dict):
        node_type = node.get("type")
        if isinstance(node_type, str) and node_type in KNOWN_STEP_TYPES:
            yield node
        for v in node.values():
            yield from _walk_steps(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_steps(v)


def test_doc_yaml_examples_use_known_step_keys():
    import yaml

    violations = []
    for path, block in _iter_yaml_blocks():
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError:
            # Illustrative / non-parseable snippet (e.g. contains {{templates}}); skip.
            continue
        for step in _walk_steps(parsed):
            name = step.get("name", "<unnamed>")
            # Per-type: a key that is real but wrong for this step's type is exactly the
            # silently-ignored case doc examples must not teach.
            allowed = allowed_step_keys(step.get("type"))
            if allowed is None:
                continue  # plugin / registered type — keys cannot be enumerated
            for key in step:
                if key not in allowed:
                    hint = COMMON_TYPOS.get(key)
                    rel = path.relative_to(REPO_ROOT)
                    msg = f"{rel}: step '{name}' (type: {step.get('type')}) uses unknown key '{key}'"
                    if hint:
                        msg += f" — did you mean '{hint}'?"
                    violations.append(msg)

    assert not violations, (
        "Documentation YAML examples use step keys the runtime does not "
        "recognise (they would be silently ignored). Fix the example, or add a "
        "'# lint-doc: skip' comment if the block is intentionally invalid:\n\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_doc_yaml_examples_name_declared_output_members():
    import yaml

    violations = []
    for path, block in _iter_yaml_blocks():
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        rel = path.relative_to(REPO_ROOT)
        violations += [f"{rel}: {e}" for e in validate_output_members(list(_walk_steps(parsed)))]

    assert not violations, (
        "Documentation YAML examples name output members their step type does not "
        "declare, so `sp lint` would refuse them. Fix the example:\n\n"
        + "\n".join(f"  - {v}" for v in violations)
    )
