"""Guardrail: a placeholder is expanded exactly once, and nothing else is expanded at all.

Design: `project/plans/design-expand-once-and-only-once.md`.

Two failures, both measured before this was written:

**Expanded more than once.** `render_prompt` substituted context values into the template and
then ran `resolve()` over the result, so a value carrying braces was expanded a second time
against the pipeline context. Fetched content became a template — injection-shaped, and silent,
because the output reads as a well-rendered prompt.

**Expanded zero times.** Names beginning with `#`, `/` or `%` were skipped by the variable
extractor — Handlebars convention in an engine with no conditionals — so they escaped the
declaration check and nothing substituted them. `{{#directive}}` reached the model verbatim.

The cases below reproduce both. A test that renders a clean prompt successfully would have
passed against the defective code, because the defect rendered successfully.

Convention: rules `prompts-in-sync` and `use-the-pipeline-language`.
"""
from __future__ import annotations

import pytest

from llmflow.steps.llm import render_prompt

HEADER = """---
requires:
{requires}
format: Markdown
description: Probe for the expansion invariant.
---
user: |
  {body}
"""


def _prompt(tmp_path, body: str, requires: list[str]) -> dict:
    """Write a prompt and return the context keys needed to render it."""
    prompts = tmp_path / "prompts"
    prompts.mkdir(exist_ok=True)
    text = HEADER.format(
        requires="\n".join(f"  - {name}" for name in requires) or "  []",
        body=body,
    )
    (prompts / "probe.gpt").write_text(text, encoding="utf-8")
    return {"prompts_dir": str(prompts)}


def test_a_declared_placeholder_is_expanded(tmp_path):
    """The baseline: the mechanism still works."""
    context = _prompt(tmp_path, "Analyse {{passage_text}}.", ["passage_text"])
    context["passage_text"] = "In the beginning"

    rendered = render_prompt("probe.gpt", context)

    assert "In the beginning" in rendered
    assert "{{passage_text}}" not in rendered


def test_a_value_containing_single_braces_is_not_expanded_again(tmp_path):
    """Data is data. `{secret}` inside a value is the data's own characters."""
    context = _prompt(tmp_path, "Analyse {{passage_text}}.", ["passage_text"])
    context["passage_text"] = "the scroll said {secret}"
    context["secret"] = "SUBSTITUTED-FROM-CONTEXT"

    rendered = render_prompt("probe.gpt", context)

    assert "SUBSTITUTED-FROM-CONTEXT" not in rendered, (
        "a substituted value was expanded a second time — data was treated as template"
    )
    assert "{secret}" in rendered


def test_a_value_containing_a_dollar_reference_is_not_expanded_again(tmp_path):
    """The `${...}` form is the one `resolve()` was reaching through the data."""
    context = _prompt(tmp_path, "Analyse {{passage_text}}.", ["passage_text"])
    context["passage_text"] = "the scroll said ${secret}"
    context["secret"] = "SUBSTITUTED-FROM-CONTEXT"

    rendered = render_prompt("probe.gpt", context)

    assert "SUBSTITUTED-FROM-CONTEXT" not in rendered
    assert "${secret}" in rendered


def test_a_value_containing_a_placeholder_is_left_alone(tmp_path):
    """`once` rather than `until stable` — the case a naive implementation gets wrong.

    A value arriving with `{{name}}` in it must reach the model unexpanded, and must not be
    mistaken for an unfilled placeholder and refused: the template's own placeholder was
    filled exactly once, which is what the invariant asks.
    """
    context = _prompt(tmp_path, "Analyse {{passage_text}}.", ["passage_text"])
    context["passage_text"] = "the scroll said {{secret}}"
    context["secret"] = "SUBSTITUTED-FROM-CONTEXT"

    rendered = render_prompt("probe.gpt", context)

    assert "SUBSTITUTED-FROM-CONTEXT" not in rendered
    assert "{{secret}}" in rendered


def test_a_handlebars_style_name_is_refused_rather_than_ignored(tmp_path):
    """`{{#directive}}` is not syntax this engine has, so it is an undeclared variable."""
    context = _prompt(tmp_path, "Analyse {{passage_text}} {{#directive}}.", ["passage_text"])
    context["passage_text"] = "x"

    with pytest.raises(ValueError, match="#directive|not declared"):
        render_prompt("probe.gpt", context)


@pytest.mark.parametrize("prefix", ["#", "/", "%"])
def test_no_prefix_is_exempt_from_the_declaration_check(tmp_path, prefix):
    """All three skipped forms, so the two disagreeing skip-lists cannot come back."""
    context = _prompt(tmp_path, f"Analyse {{{{{prefix}thing}}}}.", [])

    with pytest.raises(ValueError, match="not declared"):
        render_prompt("probe.gpt", context)


def test_no_placeholder_survives_rendering(tmp_path):
    """The backstop: whatever the static checks miss, nothing unfilled reaches the model."""
    context = _prompt(tmp_path, "Analyse {{passage_text}}.", ["passage_text"])
    context["passage_text"] = "In the beginning"

    rendered = render_prompt("probe.gpt", context)

    body = rendered.split("---", 2)[-1]
    assert "{{" not in body, f"an unexpanded placeholder reached the model: {body!r}"
