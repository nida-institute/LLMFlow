# Verse regions

**Status:** built as `llmflow.utils.verse_ranges`, tested in `tests/test_verse_ranges.py`.
**Issue:** #169.
**Supersedes:** `design-verse-range-operations.md` and `plan-verse-range-set-ops.md`.

**What was found on contact with the code — §10.** The engine already had the parsing half, twice
over, and one book resolves to the wrong book.

**Ruled by the Captain during design, 2026-09-05:**

1. `touches`, not Allen's `meets` — plain vocabulary over interval-algebra jargon.
2. **Books are distinct documents.** No range spans books; book boundaries are out of scope.
3. **Both `select` and the boolean predicates ship.** See §5 for why the earlier retraction was wrong.
4. **The module is `llmflow.utils.verse_ranges`** — the word the reader already has, and the one the
   consumers use (`division["verse_range"]`). Not `verse_algebra`: an algebra's operations return
   elements of the same kind, and §3 declines exactly the operations that would make it one, so the
   name would advertise an absent half rather than a decided one.
5. **The colloquial sense of `overlaps` wins the name** — shares at least one verse. Allen's strict
   partial case needs no public name at all, which is what lets the partition stay internal (§4.1).

Earlier and still binding: **scheme is a required parameter, no default** (2026-09-03), and
**cross-book comparisons answer rather than raise** (2026-08-17).

---

## 1. What #169 reports, and what the code shows

Four plugins in `ears-to-hear/scriptorium/plugins/` independently implement verse-range overlap:

| plugin | asks | how |
|---|---|---|
| `division_lookup.py:53` | which division is this passage in | predicate + loop, **`return` on first match** |
| `passage_extract.py:13` | which scenes does this passage touch | predicate + loop, recursing into nested pericopes |
| `book_frameworks.py:20` | is this verse in this range | predicate, degenerate probe |
| `extract_pericopes.py:85` | do my pericopes overlap each other, and cover the book | pairwise, plus point-set coverage |

**The issue names the overlap logic. The evidence says the parsers are worse.** Five of them across
the four files, with three incompatible return types:

```
book_frameworks    _parse_canonical_reference -> Tuple[int, int, int, int]
extract_pericopes  _parse_verse_ref           -> Tuple[int, int]
extract_pericopes  _parse_verse_range         -> Tuple[Tuple[int,int], Tuple[int,int]]
extract_pericopes  _parse_range_interval      -> Tuple[Tuple[int,int], Tuple[int,int]]
division_lookup    _parse_verse_range         -> tuple[int, int, int, int]
```

`extract_pericopes` carries two with identical signatures. And **not one of the five returns the
book** — there is no room for it in any of those types.

### 1.1 Three findings, reported not fixed

**A live bug, `division_lookup.py:31`.** The reference is reduced by
`re.search(r'(\d+:\d+(?:-\d+(?::\d+)?)?)', passage_ref)`, discarding the book: `Mark 1:1-5` and
`John 1:1-5` compare as overlapping. This is **structural, not a slip** — the parsed type cannot
hold a book, so no care in the comparison code could have caught it.

**A silent narrowing, `division_lookup.py:56`.** `return` on first match gives a passage spanning
two divisions whichever appears first, with nothing reported. Same class as the `--resume` empty
accumulator: not wrongness, but wrongness with no symptom.

**Malformed input reports as "no overlap", `division_lookup.py:40`.** `except ValueError: return
False` converts an unparseable reference into *overlaps nothing*. The error handling manufactures
the same failure class.

Two implementations also agree today for no stated reason: `passage_extract` uses the canonical form
(`a.start <= b.end and a.end >= b.start`), `division_lookup` three membership tests that happen to
cover the same cases. Nothing holds them together. §4 makes agreement structural.

---

## 2. Parse once, at the boundary

The defect above is the gap between *"string that might be a reference"* and *"reference"*, and each
of the five parsers widens it by discarding information. The remedy is a type built once by a smart
constructor that carries everything and refuses what is illegal:

- a range **belongs to one book** — ruled; cross-book ranges are unconstructible
- `end` before `start` is unconstructible
- **no range exists without a scheme** — ruled; there is no default
- a book the scheme does not carry **fails at construction**, naming scheme and book, rather than
  comparing `False` against everything and passing for an answer

Downstream, every function is then total: no `try/except ValueError` anywhere, because there is no
parsing left to fail.

### 2.1 Ordinals are book-local, and that is what the ruling buys

Within one book, `Scheme.max_verses[book]` yields a total order: sum the verses of prior chapters.
Every relation reduces to integer comparison on `(start, end)` ordinals.

Because **no range spans books**, the ordinal needs no canon order and no book sequence. That the
schemes disagree on book *inventory* — `org` 95, `lxx` 89, `rso` 79, `vul` 86, `eng` 92, `rsc` 66 —
stops mattering entirely. Only chapter and verse counts inside a single book matter.

