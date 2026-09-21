# Design — one established order for prompt sections

**Status:** 2026-09-16. **All three questions in §8 are ruled** — no optional sections, rename
rather than renumber, and a per-project override only with the Captain's explicit approval.
**Nothing is built.** §6 awaits his authorization to implement, and sits third in the order he
set: after telling discourse-flow the engine changes landed, and after the absent type check.
**Issue:** none yet. This document is written to be posted to one.
**Author:** AI, from the Captain's ruling on 2026-09-16 — *"I want one established order"* — and
from measurements of `.claude/skills/audit-prompts/SKILL.md`,
`src/llmflow/templates/sp/disciplines/llmflow-prompt-organization.md`,
`discourse-flow/tests/test_prompt_structure.py`, all five of `discourse-flow/prompts/*.gpt`, and
`discourse-flow/project/plans/prompt-compliance-plan.md`, which reached §3.2's conclusion
independently from prompt output.
Every line number below was measured on 2026-09-16 and can be re-measured.

**The load-bearing section is §3.2.** §3 is the frame; §3.2 is the principle the Captain names as
*"one of the best things we have done"*, and it is the reason this document tightens rather than
merely reconciles.

---

## 1. The ruling

There is to be **one** order for the top-level sections of a transformation prompt. Today there
are two documents that each claim to give it, they disagree, and a third encoding — the only one
that executes — agrees with neither exactly. A prompt author cannot comply with all three, and
`/audit-prompts` currently passes prompts that CI rejects.

This document establishes the single order, shows it on a real file, and names what changes.

---

## 2. What is encoded today

| encoding | where | what it is |
|---|---|---|
| the discipline | `src/llmflow/templates/sp/disciplines/llmflow-prompt-organization.md`, "The 8-Section Pattern", lines 33–265 | a top-level order, headings numbered 1–11 |
| the skill's Step 1 | `.claude/skills/audit-prompts/SKILL.md` lines 87–102 | a *different* top-level order, presented inline |
| the test | `discourse-flow/tests/test_prompt_structure.py` lines 27–39 | the only one that runs |
| a project override | `ears-to-hear/scriptorium/docs/prompt-organization-convention.md`, 371 lines | a stale fork of the discipline — see §8.3 |

The discipline and the test are each internally consistent. The skill is not: Step 1 line 82
tells the auditor to load the discipline as the standard, and then lines 87–102 hand them a
competing complete ordering, with no statement of which wins. An auditor can reach opposite
verdicts on the same prompt depending on which half of Step 1 they weight.

**One amendment to the finding as originally stated.** The test is not a third rival. Read in
full, it is a *synthesis* of the other two:

- `test_task_sections_sit_between_the_schema_and_the_quality_controls` (line 93) treats any
  non-canonical top-level `#` heading as a **task section** and requires it to sit between
  `# OUTPUT SCHEMA` and the quality controls.
- `test_every_task_section_states_its_rules` (211), `..._shows_examples` (225) and
  `..._shows_a_counterexample` (238) then require each task section to carry
  `## Transformation Rules`, `## Examples`, and a concrete ❌.

That is exactly the skill's task-focused pattern — correctly scoped as a refinement of the
discipline's domain-rules band rather than as a replacement for its top-level ordering. The
working test already knows the answer. The two documents do not.

So this is not a contest with a loser. It is one document over-claiming, and the fix keeps every
piece of content that either document contributes.

---

## 3. The established order

**There is no discretionary section.** Every section is either required, or conditional on a
stated condition that can be checked. A section is never omitted because writing it was work.

That distinction is the whole of §3, and it is not what the current test encodes — see §3.1.

The order is a grammar, so it is stated as one. Comments carry the position numbers this
document cites elsewhere.

