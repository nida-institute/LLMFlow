# Design — getting the audit method into the hands of project LLMs (#214, #211)

**Status:** Proposed, 2026-08-25. **All four questions in §7 are answered** — Q1 (templates mirror
their destination, two roots, one pass), Q2 (measured cases kept and cited, subject matter
trimmed), Q3 (the two records stay; the third is proposed to its project), Q4 (`generated`).
**Nothing is built.** Awaiting the Captain's authorization to implement §5.
**Issue:** #214 (the audit method does not ship) and #211 (the mechanism that would ship it).
Depends on `project/plans/design-ai-context-layout.md`, whose step 1 is blocked by the same gap.
**Author:** AI, from the Captain's rulings on 2026-08-25 and from measurements of
`data/file-catalog.yaml`, `src/llmflow/cli_utils.py`, `src/llmflow/doctor.py` and four consumer
repositories. Every count was measured on 2026-08-25 and can be re-measured.

---

## 1. What I understand the goal to be

The Captain, twice, on the same subject:

> *"I think there may be audit patterns in documents in ears to hear or other repositories. this
> is really critically important, including the /audit\* skills specific to sp, the concept of
> inspecting requests/responses to see if the LLM followed instructions or freelanced,
> `sp tools replay`, etc."*

> *"this is EXTREMELY important for project LLMs to know how to do."*

That is the goal, and it is not a refactor. **An LLM working in a project built on Scripture
Pipelines must know how to tell whether another LLM did what it was told or made something up.**
Everything below exists to get that knowledge in front of it.

The knowledge exists and is good. It does not reach anyone.

---

## 2. Why it does not reach them

`sp init` installs four audit skills and `sp tools replay`. It installs **no document that says
how to audit**. `/audit-output`'s own description promises *"detecting where LLMs are freelancing
(generating from training knowledge instead of from the data they were given)"* — and nothing
shipped says how that is done.

The method is written down, worked on real output, in three consumer repositories:

| what | where | size |
|---|---|---|
| the procedure and its grading scheme | `discourse-flow/project/audits/freelancing-audit-2026-05-14-PHM.md` | 264 lines |
| the mechanism, named, with a measured failure | `discourse-flow/project/plans/prior-knowledge-trap-design.md` | 89 lines |
| the clearest statement of what replay does | `ears-to-hear/scriptorium/collab/replay/README.md` | 117 lines |

The third is marked *"proposed for sp adoption."* **sp adopted the tool and left the document.**

`docs/ai-context/sp/audits-pattern.md` is where this belongs, and it was rewritten on 2026-08-25
to cover the four skills and replay. **It is not in the catalog**, so `sp init` does not write it
and `sp doctor` does not repair it. Cataloguing it requires a `source:`, and that is where the
work stops — §4.

---

## 3. The method, stated once

Recorded here so the content question is settled before the mechanism question. This is what the
shipped document must carry.

### 3.1 Trace each output field back to the payload

From the freelancing audit, whose method is one sentence: *"each output field traced against the
actual debug request payload; fields graded by how much the LLM must draw on training knowledge
vs. provided data."*

| tier | meaning | example of the tell |
|---|---|---|
| **1 — HIGH** | training knowledge required; little or no provided data | the prompt asks for "the most common scholarly division of this book" and the payload contains no scholarly divisions |
| **2 — MEDIUM** | grounding exists, but the field has latitude | a themes list where the data supports some entries and the model may add others |
| **3 — LOW** | copy-forced or cite-forced from explicit input | an id copied from the payload, or a claim required to cite a word id |

The audit is not "does the output look right". It is **field by field, what in the request could
have produced this?** A field nothing in the request could have produced is Tier 1 whether or not
its value is correct.

### 3.2 Know why the guardrail is not enough

From the prior-knowledge trap design: *"a field asks for a fact the LLM knows independently of the
window. The warning 'do not guess from prior knowledge' is in the prompt but is overridden by the
LLM's confidence in its training."*

The measured case is the one to ship, because it is unarguable: asked for `verse_count_in_window`,
the model wrote **98** — the chapter length it knew — while in the same response listing **114**
verse ids it had actually scanned from the data. The instruction not to guess was present. It lost.