Verified 2026-09-05: `excluded_verses` is empty in all six packaged schemes, so the ordinal is
dense; `org` carries complete counts for 95 books; `Mark 1` is 45 verses.

**The ordinal is internal.** It is scheme-relative and must never be exposed or persisted — a stored
ordinal silently names a different verse under another scheme.

**Adjacency needs no special case.** `Mark 1:45` and `Mark 2:1` are adjacent only if Mark 1 has
exactly 45 verses; with ordinals that is `a.end + 1 == b.start`, and the `max_verses` dependency
lives in the constructor where it is used once. Chapter boundaries disappear from the relation code.

**Known limit:** `partialVerses` is uninterpreted — 74 entries in `lxx`, warned about at load.

---

## 3. Selection over labelled units, not a point-set algebra

**A point-set algebra** treats a region as a set of verses, closed under union, intersection and
difference, normalised to disjoint canonical form. **Selection** treats regions as named units and
asks which members of a collection stand in relation R to a probe.

Three reasons the second fits:

1. **Nesting is real and normalisation destroys it.** Book ⊃ chapter ⊃ verse, and
   `passage_extract.py:23` recurses into `pericope["pericopes"]` — nested pericopes in shipped code.
   The union of a book and a chapter inside it is the book, and the chapter is gone: correct as
   point sets, useless when the question was which units were involved.
2. **Identity is the answer.** `division_lookup` wants the division, not an interval.
3. **The point-set half is already declined.** What needs union and coverage is `extract_pericopes`
   — "do my pericopes cover the book" — which is the coverage check ruled out three times, each time
   because its semantics required judging someone else's gaps.

*(The declined algebra has a name: region sets under union form a monoid with the empty set as
identity. Recorded so nobody re-derives it as a discovery.)*

---

## 4. One total function, predicates over it

Six independent boolean functions are six chances to disagree. Allen's interval relations are a
**partition** — exhaustive and mutually exclusive — so the primitive is one total function into a
closed set of named results:

```python
def relate(a: Range, b: Range) -> Relation
```

Every predicate is then a membership test, and agreement between them is a property of the type
rather than a coincidence to re-verify. **This is `Outcome` in `discourse.py` applied to intervals**
— the same pattern already in the codebase.

### 4.1 The partition is internal

`relate` and its partition are an **implementation primitive, not public surface.** They exist so
that agreement between the predicates is a property of the type; nothing requires a consumer to
learn interval-algebra vocabulary or to choose between two senses of a word.

This settles the strict-partial case. Two ranges can partially overlap, so the implementation must
handle that configuration — but nothing in the measured demand asks to *name* it. The question it
would answer, "does this passage cross a pericope boundary", is already answered by counting a
selection: `len(select(pericopes, passage, "overlaps")) > 1`. So the case exists and the name does
not.

### 4.2 Cross-book

`overlaps`, `contains` and `touches` return `False` across books: they share no verse and are not
adjacent, so `False` is true, and callers filtering a mixed-book set need not catch anything
(2026-08-17). `before` / `after` are not exported (§6), so the one case where `False` both ways
would assert a falsehood about a total order does not arise.

**What this costs, and how it is recovered.** With the partition internal, an empty `select` result
means both "no unit overlaps this passage" and "you compared a Mark passage against John's
divisions." The second is a pipeline bug, and silence is the wrong-with-no-symptom pattern.

So **`select` warns when the probe's book matches no member's book** — a diagnostic that fires
exactly on that mistake, in the same shape as the warning already emitted for an undeclared
versification scheme. A `same_document(a, b) -> bool` predicate is trivial if anything ever needs to
branch on it; nothing does today.

---

## 5. Both surfaces — and why the retraction was wrong

A mid-design retraction argued that `filter` already exists, so `select` is a worse `filter` with a
hardcoded traversal and a needless accessor. **That argument was made against Python callers, in a
declarative-pipeline project.** YAML has no comprehension. A plugin exists precisely because a
pipeline could not express something — so shipping only the predicate guarantees those four plugins
keep existing, and keep being written wrong. The Captain ruled both; this section records why.

The accessor is not a leak but a **declaration**: `ref="verse_range"` is the pipeline stating where
its ranges live, which is `declared-not-inferred` satisfied.

**Both surfaces cost one function.** `steps/function.py:26-37` imports any dotted path and calls it
with resolved inputs, so no new step type, no runner change, no linter change:

```yaml
- name: which divisions does this passage touch
  type: function
  function: llmflow.utils.verse_ranges.select
  inputs: {collection: "${divisions}", probe: "${passage}", relation: overlaps, ref: verse_range}
  saveas: touched
```

