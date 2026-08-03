"""Tests for global conventions and skills installation (Issue #93, #164)."""
import logging
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

    with patch("llmflow.cli_utils._fetch_stand_down", return_value=None):
        install_global_skills(sp_home=sp_dir)

    for skill_name in EXPECTED_SKILLS:
        skill_file = sp_dir / "skills" / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Expected skill not installed: {skill_name}"


def test_install_global_skills_content_matches_templates(tmp_path):
    """Installed skill content must match the template (for non-fetched skills)."""
    sp_dir = tmp_path / ".sp"

    with patch("llmflow.cli_utils._fetch_stand_down", return_value=None):
        install_global_skills(sp_home=sp_dir)

    for skill_name in EXPECTED_SKILLS:
        installed = sp_dir / "skills" / skill_name / "SKILL.md"
        template = get_skills_templates_dir() / skill_name / "SKILL.md"
        assert installed.read_text(encoding="utf-8") == template.read_text(encoding="utf-8"), \
            f"Installed {skill_name} does not match template"


def test_install_global_skills_stand_down_uses_fetched_content(tmp_path):
    """When fetch succeeds, stand-down uses fetched content not bundled fallback."""
    sp_dir = tmp_path / ".sp"
    fetched_content = "---\nname: stand-down\n---\n# Fetched version\n"

    with patch("llmflow.cli_utils._fetch_stand_down", return_value=fetched_content):
        install_global_skills(sp_home=sp_dir)

    installed = (sp_dir / "skills" / "stand-down" / "SKILL.md").read_text(encoding="utf-8")
    assert installed == fetched_content


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

    with patch("pathlib.Path.home", return_value=fake_home), \
         patch("llmflow.cli_utils._fetch_stand_down", return_value=None):
        main(["init"])

    # Verify global conventions were installed
    assert (fake_home / ".sp" / "conventions" / "llmflow-prompt-organization.md").exists()
    assert (fake_home / ".sp" / "conventions" / "README.md").exists()
    assert (fake_home / ".sp" / "conventions" / "llmflow-project-tracking.md").exists()

    # Verify all expected skills were installed
    for skill_name in {"audit-prompts", "load-context", "authorize", "stand-down"}:
        assert (fake_home / ".sp" / "skills" / skill_name / "SKILL.md").exists(), \
            f"Expected skill not installed by sp init: {skill_name}"
