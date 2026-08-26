"""`sp tools replay` pairs request with response from the manifest (LLMFlow#198).

`find_response_file()` used to strip the timestamp and suffix off a request filename, glob
the directory for responses with the same middle, sort them, and take "the earliest at or
after" the request. Its own docstring conceded the guess. That works until two steps share
a prompt file, or a step is retried — both of which produced identical names.

With a manifest the pairing is a recorded field. Directories captured before #198 have no
manifest, so the old path has to keep working; absence is normal, not an error.
"""
import json
from pathlib import Path

import pytest

from llmflow.tools.replay import find_response_file


@pytest.fixture
def run_dir(tmp_path):
    return tmp_path


def _manifest(run_dir, *records):
    (run_dir / "manifest.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
    )


class TestManifestPairing:
    def test_pairs_from_the_manifest(self, run_dir):
        (run_dir / "0001-analyze-request.txt").write_text("req")
        (run_dir / "0001-analyze-response.json").write_text('{"a": 1}')
        _manifest(run_dir, {
            "seq": 1, "step": "analyze",
            "request_file": "0001-analyze-request.txt",
            "response_file": "0001-analyze-response.json",
        })

        found = find_response_file(str(run_dir / "0001-analyze-request.txt"))
        assert found and Path(found).name == "0001-analyze-response.json"

    def test_two_steps_sharing_a_prompt_pair_correctly(self, run_dir):
        """The case filename-sorting could not get right."""
        for seq, step in ((1, "greek"), (2, "hebrew")):
            (run_dir / f"000{seq}-{step}-request.txt").write_text(f"{step} req")
            (run_dir / f"000{seq}-{step}-response.json").write_text(f'"{step} resp"')
        _manifest(
            run_dir,
            {"seq": 1, "step": "greek", "request_file": "0001-greek-request.txt",
             "response_file": "0001-greek-response.json"},
            {"seq": 2, "step": "hebrew", "request_file": "0002-hebrew-request.txt",
             "response_file": "0002-hebrew-response.json"},
        )

        found = find_response_file(str(run_dir / "0002-hebrew-request.txt"))
        assert Path(found).read_text() == '"hebrew resp"'

    def test_a_retry_pairs_with_its_own_response(self, run_dir):
        for name in ("0001-analyze", "0002-analyze-attempt2"):
            (run_dir / f"{name}-request.txt").write_text(f"{name} req")
            (run_dir / f"{name}-response.json").write_text(f'"{name} resp"')
        _manifest(
            run_dir,
            {"seq": 1, "step": "analyze", "attempt": 1,
             "request_file": "0001-analyze-request.txt",
             "response_file": "0001-analyze-response.json"},
            {"seq": 2, "step": "analyze", "attempt": 2,
             "request_file": "0002-analyze-attempt2-request.txt",
             "response_file": "0002-analyze-attempt2-response.json"},
        )

        found = find_response_file(str(run_dir / "0002-analyze-attempt2-request.txt"))
        assert Path(found).read_text() == '"0002-analyze-attempt2 resp"'

    def test_a_call_with_no_response_returns_none(self, run_dir):
        (run_dir / "0001-analyze-request.txt").write_text("req")
        _manifest(run_dir, {"seq": 1, "step": "analyze",
                            "request_file": "0001-analyze-request.txt",
                            "response_file": None})
        assert find_response_file(str(run_dir / "0001-analyze-request.txt")) is None


class TestLegacyDirectoriesStillWork:
    """Captured before #198: no manifest, old filenames."""

    def test_falls_back_to_filename_pairing(self, run_dir):
        (run_dir / "2026-07-07-124717_scene_request.txt").write_text("req")
        (run_dir / "2026-07-07-124719_scene_response.txt").write_text("resp")

        found = find_response_file(str(run_dir / "2026-07-07-124717_scene_request.txt"))
        assert found and Path(found).read_text() == "resp"

    def test_missing_manifest_is_not_an_error(self, run_dir):
        (run_dir / "2026-07-07-124717_scene_request.txt").write_text("req")
        assert find_response_file(str(run_dir / "2026-07-07-124717_scene_request.txt")) is None

    def test_a_truncated_manifest_does_not_break_the_run_dir(self, run_dir):
        """A run killed mid-write must not make its directory unreadable."""
        (run_dir / "2026-07-07-124717_scene_request.txt").write_text("req")
        (run_dir / "2026-07-07-124719_scene_response.txt").write_text("resp")
        (run_dir / "manifest.jsonl").write_text('{"seq": 1, "step": "x"\n')

        found = find_response_file(str(run_dir / "2026-07-07-124717_scene_request.txt"))
        assert found and Path(found).read_text() == "resp"
