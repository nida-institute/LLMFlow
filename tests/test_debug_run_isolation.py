"""Runs no longer destroy each other's debug output (LLMFlow#198).

`_clear_debug_dir()` did `shutil.rmtree()` on a directory keyed by pipeline filename
alone, at the start of every run. So running the same pipeline for Ruth and then for Mark
deleted every captured request and unedited reply from the Ruth run — and, when
`intermediate_file_directory` was declared, the run log with them, since `llmflow.log` is
written into that same directory.

Two fixes, because they save different files:

1. **The run's distinguishing variables go in the path.** CLI `--var` values are the
   natural signal: they are by definition what varies between runs. This is what saves
   `llmflow.log`, whose name is fixed and would otherwise be overwritten regardless.
2. **No `rmtree`.** Files are written over in place. This is what saves the dumps, whose
   names already carry the passage and so do not collide across passages.

The larger layout redesign — sequence numbers, attempt numbers and a run manifest — stays
in #198; this is the data-loss fix only.
"""
from pathlib import Path

import pytest

from llmflow.utils.debug import _clear_debug_dir, _get_debug_dir, run_key_for


class TestRunKey:
    def test_cli_vars_become_the_key(self):
        assert run_key_for({"book": "Ruth"}) == "book-Ruth"

    def test_multiple_vars_are_ordered_deterministically(self):
        a = run_key_for({"book": "Ruth", "chapter": "1"})
        b = run_key_for({"chapter": "1", "book": "Ruth"})
        assert a == b, "key must not depend on dict order"

    def test_no_cli_vars_gives_a_stable_default(self):
        assert run_key_for({}) == "default"
        assert run_key_for(None) == "default"

    def test_path_hostile_values_are_sanitised(self):
        key = run_key_for({"passage": "Mark 1:14-39"})
        assert "/" not in key and ":" not in key and " " not in key, key

    def test_different_books_give_different_keys(self):
        assert run_key_for({"book": "Ruth"}) != run_key_for({"book": "Mark"})


class TestDebugDirIsPerRun:
    def test_run_key_is_in_the_path(self, tmp_path):
        d = _get_debug_dir({"intermediate_file_directory": str(tmp_path)}, {},
                           "my-pipeline", run_key="book-Ruth")
        assert d.endswith(str(Path("debug") / "my-pipeline" / "book-Ruth")), d

    def test_two_books_get_two_directories(self, tmp_path):
        cfg = {"intermediate_file_directory": str(tmp_path)}
        ruth = _get_debug_dir(cfg, {}, "p", run_key=run_key_for({"book": "Ruth"}))
        mark = _get_debug_dir(cfg, {}, "p", run_key=run_key_for({"book": "Mark"}))
        assert ruth != mark

    def test_omitting_run_key_keeps_the_old_shape(self, tmp_path):
        """Callers that do not supply a key must still get a usable directory."""
        d = _get_debug_dir({"intermediate_file_directory": str(tmp_path)}, {}, "p")
        assert d.endswith(str(Path("debug") / "p"))

    def test_a_run_with_no_vars_adds_no_segment(self, tmp_path):
        """The subdirectory names what varied; when nothing varied, there is nothing to
        name. Keeps the layout unchanged for pipelines that take no --var."""
        d = _get_debug_dir({"intermediate_file_directory": str(tmp_path)}, {}, "p",
                           run_key=run_key_for({}))
        assert d.endswith(str(Path("debug") / "p"))


class TestNothingIsDeleted:
    @pytest.fixture
    def cfg(self, tmp_path):
        return {"intermediate_file_directory": str(tmp_path)}

    def test_ruth_survives_a_mark_run(self, cfg):
        """The reported bug, end to end."""
        ruth_dir = Path(_get_debug_dir(cfg, {}, "p", run_key="book-Ruth"))
        _clear_debug_dir(cfg, {}, dry_run=False, pipeline_name="p", run_key="book-Ruth")
        (ruth_dir / "Ruth_1_1_analyze_request.txt").write_text("ruth request")
        (ruth_dir / "llmflow.log").write_text("ruth log")

        _clear_debug_dir(cfg, {}, dry_run=False, pipeline_name="p", run_key="book-Mark")

        assert (ruth_dir / "Ruth_1_1_analyze_request.txt").read_text() == "ruth request"
        assert (ruth_dir / "llmflow.log").read_text() == "ruth log", "the run log was destroyed"

    def test_rerunning_the_same_book_does_not_delete_its_own_history(self, cfg):
        d = Path(_get_debug_dir(cfg, {}, "p", run_key="book-Ruth"))
        _clear_debug_dir(cfg, {}, dry_run=False, pipeline_name="p", run_key="book-Ruth")
        (d / "keep.txt").write_text("previous run")

        _clear_debug_dir(cfg, {}, dry_run=False, pipeline_name="p", run_key="book-Ruth")

        assert (d / "keep.txt").exists(), "rmtree is back"

    def test_directory_is_created(self, cfg):
        _clear_debug_dir(cfg, {}, dry_run=False, pipeline_name="p", run_key="book-Ruth")
        assert Path(_get_debug_dir(cfg, {}, "p", run_key="book-Ruth")).is_dir()

    def test_dry_run_creates_nothing(self, cfg):
        _clear_debug_dir(cfg, {}, dry_run=True, pipeline_name="p", run_key="book-Ruth")
        assert not Path(_get_debug_dir(cfg, {}, "p", run_key="book-Ruth")).exists()
