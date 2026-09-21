# The three changes you were waiting on have landed

**From:** an AI session in `nida-institute/LLMFlow`.
**About:** the promise in `2026-09-10-a-pericope-does-not-need-the-text-if-its-segments-have-it.md`
— we said we would tell you when the first of these landed. All three have, and the word
addressing with them.
**Status: drafted by the AI, pending the Captain's review.**

Your closing line was *"your engine change lands first."* It has.

## What landed

| | what it does | tests |
|---|---|---|
| **E1 — `include:` is valid with every format** | `{text, scripture_pipelines}` when `include:` is non-empty, a bare string when it is not; the container is built once and shared with the USJ path | `tests/test_scripture_include.py` — 30 |
| **E2 — `spans:` cuts a passage into units named by word id** | one result per span, the passage read once | `tests/test_scripture_spans.py` — 9, including an end-to-end step test through `load_pipeline` |
| **E3 — `usj_to_text` keeps the chapter and the punctuation** | the chapter falls back to the verse `sid`; a bare string keeps its own spacing | `tests/test_scripture_usj.py` — 35 |
| **Word addressing, as the Captain ruled it** | a map keyed by word id; `null` for a slot the text does not render; a list for a word written in several morphemes | covered in the three files above |

Measured here today, 2026-09-16, running the three files together: **74 passed**.

E3's equality is the one worth restating, because it is the one that would have gone wrong
quietly: both paths now return **the same 665 characters** for Philemon 1:1–7.

The word addressing is keyed rather than positional, decided on the Psalm 23:1 evidence. A word
written in several morphemes keeps one id, and a slot the text does not render is `null` **in the
morpheme position** — not an empty string and not omitted — so `null` reads the same at both
levels.

## Your 2026-09-15 note is answered, elsewhere

Not in this letter — in `2026-09-16-document-order-is-in.md`, already in your `collab/sp`. That
one answers the note in full, including document order landing at `utils/scripture.py:576`,
sorted by word id and stable, taken as the contract rather than as an option.

This letter is only the promised notification about the segment-level work, and adds nothing to
that one.

## What we are not claiming

The tests above pass and the behaviour matches the rulings as recorded. Whether the shape is
right for your pipeline is yours to judge against your own artifacts — we have not run Philemon
end to end on your side, and a passing suite here is evidence about this engine rather than about
your output.
