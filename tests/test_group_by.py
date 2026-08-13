"""
TDD tests for group-by and order-by on for-each steps.

Tests are written BEFORE implementation and should fail until
_group_items, _sort_groups, and the run_for_each_step group-by
branch are implemented.

Follows XQuery FLWOR group-by semantics:
  - Items with the same key expression result → one group
  - Each iteration receives {key, items} as item_var
  - order-by sorts groups before iteration
  - Works with parallel: (groups are independent)
"""
import sys
import types
import pytest

from llmflow.steps.for_each import _group_items, _sort_groups, run_for_each_step
from llmflow.utils.linter import _lint_for_each_group_by, lint_pipeline_steps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reg(mod_name, **fns):
    mod = types.ModuleType(mod_name)
    for name, fn in fns.items():
        setattr(mod, name, fn)
    sys.modules[mod_name] = mod
    return lambda: sys.modules.pop(mod_name, None)


# ---------------------------------------------------------------------------
# _group_items
# ---------------------------------------------------------------------------

class TestGroupItems:

    def test_groups_by_string_field(self):
        items = [
            {"div": "A", "seq": 1},
            {"div": "B", "seq": 2},
            {"div": "A", "seq": 3},
        ]
        groups = _group_items(items, "${item.div}", {})
        keys = [g["key"] for g in groups]
        assert set(keys) == {"A", "B"}
        a = next(g for g in groups if g["key"] == "A")
        assert len(a["items"]) == 2
        assert a["items"][0]["seq"] == 1
        assert a["items"][1]["seq"] == 3

    def test_preserves_insertion_order_within_group(self):
        items = [{"k": "X", "n": i} for i in range(5)]
        groups = _group_items(items, "${item.k}", {})
        assert len(groups) == 1
        assert [g["n"] for g in groups[0]["items"]] == list(range(5))

    def test_empty_input_returns_empty(self):
        assert _group_items([], "${item.k}", {}) == []

    def test_numeric_key(self):
        items = [{"ch": 1}, {"ch": 2}, {"ch": 1}]
        groups = _group_items(items, "${item.ch}", {})
        assert len(groups) == 2
        assert all(isinstance(g["key"], int) for g in groups)

    def test_single_item_groups(self):
        items = [{"k": "A"}, {"k": "B"}, {"k": "C"}]
        groups = _group_items(items, "${item.k}", {})
        assert len(groups) == 3
        assert all(len(g["items"]) == 1 for g in groups)

    def test_all_same_key(self):
        items = [{"k": "X"} for _ in range(4)]
        groups = _group_items(items, "${item.k}", {})
        assert len(groups) == 1
        assert len(groups[0]["items"]) == 4

    def test_group_order_follows_first_appearance(self):
        """Groups appear in order of their first item's appearance in input."""
        items = [{"k": "B"}, {"k": "A"}, {"k": "B"}, {"k": "C"}]
        groups = _group_items(items, "${item.k}", {})
        assert [g["key"] for g in groups] == ["B", "A", "C"]

    def test_context_available_in_key_expression(self):
        """Key expression can reference parent context variables."""
        items = [{"raw": 1}, {"raw": 2}, {"raw": 1}]
        # (Simple field access is enough; context reference tested separately)
        groups = _group_items(items, "${item.raw}", {"book": "Luke"})
        assert len(groups) == 2


# ---------------------------------------------------------------------------
# _sort_groups
# ---------------------------------------------------------------------------

