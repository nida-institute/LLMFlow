# Consumer Repo Layout Convention

## The `project/` directory

LLMFlow consumer repositories (repos that *use* the `sp` CLI to run pipelines)
should maintain a `project/` directory for active working documents.  This keeps
ephemeral material out of `docs/` and off the repo root.

```
project/
  TODO.md          ← single active task list for this repo
  audits/          ← per-run quality audits, named by passage or date
  plans/           ← in-flight design docs; archived or deleted once implemented
```

### Rules of thumb

| Directory | What goes here | Lifecycle |
|---|---|---|
| `project/TODO.md` | Active tasks, backlog, links to open issues | Continuously updated |
| `project/audits/` | Quality reviews tied to a specific pipeline run or passage (e.g. `audit-MRK-12.md`) | Discard once issues are filed on GitHub |
| `project/plans/` | In-flight design notes for prompt restructuring, new features, data-source changes | Move to `docs/decisions/` as an ADR, or delete, once implemented |

### Distinction from `docs/`

- `docs/` — **stable reference**: architecture, ADRs, AI context index, prompt
  engineering notes.  Files here are meant to persist.
- `project/` — **active work**: what is being done right now, audits of recent
  runs, designs in flight.  Files here are expected to change or disappear.

## The `docs/decisions/` directory (optional)

For teams that want an Architecture Decision Record trail:

```
docs/decisions/
  001-use-basex-for-corpus-queries.md
  002-macula-hebrew-as-primary-source.md
```

When a plan in `project/plans/` is implemented, move it here with a sequential
number prefix and a one-line summary header.  This is optional — small repos can
skip it and just delete the plan.

## For AI assistants working in consumer repos

When asked about design decisions in progress → look in `project/plans/`.

When asked to record a quality audit → write to `project/audits/<passage>-<date>.md`.

When asked where to put a TODO → `project/TODO.md` (one file, not scattered).

Do **not** put in-progress notes in `docs/` — that directory is for stable reference.

### DO NOT modify the LLMFlow dependency in `pyproject.toml`

Consumer repos reference LLMFlow as a local editable install so that changes to the LLMFlow dev tree flow through immediately. **Never reformat, simplify, or otherwise touch this line**, even when editing `pyproject.toml` for other reasons. Reverting it to a non-editable reference causes silent stale-install bugs that are hard to diagnose (e.g. `response_format` crashes, missing features). This rule exists because AI agents have repeatedly broken this — April 2026.
