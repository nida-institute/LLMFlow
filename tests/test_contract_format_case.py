import pytest
from llmflow.utils.linter import validate_prompt_format

class TestContractFormatCase:
    """Test the format validation case sensitivity issue"""

    def test_format_case_insensitive(self):
        """Test that format validation is case-insensitive"""
        # Should accept both cases
        assert validate_prompt_format("markdown") == True
        assert validate_prompt_format("Markdown") == True
        assert validate_prompt_format("MARKDOWN") == True
        assert validate_prompt_format("json") == True
        assert validate_prompt_format("JSON") == True

    def test_format_validation_in_contract(self):
        """Test that contract format field is validated case-insensitively"""
        contract = {"format": "Markdown"}  # Capital M
        # Should not fail validation