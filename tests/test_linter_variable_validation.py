"""Tests for variable reference validation in linter"""
import pytest
import tempfile
import yaml
from pathlib import Path
from llmflow.utils.linter import (
    _validate_all_variable_references,
    _extract_all_variables_from_value,
    _build_available_context,
    lint_pipeline_full
)


class TestExtractVariablesFromValue:
    """Test variable extraction from different value types"""

    def test_extract_from_string(self):
        """Test extracting variables from strings"""
        text = "Hello ${name}, your score is ${score}"
        vars = _extract_all_variables_from_value(text)
        assert vars == {"name", "score"}

    def test_extract_from_dict(self):
        """Test extracting variables from dictionaries"""
        data = {
            "greeting": "Hello ${name}",
            "info": {
                "city": "${city}",
                "country": "${country}"
            }
        }
        vars = _extract_all_variables_from_value(data)
        assert vars == {"name", "city", "country"}

    def test_extract_from_list(self):
        """Test extracting variables from lists"""
        data = ["${first}", "${second}", {"nested": "${third}"}]
        vars = _extract_all_variables_from_value(data)
        assert vars == {"first", "second", "third"}

    def test_extract_curly_braces(self):
        """Test extracting {{variable}} syntax"""
        text = "{{name}} is in {{city}}"
        vars = _extract_all_variables_from_value(text)
        assert vars == {"name", "city"}

    def test_extract_mixed_syntax(self):
        """Test extracting both ${} and {{}} syntax"""
        text = "${var1} and {{var2}}"
        vars = _extract_all_variables_from_value(text)
        assert vars == {"var1", "var2"}

    def test_extract_with_dot_notation(self):
        """Test that root variable is extracted from dot notation"""
        text = "${scene.title} and ${scene.content}"
        vars = _extract_all_variables_from_value(text)
        assert vars == {"scene"}

    def test_extract_with_indexing(self):
        """Test that root variable is extracted from array indexing"""
        text = "${items[0]} and ${items[1].name}"
        vars = _extract_all_variables_from_value(text)
        assert vars == {"items"}

    def test_no_variables(self):
        """Test text with no variables"""
        text = "Just plain text"
        vars = _extract_all_variables_from_value(text)
        assert vars == set()

    def test_empty_string(self):
        """Test empty string"""
        vars = _extract_all_variables_from_value("")
        assert vars == set()

    def test_non_string_values(self):
        """Test non-string values don't cause errors"""
        vars = _extract_all_variables_from_value(123)
        assert vars == set()

        vars = _extract_all_variables_from_value(None)
        assert vars == set()


class TestBuildAvailableContext:
    """Test context building for variable availability"""

    def test_pipeline_variables_only(self):
        """Test context with only pipeline variables"""
        available = _build_available_context(
            {"var1": "value1", "var2": "value2"},
            set(),
            None,
            None
        )
        assert available == {"var1", "var2"}

    def test_declared_outputs_only(self):
        """Test context with only declared outputs"""
        available = _build_available_context(
            {},
            {"output1", "output2"},
            None,
            None
        )
        assert available == {"output1", "output2"}

    def test_with_item_var(self):
        """Test context with for-each item_var"""
        available = _build_available_context(
            {"var1": "value"},
            {"output1"},
            "item",
            None
        )
        assert available == {"var1", "output1", "item"}

    def test_with_for_each_var(self):
        """Test context with for-each variable"""
        available = _build_available_context(
            {"var1": "value"},
            set(),
            None,
            "my_list"
        )
        assert available == {"var1", "my_list"}

    def test_all_sources(self):
        """Test context with all variable sources"""
        available = _build_available_context(
            {"pipeline_var": "value"},
            {"step_output"},
            "item",
            "list_var"
        )
        assert available == {"pipeline_var", "step_output", "item", "list_var"}


