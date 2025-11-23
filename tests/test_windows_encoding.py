import io
from pathlib import Path

import pytest

from llmflow.runner import render_prompt


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