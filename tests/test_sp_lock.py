"""
Tests for filesystem permissions on ~/.sp/ protected directories.

After sp init, the following directories are read-only:
  ~/.sp/disciplines/
  ~/.sp/skills/
  ~/.sp/projects/

The following are explicitly left writable:
  ~/.sp/data/
  ~/.sp/user-context/
"""
import os
import stat
from pathlib import Path

import pytest

from llmflow.cli_utils import init_project


def _is_writable(path: Path) -> bool:
    return os.access(path, os.W_OK)


def _make_sp_dirs(tmp_path: Path) -> None:
    """Pre-create directories that sp init does not own but should not touch."""
    (tmp_path / ".sp" / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".sp" / "user-context").mkdir(parents=True, exist_ok=True)


@pytest.fixture()
def sp_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _make_sp_dirs(tmp_path)
    return tmp_path


class TestLockedAfterInit:
    def test_disciplines_dir_locked(self, sp_home):
        init_project(sp_home / "project")
        disciplines = sp_home / ".sp" / "disciplines"
        assert disciplines.exists()
        assert not _is_writable(disciplines), "~/.sp/disciplines/ should be read-only after sp init"

    def test_skills_dir_locked(self, sp_home):
        init_project(sp_home / "project")
        skills = sp_home / ".sp" / "skills"
        assert skills.exists()
        assert not _is_writable(skills), "~/.sp/skills/ should be read-only after sp init"

    def test_projects_dir_locked(self, sp_home):
        init_project(sp_home / "project")
        projects = sp_home / ".sp" / "projects"
        assert projects.exists()
        assert not _is_writable(projects), "~/.sp/projects/ should be read-only after sp init"


class TestUnprotectedDirsRemainWritable:
    def test_data_dir_remains_writable(self, sp_home):
        init_project(sp_home / "project")
        data = sp_home / ".sp" / "data"
        assert _is_writable(data), "~/.sp/data/ must remain writable after sp init"

    def test_user_context_dir_remains_writable(self, sp_home):
        init_project(sp_home / "project")
        user_context = sp_home / ".sp" / "user-context"
        assert _is_writable(user_context), "~/.sp/user-context/ must remain writable after sp init"


class TestIdempotence:
    def test_second_init_succeeds_when_locked(self, sp_home):
        init_project(sp_home / "project")
        # Second run must unlock, write, and relock without raising
        init_project(sp_home / "project")
        assert not _is_writable(sp_home / ".sp" / "disciplines")
        assert not _is_writable(sp_home / ".sp" / "skills")
        assert not _is_writable(sp_home / ".sp" / "projects")

    def test_update_succeeds_when_locked(self, sp_home):
        init_project(sp_home / "project")
        init_project(sp_home / "project", update=True)
        assert not _is_writable(sp_home / ".sp" / "disciplines")
        assert not _is_writable(sp_home / ".sp" / "skills")

    def test_no_examples_succeeds_when_locked(self, sp_home):
        init_project(sp_home / "project")
        init_project(sp_home / "project", no_examples=True)
        assert not _is_writable(sp_home / ".sp" / "disciplines")
        assert not _is_writable(sp_home / ".sp" / "skills")


class TestWriteBlocked:
    def test_direct_write_to_locked_disciplines_raises(self, sp_home):
        init_project(sp_home / "project")
        target = sp_home / ".sp" / "disciplines" / "sneaky.md"
        with pytest.raises(PermissionError):
            target.write_text("unauthorized content", encoding="utf-8")

    def test_direct_write_to_locked_skills_raises(self, sp_home):
        init_project(sp_home / "project")
        target = sp_home / ".sp" / "skills" / "sneaky.md"
        with pytest.raises(PermissionError):
            target.write_text("unauthorized content", encoding="utf-8")
