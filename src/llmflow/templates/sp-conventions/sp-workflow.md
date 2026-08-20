# SP Workflow Conventions

Rules specific to Scripture Pipelines projects. The general practice they sit on top of —
shell commands, audit workflow, files the human controls — is in `workflow.md`, which applies
to every project on this machine whatever it is written in.

---

## CLI Commands

The CLI commands are `sp run` and `sp lint`, not `llmflow run` or `llmflow lint`. The `llmflow` prefix is stale training data — it will not work.

```bash
sp run --pipeline pipelines/<name>.yaml --var key=value
sp lint --pipeline pipelines/<name>.yaml
sp run --pipeline pipelines/<name>.yaml --dry-run
```

Never run `sp run` without being asked. The human decides when pipelines run and pays the token cost.

---

## Project Tracking

The rolling-file structure is in `project-tracking.md`. Here the unit it rolls per is the
**pipeline**:

```
project/
  audits/
    audit-{pipeline-name}.md    # findings, updated in place
  plans/
    {pipeline-name}-plan.md     # tasks, checked off when done
```

**Examples:** `project/audits/audit-leadersguide.md`, `project/audits/audit-build-book.md`,
`project/plans/leadersguide-plan.md`, `project/plans/build-book-plan.md`.

**Distinct from per-artifact records.** A per-pipeline file tracks one pipeline's ongoing
health and tasks. A per-artifact record (e.g. `project/audits/audit-MRK-6-14-29.md`) records
findings for a specific passage or output and follows the naming convention in
`audits-pattern.md`.

| File | Purpose | Lifecycle |
|------|---------|-----------|
| `project/audits/audit-{pipeline}.md` | Pipeline-level findings (rolling) | Updated in place; items removed when resolved |
| `project/audits/audit-{PASSAGE}.md` | Artifact-level findings | One file per artifact; retained as record |
| `project/plans/{pipeline}-plan.md` | Implementation tasks (rolling) | Updated in place; items removed when done |

---

## Where the Machine User Account Is Recorded

`github-authority.md` says to keep the AI's GitHub account details somewhere that belongs to
you alone. Here that place is `~/.sp/user-context/` — that directory is never shipped and
`sp init` never overwrites it.