```ebnf
prompt           = frontmatter ,                   (* 1 *)
                   produces ,                      (* 2 *)
                   [ variables ] ,                 (* 3 — C1 *)
                   system-role ,                   (* 4 *)
                   [ examples ] ,                  (* 5 — C2 *)
                   data-sources ,                  (* 6 *)
                   input-data ,                    (* 7 *)
                   output-schema ,                 (* 8 *)
                   band ,                          (* 9 *)
                   quality-controls ,              (* 10 *)
                   checklist ;                     (* 11 *)

band             = task-section , { task-section } ;
task-section     = task-heading , input , rules , task-examples , task-guardrails ;

produces         = "# WHAT THIS " , ( "STEP" | "PROMPT" ) , " PRODUCES" ;
variables        = "# VARIABLES" ;
system-role      = "# SYSTEM ROLE" ;
examples         = "# EXAMPLES" ;
data-sources     = "# DATA SOURCES" ;
input-data       = "# INPUT DATA" ;
output-schema    = "# OUTPUT SCHEMA" ;
quality-controls = "# " , ( "GUARDRAILS" | "EVIDENCE DOCUMENTATION REQUIREMENTS"
                          | "VALIDATION RULES" | "OUTPUT CONSTRAINTS"
                          | "COMPLIANCE REQUIREMENTS" ) ;
checklist        = "# " , ( "COVERAGE & QUALITY CHECKLIST" | "FINAL VALIDATION CHECKLIST" ) ;
task-heading     = "# " , ? text matching no other production — C5 ? ;

input            = "## Input: Where to Find the Data" ;
rules            = "## Transformation Rules" ;
task-examples    = "## Examples" , [ ":" , ? suffix ? ] ;   (* C3 *)
task-guardrails  = "## Guardrails" ;
```

**`[ ]` means conditional, never discretionary.** A bracket is licensed only by its side
condition; no position may be dropped by preference (§3.1). The conditions are what the grammar
cannot express, so they are stated separately and each is checkable:

| | side condition |
|---|---|
| C1 | `variables` present iff the prompt declares template variables |
| C2 | `examples` present iff examples are cross-cutting rather than per-task |
| C3 | every `task-examples` contains at least one ❌ counterexample |
| C4 | a guardrail naming one task appears in that task's `task-guardrails`, never in `quality-controls` (§3.2) |
| C5 | `task-heading` is how a task section is detected — any `#` heading matching no other production |

C3 carries what the brackets otherwise obscure: **examples are never optional.** Position 5
governs only the consolidated section; every task section carries its own, enforced today at
`test_prompt_structure.py` lines 225 and 238. `# OUTPUT FORMAT` has no production — the name is
`# OUTPUT SCHEMA`. `# CORE PRINCIPLES` has none either; it was removed (§3.1).

### 3.1 Why no position is discretionary

The first draft of §3 marked five of twelve positions optional. That was transcribed from the
`required` booleans at `test_prompt_structure.py` lines 27–39 rather than reasoned, and the
Captain's objection on 2026-09-16 — *"seems like an invitation to laziness, even when the section
would help"* — is correct. Two unlike things were sharing one flag:

- **Conditional** — the section cannot be written when a named condition fails. A prompt with no
  template variables cannot have a `# VARIABLES` section. Absence is forced, not chosen, and is
  checkable.
- **Discretionary** — the section is always writable and always helps; omitting it is a
  preference. This is the category that invites laziness, because the omission is invisible and
  costs the author nothing.

Measured across all five prompts in `discourse-flow/prompts/` on 2026-09-16:

| section | carried by | ruling |
|---|---|---|
| `WHAT THIS STEP PRODUCES` | 5 of 5 | promote to required — **no prompt to edit** |
| `COVERAGE & QUALITY CHECKLIST` | 4 of 5 | promote to required — one checklist to write, `pericope-analysis.gpt` |
| `VARIABLES` | 1 of 5 | genuinely conditional — keep, with the condition named |
| consolidated `EXAMPLES` | 1 of 5 | genuinely conditional — keep, with the condition named |
| `CORE PRINCIPLES` | **0 of 5** | **remove from the standard** |

`CORE PRINCIPLES` is the clearest case. No prompt has ever carried one. An optional section that
nobody has written is not flexibility, it is clutter in the standard — and every reader has to
decide about it, forever, to reach the same answer every previous reader reached. Where a prompt
has cross-cutting principles they belong in `# SYSTEM ROLE`; where they are per-task they belong
in that task's `## Transformation Rules`. Nothing is lost by deleting the row.

