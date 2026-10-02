"""Guardrail: a prompt header is YAML frontmatter fenced by `---` on the first line, and nothing else.

The `<!-- ... -->` comment header is withdrawn. It was parsed as a fallback, but the section
grammar binds only a prompt whose first line is `---`, so a prompt using the comment form was
never structure-checked. Removing a form from the language means the parser refuses it, at lint
time and at run time, rather than quietly reading the prompt as having no header.

Convention: rules `pipeline-schema` and `one-design`.
"""
import json
from pathlib import Path

import pytest

from llmflow import load_pipeline
from llmflow.utils.linter import parse_prompt_header

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Where this repository holds or ships prompts.
PROMPT_DIRS = (REPO_ROOT / "prompts", REPO_ROOT / "src" / "llmflow" / "templates")

PROMPTS = sorted(
    path
    for directory in PROMPT_DIRS
    if directory.is_dir()
    for path in directory.rglob("*.gpt")
    if path.is_file()
)

COMMENT_HEADER = """<!--
prompt:
  requires:
    - passage
-->
Summarise {{passage}}.
"""

FRONTMATTER = """---
prompt:
  requires:
    - passage
---
Summarise {{passage}}.
"""

#: A `---` pair that is not on the first line is a pair of horizontal rules, not a header.
RULES_NOT_HEADER = """Summarise the passage.

---

requires:
  - passage

---
"""


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    """A one-step llm pipeline over a prompt with the given text; returns the loaded Pipeline."""
    monkeypatch.chdir(tmp_path)

    def _build(prompt_text):
        (tmp_path / "prompts").mkdir(exist_ok=True)
        (tmp_path / "prompts" / "p.gpt").write_text(prompt_text, encoding="utf-8")
        cfg = {
            "name": "p",
            "variables": {"passage": "MRK 1:1"},
            "steps": [{
                "name": "s", "type": "llm",
                "prompt": {"file": "prompts/p.gpt", "inputs": {"passage": "${passage}"}},
                "output": "r",
            }],
        }
        path = tmp_path / "p.yaml"
        path.write_text(json.dumps(cfg), encoding="utf-8")
        return load_pipeline(str(path))

    return _build


def test_lint_refuses_a_comment_header(pipeline):
    result = pipeline(COMMENT_HEADER).lint()

    assert not result.valid, "a prompt with a `<!-- -->` header passed lint"
    assert any("<!--" in error and "---" in error for error in result.errors), result.errors


def test_lint_accepts_frontmatter(pipeline):
    result = pipeline(FRONTMATTER).lint()

    assert result.valid, result.errors


def test_the_runtime_refuses_a_comment_header(tmp_path):
    """A run need not lint first, so the contract check must refuse it too."""
    from llmflow.steps.llm import render_prompt

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "p.gpt").write_text(COMMENT_HEADER, encoding="utf-8")

    with pytest.raises(ValueError, match="<!--"):
        render_prompt("p.gpt", {"prompts_dir": str(prompts_dir), "passage": "MRK 1:1"})


def test_a_fence_below_the_first_line_is_not_a_header(tmp_path):
    prompt = tmp_path / "rules.gpt"
    prompt.write_text(RULES_NOT_HEADER, encoding="utf-8")

    assert parse_prompt_header(str(prompt)) is None


def test_prompts_exist():
    assert PROMPTS, f"no prompts found under {[str(d) for d in PROMPT_DIRS]}"


@pytest.mark.parametrize("path", PROMPTS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_no_prompt_here_uses_a_comment_header(path):
    assert not path.read_text(encoding="utf-8").lstrip("\ufeff").lstrip().startswith("<!--"), (
        f"{path.relative_to(REPO_ROOT)} opens with a `<!-- -->` header. A prompt header is YAML "
        f"frontmatter fenced by `---` on the first line."
    )
