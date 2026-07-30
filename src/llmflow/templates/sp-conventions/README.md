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

### llmflow-pipeline-steps.md
Convention for documenting pipeline steps, including the `description:` field.

**Key standard:** Use `description: |` (YAML block scalar) on steps for multi-line human commentary. The `description` field is whitelisted by the linter and ignored by the runner. YAML `#` comments are reserved for short inline notes and section dividers only.

### surface-decisions.md
Surface genuine decisions to the Captain (whoever directs the project) and stop; never proceed on an assumption.

**Key standard:** A genuine decision (scope boundary, design choice, anything with real consequence) → name it crisply, make sure the Captain sees it, and halt for the Captain's call. Mechanical/low-stakes work proceeds without gating. Streaming decisions past the Captain and acting on an assumption are both drift.

---

## Adding New Conventions

When creating a new global convention:
1. Document it in a descriptive `.md` file
2. Add entry to this README
3. Update relevant skills to reference it
4. Note the originating project in the header