The work this creates is one checklist, in `pericope-analysis.gpt` — five task sections deep and
the prompt in the set that most needs one. Writing it is not a price paid for the ruling; it is
the ruling being applied to a prompt the current standard let its author leave unfinished.

### 3.2 Group by task — the governing principle

The order in §3 is the frame. **This is the part that does the work.** The Captain, 2026-09-16:

> *"putting these three together in one focused section for a given task is what works best: what
> to do, examples and counter examples, guardrails. when these same sections are NOT grouped,
> results are measurably worse."*
>
> *"in general 'group by task' is one of the best things we have done."*

So band 9 is not merely where domain rules are allowed to sit. It is the unit the model actually
reads when performing one task, and everything governing that task belongs inside it:

- `## Input: Where to Find the Data` — where the data is
- `## Transformation Rules` — **what to do**
- `## Examples` — **examples and counterexamples**, at least one ❌
- `## Guardrails` — **what must not happen**, for this task

All four are required in every task section. The fourth is the new one: guardrails were
previously pooled in the terminal `# GUARDRAILS`, away from the rules and examples they
constrain. A model performing task B should not have to read past task C's rules to find the
boundary on task B.

**The evidence that pooling is worse is already written down.**
`discourse-flow/project/plans/prompt-compliance-plan.md` lines 56–60 records the failure mode in
a named file:

> *"`synthesize-book-arc.gpt` has five example sections and no counterexample in any of them. All
> its `❌` markers are in `# GUARDRAILS` at the end. […] a task section whose examples show only
> the right answer teaches the shape without the boundary."*

and lines 62–63 name `segment-book.gpt`, `subdivide-pericope.gpt` and `pericope-analysis.gpt` —
the three that carry rules, examples and counterexamples inside each task section — as **"the
models to follow."** That document reached this conclusion independently, from prompt output,
before this one was written.

**Its example no longer holds, and the replacement is stronger.** Measured 2026-09-16,
`synthesize-book-arc.gpt` has **four** task sections, not five, and **three of them do carry ❌
inside their own `## Examples`** — 13 of the file's 23 markers, at 221–226, 314–378 and 474–486.
The plan's specific claim is stale; its stated principle — *"a task section whose examples show
only the right answer teaches the shape without the boundary"* — is not.

What that file actually shows is the same failure in a purer form:
`# DETECT KEYWORD PATTERNS FROM CANDIDATES` (388–435) carries **no subsections at all** — no
`## Input`, no `## Transformation Rules`, no `## Examples`. One task of four states no rules and
shows no examples, in a prompt whose other three do both. Ungrouped is not the only way a task
section fails to carry its own instruction; empty is the other, and the old standard reported
neither.

**The skill already says this and does not carry it through.**
`.claude/skills/audit-prompts/SKILL.md` line 104: *"Everything about a task is co-located in that
task's section (data sources, rules, examples)."* Guardrails are missing from that list, and the
running test then requires them at top level. The principle was stated and then not applied to
the one section most likely to be written as a distant pool.

**What remains in the top-level `# GUARDRAILS` (10):** only guardrails that genuinely cross every
task — output-wide constraints, evidence requirements, refusal conditions. The test is
mechanical: *a guardrail that names one task, or that only makes sense while performing one task,
belongs in that task's `## Guardrails`.* Without that rule the top-level section is an escape
hatch and the pooling returns.

### 3.3 Length is a guideline, and never a reason to omit a section

The Captain, 2026-09-16:

> *"the line number limit is helpful as a guideline, but should not be seen as absolute. longer
> prompts with more lines and the right structure often work better than shorter ones, and length
> often becomes an excuse to not write examples."*

The discipline (line 305) and the skill (lines 111–115) both carry the same numeric bands —
simple under 200 lines, complex 300–500, "warning signs of sprawl" above 500 or 35 headers.
Measured against the five real prompts on 2026-09-16:

