"""What a project is told it may reach this engine through.

One surface: the `sp` command line, and the pipeline language it reads. The Python API is
real and supported, and it is the engine's own business — a project that builds against it
has taken on a second contract nobody offered it, and an internal helper reached through an
`llmflow.*` submodule is not a contract at all.

A guard rather than a sentence in a document, because the shipped context is regenerated:
`sp init --update` rewrites every `generated` file from these templates, so a rule that lives
only in prose is one the next regeneration can quietly undo, in every project at once and
with nothing reporting it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "src" / "llmflow" / "templates"

#: Everything a session in a project reads. The project's own AI context, the pipeline
#: language reference beside it, and the disciplines and skills installed into `~/.sp` —
#: which are project-facing however the store is arranged.
SHIPPED_DIRECTORIES = (
    TEMPLATES / "project" / "docs",
    TEMPLATES / "sp" / "disciplines",
    TEMPLATES / "sp" / "skills",
    TEMPLATES / "sp" / "versification",
)

#: Names that only mean something to a program importing the engine. `load_pipeline` and
#: `api_catalog` are the public API's own entry points; `PIPELINE_SCHEMA` is the declaration
#: it publishes; `import llmflow` is how any of them is reached.
PYTHON_API_NAMES = (
    "load_pipeline",
    "api_catalog",
    "PIPELINE_SCHEMA",
    "import llmflow",
    "from llmflow",
    # The dotted path in a `function:` step counts too. It is pipeline YAML rather than an
    # import, but it names our Python all the same, and a project that copies it has taken a
    # dependency on a submodule that carries no compatibility promise. The language has a
    # high-level construct for the work these examples were doing; where it does not, that is
    # a gap to report rather than a reason to reach past the surface.
    "llmflow.utils",
    "llmflow.steps",
    "llmflow.modules",
)

#: `docs/index.json` maps the engine's internals. It answers a question only work on the
#: engine is entitled to ask, and it is not shipped — this is the check that it stays that way.
INTERNALS_MAP = "index.json"


def shipped_context_files() -> list[Path]:
    return sorted(
        path
        for directory in SHIPPED_DIRECTORIES
        if directory.is_dir()
        for path in directory.rglob("*.md")
    )


def test_there_are_shipped_context_files_to_check():
    """A guard that can quietly reduce to nothing is worse than an absent one."""
    assert shipped_context_files()


@pytest.mark.parametrize("path", shipped_context_files(), ids=lambda p: p.name)
def test_a_project_is_told_about_the_command_line_and_nothing_else(path: Path):
    text = path.read_text(encoding="utf-8")
    named = [name for name in PYTHON_API_NAMES if name in text]
    assert not named, (
        f"{path.relative_to(REPO_ROOT)} tells a project about the Python API "
        f"({', '.join(named)}). A project reaches this engine through the `sp` command line "
        "and the pipeline language it reads. Describe the command, not the call."
    )


@pytest.mark.parametrize("path", shipped_context_files(), ids=lambda p: p.name)
def test_the_internals_map_is_not_shipped(path: Path):
    assert INTERNALS_MAP not in path.read_text(encoding="utf-8"), (
        f"{path.relative_to(REPO_ROOT)} names {INTERNALS_MAP}, which maps the engine's own "
        "modules and functions. It is engine-only; a project has no use for it and no "
        "compatibility promise about anything in it."
    )
