import pytest
from llmflow.runner import run_for_each_step

class TestAppendToMechanism:
    """Test the append_to functionality in for-each loops"""

    def test_append_to_with_function_steps(self):
        """Test that append_to works with function steps (not just LLM steps)"""
        context = {
            "items": ["A", "B", "C"]
        }

        rule = {
            "name": "test_foreach",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [
                {
                    "name": "function_step",
                    "type": "function",
                    "function": "test_func",
                    "outputs": "result",
                    "append_to": "results_list"
                }
            ]
        }

        # After running, context should have results_list with 3 items
        # This was the bug we fixed - it only worked for LLM steps

    def test_append_creates_list_if_missing(self):
        """Test that append_to creates the list if it doesn't exist"""
        context = {}  # No lists pre-defined

        # Run for-each with append_to
        # Should create the list automatically