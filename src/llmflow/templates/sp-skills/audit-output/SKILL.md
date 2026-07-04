---
name: audit-output
description: |
  **WORKFLOW SKILL** — Audit pipeline output files against the project's docs/audits/ checklist.
  Covers final outputs AND intermediate outputs. Core focus: detecting where LLMs are freelancing
  (generating from training knowledge instead of from the data they were given) and verifying that
  each step actually leverages the output of prior steps.
  DO NOT USE FOR: modifying output files; modifying prompts; making pipeline changes.
toolRestrictions:
  forbidden:
    - replace_string_in_file
    - multi_replace_string_in_file
    - create_file
  reasoning: "Read-only audit skill. Identifies issues; human decides whether/how to fix."
---

# Audit Output Skill

## Tool Protocol — No Approval Required

**Use `Read` for all file content. Do not use `cat`, `grep`, `jq`, or `awk`.**

The `Read` tool never requires approval. Bash commands do.

| What you need | How to do it without bash |
|---|---|
| Read a file | `Read path/to/file` |
| Find a keyword in a file | `Read` the file; search in context |
| Inspect a JSON field | `Read` the JSON; extract in context |
| Count items | `Read` the file; reason about it |

The one bash that remains is `ls` for file discovery — finding which debug or
intermediate files exist for a given passage. Everything else uses `Read`.

---

## Core Principle: My Findings Require Human Review

My audit results are a starting point — not conclusions. For every finding, I provide the
specific quote and file location so the human can verify independently. I never report bare
pass/fail. If I am uncertain, I say so explicitly and flag it for human judgment.

The human reads what I cite and decides if they agree. If they disagree, that is an editorial
note: either the checklist criterion is wrong, or my application of it was.

**I never declare output "clean," "ready for review," or "production ready."** That judgment
belongs to the human.

---

## Two Layers of Audit

Every output audit has two layers:

### Layer 1 — Final Output Quality
Run the project's checklist from `docs/audits/` for this output type. Report findings with
specific quotes and line numbers.

### Layer 2 — Grounding and Freelancing Detection
This is the more important layer. Regardless of whether the final output looks good,
verify that the model actually used the data it was given.

---

## Freelancing Detection

**Freelancing** is when an LLM generates content from its training knowledge instead of from
the data it was given. It looks like good output. It passes format checks. It fails when you
compare it against the input data that was supposed to drive it.

### Signs of freelancing

- **Generic content**: Could describe any passage of this type, not this specific text
  ("The crowd was restless" — is that in sensory_inventory, or invented?)
- **Plausible cultural detail not in the data**: Historical background that sounds right
  but doesn't appear in any background item
- **Emotions not grounded in heart_movements**: Characters feeling things the data doesn't say
- **Sensory details invented**: Smells, textures, sounds not present in sensory_inventory
- **Tension threads not matched**: Claims about narrative arc that don't correspond to
  tension_threads in the input
- **Smooth prose over empty data**: The model received sparse input for a section and
  generated fluent content anyway, masking the gap

### How to detect it

1. Find the debug request file for this passage:
   ```bash
   ls outputs/debug/
   ```
   Then `Read` the matching `*request*` file directly — no grep needed.

2. Pick **5 specific claims** from the output — not summaries, specific details:
   - A sensory detail ("the smell of river mud")
   - A cultural claim ("John's camel-hair garment marks him as a prophet")
   - A character's inner state ("You feel both resolve and vulnerability")
   - A tension thread reference ("the authority contest thread")
   - A structural claim ("this scene is the pivot from...")

3. For each claim, `Read` the request file and search in context for the keyword.

4. Report each as:
   - ✅ **Grounded**: quote the claim → quote the source field and text
   - ❌ **Freelancing**: quote the claim → "NOT FOUND in request data"
   - ⚠️ **Uncertain**: quote the claim → "partial match at [field] — needs human check"

---

