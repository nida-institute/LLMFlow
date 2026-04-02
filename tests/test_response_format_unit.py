"""Unit tests for response_format detection and routing logic.

These tests use mocking to verify behavior without making actual API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestResponseFormatDetection:
    """Test that call_llm() correctly detects response_format and routes to direct client."""

    @patch("llmflow.utils.llm_runner._call_openai_with_response_format")
    def test_detects_json_schema_and_routes_to_direct_client(self, mock_direct_call):
        """When response_format is present, should route to direct OpenAI client."""
        from llmflow.utils.llm_runner import call_llm

        mock_direct_call.return_value = {
            "content": {"result": "success"},
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

        config = {
            "model": "gpt-4o-2024-08-06",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "strict": True,
                    "schema": {"type": "object", "properties": {"result": {"type": "string"}}}
                }
            }
        }

        result = call_llm("Test prompt", config, output_type="json")

        # Should have called the direct client function
        mock_direct_call.assert_called_once()
        # Returns the dict with content and usage
        assert result == {"content": {"result": "success"}, "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}

    @patch("llmflow.utils.llm_runner._call_model")
    def test_without_response_format_uses_llm_package(self, mock_llm_call):
        """Without response_format, should use normal llm package path."""
        from llmflow.utils.llm_runner import call_llm

        mock_llm_call.return_value = {
            "content": "response text",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

        config = {"model": "gpt-4o"}

        result = call_llm("Test prompt", config)

        # Should have called the llm package path
        mock_llm_call.assert_called_once()
        # For text output, returns the dict directly
        assert result == {"content": "response text", "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}

    @patch("llmflow.utils.llm_runner._call_openai_with_response_format")
    def test_detects_basic_json_object_mode(self, mock_direct_call):
        """Should route to direct client for json_object mode too."""
        from llmflow.utils.llm_runner import call_llm

        mock_direct_call.return_value = {
            "content": {"message": "hello"},
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        }

        config = {
            "model": "gpt-4o-2024-08-06",
            "response_format": {"type": "json_object"}
        }

        result = call_llm("Test prompt", config, output_type="json")

        mock_direct_call.assert_called_once()
        assert result == {"content": {"message": "hello"}, "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}}

    @patch("llmflow.utils.llm_runner._call_openai_with_response_format")
    def test_passes_all_config_to_direct_client(self, mock_direct_call):
        """Should pass full config dict to direct client function."""
        from llmflow.utils.llm_runner import call_llm

        mock_direct_call.return_value = {
            "content": {"data": "test"},
            "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3}
        }

        config = {
            "model": "gpt-4o-2024-08-06",
            "temperature": 0.5,
            "max_tokens": 500,
            "response_format": {"type": "json_schema", "json_schema": {"name": "test"}}
        }

        call_llm("Test", config, output_type="json")

        # Verify config was passed through
        call_args = mock_direct_call.call_args
        assert call_args[0][1] == config  # Second argument is config
        assert call_args[0][1]["temperature"] == 0.5
        assert call_args[0][1]["max_tokens"] == 500


class TestDirectOpenAIClient:
    """Test _call_openai_with_response_format() function."""

    @patch("openai.OpenAI")
    def test_constructs_api_params_correctly(self, mock_openai_class):
        """Should build correct parameters for OpenAI API."""
        from llmflow.utils.llm_runner import _call_openai_with_response_format

        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"result": "ok"}'))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "model": "gpt-4o-2024-08-06",
            "temperature": 0.3,
            "max_tokens": 200,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "test_schema"}
            }
        }

        _call_openai_with_response_format("Test prompt", config, output_type="json")

        # Verify API call
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]

        assert call_kwargs["model"] == "gpt-4o-2024-08-06"
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 200
        assert "response_format" in call_kwargs
        assert call_kwargs["response_format"]["type"] == "json_schema"

    @patch("openai.OpenAI")
    def test_handles_max_completion_tokens_parameter(self, mock_openai_class):
        """Should use max_completion_tokens for newer models."""
        from llmflow.utils.llm_runner import _call_openai_with_response_format

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"ok": true}'))]
        mock_response.usage = Mock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "model": "gpt-4o-2024-08-06",
            "max_completion_tokens": 1000,
            "response_format": {"type": "json_object"}
        }

        _call_openai_with_response_format("Test", config, output_type="json")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "max_completion_tokens" in call_kwargs
        assert call_kwargs["max_completion_tokens"] == 1000
        assert "max_tokens" not in call_kwargs  # Should not include both

    @patch("openai.OpenAI")
    def test_passes_through_openai_specific_params(self, mock_openai_class):
        """Should pass top_p, frequency_penalty, etc."""
        from llmflow.utils.llm_runner import _call_openai_with_response_format

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{}'))]
        mock_response.usage = Mock(prompt_tokens=1, completion_tokens=1, total_tokens=2)
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "model": "gpt-4o",
            "top_p": 0.9,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.2,
            "seed": 42,
            "stop": ["END"],
            "response_format": {"type": "json_object"}
        }

        _call_openai_with_response_format("Test", config, output_type="json")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["frequency_penalty"] == 0.5
        assert call_kwargs["presence_penalty"] == 0.2
        assert call_kwargs["seed"] == 42
        assert call_kwargs["stop"] == ["END"]

    @patch("openai.OpenAI")
    def test_returns_parsed_json_when_requested(self, mock_openai_class):
        """Should parse JSON response when output_type='json'."""
        from llmflow.utils.llm_runner import _call_openai_with_response_format

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"name": "test", "count": 42}'))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "model": "gpt-4o",
            "response_format": {"type": "json_object"}
        }

        result = _call_openai_with_response_format("Test", config, output_type="json")

        assert result["content"] == {"name": "test", "count": 42}
        assert result["usage"]["prompt_tokens"] == 10

    @patch("openai.OpenAI")
    def test_returns_text_when_not_json_output(self, mock_openai_class):
        """Should return raw text when output_type != 'json'."""
        from llmflow.utils.llm_runner import _call_openai_with_response_format

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"name": "test"}'))]
        mock_response.usage = Mock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "model": "gpt-4o",
            "response_format": {"type": "json_object"}
        }

        result = _call_openai_with_response_format("Test", config, output_type="text")

        # Should return raw string, not parsed JSON
        assert result["content"] == '{"name": "test"}'


class TestErrorHandling:
    """Test error conditions and edge cases."""

    @patch("openai.OpenAI")
    def test_raises_on_openai_api_error(self, mock_openai_class):
        """Should propagate OpenAI API errors."""
        from llmflow.utils.llm_runner import _call_openai_with_response_format

        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error: Rate limit exceeded")

        config = {
            "model": "gpt-4o",
            "response_format": {"type": "json_object"}
        }

        with pytest.raises(Exception, match="API Error: Rate limit exceeded"):
            _call_openai_with_response_format("Test", config)

    @patch("openai.OpenAI")
    def test_handles_missing_usage_stats(self, mock_openai_class):
        """Should handle case where usage stats are None."""
        from llmflow.utils.llm_runner import _call_openai_with_response_format

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"ok": true}'))]
        mock_response.usage = None  # No usage stats
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "model": "gpt-4o",
            "response_format": {"type": "json_object"}
        }

        result = _call_openai_with_response_format("Test", config, output_type="json")

        # Should default to 0
        assert result["usage"]["prompt_tokens"] == 0
        assert result["usage"]["completion_tokens"] == 0
        assert result["usage"]["total_tokens"] == 0

    @patch("openai.OpenAI")
    def test_handles_empty_content(self, mock_openai_class):
        """Should handle case where content is None or empty."""
        from llmflow.utils.llm_runner import _call_openai_with_response_format

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=None))]
        mock_response.usage = Mock(prompt_tokens=1, completion_tokens=1, total_tokens=2)
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "model": "gpt-4o",
            "response_format": {"type": "json_object"}
        }

        result = _call_openai_with_response_format("Test", config)

        # Should return empty string
        assert result["content"] == ""

    @patch("openai.OpenAI")
    def test_json_parse_error_logged_but_raised(self, mock_openai_class):
        """Should log JSON parse errors and re-raise."""
        from llmflow.utils.llm_runner import _call_openai_with_response_format

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='invalid json {'))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_client.chat.completions.create.return_value = mock_response

        config = {
            "model": "gpt-4o",
            "response_format": {"type": "json_object"}
        }

        # Should raise because JSON parsing fails
        with pytest.raises(Exception):  # parse_llm_json_response will raise
            _call_openai_with_response_format("Test", config, output_type="json")


class TestIntegrationWithExistingCode:
    """Test that new code integrates properly with existing patterns."""

    @patch("llmflow.utils.llm_runner._call_openai_with_response_format")
    def test_preserves_telemetry_usage_stats(self, mock_direct_call):
        """Usage stats should flow through for telemetry."""
        from llmflow.utils.llm_runner import call_llm

        mock_direct_call.return_value = {
            "content": {"result": "test"},
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }

        config = {
            "model": "gpt-4o-2024-08-06",
            "response_format": {"type": "json_object"}
        }

        result = call_llm("Test", config, output_type="json")

        # Returns dict with content and usage
        assert result["content"] == {"result": "test"}
        assert result["usage"]["prompt_tokens"] == 100

    @patch("llmflow.utils.llm_runner._call_openai_with_response_format")
    def test_works_with_step_config_merging(self, mock_direct_call):
        """Should work with merged configs from pipeline steps."""
        from llmflow.utils.llm_runner import call_llm

        mock_direct_call.return_value = {
            "content": {"data": "merged"},
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        }

        # Simulates config after runner.py merges universal defaults → llm_config → step_options
        merged_config = {
            "model": "gpt-4o-2024-08-06",
            "temperature": 0.4,  # from llm_config
            "max_tokens": 2000,  # from llm_config
            "response_format": {  # from step
                "type": "json_schema",
                "json_schema": {"name": "step_schema"}
            }
        }

        result = call_llm("Test", merged_config, output_type="json")

        assert result["content"] == {"data": "merged"}
        """Non-OpenAI models can't use response_format - should error clearly."""
        from llmflow.utils.llm_runner import call_llm

        config = {
            "model": "claude-3-opus-20240229",  # Not OpenAI
            "response_format": {"type": "json_object"}
        }

        # The detection logic checks for OpenAI model families
        # This should either skip the direct client or error appropriately
        # For now, the code doesn't validate - that's a future enhancement
        # This test documents expected future behavior
        pass  # TODO: Add model family detection in call_llm()
