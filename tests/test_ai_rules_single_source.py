"""`docs/ai-context/rules.md` must have one source, not two.

Found 2026-08-21 while checking what `sp doctor` would overwrite. Two generators in this
repository write the same file from two independently hand-maintained texts:

- `tools/update_ai_context.py` — its `RULES` list, 17 items, produces this repo's
  `docs/ai-context/rules.md`
- `llmflow.cli_utils.AI_RULES_DOC` — a *different* 12 items, and what `sp init` writes into
  every new project

Neither derives from the other. So which rules a project is held to depends on which
generator last ran, and `sp doctor` in this repo would replace the 17 with the 12 — silently,
because `data/file-catalog.yaml` marks the file `policy: generated` and both claims are true.

Rules that existed in only one of the two when this was found:

| only in the repo's 17 | only in the shipped 12 |
|---|---|
| the authorization workflow | avoid destructive changes |
| source text as a named input on every LLM step | `outputs/` requires human review |
| file organisation; plans before implementation | `project/TODO.md` as a session cache |
| audits are diagnostic, not gates | draft GH issues for human approval |
| verses are milestones; four-column boards | nothing is intentional unless the human says so |

The Captain, 2026-08-21: *"we need to fix this NOW, not file an issue for later."*

**This test asserts agreement, not content.** It does not care which rules survive the merge
or where the single list ends up living — only that a project and this repository are held to
the same set. That keeps it valid whatever the Captain rules the merged set to be.
"""

from __future__ import annotations

import re
from pathlib import Path

from llmflow.cli_utils import AI_RULES_DOC

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATED_RULES = REPO_ROOT / "docs" / "ai-context" / "rules.md"

# A rule is a numbered list item. Both texts are markdown ordered lists, and the leading
# `**Bold lead.**` is what makes two phrasings of the same rule recognisable as one rule.
NUMBERED = re.compile(r"^\s*\d+\.\s+(.*)$", re.M)
LEAD = re.compile(r"\*\*(.+?)\*\*")


def _rules(text: str) -> dict[str, str]:
    """Rules keyed by their bolded lead phrase, or by the whole item when there is none."""
    found = {}
    for item in NUMBERED.findall(text):
        item = re.sub(r"\s+", " ", item).strip()
        lead = LEAD.search(item)
        key = (lead.group(1) if lead else item)[:60].rstrip(".:").lower()
        found[key] = item
    return found


def test_a_project_and_this_repository_are_held_to_the_same_rules():
    """One file, one source. Two hand-maintained texts is the defect.

    `sp init` writes `AI_RULES_DOC`; `tools/update_ai_context.py` writes this repo's copy.
    Both are ours, which is exactly why they must not be able to disagree.
    """
    shipped = _rules(AI_RULES_DOC)
    generated = _rules(GENERATED_RULES.read_text(encoding="utf-8"))

    only_shipped = sorted(set(shipped) - set(generated))
    only_generated = sorted(set(generated) - set(shipped))

    assert not only_shipped and not only_generated, (
        "docs/ai-context/rules.md is written from two independent texts.\n"
        f"  in cli_utils.AI_RULES_DOC only ({len(only_shipped)}): {only_shipped}\n"
        f"  in the generated file only ({len(only_generated)}): {only_generated}\n"
        "A project scaffolded by `sp init` is held to the first; this repository to the "
        "second. Derive both from one list."
    )


def test_the_two_texts_word_each_shared_rule_identically():
    """Agreeing on which rules exist is not enough if the wording drifts.

    Two copies of one rule in slightly different words is how the shorter one silently
    becomes a weaker version — the failure this repository has now hit three times
    (`.cursorrules` losing the `sp run` prohibition, `load-context` paraphrasing
    `rules.md`, and `design-authority.md` shortened across two repositories).
    """
    shipped = _rules(AI_RULES_DOC)
    generated = _rules(GENERATED_RULES.read_text(encoding="utf-8"))

    differing = sorted(key for key in set(shipped) & set(generated) if shipped[key] != generated[key])

    assert not differing, (
        "these rules exist in both texts but are worded differently, so one is a paraphrase "
        f"of the other and will drift: {differing}"
    )
