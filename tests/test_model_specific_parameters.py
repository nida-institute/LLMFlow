"""
Test model-specific parameter validation.

This test suite validates that parameter validation respects model families,
allowing or rejecting parameters based on what each model actually supports.
"""

import pytest
from llmflow.utils.llm_runner import (
    get_model_family,
    get_valid_parameters,
    validate_model_parameter,
)


class TestModelFamilyDetection:
    """Test that models are correctly categorized into families."""

    def test_gpt5_family_detection(self):
        """GPT-5 models should be detected as gpt-5 family."""
        assert get_model_family("gpt-5") == "gpt-5"
        assert get_model_family("gpt-5-mini") == "gpt-5"
        assert get_model_family("gpt-5-nano") == "gpt-5"

    def test_o3_mini_is_gpt5_family(self):
        """o3-mini uses GPT-5 parameter set."""
        assert get_model_family("o3-mini") == "gpt-5"
        assert get_model_family("o4") == "gpt-5"

    def test_o1_family_detection(self):
        """o1 reasoning models should be detected as o1 family."""
        assert get_model_family("o1") == "o1"
        assert get_model_family("o1-mini") == "o1"
        assert get_model_family("o1-preview") == "o1"

    def test_gpt4_family_detection(self):
        """GPT-4 models should be detected as gpt-4 family."""
        assert get_model_family("gpt-4") == "gpt-4"
        assert get_model_family("gpt-4o") == "gpt-4"
        assert get_model_family("gpt-4-turbo") == "gpt-4"
        assert get_model_family("gpt-3.5-turbo") == "gpt-4"  # Uses same params

    def test_claude_family_detection(self):
        """Claude models should be detected as claude family."""
        assert get_model_family("claude-3.7-sonnet") == "claude"
        assert get_model_family("claude-3-opus") == "claude"
        assert get_model_family("claude-4") == "claude"

    def test_gemini_family_detection(self):
        """Gemini models should be detected as gemini family."""
        assert get_model_family("gemini-2.5-pro") == "gemini"
        assert get_model_family("gemini-pro") == "gemini"
        assert get_model_family("gemini-flash") == "gemini"

    def test_unknown_model_defaults_to_gpt4(self):
        """Unknown models should default to gpt-4 parameter set."""
        assert get_model_family("unknown-model-xyz") == "gpt-4"


class TestValidParametersForFamily:
    """Test that each model family has the correct parameter set."""

    def test_gpt5_valid_parameters(self):
        """GPT-5 family should accept max_completion_tokens, not max_tokens."""
        params = get_valid_parameters("gpt-5")
        assert "max_completion_tokens" in params
        assert "max_tokens" not in params
        assert "temperature" in params
        assert "top_p" in params

    def test_o1_limited_parameters(self):
        """o1 family has very restricted parameter set."""
        params = get_valid_parameters("o1")
        assert "max_completion_tokens" in params
        # o1 doesn't support temperature/top_p customization
        assert "temperature" not in params
        assert "top_p" not in params

    def test_gpt4_valid_parameters(self):
        """GPT-4 family should accept max_tokens."""
        params = get_valid_parameters("gpt-4o")
        assert "max_tokens" in params
        assert "max_completion_tokens" not in params
        assert "temperature" in params
        assert "stop" in params

    def test_claude_valid_parameters(self):
        """Claude family has different parameter naming."""
        params = get_valid_parameters("claude-3.7-sonnet")
        assert "max_tokens" in params  # Claude still uses max_tokens
        assert "top_k" in params  # Claude-specific
        assert "stop_sequences" in params  # Different from OpenAI's 'stop'

    def test_gemini_valid_parameters(self):
        """Gemini uses camelCase parameter naming."""
        params = get_valid_parameters("gemini-2.5-pro")
        assert "maxOutputTokens" in params  # camelCase
        assert "topP" in params
        assert "topK" in params


class TestModelSpecificParameterValidation:
    """Test that parameter validation respects model families."""

    def test_gpt4_accepts_max_tokens(self):
        """GPT-4 models accept max_tokens parameter."""
        errors = validate_model_parameter("gpt-4o", "max_tokens", 1000)
        assert errors == []

    def test_gpt5_accepts_max_completion_tokens(self):
        """GPT-5 models accept max_completion_tokens parameter."""
        errors = validate_model_parameter("gpt-5", "max_completion_tokens", 1000)
        assert errors == []

    def test_gpt5_rejects_max_tokens(self):
        """GPT-5 models should reject max_tokens with helpful message."""
        errors = validate_model_parameter("gpt-5", "max_tokens", 1000)
        assert len(errors) > 0
        assert "max_completion_tokens" in errors[0].lower()

    def test_gpt4_rejects_max_completion_tokens(self):
        """GPT-4 models should reject max_completion_tokens."""
        errors = validate_model_parameter("gpt-4o", "max_completion_tokens", 1000)
        assert len(errors) > 0

    def test_o1_rejects_temperature(self):
        """o1 models don't support temperature parameter."""
        errors = validate_model_parameter("o1", "temperature", 0.7)
        assert len(errors) > 0

    def test_o1_accepts_max_completion_tokens(self):
        """o1 models accept max_completion_tokens."""
        errors = validate_model_parameter("o1-mini", "max_completion_tokens", 5000)
        assert errors == []

    def test_claude_accepts_max_tokens(self):
        """Claude models accept max_tokens parameter."""
        errors = validate_model_parameter("claude-3.7-sonnet", "max_tokens", 1000)
        assert errors == []

    def test_claude_accepts_top_k(self):
        """Claude models accept top_k parameter."""
        errors = validate_model_parameter("claude-3.7-sonnet", "top_k", 40)
        assert errors == []

    def test_gemini_accepts_camelcase_params(self):
        """Gemini models accept camelCase parameters."""
        errors = validate_model_parameter("gemini-2.5-pro", "maxOutputTokens", 2000)
        assert errors == []

    def test_universal_parameter_temperature(self):
        """Temperature should work for most models (except o1)."""
        assert validate_model_parameter("gpt-4o", "temperature", 0.7) == []
        assert validate_model_parameter("gpt-5", "temperature", 0.7) == []
        assert validate_model_parameter("claude-3.7-sonnet", "temperature", 0.7) == []
        assert len(validate_model_parameter("o1", "temperature", 0.7)) > 0

    def test_type_validation_still_works(self):
        """Type validation should still catch type errors."""
        errors = validate_model_parameter("gpt-4o", "temperature", "not-a-number")
        assert len(errors) > 0
        assert "type" in errors[0].lower() or "must be" in errors[0].lower()

    def test_range_validation_still_works(self):
        """Range validation should still catch out-of-range values."""
        errors = validate_model_parameter("gpt-4o", "temperature", 5.0)
        assert len(errors) > 0

    def test_unknown_parameter_passes_through(self):
        """Unknown parameters should pass through (let API validate)."""
        errors = validate_model_parameter("gpt-4o", "custom_param", "value")
        assert errors == []