| prompt | lines | standing in `prompt-compliance-plan.md` |
|---|---|---|
| `segment-book.gpt` | **889** | one of *"the models to follow"* |
| `synthesize-book-arc.gpt` | 558 | the documented defect — five example sections, no ❌ in any |
| `segments.gpt` | 518 | |
| `pericope-analysis.gpt` | 486 | one of *"the models to follow"* |
| `subdivide-pericope.gpt` | 473 | one of *"the models to follow"* |

Three of five are over the warning threshold. The **longest file in the set, at nearly twice it,
is a model to follow**; the file with the one documented structural defect is 331 lines shorter.
In this set length does not predict quality, and the numbers are re-measurable.

**The failure mode shortens files.** Omitting `## Examples` and its counterexamples is the single
largest line saving available in a task section, and it is precisely what §3.1 and §3.2 forbid.
A numeric ceiling therefore prices the remedy as if it were the offence, and hands an author a
sanctioned reason to skip the section that matters most. That is the excuse the Captain names,
and the standard currently supplies it.

**The rule.** When length and a required section conflict, the section wins. Length is never
grounds for omitting one — not `## Examples`, not `## Guardrails`, not the checklist. A prompt
that is long because every task carries its rules, examples, counterexamples and guardrails is
correctly shaped, not sprawling.

**What the sprawl check should detect** is not the line count. It is repetition, rules stated at
a distance from the task they govern, and context duplicated across prompts that were split to
get under a number. The discipline already half-says this — it warns against splitting for its
own sake and states that a long well-organised prompt beats two with duplicated context — and is
then contradicted by its own thresholds. The thresholds become descriptive: a prompt over 500
lines is worth *looking at*, and finding four well-formed task sections is a complete answer.

This settles **D4** in `prompt-compliance-plan.md`, which has been waiting on exactly this
question — *"Adding examples makes them longer. Split, or accept the length?"* Accept the length.

### 3.4 Notation over prose — in the prompts too

The Captain, 2026-09-16:

> *"notation instead of prose can help make more precise and concise in some descriptions, e.g a
> BNF instead of describing a sequence in words, a JSON schema instead of words, a table, etc."*
> *"this is also true in prompts themselves."*

**Encouraged, with a two-part test, not mandated.** Reach for a formal notation or another
structure representation **where it is both more precise and more concise** than the prose it
replaces. Where it is only one of the two, it is a judgement call; where it is neither, it is
decoration. Examples that routinely pass the test:

| being described | representation |
|---|---|
| the shape of JSON output | JSON Schema, in `# OUTPUT SCHEMA` — not prose about the shape |
| the shape of XML output | RNC (RELAX NG compact) — the project's own `usx.rnc`; shorter than XSD or than RELAX NG's own XML syntax |
| a sequence, an ordering, or an identifier format | EBNF — `ref = book , "." , chapter , "." , verse ;` is exact where a sentence and one example are not |
| a mapping from input fields to output fields | a table |
| a closed set of values | an enum, not a sentence listing them |

**RNC is already the notation of record here, not a foreseeable case.** Current pipelines produce
USX and USJ, and `discourse-flow/pipelines/book-discourse-flow.yaml` line 229 cites **`usx.rnc`
line 553** by number as the authority for a structural rule — a para cannot span chapters.

Two things follow. First, USJ is the JSON serialization of USX, so a prompt can emit JSON whose
validity is governed by an RNC grammar: the two rows above split by *serialization*, not by which
grammar is authoritative. Second, and more useful — **where a grammar already exists, cite it.**
`usx.rnc:553` is exact, checkable, and stays correct when the schema changes. Paraphrasing its
rules into prose inside a prompt is the same failure §3.4 is about, one level up: a less precise
copy of something that already has a precise statement, which then drifts from it.

**Two readers, and only one of them reads the prompt.** The prompt's reader is a model, fluent in
JSON Schema, EBNF and RNC, so notation is a straight gain there. The prompt's *maintainers* are
developers, and many are not fluent in formal notations.

That is not an argument for less notation in prompts. It is an argument about where the
explanation lives — and the answer is **in the `.gpt`, outside what the model reads**, not in a
document elsewhere. The Captain, 2026-09-16:

