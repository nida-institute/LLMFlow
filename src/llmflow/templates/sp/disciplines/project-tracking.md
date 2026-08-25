# Project Tracking Convention

## One Rolling File Per Subsystem

Maintain one rolling file per subsystem for both audit findings and implementation plans:

```
project/
  audits/
    audit-{subsystem}.md    # findings, updated in place
  plans/
    {subsystem}-plan.md     # tasks, checked off when done
```

**A project names its own unit.** "Subsystem" is whatever this project tracks work by — a
service, a package, a build target, a data flow. Name it once and use the same name in both
directories, so a reader looking for the plan can guess it from the audit.

**Examples:** `project/audits/audit-importer.md`, `project/audits/audit-web-client.md`,
`project/plans/importer-plan.md`, `project/plans/web-client-plan.md`.

## Rules

- **Dates on items, not filenames.** Filenames are stable across time; dates appear on individual entries.
- **Rolling updates.** Check off completed items. Remove fully-resolved items. The file reflects current state.
- **Git history is the audit trail.** Do not accumulate dated copies — use `git log` to see history.
- **Audits and plans stay separate.** Audit files record what was found; plan files record what will be done.

## Distinction from Per-Artifact Records

This convention applies to **per-subsystem status files** — one file tracking the ongoing health and tasks for a subsystem.

It is distinct from **per-artifact audit records**, which record findings for one specific
output and are retained as a record of that output rather than updated in place. A project
that produces artifacts worth auditing individually states its own naming convention for
them.

| File | Purpose | Lifecycle |
|------|---------|-----------|
| `project/audits/audit-{subsystem}.md` | Subsystem-level findings (rolling) | Updated in place; items removed when resolved |
| `project/audits/audit-{artifact}.md` | Artifact-level findings | One file per artifact; retained as record |
| `project/plans/{subsystem}-plan.md` | Implementation tasks (rolling) | Updated in place; items removed when done |

## Why This Works

Before adopting this pattern, projects accumulate many dated audit and plan files with overlapping content. It becomes unclear which file is current, findings are duplicated, and AI assistants have no stable place to look for project state.

A single rolling file per subsystem gives AI assistants and humans a stable, authoritative location. The file itself is always current; git history preserves the full record.
