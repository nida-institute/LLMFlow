"""`sp doctor` — verify that this machine is set up correctly (#204).

Why this exists: a new contributor ran `sp init` and then `/load-context`, and got an
HTTP 400 with no body. Nothing on the machine could answer "is this set up correctly?",
so the first symptom of a missing markdown file was an API error that named nothing.

Design rules, from `project/plans/design-onboarding-fresh-clone.md`:

- **Expectations are derived from the shipped package.** The set of conventions, skills
  and root files that *should* be installed is read from `templates/`, never from a list
  kept here. A second list would drift, which is exactly how three conventions went
  unshipped for months.
- **Read-only.** `doctor` reports; it never repairs. Running it is always safe.
- **A missing `CLAUDE.md` is INFO, not a failure** (D3-A). The skill reads it only if
  present, and it is gitignored by convention, so a clone never has one.
- **`~/.sp/user-context/filesystem-access.md` is not checked at all** (D6). It grants an
  AI standing read access to a directory tree; only the machine's owner can grant that,
  so its absence is the correct default rather than a misconfiguration.

Known overlap: `sp registry status` also reports on `~/.sp/`. Whether `doctor` subsumes
it is an open question tracked in #205; this command does not consolidate anything.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class Severity(enum.Enum):
    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


_MARK = {
    Severity.OK: "✓",
    Severity.INFO: "·",
    Severity.WARNING: "!",
    Severity.ERROR: "✗",
}


@dataclass
class Check:
    id: str
    title: str
    severity: Severity
    detail: str = ""
    remedy: str = ""


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(c.severity is Severity.ERROR for c in self.checks)

    @property
    def exit_code(self) -> int:
        return 0 if self.ok else 1

    def render(self) -> str:
        lines = ["Scripture Pipelines — machine check", ""]
        for check in self.checks:
            lines.append(f"  {_MARK[check.severity]} {check.title}")
            if check.detail:
                lines.append(f"      {check.detail}")
            if check.remedy and check.severity in (Severity.ERROR, Severity.WARNING):
                lines.append(f"      → {check.remedy}")
        lines.append("")
        errors = sum(1 for c in self.checks if c.severity is Severity.ERROR)
        warnings = sum(1 for c in self.checks if c.severity is Severity.WARNING)
        if errors:
            lines.append(f"{errors} problem(s) found." + (f" {warnings} warning(s)." if warnings else ""))
        elif warnings:
            lines.append(f"No problems found. {warnings} warning(s).")
        else:
            lines.append("No problems found.")
        return "\n".join(lines)


def _templates_dir() -> Path:
    import llmflow

    return Path(llmflow.__file__).parent / "templates"


def _shipped_names(subdir: str) -> set[str]:
    """Names the package ships for a given template subdirectory."""
    d = _templates_dir() / subdir
    if not d.is_dir():
        return set()
    return {p.name for p in d.glob("*.md")}


def _shipped_skill_names() -> set[str]:
    d = _templates_dir() / "sp-skills"
    if not d.is_dir():
        return set()
    return {p.name for p in d.iterdir() if (p / "SKILL.md").exists()}


def run_doctor(
    sp_home: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    claude_home: Optional[Path] = None,
) -> Report:
    """Inspect the machine and return a Report. Writes nothing.

    Args:
        sp_home: the ~/.sp directory. Defaults to Path.home() / ".sp".
        project_dir: the repository to check. Defaults to the working directory.
        claude_home: the ~/.claude directory. Defaults to Path.home() / ".claude".
    """
    sp_home = sp_home or Path.home() / ".sp"
    project_dir = project_dir or Path.cwd()
    claude_home = claude_home or Path.home() / ".claude"

    report = Report()
    add = report.checks.append

    # --- ~/.sp itself -------------------------------------------------------
    if sp_home.is_dir():
        add(Check("sp_home", f"{sp_home} exists", Severity.OK))
    else:
        add(
            Check(
                "sp_home",
                f"{sp_home} is missing",
                Severity.ERROR,
                detail="No global resources are installed on this machine.",
                remedy="Run `sp init` in a project directory.",
            )
        )

    # --- conventions -------------------------------------------------------
    expected = _shipped_names("sp-conventions")
    installed = {p.name for p in (sp_home / "conventions").glob("*.md")}
    missing = sorted(expected - installed)
    if not expected:
        add(
            Check(
                "conventions",
                "Conventions",
                Severity.WARNING,
                detail="The installed package ships no conventions; this build looks incomplete.",
                remedy="Reinstall Scripture Pipelines.",
            )
        )
    elif missing:
        add(
            Check(
                "conventions",
                f"Conventions: {len(installed & expected)}/{len(expected)} installed",
                Severity.ERROR,
                detail="Missing: " + ", ".join(missing),
                remedy="Run `sp init --update` to install the missing conventions.",
            )
        )
    else:
        add(Check("conventions", f"Conventions: all {len(expected)} installed", Severity.OK))

    # --- root-level files (drift-patterns.md and friends) -------------------
    expected_root = _shipped_names("sp-root")
    missing_root = sorted(n for n in expected_root if not (sp_home / n).exists())
    if not expected_root:
        add(Check("sp_root_files", "Root files: none shipped by this build", Severity.INFO))
    elif missing_root:
        add(
            Check(
                "sp_root_files",
                "Files the skills read directly are missing",
                Severity.ERROR,
                detail="Missing: " + ", ".join(f"~/.sp/{n}" for n in missing_root),
                remedy="Run `sp init --update`.",
            )
        )
    else:
        add(
            Check(
                "sp_root_files",
                f"Root files: all {len(expected_root)} installed",
                Severity.OK,
            )
        )

    # --- skills present in ~/.sp -------------------------------------------
    expected_skills = _shipped_skill_names()
    skills_dir = sp_home / "skills"
    installed_skills = (
        {p.name for p in skills_dir.iterdir() if (p / "SKILL.md").exists()}
        if skills_dir.is_dir()
        else set()
    )
    missing_skills = sorted(expected_skills - installed_skills)
    if missing_skills:
        add(
            Check(
                "skills_installed",
                f"Skills in ~/.sp: {len(installed_skills & expected_skills)}/{len(expected_skills)}",
                Severity.ERROR,
                detail="Missing: " + ", ".join(missing_skills),
                remedy="Run `sp init --update`.",
            )
        )
    else:
        add(
            Check(
                "skills_installed",
                f"Skills in ~/.sp: all {len(expected_skills)} installed",
                Severity.OK,
            )
        )

    # --- can Claude Code actually see any of them? -------------------------
    # ~/.sp/skills is NOT a location Claude Code reads. Skills only become invocable
    # from ~/.claude/skills/ or <repo>/.claude/skills/ (plan D1).
    project_skills = project_dir / ".claude" / "skills"
    personal_skills = claude_home / "skills"
    found: list[str] = []
    if project_skills.is_dir() and any(
        (p / "SKILL.md").exists() for p in project_skills.iterdir() if p.is_dir()
    ):
        found.append(".claude/skills (this project)")
    if personal_skills.is_dir() and any(
        (p / "SKILL.md").exists() for p in personal_skills.iterdir() if p.is_dir()
    ):
        found.append("~/.claude/skills (personal)")

    if found:
        add(
            Check(
                "skills_reachable",
                "Skills are where Claude Code reads them",
                Severity.OK,
                detail="Found in: " + ", ".join(found),
            )
        )
    else:
        add(
            Check(
                "skills_reachable",
                "No skills are where Claude Code can find them",
                Severity.ERROR,
                detail=(
                    "~/.sp/skills is not a location Claude Code reads. Slash commands such as "
                    "/load-context will not exist until skills are in .claude/skills."
                ),
                remedy=(
                    "Copy them into this project's .claude/skills/, or into ~/.claude/skills/ "
                    "for every project."
                ),
            )
        )

    # --- project-side AI context -------------------------------------------
    ai_context = project_dir / "docs" / "ai-context"
    if ai_context.is_dir():
        present = sorted(p.name for p in ai_context.glob("*.md"))
        if present:
            add(
                Check(
                    "ai_context",
                    f"docs/ai-context/: {len(present)} file(s)",
                    Severity.OK,
                    detail=", ".join(present),
                )
            )
        else:
            add(
                Check(
                    "ai_context",
                    "docs/ai-context/ exists but is empty",
                    Severity.WARNING,
                    remedy="Run `sp init` in this project.",
                )
            )
    else:
        add(
            Check(
                "ai_context",
                "docs/ai-context/ is missing",
                Severity.WARNING,
                detail="This project carries no committed AI context.",
                remedy="Run `sp init` in this project.",
            )
        )

    # --- CLAUDE.md: informational only (D3-A) ------------------------------
    claude_md = project_dir / "CLAUDE.md"
    if claude_md.exists():
        add(Check("claude_md", "CLAUDE.md present", Severity.OK))
    else:
        add(
            Check(
                "claude_md",
                "No CLAUDE.md in this project",
                Severity.INFO,
                detail=(
                    "Not required. It is gitignored by convention, so a fresh clone never has "
                    "one; committed context lives in docs/ai-context/."
                ),
            )
        )

    # --- project registration ----------------------------------------------
    projects_dir = sp_home / "projects"
    registered = {p.stem for p in projects_dir.glob("*.yaml")} if projects_dir.is_dir() else set()
    if project_dir.name in registered:
        add(Check("registered", f"Project '{project_dir.name}' is registered", Severity.OK))
    else:
        add(
            Check(
                "registered",
                f"Project '{project_dir.name}' is not registered in ~/.sp/projects/",
                Severity.WARNING,
                remedy="Run `sp init` in this project.",
            )
        )

    return report


def doctor_command(project_dir: Optional[Path] = None) -> int:
    """CLI entry point. Prints the report and returns an exit code."""
    report = run_doctor(project_dir=project_dir)
    print(report.render())
    return report.exit_code
