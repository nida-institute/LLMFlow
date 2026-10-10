"""`release` releases Scripture Pipelines itself, so it lives in this repository and ships nowhere.

In the package's skill templates, `sp init` put it in `~/.sp/skills/` and from there into every
project's `.claude/skills/`. Its text is about Nuitka builds, this repository's
`build-release.yml`, PyPI and `nida-institute/LLMFlow` — a workshop participant typing `/release`
in their own project was handed instructions for tagging somebody else's engine.

So the skill moves to `.claude/skills/release/` here, tracked by a `.gitignore` exception, and
the installers treat the name as retired: removed from `~/.sp/skills/` where an earlier install
left it, and never copied into a project.

The same ruling moved tags and pushes to the human (rule `commit-authority`), so the skill hands
over `git push origin "v$VERSION"` rather than running it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_SKILL = REPO_ROOT / ".claude" / "skills" / "release" / "SKILL.md"


def _package_skills_dir() -> Path:
    import llmflow

    return Path(llmflow.__file__).parent / "templates" / "sp" / "skills"


def test_release_is_not_in_the_package():
    assert not (_package_skills_dir() / "release").exists(), (
        "release is still in the package's skill templates, so sp init installs it everywhere"
    )


def test_release_lives_in_this_repository():
    assert REPO_SKILL.is_file()


def test_release_is_tracked_not_ignored():
    """`.claude/*` is git-ignored here; without the exception the skill would have no history."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", str(REPO_SKILL)],
        check=False,
    )
    assert result.returncode == 1, ".claude/skills/release/SKILL.md is git-ignored"


def test_installed_copies_of_other_skills_stay_ignored():
    """The exception is for release alone, not every skill `sp init` copies in."""
    other = REPO_ROOT / ".claude" / "skills" / "handoff" / "SKILL.md"
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", str(other)],
        check=False,
    )
    assert result.returncode == 0, ".claude/skills/handoff is no longer git-ignored"


def test_install_global_skills_removes_a_release_left_by_an_earlier_install(tmp_path: Path):
    from llmflow.cli_utils import install_global_skills

    stale = tmp_path / "skills" / "release" / "SKILL.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("---\nname: release\n---\n", encoding="utf-8")

    install_global_skills(sp_home=tmp_path)

    assert not (tmp_path / "skills" / "release").exists()
    assert (tmp_path / "skills" / "commit-ready" / "SKILL.md").is_file()


def test_a_project_never_receives_release(tmp_path: Path):
    """Even from a `~/.sp/skills/` that still holds it."""
    from llmflow.cli_utils import _install_claude_skills

    sp_home = tmp_path / "sp"
    for name in ("release", "handoff"):
        skill = sp_home / "skills" / name / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(f"---\nname: {name}\n---\n", encoding="utf-8")

    project = tmp_path / "project"
    project.mkdir()
    installed = _install_claude_skills(project, sp_home=sp_home)

    assert installed == ["handoff"]
    assert not (project / ".claude" / "skills" / "release").exists()


def _code_blocks() -> list[str]:
    return re.findall(r"```[a-z]*\n(.*?)```", REPO_SKILL.read_text(encoding="utf-8"), re.DOTALL)


@pytest.mark.parametrize("command", ["git push", "git commit", "git merge", "gh pr merge"])
def test_release_hands_pushes_to_the_human(command: str):
    """Rule `commit-authority`: a tag push is a push. Every one is in a block the human runs."""
    text = REPO_SKILL.read_text(encoding="utf-8")
    for block in _code_blocks():
        if command not in block:
            continue
        start = text.index(block)
        lead_in = text[max(0, start - 400):start]
        assert "The human runs" in lead_in, (
            f"release gives {command!r} without saying the human runs it:\n{block}"
        )


def test_release_checks_it_is_on_main():
    """A tag on `dev` publishes work that has not been through the `dev` -> `main` merge."""
    text = REPO_SKILL.read_text(encoding="utf-8")
    assert "git rev-parse --abbrev-ref HEAD" in text
    assert "main" in text
