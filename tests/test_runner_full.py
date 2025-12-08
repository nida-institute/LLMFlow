"""Tests for src/llmflow/runner.py core functionality"""

import pytest
from unittest.mock import MagicMock, patch

from llmflow.runner import (
    handle_step_outputs,
    resolve,
    run_function_step,
    run_llm_step,
    run_plugin_step,
    run_step,
)


class TestResolve:
    """Test variable resolution with context"""

    def test_resolve_simple_variable(self):
        context = {"name": "John"}
        assert resolve("${name}", context) == "John"
        assert resolve("{name}", context) == "John"

    def test_resolve_nested_dict(self):
        context = {"user": {"name": "Alice", "age": 30}}
        assert resolve("${user.name}", context) == "Alice"

    def test_resolve_list_indexing(self):
        context = {"items": ["a", "b", "c"]}
        assert resolve("${items[0]}", context) == "a"
        assert resolve("${items[-1]}", context) == "c"

    def test_resolve_row_object(self):
        """Test resolving dot notation on Row-like objects"""
        class Row:
            def __init__(self, lemma):
                self.lemma = lemma

        context = {"row": Row("λόγος")}
        assert resolve("${row.lemma}", context) == "λόγος"

    def test_resolve_dict_recursively(self):
        context = {"base": "test", "ref": "${base}"}
        result = resolve("${ref}", context, max_depth=5)
        assert result == "test"


class TestHandleStepOutputs:
    """Test unified output handling"""

    def test_outputs_string(self):
        context = {}
        rule = {"name": "test", "outputs": "result"}
        result = "test_value"

        handle_step_outputs(rule, result, context)

        assert context["result"] == "test_value"

    def test_outputs_list(self):
        context = {}
        rule = {"name": "test", "outputs": ["out1", "out2"]}
        result = ("val1", "val2")

        handle_step_outputs(rule, result, context)

        assert context["out1"] == "val1"
        assert context["out2"] == "val2"

    def test_append_to_creates_list(self):
        context = {}
        rule = {"name": "test", "outputs": "item", "append_to": "items"}
        result = "first_item"

        handle_step_outputs(rule, result, context)

        assert "items" in context
        assert context["items"] == ["first_item"]

    def test_append_to_extends_list(self):
        context = {"items": ["existing"]}
        rule = {"name": "test", "outputs": "item", "append_to": "items"}
        result = "new_item"

        handle_step_outputs(rule, result, context)

        assert len(context["items"]) == 2
        assert context["items"][1] == "new_item"

    def test_saveas_simple(self, tmp_path):
        """Test saveas writes file correctly"""
        context = {}
        step = {
            "name": "test",
            "outputs": "content",
            "saveas": str(tmp_path / "output.txt")
        }
        result = "Hello World"

        handle_step_outputs(step, result, context, base_dir=str(tmp_path.parent))

        # Verify file was written
        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == "Hello World"

        # Verify context was updated
        assert context["content"] == "Hello World"


class TestRunFunctionStep:
    """Test function step execution"""

    def test_basic_function_execution(self):
        context = {}

        def test_func():
            return "result_value"

        import sys
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].test_func = test_func

        rule = {
            "name": "test",
            "type": "function",
            "function": "test_module.test_func",
            "outputs": "result"
        }

        # Call run_step which should handle outputs
        run_step(rule, context, {})

        assert "result" in context
        assert context["result"] == "result_value"

    def test_function_with_inputs(self):
        context = {"name": "Alice"}

        def greet(name):
            return f"Hello {name}"

        import sys
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].greet = greet

        rule = {
            "name": "greet_step",
            "type": "function",
            "function": "test_module.greet",
            "inputs": {"name": "${name}"},
            "outputs": "greeting"
        }

        run_step(rule, context, {})

        assert context["greeting"] == "Hello Alice"

    def test_function_with_append_to(self):
        context = {}

        def generate():
            return "item1"

        import sys
        sys.modules["test_module"] = MagicMock()
        sys.modules["test_module"].generate = generate

        rule = {
            "name": "gen",
            "type": "function",
            "function": "test_module.generate",
            "outputs": "item",
            "append_to": "items_list"
        }

        run_step(rule, context, {})

        assert "items_list" in context
        assert len(context["items_list"]) == 1
        assert context["items_list"][0] == "item1"


class TestRunPluginStep:
    """Test plugin step execution"""

    def test_plugin_execution(self):
        context = {}

        # Mock plugin
        def mock_plugin(config):
            return ["result1", "result2"]

        from llmflow.plugins import plugin_registry
        plugin_registry["test_plugin"] = mock_plugin

        rule = {
            "name": "test",
            "type": "test_plugin",
            "param": "value",
            "outputs": "results"
        }

        result = run_plugin_step(rule, context)

        assert result == ["result1", "result2"]

    def test_plugin_with_variable_resolution(self):
        context = {"input_path": "data.xml"}

        def mock_plugin(config):
            return f"Processed {config['path']}"

        from llmflow.plugins import plugin_registry
        plugin_registry["test_plugin"] = mock_plugin

        rule = {
            "name": "test",
            "type": "test_plugin",
            "path": "${input_path}",
            "outputs": "result"
        }

        result = run_plugin_step(rule, context)

        assert "data.xml" in result


