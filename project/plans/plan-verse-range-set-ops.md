# Plan: Verse Range Set Operations

**Status:** Proposed — not built. Nothing in `src/` implements this. Requires the Captain's approval before any code.

Verified 2026-08-17: none of the proposed set operations exist in `utils/data.py`.

Ends with an **unanswered "Open Question for the Captain"**, and overlaps with
`design-verse-range-operations.md`. Which is authoritative is an open Captain decision — do
not start from either without asking.

**Goal:** Add `overlaps()`, `contains()`, `union()`, and `intersect()` to `llmflow.utils.data`
so pipeline Python functions can do range arithmetic on biblical references without
reimplementing the comparison logic.

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
- Multi-chapter union adjacency (deferred pending decision above)
- Verse-level iteration (expanding a range to a list of verse strings)

---

## Open Question for the Captain

Should `verse_range_union` allow adjacent ranges (gap = 0), or require overlap (gap < 0)?
The adjacent case requires a verse count lookup; the overlap-only case avoids it.
