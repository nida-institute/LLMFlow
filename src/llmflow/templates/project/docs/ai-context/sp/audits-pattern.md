# Audits Pattern for AI Assistants

> **Use this file for:** which audit to run and how, the `docs/audits` vs `project/audits`
> split, the checklist format, and how to test a fix cheaply before proposing it.

An audit is diagnostic, not a gate (rule 17). It is how you find out what needs to change, and
it often produces the plan or the issues that then authorize the work. Findings are reported;
**the verdict is the human's** — never write "Approved", "Needs attention" or "Production ready".

---

## Two kinds of audit, and how to choose

**Skills** audit the pipeline and its code. They are read-only, they ship with `sp init`, and
they are invoked with a slash command. **Checklists** audit a specific generated artifact
against criteria a project writes for itself.

| You want to check | Use | Read-only |
|---|---|---|
| Generated output — is the model working from the data it was given, or from training knowledge? | `/audit-output` | yes |
| `.gpt` prompts and pipeline YAML — grounding, sprawl, examples, missing `response_format` | `/audit-prompts` | yes |
| Pipeline contracts — identifier lifecycle, field names, schema coverage, structured-output enforcement | `/audit-pipeline` | yes |
| Python plugins — determinism, identifier normalization, reimplementation of `sp` core utilities | `/audit-code` | yes |
| One artifact against this project's own criteria | the checklist in `docs/audits/` | yes |

Pick by what you are looking at, not by what you suspect. The two pipeline-facing skills divide
cleanly: `/audit-pipeline` is contracts *between* steps, `/audit-code` is what happens *inside* a
plugin.

### What each skill is actually for

- **`/audit-output`** — covers final and intermediate outputs. Its core question is whether each
  step used the output of the step before it, or quietly generated from training knowledge
  instead. Run it after a run when the output looks plausible but you cannot say where a claim
  came from.
- **`/audit-prompts`** — structure and grounding in `.gpt` and `.yaml` files: whether every output
  field has a documented input source, whether examples generalise beyond one passage, whether
  guardrails have been weakened since the last commit, and whether JSON steps declare
  `response_format`.
- **`/audit-pipeline`** — four axes: identifiers used as match keys across stages, fields prompts
  read that the data does not carry, schemas wired to LLM calls, and plugin output against what
  the schema requires.
- **`/audit-code`** — determinism, and whether a local plugin has reimplemented something `sp`
  already provides. Local reimplementations diverge from core as core changes.

---

## Directory structure

```
docs/audits/           ← Procedures: how to audit. Version-controlled, reusable.
  INDEX.md             ← Dispatch table: artifact type → trigger phrase → checklist file
  audit-passage.md     ← A 20–60 line checkbox-only procedure

project/audits/        ← Records: what you found.
  audit-<ARTIFACT>.md       ← Per-artifact, one file per output audited; retained
  audit-<pipeline>.md       ← Per-pipeline, one rolling file; updated in place

project/plans/         ← What will be done.
  <pipeline>-plan.md        ← Tasks, checked off and removed when done
```

**The distinction that matters:** `docs/audits/` is *how to audit* and is stable across runs;
`project/audits/` is *what you found* on one run. Never write findings into `docs/audits/`.

Records come in two shapes. A **per-artifact** record is one file per passage or output and is
kept as a record. A **per-pipeline** record is one rolling file, updated in place, with items
removed as they are resolved — git history is the audit trail, so dated copies do not accumulate.

See `~/.sp/disciplines/project-tracking.md` for the full rolling-file convention, and
`~/.sp/disciplines/sp-workflow.md` for the pipeline being the unit it rolls per.

---

## Running a checklist audit

When the user says *"audit this per the checklist"*, or names an artifact type:

1. **Open `docs/audits/INDEX.md`** and find the matching trigger phrase.
2. **Open the checklist it names** and read all of it before evaluating anything.
3. **Execute each checkbox in order.** Mark pass or fail.
4. **Write findings** to `project/audits/audit-<identifier>.md`, with the date, what passed and
   failed, and specific evidence.

**Cite exact quotes and locations for every finding.** The human reads what you cite and decides
whether they agree — a finding without a location cannot be checked.

Open the checklist file rather than recalling it, keep the checkbox order, and put findings in
`project/audits/` rather than beside the procedure.

---

## Checklist file format

- 20–60 lines
- **STOP conditions** in bold at the top — hard blockers that make the rest pointless
- `- [ ]` checkboxes only, no prose explaining why a criterion matters
- shell commands in code blocks where they help
- pass/fail criteria at the end

```markdown
# Audit: <artifact type>

**STOP if:**
- <hard blocker>

## Checklist

- [ ] <specific, verifiable criterion>
- [ ] <another>

## Pass/Fail

**Pass:** all boxes checked, no STOP condition.
**Fail:** any STOP condition, or 2+ unchecked.
```

