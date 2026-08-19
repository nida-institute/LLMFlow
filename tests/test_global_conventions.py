"""Tests for global conventions and skills installation (Issue #93, #164)."""
import logging
import re
import stat
import yaml
from pathlib import Path
from unittest.mock import patch

import pytest

from llmflow.cli import main
from llmflow.cli_utils import (
    install_global_conventions,
    install_global_skills,
)

# Conventions the package must ship to ~/.sp/conventions/ (#204, #181).
#
# This set is the counterpart to EXPECTED_SKILLS below, and it exists because that
# asymmetry caused a real bug: skills had a drift guard and conventions did not, so
# three conventions present on the author's machine were never added to the package.
# Nobody noticed until a new contributor's machine had 5 of 8 (#204).
#
# Adding a convention to ~/.sp/ without adding it here — or to templates/ without
# listing it here — fails the test.
EXPECTED_CONVENTIONS = {
    "README.md",
    "consumer-repo-conventions.md",
    "design-authority.md",
    "github-authority.md",
    "llmflow-pipeline-steps.md",
    "llmflow-project-tracking.md",
    "llmflow-prompt-organization.md",
    "sp-debugging.md",
    "sp-workflow.md",
    "surface-decisions.md",
}

# Files installed at the root of ~/.sp/ rather than into a subdirectory.
EXPECTED_SP_ROOT_FILES = {"drift-patterns.md"}

EXPECTED_SKILLS = {
    "audit-code",
    "audit-output",
    "audit-pipeline",
    "audit-prompts",
    "authorize",
    "commit-ready",
    "handoff",
    "load-context",
    "release",
    "stand-down",
}


def get_template_content(relative_path: str) -> str:
    """Get template file content from the llmflow package."""
    import llmflow
    pkg_root = Path(llmflow.__file__).parent
    template_file = pkg_root / "templates" / relative_path
    return template_file.read_text(encoding="utf-8")


def get_skills_templates_dir() -> Path:
    import llmflow
    return Path(llmflow.__file__).parent / "templates" / "sp-skills"


def test_convention_template_exists():
    """Convention template file must exist in package."""
    import llmflow
    pkg_root = Path(llmflow.__file__).parent
    template_file = pkg_root / "templates" / "sp-conventions" / "llmflow-prompt-organization.md"
    assert template_file.exists(), f"Convention template not found at {template_file}"


def test_project_tracking_convention_template_exists():
    """Rolling-file convention template must exist in package."""
    import llmflow
    pkg_root = Path(llmflow.__file__).parent
    template_file = pkg_root / "templates" / "sp-conventions" / "llmflow-project-tracking.md"
    assert template_file.exists(), f"Project tracking convention not found at {template_file}"


def get_conventions_templates_dir() -> Path:
    import llmflow

    return Path(llmflow.__file__).parent / "templates" / "sp-conventions"


@pytest.mark.parametrize("convention_name", sorted(EXPECTED_CONVENTIONS))
def test_convention_template_shipped(convention_name):
    """Every expected convention must exist in the templates directory."""
    template = get_conventions_templates_dir() / convention_name
    assert template.exists(), f"Convention template not shipped: {template}"


def test_shipped_conventions_match_expected():
    """Templates conventions set must equal EXPECTED_CONVENTIONS — drift guard (#204).

    The counterpart to test_installed_skills_match_templates. Without this, a
    convention can live on one machine and never reach the package — which is exactly
    how design-authority.md, sp-debugging.md and sp-workflow.md went missing.
    """
    shipped = {p.name for p in get_conventions_templates_dir().glob("*.md")}
    assert shipped == EXPECTED_CONVENTIONS, (
        "Shipped conventions do not match EXPECTED_CONVENTIONS:\n"
        f"  Extra in templates:   {sorted(shipped - EXPECTED_CONVENTIONS)}\n"
        f"  Missing from templates: {sorted(EXPECTED_CONVENTIONS - shipped)}"
    )


@pytest.mark.parametrize("filename", sorted(EXPECTED_SP_ROOT_FILES))
def test_sp_root_file_shipped(filename):
    """Files belonging at the root of ~/.sp/ must ship in the package.

    drift-patterns.md is read directly by the load-context skill, and was absent from
    the package entirely — a fresh machine could not obtain it at all (#204).
    """
    import llmflow

    template = Path(llmflow.__file__).parent / "templates" / "sp-root" / filename
    assert template.exists(), f"Not shipped: {template}"


