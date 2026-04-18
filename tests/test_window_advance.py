"""
Tests for !window_advance step type inside window steps.

The !window_advance step is a YAML-tagged step (type: window_advance) that:
- Appears in the steps list of a window step
- Wraps an inner step (llm or function)
- Runs the inner step normally (outputs flow into pipeline scope)
- Reads a named cursor variable from the inner step's output
- Sets _window_cursor in context for the window runner to use
- When _window_cursor is None, the window loop stops

NO STUBS — uses real runner.py.
"""
import pytest
import yaml

from llmflow.runner import run_window_step, _LLMFlowLoader
from tests.test_helpers import set_cursor_seq


# ---------------------------------------------------------------------------
# YAML tag parsing
# ---------------------------------------------------------------------------

class TestYamlTagParsing:

    def test_window_advance_tag_sets_tag_field(self):
        """!window_advance tag on a mapping adds _tag: 'window_advance'."""
        src = """\
steps:
  - !window_advance
    name: advance
    cursor: next_pos
    step:
      type: function
      function: tests.test_helpers.cursor_pop
      outputs: next_pos
"""
        parsed = yaml.load(src, Loader=_LLMFlowLoader)
        step = parsed["steps"][0]
        assert step["_tag"] == "window_advance"
        assert step["name"] == "advance"
        assert step["cursor"] == "next_pos"

    def test_plain_steps_unaffected(self):
        """Steps without tags parse as normal dicts (no _tag key)."""
        src = """\
steps:
  - name: segment
    type: llm
    outputs: result
"""
        parsed = yaml.load(src, Loader=_LLMFlowLoader)
        step = parsed["steps"][0]
        assert "_tag" not in step
        assert step["type"] == "llm"

    def test_inner_step_preserved(self):
        """The 'step' sub-key of !window_advance is parsed as a plain dict."""
        src = """\
steps:
  - !window_advance
    name: advance
    cursor: next_pos
    step:
      type: function
      function: tests.test_helpers.cursor_pop
      outputs: next_pos
"""
        parsed = yaml.load(src, Loader=_LLMFlowLoader)
        inner = parsed["steps"][0]["step"]
        assert inner["type"] == "function"
        assert "_tag" not in inner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_content(n):
    """Return a list of n simple string items (low token count per item)."""
    return [f"item{i}" for i in range(n)]


def _window_advance_step(cursor_var="next_pos"):
    """Return a !window_advance step dict using cursor_pop as the inner function."""
    return {
        "_tag": "window_advance",
        "name": "advance",
        "cursor": cursor_var,
        "step": {
            "name": "pop_cursor",
            "type": "function",
            "function": "tests.test_helpers.cursor_pop",
            "inputs": {},
            "outputs": cursor_var,
        },
    }


# ---------------------------------------------------------------------------
# Dynamic windowing — single and multi-iteration
# ---------------------------------------------------------------------------

