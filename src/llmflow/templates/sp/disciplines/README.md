# Global Disciplines

This directory contains shared disciplines used across multiple projects.

They come in two kinds, and the split is deliberate. **General disciplines** are practice that
holds in any repository in any language; they are the ones shared with Human at the Helm.
**Scripture Pipelines disciplines** are about this engine — its CLI, its prompt files, its
pipeline YAML — and stay here. A discipline that mixes the two gets split rather than filed
under whichever half is larger; that is what `sp-workflow.md` and `workflow.md` are.

---

## General Disciplines

### workflow.md
Workflow rules that hold in every project on this machine, whatever it is written in.

**Key standard:** Prefer the file tools over bash; never `cd /path && command` — pass the path as an argument; never pipe git output. Audit findings need exact quotes and locations, and verdicts belong to the human. Design comments cite a GH issue. `docs/ai-context/`, project memory files and CLAUDE.md belong to the human and are never written without approval.

### design-authority.md
The human is the designer; the AI is not.

**Key standard:** Only what the human wrote or agreed to carries design authority — design documents, GH issues and PR bodies they authored, explicit agreement in conversation. Existing code behaviour, docstrings, AI-generated rationale and prior unreviewed AI choices carry none. Before implementing, name the authority; if you cannot, stop and ask. When the human contradicts a comment the AI wrote, the human is right.

**Source:** nida-institute/human-at-the-helm, which is upstream for this file. This engine carried a 49-line summary of it until 2026-08-21; Helm `24fd64f` had already grafted the two points that summary added, on the principle that one subject must not live in two documents.

### surface-decisions.md
Surface genuine decisions to the Captain (whoever directs the project) and stop; never proceed on an assumption.

**Key standard:** A genuine decision (scope boundary, design choice, anything with real consequence) → name it crisply, make sure the Captain sees it, and halt for the Captain's call. Mechanical/low-stakes work proceeds without gating. Streaming decisions past the Captain and acting on an assumption are both drift.

**A well-formed request:** if you don't give the Captain the information needed to decide, you haven't got a well-formed request for a decision. State what each option does, what it costs, and which existing rule bears on it. **No jargon** — use the vocabulary of the project and of the Captain; a term he has to decode blocks the decision.

**Asking in a document:** pose the question, then leave a line containing only `=>` for the answer. Never checkboxes or underline blanks — neither is fillable by someone editing the file. Once the Captain has written after a `=>`, that text is the ruling: quote it, never reword it.

### working-for-a-person.md
Ask what the work is for and who it serves, before choosing an approach; and spend the machine's resources rather than the human's.

**Key standard:** Before the first substantial artifact, say who it is for and what would make it good for them. If you cannot, that is the question to ask — about the goal, in their words, not about implementation details in your own. The option space belongs to whoever posed the question: a third option you invented is a design decision smuggled in as helpfulness. Deliver the kind of thing that was asked for — an issue raising a question records the question, it does not answer it.

**The cost function:** their attention is scarce; compute, tokens, a re-run and a rewritten file are cheap. Where permission is needed before spending money, the constraint is on the act and not on the recommendation — say what the spend buys and let them decide. Your own output is a cost too: answer the size of the question, and treat a correction as a correction rather than as a prompt for more analysis.

**Why:** an AI protects whatever it can count and spends the one thing it cannot see. The visible units are almost never the scarce ones.

### github-authority.md
What an AI may and may not do to a GitHub account, in every project.

**Key standard:** Reading, creating issues, commenting, branching, pushing and opening PRs need no per-action approval. Merging or approving a PR, assigning work to a person, changing collaborators or org settings, closing an issue not created in the same turn, and pushing to a protected branch are hard stops requiring explicit instruction each time. "It seemed like the next logical step" is not authorisation.

**Identity is yours, not the tooling's:** record your machine user account somewhere that belongs to you alone, which no install step overwrites and nothing ships. Where that is in this project is stated in `sp-workflow.md`.

**Why:** in April 2026 an agent applied PRs and assigned tasks to team members unasked.

### project-tracking.md
One rolling file per subsystem for audit findings and implementation plans.

**Key standard:** `project/audits/audit-{subsystem}.md` and `project/plans/{subsystem}-plan.md`, updated in place. Dates go on individual items, never in filenames; git history is the audit trail, so dated copies do not accumulate. Audits record what was found; plans record what will be done — the two stay separate. A project names its own unit; here it is the pipeline, per `sp-workflow.md`.

---

## Scripture Pipelines Disciplines

### sp-workflow.md
The rules specific to this engine, on top of `workflow.md`.

**Key standard:** The CLI is `sp run` / `sp lint`, not `llmflow` — that prefix is stale. Never run `sp run` unasked; the human decides when pipelines run and pays for it. The unit project tracking rolls per is the pipeline. The machine user account is recorded in `~/.sp/user-context/`.

### llmflow-prompt-organization.md
Standard organization pattern for Scripture Pipelines `.gpt` prompt files.

**Used by:**
- audit-prompts skill (`~/.sp/skills/audit-prompts/`)
- Any project using Scripture Pipelines for prompt engineering

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

### tests-and-audits.md
Tests and audits answer different questions, and must not be blurred.

**Key standard:** unit tests under `tests/` answer *"does the code work?"* against small
synthetic fixtures; audit scripts under `scripts/` answer *"how good is this output?"* against
real generated artifacts. A test that loads a built artifact from `outputs/` is the
anti-pattern — it is slow, it breaks when a better prompt changes the output, it cannot run on
a fresh clone, and it treats derived output as a specification. The test to apply: *would
regenerating the output with a better prompt make this fail?* If yes, it is an audit.

**Source:** recovered 2026-08-24 from a deleted `~/.claude` memory file written in
nida-institute/ears-to-hear.

### sp-debugging.md
Project-neutral debugging practice for any `sp` pipeline.

**Key standard:** `linter_config.log_level: debug` makes every `type: llm` step dump its rendered request and raw response to disk — there is no `--debug` flag and no environment variable. Dumps land under `<intermediate_file_directory>/debug/<pipeline_name>/` and are cleared each run.

**Source:** Generalized from nida-institute/ears-to-hear `docs/architecture/debugging.md`

### consumer-repo-conventions.md
Rules for repositories that consume Scripture Pipelines rather than being it.

**Key standard:** never modify the Scripture Pipelines dependency line in a consumer repo's `pyproject.toml`. It must stay an editable install so local engine changes take effect without rebuilding; agents have repeatedly reverted it to non-editable while "tidying", producing stale-install bugs.

---

## Adding New Disciplines

When creating a new global discipline:
1. Document it in a descriptive `.md` file
2. Decide which kind it is — general, or specific to this engine. If it is both, write two files rather than one mixed one.
3. Add entry to this README, under the matching heading
4. Classify it in `tests/test_portable_disciplines.py`, which fails on an unclassified file
5. Update relevant skills to reference it
6. Note the originating project in the header
