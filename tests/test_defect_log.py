"""Tests: a run records what it noticed without failing.

A step that finds a discrepancy in the data — a citation that did not resolve, a unit needing
review, an assumption it had to make — should say so and carry on. There was nowhere to put that,
so a consumer built a module-level list with a lock, which `context-is-the-only-channel` forbids:
invisible to `sp lint`, to `--dry-run`, to `--rewind-to` and to telemetry.

Two channels, both ruled:

  **the reserved key** — a step returns `defects` alongside its data. This is ordinary step
  output, so it needs no exemption from that rule, and every step type can write one: an XQuery,
  a SQL query, an LLM under a schema, a function.

  **the logger** — Python code writes to the `llmflow.defects` logger and is captured, so a
  plugin author needs no new import.

`[]` and absence differ, per `say-which-kind-of-nothing`: an empty log means the run looked and
found nothing.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
import yaml

from llmflow.defects import (
    DEFECT_LOG_KEY,
    RESERVED_KEY,
    DefectLog,
    defect_logging_handler,
)
from llmflow.runner import run_pipeline
from llmflow.utils.step_outputs import handle_step_outputs

# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

class TestRecording:

    def test_a_defect_is_kept_in_the_order_it_was_found(self):
        log = DefectLog()
        log.record("first", "one")
        log.record("second", "two")
        assert [d["message"] for d in log.entries()] == ["one", "two"]

    def test_severity_defaults_to_warning(self):
        log = DefectLog()
        log.record("step", "something")
        assert log.entries()[0]["severity"] == "warning"

    def test_an_unknown_severity_is_refused(self):
        log = DefectLog()
        with pytest.raises(ValueError):
            log.record("step", "something", severity="catastrophe")

    def test_detail_is_kept_verbatim(self):
        log = DefectLog()
        log.record("step", "msg", location="MRK 1:1", words=7)
        entry = log.entries()[0]
        assert entry["location"] == "MRK 1:1"
        assert entry["detail"]["words"] == 7

    def test_a_deep_copy_shares_the_same_log(self):
        """`for-each` deep-copies the context per iteration.

        The log must survive that as *itself*: a copy would collect an iteration's defects into
        an object that is then discarded, which is the silent loss this exists to end. It also
        cannot be copied at all — a `threading.Lock` refuses — so sharing is both the correct
        answer and the only one.
        """
        from copy import deepcopy

        log = DefectLog()
        context = {DEFECT_LOG_KEY: log, "other": {"nested": 1}}
        copied = deepcopy(context)

        assert copied[DEFECT_LOG_KEY] is log
        assert copied["other"] is not context["other"], "everything else still copies"

        copied[DEFECT_LOG_KEY].record("inside", "found in an iteration")
        assert log.entries()[0]["message"] == "found in an iteration"

    def test_concurrent_records_all_arrive(self):
        """`for-each` with `parallel:` means concurrent writes; a lost defect is a silent one."""
        log = DefectLog()
        with ThreadPoolExecutor(max_workers=8) as pool:
            for i in range(200):
                pool.submit(log.record, f"step{i}", f"msg{i}")
        assert len(log.entries()) == 200


# ---------------------------------------------------------------------------
# The reserved key, drained wherever a step returns one
# ---------------------------------------------------------------------------

class TestReservedKey:

    def test_a_step_returning_defects_is_drained(self):
        log = DefectLog()
        result = {"data": [1, 2], RESERVED_KEY: [{"message": "no match for MRK 1:1"}]}
        handle_step_outputs({"name": "check", "output": "out"}, result, {}, defects=log)
        assert len(log.entries()) == 1
        assert log.entries()[0]["message"] == "no match for MRK 1:1"

    def test_the_step_name_is_filled_in_when_the_defect_omits_it(self):
        log = DefectLog()
        result = {RESERVED_KEY: [{"message": "x"}]}
        handle_step_outputs({"name": "derive", "output": "out"}, result, {}, defects=log)
        assert log.entries()[0]["step"] == "derive"

    def test_a_bare_string_is_accepted_as_a_message(self):
        log = DefectLog()
        handle_step_outputs(
            {"name": "s", "output": "o"}, {RESERVED_KEY: ["just a note"]}, {}, defects=log
        )
        assert log.entries()[0]["message"] == "just a note"

    def test_the_result_reaching_context_is_not_mutated(self):
        """Draining copies; a step's own output is its own."""
        log = DefectLog()
        context: dict = {}
        result = {"data": 1, RESERVED_KEY: [{"message": "x"}]}
        handle_step_outputs({"name": "s", "output": "out"}, result, context, defects=log)
        assert RESERVED_KEY in context["out"]

    def test_a_step_returning_nothing_reserved_records_nothing(self):
        log = DefectLog()
        handle_step_outputs({"name": "s", "output": "o"}, {"data": 1}, {}, defects=log)
        assert log.entries() == []

    def test_a_non_dict_result_is_ignored(self):
        log = DefectLog()
        handle_step_outputs({"name": "s", "output": "o"}, "plain text", {}, defects=log)
        assert log.entries() == []

    def test_no_log_supplied_is_not_an_error(self):
        """Every step handler calls this; a run without a log must still work."""
        handle_step_outputs({"name": "s", "output": "o"}, {RESERVED_KEY: [{"message": "x"}]}, {})

    def test_the_log_is_found_in_the_context(self):
        """The channel every step already has, rather than a new argument on every handler."""
        log = DefectLog()
        context = {DEFECT_LOG_KEY: log}
        handle_step_outputs(
            {"name": "s", "output": "o"}, {RESERVED_KEY: [{"message": "from context"}]}, context
        )
        assert log.entries()[0]["message"] == "from context"