**Why short:** long audit documents get skimmed, and an assistant that skims reads the top and
guesses at the rest. A 20–60 line file is read entirely. The trigger phrase in `INDEX.md` makes
it unambiguous which file to open, and the STOP conditions prevent effort spent auditing an
artifact that was already broken.

---

# Finding where the model made something up

The audit skills promise this; the method is here. `/audit-output` exists to detect **freelancing**
— a model generating from training knowledge instead of from the data it was given — and the way
to detect it is mechanical, not intuitive.

## Trace each output field back to the request

Not *"does the output look right"*. **Field by field: what in the request could have produced
this?** A field that nothing in the request could have produced is a finding whether or not its
value happens to be correct.

Grade every field:

| tier | meaning |
|---|---|
| **1 — HIGH** | training knowledge required; little or no supporting data in the request |
| **2 — MEDIUM** | some grounding exists, but the field has latitude to invent |
| **3 — LOW** | copy-forced or cite-forced from explicit input |

A Tier 1 field is not a bad answer waiting to happen — it is a field the pipeline cannot check.
Worked example, `discourse-flow/project/audits/freelancing-audit-2026-05-14-PHM.md`: a prompt asked
for *"the most common scholarly division of this book"* while the payload contained no scholarly
divisions at all. The model named one from training, then compared its own output against its own
training-knowledge reference. Nothing in the run could have falsified it.

## Know why the guardrail is not enough

**A Tier 1 field is a design defect, not a prompt-wording defect.** Strengthening the warning does
not work, and there is a measurement rather than an opinion behind that.

From `discourse-flow/project/plans/prior-knowledge-trap-design.md`: asked for the number of verses
in a window, the model wrote **98** — a chapter length it knew — while in the same response listing
**114** verse ids it had actually scanned from the data. *"The warning 'do not guess from prior
knowledge' is in the prompt but is overridden by the LLM's confidence in its training."*

The fix is to put the options in the payload and have the model select from them, not to word the
warning more strongly.

## Read the payloads

Debug capture is off by default. Set `linter_config.log_level: debug` in the pipeline and every
`type: llm` step writes its rendered request and raw response to
`<intermediate_file_directory>/debug/<pipeline_name>/`, cleared each run. There is no `--debug`
flag and no environment variable — see `~/.sp/disciplines/sp-debugging.md`.

**The request file is the whole of what the model saw.** If a claim in the output is not derivable
from that file, the model supplied it.

## The prescribed prompt structure is not optional

`~/.sp/disciplines/llmflow-prompt-organization.md` gives the eight-section structure. Following it
is required, and the reason is measured — same clause units, same book, only the prompt differing
(`discourse-flow/project/audits/audit-relation-runs.md`):

| prompt | unlabelled F1 | labelled F1 | label agreement |
|---|---|---|---|
| no constraints, no examples | 0.791 | 0.659 | 76.6% |
| constraints + examples, **invented** shape | 0.705 | 0.618 | 91.0% |
| constraints + examples, **the convention's** shape | 0.763 | **0.685** | 85.6% |

The convention's shape has the best labelled F1, and the invented shape was worse than it on both
stability measures — it bought agreement by costing structure. What the invention omitted is what
the convention requires: the input shown as the JSON the model receives, and the output shown as
the JSON the decision becomes.

The cost of deviating is larger than quality. Four earlier runs used an unconventional prompt and
reported *"the model collapses at 11 units"* as a **property of the task**. It was a property of
the prompt. **A bad prompt does not merely produce bad output; it produces false findings about
the subject.**

**Examples may be drafted by an assistant and must be approved by a human before they ship.** A
wrong example teaches the wrong thing on every subsequent run, and unlike a wrong rule it does not
read as a rule — it reads as a demonstration. `/audit-prompts` flags every new example since the
last commit for exactly this reason.

**A convention that is wrong is a finding, not a licence to deviate.** Follow the prescribed form;
if it contradicts itself, the evidence, or another rule, say so with the specific lines and the
measurement.

---

# Auditing well — the audit is itself a source of drift

A bad audit is worse than no audit: it produces a finding, the finding authorizes a change, and the
change is wrong. Every rule below was paid for.

**1 — Suspect your own code before the data.** One project tabulated every session that concluded
the data could not support something. **Five reports; none survived investigation. Bugs 5, data 0.**
One was reported as 34% agreement between two sources; it had compared *main* units to *all* units
at *exact* position, and at one word's offset agreement is 82–90%. The cost was not tokens — the
sessions explained their own bugs as properties of the subject matter, which sent a human reading
linguistics instead of reading a parser. **Before reporting a data limitation, look for a bug, and
state what you ruled out. A report that says "the data cannot support X" without naming the code
paths checked is not a finding.**