class TestValidateAllVariableReferences:
    """Test the main variable validation function"""

    def test_valid_pipeline_variable(self):
        """Test that pipeline variables are recognized"""
        steps = [
            {
                "name": "step1",
                "inputs": {"text": "${greeting}"}
            }
        ]
        pipeline_vars = {"greeting": "Hello"}
        errors = []

        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert len(errors) == 0

    def test_undefined_variable_error(self):
        """Test that undefined variables are caught"""
        steps = [
            {
                "name": "step1",
                "inputs": {"text": "${undefined_var}"}
            }
        ]
        pipeline_vars = {"other_var": "value"}
        errors = []

        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert len(errors) == 1
        assert "undefined_var" in errors[0]
        assert "step1" in errors[0]
        assert "Available:" in errors[0]

    def test_step_output_available_to_next_step(self):
        """Test that step outputs are available to subsequent steps"""
        steps = [
            {
                "name": "step1",
                "outputs": "result1"
            },
            {
                "name": "step2",
                "inputs": {"data": "${result1}"}
            }
        ]
        pipeline_vars = {}
        errors = []

        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert len(errors) == 0

    def test_step_output_not_available_before_declaration(self):
        """Test that outputs are not available before they're declared"""
        steps = [
            {
                "name": "step1",
                "inputs": {"data": "${result2}"}  # Uses result2 before it exists
            },
            {
                "name": "step2",
                "outputs": "result2"
            }
        ]
        pipeline_vars = {}
        errors = []

        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert len(errors) == 1
        assert "result2" in errors[0]

    def test_for_each_item_var(self):
        """Test that for-each item_var is available inside the loop"""
        steps = [
            {
                "name": "process_items",
                "type": "for-each",
                "in": "${items}",
                "for": "item",
                "steps": [
                    {
                        "name": "inner",
                        "inputs": {"current": "${item}"}
                    }
                ]
            }
        ]
        pipeline_vars = {"items": ["a", "b"]}
        errors = []

        # Note: This validates the parent step, not nested steps
        # The actual for-each validation would need to recursively check nested steps
        _validate_all_variable_references(steps, pipeline_vars, errors)
        # The parent level won't have errors about items since it exists in pipeline_vars
        assert len(errors) == 0

    def test_for_each_loop_index_available(self):
        """_for_each_index is available inside for-each substeps (saveas, inputs, etc.)"""
        steps = [
            {
                "name": "outer",
                "type": "for-each",
                "in": "${sections}",
                "for": "section",
                "steps": [
                    {
                        "name": "generate",
                        "type": "llm",
                        "saveas": "output/${_for_each_index}_${section}.txt",
                        "inputs": {"text": "${section}"},
                        "outputs": "result",
                    }
                ],
            }
        ]
        pipeline_vars = {"sections": []}
        errors = []
        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_for_each_loop_variable_available(self):
        """loop (and thus loop.index etc.) is available inside for-each substeps"""
        steps = [
            {
                "name": "outer",
                "type": "for-each",
                "in": "${items}",
                "for": "item",
                "steps": [
                    {
                        "name": "inner",
                        "type": "function",
                        "function": "some.fn",
                        "inputs": {"idx": "${loop.index}", "total": "${loop.total}"},
                        "outputs": "result",
                    }
                ],
            }
        ]
        pipeline_vars = {"items": []}
        errors = []
        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_multiple_fields_checked(self):
        """Test that multiple fields are checked for variables"""
        steps = [
            {
                "name": "step1",
                "inputs": {"a": "${var1}"},
                "saveas": "${output_dir}/file.txt",
                "condition": "${should_run}"
            }
        ]
        pipeline_vars = {"var1": "value", "output_dir": "./out"}
        errors = []

        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert len(errors) == 1  # should_run is missing
        assert "should_run" in errors[0]

    def test_dict_outputs(self):
        """Test that dict outputs are tracked correctly"""
        steps = [
            {
                "name": "step1",
                "outputs": {"result": "data", "status": "ok"}
            },
            {
                "name": "step2",
                "inputs": {"r": "${result}", "s": "${status}"}
            }
        ]
        pipeline_vars = {}
        errors = []

        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert len(errors) == 0

    def test_list_outputs(self):
        """Test that list outputs are tracked correctly"""
        steps = [
            {
                "name": "step1",
                "outputs": ["result1", "result2"]
            },
            {
                "name": "step2",
                "inputs": {"a": "${result1}", "b": "${result2}"}
            }
        ]
        pipeline_vars = {}
        errors = []

        _validate_all_variable_references(steps, pipeline_vars, errors)
        assert len(errors) == 0