@pytest.mark.parametrize("filename", sorted(EXPECTED_SP_ROOT_FILES))
def test_install_places_sp_root_files(tmp_path, filename):
    """install_global_conventions() must place root-level files at ~/.sp/<name>.

    Not in ~/.sp/conventions/ — the load-context skill reads ~/.sp/drift-patterns.md
    by that exact path.
    """
    sp_dir = tmp_path / ".sp"
    install_global_conventions(sp_home=sp_dir)
    assert (sp_dir / filename).exists(), f"sp init did not install ~/.sp/{filename}"


def test_shipped_templates_carry_no_machine_specific_content():
    """No shipped template may contain a personal address or an absolute home path.

    github-authority.md was promoted from ~/.sp/user-context/ and named a specific bot
    account; shipping that would have put one person's email on every user's machine.
    The same class of defect made ~/.sp/editions/*.yaml non-portable (#204).
    """
    import llmflow

    templates = Path(llmflow.__file__).parent / "templates"
    offenders: list[str] = []
    patterns = {
        "email address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
        "absolute home path": re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+"),
    }
    for path in sorted(templates.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for label, pattern in patterns.items():
            for hit in pattern.findall(text):
                # A generic placeholder is fine; a real one is not.
                if any(token in hit.lower() for token in ("example.com", "you@", "<", "your-")):
                    continue
                offenders.append(f"{path.relative_to(templates)}: {label} {hit!r}")

    assert not offenders, "Machine-specific content in shipped templates:\n" + "\n".join(
        f"  {o}" for o in offenders
    )


def test_conventions_readme_indexes_every_convention():
    """The conventions README must document every shipped convention.

    Its own instructions say to "Add entry to this README" when adding a convention,
    and it had drifted to listing 3 of 8 — the same silent-omission failure as the
    missing templates, one level up. Enforced rather than trusted.
    """
    readme = get_conventions_templates_dir() / "README.md"
    text = readme.read_text(encoding="utf-8")
    undocumented = sorted(
        name
        for name in EXPECTED_CONVENTIONS
        if name != "README.md" and name not in text
    )
    assert not undocumented, (
        f"These conventions are shipped but not listed in {readme.name}: {undocumented}"
    )


def test_install_global_conventions_installs_every_expected_convention(tmp_path):
    """A fresh machine must end up with all of them, not a subset (#204).

    The bug this pins: a new contributor's ~/.sp/conventions/ had 5 of 8 files, so
    /load-context silently loaded less guidance than the mentor's machine had.
    """
    sp_dir = tmp_path / ".sp"
    install_global_conventions(sp_home=sp_dir)

    installed = {p.name for p in (sp_dir / "conventions").glob("*.md")}
    missing = EXPECTED_CONVENTIONS - installed
    assert not missing, f"sp init left these conventions uninstalled: {sorted(missing)}"


@pytest.mark.parametrize("skill_name", sorted(EXPECTED_SKILLS))
def test_skill_template_exists(skill_name):
    """Every expected skill must have a SKILL.md in the templates directory."""
    templates_dir = get_skills_templates_dir()
    skill_file = templates_dir / skill_name / "SKILL.md"
    assert skill_file.exists(), f"Skill template not found: {skill_file}"


def test_installed_skills_match_templates():
    """Templates directory skills set must equal EXPECTED_SKILLS — regression guard against drift."""
    templates_dir = get_skills_templates_dir()
    template_skills = {
        d.name for d in templates_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    }
    assert template_skills == EXPECTED_SKILLS, (
        f"Skills in templates do not match expected set.\n"
        f"  Extra in templates: {template_skills - EXPECTED_SKILLS}\n"
        f"  Missing from templates: {EXPECTED_SKILLS - template_skills}"
    )


def test_skill_has_valid_yaml_frontmatter():
    """Skill YAML frontmatter must parse correctly."""
    content = get_template_content("sp-skills/audit-prompts/SKILL.md")

    assert content.startswith("---\n")
    parts = content.split("---\n", 2)
    assert len(parts) >= 3, "Skill must have YAML frontmatter"

    data = yaml.safe_load(parts[1])
    assert data["name"] == "audit-prompts"
    assert "toolRestrictions" in data
    assert "replace_string_in_file" in data["toolRestrictions"]["forbidden"]


def test_install_global_conventions_creates_files(tmp_path):
    """install_global_conventions creates ~/.sp/conventions/ files."""
    sp_dir = tmp_path / ".sp"

    install_global_conventions(sp_home=sp_dir)

    convention_file = sp_dir / "conventions" / "llmflow-prompt-organization.md"
    readme_file = sp_dir / "conventions" / "README.md"
    tracking_file = sp_dir / "conventions" / "llmflow-project-tracking.md"

    assert convention_file.exists()
    assert readme_file.exists()
    assert tracking_file.exists()

    # Verify content matches templates
    template_convention = get_template_content("sp-conventions/llmflow-prompt-organization.md")
    assert convention_file.read_text(encoding="utf-8") == template_convention


def test_install_global_skills_creates_files(tmp_path):
    """install_global_skills installs all expected skills to ~/.sp/skills/."""
    sp_dir = tmp_path / ".sp"

    install_global_skills(sp_home=sp_dir)

    for skill_name in EXPECTED_SKILLS:
        skill_file = sp_dir / "skills" / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Expected skill not installed: {skill_name}"


def test_install_global_skills_content_matches_templates(tmp_path):
    """Every installed skill matches the shipped template — stand-down included.

    stand-down used to be fetched from human-at-the-helm at install time, with the
    bundled template as a fallback, so its content was deliberately allowed to differ.
    Removed 2026-08-19 (#204, plan D10): `sp doctor` now restores any sp-owned file whose
    content has diverged from what the package ships, and a file fetched from elsewhere
    diverges by design — doctor would have overwritten the fetched copy on every run.

    Captain's ruling: *"Drop the fetch — ship stand-down like every other skill, one
    source of truth."*
    """
    sp_dir = tmp_path / ".sp"

    install_global_skills(sp_home=sp_dir)

    for skill_name in EXPECTED_SKILLS:
        installed = sp_dir / "skills" / skill_name / "SKILL.md"
        template = get_skills_templates_dir() / skill_name / "SKILL.md"
        assert installed.read_text(encoding="utf-8") == template.read_text(encoding="utf-8"), \
            f"Installed {skill_name} does not match template"


def test_install_global_skills_makes_no_network_call(tmp_path, monkeypatch):
    """Installing skills must not depend on the network (#204, plan D10).

    The fetch made `sp init` fail differently offline than online, and made one skill's
    installed content unpredictable. One source of truth means the package.
    """
    import urllib.request

    def explode(*args, **kwargs):
        raise AssertionError("install_global_skills attempted a network call")

    monkeypatch.setattr(urllib.request, "urlopen", explode)

    install_global_skills(sp_home=tmp_path / ".sp")

    stand_down = tmp_path / ".sp" / "skills" / "stand-down" / "SKILL.md"
    template = get_skills_templates_dir() / "stand-down" / "SKILL.md"
    assert stand_down.read_text(encoding="utf-8") == template.read_text(encoding="utf-8")


def test_install_conventions_is_idempotent(tmp_path):
    """install_global_conventions respects existing files with force=False."""
    sp_dir = tmp_path / ".sp"

    install_global_conventions(sp_home=sp_dir)
    convention_file = sp_dir / "conventions" / "llmflow-prompt-organization.md"

    original_content = convention_file.read_text(encoding="utf-8")
    convention_file.chmod(convention_file.stat().st_mode | stat.S_IWUSR)
    convention_file.write_text("# MODIFIED\n", encoding="utf-8")

    # Should NOT overwrite
    install_global_conventions(sp_home=sp_dir, force=False)
    assert convention_file.read_text(encoding="utf-8") == "# MODIFIED\n"

    # With force=True, should overwrite
    install_global_conventions(sp_home=sp_dir, force=True)
    assert convention_file.read_text(encoding="utf-8") == original_content


def test_sp_init_installs_global_resources(tmp_path, monkeypatch, caplog):
    """sp init should install conventions and skills to ~/.sp/."""
    caplog.set_level(logging.INFO)

    fake_home = tmp_path / "home"
    fake_home.mkdir()

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    monkeypatch.chdir(project_dir)

    with patch("pathlib.Path.home", return_value=fake_home):
        main(["init"])

    # Verify global conventions were installed
    assert (fake_home / ".sp" / "conventions" / "llmflow-prompt-organization.md").exists()
    assert (fake_home / ".sp" / "conventions" / "README.md").exists()
    assert (fake_home / ".sp" / "conventions" / "llmflow-project-tracking.md").exists()

    # Verify all expected skills were installed
    for skill_name in {"audit-prompts", "load-context", "authorize", "stand-down"}:
        assert (fake_home / ".sp" / "skills" / skill_name / "SKILL.md").exists(), \
            f"Expected skill not installed by sp init: {skill_name}"
