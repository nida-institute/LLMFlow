# Design: Verse Range Operations

**Status:** Approved 2026-08-17 — **authoritative for the data model.** Not a work order: the
implementation is specified in `plan-verse-range-set-ops.md`, which is authoritative for names,
signatures and files. Spec and work order, not two competing specs.

No code yet — the Captain has approved the framing, not the build.

**Captain's rulings, 2026-08-17:**

1. **Cross-book ranges never overlap.** Two ranges naming different books are non-overlapping —
   `overlaps` returns False rather than raising, and `intersect` returns None. This answers
   Question 1 below, which had proposed rejection as an alternative. Consequence to confirm at
   implementation time: `union` across books cannot yield a valid single range, since a range
   belongs to one book by definition, so it raises rather than returning a cross-book span.
2. **This document's operation set stands** — six operations, `adjacent` and `verse_count`
   included. They were dropped in an earlier draft of the plan, which is what left the plan's
   union/adjacency question unanswerable.
3. **Singleton-or-list inputs stand** (Question 3, "both"). A bare string is treated as a
   one-element set, so `overlaps("Mark 1:1-10", scenes)` works whether `scenes` is one reference
   or many. Iterating sets in caller code is the problem being solved.

---

## What We Have Now

`parse_bible_reference()` in `llmflow.utils.data` parses a reference string and returns a dict:

```python
{
  'book_name': 'Luke',
  'book_number': '42',         # canonical numeric order
  'book_code': 'LUK',
  'chapter': 12,
  'start_verse': 5,
  'end_verse': 19,
  'filename_prefix': '042012005-042012019',   # sortable, comparable
  ...
}
```

**Limitations relevant to this design:**

1. **Single-chapter only.** The `chapter` field is a scalar. Cross-chapter ranges ("Mark 1:40–2:12") are not representable.
2. **Incomplete verse count table.** Whole-chapter references require knowing the last verse of the chapter; the current table covers only a few chapters.
3. **No comparison operations.** `filename_prefix` encodes start and end as a sortable string, but no functions use it for overlap detection.
4. **Not designed for set operations.** The function returns one parsed range; there is no concept of a set of ranges.

Any new design must either extend `parse_bible_reference` or define a clean boundary between parsing (what it does) and range operations (what the new library adds).

---

## Data Model Questions

### Question 1: What is a verse range?

A verse range is a contiguous span of scripture with a defined start and end. It always belongs to a single book. The minimal representation needs:

- Book identity (for cross-range comparisons to detect different-book cases)
- Start: chapter + verse
- End: chapter + verse

The existing `filename_prefix` encoding (`042012005-042012019`) already encodes book + chapter + verse as a zero-padded integer triple, making string comparison equivalent to numeric comparison. This is the right internal representation for ordering and overlap detection.

**Open question:** should a verse range be allowed to span books? Almost certainly not — a range that crosses from Malachi into Matthew is not a meaningful unit in any biblical scholarly context. Cross-book should be rejected or treated as always non-overlapping.

**RESOLVED 2026-08-17 — the Captain's ruling: books never overlap.** Of the two alternatives above, the second: cross-book ranges are treated as **non-overlapping**, not rejected. `overlaps` returns False and `intersect` returns None for references naming different books — no exception, because "these are in different books" is a legitimate answer to "do these overlap?", and callers filtering a mixed-book set should not have to catch errors to do it.

`union` is the exception, and only because of what a range *is*: a range belongs to one book, so there is no single range covering Malachi and Matthew. Cross-book `union` therefore raises rather than inventing one. Confirm at implementation time.

### Question 2: What is a "set of ranges"?

A set of ranges is a collection of possibly non-contiguous verse spans. It arises naturally from:

- A passage composed of multiple scenes, each with its own reference
- A theme or thread that appears in scattered locations
- The union of pericopes that belong to a narrative unit

A set of ranges is **not** the same as a single range. Mark 1:1-10 and Mark 1:15-20 cannot be faithfully represented as a single range without implying coverage of Mark 1:11-14.

**Two representations are possible:**

A. **List of range strings:** `["Mark 1:1-10", "Mark 1:15-20"]` — simple, matches how pipeline YAML would express it, but requires parsing on every call.

B. **List of parsed range objects:** internal representation after parsing — efficient for repeated operations but requires a VerseRange type.

For the pipeline-facing API, list-of-strings is the right input. Internally the functions should parse to objects and operate on those.

### Question 3: Should functions accept singletons, sets, or both?

**Singletons only:** simpler to implement; callers must iterate for the common pipeline cases (does this thread overlap any of these scenes?). Set iteration ends up as per-project Python — exactly the problem we're solving.

**Sets only:** forces callers to always wrap singletons in lists, which is awkward at call sites.

