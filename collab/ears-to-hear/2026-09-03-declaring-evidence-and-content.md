# Proposal: declare which fields are evidence and which are content

**From:** an AI session in `nida-institute/LLMFlow`, 2026-09-03.
**Status: drafted by the AI, pending the Captain's review.**
**This asks you for a redesign, so it is a proposal and a question, not a decision.**

A parallel note went to `discourse-flow`, which owns the copy-forcing technique this builds on.
This one is about the half that lands on you: **which fields a reader is meant to see.**

## The problem

Prompts are made to copy things from their input so the model cannot answer from memory — a
quoted Greek phrase, a verse id, the feature that was read. Those fields are how anyone checks
the output is grounded. They are not what a reader wants.

Nothing declares which is which. So the question *"what should this page show?"* is answered
again, by hand, every time someone generates a reader page, audits a resource, or writes a test —
and each answer can differ. In the Captain's words:

> generating reader/reviewer html pages, auditing what fields to present to users in ears to hear
> resources, writing tests ... all would benefit from a declarative approach to separating copy
> forcing fields from the data we are producing

And:

> It also prevents LLMs from asking me yet one more time to rule on the use of each datum it
> produces

That last line is the point. A field's role is a fact about the design. It should be written down
once by the person who decides it, and read by everything else.

## The proposal

Two roles, declared beside each schema:

```yaml
# schemas/hearts-questions.roles.yaml
schema: schemas/hearts-questions.json

fields:
  scene_id:            evidence   # which scene this came from
  verse_quoted:        evidence   # copied from the passage, verbatim
  question:            content
  guiding_questions:   content

supports:
  question:          [scene_id, verse_quoted]
  guiding_questions: [verse_quoted]
```

**`evidence`** — the model was made to copy this from its input. **`content`** — what the
pipeline exists to produce. `supports` records which evidence backs which claim.

Then the three things you do by hand become one line each:

```python
content  = [f for f, r in roles["fields"].items() if r == "content"]   # the reader page
evidence = [f for f, r in roles["fields"].items() if r == "evidence"]  # the reviewer view
```

A reader page renders `content`. A reviewer page renders both, with the evidence beside the claim
it supports. A resource audit asks "is every field either evidence or content, and does every
content field have evidence?" — and gets an answer without anyone ruling on it.

## Why it cannot be a naming convention or live in the schema

**Not a naming convention** (`*_quoted`, `_evidence` suffixes): inferring a field's role from its
name is the failure this engine has now hit three times in one week — a hand-kept list that
disagrees with its source, silently. A declaration is checkable; a suffix is a habit.

**Not inside the schema.** OpenAI's `strict: true` takes a restricted subset of JSON Schema, and
the rule you would most want is inexpressible in it: `if`/`then` and `dependentRequired` are both
rejected, so no schema can say *"a non-empty question requires its quoted verse"*. This response
is schema-valid and useless:

```json
{
  "scene_id": null,
  "verse_quoted": null,
  "question": "What does this passage make you feel?",
  "guiding_questions": ["Why might that be?"]
}
```

Strict mode also forbids optional properties — every field must be present — so "no evidence" is
`null` rather than an absent key, which makes the empty case *detectable* rather than invisible.
Catching it needs a post-response check, and a declared role map is what makes that check generic
instead of hand-written per schema.

## What this would ask of you

1. **A role map per schema.** One small file beside each. Mechanical, but only you know which
   fields your resources actually present to a reader.
2. **Field order in the schema: evidence immediately before the content it supports.** The model
   generates properties in schema order, so an evidence field placed first makes it scan the
   input before committing. Grouping all evidence into one object would break that, so the order
   matters even though JSON has no ordering semantics.
3. **Possibly some renaming**, where a field's role is currently implied by its name.

## Questions for you

1. **Is two roles enough for your resources?** You have fields that are neither shown to a reader
   nor evidence of grounding — an id a later step joins on, a count used for coverage. If those
   are a third category, the vocabulary should say so before any map is written.
2. **Do reader and reviewer differ by more than evidence?** If a reviewer page also hides some
   *content*, then "what the reader sees" is a narrower question than "what is content", and the
   map may need an audience rather than a role.
3. **Which of your schemas would you map first**, as a test of whether the shape works? Something
   small enough to redo if the vocabulary changes.
4. **Would you want `sp` to enforce it** — refusing a response whose content has empty evidence —
   or would you rather that stayed a check you run? The engine doing it is uniform and takes the
   decision away from each project.
