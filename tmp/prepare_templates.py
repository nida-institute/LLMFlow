#!/usr/bin/env python3
"""Prepare template constants for cli_utils.py."""
from pathlib import Path

# Read the actual files
convention_file = Path.home() / ".sp" / "conventions" / "llmflow-prompt-organization.md"
readme_file = Path.home() / ".sp" / "conventions" / "README.md"
skill_file = Path.home() / ".sp" / "skills" / "audit-prompts" / "SKILL.md"

convention_content = convention_file.read_text(encoding="utf-8")
readme_content = readme_file.read_text(encoding="utf-8")
skill_content = skill_file.read_text(encoding="utf-8")

# Write as Python constants
output = Path("/tmp/template_constants.py")
with output.open("w", encoding="utf-8") as f:
    f.write('"""Template constants for global conventions and skills (Issue #93)."""\n\n')

    # Convention template
    f.write("PROMPT_ORGANIZATION_CONVENTION = ")
    f.write(repr(convention_content))
    f.write("\n\n")

    # README template
    f.write("CONVENTIONS_README = ")
    f.write(repr(readme_content))
    f.write("\n\n")

    # Skill template
    f.write("AUDIT_PROMPTS_SKILL = ")
    f.write(repr(skill_content))
    f.write("\n")

print(f"Templates written to {output}")
print(f"Convention: {len(convention_content)} chars")
print(f"README: {len(readme_content)} chars")
print(f"Skill: {len(skill_content)} chars")
