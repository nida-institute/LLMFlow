"""Conventions shared with Human at the Helm must carry no Scripture Pipelines vocabulary.

Plan: `project/plans/design-hath-parity.md` §4 (classification) and §7 step 4 (the split).

The counterpart to `test_portable_skills.py`, one level down. That file makes the skill
classification falsifiable; this one does the same for the conventions, which are the other
half of what a project set up by Human at the Helm receives.

The classification below is §4's, with one file resolved by the split itself:

- `sp-workflow.md` mixed general practice with this engine's CLI. Its general half is now
  `workflow.md` and transfers; the name `sp-workflow.md` stays with the engine half.
- `llmflow-project-tracking.md` became `project-tracking.md`. The rolling-file structure is
  general practice; "one file per pipeline" is not, so that application moved into
  `sp-workflow.md` beside the other engine-specific rules.
- `README.md` is neither shared nor engine-only. It is an index of whatever ships beside it,
  so it necessarily names the engine files; Human at the Helm writes its own.

The patterns come from `test_portable_skills.py` rather than being restated here. A second
copy of "what counts as engine vocabulary" is the failure this whole plan exists to end —
three conventions went unshipped for months because a hand-kept list disagreed with what the
package contained (#204).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.test_portable_skills import (
    ECOSYSTEM_MARKERS,
    ENGINE_VOCABULARY,
    _offenders,
)

SHARED_WITH_HATH = (
    "design-authority.md",
    "github-authority.md",
    "project-tracking.md",
    "surface-decisions.md",
    "workflow.md",
)

ENGINE_ONLY = (
    "consumer-repo-conventions.md",
    "llmflow-pipeline-steps.md",
    "llmflow-prompt-organization.md",
    "sp-debugging.md",
    "sp-workflow.md",
)

# Rewritten rather than copied: an index of what ships, which differs on each side.
REWRITTEN = ("README.md",)


def _conventions_dir() -> Path:
    import llmflow

    return Path(llmflow.__file__).parent / "templates" / "sp-conventions"


@pytest.mark.parametrize("convention", SHARED_WITH_HATH)
def test_shared_convention_carries_no_engine_vocabulary(convention: str):
    """A convention shared with Human at the Helm must not mention this engine.

    Where the removed text was an engine rule, it belongs in an engine-only convention —
    `sp-workflow.md` for the CLI and for per-pipeline tracking. Nothing is deleted; it moves
    to the file that owns it.
    """
    path = _conventions_dir() / convention
    assert path.is_file(), f"{convention} is not shipped"

    offenders = _offenders(path.read_text(encoding="utf-8"), ENGINE_VOCABULARY)

    assert not offenders, (
        f"{convention} is shared with Human at the Helm but names this engine:\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("convention", SHARED_WITH_HATH)
def test_shared_convention_serves_both_toolchains(convention: str):
    """A shared convention may name concrete tooling — but not only Python's.

    Same rule as the skills: parity, not silence. `pytest /path/tests/` earns its place in a
    list of shell examples; it may not appear without `npm test --prefix /path/` beside it,
    or a TypeScript reader is being shown a command they cannot run and no alternative.
    """
    text = (_conventions_dir() / convention).read_text(encoding="utf-8")
    present = {name for name, pattern in ECOSYSTEM_MARKERS.items() if pattern.search(text)}

    if not present:
        return

    missing = set(ECOSYSTEM_MARKERS) - present
    assert not missing, (
        f"{convention} shows {', '.join(sorted(present))} tooling but not "
        f"{', '.join(sorted(missing))}. Name the counterpart command beside it "
        f"(pytest ↔ vitest, hatch ↔ npm/pnpm, ruff ↔ tsc)."
    )


def test_every_shipped_convention_is_classified():
    """No convention may be added without deciding whether Human at the Helm gets it.

    An unclassified convention is one nobody has asked the governing question about, and it
    would silently miss the guard above.
    """
    shipped = {p.name for p in _conventions_dir().glob("*.md")}
    classified = set(SHARED_WITH_HATH) | set(ENGINE_ONLY) | set(REWRITTEN)

    assert shipped == classified, (
        "design-hath-parity.md §4 classifies every convention as shared, engine-only or "
        "rewritten.\n"
        f"  shipped but unclassified: {sorted(shipped - classified)}\n"
        f"  classified but not shipped: {sorted(classified - shipped)}"
    )


@pytest.mark.parametrize("convention", ENGINE_ONLY)
def test_engine_only_convention_keeps_its_specificity(convention: str):
    """The five that stay must not be generalized by accident.

    Each is about this engine, and losing that would make it useless here without making it
    useful anywhere else.
    """
    path = _conventions_dir() / convention
    assert path.is_file(), f"{convention} is no longer shipped"
    assert _offenders(path.read_text(encoding="utf-8"), ENGINE_VOCABULARY), (
        f"{convention} no longer names this engine — if it was generalized, §4 needs "
        "revisiting rather than this test being deleted"
    )


def test_the_split_kept_the_prohibition_on_running_pipelines():
    """The engine half must still forbid running a pipeline unasked.

    This is the load-bearing line of the file being split, and losing it in a move is not
    hypothetical: `.cursorrules` silently lost this exact prohibition, and the loss was
    invisible because everything around it still read correctly.
    """
    text = (_conventions_dir() / "sp-workflow.md").read_text(encoding="utf-8")
    assert re.search(r"[Nn]ever run `?sp run`?", text), (
        "sp-workflow.md no longer forbids running a pipeline without being asked"
    )


def test_the_split_left_no_engine_content_behind_in_the_general_half():
    """`workflow.md` must carry the general rules and none of the CLI ones.

    The vocabulary guard above catches an `sp` command; this catches the softer version —
    the general half keeping a section heading whose content went to the other file.
    """
    text = (_conventions_dir() / "workflow.md").read_text(encoding="utf-8")
    for heading in ("CLI Commands", "Project Tracking"):
        assert heading not in text, (
            f"workflow.md still has a '{heading}' section; that content belongs in "
            "sp-workflow.md"
        )
