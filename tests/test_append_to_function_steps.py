import pytest
from llmflow.runner import run_function_step

class TestAppendToFunctionSteps:
    """Test that append_to works with function steps"""

    def test_append_to_not_implemented_for_function_steps(self):
        """Document that append_to doesn't work for function steps"""
        context = {}

        step = {
            "name": "test_step",
            "type": "function",
            "function": "tests.test_append_to_function_steps.return_value",
            "outputs": "result",
            "append_to": "results_list"
        }

        def return_value():
            return "test_value"

        import sys
        sys.modules[__name__].return_value = return_value

        # Run the step
        run_function_step(step, context)

        print(f"\nContext after function step with append_to: {context}")

        # This will fail - append_to doesn't work for function steps
        assert "results_list" not in context, "append_to is not implemented for function steps"

        # But the output is stored
        assert "result" in context
        assert context["result"] == "test_value"

    def test_workaround_for_function_append(self):
        """Test a workaround - manually append in a subsequent step"""
        context = {"items_list": []}

        # Step 1: Function generates content
        step1 = {
            "name": "generate",
            "type": "function",
            "function": "tests.test_append_to_function_steps.generate_content",
            "outputs": "new_item"
        }

        def generate_content():
            return "generated content"

        import sys
        sys.modules[__name__].generate_content = generate_content

        # Run step 1
        run_function_step(step1, context)

        # Manual append (what should happen automatically)
        if "new_item" in context:
            context["items_list"].append(context["new_item"])

        # Now the list has the item
        assert len(context["items_list"]) == 1
        assert context["items_list"][0] == "generated content"