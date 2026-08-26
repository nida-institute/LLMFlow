"""Guardrail: the GUI files `build_gui.py` copies must already be identical to their targets.

`build_gui.py` copies `gui/backend/server.py` and `executor.py` over `src/llmflow/gui/`, and CI
runs it before the tests. Both sides are tracked, and the suite imports both — some tests use
`gui.backend.server`, others `llmflow.gui.server`. So a change made to one copy only passes
locally and then fails in CI, where the copy erases it: a missing `find_pipelines_dir` turned
into a collection error that stopped the whole suite from running.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

#: (copy source, copy target), as `build_gui.py` pairs them.
COPIED = (
    ("gui/backend/server.py", "src/llmflow/gui/server.py"),
    ("gui/backend/executor.py", "src/llmflow/gui/executor.py"),
)


@pytest.mark.parametrize("source, target", COPIED, ids=lambda p: Path(p).name)
def test_both_copies_exist(source: str, target: str):
    assert (REPO_ROOT / source).is_file()
    assert (REPO_ROOT / target).is_file()


@pytest.mark.parametrize("source, target", COPIED, ids=lambda p: Path(p).name)
def test_the_copy_source_matches_its_target(source: str, target: str):
    source_text = (REPO_ROOT / source).read_text(encoding="utf-8")
    target_text = (REPO_ROOT / target).read_text(encoding="utf-8")
    assert source_text == target_text, (
        f"{source} and {target} have diverged. `build_gui.py` copies the first over the second, "
        f"so whatever is only in {target} is erased in CI. Make the change in both, or make "
        f"them one file."
    )


def test_build_gui_copies_exactly_these_files():
    """If `build_gui.py` learns to copy another file, this list has to learn it too."""
    script = (REPO_ROOT / "build_gui.py").read_text(encoding="utf-8")
    for source, _ in COPIED:
        assert Path(source).name in script, f"{source} is no longer copied by build_gui.py"
    copied_names = {Path(source).name for source, _ in COPIED}
    mentioned = {
        line.split('"')[1].split("/")[-1]
        for line in script.splitlines()
        if '_src = script_dir /' in line and '"' in line
    }
    python_copies = {name for name in mentioned if name.endswith(".py")}
    assert python_copies <= copied_names, (
        f"build_gui.py copies Python files this guard does not check: "
        f"{sorted(python_copies - copied_names)}"
    )
