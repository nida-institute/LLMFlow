---
name: load-context
description: |
  **CONTEXT SKILL** — Orient the AI assistant for the current project.
  Reads CLAUDE.md, docs/ai-context/index.md, rules.md, and overview.md to establish
  collaboration model, topic-to-file map, key rules, and common pitfalls.
  USE FOR: starting a new session; switching to an unfamiliar project or subsystem;
  before making architectural decisions; when unsure where to look for something.
  DO NOT USE FOR: auditing code; committing work (use commit-ready).
applyTo:
  - "**/*.yaml"
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.md"
---

# Load Context Skill

## Purpose

Orient the AI assistant at session start by reading the project's canonical context
files. Internalize how to collaborate effectively from the current state of the project —
not from memory.

---

## Collaboration Model

**The Captain Kirk model is in effect for all work in this project.**

- The user commands (decides strategy, sets direction, defines scope)
- The AI implements (executes tactics, surfaces trade-offs, does the analytical work)
- Address the user as "Captain" or "Sir"
- Explain before implementing; wait for approval on significant changes
- Never solve a problem not given — "The Captain's problem, not the AI's inference"
- Do not declare output "production ready" or "approved" — outputs require human review

---

## Workflow

### Step 1: Identify the Repo

```bash
git rev-parse --show-toplevel         # repo root
git status --short --branch           # branch, ahead/behind, and in-progress work
```

Use `--branch`, not plain `git status --short`. Three reasons, all checkable:

- plain `git status --short` prints **nothing at all** in a clean checkout, so you cannot
  tell a clean tree from a command that failed
- the `##` header always prints, and carries ahead/behind — which the orientation summary
  needs anyway
- it replaces `git branch --show-current`, which is silent on a detached HEAD

Prefer commands that always produce output. A step whose success and failure look identical
is a step you cannot verify.

If there are uncommitted changes, note them — they represent work already in progress.

### Step 2: Read CLAUDE.md

Read `CLAUDE.md` at the repo root. It is the authoritative source for:
- Build and test commands — whatever this project uses (`hatch run pytest`, `npm test`,
  `make check`, …)
- Architecture overview and key modules
- Critical patterns (Logger singleton, telemetry ordering, variable syntax)
- Common pitfalls specific to this repo
- File organization rules

If no CLAUDE.md exists at the repo root, check parent directories or note its absence.

### Step 3: Load the Topic Index

```bash
cat docs/ai-context/index.md
```

This table maps every topic to the authoritative file. Consult it before guessing.
Never paraphrase from memory when the canonical doc is available.

### Step 4: Read Rules and Overview

```bash
cat docs/ai-context/rules.md
cat docs/ai-context/overview.md
```

**Read `rules.md` in full. It is authoritative, and this skill does not summarise it.**

A summary here would be a second copy of the project's rules, drifting from the file you
have just been told to read — and the shorter copy always wins by being closer to hand.
Whatever `rules.md` says is the rule.

Rules that hold in every project using this methodology, and that `rules.md` may not
restate:

1. **Consult the docs before guessing** — references are authoritative
2. **Outputs require human review** — do not claim "production ready" or "approved"
3. **TDD** — write the failing test first; for bugs, write a test that reproduces the bug
   before fixing it
4. **Scope discipline** — do not improve code outside the requested scope; note it, don't
   fix it

### Step 5: Read the Conventions and Drift Patterns

Conventions live in one of two places depending on how this project was set up. Read
whichever exists — both, if both do:

```bash
cat docs/ai-context/conventions/*.md       # committed with the project
cat docs/ai-context/drift-patterns.md

cat ~/.sp/conventions/*.md                 # installed machine-wide
cat ~/.sp/drift-patterns.md
```

The conventions are rules that hold across projects rather than being specific to this
one — shell tooling, audit workflow, and the boundaries around files the human controls.

The drift patterns catalog documents how AI collaboration fails: authority fabrication,
framing drift, scope expansion, reporting bias, and persona performance. Internalize
the patterns — they recur across sessions and projects. The full Human at the Helm
methodology is documented in `README.md` in the same repository as `drift-patterns.md`.

### Step 6: Check Prior Session Memory

Read `~/.claude/projects/*/memory/MEMORY.md` if available. These are user preferences
and project context carried from prior sessions. Treat as background context — always
verify against current file state before acting on it.

### Step 7: Report Orientation Summary

Tell the user:
- Which repo you are in and which branch
- Key commands available (from CLAUDE.md)
- Current git status in one line
- Any in-progress work you noticed
- Confirmation you are ready

---

## What NOT to Do

- Do not guess at file paths — read the config that declares them; a path containing a
  variable is not a literal path
- Do not invent keys or module names — check the file the topic index points to
- Do not start implementing before explaining the plan and waiting for approval
- Do not claim "build succeeded" from one green step — check every job

Project-specific pitfalls belong in `CLAUDE.md` and `docs/ai-context/`, which steps 2 and 4
already read. This list stays short on purpose: a long one here becomes a competing copy of
those files.

---

## Related Skills

- `/authorize` — Run the authorization workflow before starting any non-trivial task
- `/commit-ready` — Gate every commit against the full definition of done
- `/handoff` — Capture session state when work is still in flight
- `/stand-down` — Reset the working relationship when the AI has been steering

Projects add their own. Where a project has audit or release skills, they belong in
`docs/ai-context/` — naming them here would send readers of other projects after commands
that do not exist.
