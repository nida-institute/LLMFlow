"""`sp lint` checks a prompt against the grammar, and says what to write instead.

Lint **warns** which prompts do not conform, shows the **first** finding for each, and prints
the required sequence once, at the first finding. Non-conformance never fails a lint: the run
it describes is still correct.

A prompt declaring a header is held to the grammar; a prompt with none takes no input and
nothing checks its structure. Because the trigger is a declaration rather than a formatting
choice, any prompt may use `#` sections without being surprised by the grammar.
`data/prompt-structure.yaml` states that trigger and the reasoning behind it, and every
expectation below is read from there — nothing in this module states the order.
"""

from __future__ import annotations

import pytest

from llmflow import prompt_structure


def _conforming() -> str:
    """A prompt built from the declaration, so it conforms by construction.

    Written from `positions()` rather than typed out, because a typed-out sample is one more
    statement of the order and would go stale exactly as the worked example did.
    """
    lines = ["---", "prompt:", "  requires:", "    - passage", "---", ""]
    for position in prompt_structure.positions():
        if position.id == "frontmatter":
            continue
        if position.id == "band":
            lines += ["# NOTICE QUESTIONS", ""]
            for subsection in prompt_structure.task_subsections():
                lines += [subsection, ""]
                if subsection.endswith("Examples"):
                    lines += ["❌ counterexample: asks the reader to speculate", ""]
            continue
        if not position.headings:
            continue
        lines += [position.headings[0], "", "body", ""]
    return "\n".join(lines)


def test_the_declaration_says_what_the_grammar_binds():
    assert prompt_structure.binds().strip(), (
        "the declaration does not say which prompts the grammar binds, so the linter would "
        "have to decide it in code — two encodings of one fact"
    )


def test_the_rendered_block_carries_the_binding_rule():
    """The AI context documents the trigger by rendering it, never by restating it."""
    assert prompt_structure.binds().split(".")[0] in prompt_structure.render_markdown()


def test_the_rendered_sequence_names_every_position():
    sequence = prompt_structure.render_sequence()
    for position in prompt_structure.positions():
        assert position.id in sequence, f"position {position.n} ({position.id}) is not shown"


def test_a_prompt_with_no_header_is_not_bound():
    assert prompt_structure.check("Summarise this passage:\n\n{{passage}}\n") is None


def test_a_horizontal_rule_in_the_body_does_not_bind_a_prompt():
    """An unanchored fence match read a markdown rule as a header; the fence must be line one."""
    assert prompt_structure.check("# Notes\n\nSome prose.\n\n---\n\nMore prose.\n") is None


def test_a_heading_alone_never_binds_a_prompt():
    """Any prompt may use `#` sections without being surprised by the grammar.

    The trigger is the author's declaration, not a formatting choice, so adding a heading to a
    headerless prompt does not change what it is held to.
    """
    assert prompt_structure.check("# Notes\n\nSome prose.\n") is None


def test_a_prompt_with_a_header_is_bound_even_with_no_headings():
    """The hole the heading trigger left: the case most in need of checking escaped it."""
    finding = prompt_structure.check("---\nprompt:\n  requires:\n    - passage\n---\n\nDo it.\n")
    assert finding is not None, "a prompt declaring a header is held to the grammar"


def test_header_detection_agrees_with_the_linter_on_every_shipped_prompt():
    """Two encodings of what a header is, held to one answer.

    `check` only asks whether a header is present; `linter.parse_prompt_header` parses one. They
    are separate functions, so this pins them together on real files rather than trusting that
    two regexes stay in step.
    """
    from pathlib import Path

    from llmflow.utils.linter import parse_prompt_header

    prompts = sorted(Path(__file__).resolve().parent.parent.rglob("prompts/*.gpt"))
    assert prompts, "no shipped prompts found; this guard would check nothing"
    for path in prompts:
        text = path.read_text(encoding="utf-8")
        assert prompt_structure.declares_a_header(text) == (parse_prompt_header(str(path)) is not None), (
            f"{path.name}: the binding rule and the header parser disagree about whether this prompt has a header"
        )


def test_reference_is_the_declared_extension_point_at_the_end():
    last = prompt_structure.positions()[-1]
    assert last.id == "reference", "the extension point is the last position, or it is not an end"
    assert not last.required, "a prompt needs no reference section"
    assert last.condition in prompt_structure.conditions(), (
        "the extension point declares no side condition, so nothing constrains what goes in it"
    )


def test_a_reference_section_at_the_end_conforms():
    text = _conforming() + "\n## Discourse Function Labels\n\nA table the tasks cite.\n"
    assert prompt_structure.check(text) is None


def test_a_reference_section_before_the_checklist_is_out_of_order():
    text = _conforming().replace("# REFERENCE\n\nbody\n\n", "")
    text = text.replace("# COVERAGE & QUALITY CHECKLIST", "# REFERENCE\n\nbody\n\n# COVERAGE & QUALITY CHECKLIST")
    finding = prompt_structure.check(text)
    assert finding is not None, "the extension point is the end, so it cannot precede the checklist"
    assert "position 11" in finding.message and "position 12" in finding.message, (
        f"the inversion is reported on the heading that arrives out of order: {finding}"
    )


def test_a_heading_after_reference_is_extension_and_not_a_task_section():
    """The whole point: material the grammar does not name gets a home.

    Without this it is an unrecognised heading, which C5 reads as a task section and then
    reports as missing four subsections — a wrong diagnosis for a section that is not a task.
    """
    text = _conforming() + "\n# Label Sets\n\nA table.\n"
    assert prompt_structure.check(text) is None


