"""Test model-parameter compatibility validation in linter."""
import pytest
from llmflow.utils.linter import validate_model_parameters


class TestModelParameterValidation:
    """Test that linter catches incompatible model-parameter combinations."""

    def test_gpt5_rejects_max_tokens(self):
        """GPT-5 should fail validation when max_tokens is specified."""
        all_steps = [
            {
                "name": "test_step",
                "type": "llm",
                "model": "gpt-5",
                "max_tokens": 1000,
            }
        ]
        pipeline_config = {}

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) > 0
        assert "max_tokens" in errors[0].lower()
        assert "not supported" in errors[0].lower()

    def test_gpt4o_accepts_max_tokens(self):
        """GPT-4o should pass validation with max_tokens."""
        all_steps = [
            {
                "name": "test_step",
                "type": "llm",
                "model": "gpt-4o",
                "max_tokens": 1000,
            }
        ]
        pipeline_config = {}

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) == 0

    def test_gpt4o_rejects_max_completion_tokens(self):
        """GPT-4o should fail validation when max_completion_tokens is specified."""
        all_steps = [
            {
                "name": "test_step",
                "type": "llm",
                "model": "gpt-4o",
                "max_completion_tokens": 2500,
            }
        ]
        pipeline_config = {}

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) > 0
        assert "max_completion_tokens" in errors[0].lower()

    def test_parameter_in_llm_options(self):
        """Should validate parameters in llm_options."""
        all_steps = [
            {
                "name": "test_step",
                "type": "llm",
                "model": "gpt-5",
                "llm_options": {
                    "max_tokens": 1000,
                }
            }
        ]
        pipeline_config = {}

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) > 0
        assert "llm_options" in errors[0]

    def test_parameter_in_pipeline_llm_config(self):
        """Should validate parameters in pipeline-level llm_config."""
        all_steps = [
            {
                "name": "test_step",
                "type": "llm",
                "model": "gpt-5",
            }
        ]
        pipeline_config = {
            "llm_config": {
                "max_tokens": 1000,
            }
        }

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) > 0
        assert "pipeline.llm_config" in errors[0]

    def test_model_from_pipeline_config(self):
        """Should use model from pipeline config if not specified in step."""
        all_steps = [
            {
                "name": "test_step",
                "type": "llm",
                "max_tokens": 1000,
            }
        ]
        pipeline_config = {
            "llm_config": {
                "model": "gpt-5",
            }
        }

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) > 0
        assert "max_tokens" in errors[0].lower()

    def test_non_llm_steps_ignored(self):
        """Should ignore non-LLM steps."""
        all_steps = [
            {
                "name": "function_step",
                "type": "function",
                "max_tokens": 1000,  # Invalid but should be ignored
            }
        ]
        pipeline_config = {}

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) == 0

    def test_o1_rejects_max_tokens(self):
        """o1 models should fail validation with max_tokens."""
        all_steps = [
            {
                "name": "test_step",
                "type": "llm",
                "model": "o1",
                "max_tokens": 1000,
            }
        ]
        pipeline_config = {}

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) > 0

    def test_o1_accepts_max_completion_tokens(self):
        """o1 models should pass validation with max_completion_tokens."""
        all_steps = [
            {
                "name": "test_step",
                "type": "llm",
                "model": "o1-mini",
                "max_completion_tokens": 5000,
            }
        ]
        pipeline_config = {}

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) == 0

    def test_multiple_errors_reported(self):
        """Should report all parameter errors across multiple steps."""
        all_steps = [
            {
                "name": "step1",
                "type": "llm",
                "model": "gpt-5",
                "max_tokens": 1000,
            },
            {
                "name": "step2",
                "type": "llm",
                "model": "gpt-4o",
                "max_completion_tokens": 2500,
            },
        ]
        pipeline_config = {}

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) == 2
        assert "step1" in errors[0] or "step 'step1'" in errors[0]
        assert "step2" in errors[1] or "step 'step2'" in errors[1]

    def test_valid_temperature_passes(self):
        """Should pass valid temperature parameter."""
        all_steps = [
            {
                "name": "test_step",
                "type": "llm",
                "model": "gpt-4o",
                "temperature": 0.7,
            }
        ]
        pipeline_config = {}

        errors = validate_model_parameters(all_steps, pipeline_config)

        assert len(errors) == 0
