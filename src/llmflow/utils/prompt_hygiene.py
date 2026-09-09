"""Faults in a prompt that only a run can see.

The one here is contamination: a prompt whose example is the passage under test. The model then
reproduces the example rather than performing the task, the run looks like a success, and nothing
in the output says otherwise.

Checked against the **template**, never the rendered prompt. A `.gpt` file holds the examples
while the data arrives through `{{var}}`, so the passage under test always appears in a rendered
prompt and its presence there means nothing at all.
"""

from __future__ import annotations

from typing import Any, Mapping

from llmflow.defects import DEFECT_LOG_KEY
from llmflow.utils import verse_ranges as _ranges
from llmflow.utils.scripture import ASSUMED_SCHEME
from llmflow.utils.versification import references_in


def contaminating_references(template: str, passage: Any, scheme: str = ASSUMED_SCHEME) -> list:
    """References in *template* that overlap *passage*.

    Overlap rather than equality: a template citing `MRK 1:1-8` contaminates a run on `MRK 1:5`.
    `verse_ranges.overlaps` already answers that, so there is no second implementation of
    reference comparison here.

    Both sides are read in the same *scheme*, which is why one may be assumed here where the read
    path refuses to assume: this compares two references with each other rather than resolving
    either against a text, so a wrong scheme can only mislead at a chapter boundary where two
    schemes disagree about a chapter's length. That is an acceptable error in a warning, and is
    not acceptable when fetching verses, which is why the two behave differently.

    A passage this cannot parse yields nothing. A pipeline may name something unparseable, and
    saying so is the business of the check that owns parsing, not of this one.
    """
    target_text = str(passage or "").strip()
    if not target_text:
        return []
    try:
        target = _ranges.Range.parse(target_text, scheme=scheme)
    except Exception:
        return []

    found = []
    for reference in references_in(template):
        try:
            if _ranges.overlaps(_ranges.Range.parse(reference, scheme=scheme), target):
                found.append(reference)
        except Exception:
            # An unparseable candidate is not a finding; `references_in` is permissive by design.
            continue
    return found


def warn_about_contamination(template: str, prompt_path: Any, context: Mapping[str, Any]) -> None:
    """Record contamination as a defect, and carry on.

    A warning rather than a refusal: the run still produces something, and what it produces is
    exactly what a reader needs in order to judge the finding. Refusing would also make the check
    unrunnable on the many prompts that legitimately cite a passage for another reason.
    """
    log = context.get(DEFECT_LOG_KEY) if isinstance(context, Mapping) else None
    if log is None:
        return
    passage = context.get("passage")
    found = contaminating_references(template, passage)
    if not found:
        return
    log.record(
        "prompt",
        f"{prompt_path} uses {', '.join(found)} as an example, which overlaps the passage under "
        f"test ({passage}). The model can reproduce the example instead of performing the task, "
        f"and the run will look like a success.",
        location=str(passage),
        prompt=str(prompt_path),
        references=found,
    )
