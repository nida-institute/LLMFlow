# AI Context Bundle

This folder provides the "pinned context" we share with GPT/Claude when they help on the LLMFlow project. It summarizes the repo's purpose, doc index, and guardrails so assistants start with the same baseline.

## How to Use
1. **Pin these files in order** when opening a new chat with an AI assistant:
   - `overview.md`
   - `index.md`
   - `rules.md`
2. Mention that all other documentation lives under `docs/` (tutorial, architecture, language spec, etc.).
3. When the assistant asks for more detail, point it to the relevant doc referenced in `index.md`.

## Maintenance Plan
- **When?** After every significant doc restructure or release.
- **Checklist:**
  1. Review `overview.md` and ensure links (INSTALL, tutorial, architecture, language spec) still exist.
  2. Update `index.md` table if files were renamed/added.
  3. Confirm `rules.md` still matches current working agreements (logger usage, telemetry order, etc.).
  4. Update the "Last updated" date in `overview.md`.
- Optionally run `llmflow context` to regenerate additional context packs if the CLI gains that command.

Keeping this bundle current ensures AI helpers follow the same conventions as the engineering team.
