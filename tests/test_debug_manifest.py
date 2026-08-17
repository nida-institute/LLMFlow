"""Debug output records itself in a manifest instead of encoding facts in filenames (#198).

`build_debug_filename()` produced
`{passage|timestamp}_{prompt_stem|step_name}[_lvlN_var-label]_{request|response}.txt`,
and that name was doing a database's job. Three consequences, all verified before this
change:

* The step name was used **only when there was no prompt file**, so two steps sharing one
  `.gpt` produced the same filename and the second silently overwrote the first.
* A retry produced the identical name too, so the successful attempt destroyed the failed
  one — the attempt actually worth reading.
* The timestamp appeared **only when `passage` was absent**, so the one field that could
  establish ordering was missing exactly when there were most files to order.

And `sp tools replay` had to strip the timestamp, strip the suffix, glob the directory and
then compare filenames lexicographically to guess which response belonged to which request
— its own docstring conceded the guess.

A sequence number makes names unique and ordered; the manifest carries the facts.
"""
import json
from pathlib import Path

import pytest

from llmflow.utils.debug import DebugRecorder


@pytest.fixture
def recorder(tmp_path):
    return DebugRecorder(tmp_path, enabled=True)


def _lines(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    if not manifest.exists():
        return []
    return [json.loads(x) for x in manifest.read_text().splitlines() if x.strip()]


class TestFilenamesAreUniqueAndOrdered:
    def test_two_steps_sharing_a_prompt_file_do_not_collide(self, recorder, tmp_path):
        """The collision that used to overwrite the first step's evidence."""
        a = recorder.begin("analyze_greek", prompt_file="prompts/analyze.gpt")
        recorder.save_request(a, "greek request")
        b = recorder.begin("analyze_hebrew", prompt_file="prompts/analyze.gpt")
        recorder.save_request(b, "hebrew request")

        assert a.request_path != b.request_path
        assert Path(a.request_path).read_text() == "greek request"
        assert Path(b.request_path).read_text() == "hebrew request"

    def test_a_retry_does_not_overwrite_the_attempt_it_retried(self, recorder):
        first = recorder.begin("analyze", prompt_file="p.gpt")
        recorder.save_request(first, "attempt one")
        second = recorder.begin("analyze", prompt_file="p.gpt")
        recorder.save_request(second, "attempt two")

        assert first.attempt == 1 and second.attempt == 2
        assert Path(first.request_path).read_text() == "attempt one"
        assert Path(second.request_path).read_text() == "attempt two"

    def test_sequence_numbers_sort_in_execution_order(self, recorder, tmp_path):
        for name in ("zebra", "alpha", "middle"):
            recorder.save_request(recorder.begin(name, prompt_file="p.gpt"), "x")
        names = sorted(p.name for p in tmp_path.glob("*-request.txt"))
        assert [n.split("-")[0] for n in names] == ["0001", "0002", "0003"]
        assert "zebra" in names[0], "alphabetical order must not reorder execution"

    def test_step_name_is_always_in_the_filename(self, recorder):
        call = recorder.begin("analyze_greek", prompt_file="prompts/analyze.gpt")
        recorder.save_request(call, "x")
        assert "analyze_greek" in Path(call.request_path).name


class TestManifest:
    def test_a_line_per_call(self, recorder, tmp_path):
        for name in ("one", "two"):
            call = recorder.begin(name, prompt_file="p.gpt")
            recorder.save_request(call, "req")
            recorder.save_response(call, "resp")
            recorder.finish(call)
        assert len(_lines(tmp_path)) == 2

    def test_pairing_is_recorded_not_inferred(self, recorder, tmp_path):
        call = recorder.begin("analyze", prompt_file="p.gpt", model="gpt-4o")
        recorder.save_request(call, "req")
        recorder.save_response(call, "resp")
        recorder.finish(call)

        line = _lines(tmp_path)[0]
        assert Path(tmp_path / line["request_file"]).read_text() == "req"
        assert Path(tmp_path / line["response_file"]).read_text() == "resp"

    def test_records_the_facts_worth_querying(self, recorder, tmp_path):
        call = recorder.begin("analyze", prompt_file="prompts/a.gpt",
                              model="gpt-4o", passage="Mark 1:1")
        recorder.save_request(call, "req")
        recorder.finish(call, status="ok")

        line = _lines(tmp_path)[0]
        for field in ("seq", "step", "attempt", "prompt_file", "model",
                      "passage", "started", "status"):
            assert field in line, f"{field} missing from {line}"
        assert line["step"] == "analyze"
        assert line["model"] == "gpt-4o"

    def test_a_failed_call_is_still_recorded(self, recorder, tmp_path):
        call = recorder.begin("analyze", prompt_file="p.gpt")
        recorder.save_request(call, "req")
        recorder.finish(call, status="error", error="timeout")

        line = _lines(tmp_path)[0]
        assert line["status"] == "error" and line["error"] == "timeout"
        assert line["response_file"] is None

    def test_paths_are_relative_to_the_run_directory(self, recorder, tmp_path):
        """So a run directory can be moved or archived without breaking the manifest."""
        call = recorder.begin("analyze", prompt_file="p.gpt")
        recorder.save_request(call, "req")
        recorder.finish(call)
        assert not Path(_lines(tmp_path)[0]["request_file"]).is_absolute()


class TestDisabled:
    def test_writes_nothing_when_disabled(self, tmp_path):
        rec = DebugRecorder(tmp_path, enabled=False)
        call = rec.begin("analyze", prompt_file="p.gpt")
        rec.save_request(call, "req")
        rec.save_response(call, "resp")
        rec.finish(call)
        assert list(tmp_path.iterdir()) == []

    def test_disabled_calls_are_harmless(self, tmp_path):
        """Debug capture is off by default; the recorder must never break a run."""
        rec = DebugRecorder(tmp_path, enabled=False)
        call = rec.begin("analyze", prompt_file="p.gpt")
        assert call.request_path is None and call.response_path is None
