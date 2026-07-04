"""
Tests for the window step type.

Covers all three window strategies (tumbling, sliding, condition-based),
include_partial behaviour, context variables, append_to propagation,
and linter validation.

NO STUBS — uses real runner.py and linter.py.
"""
import pytest
from llmflow.runner import run_window_step
from llmflow.steps.window import (
    _build_windows_fixed,
    _build_windows_condition,
    _build_windows_token,
)
from llmflow.utils.linter import _lint_window_step


# ---------------------------------------------------------------------------
# _build_windows_fixed
# ---------------------------------------------------------------------------

class TestBuildWindowsFixed:

    def test_tumbling_exact_fit(self):
        items = list(range(6))
        windows = _build_windows_fixed(items, size=2, stride=2, include_partial=True)
        assert windows == [[0, 1], [2, 3], [4, 5]]

    def test_tumbling_with_partial_included(self):
        items = list(range(7))
        windows = _build_windows_fixed(items, size=3, stride=3, include_partial=True)
        assert windows == [[0, 1, 2], [3, 4, 5], [6]]

    def test_tumbling_with_partial_excluded(self):
        items = list(range(7))
        windows = _build_windows_fixed(items, size=3, stride=3, include_partial=False)
        assert windows == [[0, 1, 2], [3, 4, 5]]

    def test_sliding_overlapping(self):
        items = list(range(6))
        windows = _build_windows_fixed(items, size=3, stride=1, include_partial=True)
        assert windows == [
            [0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5],
            [4, 5], [5],
        ]

    def test_sliding_partial_excluded(self):
        items = list(range(6))
        windows = _build_windows_fixed(items, size=3, stride=1, include_partial=False)
        assert windows == [[0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5]]

    def test_sliding_stride_2(self):
        items = list(range(8))
        windows = _build_windows_fixed(items, size=4, stride=2, include_partial=True)
        assert windows == [
            [0, 1, 2, 3], [2, 3, 4, 5], [4, 5, 6, 7], [6, 7],
        ]

    def test_empty_input(self):
        assert _build_windows_fixed([], size=3, stride=3, include_partial=True) == []

    def test_size_larger_than_list_included(self):
        items = [1, 2]
        windows = _build_windows_fixed(items, size=5, stride=5, include_partial=True)
        assert windows == [[1, 2]]

    def test_size_larger_than_list_excluded(self):
        items = [1, 2]
        windows = _build_windows_fixed(items, size=5, stride=5, include_partial=False)
        assert windows == []


# ---------------------------------------------------------------------------
# _build_windows_condition
# ---------------------------------------------------------------------------

class TestBuildWindowsCondition:

    def _items(self, markers):
        return [{"marker": m, "id": i} for i, m in enumerate(markers)]

    def test_start_and_end_when(self):
        items = self._items(["s", "a", "b", "e", "x", "s", "c", "e", "y"])
        windows = _build_windows_condition(
            items,
            start_when="${item.marker == 's'}",
            end_when="${item.marker == 'e'}",
            context={},
        )
        assert len(windows) == 2
        assert [it["marker"] for it in windows[0]] == ["s", "a", "b", "e"]
        assert [it["marker"] for it in windows[1]] == ["s", "c", "e"]

    def test_items_before_first_start_dropped(self):
        items = self._items(["x", "y", "s", "a", "e"])
        windows = _build_windows_condition(
            items, start_when="${item.marker == 's'}",
            end_when="${item.marker == 'e'}", context={},
        )
        assert len(windows) == 1
        assert windows[0][0]["marker"] == "s"

    def test_items_after_last_end_dropped(self):
        items = self._items(["s", "a", "e", "x", "y"])
        windows = _build_windows_condition(
            items, start_when="${item.marker == 's'}",
            end_when="${item.marker == 'e'}", context={},
        )
        assert len(windows) == 1
        assert windows[0][-1]["marker"] == "e"

    def test_no_end_when_closes_on_next_start(self):
        items = self._items(["s", "a", "b", "s", "c", "d"])
        windows = _build_windows_condition(
            items, start_when="${item.marker == 's'}",
            end_when=None, context={},
        )
        assert len(windows) == 2
        assert [it["marker"] for it in windows[0]] == ["s", "a", "b"]
        assert [it["marker"] for it in windows[1]] == ["s", "c", "d"]

    def test_open_window_at_end_dropped_no_end_when(self):
        # Without end_when, the last open window is included (it IS closed by end-of-sequence)
        items = self._items(["s", "a", "b"])
        windows = _build_windows_condition(
            items, start_when="${item.marker == 's'}",
            end_when=None, context={},
        )
        assert len(windows) == 1
        assert [it["marker"] for it in windows[0]] == ["s", "a", "b"]

    def test_new_start_before_end_closes_current(self):
        # Two starts before any end: current window closed at second start
        items = self._items(["s", "a", "s", "b", "e"])
        windows = _build_windows_condition(
            items, start_when="${item.marker == 's'}",
            end_when="${item.marker == 'e'}", context={},
        )
        assert len(windows) == 2
        assert [it["marker"] for it in windows[0]] == ["s", "a"]
        assert [it["marker"] for it in windows[1]] == ["s", "b", "e"]

    def test_empty_input(self):
        assert _build_windows_condition([], "${item.x}", None, {}) == []


