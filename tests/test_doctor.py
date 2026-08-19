"""Tests for `sp doctor` — machine setup verification (#204).

The bug this command exists for: a new contributor's machine was missing files the
load-context skill reads, and the only symptom was an unattributable API error. Nothing
answered "is this machine set up correctly?".

Design constraints these tests pin:

- Expectations are derived from the shipped package, never from a second hardcoded
  list. Adding a template must not require editing doctor.
- A missing `CLAUDE.md` is INFO, not a failure — the skill reads it only if present
  (plan D3-A), and it is gitignored by convention so a clone never has one.
- A missing `~/.sp/user-context/filesystem-access.md` is not reported as a problem at
  all. It grants an AI read access to a tree; only the machine's owner can grant that,
  so its absence is the correct default (plan D6).
"""

from pathlib import Path

import pytest

from llmflow.doctor import Severity, run_doctor


def _templates() -> Path:
    import llmflow

    return Path(llmflow.__file__).parent / "templates"


@pytest.fixture
def empty_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


@pytest.fixture
def project(tmp_path: Path) -> Path:
    proj = tmp_path / "project"
    proj.mkdir()
    return proj


def _by_id(report):
    return {check.id: check for check in report.checks}


def test_untouched_machine_reports_errors(empty_home: Path, project: Path):
    """A machine that has never run sp init must fail, and say what is missing."""
    report = run_doctor(sp_home=empty_home / ".sp", project_dir=project)

    assert not report.ok
    assert report.exit_code != 0

    checks = _by_id(report)
    assert checks["sp_home"].severity is Severity.ERROR
    assert checks["conventions"].severity is Severity.ERROR
    assert checks["sp_root_files"].severity is Severity.ERROR
    assert checks["skills_installed"].severity is Severity.ERROR


def test_every_check_explains_what_to_do(empty_home: Path, project: Path):
    """A failing check must name a remedy. An error that names nothing is the bug."""
    report = run_doctor(sp_home=empty_home / ".sp", project_dir=project)

    for check in report.checks:
        if check.severity is Severity.ERROR:
            assert check.remedy, f"{check.id} fails without telling the user what to do"


def test_configured_machine_passes(tmp_path: Path, project: Path):
    """After install_global_conventions + install_global_skills, the ~/.sp checks pass."""
    from llmflow.cli_utils import install_global_conventions, install_global_skills

    sp_home = tmp_path / ".sp"
    install_global_conventions(sp_home=sp_home)
    install_global_skills(sp_home=sp_home)

    checks = _by_id(run_doctor(sp_home=sp_home, project_dir=project))

    for check_id in ("sp_home", "conventions", "sp_root_files", "skills_installed"):
        assert checks[check_id].severity is not Severity.ERROR, (
            f"{check_id} still failing after install: {checks[check_id].detail}"
        )


def test_expectations_come_from_the_package_not_a_hardcoded_list(tmp_path: Path, project: Path):
    """Doctor must derive expected files from shipped templates.

    Otherwise doctor becomes a third place the file set is written down, and drifts —
    which is the exact failure that left three conventions unshipped (#204, #181).
    """
    from llmflow.cli_utils import install_global_conventions

    sp_home = tmp_path / ".sp"
    install_global_conventions(sp_home=sp_home)

    # Remove one shipped convention from the installed set; doctor must notice by
    # comparing against the package, and must name the file it is missing.
    # install_global_conventions locks the directory read-only, so unlock to simulate
    # the drift.
    victim = sorted((_templates() / "sp-conventions").glob("*.md"))[0].name
    conventions = sp_home / "conventions"
    conventions.chmod(0o755)
    (conventions / victim).chmod(0o644)
    (conventions / victim).unlink()

    check = _by_id(run_doctor(sp_home=sp_home, project_dir=project))["conventions"]
    assert check.severity is Severity.ERROR
    assert victim in check.detail


def test_missing_claude_md_is_informational_not_a_failure(tmp_path: Path, project: Path):
    """Plan D3-A: the skill reads CLAUDE.md only if present, so absence is not an error."""
    from llmflow.cli_utils import install_global_conventions, install_global_skills

    sp_home = tmp_path / ".sp"
    install_global_conventions(sp_home=sp_home)
    install_global_skills(sp_home=sp_home)

    check = _by_id(run_doctor(sp_home=sp_home, project_dir=project))["claude_md"]
    assert check.severity is Severity.INFO
    assert run_doctor(sp_home=sp_home, project_dir=project).ok


def test_filesystem_access_is_never_reported(empty_home: Path, project: Path):
    """Plan D6: a missing permission grant is the correct default, not a misconfiguration."""
    report = run_doctor(sp_home=empty_home / ".sp", project_dir=project)
    rendered = " ".join(f"{c.id} {c.detail} {c.remedy}" for c in report.checks)
    assert "filesystem-access" not in rendered


def test_reports_where_claude_code_can_actually_find_skills(tmp_path: Path, project: Path):
    """~/.sp/skills is not a location Claude Code reads (plan D1).

    Skills must reach ~/.claude/skills/ or <repo>/.claude/skills/. A machine with a
    populated ~/.sp/skills and neither of those has no working slash commands, which is
    precisely the reported failure — so this must be surfaced, not passed over.
    """
    from llmflow.cli_utils import install_global_conventions, install_global_skills

    sp_home = tmp_path / ".sp"
    install_global_conventions(sp_home=sp_home)
    install_global_skills(sp_home=sp_home)

    checks = _by_id(
        run_doctor(sp_home=sp_home, project_dir=project, claude_home=tmp_path / "no-claude")
    )
    assert checks["skills_reachable"].severity is not Severity.OK

    # Now place a project-scoped skill; it must be recognised as reachable.
    skill = project / ".claude" / "skills" / "load-context"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# load-context\n", encoding="utf-8")

    checks = _by_id(
        run_doctor(sp_home=sp_home, project_dir=project, claude_home=tmp_path / "no-claude")
    )
    assert checks["skills_reachable"].severity is Severity.OK
    assert ".claude/skills" in checks["skills_reachable"].detail


def test_does_not_write_anything(tmp_path: Path, project: Path):
    """doctor diagnoses; it must not repair. A read-only command is safe to run anywhere."""
    sp_home = tmp_path / ".sp"
    run_doctor(sp_home=sp_home, project_dir=project)
    assert not sp_home.exists(), "doctor created ~/.sp — it must only report"
    assert list(project.iterdir()) == [], "doctor wrote into the project directory"
