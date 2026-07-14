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

from llmflow.utils.linter import ALLOWED_STEP_KEYS, COMMON_TYPOS

REPO_ROOT = Path(__file__).resolve().parent.parent

# Dicts whose `type` is one of these are treated as pipeline steps and key-checked.
KNOWN_STEP_TYPES = {
    "llm", "function", "for-each", "window", "if", "json", "save",
    "basex", "duckdb", "plugin", "xpath", "xslt", "tsv",
    "load_json", "load_yaml", "load_xml", "load_csv", "load_tsv",
    "load_text", "load_directory",
}

# Files whose ```yaml fenced blocks we validate: all docs, plus the embedded
# help/tutorial YAML in cli_utils.py (where doc examples also live).
_FENCE_RE = re.compile(r"```ya?ml\n(.*?)```", re.DOTALL)


def _iter_yaml_blocks():
    # docs/ai-context/ is the Captain's domain (AI must not edit it), so it is not
    # validated here — its examples are curated separately.
    sources = [p for p in (REPO_ROOT / "docs").rglob("*.md")
               if "ai-context" not in p.parts]
    sources.append(REPO_ROOT / "src" / "llmflow" / "cli_utils.py")
    for path in sources:
        text = path.read_text(encoding="utf-8")
        for block in _FENCE_RE.findall(text):
            if "lint-doc: skip" in block:
                continue
            yield path, block


def _walk_steps(node):
    """Yield every dict that looks like a pipeline step (type in KNOWN_STEP_TYPES)."""
    if isinstance(node, dict):
        if node.get("type") in KNOWN_STEP_TYPES:
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
            for key in step:
                if key not in ALLOWED_STEP_KEYS:
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
