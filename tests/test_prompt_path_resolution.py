"""Tests for prompt file path resolution (issue #91).

Covers:
- resolve_prompt_path: correct resolution, no double-prefixing
- render_prompt: clear error when prompt file is missing
- Linter/runner parity: both use the same resolution logic
- cli.py: FileNotFoundError from inside a pipeline is not misreported as
  "Pipeline file not found"
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from llmflow.utils.io import resolve_prompt_path


# ---------------------------------------------------------------------------
# resolve_prompt_path
# ---------------------------------------------------------------------------

def test_bare_filename_resolved_under_prompts_dir(tmp_path):
    """'my-prompt.gpt' → prompts_dir/my-prompt.gpt"""
    prompt = tmp_path / "prompts" / "my-prompt.gpt"
    prompt.parent.mkdir()
    prompt.write_text("hello", encoding="utf-8")

    result = resolve_prompt_path("my-prompt.gpt", str(tmp_path / "prompts"))
    assert result == prompt


def test_already_prefixed_path_not_double_prefixed(tmp_path):
    """'prompts/my-prompt.gpt' must NOT become prompts/prompts/my-prompt.gpt."""
    prompt = tmp_path / "prompts" / "my-prompt.gpt"
    prompt.parent.mkdir()
    prompt.write_text("hello", encoding="utf-8")

    # Simulate running from tmp_path so relative paths resolve there
    import os
    original = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = resolve_prompt_path("prompts/my-prompt.gpt", "prompts")
        assert result == Path("prompts/my-prompt.gpt")
    finally:
        os.chdir(original)


def test_subdirectory_prompt_resolved(tmp_path):
    """'subdir/my-prompt.gpt' → prompts_dir/subdir/my-prompt.gpt"""
    prompt = tmp_path / "prompts" / "subdir" / "my-prompt.gpt"
    prompt.parent.mkdir(parents=True)
    prompt.write_text("hello", encoding="utf-8")

    result = resolve_prompt_path("subdir/my-prompt.gpt", str(tmp_path / "prompts"))
    assert result == prompt


def test_absolute_path_used_as_is(tmp_path):
    prompt = tmp_path / "my-prompt.gpt"
    prompt.write_text("hello", encoding="utf-8")

    result = resolve_prompt_path(str(prompt), "prompts")
    assert result == prompt


def test_missing_prompt_raises_with_paths_attempted(tmp_path):
    """FileNotFoundError message must include the paths that were tried."""
    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_prompt_path("missing.gpt", str(tmp_path / "prompts"))
    msg = str(exc_info.value)
    assert "missing.gpt" in msg
    assert "tried" in msg.lower() or "prompts" in msg


# ---------------------------------------------------------------------------
# render_prompt — clear error for missing prompt
# ---------------------------------------------------------------------------

def test_render_prompt_raises_clear_error_for_missing_file(tmp_path):
    """render_prompt must raise FileNotFoundError naming the prompt, not the pipeline."""
    from llmflow.runner import render_prompt

    import os
    original = os.getcwd()
    os.chdir(tmp_path)
    try:
        with pytest.raises(FileNotFoundError) as exc_info:
            render_prompt({"file": "nonexistent.gpt", "inputs": {}}, {})
        msg = str(exc_info.value)
        assert "nonexistent.gpt" in msg
        assert "pipeline" not in msg.lower()
    finally:
        os.chdir(original)


def test_render_prompt_no_double_prefix(tmp_path):
    """render_prompt must not double-prefix 'prompts/foo.gpt' → 'prompts/prompts/foo.gpt'."""
    from llmflow.runner import render_prompt

    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    gpt = prompt_dir / "foo.gpt"
    gpt.write_text("hello {{name}}", encoding="utf-8")

    import os
    original = os.getcwd()
    os.chdir(tmp_path)
    try:
        # 'prompts/foo.gpt' is how the bug manifests — includes the prefix
        result = render_prompt({"file": "prompts/foo.gpt", "inputs": {"name": "world"}}, {})
        assert "hello world" in result
    finally:
        os.chdir(original)


# ---------------------------------------------------------------------------
# Linter/runner parity — same file found by both
# ---------------------------------------------------------------------------

def test_linter_and_runner_find_same_file(tmp_path):
    """A prompt file found by the linter must also be found by render_prompt."""
    from llmflow.utils.linter import lint_pipeline_full
    import os, yaml

    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    gpt = prompt_dir / "step.gpt"
    gpt.write_text(
        "---\nprompt:\n  requires:\n    - text\n---\n{{text}}",
        encoding="utf-8"
    )

    pipeline = {
        "name": "test",
        "version": 1,
        "steps": [{
            "name": "my_step",
            "type": "llm",
            "model": "gpt-4o",
            "prompt": {"file": "prompts/step.gpt", "inputs": {"text": "hi"}},
            "outputs": "result",
        }]
    }
    pipeline_file = tmp_path / "pipeline.yaml"
    pipeline_file.write_text(yaml.dump(pipeline), encoding="utf-8")

    original = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = lint_pipeline_full(str(pipeline_file))
        # Lint must pass — if it finds the file, runner must too
        assert result.valid, f"Lint failed: {result.errors}"

        # Runner must also find the file without raising
        from llmflow.runner import render_prompt
        context = {"text": "hello"}
        rendered = render_prompt(
            {"file": "prompts/step.gpt", "inputs": {"text": "hello"}},
            context
        )
        assert "hello" in rendered
    finally:
        os.chdir(original)


# ---------------------------------------------------------------------------
# cli.py — FileNotFoundError inside pipeline must not say "Pipeline file not found"
# ---------------------------------------------------------------------------

def test_cli_run_reports_prompt_error_not_pipeline_error(tmp_path, capsys):
    """A missing prompt file must produce a clear error, not 'Pipeline file not found'."""
    import os, yaml, sys
    from unittest.mock import patch

    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()

    pipeline = {
        "name": "test",
        "version": 1,
        "steps": [{
            "name": "my_step",
            "type": "llm",
            "model": "gpt-4o",
            "prompt": {"file": "missing-prompt.gpt", "inputs": {}},
            "outputs": "result",
        }]
    }
    pipeline_file = tmp_path / "pipeline.yaml"
    pipeline_file.write_text(yaml.dump(pipeline), encoding="utf-8")

    original = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Import cli run handler — simulate what happens when run_pipeline throws
        # FileNotFoundError for a missing prompt (not the pipeline file)
        from llmflow.cli import main
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["sp", "run", "--pipeline", str(pipeline_file),
                                    "--skip-lint"]):
                main()

        # The error output must NOT say "Pipeline file not found"
        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert "Pipeline file not found" not in combined, (
            f"Got misleading error. Output:\n{combined}"
        )
        assert "missing-prompt.gpt" in combined or "Prompt" in combined, (
            f"Expected prompt path in error. Output:\n{combined}"
        )
    finally:
        os.chdir(original)