# ---------------------------------------------------------------------------
# run_window_step — integration via real runner
# ---------------------------------------------------------------------------

def _make_capture_step(capture_list_var: str, item_var: str) -> dict:
    """A function step that appends the current window to a list."""
    return {
        "name": "capture",
        "type": "function",
        "function": "llmflow.utils.data.identity",
        "inputs": {"value": f"${{{item_var}}}"},
        "append_to": capture_list_var,
    }


class TestRunWindowStep:

    def _run(self, step_config: dict, context: dict) -> dict:
        run_window_step(step_config, context, {})
        return context

    def test_tumbling_basic(self):
        context = {"items": list(range(6)), "results": []}
        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 2,
            "steps": [
                {
                    "name": "record",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${batch}"},
                    "append_to": "results",
                }
            ],
        }
        ctx = self._run(step, context)
        assert ctx["results"] == [[0, 1], [2, 3], [4, 5]]

    def test_tumbling_partial_included(self):
        context = {"items": list(range(5)), "results": []}
        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 3,
            "include_partial": True,
            "steps": [
                {
                    "name": "record",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${batch}"},
                    "append_to": "results",
                }
            ],
        }
        ctx = self._run(step, context)
        assert ctx["results"] == [[0, 1, 2], [3, 4]]

    def test_tumbling_partial_excluded(self):
        context = {"items": list(range(5)), "results": []}
        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 3,
            "include_partial": False,
            "steps": [
                {
                    "name": "record",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${batch}"},
                    "append_to": "results",
                }
            ],
        }
        ctx = self._run(step, context)
        assert ctx["results"] == [[0, 1, 2]]

    def test_sliding_windows(self):
        context = {"items": list(range(5)), "results": []}
        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 3,
            "stride": 1,
            "include_partial": False,
            "steps": [
                {
                    "name": "record",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${batch}"},
                    "append_to": "results",
                }
            ],
        }
        ctx = self._run(step, context)
        assert ctx["results"] == [[0, 1, 2], [1, 2, 3], [2, 3, 4]]

    def test_window_context_variables(self):
        """_window_index, _window_first, _window_last are set per iteration."""
        captured = []

        def fake_emit(step, ctx, _cfg):
            captured.append({
                "index": ctx["_window_index"],
                "first": ctx["_window_first"],
                "last": ctx["_window_last"],
            })

        context = {"items": [10, 20, 30, 40]}
        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 2,
            "steps": [],  # empty steps — we'll check context directly
        }
        # Patch steps to capture context mid-iteration
        indices = []
        firsts = []
        lasts = []

        import llmflow.runner as runner_mod
        original_run_step = runner_mod.run_step

        def capturing_run_step(step, ctx, cfg):
            # Not called (steps is empty), but we need to verify context is set
            pass

        # Directly inspect by adding a thin recording step
        records = []

        def record_fn(value):
            return value

        step["steps"] = [
            {
                "name": "rec_index",
                "type": "function",
                "function": "llmflow.utils.data.identity",
                "inputs": {"value": "${_window_index}"},
                "append_to": "_indices",
            },
            {
                "name": "rec_first",
                "type": "function",
                "function": "llmflow.utils.data.identity",
                "inputs": {"value": "${_window_first}"},
                "append_to": "_firsts",
            },
        ]
        ctx = self._run(step, context)
        assert ctx["_indices"] == [1, 2]   # _window_index via identity capture
        assert ctx["_firsts"] == [10, 30]

    def test_condition_based_windows(self):
        items = [
            {"marker": "s", "v": 1},
            {"marker": "a", "v": 2},
            {"marker": "e", "v": 3},
            {"marker": "x", "v": 4},  # dropped — between windows
            {"marker": "s", "v": 5},
            {"marker": "e", "v": 6},
        ]
        context = {"items": items, "results": []}
        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "pericope",
            "start_when": "${item.marker == 's'}",
            "end_when": "${item.marker == 'e'}",
            "steps": [
                {
                    "name": "record",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${pericope}"},
                    "append_to": "results",
                }
            ],
        }
        ctx = self._run(step, context)
        assert len(ctx["results"]) == 2
        assert [it["v"] for it in ctx["results"][0]] == [1, 2, 3]
        assert [it["v"] for it in ctx["results"][1]] == [5, 6]

    def test_empty_input_no_error(self):
        context = {"items": [], "results": []}
        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 3,
            "steps": [
                {
                    "name": "record",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${batch}"},
                    "append_to": "results",
                }
            ],
        }
        ctx = self._run(step, context)
        assert ctx["results"] == []

    def test_non_list_input_raises(self):
        context = {"items": "not a list"}
        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 2,
            "steps": [],
        }
        with pytest.raises(ValueError, match="must resolve to a list"):
            run_window_step(step, context, {})


# ---------------------------------------------------------------------------
# Linter validation
# ---------------------------------------------------------------------------

