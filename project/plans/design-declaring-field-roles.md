# Design — declaring what each field in a response is for

**Status: ruled 2026-09-03, and scoped to release 0.2.1.27.** All six open decisions in §8 are
answered; the ruling cut the design down rather than approving it as drafted. §10 states what
building it means. #230

The one ruling to read first, because it is what the rest follows from: *"it's analogous to sp
trying to own the application semantics of the pipelines that use it."* Each layer declares what it
knows and stops.

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

**Two values, ruled by the Captain on 2026-09-03.** Both are his words:

| role | what it is |
|---|---|
| `evidence` | copied from the input so the model attends to it before deciding, and so a human or an audit can check the claim beside it |
| `content` | what the pipeline exists to produce |

An earlier draft of this section proposed four, adding `handoff` and `adjudication`. The Captain
cut both, and the test he gave applies to this document as much as to the consumers who asked:

> Prescribing the application semantics of downstream clients you don't even know about is
> generally a bad idea, and it makes the design much more complicated.

> it's analogous to sp trying to own the application semantics of the pipelines that use it.

Each layer declares what it knows and stops. `sp` owns the vocabulary and the mechanism; a pipeline
declares which of its fields are which; a consumer decides what to do about it.

**`handoff` describes what a later step does, which the engine cannot check.** The fact is real —
`segment_directives` is produced by `pericope-analysis.gpt`, consumed by `segments.gpt`, dropped by
`merge_results`, copied from nothing, seen by nobody — and it is a fact `discourse-flow` knows about
their own pipeline. But the engine's two checks are the order rule and structural validity, and a
handoff field takes part in neither. So `sp` defines `evidence` and `content` and **does not reject
a role it has not defined**: a project needing `handoff` declares it and writes its own check. The
alternative — leaving such a field out of the map — would make an undeclared field and a handoff
field indistinguishable, which `say-which-kind-of-nothing` forbids.

**`adjudication` is answered by `supports`, on the evidence that was offered for it.**
`discourse-flow` measured, across seven artifacts, that `levinsohn_signals` is copied verbatim at
property 6 of `pericope-analysis.json` and yet **1,985 of 3,593 signals never appear in the claim
it supports — 55.2%**, with 555 of 740 pericopes dropping at least one, from 27% in Mark to 82% in
Revelation. Their conclusion:

> A flat copy adjacent to the claim was therefore **already present and inert**. What we added was
> the per-item verdict.

What makes the per-item verdict work is that `signal` precedes `verdict` **within the item**. That
is an ordering fact, it is what `supports` states, and it is what §4's check enforces. Naming the
field `adjudication` adds a word no check reads. So the finding survives in full and lands in
§4 — which is why `supports` must be expressible inside an array item, and why that is the first
thing built.

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
  levinsohn_signals_to_cite[].verdict: ["levinsohn_signals_to_cite[].signal"]
  rhetorical_features:                 [levinsohn_signals_to_cite]
  is_boundary:                         [verse, greek_quoted, feature_type]
```

A path used as a value is quoted; see §7 for why, and for the block-style alternative.

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

So **not per-item refusal**, which is settled. What the first draft went on to propose — per-field
occupancy reporting, with `empty_expected` as a declarable property — the Captain cut on
2026-09-03, and the tables above are the reason it looked attractive rather than a reason to keep
it. Reporting "this evidence field is empty 936 of 936 times" needs a threshold before it is a
finding rather than a number, and where that threshold sits is a judgment about somebody else's
data. Likewise `empty_expected`: whether *"empty when the detail is purely text-grounded
perception"* is legitimate is a statement about the domain, and `ears-to-hear` already carries it
in their own nullability rule (`schema-requirements.md §5`), so restating it here would be a second
encoding that can only drift from theirs.

The measurements keep their force and change hands. Nothing stops either project computing
occupancy from the very same declaration — the map is machine-readable and complete, which is what
`discourse-flow` asked for in order to test it against `merge_results`. The engine supplies the
declaration; the threshold and the verdict are theirs.

**Severity is the pipeline's, not the engine's** — `discourse-flow`, reconciling two of their own
rules (*a crash on bad data is often correct*, and *never soften a raise to make a run pass*):

> `sp` computes the verdict and exposes it; the pipeline says `fatal` or `report`.

That also matches how they debug — `--stop-after` and reading intermediates needs the response to
exist even when its evidence is empty. It is also the same division the Captain ruled the same day
for empty payloads under `say-which-kind-of-nothing`: the engine reports what it found and stops,
and what it means for the run belongs to whoever declared the pipeline.

So the verdicts `sp` computes are the two it can compute without knowing any domain:

1. **the order rule** — every `supports` entry, supporting path before supported path, at both the
   top level and inside an array item
2. **structural validity** — every declared path exists in the schema, no path declared twice

## 7. The declaration, entire

```yaml
# schemas/pericope-analysis.roles.yaml
schema: schemas/pericope-analysis.json