## Inter-Step Grounding (Intermediate Outputs)

The most damaging pipeline failure is a step that received its inputs, produced valid output,
and silently ignored what it was given.

### Workflow

1. Find intermediate files for this pipeline run:
   ```bash
   ls outputs/intermediate/
   ```
   Then `Read` the relevant files directly by path.

2. For each consecutive step boundary (N-1 → N), ask: **does step N's output reflect
   what step N-1 produced?**

   `Read` both files and compare in context:
   - Do specific entities, scene details, or analytical conclusions from step N-1
     appear in step N's output?
   - Or does step N look like it could have been generated without step N-1 at all?

3. **Work backward from the problem.** If the final output is thin or generic, don't
   assume the final step is broken. Check each boundary:
   - Final output → its immediate input step
   - That step's output → its input
   - Continue until you find where grounding is adequate

4. **The first boundary where grounding breaks is where the prompt needs revision** —
   not necessarily the final step, which is often just surfacing a failure that originated
   earlier.

### Report format for inter-step grounding

```
## Inter-Step Grounding: {step_A} → {step_B}

Step A output (excerpt): "[specific content from step A output]"

Does this appear in Step B output?
  ✅ YES — Step B references: "[quote from step B that uses this]"
  ❌ NO — Step B makes no reference to [specific element]. Step B output: "[quote]"
  ⚠️ PARTIAL — Step B mentions [X] but not [Y from step A]

Assessment: [Grounded / Freelancing / Needs human judgment]
```

---

## Checklist Routing

Each project maintains its own checklists in `docs/audits/`. Start there:

`Read docs/audits/INDEX.md`

The index routes each output type to its checklist. Checklists vary by project — do not
assume a checklist exists or invent criteria for one that doesn't.

If no checklist exists for this output type, say so explicitly: "No checklist found for
this output type. Human should define audit criteria before proceeding."

Audit results go in `project/audits/` — one file per passage/run, named to include
pipeline, date, time, and passage identifier.

---

## Full Audit Workflow

### Step 1: Locate files

For file discovery, use `ls` to find what exists, then `Read` the files directly:

```bash
ls outputs/debug/
ls outputs/intermediate/
```

If the Captain has named a specific output file, `Read` it directly — no ls needed.

### Step 2: Run Layer 1 (checklist)

`Read docs/audits/INDEX.md`, then `Read` the appropriate checklist file.
Work through the checklist tier by tier. For every item, quote evidence from the output.

### Step 3: Run Layer 2 (freelancing detection)

`Read` the output file and the debug request file. Do the 5-claim spot-check in context.

### Step 4: Run inter-step grounding (if intermediates exist)

`Read` consecutive intermediate files and compare in context.
Check 2–3 step boundaries, working backward from the output.

### Step 5: Write audit record

`Write` to `project/audits/audit-{pipeline}-{YYYYMMDD}-{HHMM}-{passage}.md`.

```markdown
# Audit: {pipeline} — {passage}
**Date:** {date}
**Output:** {path}
**Checklist:** docs/audits/{checklist}.md
**Debug request:** outputs/debug/{request file}

## Pre-flight Blockers
[each finding with exact quote and line number]

## Tier 0 — Structure
[findings with quotes]

## Tier 1 — Content
[findings with quotes]

## Freelancing Detection (5-claim spot-check)
1. Claim: "..." → Source: [field]: "..." ✅ / NOT FOUND ❌
2. ...

## Inter-Step Grounding
[2–3 boundary checks with quotes]

## Tier 3 — Judgment
[honest answers; flag uncertainty explicitly]

## Summary
**Blockers:** [list or "none found by me — human should verify"]
**Freelancing risk:** [Low / Medium / High — with evidence]
**Items flagged for human review:** [specific list]
**My read:** [one sentence — human decides]
```

Provide a clickable link: `[audit-filename.md](project/audits/audit-filename.md)`
