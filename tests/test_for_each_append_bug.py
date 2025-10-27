import pytest

from llmflow.runner import run_for_each_step


class TestForEachAppendBug:
    """Specific tests to diagnose the for-each append duplication bug"""

    def test_for_each_iteration_count(self):
        """Test that for-each runs exactly once per item"""
        context = {"items": ["A", "B", "C"]}
        call_count = {"A": 0, "B": 0, "C": 0}

        def count_calls(item):
            call_count[item] += 1
            return f"Processed {item}"

        import sys

        sys.modules[__name__].count_calls = count_calls

        rule = {
            "name": "test",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [
                {
                    "name": "process",
                    "type": "function",
                    "function": "tests.test_for_each_append_bug.count_calls",
                    "inputs": {"item": "${item}"},
                    "outputs": "result",
                }
            ],
        }

        run_for_each_step(rule, context, {"variables": {}})

        # Each item should be processed exactly once
        assert call_count["A"] == 1, f"A was called {call_count['A']} times"
        assert call_count["B"] == 1, f"B was called {call_count['B']} times"
        assert call_count["C"] == 1, f"C was called {call_count['C']} times"

    def test_for_each_append_isolation(self):
        """Test that append_to in different iterations don't interfere"""
        context = {"items": ["A", "B", "C"]}

        # Track what gets appended when
        append_log = []

        def process_and_log(item):
            result = f"Result-{item}"
            append_log.append((item, result))
            return result

        import sys

        sys.modules[__name__].process_and_log = process_and_log

        rule = {
            "name": "test",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [
                {
                    "name": "process",
                    "type": "function",
                    "function": "tests.test_for_each_append_bug.process_and_log",
                    "inputs": {"item": "${item}"},
                    "outputs": "result",
                    "append_to": "results",
                }
            ],
        }

        run_for_each_step(rule, context, {"variables": {}})

        # Check the append log
        print(f"Append log: {append_log}")
        print(f"Results list: {context.get('results', [])}")

        # Should have exactly 3 appends
        assert len(append_log) == 3
        assert len(context["results"]) == 3

        # Each result should appear exactly once
        assert context["results"].count("Result-A") == 1
        assert context["results"].count("Result-B") == 1
        assert context["results"].count("Result-C") == 1

    def test_context_isolation_between_iterations(self):
        """Test that context changes in one iteration don't affect others"""
        context = {"items": [1, 2, 3]}

        def modify_context(item, context):
            # This function receives context and modifies it
            context[f"temp_{item}"] = f"value_{item}"
            return f"Result {item}"

        import sys

        sys.modules[__name__].modify_context = modify_context

        rule = {
            "name": "test",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [
                {
                    "name": "process",
                    "type": "function",
                    "function": "tests.test_for_each_append_bug.modify_context",
                    "inputs": {"item": "${item}"},
                    "outputs": "result",
                    "append_to": "results",
                }
            ],
        }

        run_for_each_step(rule, context, {"variables": {}})

        # Print what's in context after for-each
        print(f"Context after for-each: {list(context.keys())}")
        print(f"Results: {context.get('results', [])}")

        # Check if temporary context items leaked between iterations
        # This might reveal if context is being shared improperly

    @pytest.mark.xfail(reason="Nested for-each with append_to not yet implemented")
    def test_nested_for_each_append(self):
        """Test append_to in nested for-each loops"""
        context = {"outer": ["X", "Y"], "inner": ["1", "2"]}

        rule = {
            "name": "outer_loop",
            "type": "for-each",
            "input": "${outer}",
            "item_var": "outer_item",
            "steps": [
                {
                    "name": "inner_loop",
                    "type": "for-each",
                    "input": "${inner}",
                    "item_var": "inner_item",
                    "steps": [
                        {
                            "name": "combine",
                            "type": "function",
                            "function": "tests.test_for_each_append_bug.combine_items",
                            "inputs": {
                                "outer": "${outer_item}",
                                "inner": "${inner_item}",
                            },
                            "outputs": "combined",
                            "append_to": "combined_results",
                        }
                    ],
                }
            ],
        }

        def combine_items(outer, inner):
            return f"{outer}-{inner}"

        import sys

        sys.modules[__name__].combine_items = combine_items

        run_for_each_step(rule, context, {"variables": {}})

        # Should have exactly 4 results (2 outer × 2 inner)
        print(f"Combined results: {context.get('combined_results', [])}")
        assert len(context.get("combined_results", [])) == 4
