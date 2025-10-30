from unittest.mock import patch

import pytest
import yaml

from llmflow.runner import run_pipeline


class TestRunPipeline:
    """Test the run_pipeline function with various scenarios"""

    @pytest.fixture
    def simple_pipeline(self, tmp_path):
        """Create a simple test pipeline"""
        pipeline_content = {
            "name": "test-pipeline",
            "variables": {"test_var": "test_value"},
            "llm_config": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000},
            "steps": [
                {
                    "name": "simple_function",
                    "type": "function",
                    "function": "tests.test_helpers.mock_function",
                    "inputs": {"a": "${test_var}", "p": "processed"},
                    "outputs": "result",
                }
            ],
        }

        pipeline_path = tmp_path / "test_pipeline.yaml"
        with open(pipeline_path, "w") as f:
            yaml.dump(pipeline_content, f)

        return str(pipeline_path)

    @pytest.fixture
    def complex_pipeline(self, tmp_path):
        """Create a more complex pipeline with for-each"""
        pipeline_content = {
            "name": "complex-pipeline",
            "variables": {"input_data": ["item1", "item2", "item3"]},
            "llm_config": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000},
            "steps": [
                {
                    "name": "process_items",
                    "type": "for-each",
                    "input": "${input_data}",
                    "item_var": "item",
                    "steps": [
                        {
                            "name": "transform_item",
                            "type": "function",
                            "function": "tests.test_helpers.transform_function",
                            "inputs": {
                                "a": "${item}",  # Fixed: transform_function expects 'a' and 'p'
                                "p": "processed",
                            },
                            "outputs": "transformed",
                            "append_to": "results",
                        }
                    ],
                }
            ],
        }

        pipeline_path = tmp_path / "complex_pipeline.yaml"
        with open(pipeline_path, "w") as f:
            yaml.dump(pipeline_content, f)

        return str(pipeline_path)

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_basic_execution(
        self, mock_lint, mock_validate, simple_pipeline
    ):
        """Test basic pipeline execution with function step"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Run pipeline
        result = run_pipeline(simple_pipeline, skip_lint=True)

        # Verify
        assert "result" in result
        assert result["result"] == "test_value_processed"
        assert result["test_var"] == "test_value"

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_with_variables(
        self, mock_lint, mock_validate, simple_pipeline
    ):
        """Test pipeline execution with custom variables"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Run with custom variables
        custom_vars = {"test_var": "custom_value"}
        result = run_pipeline(simple_pipeline, vars=custom_vars, skip_lint=True)

        # Verify custom variables override pipeline variables
        assert result["test_var"] == "custom_value"
        assert result["result"] == "custom_value_processed"

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_dry_run(self, mock_lint, mock_validate, simple_pipeline):
        """Test pipeline dry run mode"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Run in dry run mode
        result = run_pipeline(simple_pipeline, dry_run=True, skip_lint=True)

        # In dry run, steps should not execute but context should be initialized
        assert "test_var" in result
        assert result["test_var"] == "test_value"
        assert "result" not in result  # Function didn't execute

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_complex_workflow(
        self, mock_lint, mock_validate, complex_pipeline
    ):
        """Test complex pipeline with for-each and append_to"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Run pipeline
        result = run_pipeline(complex_pipeline, skip_lint=True)

        # Verify results
        assert "results" in result
        assert len(result["results"]) == 3
        assert result["results"] == [
            "item1_processed",
            "item2_processed",
            "item3_processed",
        ]

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_validation_failure(
        self, mock_lint, mock_validate, simple_pipeline
    ):
        """Test pipeline execution when validation fails"""
        mock_validate.side_effect = ValueError("Template validation failed")
        mock_lint.return_value = None

        # Should raise the validation error
        with pytest.raises(ValueError, match="Template validation failed"):
            run_pipeline(simple_pipeline, skip_lint=True)

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_step_failure(self, mock_lint, mock_validate, simple_pipeline):
        """Test pipeline execution when a step fails"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        with patch(
            "tests.test_helpers.mock_function", side_effect=Exception("Mock failure")
        ):
            with pytest.raises(Exception, match="Mock failure"):
                run_pipeline(simple_pipeline, skip_lint=True)

    def test_run_pipeline_file_not_found(self):
        """Test pipeline execution with non-existent file"""
        with pytest.raises(SystemExit):
            run_pipeline("nonexistent_pipeline.yaml")

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_invalid_yaml(self, mock_lint, mock_validate, tmp_path):
        """Test pipeline execution with invalid YAML"""
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises((SystemExit, Exception)):  # Accept SystemExit or YAML parsing errors
            run_pipeline(str(invalid_yaml))

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_skip_lint(self, mock_lint, mock_validate, simple_pipeline):
        """Test that linting is skipped when skip_lint=True"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Run with skip_lint=True
        result = run_pipeline(simple_pipeline, skip_lint=True)

        # lint_pipeline_full should not be called
        mock_lint.assert_not_called()
        # But validate_all_templates should still be called
        mock_validate.assert_called_once()
        assert result["result"] == "test_value_processed"

    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_with_lint(self, mock_lint, simple_pipeline):
        """Test that linting runs when skip_lint=False"""
        mock_lint.return_value = None

        # Run with skip_lint=False (default)
        result = run_pipeline(simple_pipeline, skip_lint=False)

        # lint_pipeline_full should be called (it includes template validation)
        mock_lint.assert_called_once()
        assert result["result"] == "test_value_processed"

    @patch("llmflow.runner.validate_all_templates")
    @patch("llmflow.runner.lint_pipeline_full")
    def test_run_pipeline_context_preservation(
        self, mock_lint, mock_validate, tmp_path
    ):
        """Test that context is properly preserved and returned"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Create pipeline with multiple steps
        pipeline_content = {
            "name": "context-test",
            "variables": {"initial": "value"},
            "llm_config": {  # Added required llm_config
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            "steps": [
                {
                    "name": "step1",
                    "type": "function",
                    "function": "tests.test_helpers.mock_function",
                    "inputs": {"a": "${initial}", "p": "step1"},
                    "outputs": "step1_result",
                },
                {
                    "name": "step2",
                    "type": "function",
                    "function": "tests.test_helpers.mock_function",
                    "inputs": {"a": "${step1_result}", "p": "step2"},
                    "outputs": "step2_result",
                },
            ],
        }
        pipeline_path = tmp_path / "context_pipeline.yaml"
        with open(pipeline_path, "w") as f:
            yaml.dump(pipeline_content, f)

        result = run_pipeline(str(pipeline_path), skip_lint=True)

        # Verify context preservation
        assert result["initial"] == "value"
        assert result["step1_result"] == "value_step1"
        assert result["step2_result"] == "value_step1_step2"