class TestWindowAdvanceDynamic:

    def _run(self, step, context):
        run_window_step(step, context, {})
        return context

    def test_stops_immediately_on_null_cursor(self):
        """When advance returns None on the first iteration, only one window runs."""
        set_cursor_seq([None])
        windows_seen = []

        content = _make_content(20)
        step = {
            "name": "seg",
            "type": "window",
            "input": "${content}",
            "item_var": "wc",
            "size": 10,
            "steps": [
                {
                    "name": "record",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${wc}"},
                    "outputs": "last_window",
                },
                _window_advance_step(),
            ],
        }
        ctx = self._run(step, {"content": content, "next_pos": None})
        # Should have processed exactly one window (items 0-9)
        assert ctx["last_window"] == content[:10]

    def test_two_iterations_with_cursor_then_null(self):
        """Two windows when advance returns an index then None."""
        set_cursor_seq([5, None])
        step = {
            "name": "seg",
            "type": "window",
            "input": "${content}",
            "item_var": "wc",
            "size": 10,
            "steps": [
                {
                    "name": "collect",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${wc}"},
                    "outputs": "last_window",
                    "append_to": "all_windows",
                },
                _window_advance_step(),
            ],
        }
        content = _make_content(20)
        ctx = self._run(step, {"content": content, "all_windows": [], "next_pos": None})
        assert len(ctx["all_windows"]) == 2
        # First window: items 0-9
        assert ctx["all_windows"][0] == content[:10]
        # Second window starts at index 5: items 5-14
        assert ctx["all_windows"][1] == content[5:15]

    def test_cursor_advances_within_content(self):
        """Second window starts exactly at the cursor index."""
        set_cursor_seq([3, None])
        seen_starts = []

        step = {
            "name": "seg",
            "type": "window",
            "input": "${content}",
            "item_var": "wc",
            "size": 5,
            "steps": [
                {
                    "name": "record_start",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${wc}"},
                    "outputs": "last_window",
                    "append_to": "all_windows",
                },
                _window_advance_step(),
            ],
        }
        content = _make_content(10)
        ctx = self._run(step, {"content": content, "all_windows": [], "next_pos": None})
        # Window 1: content[0:5], Window 2: content[3:8]
        assert ctx["all_windows"][0] == content[0:5]
        assert ctx["all_windows"][1] == content[3:8]

    def test_inner_step_outputs_available_to_subsequent_steps(self):
        """Outputs of the inner step inside window_advance are in scope for later steps."""
        set_cursor_seq([None])
        step = {
            "name": "seg",
            "type": "window",
            "input": "${content}",
            "item_var": "wc",
            "size": 5,
            "steps": [
                _window_advance_step("next_pos"),
                # A step after window_advance that reads next_pos
                {
                    "name": "copy",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${next_pos}"},
                    "outputs": "cursor_copy",
                },
            ],
        }
        content = _make_content(5)
        ctx = self._run(step, {"content": content, "next_pos": None})
        # cursor_copy should equal what cursor_pop returned (None)
        assert ctx["cursor_copy"] is None

    def test_append_to_accumulates_across_dynamic_iterations(self):
        """append_to collects results from all dynamic window iterations."""
        set_cursor_seq([2, 4, None])
        step = {
            "name": "seg",
            "type": "window",
            "input": "${content}",
            "item_var": "wc",
            "size": 3,
            "steps": [
                {
                    "name": "collect",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${wc}"},
                    "outputs": "last_window",
                    "append_to": "all_windows",
                },
                _window_advance_step(),
            ],
        }
        content = _make_content(8)
        ctx = self._run(step, {"content": content, "all_windows": [], "next_pos": None})
        assert len(ctx["all_windows"]) == 3

    def test_single_item_content_stops_after_one_window(self):
        """Content smaller than window size: one iteration, null cursor stops it."""
        set_cursor_seq([None])
        step = {
            "name": "seg",
            "type": "window",
            "input": "${content}",
            "item_var": "wc",
            "size": 10,
            "steps": [
                {
                    "name": "collect",
                    "type": "function",
                    "function": "llmflow.utils.data.identity",
                    "inputs": {"value": "${wc}"},
                    "outputs": "result",
                    "append_to": "results",
                },
                _window_advance_step(),
            ],
        }
        content = _make_content(3)
        ctx = self._run(step, {"content": content, "results": [], "next_pos": None})
        assert len(ctx["results"]) == 1
        assert ctx["results"][0] == content


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestWindowAdvanceErrors:

    def _run(self, step, context):
        run_window_step(step, context, {})
        return context

    def test_cursor_not_advancing_raises(self):
        """Cursor value <= current start raises ValueError (prevents infinite loop)."""
        set_cursor_seq([0])  # cursor 0 doesn't advance from start 0
        step = {
            "name": "seg",
            "type": "window",
            "input": "${content}",
            "item_var": "wc",
            "size": 5,
            "steps": [_window_advance_step()],
        }
        with pytest.raises(ValueError, match="does not advance"):
            self._run(step, {"content": _make_content(10), "next_pos": None})

    def test_non_integer_cursor_raises(self):
        """Non-integer, non-null cursor raises ValueError."""
        set_cursor_seq(["bad"])
        step = {
            "name": "seg",
            "type": "window",
            "input": "${content}",
            "item_var": "wc",
            "size": 5,
            "steps": [_window_advance_step()],
        }
        with pytest.raises(ValueError, match="must be a non-negative integer or null"):
            self._run(step, {"content": _make_content(10), "next_pos": None})
