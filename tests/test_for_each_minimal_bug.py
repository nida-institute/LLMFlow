def test_minimal_for_each_append_bug():
    """Minimal test case showing the for-each append duplication bug"""
    from llmflow.runner import run_for_each_step

    # Minimal context
    context = {"items": ["A", "B", "C"]}

    # Track what gets appended
    appended_items = []

    # Simple function that tracks its calls
    def track_and_return(object):
        result = str(object)
        appended_items.append(f"Processing {result}")
        return result

    # Register the function
    import sys

    sys.modules["test_minimal"] = sys.modules[__name__]

    try:
        # Minimal rule
        rule = {
            "name": "test",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [
                {
                    "name": "process",
                    "type": "function",
                    "function": "test_minimal.track_and_return",
                    "inputs": {"object": "${item}"},
                    "outputs": "result",
                    "append_to": "results",
                }
            ],
        }

        # Run the for-each
        run_for_each_step(rule, context, {"variables": {}})

        # Print what happened
        print(f"\nProcessed items: {appended_items}")
        print(f"Final results: {context['results']}")
        print("Expected: ['A', 'B', 'C']")
        print(f"Got {len(context['results'])} items instead of 3")

        # Show the duplication pattern
        from collections import Counter

        counts = Counter(context["results"])
        print(f"\nItem counts: {dict(counts)}")

        # Should have exactly 3 items
        assert (
            len(context["results"]) == 3
        ), f"Expected 3, got {len(context['results'])}: {context['results']}"

    finally:
        # Clean up
        if "test_minimal" in sys.modules:
            del sys.modules["test_minimal"]


# Also add this function to the module
def track_and_return(object):
    return str(object)
