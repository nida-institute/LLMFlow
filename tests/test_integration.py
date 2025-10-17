import pytest
from llmflow.utils.io import render_markdown_template
from llmflow.runner import run_pipeline

class TestPipelineIntegration:
    """Integration tests for the full pipeline"""

    def test_template_variables_in_pipeline(self):
        """Test that template variables are resolved correctly in a full pipeline"""
        # Create a minimal test pipeline that reproduces the issue
        test_pipeline = {
            "name": "test-pipeline",
            "variables": {},
            "steps": [
                # Step 1: Create some lists
                {
                    "name": "create_lists",
                    "type": "function",
                    "function": "create_test_lists",
                    "outputs": ["test_list1", "test_list2"]
                },
                # Step 2: Use the lists in a template
                {
                    "name": "render_template",
                    "type": "function",
                    "function": "llmflow.utils.io.render_markdown_template",
                    "inputs": {
                        "template_path": "test_template.md",
                        "variables": {
                            "item1": "${test_list1[-1]}",
                            "item2": "${test_list2[-1]}"
                        }
                    },
                    "outputs": "rendered_output"
                }
            ]
        }

        # This would test the actual resolution chain