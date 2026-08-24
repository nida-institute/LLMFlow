"""Guardrail: the shortname for Human at the Helm is `helm`, not `hath`.

Why this exists. `hath` was an AI-introduced abbreviation — terminology capture, in the
vocabulary of `drift-patterns.md`. Nobody chose it; it propagated into a tool name, a data
file, a test, a design document, a skill directory and a shipped README before anyone
noticed. The Captain, 2026-08-24: *"hath is your abbreviation, not mine. I do not love
abbreviations, I would prefer a shortname for human at the helm."* He ruled `helm`, and a
clean sweep.

This test is what stops it coming back. A term with no author and no note is exactly what
this repository has no way to audit later, so the guard is code rather than a convention.

**Two exemptions, both deliberate, both the Captain's ruling of 2026-08-24.** The sweep
removes *cruft* — names that only have to be consistent. It does not rewrite *records* —
statements about what was said or what shipped. Renaming inside a record does not clean it,
it makes it wrong:

- `CHANGELOG.md` names the files that shipped in past releases.
- `data/helm-sync.yaml` quotes the Captain verbatim in its `ruling:` fields, and
  `disciplines/surface-decisions.md` forbids rewording a recorded answer.

Anything else containing the old term is a miss, and this test names it.
"""
import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Records, not cruft. See the module docstring.
EXEMPT_FILES = {
    "CHANGELOG.md",
    "data/helm-sync.yaml",
    "tests/test_shortname_is_helm.py",  # this file names the old term to forbid it
    # Three lines quote the Captain verbatim, two of them answers written after a `=>`
    # (lines 20, 86, 496). A sweep rewrote them on 2026-08-24 and they were restored
    # byte-for-byte. Everything in this file that is a *pointer* — `/helm-check`, the
    # filename — was swept; only his words were left standing.
    "project/plans/design-helm-parity.md",
}

#: Directories with nothing authored in them.
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist",
             "build", ".ruff_cache", ".mypy_cache", "outputs", "tmp", ".hatch"}

TERM = re.compile(r"hath", re.IGNORECASE)

#: Extensions worth scanning. A binary hit would be a false positive.
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".gpt", ".cfg", ".sh"}


def _candidate_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix in TEXT_SUFFIXES:
                found.append(path)
    return sorted(found)


def _hits(root: Path, exempt: set[str]) -> list[str]:
    """Every 'rel/path:line: text' where the old term survives."""
    hits: list[str] = []
    for path in _candidate_files(root):
        rel = str(path.relative_to(root))
        if rel in exempt:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if TERM.search(line):
                hits.append(f"{rel}:{n}: {line.strip()[:100]}")
    return hits


def test_no_stale_shortname_in_file_contents():
    hits = _hits(REPO_ROOT, EXEMPT_FILES)
    assert not hits, (
        "The shortname for Human at the Helm is `helm`; `hath` was an AI-introduced "
        "abbreviation the Captain retired on 2026-08-24.\n"
        "   Surviving occurrences:\n     " + "\n     ".join(hits) + "\n"
        "   Fix: use `helm`. If the line is a *record* — what was said, or what shipped — "
        "add its path to EXEMPT_FILES with the reason, rather than rewriting the record."
    )


def test_no_stale_shortname_in_path_names():
    # The whole relative path, not just the filename — a directory can carry the term too,
    # which is how `skills/hath-check/SKILL.md` first slipped past this check.
    bad = [
        str(p.relative_to(REPO_ROOT))
        for p in _candidate_files(REPO_ROOT)
        if TERM.search(str(p.relative_to(REPO_ROOT)))
    ]
    assert not bad, (
        "These paths still carry the retired abbreviation:\n     " + "\n     ".join(bad) + "\n"
        "   Rename with `git mv` so history follows the file."
    )


def test_the_methodology_clone_is_swept_too():
    """The sibling repository, when a clone is present.

    Skipped on CI, which has no clone — the same pattern `test_helm_sync.py` uses, so the
    suite stays green where the other repository cannot be seen.
    """
    clone = Path(os.environ.get("HELM_REPO", "~/github/nida-institute/human-at-the-helm")).expanduser()
    if not clone.is_dir():
        pytest.skip("no Human at the Helm clone on this machine; set $HELM_REPO to check it")

    hits = _hits(clone, {"CHANGELOG.md"})
    paths = [
        str(p.relative_to(clone))
        for p in _candidate_files(clone)
        if TERM.search(str(p.relative_to(clone)))
    ]
    assert not hits and not paths, (
        f"{clone} still carries the retired abbreviation.\n"
        "   Paths: " + (", ".join(paths) or "none") + "\n"
        "   Contents:\n     " + ("\n     ".join(hits) or "none")
    )