# ---------------------------------------------------------------------------
# The logging channel
# ---------------------------------------------------------------------------

class TestLoggingChannel:

    def test_a_record_on_the_defects_logger_is_captured(self):
        log = DefectLog()
        handler = defect_logging_handler(log)
        logger = logging.getLogger("llmflow.defects")
        logger.addHandler(handler)
        try:
            logger.warning("citation did not resolve", extra={"location": "MRK 1:1"})
        finally:
            logger.removeHandler(handler)
        assert log.entries()[0]["message"] == "citation did not resolve"
        assert log.entries()[0]["location"] == "MRK 1:1"

    def test_an_engine_warning_is_captured_too(self):
        """The handler hangs on `llmflow`, not on a `defects` child.

        The engine's own warnings — `partialVerses` uninterpreted, a mapping skipped, a
        versification assumed — are the same category of finding as a plugin's. Before this they
        were prose in `llmflow.log` that nothing could count.
        """
        log = DefectLog()
        handler = defect_logging_handler(log)
        handler.setLevel(logging.WARNING)
        logger = logging.getLogger("llmflow")
        logger.addHandler(handler)
        try:
            logging.getLogger("llmflow.utils.versification").warning("partialVerses ignored")
        finally:
            logger.removeHandler(handler)
        assert [e["message"] for e in log.entries()] == ["partialVerses ignored"]

    def test_routine_progress_is_not_a_defect(self):
        """`logger.info` narrates the run. A log that collects it reports nothing."""
        log = DefectLog()
        handler = defect_logging_handler(log)
        handler.setLevel(logging.WARNING)
        logger = logging.getLogger("llmflow")
        logger.addHandler(handler)
        try:
            logging.getLogger("llmflow.runner").info("Found 3 steps to execute")
        finally:
            logger.removeHandler(handler)
        assert log.entries() == []

    def test_the_level_becomes_the_severity(self):
        log = DefectLog()
        handler = defect_logging_handler(log)
        logger = logging.getLogger("llmflow.defects")
        logger.addHandler(handler)
        try:
            logger.error("nothing downstream to inspect")
        finally:
            logger.removeHandler(handler)
        assert log.entries()[0]["severity"] == "error"


# ---------------------------------------------------------------------------
# The run end to end
# ---------------------------------------------------------------------------