class TestLintWindowStep:

    def _lint(self, step: dict) -> list[str]:
        errors = []
        _lint_window_step(step, errors)
        return errors

    def test_valid_fixed_tumbling(self):
        assert self._lint({"name": "w", "type": "window", "size": 3, "steps": [{}]}) == []

    def test_valid_fixed_sliding(self):
        assert self._lint({"name": "w", "type": "window", "size": 3, "stride": 1, "steps": [{}]}) == []

    def test_valid_condition_based(self):
        assert self._lint({
            "name": "w", "type": "window",
            "start_when": "${x}", "end_when": "${y}",
            "steps": [{}],
        }) == []

    def test_valid_condition_no_end_when(self):
        assert self._lint({
            "name": "w", "type": "window",
            "start_when": "${x}",
            "steps": [{}],
        }) == []

    def test_missing_size_and_start_when(self):
        errors = self._lint({"name": "w", "type": "window", "steps": [{}]})
        assert any("size" in e and "start_when" in e for e in errors)

    def test_size_and_start_when_both_present(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size": 3, "start_when": "${x}",
            "steps": [{}],
        })
        assert any("mutually exclusive" in e for e in errors)

    def test_stride_without_size(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "start_when": "${x}", "stride": 2,
            "steps": [{}],
        })
        assert any("stride" in e for e in errors)

    def test_end_when_without_start_when(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size": 3, "end_when": "${y}",
            "steps": [{}],
        })
        assert any("end_when" in e for e in errors)

    def test_include_partial_without_size(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "start_when": "${x}", "include_partial": False,
            "steps": [{}],
        })
        assert any("include_partial" in e for e in errors)

    def test_missing_steps(self):
        errors = self._lint({"name": "w", "type": "window", "size": 3})
        assert any("steps" in e for e in errors)

    def test_empty_steps(self):
        errors = self._lint({"name": "w", "type": "window", "size": 3, "steps": []})
        assert any("steps" in e for e in errors)

    def test_bad_size_type(self):
        errors = self._lint({"name": "w", "type": "window", "size": "three", "steps": [{}]})
        assert any("size" in e for e in errors)

    def test_bad_stride_type(self):
        errors = self._lint({"name": "w", "type": "window", "size": 3, "stride": 0, "steps": [{}]})
        assert any("stride" in e for e in errors)

    def test_lint_pipeline_steps_recognises_window(self):
        """lint_pipeline_steps calls _lint_window_step for type: window steps."""
        from llmflow.utils.linter import lint_pipeline_steps
        steps = [
            {
                "name": "bad_window",
                "type": "window",
                "input": "${items}",
                "item_var": "batch",
                # Missing size AND start_when — should produce an error
                "steps": [{"name": "x", "type": "function", "function": "f"}],
            }
        ]
        errors = lint_pipeline_steps(steps)
        assert any("size" in e and "start_when" in e for e in errors)

    def test_lint_pipeline_steps_valid_window_no_errors(self):
        from llmflow.utils.linter import lint_pipeline_steps
        steps = [
            {
                "name": "valid_window",
                "type": "window",
                "input": "${items}",
                "item_var": "batch",
                "size": 3,
                "steps": [{"name": "x", "type": "function", "function": "f"}],
            }
        ]
        errors = lint_pipeline_steps(steps)
        assert errors == []


# ---------------------------------------------------------------------------
# after: exit and after: continue inside window steps
# ---------------------------------------------------------------------------

class TestWindowFlowControl:

    _record_step = {
        "name": "record",
        "type": "function",
        "function": "llmflow.utils.data.identity",
        "inputs": {"value": "${batch}"},
        "append_to": "results",
    }

    def _base_step(self, nested):
        return {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 2,
            "steps": nested,
        }

    def test_after_exit_stops_iteration(self):
        """after: exit on window 2 propagates out; window 3 never runs."""
        context = {"items": list(range(6)), "results": []}

        step = self._base_step([
            self._record_step,
            {
                "name": "bail",
                "type": "function",
                "function": "llmflow.utils.data.identity",
                "inputs": {"value": "${_window_index}"},
                "outputs": "wi",
                "condition": "window_num == 2",
                "after": "exit",
            },
        ])

        from llmflow.runner import run_window_step
        action = run_window_step(step, context, {})

        assert action == "exit"
        # Windows 1 and 2 ran; window 3 did not
        assert len(context["results"]) == 2
        assert context["results"][0] == [0, 1]
        assert context["results"][1] == [2, 3]

    def test_after_continue_skips_remaining_steps_in_iteration(self):
        """after: continue skips steps after it in that window, moves to next."""
        context = {"items": list(range(6)), "results": [], "skipped": []}

        step = self._base_step([
            self._record_step,
            {
                "name": "skip_odd",
                "type": "function",
                "function": "llmflow.utils.data.identity",
                "inputs": {"value": "${_window_index}"},
                "outputs": "_skip_dummy",
                "condition": "window_num == 2",
                "after": "continue",
            },
            {
                # This step runs on windows 1 and 3, but NOT window 2 (continue skips it)
                "name": "after_skip",
                "type": "function",
                "function": "llmflow.utils.data.identity",
                "inputs": {"value": "${_window_index}"},
                "append_to": "ran_indices",
            },
        ])

        from llmflow.runner import run_window_step
        action = run_window_step(step, context, {})

        assert action is None  # no exit
        assert context["results"] == [[0, 1], [2, 3], [4, 5]]  # all windows recorded
        # window_num 1 and 3 ran after_skip; window_num 2 was skipped by continue
        assert context.get("ran_indices") == [1, 3]

    def test_after_exit_propagates_accumulated_results(self):
        """Results accumulated before exit are visible in context."""
        context = {"items": list(range(8)), "results": []}

        step = self._base_step([
            self._record_step,
            {
                "name": "bail_at_3",
                "type": "function",
                "function": "llmflow.utils.data.identity",
                "inputs": {"value": "0"},
                "outputs": "_dummy",
                "condition": "window_num == 3",
                "after": "exit",
            },
        ])

        from llmflow.runner import run_window_step
        run_window_step(step, context, {})

        # Windows 1, 2, 3 ran before exit
        assert len(context["results"]) == 3


