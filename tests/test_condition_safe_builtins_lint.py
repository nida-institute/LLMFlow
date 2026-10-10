"""`sp lint` must accept a condition the evaluator accepts.

Reported by `nida-institute/discourse-flow`. `len` is one of the condition evaluator's safe
builtins, so this runs correctly:

    condition: "${len(window_segmentation.pericopes) > 1}"

but the variable validator read `len` as a variable reference and failed the pipeline —
*"Variable '${len}' not available"*. **A pipeline using a documented safe builtin could not pass
lint**, and the linter was the stricter of the two halves, which is the wrong way round: it is
the half that cannot execute the expression.

They worked around it by computing the count in a `function` step and comparing a plain name,
which costs a step per branch.

**One declaration governs both.** The validator skips any name in the same mapping the evaluator
builds its environment from, so the two cannot disagree again — rather than a second list of
builtin names kept beside the first, which is the defect this project keeps finding.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmflow import load_pipeline


def pipeline_with(condition: str, tmp_path: Path) -> Path:
    """A two-step pipeline whose second step is guarded by *condition*."""
    path = tmp_path / "pipeline.yaml"
    path.write_text(
        "name: conditions\n"
        "steps:\n"
        "  - name: make\n"
        "    type: save\n"
        '    content: "one\\ntwo\\nthree"\n'
        f'    path: "{tmp_path}/made.txt"\n'
        "    output: made\n"
        "  - name: guarded\n"
        "    type: save\n"
        f'    condition: "{condition}"\n'
        '    content: "ran"\n'
        f'    path: "{tmp_path}/guarded.txt"\n'
        "    output: guarded\n",
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    "condition",
    [
        "${len(made) > 1}",
        "${str(made) != ''}",
        "${int('2') > 1}",
        "${float('1.5') > 1}",
        "${bool(made)}",
        "${list(made) != []}",
        "${dict() == {}}",
    ],
)
def test_a_safe_builtin_in_a_condition_lints_clean(condition: str, tmp_path):
    """Every builtin the evaluator offers must be usable without failing lint."""
    result = load_pipeline(pipeline_with(condition, tmp_path)).lint()
    assert result.valid, (
        f"lint refused a condition the evaluator accepts: {condition}\n"
        f"{getattr(result, 'errors', result)}"
    )


def test_an_actually_undefined_name_is_still_refused(tmp_path):
    """The fix must not turn the check off.

    This is the half that matters: skipping the builtins is only safe if an unknown name is
    still caught. A guard that stops refusing anything is worse than no guard.
    """
    result = load_pipeline(pipeline_with("${len(nope) > 1}", tmp_path)).lint()
    assert not result.valid, "an undefined variable inside a builtin call must still fail lint"
    assert any("nope" in str(error) for error in result.errors)


def test_the_validator_reads_the_evaluator_s_own_mapping():
    """One declaration, not two lists that agree until they do not."""
    from llmflow.utils import condition_safe_builtins

    names = condition_safe_builtins()
    assert {"len", "str", "int", "float", "bool", "list", "dict"} <= set(names)