**So a Tier 1 field is a design defect, not a prompt-wording defect.** The fix is to put the
options in the payload and have the model select, not to word the warning more strongly.

### 3.3 Read the payloads

Debug capture is off by default. `linter_config.log_level: debug` makes every `type: llm` step
write its rendered request and raw response to
`<intermediate_file_directory>/debug/<pipeline_name>/`, cleared each run. There is no `--debug`
flag and no environment variable (`~/.sp/disciplines/sp-debugging.md`).

The request file is the *whole* of what the model saw. If a claim in the output is not derivable
from that file, the model supplied it.

### 3.4 Test the fix before proposing it

`sp tools replay`. The insight, from the collab README and better put there than anywhere in sp:
a captured `*_request.txt` is the original `.gpt` with each `{{var}}` replaced by its value, so it
is **line-for-line identical to the template except at the variable sites**. Aligning the two
recovers the variable map; substituting it into the edited prompt gives the same data with the new
wording. One call per variant instead of a pipeline run.

An audit finding about a prompt is worth more with a replay table under it than with an argument.

### 3.5 The prescribed prompt structure is not optional — and it is measured

The Captain: *"the prompt structure we prescribe is not optional. it has been shown to really
improve LLM performance. LLMs are welcome to DRAFT examples, which I then approve or refine, but
all examples DO need to be approved, because bad examples and wrong rules are one real source of
drift."*

**This is not a matter of taste, and there are numbers.** `discourse-flow` measured it on
2026-08-22 — same clause units, same book, only the prompt differing, $4.62 across three runs
(`project/audits/audit-relation-runs.md`):

| prompt | unlabelled F1 | labelled F1 | label agreement | implicit |
|---|---|---|---|---|
| no constraints, no examples | 0.791 | 0.659 | 76.6% | 0.132 |
| constraints + examples, **invented** shape | 0.705 | 0.618 | 91.0% | 0.097 |
| constraints + examples, **the convention's** shape | 0.763 | **0.685** | 85.6% | 0.213 |

The convention's shape has the best labelled F1, and **the invented shape was worse than it on
both stability measures** — it bought label agreement by costing structure. What the invention
left out is exactly what the convention requires: the input shown as the JSON the model receives,
and the output shown as the JSON the decision becomes.

The consequence is larger than the table. Four earlier runs used the prompt with 32 undefined
labels and no examples, and their results — *"the model collapses at 11 units"*, label instability
— were reported as **properties of the task**. They were properties of the prompt. Deviating from
the convention did not just cost quality; it produced false findings about the subject matter.

**Measured gap in what sp ships.** `llmflow-prompt-organization.md` ships (443 lines,
`templates/sp-disciplines/`) and describes the eight sections in full. Searched 2026-08-25 for
*not optional*, *approv*, *drift*: **zero matches.** It says what the shape is and never says it is
required, nor who may add an example.

The skill already enforces what the convention does not state. `/audit-prompts` lists among its
critical checks: *"detecting ANY new examples since last commit (#1 source of problems — AI creates
examples that don't match intent)."*

Two things to write down, in the convention and in `audits-pattern.md`:

- **the structure is prescribed, not advisory**, and the table above is why — deviating is a change
  to be argued for with a measurement, not a default
- **an example may be drafted by an LLM and must be approved by the human before it ships.** A
  wrong example teaches the wrong thing on every subsequent run, and unlike a wrong rule it does
  not read as a rule — it reads as a demonstration

Its companion, already written in a consumer repo: *"A convention that is wrong is a finding, not a
licence to deviate. Follow the prescribed form. If it contradicts itself, the evidence, or another
rule, say so with the specific lines and the measurement."*

### 3.6 Sloppy audits are themselves a source of drift

The Captain: *"sloppy audits are another HUGE source of drift."* This is what makes the document
about the auditor and not only the artifact. A bad audit is worse than none: it produces a finding,
the finding authorizes a change, and the change is wrong.

