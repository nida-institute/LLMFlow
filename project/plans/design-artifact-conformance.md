# Check a produced artifact against the schema its pipeline declares, and record a defect

Status: proposed (2026-09-21)

Targets 0.2.1.28. **Proposed is not authorization to build** — the four decisions at the foot are
unanswered, and they change what gets built.

**This document is also the drafted body of a GitHub issue that has not been created.** The title
above is the issue title. Once the issue exists, put its number here and the document becomes an
ordinary design note.

## What

A pipeline can declare the shape of what it produces, and nothing checks the thing it actually
produced against that declaration.

## Why it is the engine's

Reported by `nida-institute/discourse-flow` in
`collab/discourse-flow/2026-09-21-a-second-defect-log-and-three-more-things-sp-could-carry.md`.
They declare `schemas/pericope-unified.json`, describing their finished artifact. Nothing checks
against it, and it has been wrong in two ways for months with nothing noticing: it does not
declare their two node kinds, and it says nesting is unbounded where their design says depth is
exactly one.

That is the shape of the failure — not a bad artifact, but a declaration quietly drifting from
what is produced, with no moment at which the two are compared.

## What the engine has, and why none of it covers this

| existing | what it checks | why it is not this |
| --- | --- | --- |
| `schema_preflight` | a schema is legal for strict structured output | about what goes *to* a model |
| `response_format` / `json_schema` | a model's reply conforms | one step's output, at the moment it is produced |
| `json_schema_validator` step | data passing through a step | a step the author remembers to add, mid-pipeline |
| `Pipeline.schemas()` | which schemas a pipeline references | reports, checks nothing |

The gap is the **final artifact**: the file a pipeline exists to produce, checked against the
shape its author declared for it, at the end of the run.

## What to build

A declaration on the pipeline naming an artifact and the schema it must conform to, checked
after the run has written it.

**Reported as a defect, not raised.** Same cost asymmetry the engine already took for #232: a
book run is an hour and real money, a hard stop buys one report where finishing buys the whole
list, and the reader needs the output in order to judge the finding. It reports through the
`defects` channel, so it lands in `defects.json` and the end-of-run summary with everything else.

**`[]` and absence must differ**, per `say-which-kind-of-nothing`: a run that checked and found
the artifact conformant is not a run that checked nothing.

## Decisions needed before anything is built

**D1 — where the declaration goes.** A root-level key mapping artifact to schema, a key on the
`saveas` that produces it, or a step type that runs at the end. The `saveas` form puts the
declaration where the file is named; a root key keeps it readable as a contract for the pipeline
as a whole.

=>

**D2 — what counts as the artifact** when `saveas` is content-derived and a run writes many
files. #245's run manifest now records every path a run wrote, which is a candidate answer:
check what the run recorded writing, filtered by the declaration.

=>

**D3 — whether a missing artifact is a defect or silence.** A step that did not run because of
`if:` leaves no file, and that is not a conformance failure.

=>

**D4 — whether this runs under `--dry-run` and `--rewind-to`.** Neither produces a full artifact
set; #245 settled the analogous question for cleaning by skipping under rewind.

=>

## Related

- #232 — the defect channel this reports through. Shipped in 0.2.1.27.
- #245 — the run manifest, which already knows every path a run wrote.
- `say-which-kind-of-nothing` — governs how "checked and clean" is distinguished from "not
  checked".
