from llmflow.runner import run_function_step


class TestAppendToFixed:
    """Test that append_to now works after the fix"""

    def test_function_step_with_append_to_works(self):
        """Test that function steps now support append_to"""
        context = {}

        step = {
            "name": "test",
            "type": "function",
            "function": "tests.test_append_to_fixed.return_value",
            "outputs": "result",
            "append_to": "results_list",
        }

        def return_value():
            return "test_value"

        import sys

        sys.modules[__name__].return_value = return_value

        # Run step
        run_function_step(step, context)

        # After the fix, both outputs and append_to should work
        assert "result" in context
        assert context["result"] == "test_value"

        assert "results_list" in context, "append_to should now work!"
        assert len(context["results_list"]) == 1
        assert context["results_list"][0] == "test_value"

    def test_multiple_appends(self):
        """Test multiple appends to the same list"""
        context = {}

        for i in range(3):
            step = {
                "name": f"step_{i}",
                "type": "function",
                "function": "tests.test_append_to_fixed.make_value",
                "inputs": {"value": f"item_{i}"},
                "outputs": f"result_{i}",
                "append_to": "collected_items",
            }

            def make_value(value):
                return value

            import sys

            sys.modules[__name__].make_value = make_value

            run_function_step(step, context)

        # Check final state
        assert "collected_items" in context
        assert len(context["collected_items"]) == 3
        assert context["collected_items"] == ["item_0", "item_1", "item_2"]