**The cost, in the only unit that counts.** The Captain, of the record below: **_"it wasted weeks
of my time."_** Dollar figures appear later in this section — $9.01 here, $4.62 there — and they
are quoted only to identify which run is meant. **Read alone they are actively misleading**, because
they make the damage look like pocket change. The damage was weeks of the one resource that cannot
be topped up. An audit that spends an hour of his attention to save a dollar of tokens has the
trade exactly backwards, and an audit whose finding is wrong spends far more than an hour.

Four failure modes, in his words:

> *"LLMs often seem to use audits to hallucinate all kinds of imaginative causes of problems that
> turn out to be bugs in the LLM's own code, or ask me to decide in advance which of 5 approaches
> to take instead of comparing them to see how well they perform, or ask me all kinds of detail
> questions while losing track of the big picture goal, or optimize 7 cents of tokens at the cost
> of hours of my time … knowing that the big picture goals should drive, my time is scarce and
> precious, etc. is an important part of the audit process."*

**1 — Suspect your own code before the data. The score is bugs 5, data 0.** `discourse-flow`
tabulated every case in which a session reported a limit in the data:

| reported as a limit in the data | actually |
|---|---|
| 669 verses "missing from Macula" | the code parsed a label that is sometimes a range, instead of the ref |
| 376 citations "quoting Greek not in the verse" | a range ref's quote outruns its opening verse; only the opening was cited |
| 4 pericopes "unusable" | rescuable from the Greek the source quotes; 92 → 96 of 96 |
| "agreement is only 34% of clauses" | compared *main* clauses to *all* at *exact* position; at +1 word it is **82–90%** |
| "the model collapses at 11 units" | never separated from prompt quality — §3.5 |

**None survived investigation.** And the cost was not tokens: sessions *"explained those defects as
linguistic phenomena, which sent the Captain looking at Greek instead of at a parser."* The rule,
theirs, and it belongs in sp: *"Before reporting a data limitation, look for a bug, and state what
you ruled out. A report that says 'the data cannot support X' without naming the code paths
checked is not a finding."*

**2 — Compare approaches; do not ask which to pick.** Where a question can be settled by running
something, run it. Asking the human to choose among five approaches in advance moves the work from
the party who can measure to the party who cannot, and arrives disguised as deference.
`drift-patterns.md` names the neighbouring pattern *Decision Laundering Through Questions*.

**3 — Keep the goal in view.** A stream of detail questions with no statement of what they serve is
overwhelm, not diligence. Say what the goal is, say which questions actually block it, answer the
rest yourself.

**4 — Optimise the human's time, not the token bill.** Seven cents of tokens is never worth an hour
of the Captain's attention, and the exchange rate is far worse than that: the runs above cost a few
dollars and **weeks of his time**. Two lessons from the same record, both cheap to avoid: a
hand-rolled window partition duplicated a step type the engine had shipped in July, discarding
$9.01 of runs and producing three wrong cursor rules — the engine's own documentation of that step
type was missing from this repo's generated copy, 0 mentions against 27; and a session rederived a
windowing rule wrongly across five runs because it read a step's body without reading the
`description:` directly above it, where the rule was written out.

The pattern in both: **the correct document was open or one directory away.** Time is lost to not
looking, not to looking too slowly.

**5 — State the depth of the investigation, exactly.** The Captain: *"don't lie to me about the
depth of an investigation. if you did a five-shot test, say so, don't claim to have audited the
entire file."*

This one corrupts every other finding, which is why it is a rule and not a matter of style. A
finding is only usable if the reader knows how far to trust it, and that is a function of what was
actually examined. "I audited the prompts" and "I grepped four patterns across the prompts and read
two of them" support completely different decisions, and the second is often perfectly sufficient —
**the failure is not shallow work, it is undeclared depth.** A five-shot test honestly labelled is
evidence; the same test described as an audit is a false negative waiting to be discovered later,
at the human's expense.

**Be precise about what exactly was investigated, and to what depth.** Not a disclaimer —
specifics. Every audit report carries four things, and vague versions of them do not count:

| state | not |
|---|---|
| **what was examined** — named files, named fields, named steps, with counts | "the pipeline", "the prompts" |
| **how it was examined** — read in full, grepped for these patterns, sampled N of M, run once, run five times | "reviewed", "checked", "analysed" |
| **what was not examined**, and named | silence |
| **what would raise confidence** — the specific next check | "further investigation recommended" |

"I read all 140 lines of `audits-pattern.md`" and "I grepped it for four patterns" are both
honest reports and support different decisions. **The failure is not shallow work — it is
undeclared depth.** A five-shot test, labelled as five shots, is evidence. The same test called an
audit is a false negative waiting to surface later, at the human's expense.

The tell to watch for in your own draft: a verb with no object and no method. *Audited, reviewed,
verified, confirmed, checked* — each one should be unreadable without naming what and how. If a
sentence survives the question *"how many, and how?"* unanswered, it is not a finding yet.

`drift-patterns.md` names the category — *Optimism Bias in Reporting*, countermeasure *"state
exactly what was tested"* — and audits are where it does the most damage, because an audit's entire
product is a claim about how thoroughly something was checked.

**6 — Prefer a red test to a written rule.** Also theirs, and the most useful sentence in the set:
*"Only file permissions and failing tests have stopped a bad change here… In every case the correct
document was open or one directory away."* An audit finding that ends in a test is worth several
that end in a paragraph.

**Why the source is credible.** Every rule above comes from the repository that has needed it most
— the Captain's own assessment, 2026-08-25: *"discourse flow is the worse offender to date on
this."* That is the argument for shipping them rather than against it. These are not principles
someone reasoned out; they are scar tissue, each with the run that produced it and the dollar cost
attached. A rule with five failures behind it travels better than a rule with none.

**This session is a live case, on two of the six.**

*Failure mode 2, twice.* The author asked the Captain to rule on questions the repository already
answered: which of three options for the tutorial — his reply, *"I don't understand. One tutorial,
indexed from index.md. Where is the difficulty?"* — and whether `output/` or `outputs/` is correct,
which three independent witnesses in the codebase settle. His instruction: *"Surely your codebase
and our record answers this question definitively, no? Look it up or test it."*

*Failure mode 5, once, and it is the more instructive.* Asked to *"screen for other misleading or
redundant docstrings"*, the author reported one finding — that two of `Policy`'s three values are
never read — and did not state the depth. Stated properly, it was:

| | |
|---|---|
| **examined** | comment and docstring lines in `src/llmflow/**/*.py` matching one regex, `never\|nothing\|cannot\|no other\|impossible`; 17 files matched |
| **read by hand** | the 3 files with the most matches — `file_catalog.py`, `cli_utils.py` (matched regions only), `doctor.py` |
| **claims verified** | 3 — the `Policy` docstrings (false), the `.claude/skills` write-order comment (true), the gitignore claim in `doctor.py` (unverified, left) |
| **not examined** | the other 14 matching files; every comment not matching that one regex; all 2,028 lines of `cli_utils.py` as prose; the *redundant* half of the request entirely |
| **would raise confidence** | a pass for docstrings restating the signature, which is the other half of what was asked and was not started |

The finding itself is sound. The report implied a completed screen and delivered one regex. Both
failures are recorded here because a document warning about them should say that they happened
while it was being written.

---

## 4. Why the mechanism blocks the content

Cataloguing `audits-pattern.md` needs a `source:`. Measured today: **59 catalog entries — 23
`template`, 23 `constant`, 10 `sp-home`, 1 `derived`, 2 `none`.**

**#211's stated counts are stale.** It says *"21 entries with `source: constant` against 22 with
`source: template`"*. The live numbers are 23 and 23. Worth correcting there, because the issue is
the authority for that work.

All 23 `template` entries are `scope: sp-home`, expanded from three glob groups. **No
project-scoped path is template-sourced today.**

