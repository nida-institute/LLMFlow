"""Tests: a `requires:` entry the prompt body never uses is reported, as a warning.

The contract was checked in one direction only. `validate_gpt_body_declares_all_vars` computes
`body_vars - declared` and stops, so a prompt could declare an input, oblige every calling step
to supply it, and never use it — silently. The withdrawn-`optional:` message even advises the
remedy — *"delete it if the body does not use it"* — as advice to a human rather than a check.

A **warning**, not an error: an unused entry costs a step some plumbing, but the run it produces
is correct, and a pipeline that works should not stop working because a prompt is untidy.
"""

from pathlib import Path

import pytest

from llmflow.utils.linter import lint_pipeline_full, unused_requires_warnings


def _prompt(tmp_path: Path, requires: list[str], body: str) -> Path:
    path = tmp_path / "prompts" / "p.gpt"
    path.parent.mkdir(parents=True, exist_ok=True)
    listed = "\n".join(f"  - {name}" for name in requires)
    path.write_text(
        f"---\nprompt:\n  requires:\n{listed}\n---\n{body}\n", encoding="utf-8"
    )
    return path


class TestUnusedRequires:

    def test_a_declared_name_the_body_never_uses_is_reported(self, tmp_path):
        path = _prompt(tmp_path, ["passage", "commentary"], "Read {{passage}}.")
        warnings = unused_requires_warnings(str(path))
        assert len(warnings) == 1
        assert "commentary" in warnings[0]

    def test_a_used_name_is_not_reported(self, tmp_path):
        path = _prompt(tmp_path, ["passage"], "Read {{passage}}.")
        assert unused_requires_warnings(str(path)) == []

    def test_several_unused_names_report_together(self, tmp_path):
        path = _prompt(tmp_path, ["a", "b", "c"], "Only {{a}}.")
        warnings = unused_requires_warnings(str(path))
        assert len(warnings) == 1
        assert "b" in warnings[0] and "c" in warnings[0]

    def test_the_message_names_the_prompt(self, tmp_path):
        path = _prompt(tmp_path, ["passage", "extra"], "Read {{passage}}.")
        assert "p.gpt" in unused_requires_warnings(str(path))[0]

    def test_a_prompt_with_no_requires_reports_nothing(self, tmp_path):
        path = tmp_path / "bare.gpt"
        path.write_text("---\nprompt:\n  format: Markdown\n---\nNothing here.\n", encoding="utf-8")
        assert unused_requires_warnings(str(path)) == []

    def test_an_unparseable_prompt_reports_nothing(self, tmp_path):
        """Its own defect, reported by the check that owns it — not twice."""
        path = tmp_path / "broken.gpt"
        path.write_text("no frontmatter at all\n", encoding="utf-8")
        assert unused_requires_warnings(str(path)) == []

    def test_a_dotted_name_is_left_to_the_check_that_owns_it(self, tmp_path):
        path = _prompt(tmp_path, ["scene.title"], "Read {{scene.title}}.")
        assert unused_requires_warnings(str(path)) == []


class TestThroughTheLinter:

    def _pipeline(self, tmp_path: Path, requires: list[str], body: str) -> Path:
        _prompt(tmp_path, requires, body)
        path = tmp_path / "pipeline.yaml"
        supplied = "\n".join(f'        {name}: "x"' for name in requires)
        path.write_text(
            "name: test\n"
            "variables:\n  prompts_dir: prompts\n"
            "steps:\n"
            "  - name: ask\n"
            "    type: llm\n"
            "    model: gpt-4o\n"
            "    prompt:\n"
            "      file: p.gpt\n"
            "      inputs:\n"
            f"{supplied}\n"
            "    output: answer\n"
        )
        return path

    def test_it_warns_rather_than_failing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = self._pipeline(tmp_path, ["passage", "commentary"], "Read {{passage}}.")
        result = lint_pipeline_full(str(path))
        assert result.valid, result.errors
        assert any("commentary" in w for w in result.warnings)

    def test_a_clean_prompt_warns_about_nothing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = self._pipeline(tmp_path, ["passage"], "Read {{passage}}.")
        result = lint_pipeline_full(str(path))
        assert result.valid, result.errors
        assert not any("never uses" in w for w in result.warnings)
