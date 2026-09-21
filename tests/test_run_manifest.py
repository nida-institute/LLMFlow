"""A run records what it wrote, so a re-run can remove its own output and nothing else (#245).

`/audit-output` reading a directory that holds two runs' files reasons about a mixture. The fix
is not `sp clean` before a run: that deletes every parameterisation's intermediates, which is
#198's bug moved from `debug/` into `intermediate/`, and it breaks `--rewind-to`, which replays
by reading the very files a pre-run clean would remove.

Instead a run records the paths it wrote and deletes only those on a matching re-run.
"""

from __future__ import annotations

from llmflow.utils import file_io


def test_the_written_file_list_is_emptied_between_runs(tmp_path):
    """Two runs in one process must not share a written-file list.

    The list is what a re-run deletes from, so a stale entry is a file removed that this run
    never wrote. `runner` reset it with `global WRITTEN_FILES; WRITTEN_FILES = []`, which
    rebinds a name in `runner` rather than clearing `file_io`'s list, so nothing was reset:
    under the CLI one run is one process and it never showed, but the Python API and the test
    suite run many.
    """
    file_io.reset_written_files()
    assert file_io.WRITTEN_FILES == []

    first = tmp_path / "first.json"
    first.write_text("{}", encoding="utf-8")
    file_io._record_written_file(str(first))
    assert len(file_io.WRITTEN_FILES) == 1

    file_io.reset_written_files()
    assert file_io.WRITTEN_FILES == [], (
        "a second run starts with the first run's files still listed, so it would delete them"
    )


def test_resetting_keeps_the_same_list_object(tmp_path):
    """Callers hold a reference to the list, so it is cleared in place rather than rebound.

    Rebinding is exactly the defect this replaces: the name changed and every existing
    reference went on pointing at the old list.
    """
    before = file_io.WRITTEN_FILES
    file_io.reset_written_files()
    assert file_io.WRITTEN_FILES is before