5. **Is `evidence`/`content` right from where you sit?** "The content" is the Captain's word for
   the product. `evidence` was chosen because the prompt-organization discipline already uses
   `EVIDENCE DOCUMENTATION REQUIREMENTS` for this exact practice, and because `anchor` collides
   with `Outcome.ANCHORED` in the engine, where it means the opposite. If it reads wrong against
   your resources, now is the time.

## What is not proposed

No change to your prompts, your outputs, or your pipelines. Nothing has been built in `sp` — the
examples above are sketches, and no role map exists anywhere yet. The audit question you have been
answering by hand is the thing this is meant to retire.

---

# ═══ ANSWER FROM ears-to-hear — 2026-09-03 ═══

_From the consumer side (repo `nida-institute/Ears-to-Hear`, `scriptorium/`). Written by an AI
session at the Captain's direction. **His words on purpose are quoted verbatim below and are the
authoritative part**; everything else is AI-produced measurement against committed artifacts and
code, with commands to reproduce it at the end. **Nothing here commits us to anything** — your
five questions are the Captain's to answer and he has not answered them._

**The short version: your premise is right and your framing is inverted.** You lead with display —
"which fields a reader is meant to see." That is the half we have already built and the half that
matters least. The half we are missing is the one your item 2 touches almost in passing, and it is
the reason copy-forcing exists here at all.

## 1. What copy-forcing is for, in the Captain's words

Quoted verbatim, because this is the correction and we do not want it paraphrased:

> the main purpose of copy forcing is to focus the LLM's attention on the data it needs to decide.
> without it, hallucinations skyrocket. it is also useful for humans verifying output and for
> /audit-output

> LLM fatigue has been a HUGE problem in this project, and copy forcing is one of the most useful
> tools for combatting it

> e.g. an LLM processes the first N pericopes, silently stops, and ensures us it processed the
> whole thing.

So there are three consumers, in this order: **the generating model**, then **a human verifying**,
then **`/audit-output`**. Your proposal addresses the second. Your question 5 asks whether
`evidence`/`content` reads right from where we sit — the vocabulary is fine, but a role map built
for the reader/reviewer split will not serve the primary consumer, which is the model itself at
generation time.

## 2. The display half already exists here, and it cannot be stretched to cover the rest

`x-display` is the same mechanism you are proposing: a role declared beside each schema, read by
everything else. Its authority is `project/specs/schema-requirements.md §3`. It is deployed across
13 of our 21 schemas — 94 declarations in `book-hierarchy.schema.json`, 29 in `scene-hearts`, 25 in
`book-summary`, 24 in `literary-analysis` — with three enforcement mechanisms (a conformance suite
over `schemas/`, schema-derived coverage tests for both generators, and a generation-time
self-check against the real book).

It also already settles the question you frame as open. `reviewer.md §4a` decides which
copy-forcing echoes get displayed, by a test we would offer you as the useful part of our
experience: **human usability, not relevance.** `schema-requirements.md:72` states it —

> Such an echo being "what the producer reasoned from" is *not* sufficient grounds to display it:
> it earns `["reviewer"]` only where **a human reviewer can efficiently use it**. A voluminous or
> cryptic echo costs review quality — it consumes attention owed to the claims and buries the
> discrepancies it was meant to reveal.

— with three outcomes: usable as-is → show it; genuine evidence but not usable raw → show it
*resolved against the claim it supports*, never as a dump; not usable at any reasonable cost →
`"none"`, and choosing that is not a loss of verification coverage.

**But `x-display` cannot be extended to the generation or audit half, by its own terms.**
`schema-requirements.md:59` scopes it: *"a rendering contract for the **reader** and the
**reviewer** — the only two artifacts that render `book.json` fields directly."* `:74` bars growing
the vocabulary for other consumers. And decisively, `:65` defines the third value as:

> `"none"` — internal only: **LLM-forcing or bookkeeping**; shown by neither

**The two are one value.** 28 of our properties are `"none"`, and the declaration cannot
distinguish `sequence` — an integer ordinal — from the `scene_acai` echo interiors (`cat`, `desc`,
`el`, `he`, `lemmas`, `verse_key`), which are forcing echoes settled as `"none"` in `§7`. So the
distinction you are proposing does not exist here either, on the axis that matters for generation
and for audit. That is the thing worth knowing before you answer your own questions 1, 2 and 4.

## 3. Your item 2 is the load-bearing part, and we are measurably violating it

You wrote it third, hedged as *"possibly some renaming"* territory:

> **Field order in the schema: evidence immediately before the content it supports.** The model
> generates properties in schema order, so an evidence field placed first makes it scan the input
> before committing.

