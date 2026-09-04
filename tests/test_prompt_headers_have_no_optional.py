"""Guardrail: `optional:` is not a key of the prompt header syntax.

Every prompt parameter is required. An optional parameter needs a branch somewhere, and the
branch nobody tests is where defects live — so the keyword was withdrawn rather than kept for
the cases that seemed to need it.

Removing a key from a language means the parser refuses it. A prompt still declaring
`optional:` fails at lint time and at run time, loudly, the way the `for`/`in` migration made
the keys it replaced fail rather than quietly accepting both.

Checks that the linter refuses it, that the runtime refuses it, and that no prompt held or
shipped here declares it.

Convention: rules `pipeline-schema` and `one-design`.
"""
from pathlib import Path

import pytest

from llmflow.utils.linter import parse_prompt_header, validate_gpt_body_declares_all_vars

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Where this repository holds or ships prompts.
PROMPT_DIRS = (REPO_ROOT / "prompts", REPO_ROOT / "src" / "llmflow" / "templates")


def _is_prompt(path: Path) -> bool:
    """A `.gpt` file anywhere, or markdown sitting in a `prompts/` directory."""
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

WITH_OPTIONAL = """---
requires:
  - passage
optional: []
format: Markdown
description: A prompt still declaring the withdrawn key.
---
user: |
  Summarise {{passage}}.
"""

WITHOUT_OPTIONAL = """---
requires:
  - passage
format: Markdown
description: A prompt declaring only what it requires.
---
user: |
  Summarise {{passage}}.
"""


def test_prompts_exist():
    assert PROMPTS, f"no prompts found under {[str(d) for d in PROMPT_DIRS]}"


def test_the_linter_refuses_the_withdrawn_key(tmp_path):
    prompt = tmp_path / "declares-optional.gpt"
    prompt.write_text(WITH_OPTIONAL, encoding="utf-8")

    errors = validate_gpt_body_declares_all_vars(str(prompt))

    assert errors, "a prompt declaring `optional:` passed the linter"
    assert any("optional" in error for error in errors), errors


def test_the_linter_accepts_a_header_without_it(tmp_path):
    prompt = tmp_path / "no-optional.gpt"
    prompt.write_text(WITHOUT_OPTIONAL, encoding="utf-8")

    assert validate_gpt_body_declares_all_vars(str(prompt)) == []


def test_an_empty_list_is_refused_too(tmp_path):
    """`optional: []` is the common case here and is still the withdrawn key.

    Accepting it because it declares nothing would leave the keyword in every prompt and in
    every example anyone copies from.
    """
    prompt = tmp_path / "empty-optional.gpt"
    prompt.write_text(WITH_OPTIONAL, encoding="utf-8")

    assert validate_gpt_body_declares_all_vars(str(prompt)), "`optional: []` was accepted"


def test_the_runtime_refuses_the_withdrawn_key(tmp_path):
    """A run need not lint first, so the contract check must refuse it too."""
    from llmflow.steps.llm import render_prompt

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "declares-optional.gpt").write_text(WITH_OPTIONAL, encoding="utf-8")

    with pytest.raises(ValueError, match="optional"):
        render_prompt(
            "declares-optional.gpt",
            {"prompts_dir": str(prompts_dir), "passage": "Mark 1:1-8"},
        )


@pytest.mark.parametrize("path", PROMPTS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_prompt_here_declares_it(path):
    header = parse_prompt_header(str(path))
    assert header is None or "optional" not in header, (
        f"{path.relative_to(REPO_ROOT)} declares `optional:`, which is no longer a key of the "
        f"prompt header syntax. Every prompt parameter is required: move the name to "
        f"`requires:`, or delete it if the body does not use it."
    )
