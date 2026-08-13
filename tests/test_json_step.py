"""Tests for type: json step (TDD — written before implementation)."""
import pytest
from llmflow.runner import run_json_step
from llmflow.utils.linter import lint_pipeline_steps, _validate_all_variable_references


class TestRunJsonStep:
    def test_basic_object_construction(self):
        context = {"scene_id": "MRK-001", "ref": "Mark 1:1"}
        step = {"name": "build", "type": "json", "output": "obj",
                "value": {"scene_id": "${scene_id}", "ref": "${ref}"}}
        run_json_step(step, context)
        assert context["obj"] == {"scene_id": "MRK-001", "ref": "Mark 1:1"}

    def test_array_value(self):
        context = {"a": "foo", "b": "bar"}
        step = {"name": "build", "type": "json", "output": "items",
                "value": ["${a}", "${b}"]}
        run_json_step(step, context)
        assert context["items"] == ["foo", "bar"]

    def test_nested_object(self):
        context = {"scene_id": "MRK-001", "ref": "Mark 1:1"}
        step = {"name": "build", "type": "json", "output": "obj",
                "value": {"meta": {"scene_id": "${scene_id}", "ref": "${ref}"}}}
        run_json_step(step, context)
        assert context["obj"] == {"meta": {"scene_id": "MRK-001", "ref": "Mark 1:1"}}

    def test_dot_notation_variable(self):
        context = {"scene": {"scene_id": "MRK-001", "characters": ["Jesus", "John"]}}
        step = {"name": "build", "type": "json", "output": "obj",
                "value": {"id": "${scene.scene_id}", "cast": "${scene.characters}"}}
        run_json_step(step, context)
        assert context["obj"]["id"] == "MRK-001"
        assert context["obj"]["cast"] == ["Jesus", "John"]

    def test_list_value_preserved_as_list(self):
        context = {"characters": ["Jesus", "John", "crowd"]}
        step = {"name": "build", "type": "json", "output": "obj",
                "value": {"cast": "${characters}"}}
        run_json_step(step, context)
        assert context["obj"]["cast"] == ["Jesus", "John", "crowd"]

    def test_unknown_variable_passes_through(self):
        context = {}
        step = {"name": "build", "type": "json", "output": "obj",
                "value": {"x": "${missing_var}"}}
        run_json_step(step, context)
        assert context["obj"]["x"] == "${missing_var}"

    def test_missing_output_raises(self):
        step = {"name": "build", "type": "json", "value": {"x": "y"}}
        with pytest.raises(ValueError, match="output"):
            run_json_step(step, {})


class TestJsonStepUsesOutputOnly:
    """`output` is the one spelling — there is no `outputs` alias (see test_one_syntax.py)."""

    def test_outputs_is_not_honoured(self):
        context = {}
        step = {"name": "build", "type": "json", "outputs": "legacy", "value": {"x": 1}}
        with pytest.raises(ValueError, match="output"):
            run_json_step(step, context)
        assert "legacy" not in context

    def test_outputs_is_a_lint_error_pointing_at_output(self):
        errors = lint_pipeline_steps(
            [{"name": "build", "type": "json", "outputs": "obj", "value": {"x": "1"}}]
        )
        assert any("outputs" in e and "output" in e for e in errors)


class TestLintJsonStep:
    def test_valid_json_step_passes(self):
        steps = [{"name": "build", "type": "json", "output": "obj",
                  "value": {"x": "1"}}]
        errors = lint_pipeline_steps(steps)
        assert not errors

    def test_missing_output_is_linter_error(self):
        steps = [{"name": "build", "type": "json", "value": {"x": "1"}}]
        errors = lint_pipeline_steps(steps)
        assert any("output" in e for e in errors)

    def test_missing_value_is_linter_error(self):
        steps = [{"name": "build", "type": "json", "output": "obj"}]
        errors = lint_pipeline_steps(steps)
        assert any("value" in e for e in errors)

    def test_output_registered_for_subsequent_steps(self):
        pipeline_vars = {}
        steps = [
            {"name": "build", "type": "json", "output": "my_obj",
             "value": {"x": "1"}},
            {"name": "use", "type": "llm", "inputs": {"variables": {"v": "${my_obj}"}}},
        ]
        errors = []
        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert not any("my_obj" in e for e in errors)

    def test_value_variables_validated(self):
        pipeline_vars = {}
        steps = [
            {"name": "build", "type": "json", "output": "obj",
             "value": {"x": "${nonexistent_var}"}},
        ]
        errors = []
        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert any("nonexistent_var" in e for e in errors)
