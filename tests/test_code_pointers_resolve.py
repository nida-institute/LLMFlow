"""A working document named from code exists and is tracked in git.

`docstrings-say-what-not-why` allows prose in code to carry a cross-reference and nothing
else, so the pointer is the whole of what survives. `plans-are-temporary` then deletes the
document it points at after about eight days, and only a commit lets `git show <commit>^:<path>`
return the version the comment was written against.

Reported by `docstrings-say-what-not-why` in `data/ai-rules.yaml`.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNED = ("src/llmflow", "tests", "tools")

#: A path written with a repository prefix belongs to another repository and is not ours to
#: resolve — `human-at-the-helm/project/plans/…` is a real reference to a real file elsewhere.
POINTER = re.compile(r"(?<![\w/-])project/plans/[A-Za-z0-9._-]+\.md")

#: Named in data rather than prose: a document a skill writes during its own run, so its
#: absence before that run is correct. Each entry says which skill writes it.
WRITTEN_BY_A_SKILL = frozenset({
    "project/plans/tmp-context.md",   # written by the load-context skill
})


def _pointers() -> dict[str, list[str]]:
    """Every `project/plans/*.md` named from scanned code, mapped to where it is named."""
    found: dict[str, list[str]] = {}
    for directory in SCANNED:
        for path in sorted((REPO_ROOT / directory).rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for target in POINTER.findall(line):
                    site = f"{path.relative_to(REPO_ROOT)}:{line_number}"
                    found.setdefault(target, []).append(site)
    return found


def _tracked() -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "project/plans"],
        capture_output=True, text=True, check=True,
    )
    return set(result.stdout.split())


def test_the_scan_finds_pointers():
    """A guard that can quietly reduce to nothing is worse than an absent one.

    The subject here is derived from source text, so a change in how paths are written could
    leave every set below empty and every assertion passing.
    """
    assert len(_pointers()) >= 15, (
        "the pointer scan found almost nothing — the pattern has stopped matching, not the "
        "codebase stopped pointing"
    )


def test_every_named_plan_document_exists():
    dangling = {
        target: sites for target, sites in _pointers().items()
        if target not in WRITTEN_BY_A_SKILL and not (REPO_ROOT / target).is_file()
    }
    assert not dangling, (
        "A pointer with nothing behind it is worse than no pointer: it still reads as "
        "authority. Restore the document, or replace the reference with an issue number.\n  "
        + "\n  ".join(f"{t} — named at {', '.join(s)}" for t, s in sorted(dangling.items()))
    )


def test_every_named_plan_document_is_tracked():
    tracked = _tracked()
    untracked = {
        target: sites for target, sites in _pointers().items()
        if (REPO_ROOT / target).is_file() and target not in tracked
    }
    assert not untracked, (
        "Commit these. An untracked working document is deleted without trace, so the comment "
        "naming it points at nothing and `git show <commit>^:<path>` cannot recover the version "
        "it was written against.\n  "
        + "\n  ".join(f"{t} — named at {', '.join(s)}" for t, s in sorted(untracked.items()))
    )