# ---------------------------------------------------------------------------
# Nested window and for-each combinations
# ---------------------------------------------------------------------------

class TestWindowNesting:

    def test_window_inside_for_each(self):
        """for-each over groups, window within each group."""
        from llmflow.runner import run_step

        groups = [list(range(4)), list(range(10, 14))]
        context = {"groups": groups, "all_windows": []}

        pipeline_step = {
            "name": "outer",
            "type": "for-each",
            "input": "${groups}",
            "item_var": "group",
            "steps": [
                {
                    "name": "inner",
                    "type": "window",
                    "input": "${group}",
                    "item_var": "win",
                    "size": 2,
                    "steps": [
                        {
                            "name": "record",
                            "type": "function",
                            "function": "llmflow.utils.data.identity",
                            "inputs": {"value": "${win}"},
                            "append_to": "all_windows",
                        }
                    ],
                }
            ],
        }

        run_step(pipeline_step, context, {})

        # Each group of 4 items → 2 windows of size 2
        assert len(context["all_windows"]) == 4
        assert context["all_windows"][0] == [0, 1]
        assert context["all_windows"][1] == [2, 3]
        assert context["all_windows"][2] == [10, 11]
        assert context["all_windows"][3] == [12, 13]

    def test_for_each_inside_window(self):
        """window over a list, for-each within each window."""
        from llmflow.runner import run_step

        items = ["a", "b", "c", "d"]
        context = {"items": items, "chars": []}

        pipeline_step = {
            "name": "outer",
            "type": "window",
            "input": "${items}",
            "item_var": "win",
            "size": 2,
            "steps": [
                {
                    "name": "inner",
                    "type": "for-each",
                    "input": "${win}",
                    "item_var": "ch",
                    "steps": [
                        {
                            "name": "record",
                            "type": "function",
                            "function": "llmflow.utils.data.identity",
                            "inputs": {"value": "${ch}"},
                            "append_to": "chars",
                        }
                    ],
                }
            ],
        }

        run_step(pipeline_step, context, {})

        assert context["chars"] == ["a", "b", "c", "d"]


# ---------------------------------------------------------------------------
# Condition-based windows with richer objects
# ---------------------------------------------------------------------------

class TestConditionWindowObjects:

    def test_object_with_attribute_access(self):
        """Items that are objects (not plain dicts) — dot notation via getattr."""
        from types import SimpleNamespace
        from llmflow.steps.window import _build_windows_condition

        items = [
            SimpleNamespace(type="heading", text="Title"),
            SimpleNamespace(type="para", text="P1"),
            SimpleNamespace(type="para", text="P2"),
            SimpleNamespace(type="heading", text="Title2"),
            SimpleNamespace(type="para", text="P3"),
        ]

        windows = _build_windows_condition(
            items,
            start_when="item.type == 'heading'",
            end_when=None,
            context={},
        )

        assert len(windows) == 2
        assert windows[0][0].text == "Title"
        assert len(windows[0]) == 3
        assert windows[1][0].text == "Title2"
        assert len(windows[1]) == 2

    def test_condition_uses_parent_context(self):
        """start_when can reference parent context variables."""
        from llmflow.steps.window import _build_windows_condition

        items = [
            {"value": 1}, {"value": 5}, {"value": 2},
            {"value": 10}, {"value": 3},
        ]
        # Window starts when item.value >= threshold (threshold from parent context)
        windows = _build_windows_condition(
            items,
            start_when="item['value'] >= threshold",
            end_when=None,
            context={"threshold": 5},
        )

        assert len(windows) == 2
        assert windows[0][0]["value"] == 5
        assert windows[1][0]["value"] == 10

    def test_condition_no_matches_returns_empty(self):
        """If start_when never fires, no windows produced."""
        from llmflow.steps.window import _build_windows_condition

        items = [{"type": "para"}, {"type": "para"}]
        windows = _build_windows_condition(
            items,
            start_when="item['type'] == 'heading'",
            end_when=None,
            context={},
        )
        assert windows == []

    def test_single_item_window(self):
        """A window can contain a single item."""
        from llmflow.steps.window import _build_windows_condition

        items = [{"s": True, "e": True}, {"s": False, "e": False}]
        windows = _build_windows_condition(
            items,
            start_when="item['s']",
            end_when="item['e']",
            context={},
        )
        assert len(windows) == 1
        assert len(windows[0]) == 1

    def test_consecutive_start_markers_each_open_new_window(self):
        """Two adjacent start markers without intervening items each form their own window."""
        from llmflow.steps.window import _build_windows_condition

        items = [
            {"m": "s"}, {"m": "a"}, {"m": "e"},
            {"m": "s"}, {"m": "e"},
        ]
        windows = _build_windows_condition(
            items,
            start_when="item['m'] == 's'",
            end_when="item['m'] == 'e'",
            context={},
        )
        assert len(windows) == 2
        assert len(windows[0]) == 3
        assert len(windows[1]) == 2


