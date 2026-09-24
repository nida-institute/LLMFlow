# One established order for prompt sections — ruled, ahead of the shipped discipline

**From:** an AI session in `nida-institute/LLMFlow`.
**About:** the order a transformation prompt's sections come in. Three documents stated it and
they disagreed; the Captain has ruled one order. Sent now rather than when it ships, because you
are blocked on at least one prompt.
**Status: the order and the three rulings are the Captain's, given 2026-09-16. The prose and the
measurements are the AI's, pending his review.**

**Read this as the authority until the shipped discipline catches up.** The order is his ruling,
not a released artifact: `~/.sp/disciplines/llmflow-prompt-organization.md` on your machine and on
ours still states the old one, and will until the template change lands and each side refreshes.
Where the two differ, this letter is right and the installed file is stale.

The full reasoning, with line numbers, is `project/plans/design-one-prompt-order.md` in our repo.

## 1. What was wrong

Three encodings, and a prompt author could not satisfy all of them:

| encoding | what it was |
|---|---|
| `~/.sp/disciplines/llmflow-prompt-organization.md`, "The 8-Section Pattern" | a top-level order, headings numbered 1–11 |
| `/audit-prompts` Step 1, lines 87–102 | a *different* top-level order, stated inline |
| **your** `tests/test_prompt_structure.py` lines 27–39 | the only one that executed |

The discipline and your test are each internally consistent. The skill is not: its Step 1 line 82
tells the auditor to load the discipline as the standard, then lines 87–102 hand them a competing
ordering with no statement of which wins. An auditor could reach opposite verdicts on the same
prompt depending on which half they weighted, which is why `/audit-prompts` has been passing
prompts your CI rejects.

**Your test was closest, and it is the reason the fix keeps everyone's content.** Read in full it
is a synthesis rather than a rival: line 93 treats any non-canonical top-level `#` heading as a
task section and requires it inside the schema-to-guardrails band, and lines 211, 225 and 238
require each task section to carry its rules, examples and a concrete ❌. That is the skill's
task-focused pattern, correctly scoped.

## 2. The order

```ebnf
prompt           = frontmatter , produces , [ variables ] , system-role ,
                   [ examples ] , data-sources , input-data , output-schema ,
                   band , quality-controls , checklist ;

band             = task-section , { task-section } ;
task-section     = task-heading , input , rules , task-examples , task-guardrails ;

produces         = "# WHAT THIS " , ( "STEP" | "PROMPT" ) , " PRODUCES" ;
quality-controls = "# " , ( "GUARDRAILS" | "EVIDENCE DOCUMENTATION REQUIREMENTS"
                          | "VALIDATION RULES" | "OUTPUT CONSTRAINTS"
                          | "COMPLIANCE REQUIREMENTS" ) ;
checklist        = "# " , ( "COVERAGE & QUALITY CHECKLIST" | "FINAL VALIDATION CHECKLIST" ) ;
task-heading     = "# " , ? text matching no other production ? ;

input            = "## Input: Where to Find the Data" ;
rules            = "## Transformation Rules" ;
task-examples    = "## Examples" , [ ":" , ? descriptive suffix ? ] ;
task-guardrails  = "## Guardrails" ;
```

The suffix on `task-examples` is measured, not permissive drafting: your prompts write
`## Examples: Input → Transformation → Output` in some task sections and a bare `## Examples` in
others, and both are correct.

`[ ]` is **conditional, never discretionary** — a bracket is licensed only by its side condition,
and no position may be dropped by preference:

| | side condition |
|---|---|
| C1 | `variables` present iff the prompt declares template variables |
| C2 | `examples` present iff examples are cross-cutting rather than per-task |
| C3 | every `task-examples` contains at least one ❌ counterexample |
| C4 | a guardrail naming one task appears in that task's `task-guardrails`, never in `quality-controls` |
| C5 | `task-heading` is how a task section is detected — any `#` heading matching no other production |

`# OUTPUT FORMAT` has no production; the name is `# OUTPUT SCHEMA`. `# CORE PRINCIPLES` has none
either — it left the standard, carried by no prompt in your set.

## 3. Three rulings behind it

1. **No optional sections.** The old standard marked five positions optional, transcribed from the
   `required` booleans in your test rather than reasoned. His objection: *"seems like an invitation
   to laziness, even when the section would help."* Measured across your five prompts,
   `WHAT THIS STEP PRODUCES` was carried by 5 of 5, the checklist by 4 of 5, and `CORE PRINCIPLES`
   by **0 of 5**. The first two are now required, the last is gone, and `variables` and
   consolidated `examples` are restated as conditions rather than preferences.
2. **Group by task is the governing principle.** His words: *"putting these three together in one
   focused section for a given task is what works best: what to do, examples and counter examples,
   guardrails. when these same sections are NOT grouped, results are measurably worse"* — and
   *"in general 'group by task' is one of the best things we have done."* Hence
   `## Guardrails` as a fourth required task subsection, and the top-level section narrowing to
   cross-cutting guardrails only (C4).
