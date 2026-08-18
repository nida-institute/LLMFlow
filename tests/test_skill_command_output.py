"""Skill commands must never produce a completely empty result (#204).

A shell command that exits 0 with no stdout and no stderr yields an empty content
block. That is the suspected source of the bodyless HTTP 400 a new contributor hit
when running /load-context on a fresh clone.

The failure is invisible on the author's machine: `git status --short` is only empty
when a checkout has no local changes, which is exactly a new clone and never a
working machine mid-task.

See project/plans/design-onboarding-fresh-clone.md §2.1.
"""

import re
import subprocess
from pathlib import Path

import pytest


def get_skills_templates_dir() -> Path:
    import llmflow

    return Path(llmflow.__file__).parent / "templates" / "sp-skills"


def extract_shell_commands(skill_md: Path) -> list[str]:
    """Return single-line shell commands from ```bash fences in a SKILL.md.

    Deliberately conservative: skips continuations, comments, blank lines, and any
    line containing a shell metacharacter that would need a real parser. The point
    is to catch plain informational commands, which are the ones that can silently
    return nothing.
    """
    text = skill_md.read_text(encoding="utf-8")
    commands: list[str] = []
    for block in re.findall(r"```bash\n(.*?)```", text, re.DOTALL):
        for raw in block.splitlines():
            line = raw.split("#")[0].strip()
            if not line:
                continue
            if any(ch in line for ch in "|<>$&\\") or line.endswith(("\\", "{", "(")):
                continue
            commands.append(line)
    return commands


@pytest.fixture
def clean_clone(tmp_path: Path) -> Path:
    """A git repo in the state a new contributor's fresh clone is in: no local changes."""
    repo = tmp_path / "clone"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "README.md").write_text("placeholder\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "init"],
        cwd=repo,
        check=True,
    )
    return repo


def test_load_context_commands_never_yield_an_empty_result(clean_clone: Path):
    """No command in load-context may exit 0 with neither stdout nor stderr.

    An empty result becomes an empty content block, which the API rejects with a
    bodyless 400 — an error that names nothing and points at nothing.
    """
    skill = get_skills_templates_dir() / "load-context" / "SKILL.md"
    commands = extract_shell_commands(skill)
    assert commands, f"No shell commands extracted from {skill} — the parser or the skill changed"

    silent: list[str] = []
    for cmd in commands:
        proc = subprocess.run(
            cmd, shell=True, cwd=clean_clone, capture_output=True, text=True
        )
        if proc.returncode == 0 and not proc.stdout.strip() and not proc.stderr.strip():
            silent.append(cmd)

    assert not silent, (
        "These commands succeed with no output at all on a clean clone, producing an "
        "empty content block:\n"
        + "\n".join(f"  {c}" for c in silent)
        + "\n\nGuard each one so it always says something, e.g. "
        '`git status --short || true` with a fallback message.'
    )