class TestSortGroups:

    def _make_groups(self, keys):
        return [{"key": k, "items": [{"k": k}]} for k in keys]

    def test_sort_ascending_by_key(self):
        groups = self._make_groups(["C", "A", "B"])
        sorted_groups = _sort_groups(groups, "${group.key}", {}, direction="ascending")
        assert [g["key"] for g in sorted_groups] == ["A", "B", "C"]

    def test_sort_descending_by_key(self):
        groups = self._make_groups(["A", "C", "B"])
        sorted_groups = _sort_groups(groups, "${group.key}", {}, direction="descending")
        assert [g["key"] for g in sorted_groups] == ["C", "B", "A"]

    def test_sort_numeric(self):
        groups = self._make_groups([3, 1, 2])
        sorted_groups = _sort_groups(groups, "${group.key}", {}, direction="ascending")
        assert [g["key"] for g in sorted_groups] == [1, 2, 3]

    def test_sort_by_items_count(self):
        groups = [
            {"key": "A", "items": [1, 2, 3]},
            {"key": "B", "items": [1]},
            {"key": "C", "items": [1, 2]},
        ]
        sorted_groups = _sort_groups(
            groups, "${len(group.items)}", {}, direction="ascending"
        )
        assert [g["key"] for g in sorted_groups] == ["B", "C", "A"]

    def test_empty_groups_returns_empty(self):
        assert _sort_groups([], "${group.key}", {}, direction="ascending") == []

    def test_stable_sort_preserves_relative_order(self):
        """Equal keys preserve original order (stable sort)."""
        groups = [{"key": 1, "items": [{"n": "first"}]}, {"key": 1, "items": [{"n": "second"}]}]
        sorted_groups = _sort_groups(groups, "${group.key}", {}, direction="ascending")
        assert sorted_groups[0]["items"][0]["n"] == "first"


# ---------------------------------------------------------------------------
# run_for_each_step with group-by
# ---------------------------------------------------------------------------