3. **Length is a guideline and never grounds for omitting a section.** *"length often becomes an
   excuse to not write examples."* Measured: three of your five prompts exceed the 500-line
   "sprawl warning", the longest — `segment-book.gpt` at 889 — is one of the three your
   `prompt-compliance-plan.md` calls *"the models to follow"*, and the prompt with the one
   documented defect is 331 lines shorter than it. Thresholds become descriptive.

## 4. What this means in your repo

| where | change |
|---|---|
| `test_prompt_structure.py:28` | `PRODUCES` → required |
| `:38` | `CHECKLIST` → required |
| `:31` | delete the `CORE PRINCIPLES` row, or a stray one still classifies as canonical instead of as a task section |
| `:27–39` | the `bool` needs a third state, or conditional rows a predicate — C1 and C2 are not `required=False` |
| new, parallel to 211 and 225 | every task section carries `## Guardrails` |
| `prompts/pericope-analysis.gpt` | gains `# COVERAGE & QUALITY CHECKLIST` |
| `prompts/synthesize-book-arc.gpt` | `# DETECT KEYWORD PATTERNS FROM CANDIDATES` gains the four subsections it has none of — see §4.1 |
| all five prompts | top-level guardrails triaged — per-task move into their task, cross-cutting stay |

### 4.1 `synthesize-book-arc.gpt`, which is the prompt you named as blocked

We measured it rather than working from the record, and **the record is stale.**
`prompt-compliance-plan.md` lines 56–60 say it *"has five example sections and no counterexample
in any of them"* and that all its ❌ markers are in `# GUARDRAILS`. As of 2026-09-16 that is not
what the file contains:

| | measured |
|---|---|
| task sections | **four**, not five — at 180, 233, 388, 436 |
| carrying ❌ inside their own `## Examples` | **three** — 13 of the file's 23 markers, at 221–226, 314–378 and 474–486 |
| top-level order | **already conformant** — PRODUCES 14, SYSTEM ROLE 26, DATA SOURCES 41, INPUT DATA 49, OUTPUT SCHEMA 72, band, GUARDRAILS 495, CHECKLIST 544 |

So the ruling does not ask you to distribute pooled counterexamples, because they are not pooled.
**The actual defect is narrower and sharper:** `# DETECT KEYWORD PATTERNS FROM CANDIDATES`
(388–435) carries **no subsections at all** — no `## Input`, no `## Transformation Rules`, no
`## Examples`. One task section of four states no rules and shows no examples, in a prompt whose
other three do both.

Under §2 that is now three violations rather than a stylistic gap: `rules`, `task-examples` and
`task-guardrails` are each required in every task section, and C3 requires a ❌ in the examples.
The remaining work on this file is that one section, plus `## Guardrails` in all four.

If that is what has been blocking you, the ruling covers it. If your blocker is something else in
this file, tell us and we will amend rather than have you work around it.

**This settles two of your open decisions.** D3 — whether `synthesize-book-arc.gpt` needs
counterexamples inside its task sections "or do its guardrails count as sufficient" — is answered
no: guardrails are not a substitute for a task section's counterexamples. Note that the premise
of D3 as written no longer holds; three of its task sections already have them. D4 — *"Adding
examples makes them longer. Split, or accept the length?"* — accept the length.

We would rather you deleted that test than edited it. `sp lint` enforcing this order directly is
now **#242** in our tracker, so every project inherits one implementation instead of maintaining
its own. It is sequenced behind the shipped-document change, and it is the reason we are not
asking you to invest much in the test edits above.

### 4.2 Where documentation goes — proposed, and **do not adopt it yet**

The order above says nothing about where to explain a notation or record why a rule exists. That
is deliberate: it is specified separately, in
`project/plans/design-documentation-in-prompts.md` in our repo. The proposal is a `~~~doc` fence
written inside the `.gpt` beside the rule it explains, which `sp` strips before the prompt reaches
the model — one file, so no documentation copy can drift from the prompt it describes.

**It is proposed, not ruled, and there is no stripper yet.** Two reasons not to start using it:

- Nothing removes those blocks today, so their contents would go to the model as instructions.
- A `~~~doc` block containing a `# HEADING` would break your own test, which finds headings with
  `line.startswith("# ")` (line 44) and does not parse markdown. Any heading scan has to strip
  doc blocks first, and that is part of the unbuilt work.

Flagged so you do not invent a different placement in the meantime, and do not adopt this one
before it holds.

## 5. Your 2026-09-15 note — answered separately, not here

`2026-09-16-document-order-is-in.md` is already in your `collab/sp` and answers that note in
full. Nothing in this letter revisits it, and nothing here is waiting on it.

## 6. What we are not claiming

The order is ruled and the measurements above are ours, taken 2026-09-16 and re-measurable. Whether
it clears the specific prompt you are blocked on we cannot tell from here: we asked which prompt
and had not heard when this was written. If it does not, say so and it gets amended rather than
worked around.
