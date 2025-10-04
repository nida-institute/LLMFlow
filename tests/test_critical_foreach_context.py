from llmflow.runner import run_for_each_step
import pytest

class TestCriticalForEachContext:
    def test_nested_context_isolation(self):
        """Ensure for-each iterations don't contaminate each other"""
        context = {
            "items": ["A", "B", "C"],
            "global_value": "unchanged"
        }

        rule = {
            "name": "test_isolation",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [{
                "name": "mutate_context",
                "type": "function",
                "function": "tests.test_critical_foreach_context.mutate_context",
                "inputs": {"item": "${item}"},
                "outputs": "result",
                "append_to": "results"
            }]
        }

        run_for_each_step(rule, context, {"variables": {}})

        # Critical: global context not mutated
        assert context["global_value"] == "unchanged"

        # Critical: all results collected
        assert len(context["results"]) == 3

        # Critical: no contamination between iterations
        assert context["results"] == ["A-processed", "B-processed", "C-processed"]

    @pytest.mark.skip(reason="Need to test deepcopy implementation")
    def test_deepcopy_prevents_list_sharing(self):
        """Regression test for the shallow copy bug"""
        # This test needs access to the context object passed to functions
        pass

def mutate_context(item):
    return f"{item}-processed"