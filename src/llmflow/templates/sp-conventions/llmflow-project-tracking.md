# LLMFlow Project Tracking Convention

## One Rolling File Per Pipeline

Maintain one rolling file per pipeline for both audit findings and implementation plans:

```
project/
  audits/
    audit-{pipeline-name}.md    # findings, updated in place
  plans/
    {pipeline-name}-plan.md     # tasks, checked off when done
```

**Examples:**
- `project/audits/audit-leadersguide.md`
- `project/audits/audit-build-book.md`
- `project/plans/leadersguide-plan.md`
- `project/plans/build-book-plan.md`

## Rules

- **Dates on items, not filenames.** Filenames are stable across time; dates appear on individual entries.
- **Rolling updates.** Check off completed items. Remove fully-resolved items. The file reflects current state.
- **Git history is the audit trail.** Do not accumulate dated copies — use `git log` to see history.
- **Audits and plans stay separate.** Audit files record what was found; plan files record what will be done.

## Distinction from Per-Artifact Records

This convention applies to **per-pipeline status files** — one file tracking the ongoing health and tasks for a pipeline.

It is distinct from **per-artifact audit records** (e.g., `project/audits/audit-MRK-6-14-29.md`), which record findings for a specific passage or output and follow the naming convention in `audits-pattern.md`.

| File | Purpose | Lifecycle |
|------|---------|-----------|
| `project/audits/audit-{pipeline}.md` | Pipeline-level findings (rolling) | Updated in place; items removed when resolved |
| `project/audits/audit-{PASSAGE}.md` | Artifact-level findings | One file per artifact; retained as record |
| `project/plans/{pipeline}-plan.md` | Implementation tasks (rolling) | Updated in place; items removed when done |

## Why This Works

Before adopting this pattern, projects accumulate many dated audit and plan files with overlapping content. It becomes unclear which file is current, findings are duplicated, and AI assistants have no stable place to look for project state.

A single rolling file per pipeline gives AI assistants and humans a stable, authoritative location. The file itself is always current; git history preserves the full record.
