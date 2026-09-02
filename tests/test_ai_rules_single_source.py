"""`docs/ai-context/sp/rules.md` must have one source, and must be current with it.

Two documents state this project's rules: the one `sp init` writes into a new project
(`llmflow.cli_utils.AI_RULES_DOC`) and this repository's own
`docs/ai-context/sp/rules.md`, written by `tools/update_ai_context.py`. Each once held its own
hand-maintained list — 17 items in the tool, a different 12 in `cli_utils` — so which rules a
project was held to depended on which generator last ran, and `sp doctor` would replace one set
with the other without saying which text it considered authoritative.

Rules that existed in only one of the two when that was found:

| only in the repo's 17 | only in the shipped 12 |
|---|---|
| the authorization workflow | avoid destructive changes |
| source text as a named input on every LLM step | `outputs/` requires human review |
| file organisation; plans before implementation | `project/TODO.md` as a session cache |
| audits are diagnostic, not gates | draft GH issues for human approval |
| verses are milestones; four-column boards | nothing is intentional unless the human says so |

Four checks:
  1. The parse finds every rule the data declares — so no check here can pass vacuously.
  2. Both documents carry every declared rule id.
  3. Each shared rule is worded identically in both.
  4. The generated file matches what its generator produces now.

**These assert agreement and currency, not content.** Which rules exist, and what they say, is
the Captain's; `data/ai-rules.yaml` is where that lives.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

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

#: A rendered rule: `- `some-id` — **Lead.** text`. The id leads because it is the citation;
#: an earlier ordered-list rendering is why the parse below is keyed on it.
RENDERED = re.compile(r"^- `([a-z0-9-]+)` — (.*)$", re.M)


def _rules(text: str) -> dict[str, str]:
    """Rules keyed by id, each collapsed to one line so wording can be compared."""
    return {rule_id: re.sub(r"\s+", " ", body).strip() for rule_id, body in RENDERED.findall(text)}


def _declared_ids() -> set[str]:
    return {entry["id"] for entry in ai_rules.entries()}


def test_the_parse_finds_every_rule_the_data_declares():
    """Without this, every other check here can pass on an empty parse.

    That is not hypothetical: when the rendering moved from a numbered list to an
    id-led one, this module's regex matched nothing, and the two tests below compared two
    empty sets and passed. A guard whose subject can silently become empty is worse than no
    guard, because the triage counts it.
    """
    declared = _declared_ids()
    assert declared, "data/ai-rules.yaml declares no rules"

    for name, text in (("cli_utils.AI_RULES_DOC", AI_RULES_DOC),
                       (str(GENERATED_RULES.relative_to(REPO_ROOT)), GENERATED_RULES.read_text(encoding="utf-8"))):
        parsed = set(_rules(text))
        assert parsed == declared, (
            f"the rule parse in this module does not match what {name} contains.\n"
            f"  declared but not parsed: {sorted(declared - parsed)}\n"
            f"  parsed but not declared: {sorted(parsed - declared)}\n"
            "If the rendering changed, update RENDERED here — until then every check in this "
            "module is measuring nothing."
        )


def test_a_project_and_this_repository_are_held_to_the_same_rules():
    """One source, two documents. Two hand-maintained texts is the defect."""
    shipped = _rules(AI_RULES_DOC)
    generated = _rules(GENERATED_RULES.read_text(encoding="utf-8"))

    only_shipped = sorted(set(shipped) - set(generated))
    only_generated = sorted(set(generated) - set(shipped))

    assert not only_shipped and not only_generated, (
        "docs/ai-context/sp/rules.md and the shipped rules document disagree on which rules "
        "exist.\n"
        f"  in cli_utils.AI_RULES_DOC only ({len(only_shipped)}): {only_shipped}\n"
        f"  in the generated file only ({len(only_generated)}): {only_generated}\n"
        "A project scaffolded by `sp init` is held to the first; this repository to the "
        "second. Derive both from `data/ai-rules.yaml`."
    )


def test_the_two_texts_word_each_shared_rule_identically():
    """Agreeing on which rules exist is not enough if the wording drifts.

    Two copies of one rule in slightly different words is how the shorter one silently becomes
    a weaker version — the failure this repository has hit three times: `.cursorrules` losing
    the `sp run` prohibition, `load-context` paraphrasing `rules.md`, and `design-authority.md`
    shortened across two repositories.
    """
    shipped = _rules(AI_RULES_DOC)
    generated = _rules(GENERATED_RULES.read_text(encoding="utf-8"))

    differing = sorted(key for key in set(shipped) & set(generated) if shipped[key] != generated[key])

    assert not differing, (
        "these rules exist in both documents but are worded differently, so one is a paraphrase "
        f"of the other and will drift: {differing}"
    )


def test_the_generated_file_is_current_with_its_generator():
    """Agreement between the two renderers says nothing about the file on disk.

    Both documents can render identically from the data while the committed file is stale,
    which is what happened when the renderer gained its grouping: the suite stayed green with
    the file still carrying the previous rendering.
    """
    expected = update_ai_context._build_rules_content()
    actual = GENERATED_RULES.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/ai-context/sp/rules.md is out of date with its generator.\n"
        "   Regenerate it: hatch run python tools/update_ai_context.py"
    )
