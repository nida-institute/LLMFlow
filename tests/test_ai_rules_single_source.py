"""The two rules documents must be rendered from one source, and be current with it.

Two documents state this project's rules: the one `sp init` writes into a new project
(`llmflow.cli_utils.AI_RULES_DOC`) and this repository's own `docs/ai-context/sp/rules.md`,
written by `tools/update_ai_context.py`. Each once held its own hand-maintained list — 17 items
in the tool, a different 12 in `cli_utils` — so which rules a project was held to depended on
which generator last ran, and `sp doctor` would replace one set with the other without saying
which text it considered authoritative.

Rules that existed in only one of the two when that was found:

| only in the repo's 17 | only in the shipped 12 |
|---|---|
| the authorization workflow | avoid destructive changes |
| source text as a named input on every LLM step | `outputs/` requires human review |
| file organisation; plans before implementation | `project/TODO.md` as a session cache |
| audits are diagnostic, not gates | draft GH issues for human approval |
| verses are milestones; four-column boards | nothing is intentional unless the human says so |

**Nothing here parses a rendered document.** An earlier version of this module recovered the
rules from both documents with a regex over markdown list items, and when the rendering changed
shape the regex matched nothing: two empty sets compared equal and every check passed, silently,
for as long as it took someone to change the renderer and notice the suite stayed green.

The subject is taken from the structured source instead — `data/ai-rules.yaml` through
`llmflow.ai_rules` — and each document is checked for the rendered text verbatim. A document
that paraphrases, hand-maintains, or omits a rule fails, and there is no derivation step that
can quietly yield nothing.

**These assert agreement and currency, not content.** Which rules exist, and what they say, is
the Captain's.
"""

from __future__ import annotations

import difflib
import importlib.util
import sys
from pathlib import Path

import pytest

from llmflow import ai_rules
from llmflow.cli_utils import AI_RULES_DOC

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATED_RULES = REPO_ROOT / "docs" / "ai-context" / "sp" / "rules.md"

# `tools/` is not a package, so the generator is loaded by path rather than imported.
_TOOL = REPO_ROOT / "tools" / "update_ai_context.py"
_spec = importlib.util.spec_from_file_location("update_ai_context", _TOOL)
update_ai_context = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = update_ai_context
_spec.loader.exec_module(update_ai_context)


def _documents() -> dict[str, str]:
    """Each rules document by name, so a failure says which one is wrong."""
    return {
        "cli_utils.AI_RULES_DOC (what `sp init` writes)": AI_RULES_DOC,
        str(GENERATED_RULES.relative_to(REPO_ROOT)): GENERATED_RULES.read_text(encoding="utf-8"),
    }


def _rendered_lines(entry: dict) -> list[str]:
    """The lines `render_rules` emits for one rule, taken from the renderer's own output."""
    lines = [f"- `{entry['id']}` — {entry['rule']}"]
    note = (entry.get("note") or "").strip()
    if note:
        lines.append(f"  - _{note}_")
    return lines


#: Diff lines to show before truncating. A whole rules document is ~24,000 characters, and a
#: failure message that long is not read.
DIFF_LIMIT = 40


def _diff(actual: str, expected: str, actual_name: str, expected_name: str) -> str:
    """A unified diff of two texts, truncated, for a failure message.

    Line-based rather than structural on purpose: it says what differs without recovering any
    structure from the rendered text, which is the mistake this module is written to avoid.

    When the comparison is containment rather than equality, the document's frame — title,
    preamble, closing line — appears as removals, because a whole document is being compared
    against the block it contains. Bounded and harmless; narrowing the diff to the aligned
    region would mean locating that region, and machinery in a failure path earns its keep less
    than a few noisy lines cost.
    """
    lines = list(
        difflib.unified_diff(
            actual.splitlines(),
            expected.splitlines(),
            fromfile=actual_name,
            tofile=expected_name,
            lineterm="",
            n=1,
        )
    )
    if not lines:
        return "   (no line differs; the texts differ only in trailing whitespace)"
    shown = lines[:DIFF_LIMIT]
    rendered = "\n".join(f"   {line[:160]}" for line in shown)
    if len(lines) > DIFF_LIMIT:
        rendered += f"\n   … {len(lines) - DIFF_LIMIT} further diff lines not shown"
    return rendered


def test_the_data_declares_rules():
    """The subject of every check below, asserted directly rather than derived."""
    assert ai_rules.entries(), "data/ai-rules.yaml declares no rules"


@pytest.mark.parametrize("name", sorted(_documents()))
def test_each_document_contains_the_rendered_rules_verbatim(name):
    """One renderer, two documents. A paraphrase or a second hand-maintained list fails here.

    Checks the whole rendered block as one string, so ordering and spacing are covered too —
    a document holding the right rules in the wrong order is still two sources.
    """
    document = _documents()[name]
    rendered = ai_rules.render_rules()

    if rendered in document:
        return

    # Not present as a block: name the rules whose text is absent, then show what differs.
    # Both are diagnostics, and both read the declared data rather than the document.
    missing = [
        entry["id"]
        for entry in ai_rules.entries()
        if not all(line in document for line in _rendered_lines(entry))
    ]
    pytest.fail(
        f"{name} does not contain the text `llmflow.ai_rules.render_rules()` produces.\n"
        f"  rules whose rendered text is absent or altered ({len(missing)}): {missing}\n"
        f"  (an empty list here means every rule is present but the block differs in order or "
        f"spacing)\n\n"
        + _diff(document, rendered, name, "llmflow.ai_rules.render_rules()")
        + "\n\nBoth documents must be rendered from `data/ai-rules.yaml`. A second "
        "hand-maintained text is the defect this module exists to prevent, and a paraphrase is "
        "how the weaker wording silently wins."
    )


def test_the_generated_file_is_current_with_its_generator():
    """Agreement between the two renderers says nothing about the file committed to disk.

    Both documents can render identically from the data while the committed file is stale,
    which is what happened when the renderer gained its grouping: the suite stayed green with
    the file still carrying the previous rendering.
    """
    expected = update_ai_context._build_rules_content()
    actual = GENERATED_RULES.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/ai-context/sp/rules.md is out of date with its generator.\n"
        "   Regenerate it: hatch run python tools/update_ai_context.py\n\n"
        + _diff(actual, expected, "docs/ai-context/sp/rules.md", "its generator")
    )
