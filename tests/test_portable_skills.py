"""Skills shared with Human at the Helm must carry no Scripture Pipelines vocabulary.

Plan: `project/plans/design-helm-parity.md`, ruling H4.

The Captain, 2026-08-19: *"our ai context here is now more advanced than the original
Helm, by quite a bit. I want Helm to have the same level of maturity, without whatever is
specific to Scripture Pipelines."*

H4 ruled **one shared text** for five skills rather than a generalized fork: the
`sp`-specific lines come out of the skill entirely, because they duplicate
`docs/ai-context/rules.md`, which the skill's own procedure already reads. Measured before
that ruling:

| Skill | Lines | Lines with `sp` vocabulary |
|---|---|---|
| `stand-down` | 127 | 0 |
| `handoff` | 92 | 1 |
| `authorize` | 150 | 5 |
| `commit-ready` | 256 | 13 |
| `load-context` | 147 | 17 |

In `load-context` those 17 sat in three blocks, and `:88-90` — "key rules to internalize" —
is a paraphrase of `docs/ai-context/rules.md` items 2, 3 and 4, the file the skill's Step 4
instructs the reader to `cat`. A skill summarising a document it is about to make you read
is the same defect as the `.cursorrules` block that had silently lost the `sp run`
prohibition.

**This test is the mechanical half of the governing principle.** Without it, "this skill is
general" is an assertion in a design document; with it, it is a passing or failing build.

Two exclusions, both deliberate:

- **`audit-code` is forked, not shared** (H4-A). Its `sp` content is not a duplicated
  summary but the actual subject matter — plugin determinism, local plugins reimplementing
  LLMFlow core utilities. There is no authoritative file elsewhere to move it to, so Helm
  gets a different skill rather than a generalization of this one.
- **`audit-pipeline`, `audit-output`, `audit-prompts` and `release` stay here** (§4). Each
  is about the engine. `release` in particular was guessed to be general methodology in
  human-at-the-helm#1; its own text is about Nuitka builds and this repo's GitHub Actions.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Source of truth for this list: design-helm-parity.md §4. An earlier note here expected step
# 6 to replace it with Helm's shipped manifest; ruling D7-C is why it stays. `helm-sync.yaml`
# is checked *against* this classification, so sourcing the classification *from* the record
# would make the check circular — and Helm's manifest globs directories no CI runner can see.
SHARED_WITH_HELM = ("authorize", "stand-down", "handoff", "load-context", "commit-ready")

FORKED = ("audit-code",)
ENGINE_ONLY = ("audit-pipeline", "audit-output", "audit-prompts", "release")

# Vocabulary that ties a file to this engine. A shared skill carrying any of it would
# instruct a mentee about a tool they do not have.
ENGINE_VOCABULARY = {
    "sp CLI command": re.compile(r"\bsp (?:run|lint|init|clean|doctor|setup)\b"),
    "engine name": re.compile(r"\bllmflow\b", re.IGNORECASE),
    "prompt file extension": re.compile(r"\.gpt\b"),
    "pipeline vocabulary": re.compile(r"\bpipelines?\b", re.IGNORECASE),
    "saveas keyword": re.compile(r"\bsaveas\b"),
    "structured-output keyword": re.compile(r"\bresponse_format\b"),
    "domain": re.compile(r"\bscripture\b", re.IGNORECASE),
}

# `~/.sp` is not in the list above, deliberately. A shared skill may name it — an sp
# session must still read machine-wide disciplines — but only alongside the project-local
# location, since a project set up by Human at the Helm has no `~/.sp` at all (Q4). Naming
# a path that will not exist is harmless when the instruction says "read whichever exists";
# naming it *instead of* the one that does exist is not. Enforced by its own test below.
SP_HOME_DISCIPLINES = re.compile(r"~/\.sp/disciplines")
PROJECT_DISCIPLINES = re.compile(r"docs/ai-context/disciplines")

# Helm must serve a TypeScript project as readily as a Python one (Captain, 2026-08-19:
# "I am using this on a typescript project too" … "it would be nice to provision this for
# both Python and Typescript, with pytest and a good Typescript test framework in mind").
#
# The rule is parity, not silence. An earlier draft of this test failed on any mention of
# `pytest`, which would have driven the skills toward abstraction — "run the test suite"
# helps nobody. A skill is more useful when it shows a real command; it is only unusable
# when it shows one ecosystem's and not the other's.
# Note on the file-extension alternatives: they are deliberately *not* wrapped in a leading
# `\b`. A word boundary cannot match between two non-word characters, so `\b\.ts` fails on
# `**/*.ts` and on `` `.ts` `` while matching `file.ts` — which made the marker silently
# one-sided the first time it was written.
ECOSYSTEM_MARKERS = {
    "Python": re.compile(r"\b(?:pytest|hatch|pip install)\b|\.pyw?\b", re.IGNORECASE),
    "TypeScript": re.compile(
        r"\b(?:vitest|jest|npm (?:run|test|ci)|pnpm|tsc)\b|\.tsx?\b", re.IGNORECASE
    ),
}


def _skills_dir() -> Path:
    import llmflow

    return Path(llmflow.__file__).parent / "templates" / "sp-skills"


def _offenders(text: str, patterns: dict[str, re.Pattern]) -> list[str]:
    found = []
    for label, pattern in patterns.items():
        for hit in set(pattern.findall(text)):
            found.append(f"{label}: {hit!r}")
    return sorted(found)


@pytest.mark.parametrize("skill", SHARED_WITH_HELM)
def test_shared_skill_carries_no_engine_vocabulary(skill: str):
    """A skill shared with Helm must not mention this engine.

    Where the removed text was project rules, it belongs in `docs/ai-context/rules.md`,
    which `load-context` already reads. Nothing is lost by deleting it from the skill.
    """
    path = _skills_dir() / skill / "SKILL.md"
    assert path.is_file(), f"{skill} is not shipped"

    offenders = _offenders(path.read_text(encoding="utf-8"), ENGINE_VOCABULARY)

    assert not offenders, (
        f"{skill}/SKILL.md is shared with Human at the Helm but names this engine:\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("skill", SHARED_WITH_HELM)
def test_shared_skill_serves_both_ecosystems(skill: str):
    """A shared skill may name concrete tooling — but not only one ecosystem's.

    Concrete beats abstract: `pytest -q` teaches more than "run the test suite". The
    requirement is that a TypeScript reader gets the same courtesy, so wherever a Python
    command appears, its TypeScript counterpart appears beside it.

    A skill that names neither is fine — `stand-down` is entirely about conduct and needs
    no commands at all.
    """
    text = (_skills_dir() / skill / "SKILL.md").read_text(encoding="utf-8")
    present = {name for name, pattern in ECOSYSTEM_MARKERS.items() if pattern.search(text)}

    if not present:
        return

    missing = set(ECOSYSTEM_MARKERS) - present
    assert not missing, (
        f"{skill}/SKILL.md shows {', '.join(sorted(present))} tooling but not "
        f"{', '.join(sorted(missing))}. Helm serves both; name the counterpart command "
        f"beside it (pytest ↔ vitest, hatch ↔ npm/pnpm)."
    )


@pytest.mark.parametrize("skill", SHARED_WITH_HELM)
def test_shared_skill_never_names_only_the_machine_wide_disciplines(skill: str):
    """Conventions live in `~/.sp/` for an sp project and in the repo for a Helm one.

    A shared skill may name both — "read whichever exists" misleads nobody. It may not
    name only `~/.sp/disciplines`, because a project set up by Human at the Helm has no
    such directory and its reader would be sent to an empty path with no alternative
    offered (Q4).
    """
    text = (_skills_dir() / skill / "SKILL.md").read_text(encoding="utf-8")

    if not SP_HOME_DISCIPLINES.search(text):
        return

    assert PROJECT_DISCIPLINES.search(text), (
        f"{skill}/SKILL.md sends the reader to ~/.sp/disciplines without offering "
        "docs/ai-context/disciplines, which is where they live in a project that has no ~/.sp"
    )


@pytest.mark.parametrize("skill", ENGINE_ONLY)
def test_engine_only_skills_are_still_shipped_here(skill: str):
    """The four that stay must not be generalized by accident.

    They are about the engine, and losing their specificity would make them useless here
    without making them useful anywhere else.
    """
    assert (_skills_dir() / skill / "SKILL.md").is_file(), f"{skill} is no longer shipped"


def test_every_shipped_skill_is_classified():
    """No skill may be added without deciding whether Helm gets it.

    An unclassified skill is one nobody has asked the governing question about, and it
    would silently miss the guard above.
    """
    shipped = {p.name for p in _skills_dir().iterdir() if (p / "SKILL.md").exists()}
    classified = set(SHARED_WITH_HELM) | set(FORKED) | set(ENGINE_ONLY)

    assert shipped == classified, (
        "design-helm-parity.md §4 classifies every skill as shared, forked or engine-only.\n"
        f"  shipped but unclassified: {sorted(shipped - classified)}\n"
        f"  classified but not shipped: {sorted(classified - shipped)}"
    )


def test_audit_code_is_deliberately_not_shared():
    """Pin the H4-A exception so it cannot drift into the shared set unnoticed.

    If someone later generalizes audit-code, that is a decision to be taken and recorded,
    not one to arrive by editing.
    """
    assert "audit-code" not in SHARED_WITH_HELM
    text = (_skills_dir() / "audit-code" / "SKILL.md").read_text(encoding="utf-8")
    assert _offenders(text, ENGINE_VOCABULARY), (
        "audit-code no longer contains engine vocabulary — if it was generalized, "
        "H4-A needs revisiting rather than this test being deleted"
    )
