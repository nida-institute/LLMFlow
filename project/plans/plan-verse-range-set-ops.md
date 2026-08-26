# Plan: Verse Range Set Operations

**Status:** Approved 2026-08-17 — **authoritative for the implementation** (names, signatures,
files). The data model is `design-verse-range-operations.md`, which is authoritative for what the
operations mean. Spec and work order, not two competing specs.

No code yet — the Captain has approved the framing, not the build.

**The open question at the foot of this file is closed by construction.** It asked whether
`verse_range_union` should allow adjacent ranges, noting that the adjacent case needs a verse-count
lookup. It only arose because an earlier draft of this plan dropped `adjacent()` and
`verse_count()` from the design's operation set. With those restored, `union` does not decide:
a caller asks `verse_range_adjacent()` first and unions if it wants. Both are back in scope.

**Carried over from the design, per the Captain's rulings 2026-08-17:**

- **Six operations, not four** — `adjacent` and `verse_count` rejoin `overlaps`, `contains`,
  `union`, `intersect`.
- **Singleton-or-list inputs** — every reference argument accepts a string or a list of strings;
  a bare string is a one-element set. Normalise at the top of each function. The two-string
  signatures below need widening.
- **Cross-book ranges never overlap** — `overlaps` returns False, `intersect` returns None.
  `union` across books raises, since a range belongs to one book by definition.
- **`verse_range_*` prefix stands**, this file's naming choice, for unambiguity at pipeline call
  sites. Open naming detail: the design's `verse_count` becomes `verse_range_count` for
  consistency — confirm, since `verse_range_verse_count` is the literal composition and reads badly.

---

## Internal Representation

`parse_bible_reference()` already returns everything needed:
- `book_number` (2-char, zero-padded, e.g. `"41"` for Mark)
- `chapter`, `end_chapter` (int)
- `start_verse`, `end_verse` (int)

From these we derive a comparable 8-char **sort key**:
```
sort_key = f"{book_number}{chapter:03d}{verse:03d}"
```

`filename_prefix` already encodes this as `"{start_key}-{end_key}"`, so we can
split on `"-"` to get the two boundary keys.

Two ranges overlap iff neither ends before the other starts.
Containment, union, and intersect follow from the same boundary arithmetic.

Cross-chapter ranges are supported — `parse_bible_reference` handles
`"Mark 1:40-2:12"` already.

---

## API

All four functions accept string references, e.g. `"Mark 1:21-22"`.

```python
def verse_range_overlaps(ref1: str, ref2: str) -> bool:
    """True if the two ranges share at least one verse."""

def verse_range_contains(outer: str, inner: str) -> bool:
    """True if outer range fully contains inner range (inclusive)."""

def verse_range_union(ref1: str, ref2: str) -> str:
    """
    Return the smallest single range that covers both inputs.
    Requires both references to name the same book.
    Works for overlapping and adjacent ranges.
    Raises ValueError for non-contiguous ranges from different parts of the book
    (the result would silently include verses neither input covered).
    """

def verse_range_intersect(ref1: str, ref2: str) -> str | None:
    """
    Return the overlapping range, or None if the ranges do not overlap.
    Requires both references to name the same book.
    """
```

**Name choice**: prefixed `verse_range_*` to avoid shadowing built-ins (`contains`) and
to be unambiguous in pipeline code.

---

## Return Format for union/intersect

Results are returned as canonical reference strings (same format as
`parse_bible_reference()["canonical_reference"]`), reconstructed from the
computed boundary keys. A private `_sort_key_to_ref(key, book_name)` helper
converts back to `"Book C:V"` or `"Book C1:V1-C2:V2"`.

---

## Edge Cases and Design Decisions

| Case | Behavior |
|---|---|
| Same range (`ref1 == ref2`) | `overlaps` → True, `contains` → True, `union` → same range, `intersect` → same range |
| Adjacent but non-overlapping (`Mark 1:1-5`, `Mark 1:6-10`) | `overlaps` → False. `union` → allowed (result: `Mark 1:1-10`). `intersect` → None |
| Non-contiguous, same book (`Mark 1:1-5`, `Mark 3:1-5`) | `union` → raises ValueError (gap verses would be silently included) |
| Cross-book | All four raise ValueError — no meaningful comparison possible |
| Single verse as input (`"Mark 1:5"`) | Treated as a range of length 1 |
| Whole-book reference (`"Mark"`) | Deferred — `parse_bible_reference` returns `end_chapter=None`; raise ValueError for now |

**Note on adjacent `union`**: "adjacent" means end_key of one equals start_key of
the other minus one verse. This requires knowing the verse count of the last verse in
the range, which may require the `chapter_verse_counts` table. Simpler alternative:
allow `union` for overlapping ranges only, and let callers handle adjacency manually.
Decision point for the Captain.

---

## Files Changed

| File | Change |
|---|---|
| `src/llmflow/utils/data.py` | Add 4 public functions + 1 private helper after `parse_bible_reference` |
| `tests/test_verse_range_ops.py` | New file: tests for all four functions and edge cases |

No pipeline YAML changes. No changes to the engine runner, linter, or CLI.

---

## Out of Scope

- A native pipeline step type wrapping these — callers use `type: function`
- ~~Multi-chapter union adjacency (deferred pending decision above)~~ — now in scope; see the resolved question below
- Verse-level iteration (expanding a range to a list of verse strings)

---

## Open Question for the Captain — RESOLVED 2026-08-17

> Should `verse_range_union` allow adjacent ranges (gap = 0), or require overlap (gap < 0)?
> The adjacent case requires a verse count lookup; the overlap-only case avoids it.

**Resolved by restoring the two operations this plan had dropped.** `verse_range_union` does not
decide the adjacency policy at all: `verse_range_adjacent()` is a separate predicate, and
`verse_range_count()` provides the verse-count lookup the question was trying to avoid. A caller
that wants adjacent ranges merged tests for adjacency and then unions.

The question was an artefact of cutting scope, not a real design fork — which is a reason to read
`design-verse-range-operations.md` first.
