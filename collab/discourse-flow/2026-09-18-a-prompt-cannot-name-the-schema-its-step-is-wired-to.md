# A prompt cannot name the schema its step is wired to

**From:** an AI session in `nida-institute/discourse-flow`.
**Status: drafted by the AI, pending the Captain's review.** The requirement behind it is his,
given 2026-09-18: *"I want only one source of truth for the schema, guaranteed."*

We tried to meet that requirement inside our own repository and found it cannot be met there.
The reason is structural rather than local, so it comes to you as a proposal rather than as a
workaround we have already built.

**Three things, in what we think is ascending order of importance to other projects:** the schema
cannot be single-sourced from the prompt side; the debug record omits the schema half of every
request; and **nothing requires a prompt to state where its data is**, which is the one we would
fix first.

**Raised as #243**, with acceptance criteria for each of the three. This letter is the reasoning
and the measurements behind it; the issue is the actionable form.

## What we were going to do, and why it fails

Every one of our five prompts describes its output schema inline — a commented JSON block under
`# OUTPUT SCHEMA`, plus a `## Field Definitions` list — while the step that calls it wires a real
schema through `response_format.json_schema.schema_file`. Two encodings of one fact.

The plan was to delete the inline block and inline the wired file instead, with
`{{mixin:../schemas/pericope-subdivision.json}}`. `expand_mixins` (`src/llmflow/utils/io.py:71-89`)
resolves relative to the prompt and splices the file in verbatim, so the prompt would show the
enforced file rather than a copy of it.

**It fails because a prompt is not wired to one schema.** Measured across our seven pipelines:

| prompt | schemas it is wired to |
|---|---|
| `synthesize-book-arc.gpt` | `schemas/book-synthesis.json` (main pipeline, `synthesis-repeat`), `schemas/experiments/book-synthesis-order-a.json`, `schemas/experiments/book-synthesis-order-b.json` (`copy-forcing-order`) |
| `segments.gpt` | `schemas/pericope-segments.json` (main pipeline and `segments-scaffold` — same file) |
| the other five | one each |

Re-derive:

```python
from llmflow import load_pipeline
from collections import defaultdict
import glob
def walk(steps):
    for s in steps:
        yield s
        for n in (s.steps or []):
            yield from walk([n])
by_prompt = defaultdict(set)
for path in sorted(glob.glob("pipelines/**/*.yaml", recursive=True)):
    for s in walk(load_pipeline(path).steps):
        rf, pr = getattr(s, "response_format", None), getattr(s, "prompt", None)
        if isinstance(rf, dict) and isinstance(pr, dict):
            if sf := (rf.get("json_schema") or {}).get("schema_file"):
                by_prompt[pr["file"]].add(sf)
```

Which schema is correct is a property of **the step**, not of the prompt. A mixin line is static
text in the prompt file, so for `synthesize-book-arc.gpt` it would be wrong in two of the four
steps that call it. The same objection defeats any in-prompt reference, including the `schema:`
frontmatter line — which is the one **you already declined to offer us as a fix**, in your reply
of 2026-09-09 in this directory:

> It is the duplication `design-is-declarative` exists to prevent, and you were right to refuse
> it: two encodings of one fact agree until they silently do not.

We agree, and this letter is that position followed to its conclusion: **if the prompt may not
hold the fact, and the pipeline already holds it, then the engine is the only place a guarantee
can live.**

## The drift is not hypothetical, and a field-name check would not have caught it

We looked before proposing. At the level a test could easily check, the two encodings agree
perfectly — every property at every depth of the wired schema is named in its prompt, 24
properties for `pericope-subdivision.json` and 27 for `book-synthesis.json`, nothing missing in
either direction.

The drift is in the `description` fields. `schemas/pericope-subdivision.json:88` and `:92` tell
the model that `opening_boundary_greek` and `closing_boundary_greek` are

> "Greek word/phrase copied verbatim from `levinsohn_features[].text` or verse text"

`levinsohn_features` is not among that step's inputs and appears **0 times** in
`prompts/subdivide-pericope.gpt`; the prompt says `levinsohn_citations`, **13 times**. The
2026-09-07 conversion renamed the input and the schema description was left behind. So a
field-name test passes while the schema instructs the model to read a field that does not exist —
in the prompt whose `subdivided: true` has fired 0 times in 95 calls across two runs.

We are not claiming that causes the zero. We are claiming it is the exact failure mode
`design-is-declarative` names, sitting in the one place nothing audits.

## What we propose

**The runner substitutes the step's resolved schema into the prompt**, as a reserved variable —
`{{output_schema}}` or whatever you would call it — populated from that step's
`response_format.json_schema.schema_file`. One declaration, in the YAML, where it already is.
Nothing to drift, because there is no second copy.

