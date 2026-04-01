"""Tests for global conventions and skills installation (Issue #93)."""
import logging
import yaml
from pathlib import Path
from unittest.mock import patch

import pytest

from llmflow.cli import main
from llmflow.cli_utils import (
    install_global_conventions,
    install_global_skills,
)


def get_template_content(relative_path: str) -> str:
    """Get template file content from the llmflow package."""
    import llmflow
    pkg_root = Path(llmflow.__file__).parent
    template_file = pkg_root / "templates" / relative_path
    return template_file.read_text(encoding="utf-8")


def test_convention_template_exists():
    """Convention template file must exist in package."""
    import llmflow
    pkg_root = Path(llmflow.__file__).parent
    template_file = pkg_root / "templates" / "sp-conventions" / "llmflow-prompt-organization.md"
    assert template_file.exists(), f"Convention template not found at {template_file}"


def test_skill_template_exists():
    """Skill template file must exist in package."""
    import llmflow
    pkg_root = Path(llmflow.__file__).parent
    skill_file = pkg_root / "templates" / "sp-skills" / "audit-prompts" / "SKILL.md"
    assert skill_file.exists(), f"Skill template not found at {skill_file}"


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

    assert convention_file.exists()
    assert readme_file.exists()

    # Verify content matches templates
    template_convention = get_template_content("sp-conventions/llmflow-prompt-organization.md")
    assert convention_file.read_text(encoding="utf-8") == template_convention


def test_install_global_skills_creates_files(tmp_path):
    """install_global_skills creates ~/.sp/skills/ files."""
    sp_dir = tmp_path / ".sp"

    install_global_skills(sp_home=sp_dir)

    skill_file = sp_dir / "skills" / "audit-prompts" / "SKILL.md"
    assert skill_file.exists()

    template_skill = get_template_content("sp-skills/audit-prompts/SKILL.md")
    assert skill_file.read_text(encoding="utf-8") == template_skill


def test_install_conventions_is_idempotent(tmp_path):
    """install_global_conventions respects existing files with force=False."""
    sp_dir = tmp_path / ".sp"

    install_global_conventions(sp_home=sp_dir)
    convention_file = sp_dir / "conventions" / "llmflow-prompt-organization.md"

    original_content = convention_file.read_text(encoding="utf-8")
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

    # Verify global skills were installed
    assert (fake_home / ".sp" / "skills" / "audit-prompts" / "SKILL.md").exists()
