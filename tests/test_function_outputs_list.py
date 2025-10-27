from llmflow.runner import run_function_step


class TestFunctionOutputsList:
    """Test function steps with outputs defined as a list"""

    def test_function_with_list_outputs(self):
        """Test that function steps handle outputs as a list correctly"""
        context = {}

        # Step with outputs as a list
        step = {
            "name": "multi_output_function",
            "type": "function",
            "function": "tests.test_function_outputs_list.return_multiple",
            "outputs": ["result1", "result2", "result3"],  # List of outputs
        }

        def return_multiple():
            return ("value1", "value2", "value3")

        import sys

        sys.modules[__name__].return_multiple = return_multiple

        # This should work without error
        run_function_step(step, context)

        # Check all outputs were stored
        assert "result1" in context
        assert "result2" in context
        assert "result3" in context
        assert context["result1"] == "value1"
        assert context["result2"] == "value2"
        assert context["result3"] == "value3"

    def test_function_with_single_item_list_outputs(self):
        """Test function with outputs as a single-item list"""
        context = {}

        step = {
            "name": "single_list_output",
            "type": "function",
            "function": "tests.test_function_outputs_list.return_single",
            "outputs": ["single_result"],  # Single item list
        }

        def return_single():
            return "single_value"

        import sys

        sys.modules[__name__].return_single = return_single

        # This should work without error
        run_function_step(step, context)

        assert "single_result" in context
        assert context["single_result"] == "single_value"
