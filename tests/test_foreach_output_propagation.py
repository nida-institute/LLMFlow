"""
Regression tests for for-each output propagation to parent context.

Regular `outputs` variables from inside a for-each loop should be visible in
the parent context after the loop completes (last-iteration wins), matching
Python's for-loop semantics. Only `append_to` targets were propagated before
this fix; regular outputs were silently discarded on normal completion.
"""
from llmflow.runner import run_for_each_step


def test_regular_output_visible_after_loop():
    """A step output from inside for-each should be readable after the loop."""
    context = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}

    step = {
        "name": "loop",
        "type": "for-each",
        "in": "${items}",
        "for": "item",
        "steps": [
            {
                "name": "make_dict",
                "type": "function",
                "function": "llmflow.utils.data.create_json_dictionary",
                "inputs": {"id": "${item.id}"},
                "outputs": "last_item",
            }
        ],
    }

    run_for_each_step(step, context, {})

    assert "last_item" in context, "last_item should be in parent context after loop"
    assert context["last_item"] == {"id": 3}, (
        f"last_item should be last iteration's value (id=3), got {context['last_item']!r}"
    )


def test_last_iteration_wins():
    """When multiple iterations produce the same output var, the last one wins."""
    context = {"items": ["a", "b", "c"]}

    step = {
        "name": "loop",
        "type": "for-each",
        "in": "${items}",
        "for": "item",
        "steps": [
            {
                "name": "make_dict",
                "type": "function",
                "function": "llmflow.utils.data.create_json_dictionary",
                "inputs": {"value": "${item}"},
                "outputs": "current",
            }
        ],
    }

    run_for_each_step(step, context, {})

    assert context["current"] == {"value": "c"}, (
        f"current should be last iteration's value 'c', got {context['current']!r}"
    )


def test_append_to_and_regular_output_both_propagate():
    """append_to accumulates all iterations; regular output holds only the last."""
    context = {"items": [1, 2, 3]}

    step = {
        "name": "loop",
        "type": "for-each",
        "in": "${items}",
        "for": "item",
        "steps": [
            {
                "name": "make_dict",
                "type": "function",
                "function": "llmflow.utils.data.create_json_dictionary",
                "inputs": {"n": "${item}"},
                "outputs": "current_item",
                "append_to": "all_items",
            }
        ],
    }

    run_for_each_step(step, context, {})

    assert context["all_items"] == [{"n": 1}, {"n": 2}, {"n": 3}], (
        "all_items should accumulate all iterations"
    )
    assert context["current_item"] == {"n": 3}, (
        "current_item should be the last iteration's value"
    )


def test_output_after_loop_usable_in_next_step():
    """A step that follows the for-each can reference the loop's last output."""
    from llmflow.runner import run_step

    context = {"items": [{"x": 10}, {"x": 20}, {"x": 30}]}

    foreach_step = {
        "name": "loop",
        "type": "for-each",
        "in": "${items}",
        "for": "item",
        "steps": [
            {
                "name": "capture",
                "type": "function",
                "function": "llmflow.utils.data.create_json_dictionary",
                "inputs": {"x": "${item.x}"},
                "outputs": "last_captured",
            }
        ],
    }

    followup_step = {
        "name": "use_output",
        "type": "function",
        "function": "llmflow.utils.data.create_json_dictionary",
        "inputs": {"final_x": "${last_captured.x}"},
        "outputs": "result",
    }

    run_step(foreach_step, context, {})
    run_step(followup_step, context, {})

    assert context["result"] == {"final_x": 30}, (
        f"Step after for-each should see last iteration's output, got {context['result']!r}"
    )
