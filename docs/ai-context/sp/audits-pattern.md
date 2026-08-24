# Audits Pattern for AI Assistants

> **Use this file for:** Guidance on executing audit procedures for pipeline outputs, understanding the docs/audits vs project/audits split, and when to invoke audit checklists.

---

## Directory Structure

```
docs/audits/           ← Procedures (version-controlled, reusable)
  INDEX.md             ← Dispatch table: artifact type → trigger phrase → checklist file
  audit-passage.md     ← Example: 20–60 line checkbox-only procedure
  audit-book-summary.md
  audit-verse-atlas.md

project/audits/        ← Records (per-run findings, not committed)
  audit-MRK-6-14-29.md      ← Per-artifact: one file per passage/output audited
  audit-leadersguide.md     ← Per-pipeline: one rolling file per pipeline (see below)

project/plans/         ← Implementation tasks (per-pipeline rolling files)
  leadersguide-plan.md      ← Tasks for the leader's guide pipeline
```

**Key distinction:**
- `docs/audits/` = **how to audit** (procedures, stable across runs)
- `project/audits/` = **what you found** — two types:
  - **Per-artifact records** (`audit-<PASSAGE>.md`) — one file per passage or output; retained as a record
  - **Per-pipeline rolling files** (`audit-{pipeline-name}.md`) — one file per pipeline, updated in place; items removed when resolved; git history is the audit trail
- `project/plans/` = **what will be done** (`{pipeline-name}-plan.md`) — tasks checked off and removed when done

See `~/.sp/disciplines/project-tracking.md` (installed by `sp init`) for the full rolling-file convention, and `~/.sp/disciplines/sp-workflow.md` for the pipeline being the unit it rolls per.

---

## Workflow for AI Assistants

### When the user says:
- "audit this per the checklist"
- "audit this passage"
- "audit the verse atlas"

### Do this:
1. **Open `docs/audits/INDEX.md`** and find the matching trigger phrase
2. **Open the corresponding checklist file** (e.g. `audit-passage.md`)
3. **Read the entire checklist** before evaluating the artifact
4. **Execute each checkbox** in order, NOT skipping any
5. **Write findings** to `project/audits/audit-<identifier>.md` (e.g. `audit-MRK-6-14-29.md`)

### DO NOT:
- Paraphrase the checklist from memory — open the file
- Skip checkboxes or reorder them
- Write audit findings into `docs/audits/` (that's for procedures only)
- Add explanatory prose when executing a checkbox (just mark pass/fail)

---

## Checklist File Format

**Constraints:**
- 20–60 lines max
- **STOP conditions** in bold at the top (hard blockers)
- `- [ ]` checkbox format only — no paragraphs explaining why something matters
- Shell commands in code blocks (if applicable)
- Pass/Fail criteria at the end

**Example structure:**

```markdown
# Audit: [Artifact Type]

**STOP if:**
- [Hard blocker condition 1]
- [Hard blocker condition 2]

## Checklist

- [ ] [Specific verifiable criterion]
- [ ] [Another criterion]
- [ ] [Another criterion]

## Shell Commands

\```bash
# Command to help verify something
find output/ -name "*.md" | wc -l
\```

## Pass/Fail Criteria

**Pass:** All checkboxes marked, no STOP conditions.
**Fail:** Any STOP condition OR 2+ unchecked boxes.
```

---

## Why This Pattern Works

**Problem:** Long audit documents get skimmed. AI assistants read the top and guess at the rest.

**Solution:**
- Short checklist files (20–60 lines) are read entirely
- Trigger phrases in `INDEX.md` make it explicit which file to open
- Checkbox-only format prevents prose bloat
- STOP conditions prevent wasted effort on broken artifacts

---

## Adding New Audit Procedures

1. Create `docs/audits/audit-<artifact-type>.md` (follow format above)
2. Add row to `docs/audits/INDEX.md` dispatch table
3. Test by asking an AI assistant to "audit [artifact] per the checklist"
4. If the assistant skips the file or paraphrases, the trigger phrase needs adjustment

---

## Audit Records Naming Convention

Findings should be written to:
```
project/audits/audit-<BOOK>-<CHAPTER>-<VERSES>.md
project/audits/audit-<scope>-<pipeline-name>.md
```

Examples:
- `project/audits/audit-MRK-6-14-29.md` (specific passage)
- `project/audits/audit-full-NT-storyflow.md` (full scope)
- `project/audits/audit-LUK-1-semlex-multipass.md` (single chapter, specific pipeline)

Include:
- Date of audit
- What passed/failed
- Specific findings (line numbers, examples)
- Recommended fixes (if applicable)

---

## Reference Implementation

See `nida-institute/Ears-to-Hear` repo (`LLMFlow/docs/audits/`) for working examples of dispatch-driven audit procedures.
