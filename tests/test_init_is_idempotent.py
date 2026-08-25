"""Guardrail: a second `sp init --update` writes nothing when nothing has changed.

The Captain, 2026-08-25: *"perhaps if the `~/.sp` files match exactly, we simply leave them in
place instead of overwriting, so as not to change the file dates? that might be easier for the
user and cleaner."*

Before this, `--update` passed `force=True` and every installer overwrote unconditionally, so a
routine refresh touched all 23 `~/.sp` files and every generated project file whether or not a
byte had changed. Two costs. The small one is mtime churn. The large one is that `~/.sp` is a
version-controlled store whose dirty state is how an unreviewed write gets noticed — and when
every refresh dirties everything, a real change is invisible in the crowd.

`sp doctor` already worked this way: it reports conventions as *"present and unchanged"* because
it compares content. This makes `sp init --update` agree with it, which is the same init/doctor
split as the generated-marker problem, in a second place.

Not solved here, and deliberately: `_register_in_global_registry` writes a *new* file per
project, so there is nothing to compare it against. That is the source of the junk registrations
in #207.
"""
import time
from pathlib import Path

import pytest

from llmflow.cli_utils import init_project


def _mtimes(root: Path) -> dict[str, int]:
    return {
        str(p.relative_to(root)): p.stat().st_mtime_ns
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("SP_HOME", str(home / ".sp"))
    base = tmp_path / "project"
    base.mkdir()
    init_project(base)
    return base, home / ".sp"


def test_update_rewrites_no_unchanged_project_file(isolated):
    base, _ = isolated
    before = _mtimes(base)
    time.sleep(0.01)
    init_project(base, update=True)
    after = _mtimes(base)

    touched = sorted(k for k in before if k in after and before[k] != after[k])
    assert not touched, (
        "`--update` rewrote project files whose content had not changed:\n  "
        + "\n  ".join(touched)
        + "\nWrite only when the content differs."
    )


def test_update_rewrites_no_unchanged_sp_home_file(isolated):
    base, sp_home = isolated
    if not sp_home.is_dir():
        pytest.skip("no ~/.sp was created")
    before = _mtimes(sp_home)
    time.sleep(0.01)
    init_project(base, update=True)
    after = _mtimes(sp_home)

    touched = sorted(k for k in before if k in after and before[k] != after[k])
    assert not touched, (
        "`--update` rewrote ~/.sp files whose content had not changed:\n  "
        + "\n  ".join(touched)
        + "\n~/.sp is version-controlled; churn hides the writes that matter."
    )


def test_update_still_repairs_a_file_that_did_change(isolated):
    """The comparison must not turn --update into a no-op."""
    base, _ = isolated
    quickref = base / "docs" / "llmflow-language-quickref.md"
    quickref.write_text("# clobbered\n", encoding="utf-8")
    init_project(base, update=True)
    assert quickref.read_text(encoding="utf-8") != "# clobbered\n", (
        "--update must still restore a generated file whose content has diverged."
    )
