"""The `stage-commits` skill must emit shell that runs in sh, bash and zsh alike (#253).

The skill's whole output is shell a human pastes. A construct that works in the shell the author
happened to use, and not in the one the reader has, fails at the moment the reader is least able
to debug it — mid-commit, with a staged index.

These checks read the shipped template rather than an installed copy, because the template is the
source and an installed copy is refreshed from it.
"""

import re
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / (
    "src/llmflow/templates/sp/skills/stage-commits/SKILL.md"
)

# Constructs that are not POSIX `sh`. Each names the shell that tolerates it, because the point
# is that tolerance differs — not that the construct is wrong everywhere.
NON_POSIX = {
    "[[ ]] test": re.compile(r"\[\["),
    "(( )) arithmetic": re.compile(r"\(\("),
    "array assignment": re.compile(r"^\s*\w+=\("),
    "+= append": re.compile(r"\w\+="),
    "process substitution": re.compile(r"[<>]\("),
    "echo -e / -n": re.compile(r"\becho\s+-[en]"),
    "function keyword": re.compile(r"^\s*function\s+\w+"),
    "$'...' quoting": re.compile(r"\$'"),
    "&> redirect": re.compile(r"&>"),
}

# Instructions the skill must never give. Each has cost this repository real work.
FORBIDDEN_GIT = {
    "git add -A or -a sweeps tracked node_modules": re.compile(r"git\s+add\s+(-A|-a)\b"),
    "git commit -m breaks on quotes, backticks and $": re.compile(r"git\s+commit\s+[^\n]*-m\s"),
    "the agent does not run git push": re.compile(r"^\s*git\s+push\b", re.M),
    "the agent does not run git merge": re.compile(r"^\s*git\s+merge\b", re.M),
}


def shell_blocks(text):
    """Every fenced block whose language is a shell, as (language, body) pairs."""
    return [
        (match.group("lang"), match.group("body"))
        for match in re.finditer(
            r"^```(?P<lang>sh|bash|zsh|shell|console)\n(?P<body>.*?)^```",
            text,
            re.S | re.M,
        )
    ]


@pytest.fixture(scope="module")
def skill_text():
    assert SKILL.exists(), (
        f"{SKILL.relative_to(SKILL.parents[5])} does not exist. The skill is shipped from the "
        "template tree; `.claude/skills/` and `~/.sp/skills/` are installed copies of it."
    )
    return SKILL.read_text(encoding="utf-8")


def test_the_skill_has_shell_to_check(skill_text):
    """A skill that emits no shell would pass every check below by vacuum."""
    assert shell_blocks(skill_text), (
        "No shell code blocks found. This skill's output is shell a human pastes, so the "
        "portability checks below would be inert — the failure mode `check-the-source-not-the-"
        "rendering` names."
    )


@pytest.mark.parametrize("name,pattern", sorted(NON_POSIX.items()))
def test_shell_is_posix(skill_text, name, pattern):
    offences = [
        f"{name}: {line.strip()}"
        for _lang, body in shell_blocks(skill_text)
        for line in body.splitlines()
        if pattern.search(line)
    ]
    assert not offences, (
        "The skill's shell must run in sh, bash and zsh alike (#253). Rewrite:\n  "
        + "\n  ".join(offences)
    )


@pytest.mark.parametrize("reason,pattern", sorted(FORBIDDEN_GIT.items()))
def test_forbidden_git_instructions_are_absent(skill_text, reason, pattern):
    offences = [
        line.strip()
        for _lang, body in shell_blocks(skill_text)
        for line in body.splitlines()
        if pattern.search(line)
    ]
    assert not offences, f"{reason}:\n  " + "\n  ".join(offences)


def test_the_commit_message_goes_through_a_file(skill_text):
    """`-F` is what makes the command portable: it removes quoting from the problem."""
    assert re.search(r"git\s+commit\s+[^\n]*-F\s", skill_text), (
        "The skill must hand over `git commit -F <file>`. A message carrying a quote, a backtick "
        "or a `$` breaks differently in each shell, and `commit-authority` already asks for the "
        "message to be written to a file."
    )


def test_the_staged_result_is_verified(skill_text):
    """"Committed" is not evidence that the commit holds what was intended."""
    assert "git show --stat" in skill_text or "git diff --cached --stat" in skill_text, (
        "The skill must tell the reader how to check what was actually staged or committed "
        "against what was intended."
    )
