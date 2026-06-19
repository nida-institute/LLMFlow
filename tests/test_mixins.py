"""Tests for prompt mixin expansion ({{mixin:path}} directives)."""

import pytest
from pathlib import Path

from llmflow.utils.io import expand_mixins
from llmflow.utils.linter import extract_template_variables


# ---------------------------------------------------------------------------
# expand_mixins
# ---------------------------------------------------------------------------


def test_expand_mixins_basic(tmp_path):
    mixin = tmp_path / "mixins" / "guardrails.md"
    mixin.parent.mkdir()
    mixin.write_text("Do not import background from training knowledge.\n")

    prompt_path = tmp_path / "scene-hearts.gpt"
    content = "System prompt.\n\n{{mixin:mixins/guardrails.md}}\n\nEnd."

    result = expand_mixins(content, prompt_path)

    assert "Do not import background from training knowledge." in result
    assert "{{mixin:" not in result


def test_expand_mixins_multiple(tmp_path):
    (tmp_path / "mixins").mkdir()
    (tmp_path / "mixins" / "lang.md").write_text("Write in clear English.")
    (tmp_path / "mixins" / "guard.md").write_text("Cite sources.")

    prompt_path = tmp_path / "prompt.gpt"
    content = "{{mixin:mixins/lang.md}}\n\nBody.\n\n{{mixin:mixins/guard.md}}"

    result = expand_mixins(content, prompt_path)

    assert "Write in clear English." in result
    assert "Cite sources." in result
    assert "{{mixin:" not in result


def test_expand_mixins_preserves_variables(tmp_path):
    """{{var}} references inside a mixin pass through unchanged for later substitution."""
    mixin = tmp_path / "mixins" / "context.md"
    mixin.parent.mkdir()
    mixin.write_text("This concerns the book of {{book}}.")

    prompt_path = tmp_path / "prompt.gpt"
    content = "{{mixin:mixins/context.md}}"

    result = expand_mixins(content, prompt_path)

    assert "{{book}}" in result
    assert "{{mixin:" not in result


def test_expand_mixins_no_directives(tmp_path):
    prompt_path = tmp_path / "prompt.gpt"
    content = "No mixins here, just {{book}} and {{scene}}."

    result = expand_mixins(content, prompt_path)

    assert result == content


def test_expand_mixins_missing_file_raises(tmp_path):
    prompt_path = tmp_path / "prompt.gpt"
    content = "{{mixin:mixins/missing.md}}"

    with pytest.raises(FileNotFoundError, match="missing.md"):
        expand_mixins(content, prompt_path)


def test_expand_mixins_path_relative_to_prompt_file(tmp_path):
    """Path is resolved relative to the prompt file's directory, not cwd."""
    subdir = tmp_path / "prompts" / "build-book"
    subdir.mkdir(parents=True)
    mixins_dir = tmp_path / "prompts" / "mixins"
    mixins_dir.mkdir()
    (mixins_dir / "guardrails.md").write_text("Grounded output only.")

    prompt_path = subdir / "scene-hearts.gpt"
    content = "{{mixin:../mixins/guardrails.md}}"

    result = expand_mixins(content, prompt_path)

    assert "Grounded output only." in result


def test_expand_mixins_whitespace_in_directive(tmp_path):
    """Whitespace around the path inside {{ }} is handled."""
    mixin = tmp_path / "mixins" / "lang.md"
    mixin.parent.mkdir()
    mixin.write_text("Clear English.")

    prompt_path = tmp_path / "prompt.gpt"
    content = "{{ mixin: mixins/lang.md }}"

    result = expand_mixins(content, prompt_path)

    assert "Clear English." in result


# ---------------------------------------------------------------------------
# Linter: mixin directives excluded from variable extraction
# ---------------------------------------------------------------------------


def test_extract_template_variables_ignores_mixin_directives():
    """{{mixin:path}} should not be returned as a variable reference."""
    content = "Hello {{book}}.\n\n{{mixin:mixins/guardrails.md}}\n\n{{scene}}"

    variables = extract_template_variables(content)

    assert "book" in variables
    assert "scene" in variables
    assert not any(v.startswith("mixin:") for v in variables), (
        f"mixin: directive incorrectly treated as variable: {variables}"
    )
