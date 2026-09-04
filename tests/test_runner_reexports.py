"""`llmflow.runner`'s import surface is declared in `__all__` and every name in it resolves.

Most of what callers import from `llmflow.runner` is defined elsewhere and re-exported, because
this module was their home before they moved into their own modules. An unused-import check reads
those imports as dead and offers to delete them, and deleting one breaks every caller at import
time rather than at the call — twice while lint was being fixed, once for `save_content_to_file`
and once for `_MISSING`.

The subject comes from the source: every `from llmflow.runner import` in the tree, found by
parsing, not from a list kept here that could disagree with both.
"""

import ast
from pathlib import Path

import llmflow.runner as runner

REPO = Path(__file__).resolve().parent.parent
SEARCHED = ("src", "tests")


def imported_names() -> dict[str, set[str]]:
    """Every name imported from `llmflow.runner`, mapped to the files importing it."""
    found: dict[str, set[str]] = {}
    for base in SEARCHED:
        for path in (REPO / base).rglob("*.py"):
            if path.name == Path(__file__).name:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover - a broken file is another test's business
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "llmflow.runner":
                    for alias in node.names:
                        found.setdefault(alias.name, set()).add(str(path.relative_to(REPO)))
    return found


def test_the_module_declares_a_surface():
    """Without `__all__` there is nothing to check the imports against."""
    assert isinstance(getattr(runner, "__all__", None), list)
    assert runner.__all__, "__all__ is empty, so every check below would pass by having nothing"


def test_something_imports_from_the_runner():
    """Guards the guard: an empty search would make the next test vacuous."""
    assert imported_names(), f"nothing imports from llmflow.runner under {SEARCHED}"


def test_every_imported_name_is_declared():
    """A name callers import must be in `__all__`, or a lint sweep may delete it unnoticed."""
    undeclared = {
        name: sorted(files)
        for name, files in imported_names().items()
        if name != "*" and name not in runner.__all__
    }
    assert not undeclared, (
        "imported from llmflow.runner but missing from its __all__: "
        f"{undeclared}. Add the name to __all__ so an unused-import check keeps it."
    )


def test_every_declared_name_resolves():
    """`__all__` naming something absent would break `import *` and mislead the check above."""
    missing = [name for name in runner.__all__ if not hasattr(runner, name)]
    assert not missing, f"named in llmflow.runner.__all__ but not present: {missing}"
