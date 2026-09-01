---
name: handoff
description: |
  **COMMAND SKILL** — Write project/HANDOFF.md capturing session state so a fresh
  instance (or /load-context) can resume cleanly and know what to do next.
  USE FOR: the end of a work session that has unfinished or multi-threaded work;
  before /exit when there is significant in-flight context.
  DO NOT USE FOR: session start (use load-context); trivial sessions with nothing
  meaningful in flight.
---

# Handoff

## Purpose

An AI session is ephemeral — it forgets everything when it ends. `HANDOFF.md` is the durable
bridge to the next instance. This skill captures what that instance needs to **resume and act**
without re-deriving it. It is the bookend to `/load-context` (which reads it).

## The adequacy standard — the bar to meet

A handoff is **adequate** when a fresh instance, reading only `HANDOFF.md` plus the repo, can:

1. **Name the single next action** — the one thing to do first — without guessing.
2. **Start it correctly** — it knows where the work lives (files, branch, commits), what state
   it is in, and how to continue.
3. **Not re-derive or contradict** — the decisions already made, and *why*, are stated, so the
   next instance neither reopens nor undoes them.
4. **Not step on a landmine** — it knows what is deliberately deferred, what not to touch, and
   what looks like a next step but isn't.

If a fresh instance would have to ask *"what do I do now?"* or would re-investigate something you
already settled, the handoff is **not** adequate. Write to that bar — not to a word count.

## Workflow

Write (or overwrite) `project/HANDOFF.md`, dated today (absolute date), **leading with the next
action**, then the supporting map:

1. **▶ NEXT ACTION** — first, at the top: the single most important thing to do next, concrete
   enough to start immediately (the command to run, the file to edit, the decision to get from
   the Captain). If threads run in parallel, rank them and say which is first.
2. **Active threads** — live thread first. For each:
   - **goal** — what it is for,
   - **state** — where it is now (honestly: done / in-flight / blocked),
   - **next step** — the immediate continuation,
   - **verify** — how the next instance *confirms* the state instead of trusting this file
     (e.g. "`hatch run pytest tests/X` is RED", "`npm test -- --run` in `web/` is RED",
     "`git log` shows `<sha>`", "read `docs/Y`"). Name the command this project actually
     uses — a verification the next instance cannot run is not a verification.
3. **In flight / not yet done** — uncommitted changes, drafts, open PRs (with CI status),
   anything started but unfinished. Name files, issue/PR numbers, commit SHAs, and the branch.
4. **Decisions** — open decisions awaiting the Captain (that block progress) *and* decisions
   already settled this session **with their why**, so the next instance neither reopens nor
   contradicts them.
5. **Do NOT / deferred** — landmines: work deliberately deferred, boundaries, and anything that
   looks like an obvious next step but should be left alone (say why).
6. **Key files & links** — the paths, issues, PRs, design docs, and external threads to open
   first.

## HANDOFF and the task list are different files

`HANDOFF.md` and `project/TODO.md` both answer "what next", which makes them look redundant. They
are not, and the line between them is what keeps either one true:

- **`HANDOFF.md` carries only what dies when the work is committed** — uncommitted files, which
  test is RED, the branch, the SHAs, drafts in flight. Commit and push everything cleanly and
  this file is nearly empty.
- **`project/TODO.md` carries everything that survives** — the queue, its order, the rulings
  still awaited. It is about the project, not the session, and it outlives both.

So **the NEXT ACTION points at the task list rather than restating it**, unless the next action
genuinely is "finish the uncommitted thing" — which, at the end of a session, it usually is.

**The failure this prevents:** a queue item written into the handoff as the next action goes
stale the moment somebody does it, and then misdirects every session afterwards. It reads as
current because the file is short and confident. Merging a pull request, cutting a release,
starting the next feature — all queue items. None of them belong here.

## Rules

- **Lead with the next action.** The next instance's first question is "what do I do?" — answer
  it in the first lines.
- Convert relative dates to absolute ("today" → the actual date).
- Be specific: file paths, issue/PR numbers, commit SHAs, branch names — never vague summaries.
- Report status honestly: done / in-flight / blocked. Never claim work is finished that isn't.
- **Prefer verifiable pointers over claims:** "test X is RED at `<sha>`" beats "the fix is
  nearly done." State claims the next instance can check, not ones it must trust.
- Keep it short enough that the next instance reads the whole thing — a map, not a narrative.

## Adequacy checklist — the handoff is done only when every box is true

Re-read the file as a fresh instance with no memory of this session, and check each. These test
the **outcome**, so a section filled with vague text does not pass:

- [ ] A fresh instance can name the single **NEXT ACTION** and start it, from this file + the
      repo alone.
- [ ] Every state claim is backed by a **verifiable pointer** — a test to run, a commit SHA, a
      `file:line` — not a bare assertion.
- [ ] All **uncommitted / unpushed** work is named (files, branch, what's RED/failing), with SHAs
      for what is committed.
- [ ] Every **settled decision** the next instance might reopen carries its *why*.
- [ ] **Landmines** are listed: deferred work, boundaries, and "looks like a next step but isn't."
- [ ] Nothing the next instance **cannot independently know** (audit results, external-thread
      state) is left implicit — it is captured or pointed to.
- [ ] It is **short enough to read whole** — a map, not a narrative.
- [ ] The NEXT ACTION is **session residue, not a queue item** — it names something that stops
      being true once this session's work is committed. If it would still be the next action a
      week from now, it belongs in the task list and this file should point at it.

Then tell the Captain the path and offer to `/exit`.

## Related

- `/load-context` — the bookend: orients a new session (reads `HANDOFF.md`, `project/TODO.md`,
  and the project's AI context).
