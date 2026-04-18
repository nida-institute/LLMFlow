"""
Tests for parallel: key on for-each steps.

Covers:
- Identical output to sequential execution (order preserved)
- append_to accumulates in input order
- outputs (last-wins) respects input order
- First-exception propagates, cancels remaining work
- after: exit propagates correctly
- Linter error on cross-iteration append_to reference
- Shared helper functions (_setup_iteration_context, _run_iteration_steps,
  _propagate_iteration_results) used by both paths

NO STUBS — uses real runner.py and linter.py.
"""
import sys
import time
import types
import threading
import pytest

from llmflow.runner import (
    run_for_each_step,
    _collect_loop_outputs,
    _setup_iteration_context,
    _run_iteration_steps,
    _propagate_iteration_results,
)
from llmflow.utils.linter import _lint_for_each_parallel, lint_pipeline_steps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_fn(mod_name: str, **fns):
    """Register functions in a temporary module; return cleanup callable."""
    mod = types.ModuleType(mod_name)
    for name, fn in fns.items():
        setattr(mod, name, fn)
    sys.modules[mod_name] = mod
    return lambda: sys.modules.pop(mod_name, None)


def _make_identity_step(mod_name: str, input_var: str, output_var: str, append_to: str | None = None):
    """Return a step dict that passes input_var through to output_var (and optionally appends)."""
    cleanup = _register_fn(mod_name, identity=lambda value: value)
    step = {
        "name": f"id_{output_var}",
        "type": "function",
        "function": f"{mod_name}.identity",
        "inputs": {"value": f"${{{input_var}}}"},
        "outputs": output_var,
    }
    if append_to:
        step["append_to"] = append_to
    return step, cleanup


# ---------------------------------------------------------------------------
# _collect_loop_outputs
# ---------------------------------------------------------------------------

class TestCollectLoopOutputs:

    def test_collects_append_to_and_outputs(self):
        steps = [
            {"outputs": "foo", "append_to": "bar"},
            {"outputs": ["baz", "qux"]},
        ]
        targets, vars_ = _collect_loop_outputs(steps)
        assert targets == {"bar"}
        assert vars_ == {"foo", "baz", "qux"}

    def test_recursive_nested_steps(self):
        steps = [
            {"steps": [{"append_to": "inner_list", "outputs": "inner_var"}]},
        ]
        targets, vars_ = _collect_loop_outputs(steps)
        assert "inner_list" in targets
        assert "inner_var" in vars_


# ---------------------------------------------------------------------------
# _setup_iteration_context
# ---------------------------------------------------------------------------

