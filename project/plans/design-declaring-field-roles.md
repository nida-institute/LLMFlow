# Design — declaring what each field in a response is for

**Status:** proposed — **not authorization to build.** Six decisions are marked `=>` and are the
Captain's. Whether any of it belongs in release 0.2.1.26 is the last of them. #230

Origin: the Captain, 2026-09-02, on why the engine needs this at all —

> copy forcing is VERY important, we do say something about that, but we don't have general
> guidelines for distinguishing copy forcing data from data we want for consumers, and that makes
> later processing messy

> It also prevents LLMs from asking me yet one more time to rule on the use of each datum it
> produces

And on what copy forcing is *for*, which corrects the first draft of this design —

> the main purpose of copy forcing is to focus the LLM's attention on the data it needs to
> decide. without it, hallucinations skyrocket. it is also useful for humans verifying output and
> for `/audit-output`

> LLM fatigue has been a HUGE problem in this project, and copy forcing is one of the most useful
> tools for combatting it

> e.g. an LLM processes the first N pericopes, silently stops, and ensures us it processed the
> whole thing.

Two consumer projects answered a proposal built on the wrong premise. Their measurements are the
substance of this document and are cited to them; the naming choices are mine and are labelled.

---

## 1. What the first draft got wrong

It led with display — *which fields a reader is meant to see* — and treated schema property order
as a footnote. Both consumers said the priority is inverted, and `ears-to-hear` supplied the
Captain's ordering of consumers: **the generating model first**, then a human verifying, then
`/audit-output`.

That matters because the two halves need different things. A display declaration answers "render
this?"; an attention declaration answers "did the model look before it decided?" — and the second
is checkable only from **property order**, which no schema and no display map can state.

`ears-to-hear` also withdrew an inference in a way worth preserving, because it is the sharpest
evidence in either reply:

> Our first pass found `textual_basis` populated in **10,352 of 10,354 instances across six
> books** … and read that as evidence the forcing device works. It is not. A field generated
> *after* the claim is a post-hoc citation, and a model that has already decided can nearly
> always find something to quote. **The 99.98% fill rate is exactly what a non-functioning
> forcing device looks like.**

So a full evidence field proves nothing on its own. Only its *position* does.

## 2. What already exists, and why neither half can be stretched

**`ears-to-hear` has the display axis, and it is mature.** `x-display`, authority
`project/specs/schema-requirements.md §3`, deployed across 13 of 21 schemas — 94 declarations in
`book-hierarchy.schema.json` alone — with a conformance suite, schema-derived coverage tests and a
generation-time self-check.

It cannot be extended, by its own terms: `:59` scopes it to *"the reader and the reviewer — the
only two artifacts that render `book.json` fields directly"*, and `:74` bars growing the
vocabulary for other consumers. Decisively, its third value conflates the two things this design
must separate:

> `"none"` — internal only: **LLM-forcing or bookkeeping**; shown by neither

28 of their properties are `"none"`, and nothing distinguishes `sequence` — an integer ordinal —
from the forcing echoes settled as `"none"` in their §7.

**`discourse-flow` has the role axis, and it is Python.** `plugins/pericope_packaging.merge_results`
builds the artifact from an explicit field list; anything unnamed is dropped. That function *is*
the evidence/content boundary today — unreviewed, untested against any declaration, and
inconsistent across three steps:

| step | its evidence fields |
|---|---|
| segmentation | dropped |
| analysis | dropped |
| **synthesis** | **published** — `book_arc` ships `pericope_ids_to_assign` (99 entries) and `keyword_pattern_evaluation` (15) |

Nobody decided that. And `ears-to-hear` is currently writing a build-time coverage assertion that
derives expected counts from that artifact, so evidence arrays are about to become load-bearing
input somewhere as though they were content.

**Conclusion: two axes, not one.** Audience is `ears-to-hear`'s and stays theirs. Role is what
`sp` should declare. They compose; neither subsumes the other.

## 3. Axis one — role

A field's role is what it is *for*. **A list, not a scalar**, because `discourse-flow` produced a
counterexample their work depends on:

```yaml
opening_word_id: [evidence, content]
```

— copied verbatim from the window, validated against it, **and** the value every identifier in the
artifact is minted from (`pericope:n41001001001-n41001008014`), which `ears-to-hear` keys on. One
value per field forces a wrong answer on their most important field.

Four values. The first two are the Captain's words; the third and fourth are named from live
instances the consumers supplied, and the names are mine:

| role | what it is |
|---|---|
| `evidence` | copied from the input so the model attends to it before deciding, and so a human or an audit can check the claim beside it |
| `content` | what the pipeline exists to produce |
| `handoff` | consumed by a later step; no reader ever sees it |
| `adjudication` | the model's per-item disposition of evidence it has just copied |

