import pytest
from llmflow.runner import run_for_each_step

class TestForEachAppend:
    """Test the for-each step with append_to functionality"""

    def test_append_to_lists(self):
        """Test that append_to correctly builds lists during for-each"""
        # Mock pipeline config
        pipeline_config = {
            "llm_config": {},
            "variables": {}
        }

        # Initial context
        context = {
            "scenes": [
                {"title": "Scene 1", "number": 1},
                {"title": "Scene 2", "number": 2},
                {"title": "Scene 3", "number": 3}
            ]
        }

        # For-each rule that appends to lists
        rule = {
            "name": "process_scenes",
            "type": "for-each",
            "input": "${scenes}",
            "item_var": "scene",
            "steps": [
                {
                    "name": "process_scene",
                    "type": "function",
                    "function": "test_function",
                    "outputs": "processed_scene",
                    "append_to": "processed_list"
                }
            ]
        }

        # Run the for-each (you'd need to mock the function execution)
        # This test structure shows what we're testing

        # After execution, context should contain:
        # - processed_list with 3 items
        # - Each item should be accessible via processed_list[0], processed_list[-1], etc.