class TestForEachGroupBy:

    def test_each_iteration_receives_group_dict(self):
        """item_var receives {key, items} when group-by is set."""
        received = []
        cleanup = _reg("__gb_test1", capture=lambda group: received.append(group) or group)
        try:
            context = {"items": [{"div": "A"}, {"div": "B"}, {"div": "A"}]}
            step = {
                "name": "loop", "type": "for-each",
                "in": "${items}",
                "group_by": "${item.div}",
                "for": "group",
                "steps": [{
                    "name": "cap", "type": "function",
                    "function": "__gb_test1.capture",
                    "inputs": {"group": "${group}"},
                    "output": "g",
                }],
            }
            run_for_each_step(step, context, {})
            assert len(received) == 2
            keys = {g["key"] for g in received}
            assert keys == {"A", "B"}
            a = next(g for g in received if g["key"] == "A")
            assert len(a["items"]) == 2
        finally:
            cleanup()

    def test_results_ordered_by_first_appearance(self):
        """Without order-by, groups appear in first-appearance order."""
        order = []
        cleanup = _reg("__gb_test2", record=lambda group: order.append(group["key"]) or group["key"])
        try:
            context = {"items": [{"k": "B"}, {"k": "A"}, {"k": "B"}]}
            step = {
                "name": "loop", "type": "for-each",
                "in": "${items}",
                "group_by": "${item.k}",
                "for": "group",
                "steps": [{
                    "name": "rec", "type": "function",
                    "function": "__gb_test2.record",
                    "inputs": {"group": "${group}"},
                    "output": "key",
                    "append_to": "keys",
                }],
            }
            run_for_each_step(step, context, {})
            assert context["keys"] == ["B", "A"]
        finally:
            cleanup()

    def test_order_by_sorts_groups(self):
        """order-by sorts groups before iterating."""
        order = []
        cleanup = _reg("__gb_test3", record=lambda group: order.append(group["key"]) or group["key"])
        try:
            context = {"items": [{"k": "C"}, {"k": "A"}, {"k": "B"}]}
            step = {
                "name": "loop", "type": "for-each",
                "in": "${items}",
                "group_by": "${item.k}",
                "order_by": "${group.key}",
                "for": "group",
                "steps": [{
                    "name": "rec", "type": "function",
                    "function": "__gb_test3.record",
                    "inputs": {"group": "${group}"},
                    "output": "key",
                    "append_to": "keys",
                }],
            }
            run_for_each_step(step, context, {})
            assert context["keys"] == ["A", "B", "C"]
        finally:
            cleanup()

    def test_order_by_descending(self):
        order = []
        cleanup = _reg("__gb_test4", record=lambda group: order.append(group["key"]) or group["key"])
        try:
            context = {"items": [{"k": "A"}, {"k": "C"}, {"k": "B"}]}
            step = {
                "name": "loop", "type": "for-each",
                "in": "${items}",
                "group_by": "${item.k}",
                "order_by":
                    {"key": "${group.key}", "direction": "descending"},
                "for": "group",
                "steps": [{
                    "name": "rec", "type": "function",
                    "function": "__gb_test4.record",
                    "inputs": {"group": "${group}"},
                    "output": "key",
                    "append_to": "keys",
                }],
            }
            run_for_each_step(step, context, {})
            assert context["keys"] == ["C", "B", "A"]
        finally:
            cleanup()

    def test_append_to_accumulates_in_group_order(self):
        cleanup = _reg("__gb_test5", identity=lambda items: items)
        try:
            context = {"items": [
                {"div": 1, "text": "a"},
                {"div": 2, "text": "b"},
                {"div": 1, "text": "c"},
            ]}
            step = {
                "name": "loop", "type": "for-each",
                "in": "${items}",
                "group_by": "${item.div}",
                "order_by": "${group.key}",
                "for": "group",
                "steps": [{
                    "name": "id", "type": "function",
                    "function": "__gb_test5.identity",
                    "inputs": {"items": "${group.items}"},
                    "output": "group_items",
                    "append_to": "all_groups",
                }],
            }
            run_for_each_step(step, context, {})
            # Group 1 has items a,c; group 2 has item b; ordered by key → 1 then 2
            assert len(context["all_groups"]) == 2
            assert context["all_groups"][0] == [{"div": 1, "text": "a"}, {"div": 1, "text": "c"}]
            assert context["all_groups"][1] == [{"div": 2, "text": "b"}]
        finally:
            cleanup()

    def test_group_by_with_parallel(self):
        """group-by works with parallel: — groups are independent."""
        cleanup = _reg("__gb_test6", identity=lambda items: items)
        try:
            context = {"items": [
                {"div": "A", "n": 1}, {"div": "B", "n": 2},
                {"div": "A", "n": 3}, {"div": "C", "n": 4},
            ]}
            step = {
                "name": "loop", "type": "for-each",
                "in": "${items}",
                "group_by": "${item.div}",
                "order_by": "${group.key}",
                "for": "group",
                "parallel": 3,
                "steps": [{
                    "name": "id", "type": "function",
                    "function": "__gb_test6.identity",
                    "inputs": {"items": "${group.items}"},
                    "output": "g",
                    "append_to": "groups",
                }],
            }
            run_for_each_step(step, context, {})
            # Ordered A, B, C
            assert len(context["groups"]) == 3
            assert context["groups"][0][0]["div"] == "A"
            assert context["groups"][1][0]["div"] == "B"
            assert context["groups"][2][0]["div"] == "C"
        finally:
            cleanup()

    def test_group_key_available_in_step(self):
        """${group.key} is accessible inside steps."""
        keys_seen = []
        cleanup = _reg("__gb_test7", record=lambda key: keys_seen.append(key) or key)
        try:
            context = {"items": [{"div": "X"}, {"div": "Y"}]}
            step = {
                "name": "loop", "type": "for-each",
                "in": "${items}",
                "group_by": "${item.div}",
                "order_by": "${group.key}",
                "for": "group",
                "steps": [{
                    "name": "rec", "type": "function",
                    "function": "__gb_test7.record",
                    "inputs": {"key": "${group.key}"},
                    "output": "k",
                    "append_to": "keys",
                }],
            }
            run_for_each_step(step, context, {})
            assert context["keys"] == ["X", "Y"]
        finally:
            cleanup()

    def test_empty_input_produces_no_iterations(self):
        cleanup = _reg("__gb_test8", noop=lambda group: group)
        try:
            context = {"items": []}
            step = {
                "name": "loop", "type": "for-each",
                "in": "${items}",
                "group_by": "${item.div}",
                "for": "group",
                "steps": [{
                    "name": "n", "type": "function",
                    "function": "__gb_test8.noop",
                    "inputs": {"group": "${group}"},
                    "output": "g",
                    "append_to": "results",
                }],
            }
            run_for_each_step(step, context, {})
            assert context.get("results", []) == []
        finally:
            cleanup()

    def test_without_group_by_order_by_sorts_input(self):
        """order-by without group-by sorts items before iterating."""
        cleanup = _reg("__gb_test9", identity=lambda value: value)
        try:
            context = {"items": [{"n": 3}, {"n": 1}, {"n": 2}]}
            step = {
                "name": "loop", "type": "for-each",
                "in": "${items}",
                "order_by": "${item.n}",
                "for": "x",
                "steps": [{
                    "name": "id", "type": "function",
                    "function": "__gb_test9.identity",
                    "inputs": {"value": "${x.n}"},
                    "output": "v",
                    "append_to": "results",
                }],
            }
            run_for_each_step(step, context, {})
            assert context["results"] == [1, 2, 3]
        finally:
            cleanup()


