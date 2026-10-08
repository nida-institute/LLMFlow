"""The model reads the prompt; the people who maintain it read `description`.

Measured before this was written: the whole `.gpt` file went to the model, YAML header first, and
a prompt's VARIABLES list and its DATA SOURCES provenance — which step, which resource, which
options — were sections of the body, so the model read a maintainer's notes about plumbing it can
do nothing with. Now `description` is Markdown and carries that material, the frontmatter is
stripped before the call, and `# VARIABLES` leaves the grammar. Design:
`project/plans/design-prompt-description.md`; #176.
"""
from pathlib import Path

import pytest

from llmflow import prompt_structure
from llmflow.steps.llm import render_prompt

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
STARTERS = ("readers-guide.gpt", "parallel-significance.gpt")


def _write(tmp_path, text):
    prompts = tmp_path / "prompts"
    prompts.mkdir(exist_ok=True)
    (prompts / "probe.gpt").write_text(text, encoding="utf-8")
    return str(prompts)


HEADED = """---
prompt:
  requires:
    - data
  format: Markdown
  description: |
    For maintainers. ## Inputs: `data` comes from the scripture step.
---

# WHAT THIS STEP PRODUCES

A summary.

# INPUT DATA

{{data}}
"""


# --- the frontmatter never reaches the model -----------------------------------------


def test_the_rendered_prompt_has_no_frontmatter(tmp_path):
    rendered = render_prompt("probe.gpt", {"prompts_dir": _write(tmp_path, HEADED), "data": "ΑΒΓ"})
    assert rendered.lstrip().startswith("# WHAT THIS STEP PRODUCES")
    assert "requires:" not in rendered and "For maintainers" not in rendered and "---" not in rendered
    assert "ΑΒΓ" in rendered


def test_a_prompt_without_a_header_is_unchanged(tmp_path):
    rendered = render_prompt(
        "probe.gpt", {"prompts_dir": _write(tmp_path, "Summarise {{data}}.\n"), "data": "x"}
    )
    assert rendered == "Summarise x.\n"


# --- the grammar ---------------------------------------------------------------------


def test_variables_is_refused_and_says_where_it_went():
    text = HEADED.replace("# INPUT DATA", "# VARIABLES\n\n- `data`\n\n# INPUT DATA")
    finding = prompt_structure.check(text)
    assert finding is not None and "description" in finding.message


def test_the_order_no_longer_has_a_variables_position():
    assert "variables" not in {p.id for p in prompt_structure.positions()}


# --- description documents every input -----------------------------------------------


def test_a_required_input_missing_from_description_warns(tmp_path):
    from llmflow.utils.linter import prompt_description_warnings

    path = Path(_write(tmp_path, HEADED.replace("`data` comes", "it comes"))) / "probe.gpt"
    warnings = prompt_description_warnings([str(path)])
    assert len(warnings) == 1 and "data" in warnings[0] and "description" in warnings[0]


def test_a_description_naming_every_input_is_quiet(tmp_path):
    from llmflow.utils.linter import prompt_description_warnings

    path = Path(_write(tmp_path, HEADED)) / "probe.gpt"
    assert prompt_description_warnings([str(path)]) == []


# --- the starter prompts are written this way ----------------------------------------


@pytest.mark.parametrize("name", STARTERS)
def test_a_starter_prompt_conforms(name):
    assert prompt_structure.check((PROMPTS / name).read_text(encoding="utf-8")) is None


@pytest.mark.parametrize("name", STARTERS)
def test_a_starter_prompt_documents_every_input_in_description(name):
    from llmflow.utils.linter import prompt_description_warnings

    assert prompt_description_warnings([str(PROMPTS / name)]) == []


@pytest.mark.parametrize("name", STARTERS)
def test_a_starter_prompt_tells_the_model_nothing_about_provenance(name):
    """Where an input came from is the maintainer's; how to read it is the model's."""
    from llmflow.utils.linter import prompt_body

    body = prompt_body((PROMPTS / name).read_text(encoding="utf-8"))
    assert "**Source:**" not in body
    assert "type: scripture" not in body and "type: parallel-passages" not in body