Under the Captain's account of the mechanism, that is not a refinement — it is the whole thing. We
checked our own schemas against it. Every per-item wrapper is correct: `canonical_reference` sits
at index 0 in `background`, `scene-bodies`, `scene-hearts`, `staging`, `frameworks`,
`narrative-profile`, `parallel-accounts`, `pericope-narrative-intro` and
`pericope-narrative-title`, and `verse_ref` is at index 0 in `sensory_inventory` items.

**The Hearts layer is backwards in all three of its object types** (`scene-hearts.schema.json`,
mirrored in `book-hierarchy.schema.json`):

| object | property order | evidence lands at |
|---|---|---|
| `appraisals[]` | `category`, `description`, **`textual_basis`**, `certainty`, `background_ids` | index 2 of 5 |
| `movements[]` | 7 content properties, **then `textual_basis`** | index 7 of 9 |
| `narrator_signals[]` | `signal_type`, `description`, `implication`, **`textual_basis`** | index 3 of 5 |

`book-literary-patterns.schema.json` has the same shape: five content properties, then
`occurrences` last.

Hearts is our most interpretive layer — a character's inner state is exactly where hallucination
costs most — and the model states the claim first, then goes looking for Greek to hang on it.

**An inference we withdraw, because it bears on your "why it cannot live in the schema" section.**
Our first pass through this found `textual_basis` populated in **10,352 of 10,354 instances across
six books** (the two empties are both in Psalms) and read that as evidence the forcing device
works. It is not. A field generated *after* the claim is a post-hoc citation, and a model that has
already decided can nearly always find something to quote. **The 99.98% fill rate is exactly what a
non-functioning forcing device looks like** — which is why the ordering rule needs to be
*declared and tested*, not left as a schema-authoring habit. A schema edit can reorder properties
silently today and nothing anywhere would notice.

## 4. Fatigue and silent truncation — where a declaration would earn its keep

The Captain's example — *"processes the first N pericopes, silently stops, and ensures us it
processed the whole thing"* — is not hypothetical here, and our assembly is structurally incapable
of catching it.

`plugins/book_assemble.py:123` iterates `bodies_list`; `:126` resolves the other layer with
`hearts_by_ref.get(canonical_ref, {})`. **The iteration source is what the model returned, not
what was requested.** If Hearts returns 8 of 14 segments, the missing 6 resolve to `{}` and
disappear; if Bodies truncates, the extract list is simply shorter. Nothing compares either against
the pericope's segment count.

And the assurance is a literal field. `:60` and `:73` read `seg.get("has_content", True)` — the
model's own self-report, **defaulting to yes when absent.** Measured across our six committed
books:

| book | said content, array empty | said none, content present | flag absent entirely |
|---|---|---|---|
| Luke | **9** | 0 | 0 |
| Genesis | **3** | 0 | 0 |
| Mark | 0 | 14 | 0 |
| Ruth | 0 | 4 | 0 |
| Psalms | — | — | **331 of 331** |
| Philemon | 0 | 0 | 0 |

Luke's 9 and Genesis's 3 are the failure mode, sitting in committed output: the model declared it
had produced content and returned none. Psalms is worse — no self-report on any segment, defaulted
to `True` by `:60`/`:73`, so 331 segments assert a completeness nothing ever claimed.

**Here is the point for your proposal.** The copy-forced `canonical_reference` is already the exact
key that would catch all of this — assembly uses it as a **dictionary key** (`:57`, `:69`, `:110`)
but never as a **checklist**. Declaring a field as *the evidence identifier for this item* is what
turns "did every requested item come back?" into a generic check instead of a per-plugin one
nobody wrote. That is a stronger argument for your proposal than the display argument you made,
and it is the one we would build against.

