"""Guardrail: the engine parses XML with `lxml`, never with `xml.etree.ElementTree`.

ElementTree supports only a subset of XPath, handles namespaces awkwardly, and cannot run
XSLT. This engine's XML work is XPath- and XSLT-shaped, so a module that starts with
ElementTree is rewritten as soon as it needs a real XPath expression.

Walks the AST of every module under `src/llmflow/` and fails on any import of `xml.etree`,
in either `import` or `from ... import` form. Reading the source rather than importing it
keeps the check independent of whether a module has an optional dependency installed.

Convention: rule `lxml-for-xml`.
"""
import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent.parent / "src" / "llmflow"

MODULES = sorted(PACKAGE.rglob("*.py"))

#: The module whose XPath support is the reason for this rule.
FORBIDDEN_ROOT = "xml.etree"


def _forbidden_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as error:  # pragma: no cover - a broken file is another test's job
        pytest.fail(f"{path} could not be parsed: {error}")

    offences = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == FORBIDDEN_ROOT or alias.name.startswith(FORBIDDEN_ROOT + "."):
                    offences.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == FORBIDDEN_ROOT or module.startswith(FORBIDDEN_ROOT + "."):
                names = ", ".join(alias.name for alias in node.names)
                offences.append(f"line {node.lineno}: from {module} import {names}")
    return offences


def test_modules_exist():
    assert MODULES, f"no modules found under {PACKAGE}"


@pytest.mark.parametrize("path", MODULES, ids=lambda p: str(p.relative_to(PACKAGE)))
def test_module_does_not_import_elementtree(path):
    offences = _forbidden_imports(path)
    assert not offences, (
        f"{path.relative_to(PACKAGE)} imports {FORBIDDEN_ROOT}, against rule `lxml-for-xml`:\n"
        + "\n".join(f"   {o}" for o in offences)
        + "\n   Use `from lxml import etree`. ElementTree's XPath is a subset, its namespace "
        "handling is awkward, and it cannot run XSLT — so this import is rewritten as soon as "
        "the module needs a real XPath expression."
    )
