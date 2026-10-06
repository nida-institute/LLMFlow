# Plan — the starter example costs less without saying less

**Status:** approved and built 2026-10-05 — D1–D3, item 3, and the INPUT DATA fix
§5a found. Measured 2026-10-06; **gpt-4.1 stays** (the Captain, 2026-10-06, agreeing with the
recommendation in §5b).
**Issue:** none of its own; it changes the starter example of #244. One can be drafted on request.
**Author:** AI, from measurements of his MAT 19:1-11 run in `playground/sp-example/`, counted with
`o200k_base` (gpt-4.1's tokenizer), and the code as it stands at `3e5b7de`.

---

## 1. Ruled by the Captain, 2026-10-05

1. **The analyses go to the model in a compact form** — *"definitely, we should only ever be sending
   unicode to LLMs and storing unicode on disk."*
2. **Frequencies are sent only for the rare words** — yes.
3. **The significance step reads the chapter context in English, and the parallel verses
   themselves in the original language** — yes.
4. **A smaller model is measured, and used only if the results are truly comparable.**

## 2. Where the tokens go — measured

| step | input | of which | output |
|---|---|---|---|
| `reader_guide` | ~42k | the Greek USJ as `str(dict)` 37.6k: text 9.8k, morphology 6.9k, frequency 6.4k, syntax 5.5k, glosses 5.0k, senses 4.0k; prompt 4.3k | 4.6k |
| `significance` | ~46k | Greek/Hebrew chapters 31.1k, English chapters 10.8k, member verses 1.8k, prompt 2.4k | 3.0k |

About $0.24 a run at $2/$8 per million. Waste visible in the data: every word's glosses carry a
Mandarin gloss nobody reads; every frequency entry repeats `"corpus": "GNT"`; every word repeats
`'type': 'char', 'marker': 'w'`; the tree is nested objects.

**Unicode, measured:** a prompt value that is a mapping or list is substituted as `str(value)`
(`steps/llm.py:134`) — a Python repr, not JSON, though the prompts call it JSON; Python escapes any
character it deems unprintable. Two writers store `\uXXXX` on disk: `utils/debug.py:212`
(`json.dumps(content, indent=2)`, a debug response) and `utils/content_transition.py:507`.

## 3. Design — for approval

**D1 — a new scripture `format: analysis`.** Plain text, Unicode, two parts per sentence:

```
# MAT 19:1-2 — sentence 1
(cl (conj Καὶ:n40019001001) (cl (v ἐγένετο:n40019001002) (cl … )))
id            form       lemma     morph                  gloss     sense   rare
n40019001001  Καὶ        καί       conj                   And       91.1
n40019001002  ἐγένετο    γίνομαι   verb aor mid ind 3s    happened  13.107
```

- The tree in bracketed notation — the treebank convention — with each word as `form:id`, its
  class and role as the label. Every node and attachment of today's tree is kept.
- One table row per word, columns only for the families requested, glosses in English only.
- Words outside the requested verses (whole-sentence widening) marked in a column, as now.
- `milestones`, `plain` and `usj` are unchanged; `usj` stays the lossless, saved form.

The starter's Greek and Hebrew steps fetch `format: usj` for the saved intermediate as now, and a
second, free scripture step fetches `format: analysis` for the prompt — or one step with two
members, if you prefer.

**D2 — `frequency_cutoff:` on a scripture step.** With it, a word gets its frequency only when its
lemma falls within that least-frequent percent; without it, every word does, as today. The guide's
prompt then reads "a word with a frequency is a word to explain," rather than comparing numbers.

**D3 — prompt values are substituted as JSON, Unicode unescaped** (`ensure_ascii=False`), and the
two disk writers above write Unicode. A mapping in a prompt is then what the prompt says it is.

## 4. Item 3 — no engine change

`chapter_greek` / `chapter_hebrew` go; `locate_member` gains an original-language twin, fetched by
testament, so each member verse arrives in Greek or Hebrew; the chapter is fetched in English
only. The prompt's instructions about the original context are reworded to match.
Expected: `significance` ~46k → ~18k.

## 5. Measuring — each run needs the Captain's direction

1. **Before/after on the same passages**, gpt-4.1, MAT 19:1-11 (synoptic, has parallels) and one
   Old Testament passage once the Hebrew data is registered. He compares the outputs; the change
   ships only if he judges them equal.
2. **Then gpt-4.1-mini on the same passages**, side by side with (1). Adopted only if he judges the
   results truly comparable.

Estimated: about $0.15 for a gpt-4.1 run after the changes, about $0.03 for gpt-4.1-mini.

## 5a. Measured, 2026-10-05/06 — MAT 19:1-11

| run | cost | input as rendered | notes |
|---|---|---|---|
| original (`3e5b7de`) | ~$1.00 (the Captain's figure) | significance ~340k | `{{parallel_texts}}` filled 8× |
| after D1–D3 + item 3, gpt-4.1 | $0.4396 | 58,735 + 131,205 | every mention still filled |
| after the INPUT DATA fix, gpt-4.1 | $0.1274 | 13,331 + 18,699 | |
| same, gpt-4.1-mini | $0.0256 | same | |

**The first finding was not tokens but placeholders**: every `{{name}}` was filled, so each input
went to the model once per mention. Fixed in the engine (Captain's option A): a value is filled
only under `# INPUT DATA`.

**The second was a regression `analysis` introduced**: a guide gave "occurs 34×" for words with
no frequency — the Louw-Nida number from the unlabelled `sense` column (κολληθήσεται LN 34.22,
πορνείᾳ 88.271, συμφέρει 65.44). The original run's counts were all correct, because USJ
labelled them. Every number in `analysis` is now labelled; the two runs above predate that and
must be repeated before the Captain judges quality.

Checked against the input, before the labelling fix: all four guides cover the 9 distinct
infinitives and participles; gpt-4.1 covers all 8 less common words, gpt-4.1-mini 7. Words
given a count they should not have: original 16 (true counts, wrong words — it compared the
cut-off itself), fixed gpt-4.1 7, gpt-4.1-mini 18 (sense numbers).

## 5b. With every number labelled — the runs judged

| guide | cost | less common words | non-finite verbs with "Attaches to" | counts given to words not less common |
|---|---|---|---|---|
| original | ~$1.00 | 8/8 | 9/9 | 16 (true counts, wrong words) |
| labelled gpt-4.1 | $0.1281 | 8/8 | 9/9 | 0 — exactly 8 counts, all the table's |
| labelled gpt-4.1-mini | $0.0250 | 8/8 | 9/9 | 16, each "1" or "2", in no input |

**Ruled: gpt-4.1 stays.** gpt-4.1-mini invents counts where the rule says to give none, and the
prompt's contract is that every count comes from the data — not comparable. The checks cover
coverage and counts only; the quality of the explanations and of the significance output is the
Captain's to judge from `playground/sp-example/outputs/{,labelled-4.1/,labelled-mini/}`.

## 6. Tests, written first

- `format: analysis` carries every word, every tree node and every requested family of the USJ
  form it is derived from — checked by round-tripping the counts on MRK 1:1-8 and MAT 19:1-11
- no Mandarin or other non-English gloss in it unless asked for
- `frequency_cutoff` leaves frequencies only on words within it
- a mapping substituted into a prompt is valid JSON with no `\u` escapes
- the debug writer and the content-transition writer write Unicode