`handoff` is not hypothetical: `segment_directives` is produced by `pericope-analysis.gpt`,
consumed by `segments.gpt`, dropped by `merge_results`, copied from nothing, seen by nobody.

**`adjudication` is the one that earns its place, and the measurement is the argument.**
`discourse-flow`, 2026-09-03, across seven artifacts: `levinsohn_signals` is already copied
verbatim at property 6 of `pericope-analysis.json`, and yet **1,985 of 3,593 signals never appear
in the claim it supports — 55.2%**, with 555 of 740 pericopes dropping at least one, ranging from
27% in Mark to 82% in Revelation.

> A flat copy adjacent to the claim was therefore **already present and inert**. What we added was
> the per-item verdict. If the role vocabulary cannot distinguish `signal` from `verdict`, it
> cannot express the difference between the anchor that works and the one that does not.

So `{lemma, verdict, reason}` is `[evidence, adjudication, adjudication]`, and a vocabulary that
called all three `evidence` would describe the working and the inert device identically.

**The role belongs to the (schema, field) pair, not to the field name.** `levinsohn_signals` is
copy-forced evidence in `pericope-analysis.gpt` — its schema block reads `"<COPY from pericope>"` —
and simultaneously payload `ears-to-hear` depends on, one step later. Same name, opposite roles.
That rules out a single project-level file and settles the map's location: **beside each schema.**

## 4. The order rule, which is the whole point

> whatever the declaration ends up being, make the *order* rule testable from it. Everything else
> in this proposal is a convenience; that one addresses what the Captain says the technique is for.
> — `ears-to-hear`

A model generates properties in schema order, so evidence placed *after* a claim is a post-hoc
citation and forces nothing. Neither project can state that rule today, and both are violating it
where it costs most:

| schema | property order | evidence lands at |
|---|---|---|
| `appraisals[]` | `category`, `description`, **`textual_basis`**, `certainty`, `background_ids` | 2 of 5 |
| `movements[]` | seven content properties, **then `textual_basis`** | 7 of 9 |
| `narrator_signals[]` | `signal_type`, `description`, `implication`, **`textual_basis`** | 3 of 5 |
| `book-literary-patterns` | five content properties, then `occurrences` | last |

Hearts is their most interpretive layer, where hallucination costs most. Their per-item wrappers
are correct — `canonical_reference` at index 0 in nine schemas — so this is not incompetence, it
is an unstated rule that a schema edit can silently break.

`supports` is what makes it testable, and it must work **inside an array item**, which the first
draft could not express:

```yaml
supports:
  levinsohn_signals_to_cite[].verdict: [levinsohn_signals_to_cite[].signal]
  rhetorical_features:                 [levinsohn_signals_to_cite]
  is_boundary:                         [verse, greek_quoted, feature_type]
```

The check: for every entry, each supporting path must appear **earlier in property order** than
the path it supports, at the same nesting level. That is one statement, generic over every schema,
and it is the only thing here that addresses the primary consumer.

## 5. Coverage — the silent-truncation half

The Captain's example is measurable in committed output. `ears-to-hear`'s
`plugins/book_assemble.py:123` iterates `bodies_list`, and `:126` resolves the other layer with
`hearts_by_ref.get(canonical_ref, {})`:

> **The iteration source is what the model returned, not what was requested.** If Hearts returns
> 8 of 14 segments, the missing 6 resolve to `{}` and disappear.

And the completeness assurance is the model's own self-report, defaulting to yes:

| book | said content, array empty | said none, content present | flag absent entirely |
|---|---|---|---|
| Luke | **9** | 0 | 0 |
| Genesis | **3** | 0 | 0 |
| Mark | 0 | 14 | 0 |
| Psalms | — | — | **331 of 331** |

Their own conclusion, and the strongest argument in either reply:

> The copy-forced `canonical_reference` is already the exact key that would catch all of this —
> assembly uses it as a **dictionary key** but never as a **checklist**. Declaring a field as *the
> evidence identifier for this item* is what turns "did every requested item come back?" into a
> generic check.

So the declaration needs one more thing — which evidence field identifies the item:

```yaml
identifies:
  segments[]: canonical_reference
```

Given that, `sp` can compare the identifiers returned against the identifiers requested and report
what is missing, for any schema, with no per-plugin code. `discourse-flow`'s issue #162 — a nested
walk that built 3 of 99 leaf pericopes in Mark, silently — is the same defect.

## 6. What the check must and must not do

The first draft proposed refusing a response whose content has empty evidence. **`ears-to-hear`
showed that rejects ~700 valid items in Mark alone:** `background_ids` is legitimately empty by its
own schema description — *"Empty when the detail is purely text-grounded perception"* — in 313 of
915 sensory items and 383 of 1,150 appraisals.

But the same measurement found what per-item refusal would have missed and per-field reporting
catches:

