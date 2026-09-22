---
name: load-context
description: |
  **CONTEXT SKILL** — Orient the AI assistant for the current project.
  Reads CLAUDE.md, the docs/ai-context indexes, rules.md and overview.md to establish
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

**Read these with the file tools, not the shell.** `Read` needs no approval and takes an
`offset` and `limit` for a large file; where the operator has configured the hook that enforces
reading with the file tools, `cat`, `head`, `tail`, `sed -n` and `less` are refused outright —
and a refused read that nothing notices is an empty context, not an error.

Two indexes: the project's own map, and the inventory of what its tooling ships.

- `docs/ai-context/project/index.md`
- `docs/ai-context/sp/index.md`
- `docs/ai-context/index.md` — the pre-split single index. Projects created before 2026-08-24
  still have it, and it is the one to read there.

A file that is not there is skipped in silence: a project has whichever layout it has.

This table maps every topic to the authoritative file. Consult it before guessing.
Never paraphrase from memory when the canonical doc is available.

### Step 4: Read Rules and Overview

The standard set is three documents — a map, a self-description, and constraints — and each half
carries all three. Step 3 read both maps; these are the other four, plus the pre-split flat
names for projects created before 2026-08-24. Every read is guarded, because a project has
whichever layout it has and a missing file must be skipped in silence.

With the file tools, as in Step 3. Constraints first — what the tooling holds every session to,
then what this project alone adds:

- `docs/ai-context/sp/rules.md`
- `docs/ai-context/project/rules.md`
- `docs/ai-context/rules.md` — pre-split

Then the self-description: what the tooling is, then what this project is.

- `docs/ai-context/sp/overview.md`
- `docs/ai-context/project/overview.md`
- `docs/ai-context/overview.md` — pre-split

**Read the project's half as carefully as the tooling's.** `docs/ai-context/project/rules.md`
holds constraints that apply in this project and nowhere else, and it is the file whose absence
used to send project-specific rules into a memory store nobody read.

**Everything else is reached through the index, not through this skill.** Topic documents are
named by their side's `index.md`. This skill never lists them: a list here would be a second copy
of the index, drifting from it, and the shorter copy always wins by being closer to hand.

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

### Step 5: Read every document the indexes name, and write the précis

The indexes name the topic documents; this skill still does not list them — a list here would
be a second copy of the index, drifting from it. Read **all** of them, both halves, with the
file tools.

Then write a précis: **one line per document**, each naming something only that document says —
a constraint, a threshold, a term it defines, a decision it records. Under two headings,
because the halves differ in authority and in lifecycle:

- **What the tooling holds me to** — `sp/`, generated. A finding here is a note to the engine,
  never a patch.
- **What this project holds me to** — `project/`, the project's own, and where local rules live.

Then two lines of your own:

- **What I must not do here** — the three constraints likeliest to bite this session's work.
- **What I could not read** — any document an index names that is missing or unreadable.

**Why a line per document, and why specific.** A précis of a file nobody opened reads generic
where every other entry is specific, so the omission is visible in one pass. This step exists
because a session that reads half the context and quotes the rest secondhand looks identical,
from the outside, to one that read all of it — until it proposes a rule that three unread files
already contain.

**Why the halves stay apart.** `sp/` is regenerated, so an edit there is lost and the fix
belongs upstream. `project/` is the project's own. A session that has merged them will either
treat engine documentation as locally negotiable, or treat project design as someone else's to
change.

The précis goes in the orientation summary, where it can be corrected before any work is built
on it. The cost of reading is paid once, at the start; the cost of starting out unaligned is
paid all session.

### Step 6: Read the Disciplines and Drift Patterns

Disciplines live in one of two places depending on how this project was set up. Read whichever
exists — both, if both do — with the file tools:

- `docs/ai-context/disciplines/README.md` — the index, when there is one
- every `.md` in `docs/ai-context/disciplines/` — committed with the project
- `docs/ai-context/drift-patterns.md`

**If this machine also carries a machine-wide install at `~/.sp/`**, read that too — the
project it belongs to keeps disciplines there rather than in the repository. A project
whose disciplines are committed alongside its code is complete without it, so an absent
`~/.sp/` means nothing is missing:

- every `.md` in `~/.sp/disciplines/`
- `~/.sp/drift-patterns.md`

The disciplines are rules that hold across projects rather than being specific to this
one — shell tooling, audit workflow, and the boundaries around files the human controls.

**Read the operational rules every session. Read the essays once.** Where that directory
has a README, it separates the two: short checkable rules a session is held to, and
longer documents explaining the failure modes behind them. The essays are written to be
read in full by a person adopting the methodology, not re-read at every session start —
so on a routine start, read the rules and treat the essays as reference. When the README
makes no such distinction, every file in the directory is a rule.

The drift patterns catalog documents how AI collaboration fails: authority fabrication,
framing drift, scope expansion, reporting bias, and persona performance. Internalize
the patterns — they recur across sessions and projects. The full Human at the Helm
methodology is documented in `README.md` in the same repository as `drift-patterns.md`.

### Step 7: Check Prior Session Memory

Read `~/.claude/projects/*/memory/MEMORY.md` if available. These are user preferences
and project context carried from prior sessions. Treat as background context — always
verify against current file state before acting on it.

### Step 8: Report Orientation Summary

Tell the user:
- Which repo you are in and which branch
- Key commands available (from CLAUDE.md)
- Current git status in one line
- Any in-progress work you noticed
- **The précis from Step 5**, both halves, and the two lines that close it
- Confirmation you are ready

The précis is the part that is checkable. Everything else above the human already knows; the
précis is what tells them whether this session read what it was given, and whether it read it
the way they meant — while there is still time to correct it.

---

## What NOT to Do

- Do not guess at file paths — read the config that declares them; a path containing a
  variable is not a literal path
- Do not invent keys or module names — check the file the topic index points to
- Do not start implementing before explaining the plan and waiting for approval
- Do not claim "build succeeded" from one green step — check every job

- Do not summarise a document you did not open. A précis line sourced from another document
  quoting it is the failure Step 5 exists to surface, and it reads generic where the others
  read specific

Project-specific pitfalls belong in `CLAUDE.md` and `docs/ai-context/`, which steps 2, 4 and 5
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