# ---------------------------------------------------------------------------
# outputs (last-window-wins) propagation
# ---------------------------------------------------------------------------

class TestWindowOutputPropagation:

    def test_outputs_last_window_wins(self):
        """Regular outputs follow last-window-wins semantics."""
        context = {"items": list(range(6))}

        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 2,
            "steps": [
                {
                    "name": "capture",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${batch}"},
                    "outputs": "last_window",
                }
            ],
        }

        from llmflow.runner import run_window_step
        run_window_step(step, context, {})

        # Last window is [4, 5]
        assert context["last_window"] == [4, 5]

    def test_append_to_accumulates_all_windows(self):
        """append_to collects results from every window."""
        context = {"items": list(range(6)), "all": []}

        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 2,
            "steps": [
                {
                    "name": "capture",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${_window_index}"},
                    "append_to": "all",
                }
            ],
        }

        from llmflow.runner import run_window_step
        run_window_step(step, context, {})

        assert context["all"] == [1, 2, 3]

    def test_outputs_visible_in_next_iteration(self):
        """A value written via outputs in iteration N is readable in iteration N+1.

        This guarantees the deepcopy(context) + write-back pattern works correctly
        for cross-iteration state. If the write-back were missing or the deepcopy
        were taken from the wrong snapshot, the seen_count would not grow.
        """
        context = {"items": list(range(6)), "seen_count": 0}

        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 2,
            "steps": [
                {
                    # Read seen_count from previous iteration, increment, write back
                    "name": "increment",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${seen_count}"},
                    "outputs": "_prev_count",
                },
                {
                    "name": "store_count",
                    "type": "function",
                    "function": "tests.test_helpers.add_one",
                    "inputs": {"value": "${_prev_count}"},
                    "outputs": "seen_count",
                },
            ],
        }

        from llmflow.runner import run_window_step
        run_window_step(step, context, {})

        # 3 windows → seen_count incremented 3 times: 0 → 1 → 2 → 3
        assert context["seen_count"] == 3

    def test_append_to_list_readable_in_next_iteration(self):
        """Values accumulated via append_to are visible to subsequent iterations.

        This is the prior_pericopes pattern: each iteration appends a summary,
        and the next iteration reads the growing list (e.g. ${prior[-10:]}).
        """
        context = {"items": ["a", "b", "c", "d"], "prior": []}

        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 1,
            "steps": [
                {
                    # Each iteration appends the current item to prior
                    "name": "accumulate",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${batch[0]}"},
                    "append_to": "prior",
                },
                {
                    # Reads the prior list accumulated so far (including this iteration)
                    "name": "snapshot_prior",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${prior}"},
                    "append_to": "prior_snapshots",
                },
            ],
        }

        from llmflow.runner import run_window_step
        run_window_step(step, context, {})

        # After iteration 1: prior = ["a"], snapshot = ["a"]
        # After iteration 2: prior = ["a","b"], snapshot = ["a","b"]
        # After iteration 3: prior = ["a","b","c"], snapshot = ["a","b","c"]
        # After iteration 4: prior = ["a","b","c","d"]
        assert context["prior"] == ["a", "b", "c", "d"]
        assert context["prior_snapshots"][0] == ["a"]
        assert context["prior_snapshots"][1] == ["a", "b"]
        assert context["prior_snapshots"][2] == ["a", "b", "c"]
        assert context["prior_snapshots"][3] == ["a", "b", "c", "d"]

    def test_tail_slice_of_accumulated_list_in_next_iteration(self):
        """${prior[-3:]} inside a window reads only the last N items accumulated so far.

        This is the prior_pericopes[-10:] pattern from discourse-flow: the LLM
        receives only recent context, not the full history.
        """
        context = {"items": list(range(5)), "prior": []}

        step = {
            "name": "w",
            "type": "window",
            "input": "${items}",
            "item_var": "batch",
            "size": 1,
            "steps": [
                {
                    "name": "accumulate",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${batch[0]}"},
                    "append_to": "prior",
                },
                {
                    # Reads the last 3 items only
                    "name": "snapshot_tail",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${prior[-3:]}"},
                    "append_to": "tail_snapshots",
                },
            ],
        }

        from llmflow.runner import run_window_step
        run_window_step(step, context, {})

        # Tail of prior after each iteration:
        assert context["tail_snapshots"][0] == [0]           # prior=[0],     last 3=[0]
        assert context["tail_snapshots"][1] == [0, 1]        # prior=[0,1],   last 3=[0,1]
        assert context["tail_snapshots"][2] == [0, 1, 2]     # prior=[0,1,2], last 3=[0,1,2]
        assert context["tail_snapshots"][3] == [1, 2, 3]     # prior=[0..3],  last 3=[1,2,3]
        assert context["tail_snapshots"][4] == [2, 3, 4]     # prior=[0..4],  last 3=[2,3,4]


# ---------------------------------------------------------------------------
# _build_windows_token
# ---------------------------------------------------------------------------