> *"`.gpt` files are something we DO want readers to read and understand. Python, etc, not so
> much — we should be able to find all relevant documentation without looking there. `.gpt` files
> are essentially part of the higher level language environment we are defining."*

A `.gpt` is a language artifact whose reader is meant to open it, which is what distinguishes it
from `src/llmflow` — where `tests/test_docstrings_say_what_not_why.py` forbids provenance in
docstrings and keeps the reasoning in `data/ai-rules.yaml` instead. Documentation goes where its
reader already is, and for a prompt that is the prompt.

**The mechanism is specified separately.**
`project/plans/design-documentation-in-prompts.md` §1.1 carries this reasoning in full and
proposes `~~~doc` fences, written beside the rule they explain and stripped by `sp` before the
model sees them. That document is **unruled**; what §3.4 fixes is that the explanation is not
addressed to the model and is not exiled to a file the reader will not open.

So what does **not** belong in a prompt — in a doc block or anywhere else:

- **A prose gloss restating the schema "in plain English."** This is the one that matters. It
  creates a second statement of the rule, which then drifts from the first: the same defect as
  paraphrasing `usx.rnc` instead of citing it, arriving by a kinder route. Stripping it from what
  the model reads does not make it safe, because the maintainer still reads it and believes it.
- **A general primer on the notation.** It would be duplicated in every prompt that uses EBNF,
  and a developer who needs one can ask their LLM, which will explain EBNF better than any
  paragraph a prompt author would write. What is specific to *this* prompt belongs in it; what is
  true of the notation everywhere does not.
- **An apology for using it.**

Note what changes once documentation is stripped rather than exiled: length stops being the
objection (§3.3 already refused it as one), and drift becomes the whole of it.

Two reasons, neither of them taste:

- **Precision.** A schema has one reading. *"Each scene should usually include a citation"* has
  several, and the model picks.
- **Length.** Notation is denser than the prose it replaces, so it buys back lines — which is the
  legitimate way to shorten a prompt, as against the way §3.3 refuses.

**It does not replace examples.** A schema states the shape; an example shows the judgement. That
is why C3 requires both, and why a prompt whose `# OUTPUT SCHEMA` is rigorous still needs ❌
counterexamples in every task section.

**Prose stays right for what is not structured** — why a rule exists, what the model should weigh
when two rules pull against each other, what a good answer reads like. Forcing judgement into a
table loses the judgement and keeps the table.

This is encouragement where §3.1 is prohibition, and the two do not conflict: §3.1 removes
discretion over **what must be present**, §3.4 leaves discretion over **how it is expressed**,
subject to the test above. A notation is never grounds for dropping a required section, and the
list is open — any representation that passes the test qualifies, not only the four above.

### 3.5 Required work is named as work, never as a cost

The Captain, 2026-09-16:

> *"rewriting existing prompts is not a cost, it's work, but don't call it a cost."*
> *"writing software always means rewriting software, that's the means to an end."*
> *"if you call anything a cost, LLMs avoid doing it."*

The audience for a discipline, a skill and a prompt is largely a model. A model reads *costly*,
*expensive*, *overhead* or *only if needed* as licence to skip, and the skip is then invisible —
the same mechanism §3.3 identifies in the length bands, arriving through vocabulary instead of
through a number.

So in the discipline, the skill and the prompts: **required work is named as work.** No cost, no
overhead, no *if time permits*, no warning that a section will be long to write. Where effort
genuinely has to be conveyed, state the scope — what has to be written — never a price.

Rewriting is not an exception to be justified. Writing software means rewriting it; that is the
means, not a penalty, and a prompt that has to be revised to meet the standard is being finished
rather than being charged for.

**One legitimate use of the vocabulary remains:** describing why omission is tempting, as §3.1
does when it says the omission "costs the author nothing". Naming the trap is not setting it.

This document applies the rule to itself: §3 is a grammar because it describes a sequence, and
§3.1 and §3.3 are tables because their content is measurements. §3 was a flat table, then a tree,
before it was a grammar — the first two were describing a structure in a notation that could not
hold it.