fields:
  verse:                               [evidence]
  greek_quoted:                        [evidence]
  opening_word_id:                     [evidence, content]
  levinsohn_signals_to_cite[].signal:  [evidence]
  is_boundary:                         [content]
  rhetorical_features:                 [content]

supports:
  levinsohn_signals_to_cite[].verdict: ["levinsohn_signals_to_cite[].signal"]
  rhetorical_features:                 [levinsohn_signals_to_cite]
  is_boundary:                         [verse, greek_quoted]

identifies:
  segments[]: canonical_reference
```

**A path used as a value must be quoted.** An earlier version of this example was not, and did not
parse — `discourse-flow` copied it and four of their five maps failed with
`ParserError: while parsing a flow sequence`, reported 2026-09-04. The cause is YAML rather than
anything about roles: inside a flow sequence, the `[` of `[]` opens a nested sequence.

| construct | parses |
|---|---|
| `a[].b: evidence` — array path as a **key** | yes — YAML reads a plain scalar up to the colon |
| `a[].b: [evidence, content]` — a role list | yes |
| `a[].v: [a[].s]` — array path as an unquoted **value** | **no** |
| `a[].v: ["a[].s"]` | yes |
| `a[].v:` then `- a[].s` — block style | yes |

So only `supports` and `identifies` values need the quotes, and only when the path reaches into an
array. Block style is equally valid and may read better for a long list. The reader must accept
both, and the structural check should say *"quote paths used as values"* when a map fails to parse,
because that error message is otherwise about flow sequences and tells nobody what to do.

That is the whole vocabulary: two role words, a list per field, `supports`, `identifies`. Nine
lines of declaration for a schema with three anchors.

Read by three things, none of which needs to ask anyone:

1. **the order check** — every `supports` entry, supporting path before supported path, at the top
   level and inside an array item
2. **structural validity** — every declared path exists in the schema, no path declared twice
3. **the coverage check** — `identifies` against what was requested

`levinsohn_signals_to_cite[].verdict` appears in `supports` without appearing in `fields`, and that
is deliberate: what the engine needs to know about it is what it is ordered against, not what to
call it. A project wanting a name for it — `adjudication`, or anything else — declares one, and
`sp` will not reject a role word it has not defined.

**Audience is not here and will not be.** It stays in `ears-to-hear`'s `x-display`, on their axis,
decided by `reviewer.md §4a` per field. An earlier draft of this section offered to un-conflate
their `"none"` for them; that offer is withdrawn as the same overreach this design was cut back
for, pointed the other way.

**`identifies` is the one item still worth arguing about.** It carries the coverage check, which is
a real silent-truncation defect (`discourse-flow`'s #162: 3 of 99 leaf pericopes in Mark, silently).
But "this array is keyed by that field" may be a coverage concern rather than a role one, in which
case it belongs in its own declaration rather than sharing this file. It ships here because the two
travel together today; splitting it later costs a rename.

## 8. Decisions — ruled 2026-09-03

Five of the six were closed by one ruling, and the sixth stopped being ours. The ruling, in the
Captain's words:

> I doubt we need the complexity discourse flow and ears to hear asked for. I think they are trying
> to guess what other downstream applications might do with their data or how they might interpret
> their data, and they have no way of knowing that. Prescribing the application semantics of
> downstream clients you don't even know about is generally a bad idea, and it makes the design much
> more complicated.

> it's analogous to sp trying to own the application semantics of the pipelines that use it.

The second sentence is the test, and it applies to this document as much as to the consumers whose
proposals it was aimed at. Read the questions below as answered; they are kept with their original
wording so the reasoning is checkable, per `one-design`.

### 1. Four roles, or fewer? — **RULED: two.**

`evidence` and `content`. `handoff` describes what a later step does; `adjudication` describes a
field's part in a decision. Both are statements about what someone *else* does with the data, which
is the thing this ruling says a producer cannot know. §3 records how each is met: `handoff` is a
fact its project declares for itself and `sp` does not reject undefined role words; `adjudication`
is carried by `supports`, on the evidence offered for it.

### 2. Are `handoff` and `adjudication` the right names? — **MOOT.** Neither is engine vocabulary.

Whether a project's own map calls it `handoff` or `intermediate` is that project's naming.

### 3. Does `sp` own the checks, or only the vocabulary? — **RULED: the vocabulary, plus the two checks that need no domain knowledge.**

The order rule and structural validity. Not severity — that is the pipeline's, which is also what
`discourse-flow` asked for. Not occupancy. The distinction is whether the check can be computed
without knowing whose data it is.

### 4. Is `empty_expected` the right shape for legitimate emptiness? — **RULED: dropped.**

It was a per-field exemption from an occupancy expectation that no longer exists. `ears-to-hear`
already carries the distinction in a nullability rule (`schema-requirements.md §5`), so declaring
it here would have been a second encoding, able only to drift from theirs. Whether an empty value
is legitimate is a statement about a domain.

### 5. Which schema is mapped first? — **NOT OURS.**

Once `sp` ships only the vocabulary, which schema a project maps first is that project's rollout.
`ears-to-hear`'s suggestion — `scene-hearts.schema.json`, where their ordering defect is measured,
paired with Bodies where the pattern is already right — is a good way to test it, and a known-bad
case is worth more to us than a clean one. But we do not choose it for them.

### 6. Which release? — **RULED: 0.2.1.27.**

Not 0.2.1.26, which was in its release build when this was ruled. The Captain's reason for not
deferring it further:

> I am cleaning up cruft in general so that we can have a clean infrastructure to build on NOW,
> before we spend the money to rebuild everything.

So it ships before the rebuild it exists to support, not after it.

**One item keeps its clock and is not the mechanism.** `discourse-flow`'s §1 finding: two synthesis
anchors are published in an artifact `ears-to-hear` is building coverage assertions against *this
month*. Nothing in 0.2.1.27 changes that and waiting for it would waste the month. Written to both
projects on 2026-09-03 as `collab/*/2026-09-03-the-live-coupling-between-you-two.md`; the
drop-or-keep decision is the Captain's and is in front of him.

## 9. What is not proposed

- No change to `x-display`, which is `ears-to-hear`'s and adequate for what it scopes. An earlier
  draft offered to un-conflate their `"none"`; withdrawn as overreach.
- No change to how copy forcing works, to any prompt, or to property order — beyond making the
  existing ordering rule *stated* so it can be tested.
- No occupancy reporting, no `empty_expected`, no severity, no audience. Each needs a judgment about
  somebody else's data.
- Nothing built. No role map exists; every example here is a sketch.

## 10. What building it means, for 0.2.1.27

In dependency order. The first item is the one that carries `discourse-flow`'s 55.2% finding, so it
is not optional:

1. **`supports` inside an array item.** Path syntax that reaches `a[].b`, and the order check over
   it. Without this the check degrades to "some evidence exists somewhere", which is the defect it
   exists to catch.
2. **The declaration read and structurally validated.** Every declared path exists in the schema,
   no path declared twice, list-valued roles over `evidence` and `content`, undefined role words
   carried without complaint.
3. **The order check at the top level**, which falls out of 1.
4. **`identifies` and the coverage check** — or a decision to split it into its own declaration
   first, per §7.

Reported, never judged. A pipeline says what is fatal.
