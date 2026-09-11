"""`sp init` unlocks the store to write to it, rather than reporting that it could not.

`~/.sp` is deliberately read-only. The lock belongs to `sp`, so that the store is only ever
changed by this code and never by a hand or a stray script; unlocking to write and re-locking
afterwards is what the lock is for. A write refused by it is therefore not the lock working —
it is `sp` failing to use its own key.

The observed failure, on a real project:

    WARNING - Could not register in global registry:
              [Errno 13] Permission denied: '~/.sp/ai-context/project-index.md.yaml'
    WARNING - This is not critical - registry can be updated manually.

Two defects in three lines. The write should have unlocked — `_sp_dir_writable` already exists
and the project registration two blocks above already uses it. And the remedy is wrong in a way
that matters: "updated manually" invites hand-editing the one store that must never be
hand-edited, which is the act the lock is there to prevent.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llmflow.cli_utils import _lock_sp_dir, _register_in_global_registry


@pytest.fixture
def project_with_context(tmp_path: Path) -> Path:
    project = tmp_path / "a-project"
    for half, name in (("sp", "rules.md"), ("project", "overview.md")):
        target = project / "docs" / "ai-context" / half / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# {half} {name}\n", encoding="utf-8")
    return project


def _locked_store(sp_home: Path) -> Path:
    """A store in the state `sp` leaves it in: present, populated, read-only."""
    (sp_home / "projects").mkdir(parents=True, exist_ok=True)
    (sp_home / "ai-context").mkdir(parents=True, exist_ok=True)
    _lock_sp_dir(sp_home / "ai-context")
    _lock_sp_dir(sp_home / "projects")
    return sp_home


def test_the_context_index_is_written_through_the_lock(project_with_context, tmp_path,
                                                       monkeypatch):
    sp_home = _locked_store(tmp_path / ".sp")
    monkeypatch.setenv("SP_HOME", str(sp_home))

    _register_in_global_registry(project_with_context)

    written = sorted(p.name for p in (sp_home / "ai-context").glob("*.yaml"))
    assert written, (
        "nothing was indexed: the write hit the read-only store and was swallowed as a warning"
    )
    assert any("rules" in name for name in written), written


def test_the_store_is_locked_again_afterwards(project_with_context, tmp_path, monkeypatch):
    """Unlocking is a loan, not a handover. A store left writable is one a stray edit can reach."""
    sp_home = _locked_store(tmp_path / ".sp")
    monkeypatch.setenv("SP_HOME", str(sp_home))

    _register_in_global_registry(project_with_context)

    assert not os.access(sp_home / "ai-context", os.W_OK), (
        "the store was left writable after the write"
    )


def test_nothing_tells_the_reader_to_edit_the_store_by_hand(project_with_context, tmp_path,
                                                            monkeypatch, caplog):
    """The old remedy — 'registry can be updated manually' — advised the forbidden act."""
    sp_home = _locked_store(tmp_path / ".sp")
    monkeypatch.setenv("SP_HOME", str(sp_home))

    with caplog.at_level("WARNING"):
        _register_in_global_registry(project_with_context)

    offending = [r.message for r in caplog.records if "manually" in r.message.lower()]
    assert not offending, offending