---

## 4. A concrete example

`discourse-flow/prompts/pericope-analysis.gpt` already is this, today, and passes. Measured
top-level headings with real line numbers:

```
 18   # WHAT THIS STEP PRODUCES                    2 — required
 24   # VARIABLES                                  3 — conditional; declares variables
 33   # SYSTEM ROLE                                4 — required
 39   # DATA SOURCES                               6 — required
 49   # INPUT DATA                                 7 — required
 93   # OUTPUT SCHEMA                              8 — required
      ┌──────────────────────────────────────── 9 — the domain-rules band
151   ├── # COPY BASELINE FIELDS
      │   ├── ## Input: Where to Find the Data     153
      │   ├── ## Transformation Rules              157
      │   ├── ## Examples                          172
      │   └── ## Guardrails                        ABSENT
200   ├── # IDENTIFY INTERNAL STRUCTURE
      │   ├── ## Input: Where to Find the Data     202
      │   ├── ## Transformation Rules              212
      │   ├── ## Examples                          230
      │   └── ## Guardrails                        ABSENT
300   ├── # WRITE TRANSITIONS                      (same three, same gap)
347   ├── # IDENTIFY RHETORICAL FEATURES           (same three, same gap)
420   └── # WRITE EMOTIONAL DYNAMICS AND …         (same three, same gap)
462   # GUARDRAILS                                10 — required, and holds all five
                                                      tasks' guardrails pooled
      (none)                                      11 — required, ABSENT
```

**This file differs from full compliance in exactly one respect**, which is why it is the one
cited. It satisfies the frame in §3 exactly — every required top-level section, in position — and
carries three of the four subsections in every one of its five task sections. One subsection is
absent, in all five. Nothing else varies, so nothing else can account for the difference.

It is also the unfavourable case for the argument this document makes.
`prompt-compliance-plan.md` names it one of **"the models to follow"**. The gap is therefore not
attributable to a careless author: it is what the standard permitted its most careful one to do.

The missing content is not lost. It is pooled at 462 — the arrangement §3.2 rules against.
Distributing it is the edit.

Two other absences, and under §3 they are not alike. Consolidated `# EXAMPLES` (5) is
legitimately absent: this prompt's examples are per-task, which is exactly the condition that
position states. The missing checklist (11) is the one piece of writing §3.1 asks for — the
richest prompt in the set, five tasks deep, with nothing at the end to verify against. Under the
order as first drafted that omission was compliant, which is the Captain's objection made
concrete.

This file is the worked reference. When the order is ambiguous to a reader, this is what it
looks like.

---

## 5. Four traps the current skill text sets

Each row is a prompt written faithfully to the skill's Step 1 that CI then rejects.

| skill's Step 1 | §3 requires | test that fails |
|---|---|---|
| `# OUTPUT FORMAT` (line 92) | `output-schema` — no other production matches | band test (C5: unmatched heading, outside the band) |
| `# INPUT DATA` after the checklist (line 101) | position 7, before `output-schema` | ordering test |
| `# CRITICAL REMINDERS` last (line 102) | not a `quality-controls` alternative | band test (C5) |
| neither `# SYSTEM ROLE` nor `# DATA SOURCES` appears | positions 4 and 6, both required | required-sections test |

Four failures from one document, none of them the author's fault.

---

## 6. What changes

Four files, all owned by this repository:

- **discipline** — `src/llmflow/templates/sp/disciplines/llmflow-prompt-organization.md`
- **skill** — `.claude/skills/audit-prompts/SKILL.md`
- **skill template** — `src/llmflow/templates/sp/skills/audit-prompts/SKILL.md`
- **audits pattern** — `src/llmflow/templates/project/docs/ai-context/sp/audits-pattern.md`