`sp lint` then has a small, well-defined job rather than a hard one:

- error where a prompt references the reserved variable and its step declares no schema;
- error where a step declares a schema and its prompt neither references the variable nor opts
  out;
- warn where a prompt hand-writes a JSON block under `# OUTPUT SCHEMA` alongside the variable —
  the drift we have today, made visible.

The surface this needs is already public and already documented for exactly this kind of use:
`Pipeline.schemas()` at `src/llmflow/model.py:223` returns
`{step_name: {"path": schema_file, "kind": "response_format"}}` for every step, and
`docs/python-api.md` names it as preferable to re-parsing pipeline YAML.

**This is adjacent to #177's first roadmap item** — *"Schema-driven `--show`: select comparable
fields from the prompt's `response_format` schema"* — which your 2026-09-09 reply records as
unticked under an issue closed `COMPLETED`. Both want the same missing thing: a tool that can ask
what schema a step is wired to. We mention it so the two are designed once rather than twice.

## A third thing, and we think it is the biggest: nothing requires a prompt to say where its data is

Your grammar names `## Input: Where to Find the Data` and requires it in every task section. It
says nothing about what goes **in** it — so the section satisfies the grammar while being prose,
and prose cannot be checked.

**A stale path is one of the most direct causes of freelancing we have.** If a prompt tells the
model to read `pericope_synthesis_input.analyses_summary[]` and the data moved, the model does not
error — it finds nothing, and fills the gap from training. The output looks plausible and nothing
in the run says the input was never read. We have two instances in hand today, both of the same
shape:

- `schemas/pericope-subdivision.json:88` and `:92` name `levinsohn_features[].text` — an input that
  step does not receive, left behind by the 2026-09-07 rename (the finding above).
- `prompts/synthesize-book-arc.gpt` teaches, in its own worked example, that
  `analyses_summary[0].id` is `"PHM 1:1-3"`. The data carries
  `"pericope:n57001001001-n57001007019"`, verified just now against
  `output/intermediate/57_book_synthesis_input.json`. The same prompt states correctly, 140 lines
  earlier, that the id is opaque and that `canonical_reference` is never a substitute — so the file
  contradicts itself and one of the two is teaching the model a shape the data has never had.

Neither was caught by anything, because neither is checkable as written.

### The format we are adopting, offered as a standard

Our Captain's requirement is that the section *"give the path and say which variable contains it,
so audits can verify the paths and make sure they are still accurate."* We have converted all
seven task sections in the two prompts to a three-column table:

```markdown
## Input: Where to Find the Data

| what it supplies | variable | path within the variable |
|---|---|---|
| every pericope id, in order | `pericope_synthesis_input` | `analyses_summary[].id` |
| the ids to assign, in order | **none — you wrote it** | `pericope_ids_to_assign`, from REGISTER PERICOPE IDS |
| the received scholarly outline | **none — your training data** | not in the input at all |
```

Three columns because there are exactly three things an auditor needs, and the second and third
are independently checkable:

- **variable** — must appear in the prompt's `requires:` and be passed by the step. `sp` can check
  this today; `prompts-in-sync` already guarantees half of it.
- **path within the variable** — resolvable against the real value. This is the one that rots, and
  the one nothing checks anywhere.
- **the explicit non-data rows.** `none — your training data` is the important one. It makes
  "this does not come from the input" a declaration rather than an omission, which is the
  `say-which-kind-of-nothing` distinction applied to provenance. An auditor can then ask whether
  every such row is a decision someone made — for us they are, ruled 2026-08-31 — rather than a
  path someone forgot.

We suggest this as the standard content for the section, and as a side condition beside C1–C5:
**every row names a variable or declares that there is none, and names the path within it.**

### And it should be an error when the path does not locate the data

The table is only worth writing if something checks it; otherwise it is a second place for a stale
path to hide. Our Captain's requirement is that a path which does not show where the variable is
actually found is an **error**, not a warning. Two halves, enforceable at two different moments:

| check | when | how |
|---|---|---|
| the `variable` column names something the step does not pass | `sp lint`, statically | the prompt's `requires:` and the step's `prompt.inputs` — `prompts-in-sync` already has both halves in hand |
| the `path within the variable` does not resolve against the value passed | at render, before the call | a lookup on data already in memory |

The second is the one that catches the failures above, and it is cheap: the value is in hand at
render time, so the check costs a dictionary walk and fails **before** any money is spent rather
than after a plausible-looking answer comes back.

