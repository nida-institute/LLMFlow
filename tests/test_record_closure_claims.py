"""Guardrail: a record may not claim an issue closed before the commit reaches `main`.

A closing keyword in a commit message takes effect when the commit lands on the repository's
default branch. Work on `dev` therefore passes through three distinct states, and "closed"
names only the second:

  1. committed to `dev` — already live in consumer repositories on the same machine, because
     they install this engine as an editable dependency;
  2. merged to `main` — the closing keyword fires and the issue closes;
  3. released — published, and reachable by anyone not working from this tree.

A record saying "closed by <sha>" while the commit sits on `dev` conflates the first with the
second: the change is in use, and the issue is open.

Scans the tracking documents for "closed by <sha>" and requires each named commit to be an
ancestor of `main`. Skips when no `main` ref is reachable, which is the case in a clone that
has fetched only one branch.
"""
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

#: Documents that carry status claims a later session reads as settled fact.
RECORDS = ("project/TODO.md", "project/HANDOFF.md")

#: "closed by <sha>", with the sha optionally in backticks.
CLOSURE_CLAIM = re.compile(r"closed\s+by\s+`?([0-9a-f]{7,40})`?", re.IGNORECASE)

#: `Closes #12` / `Fixes #12` / `Resolves #12` in a commit message body.
CLOSING_KEYWORD = re.compile(r"\b(?:clos(?:e|es|ed)|fix(?:e[sd])?)\s+#(\d+)", re.IGNORECASE)

#: An unfinished task naming an issue: "- [ ] … #12".
OPEN_TASK = re.compile(r"^\s*[-*]\s*\[ \]\s.*?#(\d+)", re.MULTILINE)

#: Refs to try, in order, for the branch a closing keyword actually fires on.
MAIN_REFS = ("origin/main", "main", "origin/master", "master")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True, check=False
    )


def _main_ref() -> str | None:
    for ref in MAIN_REFS:
        if _git("rev-parse", "--verify", "--quiet", ref).returncode == 0:
            return ref
    return None


def _implemented_on_dev() -> set[str]:
    """Issues a commit declares finished that is on this branch but not yet on `main`."""
    main = _main_ref()
    if main is None:
        return set()
    log = _git("log", f"{main}..HEAD", "--format=%B")
    if log.returncode != 0:
        return set()
    return set(CLOSING_KEYWORD.findall(log.stdout))


def _open_tasks() -> list[tuple[str, str]]:
    found = []
    for relative in RECORDS:
        path = REPO / relative
        if not path.is_file():
            continue
        for issue in OPEN_TASK.findall(path.read_text(encoding="utf-8")):
            found.append((relative, issue))
    return found


def test_no_record_lists_dev_implemented_work_as_unfinished():
    """The inverse claim: work finished on `dev` must not sit in the record as a task to do.

    An issue closes only when its commit reaches `main`, so a session cannot learn from GitHub
    what is already implemented here. It learns it from the record, and a record that still
    lists finished work sends the next session to rebuild it.
    """
    implemented = _implemented_on_dev()
    if not implemented:
        pytest.skip("no commit ahead of main declares an issue finished")

    contradictions = [
        f"{relative} lists #{issue} as an unfinished task"
        for relative, issue in _open_tasks()
        if issue in implemented
    ]
    assert not contradictions, (
        "The record lists work as unfinished that a commit on this branch declares finished:\n"
        + "\n".join(f"   {c}" for c in contradictions)
        + "\n   The issue is legitimately still open on GitHub — it closes at the merge to "
        "main — but the record is what tells a session the work is already done here.\n"
        "   Say it is implemented and awaiting the merge, or drop the task."
    )


def _claims() -> list[tuple[str, int, str]]:
    found = []
    for relative in RECORDS:
        path = REPO / relative
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for sha in CLOSURE_CLAIM.findall(line):
                found.append((relative, number, sha))
    return found


def test_git_is_available():
    assert _git("rev-parse", "--git-dir").returncode == 0, (
        f"{REPO} is not a git working tree, so closure claims cannot be checked."
    )


@pytest.mark.parametrize(
    "relative,line,sha",
    _claims() or [pytest.param("", 0, "", marks=pytest.mark.skip(reason="no closure claims"))],
    ids=lambda value: str(value),
)
def test_closure_claim_has_reached_main(relative, line, sha):
    main = _main_ref()
    if main is None:
        pytest.skip("no main ref in this clone; nothing to compare a closure claim against")

    assert _git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0, (
        f"{relative}:{line} names commit {sha}, which is not in this repository.\n"
        f"   A closure claim must name a commit a reader can check."
    )

    reached = _git("merge-base", "--is-ancestor", sha, main).returncode == 0
    assert reached, (
        f"{relative}:{line} says an issue was 'closed by {sha}', but {sha} has not reached "
        f"{main}, so the issue is open on GitHub.\n"
        f"   The change itself may well be in use — consumer repositories on this machine "
        f"install the engine as an editable dependency and see a `dev` commit immediately. "
        f"'Closed' is not the word for that state, and a session reading this line will look "
        f"for a closed issue and find an open one.\n"
        f"   Say which state it is in: committed to `dev`, merged to {main}, or released. "
        f"Merging {main} forward is what makes 'closed' true."
    )
