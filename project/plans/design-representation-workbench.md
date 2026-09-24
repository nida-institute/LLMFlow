# Representations of the same text — a workbench

**Status:** proposed (2026-09-10). **This document rules nothing.** It exists so the decisions in
`design-annotation-without-anchors.md` §6 are taken against measured cells rather than remembered
ones. Per `plans-are-temporary` it dies on 2026-09-18 unless its content has moved into the
CHANGELOG or the rules.
**Issue:** #200 — *"choose what reaches the model"*.
**Companion:** `design-annotation-without-anchors.md`, whose §7 measurement is three rows of §2
below.

## 1. What this is and how to re-run it

Seventy-two cells: three passages × three formats × eight `include` combinations. Each cell is
produced by the two functions `steps/scripture.py` itself calls, so a cell is what a
`type: scripture` step returns — not a model of one.

```bash
hatch run python tmp/representation-grid/generate.py
```

Writes `tmp/representation-grid/grid.tsv`, `grid.json`, and one file per returned cell under
`cells/`. No pipeline, no model, no spend. Every number below is re-derivable with that command,
per `declared-not-inferred`; nothing here is estimated.

**The passages, and why these three.** `PHM 1:1-7` (SBLGNT) because downstream has already costed
it. `RUT 1:1` (WLC) because Hebrew's families differ from Greek's and because it is where the
opaque-payload fact was established. `MRK 1:1-8` (SBLGNT) because `syntax` is the largest family
and 127 words is where its shape shows.

**The eight combinations:** `[]`, `[ids]`, `[senses]`, `[ids,senses]`, `[discourse]`,
`[ids,discourse]`, `[ids,syntax]`, and all seven families.

## 2. The grid

Codepoints, and the multiple of that passage as `plain`. **45 of the 72 cells are refusals**, and
which ones are refused is as much the design surface as the sizes are.

### PHM 1:1-7 — 623 codepoints as `plain`

| include | plain | milestones | usj | ×plain | anchors | payload entries |
|---|---|---|---|---|---|---|
| `[]` | 623 | 665 | 1,329 | 2.13 | 0 | — |
| `[ids]` | refused | refused | 9,910 | **15.91** | 107 | — |
| `[senses]` | refused | refused | **refused** | — | — | — |
| `[ids,senses]` | refused | refused | 14,715 | 23.62 | 107 | senses 88 |
| `[discourse]` | refused | refused | 4,277 | 6.87 | **0** | discourse 23 |
| `[ids,discourse]` | refused | refused | 12,809 | 20.56 | 107 | discourse 23 |
| `[ids,syntax]` | refused | refused | 19,061 | 30.60 | 107 | syntax 4 |
| all seven | refused | refused | **49,783** | **79.91** | 107 | 107/88/107/20/23/4 |

### RUT 1:1 — 174 codepoints as `plain`

| include | usj | ×plain | anchors | payload entries |
|---|---|---|---|---|
| `[]` | 454 | 2.61 | 0 | — |
| `[ids]` | 3,039 | 17.47 | 32 | — |
| `[ids,senses]` | 4,697 | 26.99 | 32 | senses 18 |
| `[ids,discourse]` | 3,058 | 17.58 | 32 | **discourse null** |
| `[ids,syntax]` | 3,055 | 17.56 | 32 | **syntax null** |
| all seven | 12,384 | 71.17 | 32 | morphology **33**, glosses 33, senses 18, referents 7 |

### MRK 1:1-8 — 799 codepoints as `plain`

| include | usj | ×plain | anchors | payload entries |
|---|---|---|---|---|
| `[]` | 1,576 | 1.97 | 0 | — |
| `[ids]` | 11,753 | 14.71 | 127 | — |
| `[ids,syntax]` | 22,240 | 27.84 | 127 | syntax 6 |
| all seven | 63,231 | 79.14 | 127 | morphology 127, senses 124, glosses 127, referents 38 |

## 3. What the cells actually contain

**`plain` and `milestones` differ by 42 characters on PHM 1:1-7** — the seven `⌊1:1⌋` markers:

```
⌊1:1⌋ Παῦλος δέσμιος Χριστοῦ Ἰησοῦ καὶ Τιμόθεος ὁ ἀδελφὸς Φιλήμονι τῷ ἀγαπητῷ …
```

**`usj` with no `include` contains no word objects at all** — 0 `w` nodes. The text sits as
strings inside one `para` per chapter. All the word-object structure comes from `ids`, not from
the format.

**`ids` turns each word into a node** (SBLGNT):

```json
{"type": "char", "marker": "w", "content": ["Παῦλος"], "srcloc": "n57001001001"}
```

**A per-word family is a map keyed by that srcloc:**

```json
"senses": {"n57001001001": {"domain": "093001", "ln": "93.294a"},
           "n57001001002": {"domain": "037008", "ln": "37.117"}}
```

**`discourse` is a list, and its items are keyed the same way:**

```json
{"id": "n57001001001", "kind": "feature", "feature": "Main clauses",
 "outcome": "verified", "index": 1, "level": 0}
```

**Hebrew words are morphemes.** RUT 1:1's 32 `w` nodes are not 32 words:

```
o080010010011=וַ   o080010010012=יְהִ֗י   o080010010021=בִּ   o080010010022=ימֵי֙
o080010010031=שְׁפֹ֣ט  o080010010041=הַ   o080010010042=שֹּׁפְטִ֔ים  …
```

## 4. What the grid showed that we did not already know

**F1 — the anchors cost more than the annotation they exist to serve.** On PHM 1:1-7, `ids` adds
**8,581** codepoints to bare USJ; the entire `senses` payload adds **4,805**. The join mechanism
is 1.8× the data it makes joinable. `discourse` is 2,948 against the same 8,581.

**F2 — the 22.6× baseline is not the engine's cost.** `design-annotation-without-anchors.md` §2
carries *"622 characters of Greek prose delivered as 14,045 characters of JSON"*. The collab note
labels that figure correctly — *"in the artifact **we publish**"* — but the engine's own output
for the consumer's exact list (`[ids, discourse, morphology, senses, referents, syntax]`) is
**42,103 codepoints, 67.6×**; whole-book Philemon is 136,329. Any ruling that treats 14,045 as
the thing to improve on is aiming at a number three times smaller than the real one.

**F3 — there are two ids gates, and `discourse` passes both.** `check_include` refuses `syntax`
without `ids` (`FAMILIES_NEEDING_IDS`, `scripture.py:102`), and `rows_to_usj` separately refuses
the per-word families with a different message (`scripture.py:537`). `discourse` is in neither
set — so `usj + [discourse]` returns a document containing 23 items keyed `n57001001001` and
**zero** words carrying that id. That is precisely the state the other two gates exist to
prevent, permitted for one family. Either the gates are stricter than they need to be, or this
one is a hole; the grid cannot say which, and it is a ruling rather than a measurement.

**F4 — the option-C example in the companion document pairs an id with the wrong word.** It
writes `{"id": "o080010010022", "text": "וַיְהִי", "ref": "RUT 1:1"}`. Measured,
`o080010010022` is **ימֵי֙** — the noun morpheme of בִּימֵי. וַיְהִי is two other nodes,
`o080010010011` + `o080010010012`. The correction matters beyond the typo: under C a Hebrew
entry's `text` is a **morpheme**, often a single letter (בִּ, הַ, וַ), so the legibility argument
— *"`text` at `ref` has coredomain 180 needs no resolution at all"* — is a Greek argument. In
Hebrew the reader gets a bound morpheme with an accent mark.

**F5 — some annotation has no surface form at all.** RUT 1:1 carries a morphology entry keyed
`o080010010071ה`: `{"class": "art", "type": "definite article", "pos": "particle", "lang": "H"}`,
gloss `"the"`. It is the article elided into בָּ. **No `w` node carries that srcloc**, so with
`ids` requested and the join working as designed, this entry is unjoinable today — 1 of 33. C
does not rescue it either: there is no text to put in `text`. Greek has none of these; both Greek
passages return an empty orphan set.

