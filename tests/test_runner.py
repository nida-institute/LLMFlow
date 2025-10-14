import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path so we can import llmflow
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llmflow.runner import (
    resolve, render_prompt, run_function_step,
    run_llm_step, run_for_each_step, validate_pipeline_expressions,
    save_content_to_file, PipelineLogger
)

class TestVariableResolution:
    """Test the resolve function with various scenarios"""

    def test_resolve_simple_string(self):
        context = {"name": "John", "age": 30}
        assert resolve("Hello ${name}", context) == "Hello John"
        assert resolve("Age: ${age}", context) == "Age: 30"

    def test_resolve_exact_variable(self):
        """Test that exact variables return native types"""
        context = {
            "my_list": [1, 2, 3],
            "my_dict": {"key": "value"},
            "my_string": "hello"
        }
        assert resolve("${my_list}", context) == [1, 2, 3]
        assert resolve("${my_dict}", context) == {"key": "value"}
        assert resolve("${my_string}", context) == "hello"

    def test_resolve_dot_notation(self):
        context = {
            "user": {"name": "John", "details": {"age": 30}},
            "passage_info": {"filename_prefix": "test123"}
        }
        assert resolve("${user.name}", context) == "John"
        assert resolve("${user.details.age}", context) == 30
        assert resolve("${passage_info.filename_prefix}_file.txt", context) == "test123_file.txt"

    def test_resolve_list_indexing(self):
        context = {
            "items": ["a", "b", "c"],
            "nested": {"list": [{"name": "first"}, {"name": "second"}]}
        }
        assert resolve("${items[0]}", context) == "a"
        assert resolve("${items[-1]}", context) == "c"
        assert resolve("${nested.list[1].name}", context) == "second"

    def test_resolve_missing_variable(self):
        context = {"foo": "bar"}
        assert resolve("${missing}", context) == "${missing}"
        assert resolve("${foo.missing}", context) == "${foo.missing}"

    def test_resolve_nested_structures(self):
        context = {"key": "value", "num": 42}
        input_dict = {"a": "${key}", "b": {"c": "${num}"}}
        expected = {"a": "value", "b": {"c": 42}}
        assert resolve(input_dict, context) == expected


class TestPipelineLogger:
    """Test logging functionality"""

    def test_logger_initialization(self):
        logger = Logger()
        assert logger.logger.name == 'llmflow'
        assert len(logger.logger.handlers) == 2  # file and console

    def test_summarize_value(self):
        logger = Logger()
        assert logger._summarize_value("short") == '"short"'
        assert logger._summarize_value("x" * 200) == "<string: 200 chars>"
        assert logger._summarize_value([1, 2, 3]) == "<array: 3 int items>"
        assert logger._summarize_value({"a": 1, "b": 2}) == "<dict: 2 keys>"
        assert logger._summarize_value([]) == "[]"


class TestStepExecution:
    """Test individual step runners"""

    @patch('llmflow.runner.importlib.import_module')
    def test_run_function_step(self, mock_import):
        # Mock the function
        mock_func = Mock(return_value="result")
        mock_module = Mock()
        mock_module.my_function = mock_func
        mock_import.return_value = mock_module

        # Test step configuration
        rule = {
            "name": "test_step",
            "type": "function",
            "function": "my_module.my_function",
            "inputs": {"arg1": "${var1}", "arg2": "static"},
            "outputs": "result_var"
        }
        context = {"var1": "value1"}

        # Run the step
        run_function_step(rule, context)

        # Verify
        mock_func.assert_called_once_with(arg1="value1", arg2="static")
        assert context["result_var"] == "result"

    @patch('llmflow.runner.call_gpt_with_retry')
    @patch('llmflow.runner.render_prompt')
    def test_run_llm_step(self, mock_render, mock_gpt):
        # Setup mocks
        mock_render.return_value = "rendered prompt"
        mock_gpt.return_value = "LLM response"

        rule = {
            "name": "test_llm",
            "type": "llm",
            "prompt": {"file": "test.gpt", "inputs": {"var": "${input}"}},
            "outputs": "response"
        }
        context = {"input": "test"}
        pipeline_config = {"llm_config": {"model": "gpt-4"}}

        # Run the step
        result = run_llm_step(rule, context, pipeline_config)

        # Verify
        assert result == "LLM response"
        assert context["response"] == "LLM response"
        mock_render.assert_called_once()
        mock_gpt.assert_called_once()


class TestFileOperations:
    """Test file saving functionality"""

    def test_save_content_to_file_text(self, temp_dir):
        content = "Hello, world!"
        file_path = temp_dir / "test.txt"

        result = save_content_to_file(content, str(file_path))

        assert file_path.exists()
        assert file_path.read_text() == content
        assert result == str(file_path)

    def test_save_content_to_file_json(self, temp_dir):
        import json
        content = {"key": "value", "number": 42}
        file_path = temp_dir / "test.json"

        save_content_to_file(content, str(file_path))

        assert file_path.exists()
        saved_data = json.loads(file_path.read_text())
        assert saved_data == content


class TestValidation:
    """Test validation functions"""

    def test_validate_pipeline_expressions_success(self):
        context = {"var1": "value1", "var2": "value2"}
        # Should not raise
        validate_pipeline_expressions("${var1}", context)
        validate_pipeline_expressions({"key": "${var2}"}, context)

    def test_validate_pipeline_expressions_failure(self):
        context = {"var1": "value1"}
        with pytest.raises(ValueError, match="Unresolved pipeline expression"):
            validate_pipeline_expressions("${missing_var}", context)