| where | change | per |
|---|---|---|
| discipline | carries the §3 grammar and C1–C5; every position marked required or conditional, with the condition named. Today it marks neither | §3 |
| discipline | `produces` added at position 2; `CORE PRINCIPLES` removed | §3.1 |
| discipline | `## Guardrails` added as the fourth required task subsection | §3.2 |
| discipline, lines 305 and 323 | length bands and sprawl warnings become descriptive | §3.3 |
| discipline, line 33 | "The 8-Section Pattern" renamed — it enumerates eleven | §8.2 |
| skill, lines 87–102 | rival top-level list → a pointer to the discipline plus the four-subsection task pattern | §3.2 |
| skill, lines 111–115 and Step 4 (line 166) | thresholds prompt a look; never a finding alone, never grounds for reporting a required section as excusably absent | §3.3 |
| skill, lines 106–109 | unchanged — the heading hierarchy conflicts with nothing | |
| discipline | notation over prose where it is both more precise and more concise; existing grammars cited, never paraphrased; explanations of a notation kept in external documentation, never in the prompt | §3.4 |
| discipline and skill, throughout | required work named as work: no *cost*, *overhead* or *if time permits* anywhere a section is required | §3.5 |
| skill template | the same two skill edits. The files are byte-identical; both change together or `sp init` reinstalls the defect | |
| audits pattern, line 183 | *"gives the eight-section structure"* → names the established order without a count | §8.2 |

**The audits-pattern edit goes in the template, never in the rendered copy.**
`docs/ai-context/sp/audits-pattern.md` carries the same line 183, and `docs/ai-context/sp/` is
under a hard prohibition in CLAUDE.md: it is regenerated, so an edit there is lost and the fix
belongs upstream. `sp init --update` and `sp doctor` refresh it from the template.

**Test first, per the project's TDD rule.** Before any of the above: a test in this repository
asserting that the order named in the skill matches the order named in the discipline, so the two
cannot silently diverge again. `tests/test_global_disciplines.py` and
`tests/test_portable_disciplines.py` already govern this discipline file by name — I have not yet
read what they assert about its content, and will before writing.

---

## 7. What does not change

- **This engine's own `prompts/*.gpt`** — measured 2026-09-16: all six use zero top-level `#`
  headings. They are fixtures and examples, not transformation prompts, and the order does not
  bind them.
- **`/audit-output`** — searched 2026-09-16 for the section names and for `prompt-organization`:
  no match. It audits output against the data the step was given and encodes nothing about prompt
  structure, so this ruling does not reach it.
