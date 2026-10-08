"""A value is sent once: `{{name}}` is filled only under `# INPUT DATA`, and is a mention elsewhere.

Measured before this was written: every `{{name}}` in a prompt was replaced by the whole value,
including the ones in VARIABLES, in "Where to Find the Data", in guardrails and in checklists.
The starter's significance prompt names `{{parallel_texts}}` eight times, so about 42k tokens of
chapters reached the model eight times — roughly 340k tokens, most of a dollar per run, and
nothing failed. The prompt grammar teaches listing `{{var}}` under VARIABLES, so every prompt
written to it sent each input at least twice.

A prompt with a `# INPUT DATA` section is filled there and nowhere else; a placeholder elsewhere
renders as its bare name, which is what it was written as — a reference to the input. A prompt
with no such section is a simple prompt and is filled everywhere, as before.
"""
import pytest

from llmflow.steps.llm import render_prompt

VALUE = "ΑΒΓ-the-whole-value-ΔΕΖ"


def _render(tmp_path, body, requires=("data",), value=VALUE):
    prompts = tmp_path / "prompts"
    prompts.mkdir(exist_ok=True)
    header = "---\nrequires:\n" + "".join(f"  - {name}\n" for name in requires)
    header += "format: Markdown\ndescription: Probe.\n---\n"
    (prompts / "probe.gpt").write_text(header + body, encoding="utf-8")
    context = {"prompts_dir": str(prompts), **{name: value for name in requires}}
    return render_prompt("probe.gpt", context)


STRUCTURED = """
# VARIABLES

- `{{data}}` — the passage

# SYSTEM ROLE

Read `{{data}}` carefully.

# INPUT DATA

### The data

```
{{data}}
```

# OUTPUT SCHEMA

Every claim traces to `{{data}}`.
"""


def test_the_value_is_sent_exactly_once(tmp_path):
    assert _render(tmp_path, STRUCTURED).count(VALUE) == 1


def test_a_mention_elsewhere_renders_as_the_bare_name(tmp_path):
    rendered = _render(tmp_path, STRUCTURED)
    assert "- `data` — the passage" in rendered
    assert "Read `data` carefully." in rendered
    assert "traces to `data`." in rendered
    assert "{{" not in rendered


def test_the_value_lands_under_input_data(tmp_path):
    rendered = _render(tmp_path, STRUCTURED)
    assert rendered.index("# INPUT DATA") < rendered.index(VALUE) < rendered.index("# OUTPUT SCHEMA")


def test_a_heading_inside_a_code_fence_does_not_end_the_section(tmp_path):
    body = "# INPUT DATA\n\n```\n# not a heading\n{{data}}\n```\n\n# OUTPUT SCHEMA\n\nok\n"
    assert _render(tmp_path, body).count(VALUE) == 1


def test_a_subheading_stays_inside_the_section(tmp_path):
    body = "# INPUT DATA\n\n## Part one\n\n{{data}}\n\n## Part two\n\n{{other}}\n"
    rendered = _render(tmp_path, body, requires=("data", "other"))
    assert rendered.count(VALUE) == 2


def test_a_prompt_without_input_data_is_filled_everywhere(tmp_path):
    """A simple prompt, as before: there is no section to confine the value to."""
    rendered = _render(tmp_path, "Summarise {{data}}.\n")
    assert f"Summarise {VALUE}." in rendered


def test_a_declared_input_never_given_under_input_data_is_refused(tmp_path):
    """Otherwise the model would read about an input it is never shown."""
    body = "# SYSTEM ROLE\n\nUse `{{data}}`.\n\n# INPUT DATA\n\nnothing here\n"
    with pytest.raises(ValueError, match="INPUT DATA"):
        _render(tmp_path, body)


@pytest.mark.parametrize(
    "prompt,inputs",
    [
        ("readers-guide.gpt", ("reference", "testament", "original", "english")),
        ("parallel-significance.gpt", ("reference", "english", "parallels", "parallel_texts")),
    ],
)
def test_the_starter_prompts_send_each_input_once(prompt, inputs):
    from pathlib import Path

    prompts = Path(__file__).resolve().parent.parent / "prompts"
    for name in inputs:
        context = {"prompts_dir": str(prompts), **{n: f"<{n}-VALUE>" for n in inputs}}
        rendered = render_prompt(prompt, context)
        assert rendered.count(f"<{name}-VALUE>") == 1, name
