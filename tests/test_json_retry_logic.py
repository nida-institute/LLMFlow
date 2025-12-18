"""Test that JSON parse failures trigger LLM retries."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from llmflow.runner import run_pipeline


def test_json_parse_failure_triggers_retry():
    """Test that malformed JSON triggers 3 retry attempts."""

    # Track call count
    call_count = [0]

    def mock_call_model(*args, **kwargs):
        """Mock model that returns malformed JSON first 2 times, then valid JSON."""
        call_count[0] += 1
        if call_count[0] <= 2:
            # Return malformed JSON (unterminated string)
            return '{"scene": "incomplete string'
        else:
            # Return valid JSON on 3rd attempt
            return '{"scene": "complete"}'

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create prompt file
        prompt_file = Path(tmpdir) / "test.gpt"
        prompt_file.write_text("---\nprompt:\n  requires: []\n---\nGenerate JSON")

        pipeline = {
            "name": "test-json-retry",
            "steps": [
                {
                    "name": "generate_json",
                    "type": "llm",
                    "prompt": {
                        "file": str(prompt_file)
                    },
                    "output_type": "json",
                    "outputs": "result"
                }
            ]
        }

        # Patch _call_model which is called by call_llm
        with patch('llmflow.utils.llm_runner._call_model', side_effect=mock_call_model):
            with patch('time.sleep'):  # Skip actual sleep delays
                context = run_pipeline(pipeline, skip_lint=True)

        # Should have retried 3 times
        assert call_count[0] == 3, f"Expected 3 calls, got {call_count[0]}"

        # Final result should be the valid JSON
        assert context["result"] == {"scene": "complete"}


def test_json_parse_failure_exhausts_retries():
    """Test that 3 consecutive JSON failures raises error."""

    call_count = [0]

    def mock_call_model_always_fails(*args, **kwargs):
        """Mock model that always returns malformed JSON."""
        call_count[0] += 1
        return '{"always": "broken'

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create prompt file
        prompt_file = Path(tmpdir) / "test.gpt"
        prompt_file.write_text("---\nprompt:\n  requires: []\n---\nGenerate JSON")

        pipeline = {
            "name": "test-json-retry-fail",
            "steps": [
                {
                    "name": "generate_json",
                    "type": "llm",
                    "prompt": {
                        "file": str(prompt_file)
                    },
                    "output_type": "json",
                    "outputs": "result"
                }
            ]
        }

        # Patch _call_model which is called by call_llm
        with patch('llmflow.utils.llm_runner._call_model', side_effect=mock_call_model_always_fails):
            with patch('time.sleep'):  # Skip actual sleep delays
                with pytest.raises(ValueError, match="JSON parse failed"):
                    run_pipeline(pipeline, skip_lint=True)

        # Should have attempted 3 times before giving up
        assert call_count[0] == 3, f"Expected 3 retry attempts, got {call_count[0]}"


def test_valid_json_no_retry():
    """Test that valid JSON doesn't trigger retries."""

    call_count = [0]

    def mock_call_model_valid(*args, **kwargs):
        """Mock model that returns valid JSON on first try."""
        call_count[0] += 1
        return '{"scene": "valid"}'

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create prompt file
        prompt_file = Path(tmpdir) / "test.gpt"
        prompt_file.write_text("---\nprompt:\n  requires: []\n---\nGenerate JSON")

        pipeline = {
            "name": "test-json-no-retry",
            "steps": [
                {
                    "name": "generate_json",
                    "type": "llm",
                    "prompt": {
                        "file": str(prompt_file)
                    },
                    "output_type": "json",
                    "outputs": "result"
                }
            ]
        }

        # Patch _call_model which is called by call_llm
        with patch('llmflow.utils.llm_runner._call_model', side_effect=mock_call_model_valid):
            context = run_pipeline(pipeline, skip_lint=True)

        # Should only call once
        assert call_count[0] == 1, f"Expected 1 call, got {call_count[0]}"
        assert context["result"] == {"scene": "valid"}