- **`/audit-pipeline`, both copies** — it *reads* the order rather than restating it: line 72
  ("Read the DATA SOURCES / INPUT DATA section of the prompt") and line 267 ("Prompt DATA SOURCES
  sections"). Both names survive §3 unchanged and stay required, so no edit is needed. Recorded
  here because "checked, and unaffected" is a different claim from "not looked at".

That is the whole of it. Everything else that moves, moves in another repository — §7.1.

### 7.1 The work §3 asks of discourse-flow

The first draft of this document claimed discourse-flow needed nothing because its test already
encoded the target state. **Removing the discretionary category changes that**, and the work is
named here rather than discovered later.

Writing software means rewriting it — that is the means, not a penalty — so what follows is
scope, not a bill. The test edits are mechanical; the prompt edits are the standard actually
reaching the prompts, which is the point of the document.

| where | change |
|---|---|
| `test_prompt_structure.py:28` | `PRODUCES` → required |
| `test_prompt_structure.py:38` | `CHECKLIST` → required |
| `test_prompt_structure.py:31` | `CORE PRINCIPLES` row deleted — otherwise a stray one still classifies as canonical rather than as a task section |
| `test_prompt_structure.py:27–39` | the `bool` becomes three-state, or conditional rows carry a predicate. C1 and C2 are not expressible as `required=False` |
| `test_prompt_structure.py`, new | a test parallel to 211 and 225: every task section carries `## Guardrails` (§3.2) |
| `prompts/pericope-analysis.gpt` | gains `# COVERAGE & QUALITY CHECKLIST` |
| `prompts/synthesize-book-arc.gpt` | **the prompt the Captain reports blocked.** `# DETECT KEYWORD PATTERNS FROM CANDIDATES` (388–435) gains `## Input`, `## Transformation Rules` and `## Examples` with a ❌ — it has none of the three. Its top-level order already conforms |
| all five prompts | top-level guardrails triaged: per-task move in, cross-cutting stay (C4) |

The guardrail work is real and is not a rename. This also **settles two open decisions in that
repository**, both of which have been waiting on a ruling this document now supplies:

- **D3** — whether `synthesize-book-arc.gpt` needs counterexamples inside its task sections "or
  do its guardrails count as sufficient". §3.2 answers no: pooled guardrails are the failure
  mode, not a substitute for it.
- **D4** — the three prompts over the length guideline, *"Adding examples makes them longer.
  Split, or accept the length?"* §3.3 answers: accept the length. None of the three is split to
  reach a number, and the edits above make all of them longer still.

None of this is in a repository this change owns. The sequence I would propose: settle the order
here, then raise the test and prompt changes in discourse-flow as their own piece of work, citing
this document and closing D3 with it. I would not reach across and make them from here.

---

## 8. Three rulings, given by the Captain 2026-09-16

| | question | ruling |
|---|---|---|
| 1 | the discretionary category (§3.1) | **empty it — no optional sections** |
| 2 | the "8-Section Pattern" heading | **rename, don't renumber** |
| 3 | the per-project override | **only with the Captain's explicit approval** |

**1 — no optional sections.** §3 stands as written: every position required, except `variables`
and consolidated `examples`, which are conditional on C1 and C2 and cannot be dropped by
preference. `CORE PRINCIPLES` leaves the standard. What it sets in motion is in §7.1.

**2 — rename.** The count has drifted once and would drift again; a convention named by a number
invites it. The order is the thing, the count an accident of how it is sliced. This reaches two
files: the discipline's heading at line 33, and `audits-pattern.md` line 183, which states the
same count in prose (§6).

**3 — the override survives, gated on him.** This is a fourth answer, not one of the three
offered: the mechanism is neither kept as-is nor narrowed nor removed. A project may hold a
`docs/prompt-organization-convention.md`, and it is authoritative **only with the Captain's
explicit approval**. Silence is not approval, and neither is the file's existence.

Two consequences follow, and both need building rather than assuming:

- **Approval has to be recorded in the override itself**, or the rule is unenforceable — an
  auditor reading a project cannot otherwise tell a sanctioned override from a fork. Three fields
  are required, and an override missing any of them is not authoritative:

  ~~~text
  # <project> prompt organization — override

  **Approved by the Captain: <date he ruled>.**

  | diverges from the shipped discipline in | why |
  |---|---|
  | <the position, section or rule that differs> | <the reason it differs here> |
  ~~~

  **The date** is when he ruled, not when the file was written — the two differ, and only the
  first is the authority. **The divergence list** forces the override to be a diff rather than a
  copy: a fork cannot satisfy it without becoming one. **The rationale** is what makes the
  override re-evaluable — when the shipped discipline moves, someone has to decide whether each
  divergence still applies, and that is impossible without knowing why it was taken. That is
  precisely what is missing from scriptorium's copy: 371 lines with no statement of intent, so
  nothing in it can be told deliberate from stale.

  `sp lint` should treat an override lacking any of the three as absent rather than as a standard.
- **`ears-to-hear/scriptorium/docs/prompt-organization-convention.md` carries no such approval**,
  so under this ruling it is not authoritative today. It is a 371-line near-copy of the discipline
  forked at an earlier revision — same "Design Principle", "The 8-Section Pattern", "Migration
  Strategy", "Open Questions" and "Comparison: Hearts vs. Bodies Organization" headings, omitting
  `WHAT THIS STEP PRODUCES` and `EVIDENCE DOCUMENTATION REQUIREMENTS`. It needs either the
  Captain's approval or deletion in favour of inheriting. Second repository, outside this change
  — to be raised there, citing this ruling.

---

## 9. What this buys

`/audit-prompts` and CI reach the same verdict on the same file. A prompt author reads one order,
in one place, with a worked example beside it. And the skill stops shipping four trapdoors to
every project that runs `sp init`.
