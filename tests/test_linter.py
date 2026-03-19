import pytest
from llmflow.utils.linter import lint_pipeline_steps, ALLOWED_STEP_KEYS


def test_disallowed_keyword_fails():
    steps = [
        {"name": "bad-step", "type": "llm", "foo": "bar"}  # 'foo' is not allowed
    ]
    errors = lint_pipeline_steps(steps)
    assert errors, "Should fail for unknown keyword"
    assert "unknown keyword 'foo'" in errors[0]

def test_after_continue_allowed():
    steps = [
        {"name": "step1", "type": "llm", "after": "continue"}
    ]
    errors = lint_pipeline_steps(steps)
    assert not errors, "Should pass for after: continue"

def test_after_exit_allowed():
    steps = [
        {"name": "step2", "type": "llm", "after": "exit"}
    ]
    errors = lint_pipeline_steps(steps)
    assert not errors, "Should pass for after: exit"


class TestGptBodyDeclaresAllVars:
    """Linter must catch .gpt files that use {{var}} without declaring it in requires: or optional:."""

    def test_undeclared_var_in_body_is_error(self, tmp_path):
        gpt = tmp_path / "bad.gpt"
        gpt.write_text(
            "---\nrequires: []\noptional: []\n---\nuser: |\n  Hello {{name}}\n",
            encoding="utf-8",
        )
        from llmflow.utils.linter import validate_gpt_body_declares_all_vars

        errors = validate_gpt_body_declares_all_vars(str(gpt))
        assert len(errors) == 1
        assert "name" in errors[0]

    def test_required_var_in_body_passes(self, tmp_path):
        gpt = tmp_path / "good.gpt"
        gpt.write_text(
            "---\nrequires:\n  - name\noptional: []\n---\nuser: |\n  Hello {{name}}\n",
            encoding="utf-8",
        )
        from llmflow.utils.linter import validate_gpt_body_declares_all_vars

        errors = validate_gpt_body_declares_all_vars(str(gpt))
        assert not errors

    def test_optional_var_in_body_passes(self, tmp_path):
        gpt = tmp_path / "optional.gpt"
        gpt.write_text(
            "---\nrequires: []\noptional:\n  - tone\n---\nuser: |\n  {{tone}} Hello!\n",
            encoding="utf-8",
        )
        from llmflow.utils.linter import validate_gpt_body_declares_all_vars

        errors = validate_gpt_body_declares_all_vars(str(gpt))
        assert not errors

    def test_hello_gpt_in_repo_passes(self):
        """The canonical prompts/hello.gpt in the repo must declare all its {{vars}}."""
        from llmflow.utils.linter import validate_gpt_body_declares_all_vars

        errors = validate_gpt_body_declares_all_vars("prompts/hello.gpt")
        assert not errors, f"prompts/hello.gpt has undeclared template vars: {errors}"

    def test_lint_pipeline_full_catches_undeclared_var(self, tmp_path, monkeypatch):
        """lint_pipeline_full must fail when a .gpt body uses an undeclared {{var}}."""
        monkeypatch.chdir(tmp_path)
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "bad.gpt").write_text(
            "---\nrequires: []\noptional: []\n---\nuser: |\n  Hello {{name}}\n",
            encoding="utf-8",
        )
        pipeline = tmp_path / "pipeline.yaml"
        pipeline.write_text(
            "name: test\nvariables: {}\nsteps:\n"
            "  - name: greet\n    type: llm\n    prompt:\n      file: bad.gpt\n"
            "      inputs: {}\n    outputs: result\n",
            encoding="utf-8",
        )
        from llmflow.utils.linter import lint_pipeline_full

        result = lint_pipeline_full(str(pipeline))
        assert not result.valid
        assert any("name" in e for e in result.errors)