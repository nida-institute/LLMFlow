---
name: handoff
description: |
  **COMMAND SKILL** — Write project/HANDOFF.md capturing session state so a fresh
  session (or /load-context) can resume cleanly.
  USE FOR: the end of a work session that has unfinished or multi-threaded work;
  before /exit when there is significant in-flight context.
  DO NOT USE FOR: session start (use load-context); trivial sessions with nothing
  meaningful in flight.
---

# Handoff

## Purpose

An AI session is ephemeral — it forgets everything when it ends. `HANDOFF.md` is the
durable bridge to the next session. This skill captures what the next session needs to
resume without re-deriving it. It is the bookend to `/load-context` (which reads it).

## Workflow

Write (or overwrite) `project/HANDOFF.md`, dated today, with these sections — concise
and scannable, a map rather than a narrative:

1. **Active threads** — what is being worked on, live thread first. For each: the goal,
   the current state, and the immediate next step.
2. **In flight / not yet done** — uncommitted changes, drafts, open PRs (with CI status),
   anything started but unfinished. Name the files, issue/PR numbers, and commit SHAs.
3. **Open decisions** — questions awaiting the Captain that block progress.
4. **Facts established this session** — non-obvious things learned, so they are not
   re-derived (with `file:line` or issue references).
5. **Key files & links** — the paths, issues, and docs the next session should open first.

## Rules

- Convert relative dates to absolute ("today" → the actual date).
- Be specific: file paths, issue/PR numbers, commit SHAs — never vague summaries.
- Report status honestly: done / in-flight / blocked. Do not claim work is finished
  that isn't.
- Keep it short enough that the next session reads the whole thing.
- After writing, tell the Captain the path and offer to `/exit`.

## Related

- `/load-context` — the bookend: orients a new session (reads `HANDOFF.md`, `project/TODO.md`,
  and the project's AI context).
