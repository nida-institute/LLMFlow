"""Every intermediate the suite writes stays inside this repository, and cannot be committed.

Scope, cause and the rulings behind it: #207, and the Unreleased section of `CHANGELOG.md`.
"""
from __future__ import annotations

import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

from llmflow.cli_utils import _unlock_sp_dir

REPO_ROOT = Path(__file__).resolve().parent.parent


def _locked_tree(root: Path) -> Path:
    """Build the thing that produced 4,773 orphan directories: read-only files and dirs."""
    store = root / ".sp"
    (store / "skills" / "load-context").mkdir(parents=True)
    (store / "skills" / "load-context" / "SKILL.md").write_text("x", encoding="utf-8")
    (store / "projects").mkdir()
    (store / "projects" / "a.yaml").write_text("y", encoding="utf-8")

    # a-w, which is what _lock_sp_dir() applies.
    for path in sorted(store.rglob("*"), reverse=True):
        path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    store.chmod(store.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    return store


def test_a_locked_store_really_does_defeat_deletion(tmp_path):
    """The premise, asserted rather than assumed.

    Without this, the test below proves nothing: an unlock that fixes a problem that was never
    there would pass just as happily.
    """
    store = _locked_tree(tmp_path / "before")
    with pytest.raises(OSError):
        shutil.rmtree(store)


def test_unlock_makes_a_locked_store_deletable(tmp_path):
    """The engine's own `_unlock_sp_dir`, which the conftest hook calls rather than reimplement.

    A first version of the hook had its own copy of this — two encodings of one fact, which rule
    `design-is-declarative` names as the defect. `_unlock_sp_dir` is the exact inverse of the
    `_lock_sp_dir` that produces the state, so this guard now covers the one implementation.
    """
    store = _locked_tree(tmp_path / "after")
    _unlock_sp_dir(store)
    shutil.rmtree(store)  # raises if the unlock missed anything
    assert not store.exists()


def test_unlock_is_silent_about_a_path_that_is_not_there(tmp_path):
    """Called from `pytest_configure` on a basetemp that may not exist yet."""
    _unlock_sp_dir(tmp_path / "never-created")


def test_the_basetemp_is_inside_this_repository(tmp_path_factory):
    """The Captain's requirement, enforced.

    Guards the regression that matters: dropping the flag sends every intermediate back to a
    system temp directory, and nothing else in the suite would notice.
    """
    basetemp = tmp_path_factory.getbasetemp().resolve()
    assert REPO_ROOT in basetemp.parents, (
        f"pytest is writing to {basetemp}, outside the repository. "
        "Restore --basetemp=tmp/pytest in pytest.ini."
    )
    assert (REPO_ROOT / "tmp") in basetemp.parents or basetemp.parent == REPO_ROOT / "tmp"


def test_the_intermediates_are_not_committable(tmp_path_factory):
    """*"I don't want to commit intermediate pytest files."*

    Asked of git rather than of the ignore file's text. A first draft of this test asserted that
    `tmp/.gitignore` begins with `*`; it begins with a comment, so the test failed while the
    behaviour was correct. Reading an ignore file is a second encoding of a decision git already
    holds — rule `design-is-declarative` — and `git check-ignore` is the decision itself.

    Rule `output-and-intermediates-are-separate` is the one being satisfied: the ignore list
    follows the declared intermediate directory rather than anyone's memory.
    """
    basetemp = tmp_path_factory.getbasetemp()
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", str(basetemp / "probe.txt")],
        capture_output=True,
    )
    assert result.returncode == 0, (
        f"git would let {basetemp} be committed. Intermediates must stay ignored."
    )


def test_no_test_hands_a_shared_directory_to_the_executor():
    """The GUI executor runs with `cwd = project_path`, so a literal path writes outside.

    `test_gui_cors_config.py` passed `/tmp`, which put `llmflow.log` in `/private/tmp` on
    every run — invisible unless you went looking.
    """
    offenders = []
    for path in sorted((REPO_ROOT / "tests").glob("test_*.py")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "project_path" not in line or line.strip().startswith("#"):
                continue
            if "'/tmp'" in line or '"/tmp"' in line or "'/var" in line or '"/var' in line:
                offenders.append(f"{path.name}:{n}: {line.strip()}")
    assert not offenders, (
        "these hand a shared system directory to the executor; use tmp_path:\n  "
        + "\n  ".join(offenders)
    )


def test_pytest_ini_keeps_only_what_failed():
    """*"keep only what failed"* — declared in the config, not implemented in a fixture."""
    ini = (REPO_ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "tmp_path_retention_policy = failed" in ini
    assert "--basetemp=tmp/pytest" in ini


def test_tempfile_also_writes_inside_the_repository():
    """`--basetemp` is not enough, and this is the test that says why.

    Measured 2026-08-25: **49 files** — 24 `tmp*.yaml` and 25 `tmp*.md` — were sitting loose in
    the machine's `$TMPDIR`. Twenty-odd tests call
    `tempfile.NamedTemporaryFile(suffix=..., delete=False)`, which bypasses pytest's temp factory
    altogether, so `--basetemp` never sees them, and `delete=False` means nothing removes them
    — not pytest, not the run that created them. Under random names in a shared directory they
    are indistinguishable from any other application's, which is exactly the invisibility the
    Captain objected to.

    Redirecting `tempfile` covers every such test at once, including ones not yet written.
    Repointing the twenty tests at `tmp_path` is the deeper repair and is a separate change.
    """
    tempdir = Path(tempfile.gettempdir()).resolve()
    assert REPO_ROOT in tempdir.parents, (
        f"tempfile writes to {tempdir}, outside the repository. "
        "pytest_configure should redirect it into tmp/."
    )


def test_the_tempfile_directory_is_emptied_on_the_way_in(tmp_path):
    """*"and delete it the next time pytest runs."*

    pytest empties a configured `--basetemp` itself, so the factory half needs no help beyond the
    unlock. The `tempfile` half has no such owner, so the hook clears it — and this asserts the
    clearing function does what the hook relies on.
    """
    from tests.conftest import _empty_tree

    target = tmp_path / "loose"
    target.mkdir()
    (target / "tmpabc.yaml").write_text("x", encoding="utf-8")
    (target / "tmpdir1").mkdir()
    (target / "tmpdir1" / "inner.md").write_text("y", encoding="utf-8")
    (target / "data-gym-cache").mkdir()
    (target / "data-gym-cache" / "encoding.bpe").write_text("z", encoding="utf-8")

    _empty_tree(target)

    assert target.is_dir(), "the directory itself survives; only its contents go"
    assert not (target / "tmpabc.yaml").exists()
    assert not (target / "tmpdir1").exists()
    assert (target / "data-gym-cache" / "encoding.bpe").exists(), (
        "a third-party cache is not this suite's to delete. Redirecting TMPDIR catches every "
        "library that asks for a temp directory; measured on a real run, wiping this directory "
        "wholesale would make tiktoken re-download 5.1 MB of encoding tables every time."
    )
