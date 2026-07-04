"""
Tests for the `loop` context variable injected by for-each steps.

Covers:
- loop.index  (1-based position)
- loop.total  (length of the input list)
- loop.first  (true on first iteration only)
- loop.last   (true on last iteration only)
- Nested for-each: inner loop.* shadows outer, both are correct
- _setup_iteration_context injects the loop dict directly
- loop is not visible in the parent context after the loop completes

These tests are written TDD-style and will fail until the feature is
implemented in runner.py:_setup_iteration_context / run_for_each_step.
"""
import pytest
from llmflow.steps.for_each import run_for_each_step, _setup_iteration_context


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _capture_step(output_var, append_to=None):
    """Return a function step that captures loop.* fields into a dict."""
    step = {
        "name": f"capture_{output_var}",
        "type": "function",
        "function": "llmflow.utils.data.create_json_dictionary",
        "inputs": {
            "index": "${loop.index}",
            "total": "${loop.total}",
            "first": "${loop.first}",
            "last":  "${loop.last}",
        },
        "outputs": output_var,
    }
    if append_to:
        step["append_to"] = append_to
    return step


def _run(items, extra_steps=None, item_var="item"):
    """Run a for-each over items, capturing loop.* at every iteration."""
    context = {"items": items}
    steps = [_capture_step("snapshot", append_to="snapshots")]
    if extra_steps:
        steps.extend(extra_steps)
    step = {
        "name": "loop",
        "type": "for-each",
        "input": "${items}",
        "item_var": item_var,
        "steps": steps,
    }
    run_for_each_step(step, context, {})
    return context.get("snapshots", [])


# ---------------------------------------------------------------------------
# _setup_iteration_context — unit tests
# ---------------------------------------------------------------------------

class TestSetupIterationContextLoopDict:

    def test_loop_dict_present(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(1, "a", ctx, "item", "step", None, total=3)
        assert "loop" in iter_ctx

    def test_loop_index_1_based(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(2, "b", ctx, "item", "step", None, total=5)
        assert iter_ctx["loop"]["index"] == 2

    def test_loop_total(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(1, "a", ctx, "item", "step", None, total=7)
        assert iter_ctx["loop"]["total"] == 7

    def test_loop_first_true_on_first(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(1, "a", ctx, "item", "step", None, total=3)
        assert iter_ctx["loop"]["first"] is True

    def test_loop_first_false_on_second(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(2, "b", ctx, "item", "step", None, total=3)
        assert iter_ctx["loop"]["first"] is False

    def test_loop_last_true_on_last(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(3, "c", ctx, "item", "step", None, total=3)
        assert iter_ctx["loop"]["last"] is True

    def test_loop_last_false_on_middle(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(2, "b", ctx, "item", "step", None, total=3)
        assert iter_ctx["loop"]["last"] is False

    def test_loop_single_item_both_first_and_last(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(1, "x", ctx, "item", "step", None, total=1)
        assert iter_ctx["loop"]["first"] is True
        assert iter_ctx["loop"]["last"] is True


# ---------------------------------------------------------------------------
# Integration: loop.* accessible via ${loop.index} etc. inside substeps
# ---------------------------------------------------------------------------

class TestLoopIndexResolution:

    def test_index_sequence(self):
        snapshots = _run(["a", "b", "c"])
        assert [s["index"] for s in snapshots] == [1, 2, 3]

    def test_total_correct(self):
        snapshots = _run(["x", "y", "z", "w"])
        assert all(s["total"] == 4 for s in snapshots)

    def test_first_flag(self):
        snapshots = _run(["a", "b", "c"])
        assert snapshots[0]["first"] is True
        assert snapshots[1]["first"] is False
        assert snapshots[2]["first"] is False

    def test_last_flag(self):
        snapshots = _run(["a", "b", "c"])
        assert snapshots[0]["last"] is False
        assert snapshots[1]["last"] is False
        assert snapshots[2]["last"] is True

    def test_single_item_first_and_last(self):
        snapshots = _run(["only"])
        assert snapshots[0]["first"] is True
        assert snapshots[0]["last"] is True

    def test_two_items(self):
        snapshots = _run(["p", "q"])
        assert snapshots[0] == {"index": 1, "total": 2, "first": True,  "last": False}
        assert snapshots[1] == {"index": 2, "total": 2, "first": False, "last": True}

    def test_empty_list_no_snapshots(self):
        snapshots = _run([])
        assert snapshots == []


# ---------------------------------------------------------------------------
# Nested for-each: inner loop.* shadows outer correctly
# ---------------------------------------------------------------------------

class TestNestedLoopVariable:

    def _run_nested(self, outer_items, inner_items):
        """Capture inner loop.* at every inner iteration."""
        context = {
            "outer": outer_items,
            "inner": inner_items,
        }
        step = {
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
                            "name": "capture",
                            "type": "function",
                            "function": "llmflow.utils.data.create_json_dictionary",
                            "inputs": {
                                "inner_index": "${loop.index}",
                                "inner_total": "${loop.total}",
                            },
                            "outputs": "snap",
                            "append_to": "snaps",
                        }
                    ],
                }
            ],
        }
        run_for_each_step(step, context, {})
        return context.get("snaps", [])

    def test_inner_index_resets_each_outer_iteration(self):
        snaps = self._run_nested(["A", "B"], ["x", "y", "z"])
        # 2 outer × 3 inner = 6 snapshots
        assert len(snaps) == 6
        # Indices should be 1,2,3 repeated twice (inner loop resets)
        inner_indices = [s["inner_index"] for s in snaps]
        assert inner_indices == [1, 2, 3, 1, 2, 3]

    def test_inner_total_is_inner_list_length(self):
        snaps = self._run_nested(["A", "B"], ["x", "y", "z"])
        assert all(s["inner_total"] == 3 for s in snaps)


# ---------------------------------------------------------------------------
# loop is not leaked into the parent context after the loop completes
# ---------------------------------------------------------------------------

class TestLoopNotLeakedToParent:

    def test_loop_not_in_parent_context_after_loop(self):
        context = {"items": [1, 2, 3]}
        step = {
            "name": "loop",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [
                _capture_step("snap", append_to="snaps"),
            ],
        }
        run_for_each_step(step, context, {})
        assert "loop" not in context, (
            "loop dict should not leak into the parent context after for-each completes"
        )
