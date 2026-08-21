"""A window step's loop variables must be known to the linter, not only to the runtime.

Reported 2026-08-21 by an AI session in `nida-institute/discourse-flow`
(`collab/sp/windowing-semantics-gap.md`): *"`window_num` exists at runtime but not to the
linter … so `${window_num}` in a step input fails lint while being valid at run time. One
side or the other is wrong."* Verified: `steps/window.py` sets it at `:299` and `:450`;
`utils/linter.py` contained no occurrence of it.

Ruled D2-A in `project/plans/plan-window-semantics.md` §4 — teach the linter. The other
direction, removing the variables, would delete working behaviour that consumer pipelines may
already use for window numbering in prompts, filenames and logs, and the blast radius is not
visible from the engine repository.

`for-each` already injects its four loop variables (`linter.py`, the `step_type ==
"for-each"` branch). `window` injecting none was an omission, not a decision — which is why
the fix is symmetry rather than a special case.
"""

from __future__ import annotations

import pytest

from llmflow.utils.linter import _validate_variable_references_recursive

# What `_run_window_dynamic` and the static path both put in each iteration context.
RUNTIME_INJECTED = (
    "window_num",
    "_window_index",
    "_window_first",
    "_window_last",
    "_window_cursor",
)


def _lint(reference: str) -> list[str]:
    """Lint a window step whose nested step reads `reference` from its iteration context."""
    steps = [
        {
            "name": "chunk",
            "type": "window",
            "for": "window_content",
            "in": "${content_list}",
            "size": 10,
            "steps": [
                {
                    "name": "inner",
                    "type": "function",
                    "function": "plugins.noop",
                    "inputs": {"label": reference},
                }
            ],
        }
    ]
    errors: list[str] = []
    _validate_variable_references_recursive(steps, {"content_list": []}, set(), errors)
    return errors


@pytest.mark.parametrize("name", RUNTIME_INJECTED)
def test_a_runtime_injected_window_variable_lints_clean(name: str):
    """Whatever the runtime provides, the linter must accept — or lint is wrong, not the run."""
    errors = _lint(f"${{{name}}}")

    assert errors == [], (
        f"`${{{name}}}` is set by the window step at run time but rejected by lint: {errors}"
    )


def test_the_loop_variable_itself_still_lints_clean():
    """The `for:` binding was already handled; this pins it against the fix."""
    assert _lint("${window_content}") == []


def test_an_undefined_variable_is_still_an_error():
    """The fix must not open the field up — only the names the runtime really sets."""
    errors = _lint("${no_such_variable}")

    assert errors, "an undefined reference inside a window step must still fail lint"


def test_a_plausible_near_miss_is_still_an_error():
    """`window_index` without the underscore is a typo the runtime would not satisfy."""
    errors = _lint("${window_index}")

    assert errors, (
        "the runtime sets `_window_index`, not `window_index`; lint must not accept both"
    )
