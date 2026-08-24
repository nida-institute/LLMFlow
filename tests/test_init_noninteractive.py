"""`sp init` must work end to end with nobody at the keyboard (#204, plan D4/D5/D9).

The failure this pins: a fresh clone got no skills. `_configure_ai_assistants` returned
silently when stdin was not a TTY (`cli_utils.py:805-806`), and Claude Code setup sat
behind two `default=False` prompts (`cli_utils.py:777`, `811-812`), so a user pressing
Enter throughout got Copilot and no Claude Code configuration at all.

Captain, 2026-08-19: *"a fresh clone must get skills"*, and *"write a .gitignore if it
does not exist, but do not overwrite an existing one"*.

D1-A' put the skills copy inside the repo, so the one genuinely machine-scoped write is
gone. Every remaining write lands in the directory the user just ran `sp init` in and is
idempotent, so no prompt has anything left to protect.
"""

from pathlib import Path

import pytest

from llmflow.cli_utils import init_project


@pytest.fixture
def sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A project directory with HOME redirected, so no test touches the real ~/.sp."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    project = tmp_path / "project"
    project.mkdir()
    return project


# --- skills reach the repo ------------------------------------------------------


def test_init_places_skills_where_claude_code_reads_them(sandbox: Path):
    """D1-A': the copy goes into <repo>/.claude/skills/, not ~/.claude/skills/.

    `~/.sp/skills` is not a location Claude Code reads, so a skill left there is not
    invocable and `/load-context` does not exist as a command.
    """
    init_project(sandbox)

    skills = sandbox / ".claude" / "skills"
    assert skills.is_dir(), "sp init did not create <repo>/.claude/skills/"

    installed = {p.name for p in skills.iterdir() if (p / "SKILL.md").exists()}
    assert "load-context" in installed, f"load-context not installed; got {sorted(installed)}"


def test_init_writes_nothing_to_the_home_claude_directory(sandbox: Path, tmp_path: Path):
    """Captain's D1 ruling: 'We don't want to use ~/.claude anything if possible.'

    A′ was chosen precisely because it honours that. A machine-scoped write here would
    be a permission the user never granted.
    """
    init_project(sandbox)

    home_claude = tmp_path / "home" / ".claude"
    assert not home_claude.exists(), "sp init wrote to ~/.claude; D1-A' forbids it"


def test_skill_copy_takes_the_whole_directory(sandbox: Path, tmp_path: Path, monkeypatch):
    """`_install_claude_skills` copied only SKILL.md (`cli_utils.py:728-734`).

    All 10 shipped skills are single-file today, so it is correct now and would silently
    drop supporting files the moment a skill gained one.
    """
    init_project(sandbox)

    sp_skill = tmp_path / "home" / ".sp" / "skills" / "load-context"
    sp_skill.chmod(0o755)
    reference = sp_skill / "references"
    reference.mkdir()
    (reference / "checklist.md").write_text("# checklist\n", encoding="utf-8")

    init_project(sandbox)

    copied = sandbox / ".claude" / "skills" / "load-context" / "references" / "checklist.md"
    assert copied.exists(), "supporting files in a skill directory were dropped"


# --- no prompting ---------------------------------------------------------------


def test_init_never_prompts(sandbox: Path, monkeypatch: pytest.MonkeyPatch):
    """D5: the prompts disappear entirely; sp init becomes fully non-interactive.

    Any surviving `click.confirm` blocks scripted onboarding and, on a TTY, lets a user
    press Enter into a silently broken setup.
    """
    import click

    def explode(*args, **kwargs):  # pragma: no cover - the assertion is the point
        raise AssertionError(f"sp init prompted: {args!r}")

    monkeypatch.setattr(click, "confirm", explode)
    monkeypatch.setattr(click, "prompt", explode)

    init_project(sandbox)