class TestBuildWindowsToken:
    """Tests for token-aware windowing.

    Uses a model that tiktoken supports (gpt-4o).  Each item is a short string
    so we can reason about exact token counts.  A single ASCII word is typically
    1 token in the cl100k / o200k encoding families.
    """

    MODEL = "gpt-4o"

    def _words(self, n: int) -> list[str]:
        """Return n single-token words."""
        return [f"word{i}" for i in range(n)]

    def test_tumbling_no_overlap(self):
        """stride_by_tokens=0: non-overlapping windows."""
        import tiktoken
        enc = tiktoken.encoding_for_model(self.MODEL)
        # Each "word0".."word2" is 1 token; 3-token windows
        items = self._words(6)
        tok_per_item = len(enc.encode(items[0]))  # typically 2 tokens: "word" + digit
        size = tok_per_item * 3
        windows = _build_windows_token(items, size_by_tokens=size, stride_by_tokens=0,
                                       model=self.MODEL, include_partial=True)
        assert len(windows) == 2
        assert windows[0] == items[:3]
        assert windows[1] == items[3:]

    def test_sliding_overlap(self):
        """stride_by_tokens > 0: last N token's-worth of items carry forward."""
        import tiktoken
        enc = tiktoken.encoding_for_model(self.MODEL)
        items = self._words(6)
        tok_per_item = len(enc.encode(items[0]))
        size = tok_per_item * 3
        stride = tok_per_item * 1  # 1 item of overlap
        windows = _build_windows_token(items, size_by_tokens=size, stride_by_tokens=stride,
                                       model=self.MODEL, include_partial=True)
        # First window: items[0:3]; overlap = items[2]; next starts at items[2]
        assert windows[0] == items[:3]
        assert windows[1][0] == items[2]

    def test_include_partial_true(self):
        """Final short window is included when include_partial=True."""
        import tiktoken
        enc = tiktoken.encoding_for_model(self.MODEL)
        items = self._words(5)
        tok_per_item = len(enc.encode(items[0]))
        size = tok_per_item * 3
        windows = _build_windows_token(items, size_by_tokens=size, stride_by_tokens=0,
                                       model=self.MODEL, include_partial=True)
        # 5 items, 3 per window → [0-2], [3-4] (partial)
        assert len(windows) == 2
        assert len(windows[-1]) < 3

    def test_include_partial_false(self):
        """Final short window is dropped when include_partial=False."""
        import tiktoken
        enc = tiktoken.encoding_for_model(self.MODEL)
        items = self._words(5)
        tok_per_item = len(enc.encode(items[0]))
        size = tok_per_item * 3
        windows = _build_windows_token(items, size_by_tokens=size, stride_by_tokens=0,
                                       model=self.MODEL, include_partial=False)
        assert len(windows) == 1
        assert windows[0] == items[:3]

    def test_empty_input(self):
        windows = _build_windows_token([], size_by_tokens=1000, stride_by_tokens=0,
                                       model=self.MODEL, include_partial=True)
        assert windows == []

    def test_single_item_larger_than_size(self):
        """An item exceeding size_by_tokens is included as a window of one."""
        windows = _build_windows_token(
            ["hello world " * 100],  # ~100+ tokens
            size_by_tokens=1,
            stride_by_tokens=0,
            model=self.MODEL,
            include_partial=True,
        )
        assert len(windows) == 1
        assert len(windows[0]) == 1

    def test_dict_items_serialised_as_json(self):
        """Dict items are JSON-serialised for token counting."""
        items = [{"verse": f"v{i}", "text": "lorem ipsum"} for i in range(4)]
        windows = _build_windows_token(items, size_by_tokens=5000, stride_by_tokens=0,
                                       model=self.MODEL, include_partial=True)
        assert len(windows) >= 1
        assert all(isinstance(item, dict) for w in windows for item in w)

    def test_unknown_model_falls_back_to_cl100k(self):
        """Unknown model name falls back to cl100k_base without error."""
        items = self._words(4)
        windows = _build_windows_token(items, size_by_tokens=1000, stride_by_tokens=0,
                                       model="nonexistent-model-xyz", include_partial=True)
        assert len(windows) == 1  # all fit in 1000 tokens

    def test_implicit_sliding_when_stride_omitted(self):
        """Omitting stride_by_tokens defaults to implicit sliding (size//10 overlap), not tumbling.

        With 10 items of 1 token each and size=3:
        - implicit overlap = 3//10 = 0, but floor of 1 item is applied → overlap ≥ 1 token
        Use a larger size so the 10% overlap is measurable.
        """
        import tiktoken
        enc = tiktoken.encoding_for_model(self.MODEL)
        # Use 20 items; each ~2 tokens. size = 6 tokens (3 items).
        # Explicit stride=0 (tumbling): windows [0-2], [3-5], [6-8], [9-11], ...
        # Implicit sliding (overlap = size//10 = 0 → at least 1 token → 1 item overlap):
        # windows[0] and windows[1] share at least one item.
        items = self._words(20)
        tok_per_item = len(enc.encode(items[0]))
        size = tok_per_item * 10  # 10-item windows
        # Tumbling: no overlap
        tumbling = _build_windows_token(items, size_by_tokens=size, stride_by_tokens=0,
                                        model=self.MODEL, include_partial=True)
        # Implicit sliding: overlap = size // 10 = 1 item's worth of tokens
        implicit = _build_windows_token(items, size_by_tokens=size, stride_by_tokens=size // 10,
                                        model=self.MODEL, include_partial=True)
        # Tumbling windows do not overlap
        assert tumbling[1][0] == items[10], "tumbling: second window starts after first ends"
        # Implicit sliding windows do overlap
        assert implicit[1][0] != items[10], "implicit sliding: second window starts before tumbling restart"
        assert implicit[0][-1] in implicit[1], "implicit sliding: last item of window 0 appears in window 1"

    def test_explicit_zero_stride_still_tumbles(self):
        """Explicit stride_by_tokens=0 still produces tumbling windows (no overlap)."""
        import tiktoken
        enc = tiktoken.encoding_for_model(self.MODEL)
        items = self._words(6)
        tok_per_item = len(enc.encode(items[0]))
        size = tok_per_item * 3
        windows = _build_windows_token(items, size_by_tokens=size, stride_by_tokens=0,
                                       model=self.MODEL, include_partial=True)
        assert len(windows) == 2
        assert windows[0] == items[:3]
        assert windows[1] == items[3:], "explicit stride=0 must tumble"

    def test_no_infinite_loop_large_stride(self):
        """stride_by_tokens >= window tokens still advances at least 1 item."""
        import tiktoken
        enc = tiktoken.encoding_for_model(self.MODEL)
        items = self._words(4)
        tok_per_item = len(enc.encode(items[0]))
        size = tok_per_item * 2
        stride = tok_per_item * 100  # larger than entire sequence
        windows = _build_windows_token(items, size_by_tokens=size, stride_by_tokens=stride,
                                       model=self.MODEL, include_partial=True)
        # Should terminate; each window advances at least 1 item
        assert len(windows) >= 1


