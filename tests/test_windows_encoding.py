import io
import sys
from pathlib import Path

import pytest

from llmflow.runner import render_prompt


# --- writing output, not just reading files ------------------------------------------
#
# The tests below cover reading prompts as UTF-8. They say nothing about *writing*, which is
# where the CLI actually broke: a Windows console defaults to cp1252, and `sp doctor` prints
# `✓ · ! ✗`, an em dash and `→`. None of those encode, so the binary died with
# UnicodeEncodeError — on the first Windows run doctor ever had, because it was only added to
# the smoke test after the previous release.


def _cp1252_stream() -> io.TextIOWrapper:
    """A console that can only encode Latin-1, as Windows gives you by default."""
    return io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")


def test_a_cp1252_console_cannot_take_the_doctor_report_unaided():
    """The failure this guards, stated as a fact rather than trusted to memory."""
    from llmflow.doctor import Check, Report, Severity

    report = Report(checks=[Check("x", "needs doing", Severity.WARNING, remedy="Run `sp init`.")])
    with pytest.raises(UnicodeEncodeError):
        _cp1252_stream().write(report.render())


def test_the_cli_makes_its_output_encodable(monkeypatch):
    """`sp` reconfigures its streams at entry, so no command can die on a glyph."""
    from llmflow.cli import _make_output_encodable
    from llmflow.doctor import Check, Report, Severity

    stream = _cp1252_stream()
    monkeypatch.setattr(sys, "stdout", stream)
    monkeypatch.setattr(sys, "stderr", stream)
    _make_output_encodable()

    report = Report(checks=[Check("x", "needs doing", Severity.WARNING, remedy="Run `sp init`.")])
    sys.stdout.write(report.render())  # must not raise
    sys.stdout.flush()


def test_every_command_is_covered_not_just_doctor(monkeypatch):
    """`sp resource add` prints ✅ and ❌, and the downloader prints 📥. Fixing one printer
    would have left the next one to fail on someone else's machine."""
    from llmflow.cli import _make_output_encodable

    stream = _cp1252_stream()
    monkeypatch.setattr(sys, "stdout", stream)
    _make_output_encodable()
    sys.stdout.write("✅ Registered · ❌ Could not · 📥 Downloading · → remedy · —\n")
    sys.stdout.flush()


def test_render_prompt_uses_utf8(monkeypatch, tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_file = prompt_dir / "hello.gpt"
    prompt_file.write_text("Χαίρετε {{name}}\nשלום {{name}}", encoding="utf-8")

    real_read_text = Path.read_text

    def fake_read_text(self, encoding=None, errors=None):
        assert encoding == "utf-8"
        return real_read_text(self, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    context = {"prompts_dir": str(prompt_dir), "name": "LLMFlow"}
    rendered = render_prompt({"file": "hello.gpt"}, context)

    assert "Χαίρετε LLMFlow" in rendered
    assert "שלום LLMFlow" in rendered


def test_render_prompt_handles_utf8_bom(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_file = prompt_dir / "hello-bom.gpt"
    payload = b"\xef\xbb\xbf" + "Χαίρετε {{name}}\nשלום {{name}}".encode("utf-8")
    prompt_file.write_bytes(payload)

    context = {"prompts_dir": str(prompt_dir), "name": "LLMFlow"}
    rendered = render_prompt({"file": "hello-bom.gpt"}, context)

    assert "Χαίρετε LLMFlow" in rendered
    assert "שלום LLMFlow" in rendered