class TestRunLLMStep:
    """Test LLM step execution"""

    @patch("llmflow.runner.render_prompt")
    @patch("llmflow.runner.call_llm")
    def test_llm_basic(self, mock_call_llm, mock_render_prompt):
        mock_render_prompt.return_value = "Rendered prompt"
        mock_call_llm.return_value = "LLM response"

        context = {}
        rule = {
            "name": "test_llm",
            "type": "llm",
            "prompt": {"file": "test.gpt", "inputs": {}},
            "outputs": "response"
        }
        pipeline_config = {}

        result = run_llm_step(rule, context, pipeline_config)

        assert result == "LLM response"
        mock_call_llm.assert_called_once()

    @patch("llmflow.runner.render_prompt")
    @patch("llmflow.runner.call_llm")
    def test_llm_with_config_override(self, mock_call_llm, mock_render_prompt):
        mock_render_prompt.return_value = "Prompt"
        mock_call_llm.return_value = "Response"

        context = {}
        rule = {
            "name": "test",
            "type": "llm",
            "prompt": {"file": "test.gpt"},
            "llm_options": {"temperature": 0.5, "max_tokens": 1000},
            "outputs": "result"
        }
        pipeline_config = {"llm_config": {"model": "gpt-4"}}

        result = run_llm_step(rule, context, pipeline_config)

        # Check that config was merged
        call_kwargs = mock_call_llm.call_args[1]
        assert call_kwargs["config"]["temperature"] == 0.5
        assert call_kwargs["config"]["model"] == "gpt-4"


class TestRunStep:
    """Test the main step dispatcher"""

    def test_dispatch_function_step(self):
        context = {}

        def test_func():
            return "value"

        import sys
        sys.modules["test_mod"] = MagicMock()
        sys.modules["test_mod"].test_func = test_func

        rule = {
            "name": "test",
            "type": "function",
            "function": "test_mod.test_func",
            "outputs": "result"
        }

        run_step(rule, context, {})

        assert context["result"] == "value"

    def test_dispatch_plugin_step(self):
        context = {}

        def mock_plugin(config):
            return "plugin_result"

        from llmflow.plugins import plugin_registry
        plugin_registry["test"] = mock_plugin

        rule = {
            "name": "test_plugin",
            "type": "test",
            "outputs": "result"
        }

        run_step(rule, context, {})

        assert context["result"] == "plugin_result"

    def test_unknown_step_type_raises_error(self):
        context = {}
        rule = {"name": "bad", "type": "nonexistent"}

        with pytest.raises(ValueError, match="Unknown step type"):
            run_step(rule, context, {})


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_function_to_llm_flow(self):
        """Test data flow from function to LLM step"""
        context = {}

        # Step 1: Function generates data
        def generate_data():
            return "Generated content"

        import sys
        sys.modules["test_mod"] = MagicMock()
        sys.modules["test_mod"].generate_data = generate_data

        step1 = {
            "name": "gen",
            "type": "function",
            "function": "test_mod.generate_data",
            "outputs": "content"
        }

        run_step(step1, context, {})

        assert "content" in context
        assert context["content"] == "Generated content"

    def test_append_to_multiple_iterations(self):
        """Test append_to across multiple step executions"""
        context = {}

        def gen_item(n):
            return f"item_{n}"

        import sys
        sys.modules["test_mod"] = MagicMock()
        sys.modules["test_mod"].gen_item = gen_item

        for i in range(3):
            rule = {
                "name": f"gen_{i}",
                "type": "function",
                "function": "test_mod.gen_item",
                "inputs": {"n": i},
                "outputs": "item",
                "append_to": "items"
            }
            run_step(rule, context, {})

        assert len(context["items"]) == 3
        assert context["items"][0] == "item_0"
        assert context["items"][2] == "item_2"

    def test_nested_for_each_append(self):
        """Test nested for-each loops with append_to - FIXED by context isolation!"""
        context = {
            "rows": [
                {"id": 1, "tags": ["a", "b"]},
                {"id": 2, "tags": ["b", "c"]},
            ]
        }

        import sys
        sys.modules["test_mod"] = MagicMock()
        sys.modules["test_mod"].collect_tag = lambda tag: tag

        rule = {
            "name": "nested_loop",
            "type": "for-each",
            "input": "${rows}",
            "item_var": "row",
            "steps": [
                {
                    "name": "inner_loop",
                    "type": "for-each",
                    "input": "${row.tags}",
                    "item_var": "tag",
                    "steps": [
                        {
                            "name": "collect",
                            "type": "function",
                            "function": "test_mod.collect_tag",
                            "inputs": {"tag": "${tag}"},
                            "outputs": "tag_value",
                            "append_to": "all_tags"
                        }
                    ]
                }
            ]
        }

        run_step(rule, context, {})

        assert sorted(context["all_tags"]) == ["a", "b", "b", "c"]
