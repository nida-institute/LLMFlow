# Annotation without anchors

**Status:** proposed (2026-09-09). Nothing is built. `proposed` is not authorization to build —
§6 lists the decisions that must be ruled first.
**Issue:** #200 — the epic for scripture editions and their representations, *"choose what
reaches the model"*, which is exactly this question.
**Raised by:** `collab/discourse-flow/2026-09-09-include-forces-the-most-expensive-text-form.md`
**Touches:** `utils/scripture.py` — `check_include`, `rows_to_output`, `rows_to_usj`

---

## 1. What is true now, checked rather than recalled

**`include` is refused unless `format: usj`.** `check_include` (`scripture.py:464`):

```python
if fmt != "usj":
    raise ValueError(f"include {list(families)} needs `format: usj`; `{fmt}` has nowhere to put a payload.")
```

**The reason is the return type, not the annotation.** `rows_to_output` returns `str | dict`:
`usj` takes the dict branch, every other format returns `rows_to_text(...)`, a bare string. A
string has nowhere to hang a `scripture_pipelines` key. The families themselves are standoff and
need nothing from the shape of the text.

**A per-word payload is keyed by opaque word id and carries only the annotation.** Fetched live
from `WLC`, `Ruth 1:1`, `include: [ids, senses]`:

```
'o080010010022' -> {"lexdomain": "002002002010", "coredomain": "180",
                    "sdbh": "002854001003000", "sensenumber": "1"}
'o080010010031' -> {"sensenumber": "5"}
```

There is no surface form, no reference, nothing saying which word this is.

**Which is why the anchors are load-bearing.** `ids` writes `srcloc` onto `\w` nodes, and it is
the *only* way to answer "which word is `o080010010022`?". `check_include` says so when refusing
`syntax` without `ids`: *"no word in the document carries the `srcloc` the payload points at, so
the payload names words the document does not identify."*

So the chain is: **payload is not self-describing → anchors are required → `ids` is required →
USJ is required → the most expensive text form is required.**

## 2. What it costs, measured downstream

From the collab note, Philemon:

| | |
|---|---|
| Levinsohn citations in the book | 106 |
| words carrying a `\w` anchor | 334 |
| anchored words nothing references | **228** |

And Philemon 1:1–7: 622 characters of Greek prose delivered as **14,045** characters of JSON —
**22.6×**. The text arrives as 107 word objects separated by 106 punctuation strings; a reader
reconstructs the sentence by concatenation.

Our own document costs `usj` + families at up to **11.78×** against `milestones` at 1.072×.

## 3. The bind

`scripture-representations.md` says *"asking for a family you do not read is pure cost"*. The
inverse is what this document is about: **asking for a family you do read forces a text form you
did not want.** A pipeline whose subject is discourse features cannot have milestone-cost text.

## 4. Three options

### A. Leave it

`include` continues to require `usj`. Consumers pay 11.78× or go without annotation.

*For:* no work, no new shape, no migration. *Against:* the cost is real and recurring, and it
falls hardest on the pipelines that use the engine's most distinctive feature.

### B. Thin the anchors — anchor only referenced words

Write `srcloc` only where some requested family references the word. Philemon: 106 anchors
rather than 334.

*For:* the biggest single saving, and it matches what discourse-flow's prompts were written
against — *"anchors sit at Levinsohn-marked positions"*, the shape their retired file-based
loader produced.

*Against, and I think decisively:* **the text then varies with the `include` list.** The same
passage returns different documents depending on which families were asked for, so a change to
`include` silently changes the text a prompt sees. That is the shape that produces "it worked
yesterday". It also reintroduces the arrangement whose absence drove 555 lines of
`milestone_content.py` in the consumer, re-deriving what the engine delivers — history worth
reading before repeating.

### C. Make the payload self-describing

Each entry carries its own identity:

```json
{"id": "o080010010022", "text": "וַיְהִי", "ref": "RUT 1:1",
 "lexdomain": "002002002010", "coredomain": "180"}
```

Then nothing needs to be found in the text, and the chain in §1 breaks at its first link:

- anchors are not needed, so `ids` stops being forced
- `include` becomes valid with `milestones` and `plain`
- only annotated words appear — 106 entries, not 334 anchored words
- the payload is legible to a language model without a join. An opaque id is a key for a
  machine; `"וַיְהִי" at RUT 1:1 has coredomain 180` needs no resolution at all

*Against:* every entry grows by a surface form and a reference. Against dropping 107 word objects
and 106 punctuation strings, that is expected to be far cheaper, **but it is not yet measured** —
see §6.

*Also unresolved:* a duplicate surface form within a verse (`וַיְהִי` occurs twice in Ruth 1:1)
is not uniquely identified by text-plus-reference. The `id` stays in the entry as the precise
key; it is simply no longer needed *in the document*.

## 5. What C would change

- `check_include` stops requiring `usj`, and stops requiring `ids` for the standoff families
- `rows_to_output` returns a dict for non-`usj` formats **when `include` is non-empty** — a new
  shape, and the thing most likely to break a consumer
- per-word families gain `text` and `ref` per entry
- `ids` keeps its present meaning: write anchors into the document, for consumers that want them

## 6. Decisions needed

1. **Is C the direction?** Or is the cost acceptable and A the answer?
2. **What does `type: scripture` return for `format: milestones` with a non-empty `include`?**
   A dict `{text, scripture_pipelines}` is the obvious shape, and it means the step's return type
   depends on a sibling key. Is that acceptable, or should the annotated form have its own format
   name?
3. **Does `ids` survive as a family?** Under C it becomes "put anchors in the document", which is
   a different thing from "let annotation be joined". Same name, or a new one?
4. **Do `lemma` and `strong` belong with `morphology`?** They arrive with it today and are a
   third of the consumer's inflation. Separate family, or intended?
5. **Is B worth keeping as an option at all**, or is a text that varies with `include` ruled out
   on principle?

## 7. What to measure before ruling

Not estimates. For one passage — Philemon 1:1–7, since the consumer has already costed it:

- `usj` + all families, as today: the 14,045-character baseline
- `milestones` + the same families under C: text plus self-describing payload

If C is not decisively cheaper, its main argument goes and A becomes more attractive.

## 8. Not in scope

How discourse-flow uses the result. Their note says they will not thin the payload locally and
will take whatever the engine returns — *"we would rather do that than invent a private format"* —
which is the right instinct and the reason this belongs here rather than there.
