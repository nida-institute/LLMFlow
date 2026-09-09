"""A test that calls a live model must be marked `integration`.

`pytest -m "not integration"` is the ordinary run — what a contributor types, and what the
handoff tells the next session to verify against. It must not spend money.

Two tests in `test_schema_file.py` were gated on `OPENAI_API_KEY` and named "Integration" in
their class and docstring, but carried no marker, so the ordinary run called the model six times
— once, and once more in a five-iteration loop. It surfaced only when a truncated response made
one of them fail, which is to say it surfaced by luck rather than by any check.

The signal is the API-key gate: a test that skips without a key is a test that spends money with
one. Naming a class "Integration" is not a marker, and a docstring saying so is not either.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent

#: A `skipif` naming one of these is gating on a live credential.
CREDENTIALS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")


def _decorator_source(node: ast.AST) -> str:
    return " ".join(ast.unparse(d) for d in getattr(node, "decorator_list", []))


def _gated_tests() -> list[tuple[str, str, str]]:
    """`(file, test, decorators)` for every test gated on a live credential."""
    found = []
    for path in sorted(TESTS.glob("test_*.py")):
        source = path.read_text(encoding="utf-8")
        if not any(name in source for name in CREDENTIALS):
            continue
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            decorators = _decorator_source(node)
            if any(name in decorators for name in CREDENTIALS):
                found.append((path.name, node.name, decorators))
    return found


def test_the_scan_finds_something():
    """Absent, the check below would pass by having nothing to read.

    The failure this guards against is the one `check-the-source-not-the-rendering` names: a
    derived set that quietly becomes empty, so the assertion passes while checking nothing.
    """
    assert _gated_tests(), "no credential-gated tests found — the scan is broken, not the suite"


@pytest.mark.parametrize(
    "file_name,test_name,decorators",
    _gated_tests(),
    ids=lambda value: value if isinstance(value, str) and "::" not in value else "",
)
def test_a_credential_gated_test_is_marked_integration(file_name, test_name, decorators):
    assert "integration" in decorators, (
        f"{file_name}::{test_name} skips without an API key, so with one it calls a live model "
        f"and spends money on the ordinary `pytest -m \"not integration\"` run.\n"
        f"  Add `@pytest.mark.integration`.\n"
        f"  Naming the class Integration does not deselect it; only the marker does."
    )