| | Genesis | Psalms | Luke | Mark |
|---|---|---|---|---|
| sensory items, `background_ids` empty | **936/936** | **1048/1048** | **874/874** | 313/915 |
| appraisals, `background_ids` empty | **1077/1077** | **842/842** | **1275/1275** | 383/1150 |

Three books at 100% — 3,061 sensory items and 3,194 appraisals where the citation link was never
made at all, and every existing check passes because each field is individually well-formed. Same
class: `boundary_signals`, present on **735 of 735 pericope nodes and non-empty on none**.

So: **per-field occupancy, reported; not per-item refusal.** And an evidence field must be able to
say that empty is legitimate for it.

**Severity is the pipeline's, not the engine's** — `discourse-flow`, reconciling two of their own
rules (*a crash on bad data is often correct*, and *never soften a raise to make a run pass*):

> `sp` computes the verdict and exposes it; the pipeline says `fatal` or `report`.

That also matches how they debug — `--stop-after` and reading intermediates needs the response to
exist even when its evidence is empty.

## 7. The declaration, entire

```yaml
# schemas/pericope-analysis.roles.yaml
schema: schemas/pericope-analysis.json

fields:
  verse:                                 [evidence]
  greek_quoted:                          [evidence]
  opening_word_id:                       [evidence, content]
  levinsohn_signals_to_cite[].signal:    [evidence]
  levinsohn_signals_to_cite[].verdict:   [adjudication]
  levinsohn_signals_to_cite[].reason:    [adjudication]
  segment_directives:                    [handoff]
  is_boundary:                           [content]
  rhetorical_features:                   [content]
  background_ids:                        [evidence]
    empty_expected: true       # "empty when the detail is purely text-grounded perception"

supports:
  levinsohn_signals_to_cite[].verdict: [levinsohn_signals_to_cite[].signal]
  rhetorical_features:                 [levinsohn_signals_to_cite]
  is_boundary:                         [verse, greek_quoted]

identifies:
  segments[]: canonical_reference
```

Read by four things, none of which needs to ask anyone:

1. **the order check** — every `supports` entry, supporting path before supported path
2. **the coverage check** — `identifies` against what was requested
3. **occupancy reporting** — per evidence field, how often empty, with `empty_expected` as context rather than exemption
4. **`/audit-output`** — every claim against its declared basis, replacing the five-claim hand-picked spot check the shared skill does today against Mark's 1,150 appraisals

Audience stays in `ears-to-hear`'s `x-display`. The role map lets them un-conflate their `"none"`:
a `"none"` field is now either `handoff`, `evidence` that did not earn display, or bookkeeping.

## 8. Decisions

**Answer inline after each `=>`.**

### 1. Four roles, or fewer?

`evidence` and `content` are yours. `handoff` and `adjudication` come from live instances, but
`adjudication` in particular could be argued as a kind of content. The 55.2% measurement says the
distinction is what separates a working forcing device from an inert one — but that is an argument
for the *mechanism*, not necessarily for a fourth vocabulary item.

=>

### 2. Are `handoff` and `adjudication` the right names?

`discourse-flow` offered `handoff` or `intermediate` and had no strong view. `adjudication` is
mine. Both become vocabulary the moment a map is written.

=>

### 3. Does `sp` own the checks, or only the vocabulary?

The engine could ship all four checks and expose verdicts, with the pipeline declaring severity —
which is what `discourse-flow` asked for. Or `sp` could define the declaration and leave every
check to the projects. The first is uniform and is real engine work; the second ships in a day.

=>

### 4. Is `empty_expected` the right shape for legitimate emptiness?

It is a per-field exemption from the occupancy expectation. `ears-to-hear` carries the same
distinction in a nullability rule (`schema-requirements.md §5`), so this may be a second encoding
of something they already declare — in which case the role map should read theirs rather than
restate it.

=>

### 5. Which schema is mapped first?

`ears-to-hear` suggests `scene-hearts.schema.json` (a known ordering defect) paired with Bodies (a
known-good case), to test the vocabulary against both. `discourse-flow` owes five maps once the
vocabulary settles.

=>

### 6. Does any of this go in 0.2.1.26?

My recommendation is **no, with one exception.** The vocabulary is two days old, three of its four
values were discovered by these replies, and both projects have asked for changes to the shape.
Designing it under release pressure is how it ends up wrong.

The exception is not a feature: **`discourse-flow`'s §1 finding is live.** Evidence arrays are
published in an artifact `ears-to-hear` is building coverage assertions on *this month*. That
wants a note between the two projects now, whatever happens to the mechanism.

=>

## 9. What is not proposed

- No change to `x-display`, which is `ears-to-hear`'s and adequate for what it scopes.
- No change to how copy forcing works, to any prompt, or to property order — beyond making the
  existing ordering rule *stated* so it can be tested.
- Nothing built. No role map exists; every example here is a sketch.
