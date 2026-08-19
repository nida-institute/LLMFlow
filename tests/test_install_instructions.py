"""Install instructions must name the package we actually publish.

The repository published to PyPI as `scripture-pipelines`, but eleven places across the
docs, the GUI launcher and three test skip messages still told users to run
`pip install llmflow`. That name is **not registered on PyPI** — it returns 404 — so
anyone following the README got nothing, and an unclaimed name is one someone else can
register.

Several of them said `pip install llmflow[gui]`, naming an extra that does not exist
either: `pyproject.toml` has no `[project.optional-dependencies]` section at all, and
Flask is a hard dependency (`pyproject.toml:41-43`). The extra was never needed.

`CLAUDE.md` already lists this exact trap — *"verify project exists at
https://pypi.org/project/llmflow/ first"* — and it shipped regardless. A note in a
pitfalls list does not fail a build; this test does.

`CHANGELOG.md` is excluded on purpose: its entries describe what was true at the time of
a release and are not instructions to follow today.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "node_modules", "dist", "build", "nuitka_dist", "__pycache__", ".venv"}
# CHANGELOG.md records what was true at each release; its entries are history, not
# instructions. This file quotes the wrong commands in order to describe them.
SKIP_FILES = {"CHANGELOG.md", "test_install_instructions.py"}

# `pip install <name>` where <name> is not a path, a flag, or a local install.
_INSTALL = re.compile(r"pip install\s+(?:-U\s+|--upgrade\s+)?([A-Za-z][A-Za-z0-9._-]*)(\[[^\]]*\])?")


def _package_name() -> str:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["name"]


def _declared_extras() -> set[str]:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return set(data["project"].get("optional-dependencies", {}))


def _scanned_files() -> list[Path]:
    found: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in (".md", ".py"):
            continue
        if path.name in SKIP_FILES:
            continue
        if SKIP_DIRS & set(path.relative_to(REPO_ROOT).parts):
            continue
        found.append(path)
    return found


def _install_mentions() -> list[tuple[Path, int, str, str | None]]:
    """Every `pip install X` in the repo, as (file, line number, package, extra)."""
    mentions: list[tuple[Path, int, str, str | None]] = []
    for path in _scanned_files():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:  # pragma: no cover - binary files are not scanned
            continue
        for number, line in enumerate(lines, start=1):
            for match in _INSTALL.finditer(line):
                mentions.append((path, number, match.group(1), match.group(2)))
    return mentions


def test_the_published_package_name_is_what_we_think_it_is():
    """A guard on the guard: if the name changes, the assertions below must follow it."""
    assert _package_name() == "scripture-pipelines"


def test_no_document_tells_users_to_install_a_package_we_do_not_publish():
    """`pip install llmflow` installs nothing — the name is not registered on PyPI."""
    package = _package_name()
    ours = {package, package.replace("-", "_")}
    # Third-party packages the docs legitimately tell users to install.
    third_party_prefixes = ("llm", "flask", "pytest", "hatch", "ruff", "nuitka", "build", "twine")

    wrong: list[str] = []
    for path, number, name, _extra in _install_mentions():
        if name in ours:
            continue
        # `llm`, `llm-anthropic`, `llm-gemini`, `llm-ollama` are real, separate packages.
        if name.startswith(third_party_prefixes) and name not in ("llmflow",):
            continue
        if name == "llmflow":
            wrong.append(f"{path.relative_to(REPO_ROOT)}:{number} says `pip install {name}`")

    assert not wrong, (
        "these tell users to install a package that is not on PyPI:\n  " + "\n  ".join(wrong)
    )


def test_no_document_references_an_extra_we_do_not_declare():
    """`scripture-pipelines[gui]` would fail too — there are no extras.

    Flask is a hard dependency, so the GUI needs no extra at all.
    """
    declared = _declared_extras()
    package = _package_name()
    ours = {package, package.replace("-", "_"), "llmflow"}

    wrong: list[str] = []
    for path, number, name, extra in _install_mentions():
        if name not in ours or not extra:
            continue
        for requested in (e.strip() for e in extra.strip("[]").split(",")):
            if requested and requested not in declared:
                wrong.append(
                    f"{path.relative_to(REPO_ROOT)}:{number} requests extra [{requested}], "
                    f"which pyproject does not declare"
                )

    assert not wrong, "\n  " + "\n  ".join(wrong)


@pytest.mark.parametrize("doc", ["README.md", "INSTALL.md"])
def test_the_front_door_docs_name_the_real_package(doc: str):
    """The two files a new user actually opens must get this right."""
    text = (REPO_ROOT / doc).read_text(encoding="utf-8")
    assert f"pip install {_package_name()}" in text, (
        f"{doc} never shows the correct install command"
    )
