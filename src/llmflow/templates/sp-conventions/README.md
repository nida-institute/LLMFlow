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

**A well-formed request:** if you don't give the Captain the information needed to decide, you haven't got a well-formed request for a decision. State what each option does, what it costs, and which existing rule bears on it. **No jargon** — use the vocabulary of the project and of the Captain; a term he has to decode blocks the decision.

**Asking in a document:** pose the question, then leave a line containing only `=>` for the answer. Never checkboxes or underline blanks — neither is fillable by someone editing the file. Once the Captain has written after a `=>`, that text is the ruling: quote it, never reword it.

### llmflow-project-tracking.md
One rolling file per pipeline for audit findings and implementation plans.

**Key standard:** `project/audits/audit-{pipeline}.md` and `project/plans/{pipeline}-plan.md`, updated in place. Dates go on individual items, never in filenames; git history is the audit trail, so dated copies do not accumulate. Audits record what was found; plans record what will be done — the two stay separate.

### design-authority.md
The user is the designer; the AI is not.

**Key standard:** Only the user's design documents and explicit agreement carry design authority. Existing code behaviour, docstrings, AI-generated rationale, and prior AI choices carry none. Before writing code, name the design document that specifies it — if you cannot, stop and ask.

**Source:** Originated in nida-institute/discourse-flow

### sp-debugging.md
Project-neutral debugging practice for any `sp` pipeline.

**Key standard:** `linter_config.log_level: debug` makes every `type: llm` step dump its rendered request and raw response to disk — there is no `--debug` flag and no environment variable. Dumps land under `<intermediate_file_directory>/debug/<pipeline_name>/` and are cleared each run.

**Source:** Generalized from nida-institute/ears-to-hear `docs/architecture/debugging.md`

### github-authority.md
What an AI may and may not do to a GitHub account, across all registered projects.

**Key standard:** Reading, creating issues, commenting, branching, pushing and opening PRs need no per-action approval. Merging or approving a PR, assigning work to a person, changing collaborators or org settings, closing an issue not created in the same turn, and pushing to a protected branch are hard stops requiring explicit instruction each time. "It seemed like the next logical step" is not authorisation.

**Identity is yours, not the engine's:** record your machine user account in `~/.sp/user-context/`, which never ships and is never overwritten.

**Why:** in April 2026 an agent applied PRs and assigned tasks to team members unasked.

### consumer-repo-conventions.md
Rules for repositories that consume LLMFlow rather than being it.

**Key standard:** never modify the LLMFlow dependency line in a consumer repo's `pyproject.toml`. It must stay an editable install so local engine changes take effect without rebuilding; agents have repeatedly reverted it to non-editable while "tidying", producing stale-install bugs.

### sp-workflow.md
Machine-global workflow rules for every `sp` project.

**Key standard:** The CLI is `sp run` / `sp lint`, not `llmflow` — that prefix is stale. Never run `sp run` unasked; the human decides when pipelines run and pays for it. Prefer the file tools over bash, never `cd /path && command`, and never pipe git output. Audit findings need exact quotes and locations, and verdicts belong to the human.

---

## Adding New Conventions

When creating a new global convention:
1. Document it in a descriptive `.md` file
2. Add entry to this README
3. Update relevant skills to reference it
4. Note the originating project in the header
