"""
Tests for the window step type.

Covers all three window strategies (tumbling, sliding, condition-based),
include_partial behaviour, context variables, append_to propagation,
and linter validation.

NO STUBS — uses real runner.py and linter.py.
"""
import pytest
from llmflow.runner import (
    run_window_step,
    _build_windows_fixed,
    _build_windows_condition,
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
        from llmflow.runner import _build_windows_condition

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
        from llmflow.runner import _build_windows_condition

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
        from llmflow.runner import _build_windows_condition

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
        from llmflow.runner import _build_windows_condition

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
        from llmflow.runner import _build_windows_condition

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