class TestLintPipelineFull:
    """Integration tests for full pipeline linting"""

    def test_lint_catches_undefined_variable(self):
        """Test that lint_pipeline_full catches undefined variables"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            pipeline = {
                "pipeline": {
                    "name": "test_pipeline",
                    "variables": {"var1": "value1"},
                    "steps": [
                        {
                            "name": "step1",
                            "type": "function",
                            "function": "tests.test_helpers.mock_function",
                            "inputs": {
                                "a": "${var1}",
                                "p": "${undefined_var}"
                            }
                        }
                    ]
                }
            }
            yaml.dump(pipeline, f)
            pipeline_path = f.name

        try:
            result = lint_pipeline_full(pipeline_path)
            assert not result.valid
            assert len(result.errors) > 0
            assert any("undefined_var" in err for err in result.errors)
        finally:
            Path(pipeline_path).unlink()

    def test_lint_passes_with_valid_variables(self):
        """Test that lint_pipeline_full passes with all variables defined"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            pipeline = {
                "pipeline": {
                    "name": "test_pipeline",
                    "variables": {"var1": "value1", "var2": "value2"},
                    "steps": [
                        {
                            "name": "step1",
                            "type": "function",
                            "function": "tests.test_helpers.mock_function",
                            "inputs": {
                                "a": "${var1}",
                                "p": "${var2}"
                            },
                            "outputs": "result"
                        }
                    ]
                }
            }
            yaml.dump(pipeline, f)
            pipeline_path = f.name

        try:
            result = lint_pipeline_full(pipeline_path)
            # May have warnings but should be valid
            assert result.valid or len(result.errors) == 0
        finally:
            Path(pipeline_path).unlink()

    def test_lint_with_sequential_steps_and_outputs(self):
        """Test linting pipeline with sequential steps and outputs"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            pipeline = {
                "pipeline": {
                    "name": "test_pipeline",
                    "variables": {"input_data": "test"},
                    "steps": [
                        {
                            "name": "process",
                            "type": "function",
                            "function": "tests.test_helpers.mock_function",
                            "inputs": {
                                "a": "${input_data}",
                                "p": "test"
                            },
                            "outputs": "processed"
                        },
                        {
                            "name": "summarize",
                            "type": "function",
                            "function": "tests.test_helpers.mock_function",
                            "inputs": {
                                "a": "${processed}",
                                "p": "done"
                            },
                            "outputs": "summary"
                        }
                    ]
                }
            }
            yaml.dump(pipeline, f)
            pipeline_path = f.name

        try:
            result = lint_pipeline_full(pipeline_path)
            assert result.valid or len(result.errors) == 0
        finally:
            Path(pipeline_path).unlink()


def test_window_advance_inner_outputs_in_scope():
    """Variables produced by !window_advance inner step are available to later steps in the window."""
    from llmflow.utils.linter import _validate_variable_references_recursive

    steps = [
        {
            "name": "segment",
            "type": "window",
            "in": "${content}",
            "for": "window_content",
            "size": 10,
            "steps": [
                {
                    "name": "process",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${window_content}"},
                    "outputs": "window_result",
                },
                {
                    "_tag": "window_advance",
                    "name": "advance",
                    "cursor": "next_start",
                    "step": {
                        "name": "find_next",
                        "type": "function",
                        "function": "tests.test_helpers.cursor_pop",
                        "inputs": {},
                        "outputs": "next_start",
                    },
                },
                {
                    "name": "store_non_final",
                    "type": "function",
                    "condition": "${next_start is not None}",  # must see next_start
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${window_result}"},
                    "outputs": "stored",
                    "append_to": "all_results",
                },
            ],
        }
    ]

    pipeline_vars = {"content": []}
    errors = []
    _validate_variable_references_recursive(steps, pipeline_vars, set(), errors)
    assert errors == [], f"Unexpected linter errors: {errors}"


def test_window_advance_is_none_condition_no_error():
    """${cursor is None} condition in a window step does not raise a linter error."""
    from llmflow.utils.linter import _validate_variable_references_recursive

    steps = [
        {
            "name": "segment",
            "type": "window",
            "in": "${content}",
            "for": "window_content",
            "size": 10,
            "steps": [
                {
                    "_tag": "window_advance",
                    "name": "advance",
                    "cursor": "cursor",
                    "step": {
                        "name": "find_next",
                        "type": "function",
                        "function": "tests.test_helpers.cursor_pop",
                        "inputs": {},
                        "outputs": "cursor",
                    },
                },
                {
                    "name": "final_only",
                    "type": "function",
                    "condition": "${cursor is None}",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "done"},
                    "outputs": "final",
                },
            ],
        }
    ]

    pipeline_vars = {"content": []}
    errors = []
    _validate_variable_references_recursive(steps, pipeline_vars, set(), errors)
    assert errors == [], f"Unexpected linter errors: {errors}"
