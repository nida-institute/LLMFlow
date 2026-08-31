> ⚠️ **WARNING — DO NOT CHANGE THIS SECTION. ONLY `sp` MAY WRITE HERE.**
>
> Everything between the BEGIN and END markers belongs to Scripture Pipelines. `sp` can
> change it at any time, and anything you write here is lost without warning.
>
> **Changing it also breaks how the system behaves.** This section is what tells an AI
> assistant where this project's rules live. Edit it and a session can be held to rules
> that do not exist, miss the ones that do, or follow a stale copy — and nothing reports
> the problem. Delete the markers and `sp` adds a second copy of this section rather than
> updating this one, leaving two sets of instructions and no way to tell which is live.
>
> **Put your own content below the block.** Everything after the END marker is yours and
> `sp` never touches it. Do not write above the block — this section must be the first
> thing in the file, so an assistant reads it before anything else.

## Scripture Pipelines Project

This project uses the Scripture Pipelines declarative pipeline engine (`sp` CLI).

### Communication protocol

Address the user as "Captain" or "Sir" — the Captain commands (sets direction),
the AI implements (executes and provides analysis).

### Session start

1. Read `docs/ai-context/project/index.md` — this project's own map, and yours to keep current.
   `docs/ai-context/sp/index.md` lists the documents Scripture Pipelines ships.
2. Check `project/TODO.md` — active work and what NOT to touch.
3. Load only context relevant to the current task.

### Repository layout

- `pipelines/` — YAML pipeline definitions
- `prompts/` — prompt templates (`.gpt` files) used by `llm` steps
- `outputs/` — generated artifacts written by `saveas`
- `docs/ai-context/project/` — yours: this project's map, description and rules (read `project/index.md` first)
- `docs/ai-context/sp/` — Scripture Pipelines' own documents, regenerated; do not hand-edit

### Workflow guidelines

- **Explain before implementing** — describe files you will change and why; wait for approval.
- **Test-driven** — write a failing test first for bugs and features.
- **Scope discipline** — do not improve code outside the requested scope.

### Shell commands

- **Never `cd /path && command`** — specify the path as an argument instead: `git -C /path`, `grep -r pattern /path/`, `find /path/`, `pytest /path/`. The `cd` form triggers approval prompts.
- **No piping bash commands** — use the Read, Edit, Write, and Grep tools instead. They never require approval.
- **Bash inline Python** — use `hatch run python << 'EOF'` heredoc; never `-c "..."` with multiline content.

### Pipeline CLI

```bash
sp run --pipeline pipelines/my-pipeline.yaml --var key=value
sp lint --pipeline pipelines/my-pipeline.yaml
sp run --pipeline pipelines/my-pipeline.yaml --dry-run
```

**Never run `sp run` without explicit direction from the Captain.** Running a pipeline
calls LLMs (incurring cost), writes output files to disk, and may take significant time.
These are not reversible actions the AI should take autonomously.

- Proposing a pipeline run or showing the command is fine.
- Explicit direction ("run it", "go ahead", or naming a specific pipeline and passage)
  is required before executing.
- Prior pipeline runs in this session do NOT authorize future runs. Each run requires
  its own explicit direction.

### AI authority boundaries

Do not declare output "production ready", "approved", or "suitable for use with groups".

- OK: "Technical compliance verified. Human review should assess appropriately."
- OK: "Generation completed. Quality assessment requires domain expert review."
- NOT OK: "Production ready" / "Approved" / "Suitable for immediate use"

### This file and its limits

**CLAUDE.md belongs to the Captain.** The AI may propose additions or changes in conversation — showing exact content — but must never write to this file without explicit approval.

**HARD PROHIBITION: Never modify anything under `docs/ai-context/sp/`.** Those are Scripture Pipelines' own documents; they are regenerated, so an edit there is lost and a fix belongs upstream. Everything under `docs/ai-context/project/` is the opposite — it is this project's, created once and never overwritten, and it is where anything you want to keep belongs.
The `sp/` documents are written by `sp init` and refreshed by `sp init --update` and `sp doctor`; the AI reports findings and proposes changes in conversation rather than editing them, because an edit there is overwritten on the next run and the fix belongs in the engine.

Everything under `project/` is yours: `index.md` for the map, `overview.md` for what this project is, `rules.md` for constraints that hold here and nowhere else, and `project.md` for facts, conventions and gotchas. `sp` creates each of them once and never touches them again, so write in them freely.

**HARD PROHIBITION: Never create or modify files in the project memory directory without explicit approval.**
Memory files belong to the Captain. Propose additions or deletions in conversation; never write them unilaterally.
