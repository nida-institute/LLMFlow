import pytest

from llmflow.runner import run_for_each_step


class TestCriticalForEachContext:
    def test_nested_context_isolation(self):
        """Ensure for-each iterations don't contaminate each other"""
        context = {"items": ["A", "B", "C"], "global_value": "unchanged"}

        rule = {
            "name": "test_isolation",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [
                {
                    "name": "mutate_context",
                    "type": "function",
                    "function": "tests.test_critical_foreach_context.mutate_context",
                    "inputs": {"item": "${item}"},
                    "outputs": "result",
                    "append_to": "results",
                }
            ],
        }

        run_for_each_step(rule, context, {"variables": {}})

        # Critical: global context not mutated
        assert context["global_value"] == "unchanged"

        # Critical: all results collected
        assert len(context["results"]) == 3

        # Critical: no contamination between iterations
        assert context["results"] == ["A-processed", "B-processed", "C-processed"]

    def test_deepcopy_prevents_list_sharing(self):
        """Regression test: deepcopy prevents the shallow copy bug where lists were shared"""
        context = {"shared_list": ["initial"]}

        rule = {
            "name": "test_deepcopy",
            "type": "for-each",
            "input": ["item1", "item2", "item3"],
            "item_var": "item",
            "steps": [
                {
                    "name": "append_to_list",
                    "type": "function",
                    "function": "tests.test_critical_foreach_context.append_to_shared_list",
                    "inputs": {"item": "${item}", "shared_list": "${shared_list}"},
                    "outputs": "result",
                }
            ],
        }

        run_for_each_step(rule, context, {})

        # Critical: The shared_list in parent context should NOT be modified by iterations
        # Each iteration gets a deepcopy, so modifications stay isolated
        assert context["shared_list"] == ["initial"], "Parent context list should not be mutated"


def mutate_context(item):
    return f"{item}-processed"


def append_to_shared_list(item, shared_list):
    """This function modifies the list - testing if deepcopy isolates it"""
    shared_list.append(item)
    return f"appended {item}"