def test_init_configures_assistants_when_stdin_is_not_a_tty(sandbox: Path, monkeypatch):
    """The non-TTY early return at `cli_utils.py:805-806` is the CI / Docker / scripted path.

    It is exactly the path a 'one command' onboarding story takes, and today it does
    nothing and says nothing.
    """
    import sys

    class NotATty:
        def isatty(self):
            return False

    monkeypatch.setattr(sys, "stdin", NotATty())

    init_project(sandbox)

    assert (sandbox / ".claude" / "skills").is_dir()
    assert (sandbox / ".github" / "copilot-instructions.md").exists()
    assert (sandbox / ".cursorrules").exists()
    assert (sandbox / ".windsurfrules").exists()


# --- A2: the three non-Claude files are pointers, not copies --------------------


@pytest.mark.parametrize(
    "relative_path",
    [".cursorrules", ".windsurfrules", ".github/copilot-instructions.md"],
)
def test_assistant_files_point_at_the_authoritative_rules(sandbox: Path, relative_path: str):
    """A2: one authoritative copy of the rules, three signposts.

    A signpost cannot drift out of alignment because it carries nothing to drift.
    """
    init_project(sandbox)

    content = (sandbox / relative_path).read_text(encoding="utf-8")
    assert "docs/ai-context/sp/rules.md" in content, (
        f"{relative_path} does not point at the authoritative rules"
    )


@pytest.mark.parametrize(
    "relative_path",
    [".cursorrules", ".windsurfrules", ".github/copilot-instructions.md"],
)
def test_assistant_files_do_not_restate_the_rules(sandbox: Path, relative_path: str):
    """The finding that forced A2.

    `.cursorrules` and `.windsurfrules` are byte-identical by construction
    (`cli_utils.py:704`), and that shared 6-line block omitted the `sp run` prohibition,
    the memory-file prohibition and the `docs/ai-context/` prohibition — all of which
    `ASSISTANT_RULES_POINTER` carried. An agent reading `.cursorrules` as its rules
    found nothing saying that running a pipeline costs money and needs the Captain's
    say-so: an LLM taking a permission it was never granted.

    The fix is not to sync three copies. It is to stop them carrying rules.
    """
    init_project(sandbox)

    content = (sandbox / relative_path).read_text(encoding="utf-8")
    assert len(content.splitlines()) <= 20, (
        f"{relative_path} is long enough to be a copy of the rules, not a pointer"
    )
    assert "production ready" not in content.lower(), (
        f"{relative_path} restates a rule instead of pointing at it"
    )


# --- D9: the generated .gitignore ------------------------------------------------


def test_init_writes_a_gitignore_when_absent(sandbox: Path):
    """Captain: 'write a .gitignore if it does not exist'."""
    init_project(sandbox)

    gitignore = sandbox / ".gitignore"
    assert gitignore.exists(), "sp init did not generate a .gitignore"
    assert gitignore.read_text(encoding="utf-8").strip(), "generated .gitignore is empty"


def test_init_never_overwrites_an_existing_gitignore(sandbox: Path):
    """Captain: 'but do not overwrite an existing one'."""
    gitignore = sandbox / ".gitignore"
    original = "# mine\nsecrets/\n"
    gitignore.write_text(original, encoding="utf-8")

    init_project(sandbox)

    assert gitignore.read_text(encoding="utf-8") == original, (
        "sp init overwrote a .gitignore the project already owned"
    )


def test_generated_gitignore_does_not_hide_project_skills(sandbox: Path):
    """D1-A' depends on the skills being committed.

    `sil-translator-notes` ignores `.claude/` wholesale, which is why a clone of it
    delivers no skills. Whatever sp generates must not repeat that.
    """
    init_project(sandbox)

    lines = [
        line.strip()
        for line in (sandbox / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    for line in lines:
        assert line not in (".claude", ".claude/", "/.claude", "/.claude/"), (
            "the generated .gitignore hides .claude/ wholesale, so a clone gets no skills"
        )


def test_generated_gitignore_matches_the_catalog(sandbox: Path):
    """D7 + D9: the ignore list is derived, not hand-maintained in a second place."""
    from llmflow.file_catalog import project_gitignore_lines

    init_project(sandbox)

    written = (sandbox / ".gitignore").read_text(encoding="utf-8")
    for line in project_gitignore_lines():
        assert line in written, f"catalog declares {line!r} ignored but .gitignore omits it"