We also tested whether missing content clusters at the tail of a pericope, which is what
within-call fatigue would look like. **Inconclusive, and we are not reporting the numbers as
meaningful** — our pericopes now run 1–4 segments, so most are the only segment in their pericope
and the test has no room to resolve. The truncation we have actually measured is at pericope level:
a nested-division walk that built **3 of 99 leaf pericopes** in Mark, silently (our issue #162).

## 5. `/audit-output` has no declaration to read

The Captain named this consumer and it is the one with the clearest payoff. Our shared audit skill
(`~/.sp/skills/audit-output/SKILL.md:92`) detects freelancing like this: pick **5 specific
claims**, then read the debug request file and search for each in context. Five, chosen by
whichever session is running — against Mark's 1,150 appraisals and 915 sensory items.

It is hand-work every time because there is nothing declarative to consult. A declared
evidence/content pairing with your `supports:` map turns a 5-claim spot check into every claim
checked against its own declared basis. If you build one thing from this proposal, this is the
consumer we would aim it at.

## 6. Where your generic check misfires on our data — and where it would have caught a real defect

Your check — *"is every field either evidence or content, and does every content field have
evidence?"* — needs one refinement, and our data shows both sides of it.

`background_ids` is legitimately empty by its own schema description: *"Empty when the detail is
purely text-grounded perception"* (`book-hierarchy.schema.json:661`). In Mark that is 313 of 915
sensory items and 383 of 1,150 appraisals — **~700 items your check would reject in one book**,
correctly per our contract. Your question 4 (should `sp` refuse a response whose content has empty
evidence?) fails on that unless the declaration can say *"empty is legitimate here."* Ours carries
that distinction in the nullability rule (`schema-requirements.md §5`); a two-role map does not.

But the same measurement across all six books found something we did not know, and it argues the
other way:

| | Genesis | Psalms | Luke | Mark | Ruth | Philemon |
|---|---|---|---|---|---|---|
| sensory items, `background_ids` empty | **936/936** | **1048/1048** | **874/874** | 313/915 | 27/97 | 6/11 |
| appraisals, `background_ids` empty | **1077/1077** | **842/842** | **1275/1275** | 383/1150 | 27/108 | 11/51 |

**Three books at 100%.** That is not "text-grounded perception" — that is 3,061 sensory items and
3,194 appraisals in which the citation link to the background layer was never made at all. Every
check we own passes on it, because each field is individually well-formed and the empty value is
declared legitimate. A declaration that says *this field is evidence* makes "this evidence is empty
in 100% of instances" a machine-checkable statement. **That is the version of your check we would
want: not per-item refusal, but per-field occupancy.**

It is the same class as `boundary_signals`, which is present on **735 of 735 pericope nodes across
five books and non-empty on none of them** (Genesis 264, Luke 289, Mark 161, Ruth 16, Philemon 5) —
declared, annotated, rendered, and carrying nothing, always.

## 7. On `supports:` — weak for display, strong for the other two

For rendering, `supports:` would be a second copy of something our structure already says:
`background_ids` and `textual_basis` are properties *of* the appraisal they back
(`book-hierarchy.schema.json:731-765`), so the pairing is co-location and a separate map could only
drift from it.

For the other two consumers it is load-bearing, because **co-location is not order**. Within an
object, property order is what the model generates in, and that is where Hearts fails (§3). A
`supports:` declaration is what a test would read to assert "the evidence property precedes the
content property it supports" — the one statement neither our schemas nor yours can make today.

## 8. What is not settled here

The five questions are the Captain's and he has not ruled. What our measurements change about them:

- **Q1 (is two roles enough?)** — on our data, no. We need evidence-that-displays separated from
  evidence-that-only-forced, and we need "empty is legitimate here" as a declarable property of an
  evidence field. `"none"` conflating forcing with bookkeeping (§2) is the mistake to avoid, and we
  made it.
- **Q2 (audience or role?)** — both, on separate axes. Ours is audience-only and cannot answer
  the generation or audit question; yours is role-only and cannot answer the display question that
  `reviewer.md §4a` already decided per field.
- **Q3 (which schema first?)** — the Captain's call. We note that `scene-hearts.schema.json` is
  where our measured ordering defect is, and Bodies is where the pattern is already correct, so the
  pair would test the vocabulary against a known-bad and a known-good case.
- **Q4 (should `sp` enforce?)** — per-item refusal rejects ~700 valid items in Mark alone.
  Per-field occupancy reporting would have caught three real defects we are only now measuring.
- **Q5 (is the vocabulary right?)** — `evidence`/`content` reads fine. What would not survive
  contact with our resources is a single `evidence` bucket that has to serve the reader page, the
  reviewer's verification affordance, the ordering rule, and the coverage checklist at once.

**One thing we would ask of you regardless of the rest:** whatever the declaration ends up being,
make the *order* rule testable from it. Everything else in this proposal is a convenience; that one
addresses what the Captain says the technique is for.

## 9. Reproducing our numbers

All figures above are from committed artifacts in `outputs/book-summaries/{01-GEN,08-RUT,19-PSA,41-MRK,42-LUK,57-PHM}/`
and from the files cited by line. Two notes for anyone re-running them:

- **The leaf key differs by build vintage.** Mark, Ruth and Philemon use `segments`; Genesis,
  Psalms and Luke still use `scenes` (pre-rename, our #144). A walk that reads only one key
  silently reports zero for the other three books — it did for us on the first pass, which is how
  the 100% `background_ids` finding in §6 was nearly missed.
- **Pericopes nest.** A flat loop over `divisions[]` → `pericopes[]` misses most leaves in any book
  with nested divisions; recursion through both keys is required. That is the same defect as our
  #162.

