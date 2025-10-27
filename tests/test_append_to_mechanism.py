class TestAppendToMechanism:
    """Test the append_to functionality in for-each loops"""

    def test_append_to_with_function_steps(self):
        """Test that append_to works with function steps (not just LLM steps)"""

        # After running, context should have results_list with 3 items
        # This was the bug we fixed - it only worked for LLM steps

    def test_append_creates_list_if_missing(self):
        """Test that append_to creates the list if it doesn't exist"""

        # Run for-each with append_to
        # Should create the list automatically