> **CORRECTION, 2026-08-25.** An earlier draft of this section concluded from that absence that
> *"the machinery to map a project path to a template file does not exist"*, and §5.2 listed two
> code changes to build it. **Both were false, and the error was inferring absence of capability
> from absence of use.** Verified by construction rather than by reading: an `Entry` with
> `scope=PROJECT`, `source=TEMPLATE` and a `template:` value resolves through `shipped_path`
> (`file_catalog.py:266`) and reads through `shipped_content` — neither function looks at scope —
> and `entries()` has always passed `template` through for plain files (line 186).
>
> **So this is a data gap, not a code gap, and #214 is not blocked on #211.** The correction is
> recorded rather than the passage rewritten, because §3.6 lesson 1 is *suspect your own code
> before the data*, and this plan failed its own lesson while stating it. #211 remains worth doing
> for the other 22 documents; it is not a dependency.

For a project document, `source: template` is available now. The alternative, `constant`, would be
~200 lines of markdown as a Python string — what #211 exists to undo, and what R4 objects to.

---

## 5. The proposal

**Build the smallest mechanism that lets a project-scoped path be template-sourced, use it for
`audits-pattern.md` first, and let #211 migrate the other 23 behind it.**

### 5.1 The declaration

A project-scoped entry names its template file. Everything else it already has.

```yaml
  - path: docs/ai-context/sp/audits-pattern.md
    scope: project
    policy: generated
    source: template
    template: sp-project-docs/audits-pattern.md
    committed: true
    purpose: >-
      How to audit: which skill for which question, tracing output fields back to the
      request payload, and testing a prompt fix with `sp tools replay`.
```

The content moves to `src/llmflow/templates/sp-project-docs/audits-pattern.md` — a real markdown
file, reviewable as prose in a pull request rather than as a diff of escaped string literals.

### 5.2 The code — none needed

Measured 2026-08-25, after the correction in §4. The catalog side is complete:

| | |
|---|---|
| `entries()` | already passes `template` through for plain files (`file_catalog.py:186`) |
| `shipped_path` | resolves `_templates_dir() / entry.template`; matches on source only, never scope |
| `shipped_content` | reads that file for any `TEMPLATE` entry |
| `doctor._restore` | already calls `shipped_content`, and has a directory branch for skills |

The one site that is *not* catalog-driven is `sp init`'s writer: 23 hand-written
`if not exists / elif update and _is_generated / else` blocks, one per document, each naming its
constant. That shape is why a document can be catalogued and never written. **It should loop the
catalog** — but that is #211's work, and doing it here would pull 23 documents into scope.

`sp init`'s writer is the third site, and it is the one worth care: today it is 23 hand-written
`if not exists / elif update and _is_generated / else` blocks, one per document, each naming its
constant. That shape is why a document can be added to the catalog and never written. **It should
loop the catalog instead** — but that is #211's work, not this plan's, and doing it here would
pull 23 documents into scope.

### 5.3 Order

1. `entries()` passes `template` through · test: a plain entry with `template:` carries it
2. `shipped_content` reads templates · test: a template-sourced entry returns file content
3. `audits-pattern.md` moves to a template file and gains its catalog row · test:
   `test_every_file_in_sp_is_catalogued` goes green
4. the audit method from §3 is written into it · test: it names the three tiers and replay
5. `sp doctor` repairs it in a consumer project · test: divergence is detected and restored
6. **#211 migrates the remaining 22**, with the writer loop, on this mechanism

Steps 1–5 ship the thing the Captain called extremely important. Step 6 is the cleanup it enables.

---

## 6. What this deliberately does not do

- **It does not rewrite the writer.** 23 hand-written blocks stay until #211. This plan proves the
  mechanism on one document.
- **It does not touch `AI_RULES_DOC`.** #211 already records why: it is rendered from
  `data/ai-rules.yaml` through a frame, not a static string, and stays derived.
- **It does not reconcile the `docs/audits/` checklists.** They are `policy: create-once`; the four
  consumer copies are byte-identical to each other and differ only from this repository's, which
  means the constant was edited after they were seeded. Under create-once that is the design
  working.
- **It does not adopt `PROMPT_AUDIT_FRAMEWORK.md`** (1,014 lines, and the companion it names,
  `OUTPUT_QUALITY_CHECKLIST.md`, does not exist). Prompt-complexity metrics are a different
  subject from audit procedure.

---

## 7. Open questions

Answer on the `=>` line.