class TestParameterAutoTranslation:
    """Test automatic parameter translation for cross-model compatibility."""

    def test_suggest_max_completion_tokens_for_gpt5(self):
        """When max_tokens is used with GPT-5, suggest max_completion_tokens."""
        errors = validate_model_parameter("gpt-5", "max_tokens", 1000)
        assert any("max_completion_tokens" in err for err in errors)

    def test_suggest_max_tokens_for_gpt4_if_using_max_completion_tokens(self):
        """When max_completion_tokens is used with GPT-4, suggest max_tokens."""
        errors = validate_model_parameter("gpt-4o", "max_completion_tokens", 1000)
        assert any("max_tokens" in err for err in errors)


class TestBackwardCompatibility:
    """Test that existing pipelines don't break."""

    def test_gpt4o_still_works_as_before(self):
        """Existing GPT-4o configs should continue working."""
        params = get_valid_parameters("gpt-4o")
        assert "max_tokens" in params
        assert "temperature" in params
        assert validate_model_parameter("gpt-4o", "max_tokens", 4096) == []

    def test_unknown_params_still_pass_through(self):
        """Unknown parameters should still be allowed (for future-proofing)."""
        # This maintains the "let API validate" philosophy for truly unknown params
        errors = validate_model_parameter("gpt-4o", "future_param_2026", 123)
        assert errors == []


class TestJSONCapabilities:
    """Test JSON schema support across model families."""

    def test_gpt4_accepts_response_format(self):
        """GPT-4 models support response_format parameter."""
        schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "test_schema",
                "schema": {"type": "object", "properties": {}}
            }
        }
        errors = validate_model_parameter("gpt-4o", "response_format", schema)
        assert errors == []

    def test_gpt5_accepts_response_format(self):
        """GPT-5 models support response_format parameter."""
        schema = {"type": "json_object"}
        errors = validate_model_parameter("gpt-5", "response_format", schema)
        assert errors == []

    def test_o1_rejects_response_format(self):
        """o1 models do not support response_format."""
        schema = {"type": "json_object"}
        errors = validate_model_parameter("o1", "response_format", schema)
        assert len(errors) > 0
        assert "not supported" in errors[0].lower()

    def test_o1_mini_rejects_response_format(self):
        """o1-mini also lacks response_format support."""
        errors = validate_model_parameter("o1-mini", "response_format", {})
        assert len(errors) > 0

    def test_gemini_accepts_response_mime_type(self):
        """Gemini models support response_mime_type parameter."""
        errors = validate_model_parameter("gemini-2.5-pro", "response_mime_type", "application/json")
        assert errors == []

    def test_gemini_accepts_response_schema(self):
        """Gemini models support response_schema parameter."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        errors = validate_model_parameter("gemini-2.5-pro", "response_schema", schema)
        assert errors == []

    def test_claude_rejects_response_format(self):
        """Claude models do not have native JSON schema support."""
        errors = validate_model_parameter("claude-3.7-sonnet", "response_format", {})
        assert len(errors) > 0

    def test_claude_rejects_response_schema(self):
        """Claude doesn't support Gemini's response_schema either."""
        errors = validate_model_parameter("claude-3.7-sonnet", "response_schema", {})
        assert len(errors) > 0

    def test_gpt4_rejects_gemini_json_params(self):
        """GPT-4 shouldn't accept Gemini's JSON parameters."""
        errors = validate_model_parameter("gpt-4o", "response_mime_type", "application/json")
        assert len(errors) > 0

        errors = validate_model_parameter("gpt-4o", "response_schema", {})
        assert len(errors) > 0

    def test_gemini_rejects_openai_response_format(self):
        """Gemini shouldn't accept OpenAI's response_format."""
        errors = validate_model_parameter("gemini-2.5-pro", "response_format", {})
        assert len(errors) > 0


class TestCrossModelJSONParameterGuidance:
    """Test that helpful error messages guide users to correct JSON parameters."""

    def test_response_format_on_gemini_suggests_alternative(self):
        """Using response_format on Gemini should suggest response_schema."""
        errors = validate_model_parameter("gemini-2.5-pro", "response_format", {})
        # Should suggest using response_mime_type/response_schema instead
        assert len(errors) > 0

    def test_response_schema_on_gpt_suggests_alternative(self):
        """Using response_schema on GPT should suggest response_format."""
        errors = validate_model_parameter("gpt-4o", "response_schema", {})
        # Should suggest using response_format instead
        assert len(errors) > 0