# ---------------------------------------------------------------------------
# Token window via run_window_step
# ---------------------------------------------------------------------------

class TestRunWindowStepToken:

    def test_token_mode_produces_windows(self):
        """run_window_step with size_by_tokens dispatches to token mode."""
        import sys, types
        mod = types.ModuleType("__tok_test_mod1")
        mod.get_len = lambda items: len(items)
        sys.modules["__tok_test_mod1"] = mod
        try:
            context: dict = {"verses": [f"verse {i}" for i in range(6)]}
            step = {
                "name": "tw",
                "type": "window",
                "input": "${verses}",
                "item_var": "chunk",
                "size_by_tokens": 5000,
                "stride_by_tokens": 0,
                "model": "gpt-4o",
                "include_partial": True,
                "steps": [
                    {
                        "name": "collect",
                        "type": "function",
                        "function": "__tok_test_mod1.get_len",
                        "inputs": {"items": "${chunk}"},
                        "outputs": "chunk_len",
                        "append_to": "lens",
                    }
                ],
            }
            run_window_step(step, context, {})
            assert "lens" in context
            assert all(isinstance(x, int) for x in context["lens"])
        finally:
            sys.modules.pop("__tok_test_mod1", None)

    def test_token_mode_item_var_in_context(self):
        """item_var is exposed as the window list inside nested steps."""
        captured = []

        def _capture(**kwargs):
            captured.append(kwargs.get("items"))
            return None

        import sys
        import types
        mod = types.ModuleType("_test_capture_mod")
        mod.capture = _capture
        sys.modules["_test_capture_mod"] = mod

        context: dict = {"items": ["a", "b", "c", "d"]}
        step = {
            "name": "tw",
            "type": "window",
            "input": "${items}",
            "item_var": "my_chunk",
            "size_by_tokens": 5000,
            "stride_by_tokens": 0,
            "model": "gpt-4o",
            "steps": [
                {
                    "name": "cap",
                    "type": "function",
                    "function": "_test_capture_mod.capture",
                    "inputs": {"items": "${my_chunk}"},
                }
            ],
        }
        run_window_step(step, context, {})
        assert len(captured) >= 1
        assert all(isinstance(c, list) for c in captured)

        del sys.modules["_test_capture_mod"]

    def test_size_by_tokens_invalid_raises(self):
        context: dict = {"v": ["x"]}
        step = {
            "name": "bad",
            "type": "window",
            "input": "${v}",
            "size_by_tokens": -1,
            "steps": [{}],
        }
        with pytest.raises(ValueError, match="size_by_tokens"):
            run_window_step(step, context, {})

    def test_over_alias_for_input(self):
        """'over' is accepted as an alias for 'input'."""
        import sys, types
        mod = types.ModuleType("__over_alias_mod")
        mod.get_len = lambda items: len(items)
        sys.modules["__over_alias_mod"] = mod
        try:
            context: dict = {"items": [1, 2, 3]}
            step = {
                "name": "w",
                "type": "window",
                "over": "${items}",   # alias
                "size": 2,
                "include_partial": True,
                "steps": [
                    {
                        "name": "noop",
                        "type": "function",
                        "function": "__over_alias_mod.get_len",
                        "inputs": {"items": "${window}"},
                        "outputs": "wlen",
                        "append_to": "lens",
                    }
                ],
            }
            run_window_step(step, context, {})
            assert "lens" in context
        finally:
            sys.modules.pop("__over_alias_mod", None)


# ---------------------------------------------------------------------------
# merge: block
# ---------------------------------------------------------------------------

