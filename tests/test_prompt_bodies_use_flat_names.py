"""Guardrail: a prompt body takes flat `{{name}}` placeholders, never dotted ones.

No substitution can fill `{{a.b}}`. A placeholder is filled by matching its name against a
literal key of the pipeline context, and a dotted name is not such a key — the context holds
`scene`, not `scene.title`. `resolve()` does not reach it either: it substitutes `${var}` and
`{var}`, and leaves a `{{...}}` placeholder untouched, inner braces included.

Without the checks below nothing refuses it: declaring the name satisfies the declaration
check, declaring it optional satisfies the required-variables check, and the placeholder is
then sent to the model unfilled.

Checks the linter rejects one, the runtime rejects one, and no prompt shipped or held in this
repository contains one.

Convention: rules `prompts-in-sync` and `use-the-pipeline-language`.
"""
from pathlib import Path

import pytest

from llmflow.utils.linter import dotted_template_names, validate_gpt_body_declares_all_vars

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Where this repository holds or ships prompts.
PROMPT_DIRS = (REPO_ROOT / "prompts", REPO_ROOT / "src" / "llmflow" / "templates")


def _is_prompt(path: Path) -> bool:
    """Whether *path* is a prompt rather than prose about prompts.

    Location decides it: a `.gpt` file anywhere, or a markdown file sitting in a `prompts/`
    directory. Reading the frontmatter cannot decide it — documentation that shows an example
    contract parses as though it had one, which is how the language reference came to be
    treated as a prompt.

    Prose must stay free to name the form it warns against, and the reference now does.
    """
    if path.suffix == ".gpt":
        return True
    return path.suffix == ".md" and path.parent.name == "prompts"


PROMPTS = sorted(
    path
    for directory in PROMPT_DIRS
    if directory.is_dir()
    for path in list(directory.rglob("*.gpt")) + list(directory.rglob("*.md"))
    if path.is_file() and _is_prompt(path)
)

DOTTED_PROMPT = """---
requires:
  - scene
optional: []
format: Markdown
description: A prompt whose body names a nested field.
---
user: |
  Summarise {{scene.title}} in one sentence.
"""

FLAT_PROMPT = """---
requires:
  - scene_title
optional: []
format: Markdown
description: A prompt whose body names a flat value.
---
user: |
  Summarise {{scene_title}} in one sentence.
"""


def test_dotted_names_are_recognised():
    assert dotted_template_names({"scene.title", "passage", "a.b.c"}) == ["a.b.c", "scene.title"]
    assert dotted_template_names({"passage", "scene_title"}) == []


def test_the_linter_rejects_a_dotted_name(tmp_path):
    prompt = tmp_path / "dotted.gpt"
    prompt.write_text(DOTTED_PROMPT, encoding="utf-8")

    errors = validate_gpt_body_declares_all_vars(str(prompt))

    assert errors, "a dotted name passed the linter"
    assert any("dotted name" in error for error in errors), errors
    assert any("scene.title" in error for error in errors), errors


def test_the_linter_accepts_a_flat_name(tmp_path):
    prompt = tmp_path / "flat.gpt"
    prompt.write_text(FLAT_PROMPT, encoding="utf-8")

    assert validate_gpt_body_declares_all_vars(str(prompt)) == []


def test_a_dotted_name_is_not_reported_as_merely_undeclared(tmp_path):
    """Declaring it must not silence the error — declaring it is what used to hide the defect."""
    prompt = tmp_path / "declared-dotted.gpt"
    prompt.write_text(DOTTED_PROMPT.replace("  - scene\n", "  - scene\n  - scene.title\n"),
                      encoding="utf-8")

    errors = validate_gpt_body_declares_all_vars(str(prompt))

    assert errors, "declaring a dotted name silenced the error"
    assert all("not declared" not in error for error in errors), errors


def test_the_runtime_rejects_a_dotted_name(tmp_path):
    """`sp run` does not have to lint first, so the contract check must catch it too."""
    from llmflow.steps.llm import render_prompt

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "dotted.gpt").write_text(DOTTED_PROMPT, encoding="utf-8")

    with pytest.raises(ValueError, match="[Dd]otted"):
        render_prompt("dotted.gpt", {"prompts_dir": str(prompts_dir), "scene": {"title": "x"}})


def test_prompts_exist():
    assert PROMPTS, f"no prompts with placeholders found under {[str(d) for d in PROMPT_DIRS]}"


@pytest.mark.parametrize("path", PROMPTS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_prompt_here_uses_a_dotted_name(path):
    from llmflow.utils.linter import extract_template_variables

    dotted = dotted_template_names(extract_template_variables(path.read_text(encoding="utf-8")))
    assert not dotted, (
        f"{path.relative_to(REPO_ROOT)} names {dotted} in a placeholder. Nothing substitutes a "
        f"dotted name, so the placeholder would reach the model verbatim."
    )
