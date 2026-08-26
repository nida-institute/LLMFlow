"""`size` and `stride` accept a variable resolved before the loop starts — and nothing later.

Plan: `project/plans/plan-window-semantics.md` §4, D1. Reported via discourse-flow,
2026-08-21, as "`size` is never resolved" while `in:` on the same step is.

**The reasoning, and its limit.** The Captain: *"being able to compute this at the start of a
'loop' is also helpful for the implementation … a variable that changes during loop execution
is going to be harder to debug, that's what the cursor is for."* Then, on his own argument:
*"my argument doesn't reach variables that can be resolved before the 'loop' begins."*

So resolution happens **once, at step entry** — the same place `in:` is resolved, which is by
construction before the first iteration. A value fixed before the loop is still a constant for
the loop, so every property the restriction protected survives: the partition is knowable at
the start, identical on every iteration, and reproducible under `--rewind-to`.

**What lint can and cannot do**, and the Captain's answer to the gap: *"lint can warn that it
can't determine if it's a positive integer or not, and that runtime errors are possible."* So:

| `size:` | lint |
|---|---|
| `50` | silent — verified |
| `"${window_size}"`, name known | **warning** — unverifiable, may fail at run time |
| `"${typo}"`, name unknown | **error**, from the linter's existing generic variable check |
| `0` | error, plain message — a typo must not start lecturing about variables |
| `"10"` | error — a quoted literal is not an expression, and is not coerced |

**Scope held deliberately:** `size` and `stride` only. `include_partial` stays literal because a
string→bool coercion where `bool("false")` is `True` is a footgun with no demand behind it, and
the two token fields stay literal for the same reason.
"""

from __future__ import annotations

import pytest

from llmflow.steps.window import run_window_step
from llmflow.utils.linter import _lint_window_step


def _lint(step: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    _lint_window_step(step, errors, warnings)
    return errors, warnings


def _valid(**overrides) -> dict:
    step = {
        "name": "w",
        "for": "chunk",
        "in": "${items}",
        "size": 10,
        "steps": [{"name": "inner", "type": "function", "function": "noop"}],
    }
    step.update(overrides)
    return step


class TestLint:
    def test_a_literal_lints_clean_and_silent(self):
        errors, warnings = _lint(_valid(size=10, stride=5))
        assert errors == []
        assert warnings == []

    def test_a_variable_is_accepted_with_a_warning(self):
        errors, warnings = _lint(_valid(size="${window_size}"))

        assert errors == [], f"a variable is valid for 'size' now: {errors}"
        joined = " ".join(warnings).lower()
        assert "size" in joined and "run time" in joined.replace("runtime", "run time"), (
            "lint must say it cannot verify the value and that a bad one fails at run time. "
            f"Got: {warnings}"
        )

    def test_a_variable_stride_is_accepted_with_a_warning(self):
        errors, warnings = _lint(_valid(size=10, stride="${window_stride}"))
        assert errors == []
        assert any("stride" in w for w in warnings), warnings

    def test_a_genuinely_wrong_size_still_gets_the_plain_message(self):
        errors, warnings = _lint(_valid(size=0))

        joined = " ".join(errors).lower()
        assert "positive integer" in joined, errors
        assert "variable" not in joined, (
            f"0 is not a variable; the variable explanation does not belong here: {errors}"
        )
        assert warnings == [], "a plain bad value earns no unverifiable-warning"

    def test_a_quoted_literal_is_not_an_expression(self):
        """`size: "10"` is a typo, not parameterisation. Coercing it would hide the mistake."""
        errors, _ = _lint(_valid(size="10"))
        assert errors, "a quoted literal must still be an error"

    def test_the_warning_is_optional_for_callers(self):
        """Seven existing call sites pass only `errors`; none of them should break."""
        errors: list[str] = []
        _lint_window_step(_valid(size="${window_size}"), errors)
        assert errors == []


class TestRuntime:
    def test_a_variable_holding_an_int_partitions_the_list(self):
        context = {"items": [1, 2, 3, 4], "window_size": 2, "seen": []}
        step = _valid(size="${window_size}", steps=[])

        run_window_step(step, context, {})  # no inner steps: partitioning is what matters

    def test_a_var_supplied_string_behaves_as_the_integer(self):
        """`--var window_size=2` arrives as the string "2" — the case that would bite."""
        as_int = {"items": [1, 2, 3, 4], "window_size": 2}
        as_str = {"items": [1, 2, 3, 4], "window_size": "2"}
        step = _valid(size="${window_size}", steps=[])

        run_window_step(step, as_int, {})
        run_window_step(step, as_str, {})

    def test_a_variable_resolving_to_nonsense_names_the_resolved_value(self):
        context = {"items": [1, 2, 3], "window_size": "abc"}
        step = _valid(size="${window_size}", steps=[])

        with pytest.raises(ValueError, match=r"abc"):
            run_window_step(step, context, {})

    def test_an_unresolved_variable_says_so(self):
        """A name nothing defines comes back from `resolve` as the literal `${...}` string."""
        context = {"items": [1, 2, 3]}
        step = _valid(size="${never_set}", steps=[])

        with pytest.raises(ValueError, match=r"never_set"):
            run_window_step(step, context, {})

    def test_a_boolean_is_not_an_integer(self):
        """`isinstance(True, int)` is True in Python, so this needs its own guard."""
        context = {"items": [1, 2, 3], "window_size": True}
        step = _valid(size="${window_size}", steps=[])

        with pytest.raises(ValueError):
            run_window_step(step, context, {})

    def test_a_literal_still_works_unchanged(self):
        context = {"items": [1, 2, 3, 4]}
        run_window_step(_valid(size=2, steps=[]), context, {})
