---
name: authorize
description: |
  **WORKFLOW SKILL** — Authorization workflow. Declare scope before touching any file.
  Verify authorization, state exactly what will change and what will not, and
  get Captain sign-off before implementation begins.
  USE FOR: before starting any non-trivial task; before touching a file that wasn't
  explicitly named; whenever tempted to "improve" something adjacent to the task.
  DO NOT USE FOR: read-only tasks (audit, research, answering questions).
applyTo:
  - "**/*.py"
  - "**/*.yaml"
  - "**/*.gpt"
  - "**/*.json"
---

# Authorization Workflow

## Core Principle: Captain Decides, Crew Implements

Design decisions belong to the Captain. They live in GH issues, plans, and audits.
The AI's job is to implement exactly what is specified — nothing more, nothing added
"while I'm in here." Every change to every file requires prior authorization.

Run this skill **before opening any file to edit**.

---

## Step 1: State the Authorization

Identify what authorizes this work. One of:

- **GH issue:** `gh issue view <N>` — quote the relevant requirement
- **Explicit user message:** quote the exact instruction from this session
- **Audit finding:** name the audit doc and the specific item

If no authorization exists: **stop**. Do not proceed. Say:
> "I don't have authorization for this change. Should I file an issue first?"

---

## Step 1b: Comments That Reflect Design Must Reference a GH Issue

Any comment added during this work that explains *why* something is done a certain way
(a design decision, a constraint, a rule) **must** include a GH issue reference:

```python
# Scenes are the leaf level — segments are not rendered. See #73, #77.
```

A comment without an issue reference is not a design authority. If the AI reads it in
a future session, it will not know whether it reflects an intentional decision or a
stale assumption. Issue references make design decisions traceable and durable.

If no issue exists for the design decision: file one before writing the comment.

---

## Step 2: Declare the Scope

State exactly:

**What will change:**
- File: `path/to/file.py` — what specifically will be modified (function, lines, behavior)
- File: `path/to/other.yaml` — what specifically will be modified

**What will NOT change** (name things that might be tempting but are out of scope):
- Any file not listed above
- Any behavior not explicitly requested
- Any "while I'm in here" cleanup or improvements

**What the change will NOT do:**
- Will not add features beyond what was asked
- Will not refactor surrounding code
- Will not fix adjacent issues noticed during implementation

---

## Step 3: Ask About Written Record

Ask the Captain:
> "Should I create a plan file in `project/plans/`, a GH issue, or neither before we proceed?"

Wait for the answer. Do not proceed to sign-off until the Captain has responded.
If the Captain says to create one, create it and show it before asking for sign-off.

---

## Step 4: Get Sign-Off

Present the scope declaration to the Captain and wait for explicit confirmation before
touching any file.

If the Captain says "yes" or "go ahead": proceed with exactly the declared scope.

---

## Step 5: Write the Failing Test First

Before touching any implementation file, determine whether the change is testable:

- **If testable:** write the failing test first, confirm it fails, then implement.
- **If not testable** (e.g. prompt files, pipeline YAML, documentation): state explicitly why testing doesn't apply before proceeding.

Do not skip this step silently.

If during implementation you discover something that seems worth fixing that wasn't
in scope: **stop, report it, ask**. Do not fix it in the same change.

---

## Step 6: Verify on Completion

After implementation, diff against the declared scope:

- [ ] Every changed file was listed in Step 2
- [ ] No file was changed that wasn't listed
- [ ] No behavior was added beyond what was declared
- [ ] No "while I'm in here" changes crept in

If any deviation occurred: explain what happened and why before declaring done.

---

## Anti-Patterns This Skill Prevents

**Freelancing:** Noticing something adjacent and fixing it without authorization.
> ❌ "While I was in `book_tree.py`, I also cleaned up the color constants."
> ✅ "I noticed the color constants could be cleaned up — want me to file an issue?"

**Scope creep during implementation:** Starting with one task and expanding.
> ❌ "I updated the function signature and also refactored the callers."
> ✅ "I updated the function signature. The callers will need updating too — separate task?"

**Substitution:** Replacing something the Captain designed with something the AI designed.
> ❌ "I couldn't find the original, so I wrote a replacement."
> ✅ "I can't find the original. Where should I look, or do you want to recreate it?"

**Regression by omission:** Consolidating code and silently dropping a feature.
> ❌ Rewrites a pipeline step, leaving out a step that was there before.
> ✅ Diffs the old and new version and flags any removed behavior for confirmation.

---

## Related Skills

- `/commit-ready` — Post-work gate: verify authorization, tests, changelog before committing
- `/audit-prompts` — Run before editing any `.gpt` file
- `/audit-pipeline` — Run when pipeline structure changes
- `/audit-code` — Run before committing new plugins
