---
name: load-context
description: |
  **CONTEXT SKILL** — Orient the AI assistant for the current sp/LLMFlow project.
  Reads CLAUDE.md, docs/ai-context/index.md, rules.md, and overview.md to establish
  collaboration model, topic-to-file map, key rules, and common pitfalls.
  USE FOR: starting a new session; switching to an unfamiliar pipeline or project;
  before making architectural decisions; when unsure where to look for something.
  DO NOT USE FOR: auditing code (use audit-* skills); committing work (use commit-ready).
applyTo:
  - "**/*.yaml"
  - "**/*.py"
  - "**/*.gpt"
  - "**/*.md"
---

# Load Context Skill

## Purpose

Orient the AI assistant at session start by reading the project's canonical context
files. Internalize how to collaborate effectively from the current state of the project —
not from memory.

---

## Collaboration Model

**The Captain Kirk model is in effect for all sp/LLMFlow work.**

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

Each command above always produces output, whether run together or separately. That is a
requirement, not a coincidence: a command that returns nothing yields an empty result block, which
the API rejects with a bodyless 400 (LLMFlow#204).

`--branch` is what guarantees it — plain `git status --short` prints nothing at all in a clean
checkout. The `##` header always prints, and carries ahead/behind, which the orientation summary
needs anyway. It also replaces `git branch --show-current`, which is silent on a detached HEAD.

If there are uncommitted changes, note them — they represent work already in progress.

### Step 2: Read CLAUDE.md

Read `CLAUDE.md` at the repo root. It is the authoritative source for:
- Build and test commands (`hatch run pytest`, `sp lint`, etc.)
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

Key rules to internalize:
1. **Consult the docs before guessing** — references are authoritative
2. **Respect pipeline schema** — only use documented keys; no inventing fields
3. **Preserve Logger/telemetry conventions** — use `Logger()` from `llmflow.modules.logger`; start telemetry only after config merging
4. **Keep prompt contracts in sync** — every `prompt.requires` item must appear in `prompt.inputs`
5. **Verses are milestones, not containers** — source text is continuous running text with inline verse markers (e.g. `⌊1:1⌋ Καὶ... ⌊1:2⌋ καὶ...`), never an array of verse objects. Representing source text as `{"verses": [{"verse_ref": "...", "text": "..."}]}` is wrong.
6. **Every LLM step must have source text as an explicit named input** — no LLM is ever allowed to reason from a passage unless the actual text is right in front of it. A step missing `source_text` in its inputs is producing ungrounded output.
7. **Outputs require human review** — do not claim "production ready" or "approved"
8. **TDD** — write the failing test first; for bugs, write a test that reproduces the bug before fixing it
9. **Scope discipline** — do not improve code outside the requested scope; note it, don't fix it

### Step 5: Read Global SP Conventions and Drift Patterns

```bash
cat ~/.sp/conventions/*.md
cat ~/.sp/drift-patterns.md
```

The conventions are machine-global rules that apply to every SP project — CLI commands,
audit workflow, shell tooling, and file authority boundaries.

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

- Do not guess at file paths — read the pipeline YAML first; `${output_dir}` means paths are not literal
- Do not invent pipeline keys or module names — check `docs/llmflow-language.md`
- Do not start implementing before explaining the plan and waiting for approval
- Do not use `logging.basicConfig()` — breaks pytest's `caplog` fixture
- Do not confuse `${var}` (YAML pipeline) with `{{var}}` (template files)
- Do not import Jinja2 — the project uses its own template resolution
- Do not claim "build succeeded" based on `hatch build` alone — check all CI jobs

---

## Related Skills

- `/audit-prompts` — Audit `.gpt` prompt files and pipeline YAML before committing changes
- `/commit-ready` — Gate every commit against the full definition of done
- `/authorize` — Run the authorization workflow before starting any non-trivial task
- `/audit-pipeline` — Audit pipeline step contracts before committing new pipeline stages
- `/audit-output` — Audit pipeline output quality before closing output-related issues
