"""Tests for schema_file support in response_format configuration."""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import functions to test
from llmflow.utils.llm_runner import (
    _load_schema_from_file,
    _expand_response_format_schema,
    call_llm,
)


class TestSchemaFileLoading:
    """Test _load_schema_from_file function."""

    def test_loads_valid_schema(self, tmp_path):
        """Should load and parse a valid JSON schema file."""
        schema_file = tmp_path / "test_schema.json"
        schema_content = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
        schema_file.write_text(json.dumps(schema_content))

        result = _load_schema_from_file(str(schema_file))

        assert result == schema_content
        assert result["type"] == "object"
        assert "name" in result["properties"]

    def test_raises_on_missing_file(self):
        """Should raise FileNotFoundError for missing schema file."""
        with pytest.raises(FileNotFoundError, match="Schema file not found"):
            _load_schema_from_file("nonexistent_schema.json")

    def test_raises_on_invalid_json(self, tmp_path):
        """Should raise JSONDecodeError for invalid JSON."""
        schema_file = tmp_path / "invalid.json"
        schema_file.write_text("{invalid json")

        with pytest.raises(json.JSONDecodeError):
            _load_schema_from_file(str(schema_file))


class TestResponseFormatExpansion:
    """Test _expand_response_format_schema function."""

    def test_expands_schema_file(self, tmp_path):
        """Should expand schema_file to inline schema."""
        # Create test schema file
        schema_file = tmp_path / "test_schema.json"
        schema_content = {"type": "object", "properties": {"id": {"type": "string"}}}
        schema_file.write_text(json.dumps(schema_content))

        # Config with schema_file
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "test_schema",
                "strict": True,
                "schema_file": str(schema_file)
            }
        }

        result = _expand_response_format_schema(response_format)

        # Should have loaded schema and removed schema_file
        assert "schema" in result["json_schema"]
        assert "schema_file" not in result["json_schema"]
        assert result["json_schema"]["schema"] == schema_content
        assert result["json_schema"]["name"] == "test_schema"
        assert result["json_schema"]["strict"] is True

    def test_leaves_inline_schema_unchanged(self):
        """Should not modify response_format without schema_file."""
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "test",
                "strict": True,
                "schema": {"type": "object"}
            }
        }

        result = _expand_response_format_schema(response_format)

        # Should be identical to input
        assert result == response_format
        assert "schema" in result["json_schema"]
        assert "schema_file" not in result["json_schema"]

    def test_handles_json_object_mode(self):
        """Should handle simple json_object mode without modification."""
        response_format = {"type": "json_object"}

        result = _expand_response_format_schema(response_format)

        assert result == response_format

    def test_does_not_modify_original(self, tmp_path):
        """Should not modify the original response_format dict."""
        schema_file = tmp_path / "test.json"
        schema_file.write_text('{"type": "object"}')

        original = {
            "type": "json_schema",
            "json_schema": {
                "name": "test",
                "schema_file": str(schema_file)
            }
        }
        original_copy = original.copy()

        _expand_response_format_schema(original)

        # Original should be unchanged (still has schema_file)
        assert original == original_copy
        assert "schema_file" in original["json_schema"]


class TestSchemaFileIntegration:
    """Integration tests with call_llm (requires OPENAI_API_KEY)."""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set"
    )
    def test_schema_file_with_real_api(self):
        """Should successfully call OpenAI API with schema_file."""
        schema_path = Path(__file__).parent / "schemas" / "discourse_analysis.json"

        # Build config with schema_file
        config = {
            "model": "gpt-4o-2024-08-06",
            "temperature": 0.7,
            "max_tokens": 500,
            "output_type": "json",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "discourse_analysis",
                    "strict": True,
                    "schema_file": str(schema_path)
                }
            }
        }

        prompt = "Analyze the Gospel of Mark 1:1-8. Provide a single pericope."

        result = call_llm(prompt, config, "json")

        # Should return valid structure
        assert "content" in result
        assert "usage" in result

        # Content should be parsed JSON matching schema
        content = result["content"]
        assert isinstance(content, dict)
        assert "book" in content
        assert "pericopes" in content
        assert isinstance(content["pericopes"], list)

        # Usage stats should be present
        assert result["usage"]["prompt_tokens"] > 0
        assert result["usage"]["completion_tokens"] > 0

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set"
    )
    def test_schema_file_produces_valid_json(self):
        """Schema from file should guarantee 100% valid JSON."""
        schema_path = Path(__file__).parent / "schemas" / "discourse_analysis.json"

        config = {
            "model": "gpt-4o-2024-08-06",
            "output_type": "json",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "strict": True,
                    "schema_file": str(schema_path)
                }
            }
        }

        # Run 5 times to verify reliability
        for i in range(5):
            result = call_llm(f"Test run {i+1}. Provide one pericope from Mark.", config, "json")

            # Should never fail to parse
            assert isinstance(result["content"], dict)
            assert "book" in result["content"]
            assert "pericopes" in result["content"]


class TestSchemaFileMocked:
    """Unit tests with mocked OpenAI client."""

    @patch("openai.OpenAI")
    def test_mocked_api_receives_expanded_schema(self, mock_openai_class, tmp_path):
        """Mocked OpenAI client should receive expanded schema, not schema_file."""
        # Create test schema
        schema_file = tmp_path / "test.json"
        schema_content = {"type": "object", "properties": {"name": {"type": "string"}}}
        schema_file.write_text(json.dumps(schema_content))

        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"name": "test"}'))]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_client.chat.completions.create.return_value = mock_response

        # Config with schema_file
        config = {
            "model": "gpt-4o-2024-08-06",
            "output_type": "json",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "strict": True,
                    "schema_file": str(schema_file)
                }
            }
        }

        call_llm("Test prompt", config, "json")

        # Verify OpenAI client was called
        assert mock_client.chat.completions.create.called

        # Get the actual call arguments
        call_args = mock_client.chat.completions.create.call_args

        # Should have response_format with expanded schema (no schema_file)
        assert "response_format" in call_args[1]
        response_format = call_args[1]["response_format"]
        assert "json_schema" in response_format
        assert "schema" in response_format["json_schema"]
        assert "schema_file" not in response_format["json_schema"]
        assert response_format["json_schema"]["schema"] == schema_content


class TestSchemaFileErrorHandling:
    """Test error handling for schema_file feature."""

    @patch("openai.OpenAI")
    def test_missing_schema_file_raises_clear_error(self, mock_openai_class):
        """Should raise clear error when schema_file doesn't exist."""
        config = {
            "model": "gpt-4o-2024-08-06",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "schema_file": "nonexistent_schema.json"
                }
            }
        }

        with pytest.raises(FileNotFoundError, match="Schema file not found"):
            call_llm("Test", config, "json")

    @patch("openai.OpenAI")
    def test_invalid_schema_json_raises_clear_error(self, mock_openai_class, tmp_path):
        """Should raise clear error when schema file is invalid JSON."""
        schema_file = tmp_path / "invalid.json"
        schema_file.write_text("{not valid json")

        config = {
            "model": "gpt-4o-2024-08-06",
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "schema_file": str(schema_file)
                }
            }
        }

        with pytest.raises(json.JSONDecodeError):
            call_llm("Test", config, "json")