**F6 — the duplicate-surface-form worry is smaller than stated, and differently shaped.** The
companion says וַיְהִי occurs twice in RUT 1:1 and so text-plus-reference cannot identify it.
Measured, the two are `יְהִ֗י` and `יְהִ֥י` — different accents, therefore different strings.
They collide only after normalisation, which is a choice a consumer makes rather than a property
of the data.

**F7 — `null` and `{}` are doing their job.** WLC returns `"discourse": null` and
`"syntax": null` with a warning naming the missing registry key, because no Hebrew discourse or
Lowfat source is registered. A reader can tell "not looked for" from "looked and found nothing"
without asking us — `say-which-kind-of-nothing`, working, in live output.

**F8 — the multiplier depends on the unit, by 4.6×.** PHM 1:1-7 with all seven families is
**79.9× in codepoints** and **17.4× as escaped JSON** — because Greek escapes to ~5× while the
ASCII payload does not. Both figures are true and they answer different questions. Every cost
claim in this discussion needs its unit attached, which `scripture-representations.md` already
warns about and which the 22.6× figure does not carry.

## 5. Use cases — who reads what

Drawn from the two collab notes and the shipped docs, not invented.

| # | who | reads | needs to be able to |
|---|---|---|---|
| U1 | discourse-flow, book run | `discourse` + text | cite word ids in prompts, window over the book, segment into pericopes |
| U2 | discourse-flow-hebrew | the same over WLC | get anything at all — today both its families are `null` |
| U3 | most prompts | text only | quote a verse. `milestones`, 1.07× |
| U4 | consumers walking USJ | the document | flatten, take word ids in a span, cut by `sid` or word id, re-emit valid USJ (their §2.1) |
| U5 | derived profiles — cohesion, leitwort | `senses`, `morphology`, `referents` | consume the payload alone; the text shape is irrelevant to them |
| U6 | a reader-facing artifact | text + `glosses` | render prose a person reads |

U5 is the one the current coupling hurts most and the one least visible in the discussion so far:
those consumers do not want the document at all, and today they must take 107 word objects to get
a map of 88 entries.

## 6. Requirements the cells argue for

Numbered so an option can be checked against them rather than argued about. **These are proposed,
not ruled.**

- **R1** Choosing an annotation must not choose a text form. (F1, U5)
- **R2** The text a prompt sees must not vary with `include`. (the standing objection to option B)
- **R3** Every payload entry must be resolvable to a place in the text by the consumer, or must
  say that it cannot be. (F3, F5)
- **R4** Absence keeps its two meanings — `null` versus `{}` — in whatever shape ships. (F7)
- **R5** Whatever ships works for Hebrew morphemes as well as Greek words, including entries with
  no surface form. (F4, F5)
- **R6** Cost is proportional to what was asked for: asking for one family does not deliver the
  machinery of another. (F1)
- **R7** Any cost claim states its unit. (F8)

## 7. Questions — yours, and none of them answered here

Per `surface-decisions.md`, the line after each `=>` is where your ruling goes.

**Q1. Which unit governs these decisions — codepoints, or escaped JSON as a prompt actually
carries it?** They disagree by 4.6× on the same cell (F8), and every later comparison inherits
whichever you pick.

=>

**Q2. Is `discourse`'s exemption from both ids gates intended?** (F3) It ships an unjoinable
payload today. If the exemption is right, the same reasoning permits the per-word families; if it
is wrong, the gate is missing rather than the design being wrong.

=>

**Q3. What should a self-describing entry carry for an annotation with no surface form** — the
elided article of F5? An empty `text`, a `null`, or does it stay unjoinable and say so?

=>

**Q4. Does F4 change the weight of option C?** Its legibility argument holds in Greek and thins in
Hebrew, where `text` is a bound morpheme. Is legibility still the argument, or is the argument now
only cost?

=>

**Q5. Should this grid become a committed fixture** rather than a `tmp/` script? It is 27 real
payloads that no test currently covers, and `stale-output-is-a-defect` applies to it the moment
the code changes.

=>

## 8. Not in scope

What any of this means for discourse-flow's pipeline; how `include` should be spelled; whether
`ids` keeps its name. Those belong to the companion document's §6, after these questions are
answered.