class TestTheRunCollectsThem:
    """The handler has to survive the run that writes the file it feeds.

    `intermediate_file_directory` is the condition for writing `defects.json` — and it is also the
    condition under which the runner calls `Logger.reset()` to move `llmflow.log` into the debug
    directory. That reset clears every handler on the `llmflow` logger. So the two conditions
    coincide exactly: the runs that write a defect log are the runs whose defect log would be
    empty. Nothing but an end-to-end run shows it.
    """

    @pytest.fixture
    def pipeline(self, tmp_path):
        (tmp_path / "plugins").mkdir()
        (tmp_path / "plugins" / "__init__.py").write_text("")
        (tmp_path / "plugins" / "noisy.py").write_text(
            "import logging\n"
            "\n"
            "def run(**kwargs):\n"
            "    logging.getLogger('llmflow.plugins.noisy').warning('MRK 1:1 did not resolve')\n"
            "    return 'done'\n"
        )
        config = {
            "name": "defect-run",
            "intermediate_file_directory": str(tmp_path / "debug"),
            "steps": [
                {
                    "name": "be_noisy",
                    "type": "function",
                    "function": "plugins.noisy.run",
                    "inputs": {},
                    "output": "result",
                }
            ],
        }
        path = tmp_path / "pipeline.yaml"
        path.write_text(yaml.dump(config))
        return str(path), tmp_path

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_a_warning_raised_during_the_run_reaches_the_file(self, _lint, _validate, pipeline):
        path, working_dir = pipeline
        original = os.getcwd()
        try:
            os.chdir(working_dir)
            run_pipeline(path, skip_lint=True)
        finally:
            os.chdir(original)
            if str(working_dir) in sys.path:
                sys.path.remove(str(working_dir))

        written = json.loads((working_dir / "debug" / "defects.json").read_text())
        assert [e["message"] for e in written["defects"]] == ["MRK 1:1 did not resolve"]

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_the_handler_is_gone_when_the_run_ends(self, _lint, _validate, pipeline):
        """Otherwise a second run collects the first run's warnings, and its own twice."""
        path, working_dir = pipeline
        before = len(logging.getLogger("llmflow").handlers)
        original = os.getcwd()
        try:
            os.chdir(working_dir)
            run_pipeline(path, skip_lint=True)
        finally:
            os.chdir(original)
            if str(working_dir) in sys.path:
                sys.path.remove(str(working_dir))

        remaining = [
            h for h in logging.getLogger("llmflow").handlers
            if type(h).__name__ == "_DefectHandler"
        ]
        assert remaining == []
        assert len(logging.getLogger("llmflow").handlers) <= before + 1

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_it_is_gone_when_the_run_fails_too(self, _lint, _validate, tmp_path):
        """A failed run is the likeliest one to be re-run. Its handler must not outlive it."""
        (tmp_path / "plugins").mkdir()
        (tmp_path / "plugins" / "__init__.py").write_text("")
        (tmp_path / "plugins" / "boom.py").write_text(
            "def run(**kwargs):\n    raise RuntimeError('no')\n"
        )
        config = {
            "name": "failing-run",
            "intermediate_file_directory": str(tmp_path / "debug"),
            "steps": [
                {
                    "name": "explode",
                    "type": "function",
                    "function": "plugins.boom.run",
                    "inputs": {},
                    "output": "result",
                }
            ],
        }
        path = tmp_path / "pipeline.yaml"
        path.write_text(yaml.dump(config))

        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(Exception):
                run_pipeline(str(path), skip_lint=True)
        finally:
            os.chdir(original)
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

        remaining = [
            h for h in logging.getLogger("llmflow").handlers
            if type(h).__name__ == "_DefectHandler"
        ]
        assert remaining == []


# ---------------------------------------------------------------------------
# What is written, and what an empty log means
# ---------------------------------------------------------------------------

class TestWriting:

    def test_it_writes_the_entries_and_their_counts(self, tmp_path):
        log = DefectLog(pipeline="book")
        log.record("a", "one")
        log.record("b", "two", severity="error")
        written = log.write(tmp_path / "defects.json")
        payload = json.loads(written.read_text(encoding="utf-8"))
        assert payload["pipeline"] == "book"
        assert len(payload["defects"]) == 2
        assert payload["counts"] == {"error": 1, "warning": 1}

    def test_an_empty_log_still_writes_an_empty_list(self, tmp_path):
        """`[]` means the run looked and found nothing. Absence would mean nobody looked."""
        written = DefectLog(pipeline="book").write(tmp_path / "defects.json")
        payload = json.loads(written.read_text(encoding="utf-8"))
        assert payload["defects"] == []
        assert payload["counts"] == {"error": 0, "warning": 0}

    def test_the_directory_is_created(self, tmp_path):
        written = DefectLog().write(tmp_path / "nested" / "deeper" / "defects.json")
        assert written.is_file()

    def test_the_summary_names_the_counts(self):
        log = DefectLog()
        log.record("a", "one")
        log.record("b", "two", severity="error")
        assert "1 error" in log.summary()
        assert "1 warning" in log.summary()

    def test_an_empty_summary_says_so_rather_than_being_blank(self):
        assert "no defects" in DefectLog().summary().lower()