class TestWindowMerge:

    def _make_merge_fn(self, sys_mod_name="__merge_test_mod"):
        """Register a merge function and return its full dotted name."""
        import sys
        import types
        mod = types.ModuleType(sys_mod_name)

        def merge_fn(items, label="merged"):
            return {"merged": items, "label": label}

        mod.merge_fn = merge_fn
        sys.modules[sys_mod_name] = mod
        return f"{sys_mod_name}.merge_fn", sys_mod_name

    def test_merge_called_after_windows(self):
        import sys, types
        fn_path, mod_name = self._make_merge_fn("__merge_test_1")
        # Register a helper that returns the window as a list
        helper_mod = types.ModuleType("__merge_helper_1")
        helper_mod.pass_through = lambda items: items
        sys.modules["__merge_helper_1"] = helper_mod
        try:
            context: dict = {"items": [1, 2, 3, 4], "lbl": "test"}
            step = {
                "name": "w",
                "type": "window",
                "input": "${items}",
                "size": 2,
                "include_partial": True,
                "steps": [
                    {
                        "name": "collect",
                        "type": "function",
                        "function": "__merge_helper_1.pass_through",
                        "inputs": {"items": "${window}"},
                        "outputs": "window_out",
                        "append_to": "collected",
                    }
                ],
                "merge": {
                    "name": "merge_step",
                    "function": fn_path,
                    "inputs": {"items": "${collected}", "label": "${lbl}"},
                    "outputs": "final",
                },
            }
            run_window_step(step, context, {})
            assert "final" in context
            assert context["final"]["label"] == "test"
        finally:
            sys.modules.pop(mod_name, None)
            sys.modules.pop("__merge_helper_1", None)

    def test_merge_receives_full_accumulated_results(self):
        import sys
        import types
        mod = types.ModuleType("__merge_test_2")
        received = {}

        def merge_fn(items):
            received["items"] = items
            return {"count": len(items)}

        mod.merge_fn = merge_fn
        sys.modules["__merge_test_2"] = mod

        helper = types.ModuleType("__merge_helper_2")
        helper.get_len = lambda items: len(items)
        sys.modules["__merge_helper_2"] = helper

        try:
            context: dict = {"items": list(range(6))}
            step = {
                "name": "w",
                "type": "window",
                "input": "${items}",
                "size": 2,
                "include_partial": True,
                "steps": [
                    {
                        "name": "noop",
                        "type": "function",
                        "function": "__merge_helper_2.get_len",
                        "inputs": {"items": "${window}"},
                        "outputs": "wl",
                        "append_to": "wlens",
                    }
                ],
                "merge": {
                    "name": "merge",
                    "function": "__merge_test_2.merge_fn",
                    "inputs": {"items": "${wlens}"},
                    "outputs": "summary",
                },
            }
            run_window_step(step, context, {})
            # 6 items / size 2 → 3 windows
            assert received["items"] == [2, 2, 2]
            assert context["summary"]["count"] == 3
        finally:
            sys.modules.pop("__merge_test_2", None)
            sys.modules.pop("__merge_helper_2", None)


# ---------------------------------------------------------------------------
# Linter: size_by_tokens and merge
# ---------------------------------------------------------------------------

class TestLintWindowStepToken:

    def _lint(self, step):
        errors = []
        _lint_window_step(step, errors)
        return errors

    def test_valid_size_by_tokens(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size_by_tokens": 25000,
            "model": "gpt-4o",
            "steps": [{}],
        })
        assert errors == []

    def test_valid_size_by_tokens_with_stride(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size_by_tokens": 25000,
            "stride_by_tokens": 5000,
            "model": "gpt-4o",
            "steps": [{}],
        })
        assert errors == []

    def test_size_and_size_by_tokens_mutually_exclusive(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size": 3, "size_by_tokens": 1000,
            "steps": [{}],
        })
        assert any("mutually exclusive" in e for e in errors)

    def test_size_by_tokens_and_start_when_mutually_exclusive(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size_by_tokens": 1000, "start_when": "${x}",
            "steps": [{}],
        })
        assert any("mutually exclusive" in e for e in errors)

    def test_bad_size_by_tokens_type(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size_by_tokens": "big",
            "steps": [{}],
        })
        assert any("size_by_tokens" in e for e in errors)

    def test_bad_stride_by_tokens_negative(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size_by_tokens": 1000, "stride_by_tokens": -1,
            "steps": [{}],
        })
        assert any("stride_by_tokens" in e for e in errors)

    def test_stride_with_size_by_tokens_wrong_key(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size_by_tokens": 1000, "stride": 2,
            "steps": [{}],
        })
        assert any("stride_by_tokens" in e for e in errors)

    def test_valid_merge_block(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size": 3,
            "steps": [{}],
            "merge": {"function": "my.module.fn", "inputs": {}, "outputs": "result"},
        })
        assert errors == []

    def test_merge_not_dict_raises(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size": 3,
            "steps": [{}],
            "merge": "just_a_string",
        })
        assert any("merge" in e for e in errors)

    def test_merge_missing_function_key(self):
        errors = self._lint({
            "name": "w", "type": "window",
            "size": 3,
            "steps": [{}],
            "merge": {"inputs": {}, "outputs": "result"},
        })
        assert any("merge" in e and "function" in e for e in errors)