# ---------------------------------------------------------------------------
# Linter: group-by and order-by validation
# ---------------------------------------------------------------------------

class TestLintGroupBy:

    def _lint(self, step):
        errors = []
        _lint_for_each_group_by(step, errors)
        return errors

    def test_valid_group_by(self):
        assert self._lint({
            "name": "s", "type": "for-each",
            "group_by": "${item.div}",
            "steps": [{}],
        }) == []

    def test_valid_group_by_with_order_by(self):
        assert self._lint({
            "name": "s", "type": "for-each",
            "group_by": "${item.div}",
            "order_by": "${group.key}",
            "steps": [{}],
        }) == []

    def test_valid_order_by_without_group_by(self):
        assert self._lint({
            "name": "s", "type": "for-each",
            "order_by": "${item.sequence}",
            "steps": [{}],
        }) == []

    def test_order_by_dict_form_valid(self):
        assert self._lint({
            "name": "s", "type": "for-each",
            "order_by": {"key": "${item.n}", "direction": "descending"},
            "steps": [{}],
        }) == []

    def test_order_by_list_form_valid(self):
        assert self._lint({
            "name": "s", "type": "for-each",
            "order_by": [
                {"key": "${item.chapter}", "direction": "ascending"},
                {"key": "${item.verse}", "direction": "ascending"},
            ],
            "steps": [{}],
        }) == []

    def test_group_by_missing_item_ref_is_error(self):
        """group-by expression must reference ${item.*}."""
        errors = self._lint({
            "name": "s", "type": "for-each",
            "group_by": "${book}",   # references context, not item
            "steps": [{}],
        })
        assert any("item" in e for e in errors)

    def test_order_by_invalid_direction_is_error(self):
        errors = self._lint({
            "name": "s", "type": "for-each",
            "order_by": {"key": "${item.n}", "direction": "sideways"},
            "steps": [{}],
        })
        assert any("direction" in e for e in errors)

    def test_lint_pipeline_steps_recognises_group_by(self):
        steps = [{
            "name": "bad", "type": "for-each",
            "in": "${items}", "for": "x",
            "group_by": "${book}",   # should error
            "steps": [{}],
        }]
        errors = lint_pipeline_steps(steps)
        assert any("item" in e for e in errors)

    def test_lint_pipeline_steps_valid_group_by_no_errors(self):
        steps = [{
            "name": "ok", "type": "for-each",
            "in": "${items}", "for": "group",
            "group_by": "${item.division_id}",
            "order_by": "${group.key}",
            "steps": [{"name": "x", "type": "function", "function": "f"}],
        }]
        errors = lint_pipeline_steps(steps)
        group_errors = [e for e in errors if "group_by" in e or "order_by" in e]
        assert group_errors == []