For that to be mechanical the third column has to be a path and not prose, which is a constraint
on the format rather than on the engine. We have adopted: **a path expression rooted at the
variable — dotted names with `[]` for "each element" — or one of the literals `(whole value)` and
`(not in the input)`, comma-separated where a row names more than one.** Nothing else. Our own
first draft failed this and we tightened it; rows like *"verse markers carry `sid`; word anchors
carry `srcloc`"* became `[].content[].sid`, `[].content[].srcloc`, which we verified against real
data before writing.

A worked consequence: `pericope_synthesis_input` → `analyses_summary[].id` resolves today. Had the
producer renamed that key, the check would have failed at render on the first call, instead of the
model reading nothing there and composing ids from what a Philemon id usually looks like.

### One authoring trap worth putting in the standard

Writing the variable as `` `{{pericope}}` `` in the table **injects the entire object into the
table cell**. We did exactly that, and our own
`tests/test_prompt_variable_expansion.py::test_no_object_is_expanded_into_prose` caught it with a
message that named the fix — *"Drop the braces to reference the variable by name, or use
`{{var.field}}` to interpolate one field."* So the convention has to be: braces only where you mean
injection, bare backticked name everywhere you mean reference. That test is a good one and you may
want its equivalent in `sp lint`, since the failure is silent at render time and expensive in
tokens.

## Your grammar's C1 and your §4.1 measurement disagree, and it is four files not one

`2026-09-16-one-established-order-for-prompt-sections.md` §2 states:

> C1 — `variables` present iff the prompt declares template variables

and stresses that a bracket is *"conditional, never discretionary"*. Read literally, C1 fires on
every prompt that declares a template variable. All five of ours do — `requires:` carries 8, 6, 5,
5 and 3 entries respectively, and every one is injected under `# INPUT DATA`. **Only one of the
five has a `# VARIABLES` section** (`pericope-analysis.gpt`).

So C1 as written makes four of our five prompts non-conformant. But your §4.1 measured
`synthesize-book-arc.gpt` — one of the four — and recorded its top-level order as **"already
conformant"**, listing PRODUCES, SYSTEM ROLE, DATA SOURCES, INPUT DATA, OUTPUT SCHEMA, band,
GUARDRAILS, CHECKLIST and no VARIABLES. Your §4 worklist likewise names no VARIABLES work for any
file.

One of the two is wrong, and which decides whether four prompts gain a section:

- **the grammar is right** — we add `# VARIABLES` to four files, and your §4.1 measurement missed
  it on the file you measured most closely;
- **the worklist is right** — C1 means something narrower than "declares template variables", and
  it needs rewording, because two readers here reached the opposite conclusion from the same
  sentence.

Our reading of the intent, offered only as a guess: C1 may be aimed at prompts where a variable
needs *documenting* separately from where it is injected, and `# DATA SOURCES` already does that
job in our five — it names each variable and its fields. If that is right, then `# DATA SOURCES`
and `# VARIABLES` overlap and the grammar should say which one discharges the condition.

**We have not added the sections**, and we are not working around it. Taking your offer in §4.1
literally: *"If your blocker is something else in this file, tell us and we will amend rather than
have you work around it."*

## A second finding: the debug record holds only half of each request

We went to the captures to show that schema `description` text reaches the model, and could not,
because **the captures do not record it.**

`*-request.txt` contains the rendered prompt and nothing else — `grep -c response_format` and
`grep -c json_schema` both return 0 on
`output/intermediate/debug/book-discourse-flow/book-Mark/0023-subdivide_pericope-request.txt`
(547 lines). `manifest.jsonl` records `step`, `prompt_file`, `model`, `passage`, `iteration`,
timings, token counts, cost and the two filenames — and no schema reference of any kind.

So for a structured-output call, the record of what the model was asked is incomplete, and which
schema was in force at the time is not recoverable from the capture directory. Our two schemas
carry 19 and 27 `description` fields between them; whatever their effect, they are not in the
audit trail. We would find `schema_file` in the manifest useful on its own, ahead of anything
else in this letter — it is one field, and it would also give `sp tools replay` the resolution
path discussed in the 2026-09-09 thread.

## What we are not doing

**Not building a local version.** We could add a project test binding each prompt to its wired
schema, and for five of our seven prompts it would work. It would not work for the one wired to
three schemas, and every other project using `sp` would write the same test differently. This is
one implementation in the engine or N in the consumers.

**Not adding a `schema:` line to our prompts**, for the reason you gave us.

**Nothing is blocked.** Our prompts run, the pipeline lints clean, and the stale description above
is a one-line fix we will make regardless of what happens to this proposal. The requirement we
cannot meet without you is the *guarantee* — that the two cannot silently disagree — not the
current state of agreement.
