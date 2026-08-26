"""Tests for `sp doctor` — machine setup verification (#204).

The bug this command exists for: a new contributor's machine was missing files the
load-context skill reads, and the only symptom was an unattributable API error. Nothing
answered "is this machine set up correctly?".

Design constraints these tests pin:

- Expectations are derived from the shipped package, never from a second hardcoded
  list. Adding a template must not require editing doctor.
- A missing `CLAUDE.md` is INFO, not a failure — the skill reads it only if present
  (plan D3-A), and it is gitignored by discipline so a clone never has one.
- A missing `~/.sp/user-context/filesystem-access.md` is not reported as a problem at
  all. It grants an AI read access to a tree; only the machine's owner can grant that,
  so its absence is the correct default (plan D6).
- **`doctor` repairs sp-owned files** (plan D10). Captain, 2026-08-19: *"projects have a
  place to write their own context, and it's not in the standard context files that we
  write. we own those. they should not diverge. Report it with a warning and fix it,
  clearly saying that we are doing so."* And, on whether that covers absence as well as
  drift: *"Warn, repair, and say you repaired it."*

  This reverses the earlier "read-only" note in `doctor.py`. That note had no design
  authority: it appeared in the plan only inside the ✅ BUILT record under D8, describing
  what a previous session implemented. D8 ruled the command's *name* and that it be
  built — nothing about repair.

- **Severity is WARNING, and the exit code is 0.** A file sp owns and has just restored
  is not a machine fault. ERROR is reserved for what `doctor` cannot fix: a build that
  ships no templates, or a repair that fails to write.
- **The ownership boundary is read from the catalog** (plan D7/D10), never from a list
  inside `doctor`. `docs/ai-context/project.md`, `~/.sp/user-context/` and `CLAUDE.md`
  are never touched.
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


def _why_not_ok(report) -> str:
    """Name the checks that make a report fail, since only ERROR does.

    A bare `assert report.ok` prints a truncated repr of every check, which says nothing about
    which one failed — and the answer is what a CI-only failure needs.
    """
    errors = [c for c in report.checks if c.severity is Severity.ERROR]
    if not errors:
        return "no ERROR check, so `ok` should have been True"
    return "; ".join(f"{c.id}: {c.title} — {c.detail}" for c in errors)


def test_untouched_machine_is_repaired_not_merely_reported(empty_home: Path, project: Path):
    """D10: missing files are warned about, repaired, and the repair is stated.

    A machine that has never run sp init is the extreme case of 'missing'. It ends the
    run set up, not diagnosed.
    """
    sp_home = empty_home / ".sp"
    report = run_doctor(sp_home=sp_home, project_dir=project)

    checks = _by_id(report)
    for check_id in ("disciplines", "sp_root_files", "skills_installed"):
        assert checks[check_id].severity is Severity.WARNING, (
            f"{check_id} is {checks[check_id].severity}; a file sp owns and restored is "
            "not a machine fault"
        )
        assert checks[check_id].repaired, f"{check_id} was reported but not repaired"

    assert report.ok, f"self-repaired warnings must not fail the run: {_why_not_ok(report)}"
    assert report.exit_code == 0


def test_repair_is_stated_clearly(empty_home: Path, project: Path):
    """Captain: 'clearly saying that we are doing so'.

    A silent repair is worse than none — the user cannot tell what changed on their
    machine.
    """
    report = run_doctor(sp_home=empty_home / ".sp", project_dir=project)

    for check in report.checks:
        if check.repaired:
            assert check.detail, f"{check.id} repaired silently"
            assert "restore" in check.detail.lower() or "repair" in check.detail.lower(), (
                f"{check.id} does not say it was repaired: {check.detail!r}"
            )

    rendered = report.render()
    assert "restored" in rendered.lower() or "repaired" in rendered.lower()


def test_repair_actually_writes_the_files(empty_home: Path, project: Path):
    """The report must not claim a repair that did not happen."""
    sp_home = empty_home / ".sp"
    run_doctor(sp_home=sp_home, project_dir=project)

    installed = {p.name for p in (sp_home / "disciplines").glob("*.md")}
    shipped = {p.name for p in (_templates() / "sp" / "disciplines").glob("*.md")}
    assert shipped <= installed, f"claimed repair left these missing: {sorted(shipped - installed)}"


def test_every_check_explains_what_to_do(empty_home: Path, project: Path):
    """A check that is not OK must either name a remedy or say it fixed it itself.

    An error that names nothing is the bug this command exists for.
    """
    report = run_doctor(sp_home=empty_home / ".sp", project_dir=project)

    for check in report.checks:
        if check.severity in (Severity.ERROR, Severity.WARNING):
            assert check.remedy or check.repaired, (
                f"{check.id} reports a problem without a remedy or a repair"
            )


def test_configured_machine_passes(tmp_path: Path, project: Path):
    """After install_global_disciplines + install_global_skills, the ~/.sp checks pass."""
    from llmflow.cli_utils import install_global_disciplines, install_global_skills

    sp_home = tmp_path / ".sp"
    install_global_disciplines(sp_home=sp_home)
    install_global_skills(sp_home=sp_home)

    checks = _by_id(run_doctor(sp_home=sp_home, project_dir=project))

    for check_id in ("sp_home", "disciplines", "sp_root_files", "skills_installed"):
        assert checks[check_id].severity is not Severity.ERROR, (
            f"{check_id} still failing after install: {checks[check_id].detail}"
        )


def test_expectations_come_from_the_package_not_a_hardcoded_list(tmp_path: Path, project: Path):
    """Doctor must derive expected files from shipped templates.

    Otherwise doctor becomes a third place the file set is written down, and drifts —
    which is the exact failure that left three disciplines unshipped (#204, #181).
    """
    from llmflow.cli_utils import install_global_disciplines

    sp_home = tmp_path / ".sp"
    install_global_disciplines(sp_home=sp_home)

    # Remove one shipped discipline from the installed set; doctor must notice by
    # comparing against the package, and must name the file it is missing.
    # install_global_disciplines locks the directory read-only, so unlock to simulate
    # the drift.
    victim = sorted((_templates() / "sp" / "disciplines").glob("*.md"))[0].name
    disciplines = sp_home / "disciplines"
    disciplines.chmod(0o755)
    (disciplines / victim).chmod(0o644)
    (disciplines / victim).unlink()

    check = _by_id(run_doctor(sp_home=sp_home, project_dir=project))["disciplines"]
    assert check.severity is Severity.WARNING
    assert check.repaired
    assert victim in check.detail
    assert (disciplines / victim).exists(), "the missing discipline was named but not restored"


def test_missing_claude_md_is_informational_not_a_failure(tmp_path: Path, project: Path):
    """Plan D3-A: the skill reads CLAUDE.md only if present, so absence is not an error."""
    from llmflow.cli_utils import install_global_disciplines, install_global_skills

    sp_home = tmp_path / ".sp"
    install_global_disciplines(sp_home=sp_home)
    install_global_skills(sp_home=sp_home)

    check = _by_id(run_doctor(sp_home=sp_home, project_dir=project))["claude_md"]
    assert check.severity is Severity.INFO
    report = run_doctor(sp_home=sp_home, project_dir=project)
    assert report.ok, _why_not_ok(report)


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
    from llmflow.cli_utils import install_global_disciplines, install_global_skills

    sp_home = tmp_path / ".sp"
    install_global_disciplines(sp_home=sp_home)
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


def test_a_freshly_initialised_project_has_nothing_to_repair(tmp_path: Path, monkeypatch):
    """`sp init` then `sp doctor` must report a clean project. No repair, no warning.

    Caught by the fresh-HOME acceptance run: doctor "restored" `.cursorrules` and
    `.windsurfrules` on a project sp had just created. Those two are written with
    `_upsert_delimited_block`, so the file is the constant *wrapped in delimiters* and
    never equals the bare constant — doctor saw permanent divergence and would have
    stripped the delimiters on every run.

    sp owns its block in those files, not the whole file. That is the entire point of
    the delimiters: a project may keep its own rules around sp's block.
    """
    from llmflow.cli_utils import init_project

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SP_HOME", str(home / ".sp"))
    proj = tmp_path / "fresh"
    proj.mkdir()

    init_project(proj)

    report = run_doctor(sp_home=home / ".sp", project_dir=proj, claude_home=home / ".claude")

    repaired = [c.id for c in report.checks if c.repaired]
    assert not repaired, f"doctor repaired a freshly initialised project: {repaired}"
    assert report.ok


def test_repair_preserves_a_projects_own_content_around_the_block(tmp_path: Path, monkeypatch):
    """Restoring `.cursorrules` must replace sp's block and leave the rest untouched."""
    from llmflow.cli_utils import init_project

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SP_HOME", str(home / ".sp"))
    proj = tmp_path / "fresh"
    proj.mkdir()
    init_project(proj)

    cursorrules = proj / ".cursorrules"
    mine = "# my own rule, outside sp's block\n"
    cursorrules.write_text(mine + cursorrules.read_text(encoding="utf-8"), encoding="utf-8")

    # Corrupt sp's block only.
    text = cursorrules.read_text(encoding="utf-8")
    cursorrules.write_text(text.replace("docs/ai-context/sp/rules.md", "GONE"), encoding="utf-8")

    run_doctor(sp_home=home / ".sp", project_dir=proj, claude_home=home / ".claude")

    restored = cursorrules.read_text(encoding="utf-8")
    assert mine in restored, "repair discarded content the project owned"
    assert "docs/ai-context/sp/rules.md" in restored, "repair did not restore sp's block"


def test_sp_init_then_sp_doctor_through_the_cli(tmp_path: Path, monkeypatch, capsys):
    """The end-to-end path, run as a user runs it: `sp init` then `sp doctor`.

    Everything else here calls `run_doctor` directly. This is the only test that goes
    through `main(["doctor"])` — the CLI wiring, `doctor_command`, the printed report and
    the exit code. It exists because a manual fresh-HOME run of exactly this sequence
    caught a repair loop on `.cursorrules` that every unit test passed straight over.

    It also pins the loop's absence: a second run must report the same clean machine, not
    re-repair what the first run just fixed.
    """
    from llmflow.cli import main

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SP_HOME", str(home / ".sp"))

    project_dir = tmp_path / "repo"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    main(["init"])
    capsys.readouterr()

    with pytest.raises(SystemExit) as exited:
        main(["doctor"])
    first = capsys.readouterr().out

    assert exited.value.code == 0, f"doctor failed on a freshly initialised project:\n{first}"
    assert "No problems found." in first
    assert "restored" not in first, f"doctor repaired what sp init had just written:\n{first}"

    with pytest.raises(SystemExit):
        main(["doctor"])
    second = capsys.readouterr().out
    assert "restored" not in second, f"doctor is not idempotent:\n{second}"


def test_cli_doctor_repairs_and_says_so(tmp_path: Path, monkeypatch, capsys):
    """A drifted discipline is restored, and the user is told which file changed.

    Captain: *"Report it with a warning and fix it, clearly saying that we are doing
    so."* A silent repair is worse than none — the user cannot tell what changed on
    their machine.
    """
    from llmflow.cli import main

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SP_HOME", str(home / ".sp"))

    project_dir = tmp_path / "repo"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    main(["init"])
    capsys.readouterr()

    victim = sorted((_templates() / "sp" / "disciplines").glob("*.md"))[0]
    installed = home / ".sp" / "disciplines" / victim.name
    (home / ".sp" / "disciplines").chmod(0o755)
    installed.chmod(0o644)
    installed.write_text("# stale hand-edit\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exited:
        main(["doctor"])
    output = capsys.readouterr().out

    assert exited.value.code == 0, "a self-repaired file is not a machine fault"
    assert victim.name in output, f"the restored file was not named:\n{output}"
    assert "restored" in output.lower()
    assert installed.read_text(encoding="utf-8") == victim.read_text(encoding="utf-8")


def test_diverged_content_is_repaired_not_just_noticed(tmp_path: Path, project: Path):
    """D10, the ruling this test exists for: 'check content, not just presence'.

    The Captain's own ~/.sp/disciplines/surface-decisions.md was the stale 790-byte copy
    against a shipped 3404 bytes, and presence-only checking called that machine healthy.
    """
    from llmflow.cli_utils import install_global_disciplines

    sp_home = tmp_path / ".sp"
    install_global_disciplines(sp_home=sp_home)

    victim = sorted((_templates() / "sp" / "disciplines").glob("*.md"))[0]
    disciplines = sp_home / "disciplines"
    disciplines.chmod(0o755)
    installed = disciplines / victim.name
    installed.chmod(0o644)
    installed.write_text("# hand-edited, and stale\n", encoding="utf-8")

    check = _by_id(run_doctor(sp_home=sp_home, project_dir=project))["disciplines"]

    assert check.severity is Severity.WARNING
    assert check.repaired
    assert victim.name in check.detail
    assert installed.read_text(encoding="utf-8") == victim.read_text(encoding="utf-8"), (
        "content drift was detected but the file was not restored"
    )


def test_repair_never_touches_files_the_project_owns(tmp_path: Path, project: Path):
    """D10: 'projects have a place to write their own context' — and sp stays out of it.

    `docs/ai-context/project.md` is that place; `cli_utils.py:686` already declares sp
    never overwrites it. A repair pass that widened ownership to cover it would delete
    the one file a project is invited to write.
    """
    from llmflow.cli_utils import install_global_disciplines, install_global_skills

    sp_home = tmp_path / ".sp"
    install_global_disciplines(sp_home=sp_home)
    install_global_skills(sp_home=sp_home)

    ai_context = project / "docs" / "ai-context"
    ai_context.mkdir(parents=True)
    project_md = ai_context / "project.md"
    mine = "# This project's own context\n\nHand-written. Not sp's.\n"
    project_md.write_text(mine, encoding="utf-8")

    claude_md = project / "CLAUDE.md"
    claude_md.write_text("# Captain's file\n", encoding="utf-8")

    run_doctor(sp_home=sp_home, project_dir=project)

    assert project_md.read_text(encoding="utf-8") == mine, "doctor overwrote project.md"
    assert claude_md.read_text(encoding="utf-8") == "# Captain's file\n", (
        "doctor overwrote CLAUDE.md, which belongs to the Captain"
    )


def test_repair_survives_the_read_only_lock(tmp_path: Path, project: Path):
    """`install_global_disciplines` locks its directory on exit (`cli_utils.py:1644-1654`).

    Repair writes into that locked directory. This is the trap that already left the whole
    ~/.sp tree read-only once and broke `install_global_skills()` silently, because the
    call sat in a try/except that only warned. A repair that cannot write must not report
    success.
    """
    from llmflow.cli_utils import install_global_disciplines

    sp_home = tmp_path / ".sp"
    install_global_disciplines(sp_home=sp_home)

    victim = sorted((_templates() / "sp" / "disciplines").glob("*.md"))[0]
    installed = sp_home / "disciplines" / victim.name

    # Leave the lock exactly as install_global_disciplines left it, then drift the file.
    (sp_home / "disciplines").chmod(0o755)
    installed.chmod(0o644)
    installed.write_text("drifted\n", encoding="utf-8")
    (sp_home / "disciplines").chmod(0o555)
    installed.chmod(0o444)

    check = _by_id(run_doctor(sp_home=sp_home, project_dir=project))["disciplines"]

    assert check.repaired, "repair gave up against the lock it is expected to handle"
    assert installed.read_text(encoding="utf-8") == victim.read_text(encoding="utf-8")


def test_a_failed_repair_is_an_error_not_a_silent_pass(tmp_path: Path, project: Path, monkeypatch):
    """ERROR is reserved for what doctor cannot fix. A repair that fails is exactly that."""
    from llmflow import doctor as doctor_module
    from llmflow.cli_utils import install_global_disciplines

    sp_home = tmp_path / ".sp"
    install_global_disciplines(sp_home=sp_home)

    victim = sorted((_templates() / "sp" / "disciplines").glob("*.md"))[0]
    disciplines = sp_home / "disciplines"
    disciplines.chmod(0o755)
    (disciplines / victim.name).chmod(0o644)
    (disciplines / victim.name).unlink()

    def refuse(*args, **kwargs):
        raise PermissionError("simulated read-only filesystem")

    monkeypatch.setattr(doctor_module, "_restore", refuse)

    report = run_doctor(sp_home=sp_home, project_dir=project)
    check = _by_id(report)["disciplines"]

    assert check.severity is Severity.ERROR
    assert not check.repaired
    assert check.remedy, "a repair doctor could not perform must tell the user what to do"
    assert not report.ok
