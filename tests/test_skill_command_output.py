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

    return Path(llmflow.__file__).parent / "templates" / "sp" / "skills"


# Commands that change state rather than report it. Producing no output is correct
# for these, so they are not candidates for the empty-result bug.
ACTION_COMMANDS = frozenset(
    {
        "sleep",
        "rm",
        "mkdir",
        "rmdir",
        "cp",
        "mv",
        "touch",
        "chmod",
        "chown",
        "ln",
        "export",
        "cd",
        "set",
        "unset",
        "kill",
        "open",
        "pip",
        "hatch",
        "sp",
    }
)

# git subcommands that act rather than report.
ACTION_GIT_SUBCOMMANDS = frozenset(
    {"add", "commit", "push", "pull", "checkout", "switch", "merge", "rebase", "tag", "reset",
     "fetch", "clone", "init", "cherry-pick", "stash", "restore"}
)


def is_action(command: str) -> bool:
    """True when a command exists to change something, not to report something."""
    parts = command.split()
    if not parts:
        return True
    head = Path(parts[0]).name
    if head in ACTION_COMMANDS:
        return True
    if head == "git" and len(parts) > 1 and parts[1] in ACTION_GIT_SUBCOMMANDS:
        return True
    return False


def extract_shell_commands(skill_md: Path) -> list[str]:
    """Return single-line informational shell commands from ```bash fences in a SKILL.md.

    Deliberately conservative: skips continuations, comments, blank lines, and any
    line containing a shell metacharacter that would need a real parser. Action
    commands are excluded — the target is informational commands, which are the ones
    that can silently return nothing and produce an empty result block.
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
            if is_action(line):
                continue
            commands.append(line)
    return commands


def all_shipped_skills() -> list[Path]:
    return sorted(
        d for d in get_skills_templates_dir().iterdir() if (d / "SKILL.md").exists()
    )


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


@pytest.mark.parametrize("skill_dir", all_shipped_skills(), ids=lambda d: d.name)
def test_skill_commands_never_yield_an_empty_result(skill_dir: Path, clean_clone: Path):
    """No informational command in a shipped skill may exit 0 with no output at all.

    An empty result becomes an empty content block, which the API rejects with a
    bodyless 400 — an error that names nothing and points at nothing.

    The clean_clone fixture matters: `git status --short` is silent only when a
    checkout has no local changes, which is exactly a new contributor's clone and
    never a working machine mid-task.
    """
    commands = extract_shell_commands(skill_dir / "SKILL.md")

    silent: list[str] = []
    for cmd in commands:
        proc = subprocess.run(
            cmd, shell=True, cwd=clean_clone, capture_output=True, text=True
        )
        if proc.returncode == 0 and not proc.stdout.strip() and not proc.stderr.strip():
            silent.append(cmd)

    assert not silent, (
        f"In {skill_dir.name}, these commands succeed with no output at all on a clean "
        "clone, producing an empty result block:\n"
        + "\n".join(f"  {c}" for c in silent)
        + "\n\nMake each one always report something — e.g. `git status --short --branch`, "
        "whose `##` header prints even when the tree is clean."
    )


def test_load_context_step_one_uses_branch_flag():
    """Regression guard for #204: the fix must not be silently reverted.

    `git status --short` without `--branch` prints nothing in a clean checkout. This
    pins the flag so a later edit cannot quietly reintroduce the empty result.
    """
    skill = get_skills_templates_dir() / "load-context" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")

    assert "git status --short --branch" in text, (
        "load-context must use `git status --short --branch` — plain `--short` is "
        "silent in a clean checkout (#204)"
    )

    # Only runnable code counts. Prose may legitimately mention the bare form when
    # explaining why it is wrong — as this skill now does.
    code = "\n".join(re.findall(r"```bash\n(.*?)```", text, re.DOTALL))
    bare = re.findall(r"git status --short(?! --branch)", code)
    assert not bare, (
        f"Found {len(bare)} bare `git status --short` in a bash block — needs --branch (#204)"
    )
