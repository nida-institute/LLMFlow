# `parse_passage_ref` refuses every book whose name has a space

**From:** nida-institute/discourse-flow · 2026-09-21

A whole-book run of 1 John crashes in `fetch_book`. The string is the one both
`AGENTS.md` and the pipeline's own header document:

```
sp run --pipeline pipelines/book-discourse-flow.yaml --var book="1 John"
```

```
ValueError: '1 John' is not a passage reference. Expected forms: 'MRK', 'Mark 1',
'Mark 1:1', 'MRK 1:1-8', 'Mark 1:40-2:12' — a book name or its USFM code.
```

"1 John" is a book name, so the message names the form it refuses.

## What is refused, measured

`hatch run python`, calling `llmflow.utils.versification.parse_passage_ref`:

| input | result |
|---|---|
| `Mark`, `John`, `Galatians`, `Philemon`, `Jude`, `Titus` | OK |
| `1 John 1`, `1 John 1:1` | OK |
| **`1 John`** | **ValueError** |
| **`1 Corinthians`**, **`2 Peter`**, **`1 Kings`** | **ValueError** |
| **`Song of Songs`** | **ValueError** |

The condition is precise: **a book name containing a space, with no numeric tail.**
Add a chapter and the same name parses. A one-word book name parses.

## Where

`src/llmflow/utils/versification.py:160`

```python
if code is None or (tail is None and " " in text and not _CODE.match(written)):
    _refuse(passage, text)
```

By that line `_book_code(written)` has already resolved the whole string to a book —
`1JN` for `"1 John"`, `SNG` for `"Song of Songs"`. The second clause then rejects it
anyway, because the string contains a space and is not a three-character USFM code.

Re-derivable directly:

```python
from llmflow.utils.versification import _book_code, _split_tail, _CODE
written, tail = _split_tail("1 John")
_book_code(written)                      # '1JN'  — the book was recognised
tail is None and " " in "1 John" and not _CODE.match(written)   # True — refused anyway
```

The guard appears to assume a whole-book reference is a single token. That holds for
`Mark` and for `MRK`, and for no numbered book and no multi-word name.

## Two parsers, disagreeing

The same pipeline calls both, one step apart, and they disagree on this string:

| parser | `"1 John"` |
|---|---|
| `llmflow.utils.data.parse_bible_reference` — used by `parse_book_reference` | `1JN` |
| `llmflow.utils.versification.parse_passage_ref` — used by `type: scripture` | refused |

So step 2 succeeds and step 3 crashes on the identical value. This is the failure
`docs/ai-context/sp/passage-references.md` names in its own words — *"A second parser
drifts from the first, and the drift shows up as analysis of the wrong text"* — and
here it surfaced as a crash, which is the lucky outcome. Silent disagreement between
these two on some other input would not be.

## What it blocks

Every book whose name has a space, as a whole-book passage. In the NT that is
1–2 Corinthians, 1–2 Thessalonians, 1–2 Timothy, 1–2 Peter and 1–3 John; in the OT,
1–2 Samuel, 1–2 Kings, 1–2 Chronicles and Song of Songs.

We are not working around it. Both available workarounds corrupt the output rather
than the input: `${book}` feeds thirteen sites in our pipeline, including five prompts
and the plugins that build `canonical_reference`, so passing `1JN` or `1 John 1-5`
would put that string into every reference in the artifact instead of `1 John`.

## One thing we noticed beside it, not part of the above

`_book_code("Song of Solomon")` returns `None`, where `_book_code("Song of Songs")`
returns `SNG`. That is an alias question rather than this bug, and we have not looked
into it.

## What we are asking

That `parse_passage_ref` accept a book name it has already resolved, whatever
whitespace it contains. The shape of the fix is yours — we have not touched
`versification.py`. `06f0767` *"one declaration of book names, so both ways of writing
one work"* looks like the nearest related change, and we have not established whether
this is a regression against it or predates it.

A test over every book name the declaration holds, with no chapter and no verse, would
have caught this and would keep it caught.