**Both (recommended):** functions accept a string or a list of strings for each argument. A singleton string is treated as a one-element set. This unifies the calling convention: `overlaps("Mark 1:1-10", scenes)` works whether `scenes` is a string or a list. Implementation normalizes inputs at the start of each function.

---

## The Operations

### `overlaps(a, b) → bool`

Returns True if a and b share at least one verse.

**Singleton semantics:** `a` and `b` are both single ranges. True if their spans intersect — i.e., a.start ≤ b.end and b.start ≤ a.end.

**Set semantics:** True if any range in a overlaps any range in b. This is the most common pipeline use case: "does this thread reference appear in any of this passage's scenes?"

**Edge cases:**
- Different books: always False
- Same single verse on both sides: True
- Adjacent ranges (a ends at verse 5, b starts at verse 6): False — they touch but do not overlap. See `adjacent`.
- Empty set input: False

**Implementation note:** with the `filename_prefix` encoding, overlap between two singletons reduces to: `a_start ≤ b_end AND b_start ≤ a_end` as string comparisons, which works given the zero-padding.

---

### `contains(a, b) → bool`

Returns True if a fully covers b — every verse in b is also in a. Equivalent to: a is a superset of b, b is a subset of a.

**Singleton semantics:** a.start ≤ b.start and b.end ≤ a.end.

**Set semantics:** two reasonable interpretations:

- **A:** does the union of ranges in a cover every verse in b? This is the natural "does this passage cover this pericope?" check.
- **B:** does some single range in a contain b? Stricter; fails if b spans a gap between two ranges in a.

These are different. Mark 1:1-5 and Mark 1:8-12 as a set contains Mark 1:9 (interpretation A) but if the check is against Mark 1:3-10, interpretation A says yes (the union 1:1-12 covers 1:3-10), interpretation B says no (neither individual range covers 1:3-10).

Interpretation A is usually what pipeline logic wants ("is this pericope fully within the passage?"), but it implicitly treats the set as a convex hull. If exact coverage matters — the passage has a gap and you want to know whether b falls entirely within covered verses — interpretation A is wrong.

**Design decision needed:** which semantics for set containment? Or provide both (`contains_any`, `contains_all`)?

---

### `intersection(a, b) → list[range] | None`

Returns the verses shared by a and b, or None if no overlap.

**Singleton semantics:** returns a single range: max(a.start, b.start) to min(a.end, b.end). If a.start > b.end or b.start > a.end, returns None.

**Set semantics:** this is where the design branches significantly.

**Option 1: Return the convex hull** — a single range spanning the full overlap region. Simple, loses information about gaps.

**Option 2: Return a list of disjoint ranges** — each contiguous overlapping segment is its own range in the result. Preserves exact coverage. More complex to compute and consume.

**Example:** a = ["Mark 1:1-10", "Mark 1:15-20"], b = "Mark 1:5-18"
- Convex hull intersection: Mark 1:5-18 (the full overlap span)
- Disjoint intersection: ["Mark 1:5-10", "Mark 1:15-18"]

The disjoint form is more precise but the convex hull is almost always what downstream steps need — a single range to pass to the next LLM prompt, not a list of fragments. However, if the result is being used to filter another list or compute verse count, the disjoint form is correct.

**Design decision needed:** convex hull, disjoint list, or caller-chosen via a parameter?

---

### `union(a, b) → range` or `union(refs) → range`

Returns a range spanning all input references.

**Singleton semantics:** min(a.start, b.start) to max(a.end, b.end).

**Set semantics:** min of all starts to max of all ends — always a single convex hull.

**Important:** union is always the convex hull here, not an exact set union. Mark 1:1-5 ∪ Mark 1:8-12 = Mark 1:1-12, including the gap at Mark 1:6-7. This is a deliberate design choice appropriate for "what is the span of this passage?" but wrong for "what verses are actually covered?"

If exact set union is ever needed (list of disjoint ranges), that's a different function (`merge` or `covered_ranges`) and probably rarer.

