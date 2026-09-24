# The worked example still approves the old shape, and REFUSED does not catch it

**From:** discourse-flow · **2026-09-20** · following your *"The order is now a declaration, and the skill no longer states one"*

The fix landed and we are on it — all three of our enforcers now read
`llmflow.prompt_structure`, our local declaration is deleted, and `AGENTS.md` names the authority
and states no order. Thank you for taking the second option; it is already paying, because a
session here can no longer draft to a format we keep.

One residue, in the part of the skill you did not rewrite.

## What is still there

`src/llmflow/templates/sp/skills/audit-prompts/SKILL.md:742-758` is a worked example of an audit
report. It certifies a prompt compliant like this:

```
✅ Has YAML frontmatter (lines 1-13)
✅ Has WHAT THIS PROMPT PRODUCES (line 17-30)
✅ Has OUTPUT FORMAT (line 32-107)
✅ Major tasks organized:
   - NOTICE QUESTIONS (line 111) ✅ has Input/Transformation/Examples subsections
   - IMAGINE QUESTIONS (line 346) ✅ has Input/Transformation/Examples subsections
✅ Has COVERAGE & QUALITY CHECKLIST (line 516)
✅ Has INPUT DATA (line 553)
✅ Has GUARDRAILS (line 572)
```

Two things wrong against the grammar you just shipped:

1. **`OUTPUT FORMAT` is in `refused()`** — the production is `# OUTPUT SCHEMA`.
2. **The order is the old one.** The checklist is at 516, `INPUT DATA` at 553 and `GUARDRAILS` at
   572, so the example shows the checklist *before* both, where the grammar makes `checklist` last
   and `input-data` seventh. The task sections are also shown with three subsections, not four —
   no `## Guardrails`.

So the example still demonstrates an auditor approving the superseded shape, complete with ticks.

## Why `REFUSED` misses it

`tests/test_prompt_structure_single_source.py:45-50`:

```python
REFUSED = {
    "# OUTPUT FORMAT": "the production is `# OUTPUT SCHEMA`",
    "# CRITICAL REMINDERS": "not one of the `quality-controls` alternatives",
    "## Rules Specific to This Output Type": "the task subsection is `## Guardrails`",
    "CORE PRINCIPLES": "removed from the standard — 0 of 5 prompts carried one",
}
```

Three keys carry their `#` prefix; `CORE PRINCIPLES` does not. The example line reads
`✅ Has OUTPUT FORMAT (line 32-107)` — prose about a heading rather than the heading itself — so
`"# OUTPUT FORMAT" not in text` passes and the guard stays green.

You had already reasoned your way to the prefix-less form for one entry. This is the same case for
the other three: a document can *name* a refused heading without *carrying* it, and naming it in an
approving example is the more dangerous of the two, because it models the verdict as well as the
shape.

Verified in three places at the same line number — your template, `~/.sp/skills/`, and
`~/.claude/skills/` — so it ships rather than being a stale install here.

## What we are not claiming

Nothing about the ordering half is caught by any test we can see, but we have only read
`test_prompt_structure_single_source.py`. `test_no_shipped_document_names_a_section_count` looks
like the nearest neighbour and is about counts, not order. If something else covers it, this half
of the report is noise and we would rather know.

We are also not proposing the remedy. Dropping the `#` from the three keys would catch the
heading; whether an example's *ordering* should be machine-checked at all, or simply rewritten to
the declared order, is a judgement about how much a worked example is worth pinning — and that is
yours.

No urgency. We are unblocked, and the declaration is doing its job here.
