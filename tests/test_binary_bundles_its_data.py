"""Guardrail: the standalone binary bundles every data file the wheel force-includes.

`pyproject.toml` lists what the wheel carries; `build.yml` lists what Nuitka bundles. They are
two hand-maintained lists that must agree, and when they drifted the released binary shipped
without `data/file-catalog.yaml` — so `sp init` and `sp doctor` crashed with FileNotFoundError
on a file the binary was supposed to contain (#216). The wheel was unaffected, which is why
tests and PyPI looked fine.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import tomllib

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "build.yml"
PYPROJECT = REPO_ROOT / "pyproject.toml"

#: Force-included paths the binary legitimately does not need. Empty on purpose: an exemption
#: here is a claim that a code path can never run in the binary, which needs evidence.
NOT_NEEDED_IN_BINARY: frozenset = frozenset()


def force_included() -> dict:
    """`{source path: destination}` from pyproject's wheel force-include."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return (
        data.get("tool", {})
        .get("hatch", {})
        .get("build", {})
        .get("targets", {})
        .get("wheel", {})
        .get("force-include", {})
    )


def nuitka_commands() -> list:
    """Each Nuitka invocation in the workflow, as one whitespace-collapsed string."""
    text = WORKFLOW.read_text(encoding="utf-8")
    # Line continuations first, so the Unix multi-line form becomes one string like Windows'.
    joined = re.sub(r"\\\s*\n\s*", " ", text)
    return [
        re.sub(r"\s+", " ", line.strip())
        for line in joined.splitlines()
        if "nuitka" in line and "--include-package=llmflow" in line
    ]


def test_the_workflow_has_a_nuitka_invocation_for_each_platform():
    """Absent, every check below would pass by having nothing to read."""
    commands = nuitka_commands()
    assert len(commands) >= 2, f"expected Unix and Windows builds, found {len(commands)}"


def test_pyproject_force_includes_something():
    assert force_included(), "no force-include table; this guard would be vacuous"


@pytest.mark.parametrize("source", sorted(force_included()))
def test_every_force_included_path_is_bundled_in_the_binary(source: str):
    if source in NOT_NEEDED_IN_BINARY:
        pytest.skip(f"{source} is declared unnecessary in the binary")

    destination = force_included()[source]
    for command in nuitka_commands():
        assert f"{source}={destination}" in command, (
            f"pyproject force-includes {source!r} into the wheel, but this Nuitka command does "
            f"not bundle it. The binary would raise FileNotFoundError on it at runtime while "
            f"the wheel works — the shape of #216.\n  command: {command[:160]}…"
        )


def test_the_smoke_test_exercises_a_code_path_that_reads_the_catalog():
    """`--version` and `lint` do not touch the catalog, which is why #216 shipped green."""
    text = WORKFLOW.read_text(encoding="utf-8")
    smoke = "\n".join(
        line for line in text.splitlines() if "$BIN" in line or "sp-windows.exe" in line
    )
    assert "doctor" in smoke, (
        "no smoke-test step runs `doctor`, so a missing bundled data file passes CI. "
        "#216 shipped because the smoke test only ran --version, lint and run --dry-run."
    )


# --- the direction the guard above cannot see ----------------------------------------

#: `data/` files deliberately not shipped, each with the reason. An entry here is a claim
#: that no installed copy ever reads the file — which is checkable, so state it.
NOT_SHIPPED = {
    "helm-sync.yaml": "records hashes for syncing the Helm disciplines; a development tool",
}


def test_every_data_file_the_package_could_read_is_shipped():
    """The guard above walks pyproject to build.yml, so a file in *neither* is invisible to it.

    That is how `data/book-names.json` reached a release candidate bundled nowhere: the wheel
    lists files one by one, the module read it by name, and nothing compared the two lists. An
    installed copy would have raised FileNotFoundError on every reference it parsed.
    """
    shipped = {Path(src).name for src in force_included()}
    on_disk = {
        path.name
        for path in (REPO_ROOT / "data").iterdir()
        if path.is_file() and path.suffix in (".json", ".yaml")
    }
    missing = sorted(on_disk - shipped - set(NOT_SHIPPED))
    assert not missing, (
        f"{missing} sit in data/ and ship nowhere. Add them to pyproject's force-include and to "
        f"both Nuitka commands, or name them in NOT_SHIPPED with the reason."
    )


def test_nothing_is_exempted_that_is_actually_shipped():
    """An exemption that stops being true is worse than none: it reads as a decision."""
    shipped = {Path(src).name for src in force_included()}
    contradicted = sorted(set(NOT_SHIPPED) & shipped)
    assert not contradicted, f"{contradicted} are exempted and also shipped"
