import logging
from pathlib import Path

import pytest

from llmflow.cli import main
from llmflow.cli_utils import HELLO_PIPELINE, HELLO_PROMPT, init_project as init_environment


def test_cli_init_creates_hello_prompt(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.chdir(tmp_path)

    main(["init"])

    prompt_path = tmp_path / "prompts" / "hello.gpt"
    assert prompt_path.exists()
    assert prompt_path.read_text(encoding="utf-8") == HELLO_PROMPT

    # second run should be idempotent
    main(["init"])
    assert prompt_path.read_text(encoding="utf-8") == HELLO_PROMPT


def test_init_environment_creates_files(tmp_path, caplog):
    caplog.set_level(logging.INFO)

    init_environment(tmp_path)

    prompt_path = tmp_path / "prompts" / "hello.gpt"
    pipeline_path = tmp_path / "pipelines" / "hello-llmflow.yaml"
    output_dir = tmp_path / "output"

    assert prompt_path.read_text(encoding="utf-8") == HELLO_PROMPT
    assert pipeline_path.read_text(encoding="utf-8") == HELLO_PIPELINE
    assert output_dir.is_dir()

    init_environment(tmp_path)
    assert prompt_path.read_text(encoding="utf-8") == HELLO_PROMPT
    assert pipeline_path.read_text(encoding="utf-8") == HELLO_PIPELINE