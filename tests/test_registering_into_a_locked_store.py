"""The first `sp resource add` on a set-up machine must not fail on the lock.

`~/.sp` is kept read-only, and `~/.sp/registrations` is created by the first registration that
needs it. So the `mkdir` happens *inside* a locked directory, and on a machine where the store
already exists but has never registered a resource it fails:

    INFO  - Downloaded to ~/sp/resources/Clear-Bible/macula-greek
    Could not register 'SBLGNT': [Errno 13] Permission denied: '~/.sp/registrations'

The download succeeds and the registration does not, which is the worst division: the data is on
disk, nothing records that it is, and re-running repeats the download.

Two things make this the *new contributor's* bug specifically. A machine with no `~/.sp` at all
is unaffected, because the store is created writable and locked afterwards. A machine that has
registered anything before is unaffected, because the directory already exists. It bites exactly
once, on a fresh setup, which is why it survived: the machines it was tested on had all already
passed through the state that hides it.

This is the same defect that `~/.sp/versification` hit and had patched for that one directory.
The fix belongs where the directory is created, not once per subdirectory.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llmflow.cli_utils import _lock_sp_dir
from llmflow.resources import _write_registration


@pytest.fixture
def locked_store_without_registrations(tmp_path: Path, monkeypatch) -> Path:
    """A store as `sp init` leaves it: present, read-only, no registrations yet."""
    sp_home = tmp_path / ".sp"
    sp_home.mkdir()
    (sp_home / "disciplines").mkdir()
    _lock_sp_dir(sp_home)
    monkeypatch.setenv("SP_HOME", str(sp_home))
    return sp_home


def test_the_first_registration_creates_its_directory(locked_store_without_registrations):
    sp_home = locked_store_without_registrations
    target = sp_home / "registrations" / "SBLGNT.yaml"

    _write_registration(target, "# SBL Greek New Testament\n", {"id": "SBLGNT", "kind": "tsv"})

    assert target.is_file(), "the registration was not written"
    assert "SBLGNT" in target.read_text(encoding="utf-8")


def test_the_store_is_locked_again_afterwards(locked_store_without_registrations):
    """Unlocking is a loan. A store left writable is one a stray edit can reach."""
    sp_home = locked_store_without_registrations
    target = sp_home / "registrations" / "SBLGNT.yaml"

    _write_registration(target, "", {"id": "SBLGNT"})

    assert not os.access(sp_home, os.W_OK), "the store root was left writable"
    assert not os.access(sp_home / "registrations", os.W_OK), (
        "the registrations directory was left writable"
    )


def test_a_second_registration_still_works(locked_store_without_registrations):
    """The directory now exists and is locked — the path that always worked must keep working."""
    sp_home = locked_store_without_registrations

    _write_registration(sp_home / "registrations" / "SBLGNT.yaml", "", {"id": "SBLGNT"})
    _write_registration(sp_home / "registrations" / "WLC.yaml", "", {"id": "WLC"})

    written = sorted(p.name for p in (sp_home / "registrations").glob("*.yaml"))
    assert written == ["SBLGNT.yaml", "WLC.yaml"], written
