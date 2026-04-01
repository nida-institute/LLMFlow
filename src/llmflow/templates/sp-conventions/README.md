# Global Conventions

This directory contains shared conventions used across multiple projects.

## Available Conventions

### llmflow-prompt-organization.md
Standard organization pattern for LLMFlow `.gpt` prompt files.

**Used by:**
- audit-prompts skill (`~/.sp/skills/audit-prompts/`)
- Any project using LLMFlow for prompt engineering

**Override:** Projects can provide their own `docs/prompt-organization-convention.md` to customize standards.

**Source:** Originated in nida-institute/ears-to-hear repository

**Key standards:**
- 8-section structure (YAML → System Role → Principles → Examples → Data Sources → Input → Schema → Guardrails)
- Input data grounding (every output field must document its input source)
- No markdown fences in JSON output examples
- Examples consolidated in one section (not scattered)
- Heading hierarchy: `#` for major sections, `##` for subsections

---

## Adding New Conventions

When creating a new global convention:
1. Document it in a descriptive `.md` file
2. Add entry to this README
3. Update relevant skills to reference it
4. Note the originating project in the header
