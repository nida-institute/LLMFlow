"""
Test suite for GPT streaming fix.

This tests that the stream=False fix prevents hanging.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from llmflow.modules.gpt_api import call_gpt_with_retry


class TestGPTStreamingFix:
    """Test that GPT calls don't hang due to streaming"""

    def test_gpt_call_uses_stream_false(self):
        """Test that call_gpt_with_retry passes stream=False to prevent hanging"""
        # Mock the model object returned by get_gpt_model
        mock_model = MagicMock()
        mock_model.prompt = MagicMock(return_value="Test response")

        with patch('llmflow.modules.gpt_api.get_gpt_model', return_value=mock_model):
            # Make a test call
            config = {
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 100
            }
            response = call_gpt_with_retry(config, "Test prompt")

            # Verify prompt was called
            mock_model.prompt.assert_called()

            # Get the call arguments
            args, kwargs = mock_model.prompt.call_args

            # Verify stream=False was passed
            assert 'stream' in kwargs
            assert kwargs['stream'] is False

            # Verify other parameters were passed
            assert kwargs.get('temperature') == 0.7
            assert kwargs.get('max_tokens') == 100

    def test_gpt_retry_mechanism(self):
        """Test that retry mechanism works with stream=False"""
        # Mock model that fails twice then succeeds
        mock_model = MagicMock()
        mock_model.prompt = MagicMock(
            side_effect=[
                Exception("First failure"),
                Exception("Second failure"),
                "Success response"
            ]
        )

        with patch('llmflow.modules.gpt_api.get_gpt_model', return_value=mock_model):
            config = {"model": "gpt-4o"}
            response = call_gpt_with_retry(config, "Test prompt", max_attempts=3)

            # Should have been called 3 times
            assert mock_model.prompt.call_count == 3

            # All calls should have stream=False
            for call in mock_model.prompt.call_args_list:
                _, kwargs = call
                assert kwargs['stream'] is False

            assert response == "Success response"

    def test_gpt_call_completes_quickly(self):
        """Test that GPT calls complete without hanging"""
        # Mock a response that would hang if streaming
        def mock_prompt(prompt, **kwargs):
            if kwargs.get('stream', True):
                # Simulate hanging with streaming
                time.sleep(10)  # This would cause test to fail
            return "Quick response"

        mock_model = MagicMock()
        mock_model.prompt = MagicMock(side_effect=mock_prompt)

        with patch('llmflow.modules.gpt_api.get_gpt_model', return_value=mock_model):
            start_time = time.time()
            config = {"model": "gpt-4o"}
            response = call_gpt_with_retry(config, "Test prompt")
            elapsed = time.time() - start_time

            # Should complete quickly (under 1 second)
            assert elapsed < 1.0
            assert response == "Quick response"

    def test_system_prompt_with_stream_false(self):
        """Test that system prompts work correctly with stream=False"""
        mock_model = MagicMock()
        mock_model.prompt = MagicMock(return_value="Response with system")

        with patch('llmflow.modules.gpt_api.get_gpt_model', return_value=mock_model):
            config = {
                "model": "gpt-4o",
                "system": "You are a helpful assistant"
            }
            response = call_gpt_with_retry(config, "User prompt")

            # Verify system prompt was passed along with stream=False
            args, kwargs = mock_model.prompt.call_args
            assert kwargs.get('system') == "You are a helpful assistant"
            assert kwargs['stream'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])