**Cross-book behavior:** if refs span multiple books, two options: raise an error, or return the full span (Genesis to Revelation if that's what was passed). Raising an error is safer.

---

### `adjacent(a, b) → bool`

Returns True if a and b abut without overlapping: a ends at verse N, b starts at verse N+1 (or vice versa). Needed when merging a sequence of accumulated ranges.

**Complexity:** "verse N+1" is not trivial — it requires knowing the verse count of chapter N to detect chapter-boundary adjacency. Mark 1:45 is adjacent to Mark 2:1, but detecting this requires knowing Mark 1 has 45 verses.

This makes `adjacent` the operation most dependent on a complete verse count table. If the table is incomplete, `adjacent` will fail silently for cross-chapter boundaries (returning False when True is correct).

**Design decision:** accept this limitation and document it, or require a complete verse count table before implementing `adjacent`?

---

### `verse_count(a) → int`

Returns the number of verses covered by the range or set of ranges.

**Singleton:** requires knowing the actual verse counts for the chapters spanned. For a within-chapter range, this is end_verse - start_verse + 1. For a cross-chapter range, it requires summing remaining verses in the start chapter + full intermediate chapters + verses in the end chapter.

**Set:** sum of verse counts of each range in the set (with deduplication if ranges overlap).

`verse_count` is the operation most dependent on a complete, accurate verse-count database. The current `chapter_verse_counts` in `data.py` covers only a handful of chapters.

**Design decision:** is `verse_count` in scope for this library given the incomplete verse count table, or is it deferred?

---

## The Verse Count Table Problem

Several operations (`adjacent`, `verse_count`, whole-chapter range resolution) require knowing the number of verses in each chapter. The current table in `data.py` is explicitly approximate and covers only Psalms, Luke, and John.

Options:

**A. Bundle a complete verse count table** — a static JSON/dict mapping book+chapter to verse count. This is a one-time data entry task but needs a defined source of truth (KJV? UBS? verse divisions differ by tradition).

**B. Use an external source at runtime** — query a Bible API or local database. Adds a dependency and network requirement.

**C. Scope operations to avoid the need** — implement operations that work correctly for within-chapter ranges and cross-chapter ranges where the full span is known, but decline to implement `adjacent` and `verse_count` until the table is complete.

**D. Treat cross-chapter adjacency approximately** — use a fallback heuristic (assume chapters have at most 176 verses) and document the approximation.

Option C is the most honest approach for an initial implementation. Option A is the right long-term solution and is a bounded, one-time task.

---

## The Internal Representation

Whatever the public API accepts (strings), internally the library needs a structured representation for computation. Two choices:

**A. Dict** — consistent with the rest of the codebase (`parse_bible_reference` returns a dict):

```python
{
    'book_number': '42',
    'start_chapter': 1,
    'start_verse': 1,
    'end_chapter': 2,
    'end_verse': 28,
    'start_key': '042001001',   # zero-padded, sortable
    'end_key': '042002028',
}
```

**B. Dataclass or namedtuple** — type-safe, dot-access, hashable (useful for sets/deduplication):

```python
@dataclass(frozen=True)
class VerseRange:
    book_number: str
    start_chapter: int
    start_verse: int
    end_chapter: int
    end_verse: int
```

The dataclass is cleaner for internal operations and allows ranges to be used as dict keys or in sets. The dict is consistent with existing conventions. Either can be used internally without affecting the public API.

---

## Cross-Chapter Ranges

The existing `parse_bible_reference` assigns a single `chapter` value. Cross-chapter ranges ("Mark 1:40–2:12") require separate `start_chapter` and `end_chapter` fields.

This is a breaking change to the internal representation — or rather, an extension. The existing function's output dict would need new fields, or a new parsing function is needed that supersedes it.

**Design decision:** extend `parse_bible_reference` to support cross-chapter ranges, or create a new `parse_verse_range` function that returns the richer representation? The latter is less disruptive but creates two parsing functions doing overlapping work.

---

## Public API Shape

Assuming the "both singleton and set" decision above, the public API would be:

```python
# All functions accept str | list[str] for range arguments
# A str is treated as a list of one

def overlaps(a: str | list[str], b: str | list[str]) -> bool: ...

def contains(a: str | list[str], b: str | list[str]) -> bool: ...
# contains: does a cover every verse in b?

def intersection(a: str | list[str], b: str | list[str]) -> str | None: ...
# returns a single canonical range string, or None

def union(refs: str | list[str]) -> str: ...
# returns a single canonical range string (convex hull)

def adjacent(a: str, b: str) -> bool: ...
# singleton only — adjacency between two specific ranges

def verse_count(a: str | list[str]) -> int: ...
# deferred pending complete verse count table
```

All functions return strings or bools — compatible with pipeline context and `saveas` path construction.

---

## Integration with Pipeline Steps

These functions live in `llmflow.utils.refs` and are called via `type: function` steps:

```yaml
- name: find_active_scenes
  type: function
  function: llmflow.utils.refs.overlaps
  inputs:
    a: "${thread.reference}"
    b: "${scene_refs}"   # list of strings in context
  outputs: thread_is_active
```

They are also the building blocks for the predicate filtering issue (GH #168): a `filter` step or DuckDB query can call `overlaps` as a predicate when evaluating which items to keep.

---

## Decisions Needed Before Implementation

1. **Cross-chapter ranges:** extend `parse_bible_reference` or create `parse_verse_range`?
2. **Set containment semantics:** convex hull (union of a covers b) or exact (every verse in b is in a covered range)?
3. **Intersection return type:** convex hull (single range) or disjoint list?
4. **Verse count table:** bundle complete table now, or defer `adjacent` and `verse_count`?
5. **Internal representation:** dict (consistent with existing) or dataclass (cleaner)?
6. **Cross-book input:** error or always-False?