Each surface is independently justified: a predicate answers "does this citation overlap the passage
I am processing", where there is no collection and `select` over a one-element list would be silly;
`select` answers "which unit is this in", which three plugins wrote by hand and one got wrong.

**`select` is the documented answer to "which unit is this in."** Neutral documentation would leave
`division_lookup` with its loop and its bug, closing #169 without answering its complaint.

---

## 6. Proposed surface

```python
# the type — built once, at the boundary
Range(reference: str, *, scheme: str)      # smart constructor; refuses illegal states

# the primitive
relate(a: Range, b: Range) -> Relation     # total; exactly one member holds

# predicates, thin membership tests over relate
overlaps(a, b) -> bool     # shares at least one verse    -- colloquial sense, see §7
contains(a, b) -> bool     # a covers every verse of b
touches(a, b)  -> bool     # adjacent: no gap, no shared verse
equals(a, b)   -> bool

verse_count(a) -> int

# selection over labelled units
select(collection, probe, relation, *, ref) -> list[member]
```

`select` returns a list **always** — empty where nothing matches, never `None`
(`say-which-kind-of-nothing`). It is **flat**: `passage_extract` recurses into nested pericopes and
the caller flattens, since a declared child key would be application semantics for one call site.
`ref` is **required**; `select` refuses without it rather than guessing a key.

`before` / `after` stay in the partition — a partition with a hole is not a partition — but are
**not exported as predicates**: no measured demand, and under distinct-documents nobody has asked to
order ranges within a book.

---

## 7. Naming

Ruled: **`touches`**, not `meets`. Docstring must say adjacency explicitly — *no gap and no shared
verse* — because GIS vocabulary uses `touches` for shared boundaries and a reader may expect
partially-overlapping ranges to qualify.

That ruling implies a principle — plain vocabulary over Allen's — applied to the rest in §9.1.

**The collision that matters most.** Allen's `overlaps` is the *strictly partial* case: a starts
first, they share verses, a ends first. It excludes containment and equality. Every one of the four
plugins uses the word colloquially, to mean *shares at least one verse*, and so would any pipeline
author. Shipping both meanings under one word would be a deliberate version of the accidental
disagreement in §1.1.

**Proposed: the colloquial meaning wins the good name.** `overlaps(a, b)` = shares at least one
verse. Allen's strict case becomes a partition member under its own name — `STRADDLES` reads best
for verse work, being exactly the pericope-boundary case. `overlaps` is then a membership test over
several partition members, which is the §4 layering.

---

## 8. What is not built, and what changes from the superseded documents

**Not built:** point-set `union`, `intersection`, difference, coverage. `union` as specified was the
convex hull, so `Mark 1:1-5 ∪ Mark 1:8-12` = `Mark 1:1-12` *including the gap at 1:6-7* — right for
"what is the span", wrong for "what is covered", with the name saying neither. The question it
serves is the declined coverage check.

**Dropped as false:** the incomplete-verse-count blocker. `design-verse-range-operations.md`
§§182–204 defers `adjacent` and `verse_count` because the table "covers only Psalms, Luke, and
John". Complete counts for 95 books have shipped since; neither needs deferral.

**Dropped as unasked:** the `contains_any` / `contains_all` set-semantics question. In all four call
sites the unit is a single range and the caller loops, so union-versus-single-range containment is
asked nowhere. The names also read backwards.

**Kept:** scheme required; cross-book answers rather than raises; both singletons and collections,
which `select` subsumes by taking a probe and a collection.

**Added:** the `Range` type and single parser; `relate` as a total function; `select`; and the
finding that the parsers, not the predicates, are where the duplication and the defect live.

### 8.1 Parked: verse comprehensions

Raised by the Captain 2026-09-05 and **explicitly parked for want of requirements and use cases.**
Recorded so it is not re-derived as a discovery, and not built on speculation.

The context is that `sp` already carries a functional skeleton under other names — `for-each` with
`append_to` is map and collect, `append_to` accumulation is fold, `if` is the conditional — and
**filter is the one combinator missing.** `select` fills it. That makes this proposal a completion
of an existing set rather than a move toward a new paradigm, which is the smaller and more
defensible claim.

A verse comprehension would compose `for-each` over a `select` result, which pipelines can already
write **in two steps**. The requirement that would justify one is therefore either "two steps is too
many" or "it is needed inside an expression" — and neither has been reported by any consumer. Until
one is, there is nothing to design against.

---

## 9. Decisions for the Captain

Naming inside the partition is no longer a question for the Captain: the partition is internal
(§4.1), so only the exported names in §6 are public, and those are plain words already.

**Predicate names are bare** — `overlaps`, not `verse_overlaps`. Ruled 2026-09-05: the module name
now carries the qualification, and `select` takes the relation as an argument rather than as an
identifier, so the collision pressure that once argued for prefixing is gone.

