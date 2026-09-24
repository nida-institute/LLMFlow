# Cutting the English where the Greek is cut

**From:** an AI session in `nida-institute/discourse-flow`.
**About:** **a request for a step type** that returns the target-language text for a span named by
source word ids — what it would have to do, and what we have measured about the data.
**Status: the request in §4 and the ruling in §3 are the Captain's, given 2026-09-11. The prose
and the measurements are the AI's, pending his review.**

## 1. `spans:` is what we needed, and our data already fits it

We have read `3ca7139` and the `spans:` section of the language document. We have not run it yet,
so this is not a report of it working — but every unit in our artifacts carries the pair it takes:
390 units in Mark (93 pericopes, 297 segments) and 16 in Philemon, all with `opening_word_id` and
`closing_word_id` as Macula ids. The segment text you proposed comes from those, from your step,
with nothing for us to slice.

## 2. The English has no such handle

The Greek is addressed by word and yours now cuts on it. The BSB reaches us as a map from verse
reference to a string: we load it, filter by verse range, and emit whole verses
(`plugins/source_language.py:221-244`). At a boundary that falls inside a verse there is nothing
to cut on — no word id in the English, and no alignment in our pipeline.

So of the two fields your shape puts on a segment, `text` is derivable today and `translation` is
not, at exactly those edges.

## 3. What we are doing meanwhile, and how often it matters

Ruled by our Captain today: **where a unit's Greek opens or closes mid-verse, its `translation`
carries the whole verse.** The English is then offset from the Greek by part of a verse at that
edge. `nida-institute/discourse-flow#95` records it so it is not later mistaken for a design, and
is closed by filling a value once your step lands.

How often, measured on the current artifacts — the last three digits of a word id are the word
index within its verse, so `001` is verse-initial:

| book | units carrying word ids | open mid-verse |
|---|---|---|
| Mark | 390 | **4** |
| Philemon | 16 | 0 |
| 1 John | 10 (pericopes only) | 0 |

The four are all segments; no pericope is among them — Mark 7:29-30, 12:16-17, 14:1-2, 15:32-32.
The invariant: 93 pericopes matches the leaf count our 2026-09-09 Mark run reported. The figure
counts openings; on a tiling segmentation a mid-verse close implies the next unit's mid-verse
open.

**So this is 1% of units, and we are not blocked today.** That is sequencing information, not a
reason to decline — we would rather you had the number than read our asking as urgency. The
request in §4 stands whatever you do with the number.

## 4. The request: a step type for this

**We are asking for it to be built in the engine, and our Captain has said so in those terms: we
want the step type in `sp`, because other projects will need it too.**

What it would do: take what `spans:` takes and return the other side of it — given `{from, to}`
pairs of source word ids, the target-language text for each span. Our input would be unchanged,
the same ids from the same segments in the same request shape.

The interface is still yours; a step type is what we would expect, and if an option on
`type: scripture` or a second resource on the same step serves it better, that is your call to
make.

**Why the engine rather than us.** If we build it, we build the BSB-against-Greek case and stop,
and the next project to need it writes it again. The alignment repository you already name is
organised by target language, so one step serves every pair in it. `discourse-flow-hebrew` has
the identical need against WLC, and any project that publishes analysis of a source text beside a
translation meets this the first time a unit boundary falls inside a verse.

## 5. The data is in a repository you already name

`src/llmflow/utils/bible_data.py:63` maps `clear-bible-alignments` to `Clear/Alignments`. That
repository carries `data/eng/alignments/BSB/SBLGNT-BSB-manual.json` and
`data/eng/targets/BSB/nt_BSB.tsv`, with the same layout for `YLT` and sibling language
directories `arb`, `asm`, `ben`, `fra`, `hau`, `hin`, `man`, `mya` under a `catalog.tsv`.

We measured against our own copy of the same pair (`Clear/internal-Alignments/data/bsb`), not
against the file in the repository you name — we confirmed that file exists and did not open it.
In our copy: 115,454 records, `"type": "translation"`, `conformsTo 0.3`, each record

```json
{"source": ["n40001001001"], "target": ["400010010011","400010010021","400010010031","400010010041"]}
```

`source` is Macula word ids — the same ids `spans:` cuts on. The target TSV carries
`identifier, altId, text, transType, isPunc, isPrimary`, so the text and its punctuation flag are
both there.

The nine target-language directories are the concrete form of §4's point: the same step, given a
different pair from that catalogue, serves a project we have never met.

## 6. The decision we cannot make for you

**Alignment is not one-to-one, and the English for a Greek span is not contiguous.** On the span
`n57001018001`–`n57001019017` — Philemon 1:18-19, a real segment in our artifact — the aligned
English is 40 tokens spanning `57001018001` to `57001019026`, with six holes inside the range:

```
jq '[.records[] | select(any(.source[]; . >= "n57001018001" and . <= "n57001019017")) | .target[]]
    | map(.[0:11] | tonumber) | unique
    | {n: length, min: min, max: max, contiguous: (length == (max - min + 1))}' \
  SBLGNT-BSB_alignment.json
→ {"n": 40, "min": 57001018001, "max": 57001019026, "contiguous": false}
```

The invariant holds — the lowest token is the first English word of v.18. We checked one hole:
`570010180141` is a comma, `isPunc: true`, `isPrimary: false`.

So a step has to say what it does with tokens inside a span that no source word aligns to.
Returning only the aligned ones gives *"or owes you anything charge it to my account"* — readable
but not the translation. Returning the whole range gives the translation, and then two adjacent
spans can both claim a token, or a token can fall to neither.

**What we have not checked:** whether the English for a later Greek word can precede the English
for an earlier one. Word order between Greek and English makes it likely, and it would matter
more than the holes. We would rather say we have not measured it than guess.

## 7. One thing noticed while reading the new feature

`docs/llmflow-language.md` still says, at two places, that `include` is valid **only** with
`format: usj` — line 802 and the paragraph at 961-962: *"with `plain` or `milestones` there is
nowhere to put it, and asking is an error rather than a silent no-op."* `3ca7139` implements the
opposite and your own tests assert it
(`test_include_with_any_format_returns_the_text_beside_the_container`,
`test_the_words_arrive_keyed_by_the_id_that_names_them`). The commit's doc change added the
`spans:` section and left those two passages standing. We are reading that document to decide
whether to move our prompts off the word-object form, so it is the sentence that would have
stopped us.
