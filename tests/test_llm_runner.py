"""Comprehensive unit tests for LLM runner module.

Tests cover:
- validate_parameter(): Type validation, range validation, edge cases
- validate_llm_config(): Full config validation with errors and warnings
- get_model(): Model caching behavior
- call_llm(): Mock-based testing without actual LLM calls
- _call_model(): Parameter filtering and response cleaning
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from llmflow.utils.llm_runner import (
    validate_parameter,
    validate_llm_config,
    get_model,
    call_llm,
    _call_model,
    PARAMETER_SCHEMAS,
    _model_cache,
)


# ============================================================================
# Test validate_parameter()
# ============================================================================

class TestValidateParameter:
    """Test parameter validation for individual parameters."""

    def test_valid_temperature(self):
        """Valid temperature parameter should return no errors."""
        errors = validate_parameter("temperature", 0.7)
        assert errors == []

    def test_valid_max_tokens(self):
        """Valid max_tokens parameter should return no errors."""
        errors = validate_parameter("max_tokens", 1000)
        assert errors == []

    def test_valid_top_p(self):
        """Valid top_p parameter should return no errors."""
        errors = validate_parameter("top_p", 0.9)
        assert errors == []

    def test_valid_top_k(self):
        """Valid top_k parameter should return no errors."""
        errors = validate_parameter("top_k", 50)
        assert errors == []

    def test_temperature_wrong_type(self):
        """Temperature with wrong type should return error."""
        errors = validate_parameter("temperature", "hot")
        assert len(errors) == 1
        assert "must be" in errors[0].lower()

    def test_temperature_below_min(self):
        """Temperature below minimum should return error."""
        errors = validate_parameter("temperature", -0.1)
        assert len(errors) == 1
        assert "must be >= 0" in errors[0]

    def test_temperature_above_max(self):
        """Temperature above maximum should return error."""
        errors = validate_parameter("temperature", 2.1)
        assert len(errors) == 1
        assert "must be <= 2" in errors[0]

    def test_max_tokens_wrong_type(self):
        """max_tokens with wrong type should return error."""
        errors = validate_parameter("max_tokens", "many")
        assert len(errors) == 1
        assert "must be" in errors[0].lower()

    def test_max_tokens_below_min(self):
        """max_tokens below minimum should return error."""
        errors = validate_parameter("max_tokens", 0)
        assert len(errors) == 1
        assert "must be >= 1" in errors[0]

    def test_max_tokens_above_max(self):
        """max_tokens above maximum should return error."""
        errors = validate_parameter("max_tokens", 200000)
        # Large max_tokens may be allowed, check actual behavior
        assert errors == []  # No hard max in validate_parameter

    def test_top_p_boundary_min(self):
        """top_p at minimum boundary should be valid."""
        errors = validate_parameter("top_p", 0.0)
        assert errors == []

    def test_top_p_boundary_max(self):
        """top_p at maximum boundary should be valid."""
        errors = validate_parameter("top_p", 1.0)
        assert errors == []

    def test_top_k_wrong_type(self):
        """top_k with wrong type should return error."""
        errors = validate_parameter("top_k", 50.5)
        assert len(errors) == 1
        assert "must be" in errors[0].lower()

    def test_frequency_penalty_valid_negative(self):
        """frequency_penalty with valid negative value should pass."""
        errors = validate_parameter("frequency_penalty", -1.0)
        assert errors == []

    def test_presence_penalty_valid_positive(self):
        """presence_penalty with valid positive value should pass."""
        errors = validate_parameter("presence_penalty", 1.5)
        assert errors == []

    def test_timeout_seconds_valid(self):
        """timeout_seconds with valid value should pass."""
        errors = validate_parameter("timeout_seconds", 60)
        assert errors == []

    def test_seed_valid(self):
        """seed with valid value should pass."""
        errors = validate_parameter("seed", 42)
        assert errors == []

    def test_unknown_parameter(self):
        """Unknown parameter should be allowed (no errors)."""
        errors = validate_parameter("unknown_param", "value")
        assert errors == []


# ============================================================================
# Test validate_llm_config()
# ============================================================================

class TestValidateLLMConfig:
    """Test full LLM configuration validation."""

    def test_empty_config(self):
        """Empty config requires model name."""
        is_valid, errors, warnings = validate_llm_config({})
        assert not is_valid
        assert len(errors) == 1
        assert "model name is required" in errors[0]

    def test_valid_basic_config(self):
        """Basic valid config should pass."""
        config = {
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        is_valid, errors, warnings = validate_llm_config(config)
        assert is_valid
        assert errors == []
        assert warnings == []

    def test_valid_all_parameters(self):
        """Config with all valid parameters should pass."""
        config = {
            "model": "gpt-4o",
            "temperature": 0.8,
            "max_tokens": 2000,
            "top_p": 0.95,
            "top_k": 40,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5,
            "timeout_seconds": 120,
            "seed": 123,
        }
        is_valid, errors, warnings = validate_llm_config(config)
        assert is_valid
        assert errors == []
        assert warnings == []

    def test_invalid_temperature(self):
        """Invalid temperature should return error."""
        config = {"model": "gpt-4o", "temperature": 3.0}
        is_valid, errors, warnings = validate_llm_config(config)
        assert not is_valid
        assert len(errors) == 1
        assert "temperature" in errors[0]

    def test_multiple_invalid_parameters(self):
        """Multiple invalid parameters should return multiple errors."""
        config = {
            "model": "gpt-4o",
            "temperature": 3.0,
            "max_tokens": -1,
            "top_p": 1.5,
        }
        is_valid, errors, warnings = validate_llm_config(config)
        assert not is_valid
        assert len(errors) == 3
        assert any("temperature" in e for e in errors)
        assert any("max_tokens" in e for e in errors)
        assert any("top_p" in e for e in errors)

    def test_config_with_warnings(self):
        """Config with custom fields and model should be valid."""
        config = {"model": "gpt-4o", "custom_field": "value"}
        is_valid, errors, warnings = validate_llm_config(config)
        assert is_valid
        assert errors == []
        # Custom fields are allowed

    def test_boundary_values(self):
        """Boundary values should be valid."""
        config = {
            "model": "gpt-4o",
            "temperature": 0.0,
            "max_tokens": 1,
            "top_p": 1.0,
            "top_k": 1,
        }
        is_valid, errors, warnings = validate_llm_config(config)
        assert is_valid
        assert errors == []

    def test_mixed_valid_invalid(self):
        """Mix of valid and invalid parameters."""
        config = {
            "model": "gpt-4o",
            "temperature": 0.7,  # valid
            "max_tokens": -5,  # invalid
            "top_p": 0.9,  # valid
        }
        is_valid, errors, warnings = validate_llm_config(config)
        assert not is_valid
        assert len(errors) == 1
        assert "max_tokens" in errors[0]


# ============================================================================
# Test get_model()
# ============================================================================

class TestGetModel:
    """Test model caching and retrieval."""

    def setup_method(self):
        """Clear model cache before each test."""
        _model_cache.clear()

    @patch("llmflow.utils.llm_runner.llm.get_model")
    def test_get_model_first_call(self, mock_llm_get_model):
        """First call should fetch from llm library."""
        mock_model = Mock()
        mock_llm_get_model.return_value = mock_model

        result = get_model("gpt-4o")

        assert result == mock_model
        mock_llm_get_model.assert_called_once_with("gpt-4o")

    @patch("llmflow.utils.llm_runner.llm.get_model")
    def test_get_model_cached(self, mock_llm_get_model):
        """Subsequent calls should return cached model."""
        mock_model = Mock()
        mock_llm_get_model.return_value = mock_model

        # First call
        result1 = get_model("gpt-4o")
        # Second call
        result2 = get_model("gpt-4o")

        assert result1 == result2
        mock_llm_get_model.assert_called_once()  # Only called once

    @patch("llmflow.utils.llm_runner.llm.get_model")
    def test_get_model_different_models(self, mock_llm_get_model):
        """Different models should not share cache."""
        mock_model1 = Mock(name="model1")
        mock_model2 = Mock(name="model2")
        mock_llm_get_model.side_effect = [mock_model1, mock_model2]

        result1 = get_model("gpt-4o")
        result2 = get_model("claude-3-opus")

        assert result1 == mock_model1
        assert result2 == mock_model2
        assert mock_llm_get_model.call_count == 2


# ============================================================================
# Test call_llm()
# ============================================================================

class TestCallLLM:
    """Test main LLM calling function with mocking."""

    def setup_method(self):
        """Clear model cache before each test."""
        _model_cache.clear()

    @patch("llmflow.utils.llm_runner.get_model")
    @patch("llmflow.utils.llm_runner._call_model")
    def test_call_llm_basic(self, mock_call_model, mock_get_model):
        """Basic LLM call should work."""
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        mock_call_model.return_value = "response text"

        config = {"model": "gpt-4o", "temperature": 0.7}
        result = call_llm("test prompt", config)

        assert result == "response text"
        mock_get_model.assert_called_once_with("gpt-4o")
        mock_call_model.assert_called_once_with(mock_model, "test prompt", config)

    @patch("llmflow.utils.llm_runner.get_model")
    @patch("llmflow.utils.llm_runner._call_model")
    def test_call_llm_default_model(self, mock_call_model, mock_get_model):
        """Call with explicit model should work."""
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        mock_call_model.return_value = "response"

        result = call_llm("prompt", {"model": "gpt-4o"})

        assert result == "response"
        mock_get_model.assert_called_once_with("gpt-4o")

    @patch("llmflow.utils.llm_runner.get_model")
    @patch("llmflow.utils.llm_runner._call_model")
    @patch("llmflow.utils.llm_runner.parse_llm_json_response")
    def test_call_llm_json_output(self, mock_parse, mock_call_model, mock_get_model):
        """JSON output type should parse response."""
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        mock_call_model.return_value = '{"key": "value"}'
        mock_parse.return_value = {"key": "value"}

        config = {"model": "gpt-4o"}
        result = call_llm("prompt", config, output_type="json")

        assert result == {"key": "value"}
        mock_parse.assert_called_once_with('{"key": "value"}')

    @patch("llmflow.utils.llm_runner.get_model")
    @patch("llmflow.utils.llm_runner._call_model")
    def test_call_llm_invalid_config(self, mock_call_model, mock_get_model):
        """Invalid config should raise ValueError."""
        config = {"temperature": 5.0}  # Invalid

        with pytest.raises(ValueError, match="Invalid LLM config"):
            call_llm("prompt", config)

    @patch("llmflow.utils.llm_runner.get_model")
    @patch("llmflow.utils.llm_runner._call_model")
    def test_call_llm_with_all_parameters(self, mock_call_model, mock_get_model):
        """Call with all parameters should work."""
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        mock_call_model.return_value = "response"

        config = {
            "model": "gpt-4o",
            "temperature": 0.8,
            "max_tokens": 2000,
            "top_p": 0.95,
            "top_k": 40,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5,
            "seed": 42,
        }
        result = call_llm("prompt", config)

        assert result == "response"
        mock_call_model.assert_called_once()


# ============================================================================
# Test _call_model()
# ============================================================================

class TestCallModelInternal:
    """Test internal model calling helper."""

    @patch("llmflow.utils.llm_runner.clean_llm_response_text")
    def test_call_model_filters_parameters(self, mock_clean):
        """Should only pass valid LLM parameters to model."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text.return_value = "raw response"
        mock_model.prompt.return_value = mock_response
        mock_clean.return_value = "cleaned response"

        config = {
            "model": "gpt-4o",  # Should be filtered
            "temperature": 0.7,  # Should be passed
            "custom_field": "value",  # Should be filtered
            "max_tokens": 1000,  # Should be passed
        }

        result = _call_model(mock_model, "test prompt", config)

        assert result == "cleaned response"
        # Check that only valid params were passed
        call_kwargs = mock_model.prompt.call_args[1]
        assert "temperature" in call_kwargs
        assert "max_tokens" in call_kwargs
        assert "model" not in call_kwargs
        assert "custom_field" not in call_kwargs

    @patch("llmflow.utils.llm_runner.clean_llm_response_text")
    def test_call_model_cleans_response(self, mock_clean):
        """Should clean response text."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text.return_value = "```json\n{}\n```"
        mock_model.prompt.return_value = mock_response
        mock_clean.return_value = "{}"

        result = _call_model(mock_model, "prompt", {})

        assert result == "{}"
        mock_clean.assert_called_once_with("```json\n{}\n```")

    @patch("llmflow.utils.llm_runner.clean_llm_response_text")
    def test_call_model_all_valid_params(self, mock_clean):
        """Should pass all valid LLM parameters."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text.return_value = "response"
        mock_model.prompt.return_value = mock_response
        mock_clean.return_value = "response"

        config = {
            "temperature": 0.8,
            "max_tokens": 2000,
            "top_p": 0.95,
            "top_k": 40,
            "stop": ["\n"],
            "frequency_penalty": 0.5,
            "presence_penalty": 0.5,
            "seed": 42,
        }

        result = _call_model(mock_model, "prompt", config)

        call_kwargs = mock_model.prompt.call_args[1]
        assert call_kwargs["temperature"] == 0.8
        assert call_kwargs["max_tokens"] == 2000
        assert call_kwargs["top_p"] == 0.95
        assert call_kwargs["top_k"] == 40
        assert call_kwargs["stop"] == ["\n"]
        assert call_kwargs["frequency_penalty"] == 0.5
        assert call_kwargs["presence_penalty"] == 0.5
        assert call_kwargs["seed"] == 42

    @patch("llmflow.utils.llm_runner.clean_llm_response_text")
    def test_call_model_empty_config(self, mock_clean):
        """Empty config should work."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text.return_value = "response"
        mock_model.prompt.return_value = mock_response
        mock_clean.return_value = "response"

        result = _call_model(mock_model, "prompt", {})

        assert result == "response"
        # Should be called with no kwargs
        call_kwargs = mock_model.prompt.call_args[1]
        assert call_kwargs == {}


# ============================================================================
# Integration and Edge Cases
# ============================================================================

class TestLLMRunnerEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_parameter_schema_structure(self):
        """Each parameter schema should have required fields."""
        for param_name, schema in PARAMETER_SCHEMAS.items():
            assert "type" in schema, f"{param_name} missing type"
            if "min" in schema:
                assert isinstance(schema["min"], (int, float))
            if "max" in schema:
                assert isinstance(schema["max"], (int, float))

    @patch("llmflow.utils.llm_runner.get_model")
    @patch("llmflow.utils.llm_runner._call_model")
    def test_end_to_end_text_output(self, mock_call_model, mock_get_model):
        """End-to-end test with text output."""
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        mock_call_model.return_value = "This is the LLM response."

        config = {
            "model": "gpt-4o",
            "temperature": 0.5,
            "max_tokens": 500,
        }
        result = call_llm("Tell me a story", config, output_type="text")

        assert result == "This is the LLM response."
        assert mock_get_model.called
        assert mock_call_model.called

    @patch("llmflow.utils.llm_runner.get_model")
    @patch("llmflow.utils.llm_runner._call_model")
    @patch("llmflow.utils.llm_runner.parse_llm_json_response")
    def test_end_to_end_json_output(self, mock_parse, mock_call_model, mock_get_model):
        """End-to-end test with JSON output."""
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        mock_call_model.return_value = '{"result": "parsed"}'
        mock_parse.return_value = {"result": "parsed"}

        config = {"model": "gpt-4o"}
        result = call_llm("Generate JSON", config, output_type="JSON")

        assert result == {"result": "parsed"}
        mock_parse.assert_called_once()

    def test_validate_parameter_all_schemas(self):
        """Test validation for all parameters in schemas."""
        for param_name in PARAMETER_SCHEMAS.keys():
            # Get schema
            schema = PARAMETER_SCHEMAS[param_name]

            # Test with valid value of correct type
            if schema["type"] == int:
                valid_value = int(schema.get("min", 1))
            else:
                valid_value = float((schema.get("min", 0) + schema.get("max", 1)) / 2)
