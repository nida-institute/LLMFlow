import pytest
import yaml
import os
from unittest.mock import Mock, patch
from pathlib import Path

from llmflow.runner import run_pipeline


class TestRunPipeline:
    """Test the run_pipeline function with various scenarios"""

    @pytest.fixture
    def simple_pipeline(self, temp_dir):
        """Create a simple test pipeline"""
        pipeline_content = {
            "name": "test-pipeline",
            "variables": {
                "test_var": "test_value"
            },
            "steps": [
                {
                    "name": "simple_function",
                    "type": "function",
                    "function": "conftest.mock_function",
                    "inputs": {"input": "${test_var}"},
                    "outputs": "result"
                }
            ]
        }

        pipeline_path = temp_dir / "test_pipeline.yaml"
        with open(pipeline_path, 'w') as f:
            yaml.dump(pipeline_content, f)

        return str(pipeline_path)

    @pytest.fixture
    def complex_pipeline(self, temp_dir):
        """Create a more complex pipeline with multiple step types"""
        pipeline_content = {
            "name": "complex-pipeline",
            "variables": {
                "input_data": ["item1", "item2", "item3"],
                "prefix": "processed"
            },
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
                            "function": "conftest.transform_function",
                            "inputs": {
                                "item": "${item}",
                                "prefix": "${prefix}"
                            },
                            "outputs": "transformed",
                            "append_to": "results"
                        }
                    ]
                },
                {
                    "name": "save_results",
                    "type": "save",
                    "input": "${results}",
                    "filename": "output.json",
                    "format": "json"
                }
            ]
        }

        pipeline_path = temp_dir / "complex_pipeline.yaml"
        with open(pipeline_path, 'w') as f:
            yaml.dump(pipeline_content, f)

        return str(pipeline_path)

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
    @patch('llmflow.runner.importlib.import_module')
    def test_run_pipeline_basic_execution(self, mock_import, mock_lint, mock_validate, simple_pipeline):
        """Test basic pipeline execution with function step"""
        # Setup mocks
        mock_func = Mock(return_value="processed_test_value")
        mock_module = Mock()
        mock_module.mock_function = mock_func
        mock_import.return_value = mock_module
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Run pipeline
        result = run_pipeline(simple_pipeline, skip_lint=True)

        # Verify
        assert "result" in result
        assert result["result"] == "processed_test_value"
        assert result["test_var"] == "test_value"
        mock_func.assert_called_once_with(input="test_value")

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
    @patch('llmflow.runner.importlib.import_module')
    def test_run_pipeline_with_variables(self, mock_import, mock_lint, mock_validate, simple_pipeline):
        """Test pipeline execution with custom variables"""
        # Setup mocks
        mock_func = Mock(return_value="custom_result")
        mock_module = Mock()
        mock_module.mock_function = mock_func
        mock_import.return_value = mock_module
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Run with custom variables
        custom_vars = {"test_var": "custom_value", "extra_var": "extra"}
        result = run_pipeline(simple_pipeline, vars=custom_vars, skip_lint=True)

        # Verify custom variables override pipeline variables
        assert result["test_var"] == "custom_value"
        assert result["extra_var"] == "extra"
        assert result["result"] == "custom_result"
        mock_func.assert_called_once_with(input="custom_value")

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
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

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
    @patch('llmflow.runner.importlib.import_module')
    @patch('llmflow.runner._save_file_by_format')
    def test_run_pipeline_complex_workflow(self, mock_save, mock_import, mock_lint, mock_validate, complex_pipeline, temp_dir):
        """Test complex pipeline with for-each and save steps"""
        # Setup mocks
        mock_func = Mock(side_effect=lambda item, prefix: f"{prefix}_{item}")
        mock_module = Mock()
        mock_module.transform_function = mock_func
        mock_import.return_value = mock_module
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Change to temp directory for file operations
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Run pipeline
            result = run_pipeline(complex_pipeline, skip_lint=True)

            # Verify results
            assert "results" in result
            assert len(result["results"]) == 3
            assert result["results"] == ["processed_item1", "processed_item2", "processed_item3"]

            # Verify save was called
            mock_save.assert_called_once()

        finally:
            os.chdir(old_cwd)

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
    def test_run_pipeline_validation_failure(self, mock_lint, mock_validate, simple_pipeline):
        """Test pipeline execution when validation fails"""
        mock_validate.side_effect = ValueError("Template validation failed")
        mock_lint.return_value = None

        # Should raise the validation error
        with pytest.raises(ValueError, match="Template validation failed"):
            run_pipeline(simple_pipeline, skip_lint=True)

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
    @patch('llmflow.runner.importlib.import_module')
    def test_run_pipeline_step_failure(self, mock_import, mock_lint, mock_validate, simple_pipeline):
        """Test pipeline execution when a step fails"""
        # Setup mocks
        mock_func = Mock(side_effect=RuntimeError("Function failed"))
        mock_module = Mock()
        mock_module.mock_function = mock_func
        mock_import.return_value = mock_module
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Should raise the step error
        with pytest.raises(RuntimeError, match="Function failed"):
            run_pipeline(simple_pipeline, skip_lint=True)

    def test_run_pipeline_file_not_found(self):
        """Test pipeline execution with non-existent file"""
        with pytest.raises(FileNotFoundError):
            run_pipeline("nonexistent_pipeline.yaml")

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
    def test_run_pipeline_invalid_yaml(self, mock_lint, mock_validate, temp_dir):
        """Test pipeline execution with invalid YAML"""
        # Create invalid YAML file
        invalid_yaml = temp_dir / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(yaml.YAMLError):
            run_pipeline(str(invalid_yaml))

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
    def test_run_pipeline_skip_lint(self, mock_lint, mock_validate, simple_pipeline):
        """Test that linting is skipped when skip_lint=True"""
        mock_validate.return_value = None

        # Run with skip_lint=True
        run_pipeline(simple_pipeline, skip_lint=True)

        # lint_pipeline_full should only be called once
        assert mock_lint.call_count == 1

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
    def test_run_pipeline_with_lint(self, mock_lint, mock_validate, simple_pipeline):
        """Test that linting runs when skip_lint=False"""
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Run with skip_lint=False (default)
        run_pipeline(simple_pipeline, skip_lint=False)

        # lint_pipeline_full should be called twice
        assert mock_lint.call_count == 2

    @patch('llmflow.runner.validate_all_templates')
    @patch('llmflow.runner.lint_pipeline_full')
    @patch('llmflow.runner.importlib.import_module')
    def test_run_pipeline_context_preservation(self, mock_import, mock_lint, mock_validate, temp_dir):
        """Test that context is properly preserved and returned"""
        # Create pipeline with multiple steps
        pipeline_content = {
            "name": "context-test",
            "variables": {"initial": "value"},
            "steps": [
                {
                    "name": "step1",
                    "type": "function",
                    "function": "conftest.mock_function",
                    "inputs": {"input": "${initial}"},
                    "outputs": "step1_result"
                },
                {
                    "name": "step2",
                    "type": "function",
                    "function": "conftest.mock_function",
                    "inputs": {"input": "${step1_result}"},
                    "outputs": "step2_result"
                }
            ]
        }

        pipeline_path = temp_dir / "context_test.yaml"
        with open(pipeline_path, 'w') as f:
            yaml.dump(pipeline_content, f)

        # Setup mocks
        mock_func = Mock(side_effect=lambda input: f"processed_{input}")
        mock_module = Mock()
        mock_module.mock_function = mock_func
        mock_import.return_value = mock_module
        mock_validate.return_value = None
        mock_lint.return_value = None

        # Run pipeline
        result = run_pipeline(str(pipeline_path), skip_lint=True)

        # Verify context preservation
        assert result["initial"] == "value"
        assert result["step1_result"] == "processed_value"
        assert result["step2_result"] == "processed_processed_value"