**2 — Compare approaches; do not ask which to pick.** Where a question can be settled by running
something, run it. Presenting a human with five approaches to choose between in advance moves the
work from the party who can measure to the party who cannot, and it arrives disguised as deference.

**3 — Keep the goal in view.** A stream of detail questions with no statement of what they serve is
overwhelm, not diligence. Say what the goal is, say which questions actually block it, and answer
the rest yourself.

**4 — Optimise the human's time, not the token bill.** Seven cents of tokens is never worth an hour
of a human's attention, and the exchange rate is far worse than that: the runs behind these lessons
cost a few dollars and **weeks** of one. A hand-rolled implementation that duplicated a step type
the engine already shipped discarded $9.01 of runs and produced three wrong rules. In every such
case **the correct document was open or one directory away.** Time is lost to not looking.

**5 — State the depth of the investigation, exactly.** This one corrupts every other finding, so it
is a rule and not a matter of style. A finding is usable only if the reader knows how far to trust
it. Every report states:

| state | not |
|---|---|
| **what was examined** — named files, fields, steps, with counts | "the pipeline", "the prompts" |
| **how** — read in full, grepped for these patterns, sampled N of M, run once, run five times | "reviewed", "checked", "analysed" |
| **what was not examined**, named | silence |
| **what would raise confidence** — the specific next check | "further investigation recommended" |

**The failure is not shallow work — it is undeclared depth.** A five-shot test labelled as five
shots is evidence; the same test called an audit is a false negative waiting to surface later, at
the human's expense. The tell in your own draft: *audited, reviewed, verified, confirmed* are
unreadable without naming what and how. If a sentence survives the question *"how many, and how?"*
unanswered, it is not a finding yet.

**6 — Prefer a red test to a written rule.** From the same record: *"only file permissions and
failing tests have ever stopped a bad change here."* An audit finding that ends in a test is worth
several that end in a paragraph.

---

## Testing a fix before proposing it — `sp tools replay`

An audit finding about a prompt usually implies a prompt change, and the honest way to support
that is evidence rather than argument. A full pipeline run costs money and time;
**`sp tools replay` tests one prompt edit against requests a previous run already captured.**

```bash
sp tools replay \
  --request 'output/intermediate/debug/<pipeline>/*-request.txt' \
  --prompt prompts/<name>.gpt \
  --prompt-new prompts/<name>-edited.gpt \
  --n 5
```

How it works: a captured request file is the original `.gpt` with every `{{var}}` replaced by its
value, so aligning the original prompt against the request recovers the variable map. Substituting
that map into the edited prompt gives a faithful test prompt carrying the same data — one call per
variant instead of a full run.

- `--request` takes files or globs. Captures are named `*-request.txt` from 0.2.1.24 on, and
  `*_request.txt` before that.
- `--prompt` **must be the version that produced the capture.** If the line counts differ, replay
  refuses rather than guessing.
- `--set VAR=VALUE` or `VAR=@file` supplies or overrides a variable; repeatable.
- `--n` sets draws per segment, so a change can be judged against variation rather than one lucky
  sample. `--show` picks the fields to compare; `--full` prints whole responses.

**Captures come from debug logging**, which is off by default. Set `linter_config.log_level:
debug` in the pipeline and every `type: llm` step writes its rendered request and raw response
under `<intermediate_file_directory>/debug/<pipeline_name>/`, cleared each run. There is no
`--debug` flag and no environment variable — see `~/.sp/disciplines/sp-debugging.md`.

Replay carries assumptions from the tool it was ported from, tracked in
[#177](https://github.com/nida-institute/LLMFlow/issues/177): it expects a response shaped as a
list of `segments` each with a `canonical_reference`, and it calls OpenAI directly. Check those
hold for your pipeline before trusting a comparison.

---

## Naming a record

```
project/audits/audit-<ARTIFACT>.md      # one artifact — a passage, a book, a generated file
project/audits/audit-<pipeline>.md      # one pipeline, rolling
```

Use the identifier the project already uses for the artifact. Dates go on individual items inside
the file, never in the filename — git history is the record of when, so dated filenames only
accumulate copies.

Every record carries the date of the audit, what passed and what failed, specific findings with
locations, and — where you have one — a proposed fix. It does not carry a verdict.

---

## Adding a procedure

1. Write `docs/audits/audit-<artifact-type>.md` in the format above.
2. Add a row to the `docs/audits/INDEX.md` dispatch table.
3. Test it by asking an assistant to audit that artifact by its trigger phrase.
4. If the assistant paraphrases instead of opening the file, the trigger phrase needs sharpening.