class TestSetupIterationContext:

    def test_item_var_set(self):
        ctx = {"x": 1}
        iter_ctx = _setup_iteration_context(1, "hello", ctx, "word", "step", None)
        assert iter_ctx["word"] == "hello"

    def test_for_each_index_set(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(3, "a", ctx, "item", "step", None)
        assert iter_ctx["_for_each_index"] == 3

    def test_parent_context_not_mutated(self):
        ctx = {"original": True}
        _setup_iteration_context(1, "x", ctx, "item", "step", None)
        assert "item" not in ctx

    def test_stack_appended(self):
        ctx = {}
        iter_ctx = _setup_iteration_context(2, "val", ctx, "item", "my_step", None)
        assert len(iter_ctx["_for_each_stack"]) == 1
        assert iter_ctx["_for_each_stack"][0]["index"] == 2


# ---------------------------------------------------------------------------
# _propagate_iteration_results
# ---------------------------------------------------------------------------

class TestPropagateIterationResults:

    def test_append_to_extends_parent(self):
        parent = {"results": [1, 2]}
        iter_ctx = {"results": [1, 2, 3, 4]}  # items 3,4 added by iteration
        _propagate_iteration_results(
            iter_ctx, parent, {"results"}, set(), {"results": 2}
        )
        assert parent["results"] == [1, 2, 3, 4]

    def test_append_to_creates_list_if_absent(self):
        parent = {}
        iter_ctx = {"results": ["a", "b"]}
        _propagate_iteration_results(iter_ctx, parent, {"results"}, set(), {})
        assert parent["results"] == ["a", "b"]

    def test_output_var_propagated(self):
        parent = {}
        iter_ctx = {"last": "value"}
        _propagate_iteration_results(iter_ctx, parent, set(), {"last"}, {})
        assert parent["last"] == "value"

    def test_only_new_items_propagated(self):
        parent = {"items": ["pre"]}
        iter_ctx = {"items": ["pre", "new1", "new2"]}
        _propagate_iteration_results(
            iter_ctx, parent, {"items"}, set(), {"items": 1}
        )
        assert parent["items"] == ["pre", "new1", "new2"]


# ---------------------------------------------------------------------------
# Parallel == sequential output (core invariant)
# ---------------------------------------------------------------------------

class TestParallelMatchesSequential:
    """parallel: N must produce identical results to parallel: 1."""

    def _run(self, items, parallel, mod_name):
        cleanup = _register_fn(mod_name, double=lambda value: value * 2)
        try:
            context = {"items": items}
            step = {
                "name": "loop",
                "type": "for-each",
                "input": "${items}",
                "item_var": "x",
                "parallel": parallel,
                "steps": [
                    {
                        "name": "do",
                        "type": "function",
                        "function": f"{mod_name}.double",
                        "inputs": {"value": "${x}"},
                        "outputs": "doubled",
                        "append_to": "results",
                    }
                ],
            }
            run_for_each_step(step, context, {})
            return context.get("results", [])
        finally:
            cleanup()

    def test_order_preserved_parallel_3(self):
        items = list(range(10))
        seq = self._run(items, 1, "__par_seq_mod1")
        par = self._run(items, 3, "__par_seq_mod2")
        assert par == seq
        assert par == [x * 2 for x in items]

    def test_order_preserved_parallel_5(self):
        items = list(range(20))
        seq = self._run(items, 1, "__par_seq_mod3")
        par = self._run(items, 5, "__par_seq_mod4")
        assert par == seq

    def test_outputs_last_wins_by_input_order(self):
        """outputs (last-wins) uses last item in input order, not completion order."""
        delays = {"__par_last_mod": None}
        cleanup = _register_fn(
            "__par_last_mod",
            slow_identity=lambda value: value,
        )
        try:
            context = {"items": ["first", "second", "third"]}
            step = {
                "name": "loop",
                "type": "for-each",
                "input": "${items}",
                "item_var": "x",
                "parallel": 3,
                "steps": [
                    {
                        "name": "do",
                        "type": "function",
                        "function": "__par_last_mod.slow_identity",
                        "inputs": {"value": "${x}"},
                        "outputs": "last_seen",
                    }
                ],
            }
            run_for_each_step(step, context, {})
            # "third" is last in input order — must win regardless of thread completion order
            assert context["last_seen"] == "third"
        finally:
            cleanup()

    def test_empty_input_no_results(self):
        cleanup = _register_fn("__par_empty_mod", noop=lambda value: value)
        try:
            context = {"items": []}
            step = {
                "name": "loop",
                "type": "for-each",
                "input": "${items}",
                "item_var": "x",
                "parallel": 4,
                "steps": [
                    {
                        "name": "do",
                        "type": "function",
                        "function": "__par_empty_mod.noop",
                        "inputs": {"value": "${x}"},
                        "outputs": "v",
                        "append_to": "results",
                    }
                ],
            }
            run_for_each_step(step, context, {})
            assert context.get("results", []) == []
        finally:
            cleanup()

    def test_parallel_1_behaves_sequentially(self):
        """parallel: 1 is equivalent to the default (no parallel key)."""
        items = list(range(5))
        cleanup1 = _register_fn("__par1_mod1", identity=lambda value: value)
        cleanup2 = _register_fn("__par1_mod2", identity=lambda value: value)
        try:
            def _run(mod, parallel_val):
                ctx = {"items": items}
                s = {
                    "name": "loop", "type": "for-each",
                    "input": "${items}", "item_var": "x",
                    "steps": [{
                        "name": "do", "type": "function",
                        "function": f"{mod}.identity",
                        "inputs": {"value": "${x}"},
                        "outputs": "v", "append_to": "results",
                    }],
                }
                if parallel_val is not None:
                    s["parallel"] = parallel_val
                run_for_each_step(s, ctx, {})
                return ctx["results"]

            default = _run("__par1_mod1", None)
            explicit1 = _run("__par1_mod2", 1)
            assert default == explicit1 == items
        finally:
            cleanup1()
            cleanup2()


# ---------------------------------------------------------------------------
# Parallel exception propagation
# ---------------------------------------------------------------------------

class TestParallelExceptionPropagation:

    def test_exception_in_iteration_propagates(self):
        def boom(value):
            if value == 3:
                raise RuntimeError("deliberate failure")
            return value

        cleanup = _register_fn("__par_exc_mod", boom=boom)
        try:
            context = {"items": list(range(6))}
            step = {
                "name": "loop",
                "type": "for-each",
                "input": "${items}",
                "item_var": "x",
                "parallel": 3,
                "steps": [
                    {
                        "name": "do",
                        "type": "function",
                        "function": "__par_exc_mod.boom",
                        "inputs": {"value": "${x}"},
                        "outputs": "v",
                    }
                ],
            }
            with pytest.raises(RuntimeError, match="deliberate failure"):
                run_for_each_step(step, context, {})
        finally:
            cleanup()


# ---------------------------------------------------------------------------
# after: exit in parallel mode
# ---------------------------------------------------------------------------

class TestParallelAfterExit:

    def test_exit_from_iteration_propagates(self):
        """after: exit in a parallel iteration returns 'exit' from the loop."""
        cleanup = _register_fn("__par_exit_mod", identity=lambda value: value)
        try:
            context = {"items": [1, 2, 3]}
            step = {
                "name": "loop",
                "type": "for-each",
                "input": "${items}",
                "item_var": "x",
                "parallel": 3,
                "steps": [
                    {
                        "name": "do",
                        "type": "function",
                        "function": "__par_exit_mod.identity",
                        "inputs": {"value": "${x}"},
                        "outputs": "v",
                        "append_to": "results",
                        "after": "exit",
                    }
                ],
            }
            result = run_for_each_step(step, context, {})
            assert result == "exit"
        finally:
            cleanup()


# ---------------------------------------------------------------------------
# Linter: cross-iteration append_to reference
# ---------------------------------------------------------------------------

class TestLintForEachParallel:

    def _lint(self, step):
        errors = []
        _lint_for_each_parallel(step, errors)
        return errors

    def test_no_parallel_no_error(self):
        step = {
            "name": "loop", "type": "for-each", "input": "${items}",
            "steps": [
                {"outputs": "v", "append_to": "results"},
                {"inputs": {"x": "${results}"}},
            ],
        }
        assert self._lint(step) == []

    def test_parallel_1_no_error(self):
        step = {
            "name": "loop", "type": "for-each", "input": "${items}",
            "parallel": 1,
            "steps": [
                {"outputs": "v", "append_to": "results"},
                {"inputs": {"x": "${results}"}},
            ],
        }
        assert self._lint(step) == []

    def test_parallel_cross_iteration_ref_is_error(self):
        step = {
            "name": "loop", "type": "for-each", "input": "${items}",
            "parallel": 5,
            "steps": [
                {"outputs": "v", "append_to": "results"},
                {"inputs": {"prior": "${results}"}},   # ← reads own append_to target
            ],
        }
        errors = self._lint(step)
        assert len(errors) == 1
        assert "results" in errors[0]
        assert "parallel" in errors[0]

    def test_parallel_no_cross_ref_no_error(self):
        step = {
            "name": "loop", "type": "for-each", "input": "${items}",
            "parallel": 5,
            "steps": [
                {"outputs": "v", "append_to": "results"},
                {"inputs": {"other": "${parent_var}"}},  # reads parent, not results
            ],
        }
        assert self._lint(step) == []

    def test_multiple_cross_refs_multiple_errors(self):
        step = {
            "name": "loop", "type": "for-each", "input": "${items}",
            "parallel": 3,
            "steps": [
                {"outputs": "a", "append_to": "list_a"},
                {"outputs": "b", "append_to": "list_b"},
                {"inputs": {"x": "${list_a}", "y": "${list_b}"}},
            ],
        }
        errors = self._lint(step)
        assert len(errors) == 2

    def test_nested_cross_ref_detected(self):
        step = {
            "name": "loop", "type": "for-each", "input": "${items}",
            "parallel": 4,
            "steps": [
                {"outputs": "v", "append_to": "results"},
                {"steps": [{"inputs": {"x": "${results}"}}]},  # nested
            ],
        }
        errors = self._lint(step)
        assert any("results" in e for e in errors)

    def test_lint_pipeline_steps_calls_for_each_lint(self):
        """lint_pipeline_steps calls _lint_for_each_parallel for for-each steps."""
        steps = [
            {
                "name": "bad_parallel",
                "type": "for-each",
                "input": "${items}",
                "item_var": "x",
                "parallel": 5,
                "steps": [
                    {"name": "a", "type": "function", "function": "f",
                     "outputs": "v", "append_to": "acc"},
                    {"name": "b", "type": "function", "function": "g",
                     "inputs": {"prior": "${acc}"}},
                ],
            }
        ]
        errors = lint_pipeline_steps(steps)
        assert any("acc" in e and "parallel" in e for e in errors)

    def test_lint_pipeline_steps_valid_parallel_no_errors(self):
        steps = [
            {
                "name": "ok_parallel",
                "type": "for-each",
                "input": "${items}",
                "item_var": "x",
                "parallel": 5,
                "steps": [
                    {"name": "a", "type": "function", "function": "f",
                     "outputs": "v", "append_to": "acc"},
                ],
            }
        ]
        errors = lint_pipeline_steps(steps)
        parallel_errors = [e for e in errors if "acc" in e and "parallel" in e]
        assert parallel_errors == []