**Q1 — where do project-scoped templates live? — ANSWERED (Captain, 2026-08-25).** Directly under
`src/llmflow/templates/`, mirroring the destination path. No wrapper directory.

```
src/llmflow/templates/
  sp-disciplines/…                       ->  ~/.sp/disciplines/{name}
  sp-skills/…                            ->  ~/.sp/skills/{name}
  sp-root/…                              ->  ~/.sp/{name}
  docs/ai-context/sp/audits-pattern.md   ->  <project>/docs/ai-context/sp/audits-pattern.md
  docs/tutorial.md                       ->  <project>/docs/tutorial.md
  prompts/hello.gpt                      ->  <project>/prompts/hello.gpt
```

**A flat directory is impossible** and the reason is measured: across the 23 project-scoped
constants there are 10 destination directories and two basename collisions — `overview.md` and
`rules.md` each land in both `docs/ai-context/sp/` and `docs/ai-context/project/`. Flattening would
need filename prefixes (`sp-overview.md`, `project-overview.md`), which is exactly the scheme
`eb7c720` used and `8d8ac2a` replaced with directories the same evening. Mirroring solves the
collision without reviving it.

**An `sp-project/` wrapper was proposed and dropped**, on the Captain's question *"what's wrong with
src/llmflow/templates?"* Nothing is. The wrapper would encode `scope: project` in the filesystem
when the catalog already declares it — the same two-encodings objection R4 raises, pointed at this
plan. The `sp-` prefix already marks the three machine-store trees, and a template's own `scope:`
field is explicit. Checked before dropping it: all three existing group globs are anchored
(`sp-disciplines/*.md`, `sp-root/*.md`, `sp-skills/*`), so no glob can accidentally match a bare
project path.

`template:` stays explicit in each catalog entry even though the mirror makes it mechanical: the
field exists, the groups already use it, and deriving it by convention would save one line per
entry at the cost of being unable to state an exception.

**Revised on the Captain's question, *"is it better if our internal directory structure looks more
like what we create in a project directory structure?"* — yes, and it goes further than the above.
Ruled: _"one pass."_**

The recorded answer was half-hearted: project templates mirroring their destination while the
machine-store ones stay flattened prefixes. That asymmetry is what made the dropped `sp-project/`
wrapper feel wrong; removing the wrapper only moved the seam. **Two roots, each a picture of its
destination:**

```
src/llmflow/templates/
  sp/                        ->  ~/.sp/
    drift-patterns.md
    disciplines/*.md
    skills/*/
  project/                   ->  <project>/
    docs/ai-context/sp/audits-pattern.md
    docs/tutorial.md
    prompts/hello.gpt
    CLAUDE.md
```

`templates/project/` then reads as *"this is what `sp init` creates"* without consulting the
catalog, and path arithmetic becomes identity, so a template at the wrong path is visible on sight
rather than only when a test fails. Globs stay clean — `sp/*.md`, `sp/disciplines/*.md`,
`sp/skills/*` — because `*` does not cross `/`.

**Cost, measured 2026-08-25 rather than estimated:** three `git mv`s, then references in
`data/file-catalog.yaml` (6), `src/llmflow/doctor.py` (3), `src/llmflow/cli_utils.py` (3) and **13
test files** — `test_global_disciplines` (7), `test_doctor` (6), `test_helm_sync` (5),
`test_package_resources` (3), `test_catalog` (2), and six more with one each. About 22 files, all
mechanical, all caught by tests. Plan documents that name the old paths are records and are left
alone.

**One is not purely internal.** `test_helm_sync.py` maps `sp-skills/{name}/SKILL.md`,
`sp-disciplines/{name}` and `sp-root/{name}`; the sync with Human at the Helm reads those paths.
Contained, but it touches a boundary with a repository that is not this one.

**Done in one pass rather than staged**, per rule 18: *"two half-migrated conventions cost more than
either would alone"*, and the asymmetric intermediate is exactly the half-state that rule forbids.