def test_a_refused_heading_is_still_caught_after_reference():
    """Extension is unchecked for shape, not a hole where any heading becomes legal."""
    text = _conforming() + "\n# OUTPUT FORMAT\n\nstuff\n"
    finding = prompt_structure.check(text)
    assert finding is not None, "a refused heading in the extension region was not reported"


def test_a_conforming_prompt_has_no_finding():
    finding = prompt_structure.check(_conforming())
    assert finding is None, f"a prompt built from the declaration was rejected: {finding}"


def test_a_refused_heading_is_reported_with_what_to_write_instead():
    name, instead = next(iter(prompt_structure.refused().items()))
    if not name.startswith("# "):
        pytest.skip("the first refused entry is not a top-level heading")
    finding = prompt_structure.check(_conforming().replace("# OUTPUT SCHEMA", name))
    assert finding is not None, f"{name} is refused by the grammar and was not reported"
    assert instead in finding.message, (
        f"the finding does not say what to write instead of {name!r}. The declaration carries "
        "the remedy precisely so a rejection can be acted on."
    )


def test_sections_out_of_order_are_reported_with_both_positions():
    text = _conforming().replace("# INPUT DATA\n\nbody\n\n", "")
    text = text.replace(
        "# OUTPUT SCHEMA\n\nbody\n\n",
        "# OUTPUT SCHEMA\n\nbody\n\n# INPUT DATA\n\nbody\n\n",
    )
    finding = prompt_structure.check(text)
    assert finding is not None, "a section out of order was not reported"
    assert "INPUT DATA" in finding.message
    assert "position 7" in finding.message and "position 8" in finding.message, (
        f"the finding must name both positions so the author can see the inversion: {finding}"
    )


def test_a_missing_required_section_is_reported():
    finding = prompt_structure.check(_conforming().replace("# OUTPUT SCHEMA\n", ""))
    assert finding is not None, "a required section was absent and nothing was reported"
    assert "OUTPUT SCHEMA" in finding.message


def test_a_task_section_missing_a_subsection_is_reported():
    dropped = prompt_structure.task_subsections()[-1]
    finding = prompt_structure.check(_conforming().replace(dropped + "\n", ""))
    assert finding is not None, f"a task section without {dropped!r} was not reported"
    assert dropped.lstrip("#").strip() in finding.message


def test_only_the_first_finding_is_returned():
    """Lint shows the first error, not every error.

    A prompt broken in several ways gets one line, so a warning list stays readable.
    """
    text = _conforming().replace("# OUTPUT SCHEMA", "# OUTPUT FORMAT").replace("# INPUT DATA\n", "")
    finding = prompt_structure.check(text)
    assert finding is not None
    assert isinstance(finding.message, str)
    assert "\n" not in finding.message, "a finding is one line; lint shows the first, not a list"


def test_lint_names_each_non_conforming_prompt_and_shows_the_order_once(tmp_path):
    """End to end: which prompts do not conform, the first error, and the order once."""
    from llmflow.utils.linter import prompt_conformance_warnings

    good = tmp_path / "good.gpt"
    good.write_text(_conforming(), encoding="utf-8")
    simple = tmp_path / "simple.gpt"
    simple.write_text("# Notes\n\nSummarise the passage.\n", encoding="utf-8")
    bad = tmp_path / "bad.gpt"
    bad.write_text(_conforming().replace("# OUTPUT SCHEMA", "# OUTPUT FORMAT"), encoding="utf-8")
    worse = tmp_path / "worse.gpt"
    worse.write_text(_conforming().replace("# SYSTEM ROLE\n\nbody\n\n", ""), encoding="utf-8")

    warnings = prompt_conformance_warnings([str(p) for p in (good, simple, bad, worse)])

    assert len(warnings) == 2, f"one warning per non-conforming prompt, got {warnings}"
    assert "bad.gpt" in warnings[0] and "worse.gpt" in warnings[1]
    assert "good.gpt" not in " ".join(warnings), "a conforming prompt must not be warned about"
    assert "simple.gpt" not in " ".join(warnings), (
        "a prompt with no header is not bound by the grammar and must stay silent"
    )

    sequence = prompt_structure.render_sequence()
    assert sequence in warnings[0], "the required sequence is shown at the first finding"
    assert sequence not in warnings[1], "the sequence is shown once per run, not once per prompt"

    for warning in warnings:
        assert not warning.startswith("⚠"), (
            "the caller printing the warning list adds the marker; carrying one here printed "
            "it twice, which a unit test missed and `sp lint` showed immediately"
        )


def test_lint_reads_a_prompt_once_however_many_steps_call_it(tmp_path):
    from llmflow.utils.linter import prompt_conformance_warnings

    bad = tmp_path / "bad.gpt"
    bad.write_text(_conforming().replace("# OUTPUT SCHEMA", "# OUTPUT FORMAT"), encoding="utf-8")
    assert len(prompt_conformance_warnings([str(bad)])) == 1


def test_a_finding_carries_the_line_it_was_found_on():
    finding = prompt_structure.check(_conforming().replace("# OUTPUT SCHEMA", "# OUTPUT FORMAT"))
    assert finding is not None
    assert finding.line > 0, "a finding without a line number cannot be acted on"
