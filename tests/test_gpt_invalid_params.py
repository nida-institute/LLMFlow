"""Test that invalid GPT parameters are handled properly"""
import pytest
from unittest.mock import Mock, patch
import pydantic

def test_invalid_gpt_parameters():
    """Test that invalid parameters to GPT calls raise clear errors, not hang"""
    from src.llmflow.modules.gpt_api import call_gpt_with_retry

    # Mock the model to simulate pydantic validation error
    mock_model = Mock()

    # Simulate what happens when we pass invalid params like 'timeout'
    def mock_prompt(*args, **kwargs):
        if 'timeout' in kwargs:
            # This simulates the actual pydantic validation error
            raise pydantic.ValidationError.from_exception_data(
                "ValidationError",
                [
                    {
                        "type": "extra_forbidden",
                        "loc": ("timeout",),
                        "msg": "Extra inputs are not permitted",
                        "input": kwargs['timeout'],
                    }
                ]
            )
        return Mock(text=lambda: "Valid response")

    mock_model.prompt = mock_prompt

    with patch('src.llmflow.modules.gpt_api.get_gpt_model', return_value=mock_model):
        # Test with invalid parameter should raise exception, not hang
        config = {
            'model': 'gpt-4o',
            'timeout': 'invalid_param'  # This should cause an error
        }

        with pytest.raises(Exception) as exc_info:
            call_gpt_with_retry(config, "Test prompt")

        # Should fail after retries with a clear error message
        assert "GPT call failed after maximum retries" in str(exc_info.value)


def test_valid_gpt_parameters():
    """Test that valid parameters work correctly"""
    from src.llmflow.modules.gpt_api import call_gpt_with_retry

    mock_model = Mock()
    mock_model.prompt = Mock(return_value=Mock(text=lambda: "Valid response"))

    with patch('src.llmflow.modules.gpt_api.get_gpt_model', return_value=mock_model):
        config = {
            'model': 'gpt-4o',
            'temperature': 0.7,  # Valid parameter
            'max_tokens': 1000   # Valid parameter
        }

        result = call_gpt_with_retry(config, "Test prompt")
        assert result == "Valid response"

        # Verify stream=False was passed
        mock_model.prompt.assert_called_with("Test prompt", stream=False, temperature=0.7, max_tokens=1000)


def test_gpt_validation_error_message():
    """Test that validation errors provide helpful messages"""
    from src.llmflow.modules.gpt_api import call_gpt_with_retry

    mock_model = Mock()

    def mock_prompt(*args, **kwargs):
        # Simulate actual validation error from llm library
        raise pydantic.ValidationError.from_exception_data(
            "ValidationError",
            [
                {
                    "type": "extra_forbidden",
                    "loc": ("bad_param",),
                    "msg": "Extra inputs are not permitted",
                    "input": "bad_value",
                }
            ]
        )

    mock_model.prompt = mock_prompt

    with patch('src.llmflow.modules.gpt_api.get_gpt_model', return_value=mock_model):
        config = {'model': 'gpt-4o', 'bad_param': 'bad_value'}

        # The function should fail after retries
        with pytest.raises(Exception) as exc_info:
            call_gpt_with_retry(config, "Test prompt")

        assert "GPT call failed after maximum retries" in str(exc_info.value)


if __name__ == "__main__":
    test_invalid_gpt_parameters()
    test_valid_gpt_parameters()
    test_gpt_validation_error_message()
    print("All tests passed!")