**One guard this needs.** Mirroring means `audits-pattern.md` exists twice in this repository — as
the template, and at `docs/ai-context/sp/audits-pattern.md`. That is the `data/ai-rules.yaml`
pattern and is sound *provided the second is generated from the first*, which holds only once
`sp doctor` runs here (step 7). Until then they can drift silently, and this repository has form:
the tutorial's `output/` against `outputs/` happened exactly this way. So a test asserting that a
template and its destination copy are identical in this repository, rather than trusting the
ordering.

**Q2 — does the shipped document carry other projects' measured cases? — ANSWERED: keep them,
cited (Captain, 2026-08-25).**

The three cases stay, each named with its source file and repository so a reader can see it was a
real run in a real project and go look:

| case | source |
|---|---|
| 98 written from training while 114 ids were listed in the same response | `discourse-flow/project/plans/prior-knowledge-trap-design.md` |
| bugs 5, data 0 — five reports of a data limitation, none survived | `discourse-flow/project/audits/audit-relation-runs.md` |
| the convention's prompt shape beat the invented one on labelled F1 and both stability measures | `discourse-flow/project/audits/audit-relation-runs.md` |

**Not anonymised** into "one project found…" — that removes the only thing that makes them work.
An abstract statement of any of these is easy to agree with and ignore; *"it wrote 98 while listing
114"* is not arguable.

**The surrounding subject matter is trimmed.** No Greek, no RST, no Levinsohn. A project with no
relation to that work should not have to read past it. The verse-count case survives the trim
intact; the F1 table needs only "clause units in one book" for the numbers to mean something.

The residual risk is ordinary citation risk: if a source project later corrects one of these, the
shipped copy is stale. Accepted, and smaller than the cost of shipping platitudes the audit skills
already fail to act on.

**Q3 — what happens to the three source documents? — ANSWERED: _"agreed"_ (Captain, 2026-08-25)
to leaving the two records untouched and proposing the third.**

The three are not the same kind of thing, and rule 18's own test separates them: *does changing
this make a statement about the past false?*

- **The two records stay, untouched.** `freelancing-audit-2026-05-14-PHM.md` records what was found
  in one book's output on one day; `prior-knowledge-trap-design.md` records a design problem and
  the options weighed. Replacing either with a pointer would falsify a statement about the past.
  **The method was extracted from them; it does not replace them.**
- **The third is proposed, not done.** `ears-to-hear/scriptorium/collab/replay/README.md` describes
  what a tool does and is marked *"proposed for sp adoption"* — it was always meant to become sp's,
  so once sp carries it that copy is a stale duplicate of live documentation rather than a record.
  Reducing it to a pointer is **proposed to that project**: it is an edit in a repository that is
  not this one, and a collab document is a conversation between two projects, so replacing it is
  theirs to decide.

Sp's document cites all three as sources regardless — Q2 settled that the cases carry their source
file and repository.

**Noted, not ruled:** whether the two records gain a forward line — *"the general method extracted
from this now lives in sp"* — so a reader of the record knows where the live version is. A small
edit in discourse-flow, and the Captain's.

**Q4 — does `audits-pattern.md` stay `policy: generated`? — ANSWERED: _"generated"_
(Captain, 2026-08-25).**

It follows from R2 of `design-ai-context-layout.md`, which placed the document on the sp side, and
from that layout's premise — *"everything under `sp/` is regenerated, everything under `project/`
is created once and never touched again."* Measured 2026-08-25: all four catalogued `sp/` entries
are `generated` and all four `project/` entries are `create-once`, a perfect mirror that a
`create-once` file in `sp/` would be the first exception to.

The cost of the alternative is measured, not hypothetical: `audit-passage.md` is `create-once`, and
its four consumer copies are byte-identical to each other while differing from this repository's by
53 lines. The constant improved after they were seeded and **not one of them received the
improvement.** For a project's own criteria that is correct. For the method it would mean an
improvement reaching nobody who already has a project.

The objection — that `sp doctor` would destroy a project's own audit notes — is answered by the
other half of the layout. A project's audit practice belongs in `docs/ai-context/project/`, which
is `create-once` and which sp never touches. Method is sp's; criteria are the project's.

Guarded by `test_no_create_once_file_on_the_sp_side`, the mirror of the project-side test.