### 9.1 Deferred, because they widen

Ruled 2026-09-05, on the Captain's test that both can be added later without breaking anyone:

- **`select` takes the relation as a string**, from an enumerated set, with an unknown one refused
  by name. Accepting a `Callable` as well is a **widening** — existing callers keep working, and
  lint simply skips a non-string. Deferred until something asks: measured demand is one relation
  from four call sites, and a Python caller wanting a custom predicate writes a comprehension and
  does not need `select` at all.
- **`Range` takes a reference string.** `Range.from_member(member, ref=...)` as an alternate
  constructor is additive, and cheaper than deferral implies — `select` needs that extraction
  internally either way, so only the export waits. Not a `str | Mapping` union resolved by
  sniffing: a dict without `ref`, or a string with one, are the silent-wrong-answer shapes this
  design exists to remove.

### 9.2 The test itself, recorded for later items

**Decisions that widen are safe to defer; decisions that narrow are not.** Accepting more types,
exposing more surface and relaxing a requirement can all be done later. Renaming, restricting, and
changing a return shape cannot.

| decision | direction | when |
|---|---|---|
| module `verse_ranges` | one-way — breaks every `function:` path | ruled now |
| bare predicate names | one-way — breaks imports | ruled now |
| `overlaps` = colloquial | one-way, and *silently* — same name, other behaviour | ruled now |
| `select` returns `[]`, never `None` | one-way — breaks `is None` checks | decided now |
| `ref` required | required→optional is safe; the reverse is not | required now |
| partition internal | private→public is safe; the reverse is not | internal now |
| relation as `str` | widening | deferred |
| `Range.from_member` | widening | deferred |

### 9.3 Settled at implementation

**`ref` is a resolved path, not a flat key.** This was the one deferral that did not widen — a key
literally named `a.b` means that key under flat lookup and a nested path under resolution, same
input, different result, no error — so it was closed rather than left. `select` uses the engine's
own `get_from_context`, which gives `meta.range` and `items[0].ref` and makes `ref` behave like
every other path in sp.

Not asked, treated as settled: whether point-set operations are in scope. Say so if that is wrong.

---

## 10. What contact with the code changed

**The parsing half already existed, twice.** `versification.parse_passage_ref` returns a
`PassageRef` — frozen, carrying the book — and `data.parse_bible_reference` returns an 18-key dict
that is scheme-aware and resolves whole chapters. §2 proposed building the type this design needs;
most of it was there. `Range` therefore **wraps `PassageRef`** rather than extending it, leaving the
shipped scripture step untouched, and adds only what was missing: a scheme, book-local ordinals, and
a refusal for `Mark 1:5-1:2`, which the existing parser accepts.

**So the engine carried the duplication it reports in the plugins.** The two parsers are layered
rather than duplicated — syntax, then scheme and presentation — and both resolve books through
`llmflow.books`. But each carries its own regex pattern set, and nothing held them in agreement.
`test_the_engines_two_parsers_agree_on_the_syntax_they_share` is the pin; if it fires, unify them.
That unification is the real fix and is **deferred, not denied**.

**A book resolved to the wrong book — found here, fixed at the Captain's direction.**
`books.resolve("PSS")` returned `PSA`. It is not a typo but a collision between two published
standards this engine reads: the SBL Handbook gives `Pss` for Psalms (plural), USFM gives `PSS` for
Psalms of Solomon, which `org` and `lxx` carry as a book of 18 chapters. `_index()` adds
`other_codes` with `setdefault`, so the alias won and a pipeline asking for Psalms of Solomon
silently received Psalms.

Neither claim can be dropped, so the token is **refused** — the `ambiguous` mechanism, used for what
the declaration says it is for. The guard that should have caught this compared aliases only against
each other, never against `other_codes`; widened, so the next collision fails.

Psalms of Solomon is now **unreachable rather than wrong**: it has no display name, `other_codes`
invents none, and so the refusal's advice to write the book out cannot be followed for it. That is a
known limit, not an oversight.

**Verification was laws over the real corpus rather than examples.** Every book and chapter of all
six packaged schemes — 1,584 chapters in `org` alone — checked for verse counts against the scheme,
whole-book containment, and consecutive chapters touching without overlapping. `hypothesis` is not
in the project, and the corpus is real where generated input would not be.

### 10.1 Known limits of what was built

- **`select` over bare reference strings warns and skips.** A collection of plain strings has
  nothing for `ref` to resolve against. Supporting it is a widening and can be added without
  breaking a caller; nothing has asked.
- **Nothing consumes it yet.** The four plugins in `ears-to-hear` are unchanged; adopting it is
  theirs, and the three defects in `division_lookup.py` are reported rather than fixed.
- `partialVerses` remains uninterpreted — 74 entries in `lxx`.
