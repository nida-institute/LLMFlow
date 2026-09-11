# Pericope → segments → text: redesigning the handoff

**Status:** ruled (2026-09-10) on §10 Q1–Q10; nothing is built. §7–§9 remain proposals except
where a ruling in §10 adopts them. **Two items are reopened by evidence found after the ruling
— Q6's elided article and Q9's compound marker — and four small carve-outs await a yes or no,
marked `=>` in §10 (Q2 E3-first, Q5 sharing, Q7 `print`, Q9).** Per `plans-are-temporary` this
file dies on 2026-09-18 unless its rulings have moved into the CHANGELOG.
**Issue:** #200 — *"choose what reaches the model"*.
**Companions:** `design-representation-workbench.md` (the measured grid),
`design-annotation-without-anchors.md` (the `include`/`usj` coupling).
**Two consumers, and they are the two that matter:** `nida-institute/discourse-flow` produces
the analysis; `nida-institute/ears-to-hear` consumes it in `build-book.yaml`.

---

## 1. The target

The Captain, 2026-09-10:

> *"a pericope holds segments, each segment holds the text itself in [milestone] format, and all
> the things it asks for in the build-book.yaml are available and useful without all the cruft."*

And on cost:

> *"it also increases token cost and wall clock time. focus matters more than these, but it IS
> getting expensive"*

So three tests, in the Captain's order of priority: **can a model or a person read it**, **does
`build-book.yaml` still get everything it asks for**, and **what does it cost**.

### The ordering that governs every proposal below

Stated by the Captain, 2026-09-10, and it decides the cases where the three tests disagree:

> *"we can optimize all of these. but without loss of information, and both LLM focus and
> readability are more important than tokens or size or processing time."*

Two things follow, and they are the standard §7–§9 are written against.

**Nothing is deleted; things are relocated or derived.** A field may move, be computed on demand,
or stop being serialised in a place where it is redundant — but no fact that exists today may
become unavailable. Where a proposal fails that test it is marked, not quietly dropped: §6.1 is
one such case.

**A saving that costs focus is not a saving.** Indentation, duplicated encodings and payloads a
prompt never reads are pure win. Shortening something a model or a reviewer needs to see is a
loss, whatever it does to the token count.

## 2. What happens today, measured

The text crosses three artifacts and two conversions before a prompt sees it.

```
sp  type: scripture  SBLGNT PHM, format: usj, include: [ids, discourse, morphology,
                     senses, referents, syntax]                      136,329 chars
 ↓  discourse-flow: slice per pericope, strip the annotation container
    output/book-discourse/57-PHM-discourse.json                      259,210 bytes on disk
 ↓  ears-to-hear: plugins/load_discourse.usj_to_milestone_string
    ${pericope_section.source_text}                                  51 chars
 ↓  ten gpt-4.1 steps per pericope
```

The Greek in all of this is **1,942 characters** — whole-book Philemon as `plain`; 2,108 as
`milestones`.

**Where the 259 KB goes** (248,926 codepoints on disk, 130,096 compacted):

| | codepoints | share of file |
|---|---|---|
| indentation — **ours, see below** | 118,830 | **47.7%** |
| their analysis fields | ~81,700 | 32.8% |
| `source_text` — 4 USJ docs | 43,938 | 17.7% |
| `translation` — 4 USJ docs | 4,445 | 1.8% |
| `genre_markers`, 19 of 25 empty | 1,204 | 0.5% |

**Corrected 2026-09-10 by discourse-flow, and verified here: the indentation is the engine's.**
An earlier draft filed it under "theirs and cheap" and named `separators=(",",":")` as their
fix. They never serialise the artifact — the step returns a dict and `saveas:` writes it, and
`grep -rn "json.dump"` over their tree returns nothing. Ours is `utils/io.py:409`:
`json.dump(content, f, ensure_ascii=False, indent=2)`, hardcoded in `save_json`, so **every
`saveas` JSON artifact in every pipeline is indented and no pipeline can decline it**.

**And it stays.** Ruled by the Captain, 2026-09-10: *"we normalize spaces by pretty printing …
the number of spaces doesn't matter, 2, is fine, what matters is validity. adding complexity to
the interface is the wrong move."* So the row is not a defect and not a saving — it is the
engine writing valid, readable output, which is what the §1 ordering asks for. The 47.7% is a
measurement, not a finding. `genre_markers` in the row above genuinely is theirs.

## 3. The live defect: `source_text` is punctuation

`build-book.yaml` never calls `type: scripture`. It reads discourse-flow's file and converts it
with `plugins.load_discourse.usj_to_milestone_string` (`load_discourse.py:14`), which walks each
`para` and keeps **only bare strings**. In an anchored USJ document the words are `char`/`w`
nodes and the bare strings are the punctuation. Run through their own `extract_pericopes`:

```
Philemon 1:1-7     51 chars   ⌊1:2⌋ ’ · ⌊1:3⌋ . ⌊1:4⌋ , ⌊1:5⌋ , ⌊1:6⌋ · ⌊1:7⌋ , ,
Philemon 1:8-16    94 chars   ⌊1:8⌋ , , ⌊1:9⌋ , ⌊1:10⌋ , , ⌊1:11⌋ , ⌊1:12⌋ , ’ · …
Philemon 1:17-22   69 chars
Philemon 1:23-25   25 chars
```

That value is `source_text` for `canonical_context`, `background`, `staging`, `bodies`,
`hearts`, `pericope_intro`, `pericope_narrative_title`, `narrative_profile`,
`literary_analysis` and `frameworks` — ten LLM steps per pericope, each asked to analyse a
passage it is not shown. Rule `source-text-required`, breached silently.

**Everything the current pipeline produces is broken — two files of two.** Running
`extract_pericopes` over the output of the 9 September run:

| discourse file | converts to |
|---|---|
| `41-MRK-discourse.json` | **0 Greek letters** |
| `57-PHM-discourse.json` | **0 Greek letters** |

Older files in that directory convert cleanly, and they are not evidence: they were written by
earlier versions of the pipeline, in a format it no longer emits. By `stale-output-is-a-defect`
they are wrong rather than reassuring — regenerating any of them produces a file `build-book`
cannot read.

The current output differs structurally in a second way — Mark now has **17 leaf pericopes**
where the August run had 131 — which is discourse-flow's business rather than ours, except that
it means the August artifact is not a fallback.

**Nothing published is damaged yet.** Every saved outline in ears-to-hear is dated 30 July to
16 August and every one still carries its source language — Philemon 1,560 letters, Mark 56,265,
Ruth 10,688 — and no artifact anywhere under `outputs/` for those books is newer than 16 August.
So no `build-book` run has consumed a broken file. The damage arrives with the next run of Mark
or Philemon, silently.

*(An earlier draft of this section said "it has not fired yet" on the strength of one file's
modification date. That was one book's evidence stretched into a general claim; the table above
is what was actually checked.)*

**Both sides own part of it.** Theirs: a hand-rolled converter that skips the node type carrying
the words. **Ours:** `usj_to_text(usj, fmt="milestones")` already does this correctly — it
recovers all 672 characters of that pericope — but on their sliced document it emits `⌊?:1⌋`,
losing the chapter although the verse `sid` says `PHM 1:1`, and it detaches punctuation
(`ἐκκλησίᾳ ·`, `κατ ’ οἶκόν`). The shipped alternative is better than theirs and still not right.

## 4. Where the cost actually is

Not in the text, and not in the fetch.

**The fetch is not the bottleneck.** Whole-book Philemon: `milestones` 445 ms / 2,108 chars,
`usj` + their six families 675 ms / 136,329 chars. A 230 ms difference, once per book.

**The prompt payload is.** `build-book.yaml` passes `scene: "${pericope_section}"` — the whole
leaf pericope object — into most of its ten steps:

| pericope | whole `scene` | `segments` alone | largest fields inside |
|---|---|---|---|
| PHM 1:1-7 | 17,590 | 4,107 | `supporting_evidence` 3,811, `levinsohn_signals_to_cite` 2,296 |
| PHM 1:8-16 | 30,312 | 7,700 | `supporting_evidence` 6,947, `levinsohn_signals_to_cite` 4,169 |
| PHM 1:17-22 | 23,607 | 7,296 | `supporting_evidence` 4,104, `levinsohn_signals_to_cite` 3,011 |
| PHM 1:23-25 | 6,475 | 2,637 | `structure` 815, `translation` 492 |

**77,984 characters across four pericopes**, most of it fed to ten prompts each. Against 1,942
characters of Greek. **Fixing the USJ shape alone would barely move the bill** — the cost is
discourse-flow's analysis metadata travelling inside `${pericope_section}` into prompts that
were never shown to need it.

**Corrected 2026-09-10 by discourse-flow, and the correction is right.** An earlier draft of
this section said the prompt payload was *"a focus question rather than a cost one"*, four
sentences after locating the weight there. A prompt payload **is** tokens, and the object
reaches a prompt once per pericope for every pericope in the book — so the paragraph identified
a cost and then declined the word, which files it under the heading that gets deferred.

**It is both, and the split does not exist.** An oversized payload is paid twice: once in
tokens, and once in the analysis it degrades. Of those the second is dearer, because a run that
attended to the wrong half of its input is re-run and re-reviewed, and the reviewing is the
Captain's time. The §1 ordering says focus outranks tokens; it does not say the tokens are not
also being spent.

So: **text shape is a focus problem** — a prompt that cannot see the passage cannot attend to it
— and **prompt scope is both**, with the focus half the more expensive. Neither fix removes a
fact from the artifact: §9's H3 routes fields, it does not delete them.

## 5. What is structurally wrong

**W1 — the text can only be had in the expensive form.** `include` requires `format: usj`, so a
pipeline reading Levinsohn features cannot also have milestone prose. Everything downstream is
a workaround for that.

**W2 — the extension is the problem, not USJ.** *(Corrected by the Captain, 2026-09-10: "I think
people DO want USJ and USX as options, but without our extensions." An earlier draft of this
document said "nobody wants the USJ", generalising from two consumers' behaviour to a claim
about the format. That was wrong.)*

USJ and USX are the interchange formats of this field and are wanted in their own right. What is
not wanted is **our extension riding inside them**, or the form being **forced** on a consumer
who asked only for annotation.

The evidence supports the corrected reading rather than the original one. discourse-flow's
published `source_text` is **standard, extension-free USJ**: the `scripture_pipelines` container
is stripped, and every attribute on its `w` nodes — `srcloc`, `lemma`, `strong` — is USX-defined,
which is why `scripture-representations.md` puts `ids` there rather than in the container. The
one non-standard thing in the file is `genre_markers` on verse nodes, and that is theirs. So
they are not discarding USJ; they are producing conformant USJ, which is a legitimate deliverable.

What is actually wrong is narrower and still real: **a consumer who wants milestone text has to
buy the word-object document to get annotation** (W1), and then convert it — badly, as §3 shows.
Two legitimate wants, one artifact, and today the artifact can only satisfy one of them.

**W3 — segments carry no text.** A segment today has `opening_word_id`, `closing_word_id`,
`verse_range`, `opening_verse_sid`, `closing_verse_sid` and analysis — and no text at all. The
pericope holds one lump of `source_text`; the segments hold references into it. Anything wanting
a segment's words must slice, which is why `milestone_content.py` exists.

**W4 — three hand-rolled walkers over our own format.** `usj_to_milestone_string` in
ears-to-hear; `slice_usj_content`, `_strip_levinsohn_features` and four more in discourse-flow.
Each is a private reimplementation of something the engine either ships or should.

**W5 — the only running Greek in the artifact is quoted by the model.** 82 contiguous Greek
strings of 40+ characters in the published file, and every one is in an analysis field the model
wrote (`evidence`, `reason`, `opening_greek_here`). A human auditing a claim has nothing to
check it against.

## 6. The proposed shape

A pericope holds segments; a segment holds its own text, **in whichever form that consumer
asked for**. For the two consumers here that is milestone text, and the example below shows it —
but the shape is "the segment carries its text", not "the text is milestones". A project
publishing for Paratext or a typesetter asks for USJ, USX or USFM and gets the same structure
with a different `text`.

```json
{
  "id": "pericope:n57001001001-n57001007012",
  "canonical_reference": "Philemon 1:1-7",
  "verse_range": "1:1-7",
  "title": "Thanksgiving for Philemon's love and faith",
  "segments": [
    {
      "id": "segment:n57001001001-n57001003012",
      "canonical_reference": "Philemon 1:1-3",
      "verse_range": "1:1-3",
      "opening_word_id": "n57001001001",
      "closing_word_id": "n57001003012",
      "text": "⌊1:1⌋ Παῦλος δέσμιος Χριστοῦ Ἰησοῦ καὶ Τιμόθεος ὁ ἀδελφὸς Φιλήμονι …",
      "translation": "⌊1:1⌋ Paul, a prisoner of Christ Jesus, and Timothy our brother, …",
      "levinsohn_features": [
        {"id": "n57001001001", "feature": "Main clauses", "outcome": "verified"}
      ]
    }
  ]
}
```

Three properties worth stating, because each is a decision and not an obvious consequence:

- **the text is a string, in milestone format** — readable by a person, quotable by a model,
  and 1.07× the cost of bare text
- **word ids stay** on the segment boundary and inside `levinsohn_features`, because they are
  the precise key; they are simply no longer needed *in the text*
- **the pericope's `source_text` disappears** — a pericope's text is the concatenation of its
  segments', so storing both is two encodings of one fact (`design-is-declarative`)
- **the form is the consumer's choice, and our extension is never in it by default** — a
  request for USJ returns conformant USJ; annotation travels beside the text, not inside it
  (E6)

### 6.1 What §6 would lose, and what would preserve it

Held against the no-loss standard, most of §6 passes and **one part does not**.

**Lossless.** Dropping the pericope's `source_text` loses nothing: a pericope's text is the
concatenation of its segments'. Dropping indentation loses nothing. Moving `genre_markers` out
of verse nodes into the segment loses nothing. Not serialising the annotation container that
discourse-flow already strips loses nothing that reaches anyone today.

**Not lossless, and this is the real cost of §6.** An anchored USJ document can answer *"where
in the text is word `n57001004003`?"* for **every** word — that is what 334 `srcloc` attributes
buy. A milestone string cannot: it has segment boundaries and verse markers, and nothing finer.
Any consumer that needs to locate an arbitrary word in the text loses that ability.

Who actually needs it decides how much this matters, and the evidence is mixed. Their own note
says 228 of 334 anchored words in Philemon are referenced by nothing — so most of the addressing
is unused. But `levinsohn_features` cites word ids, and a reviewer checking *"Main clauses at
`n57001001009`"* against the text has to find that word.

### 6.2 The word array — the Captain's proposal, measured

His words, 2026-09-10:

> *"a simple data structure could provide this map. apps can ask for it with include [ids]. or
> really, we could just use arrays and indexes, where the array contains the list of words for
> greek, and hebrew can also use embedded lists for morphs within a word. compound words in
> hebrew are one complicating factor we need to account for."*

Beside the milestone text, a segment carries the words as an ordered array. The index *is* the
address, so nothing has to be found in the text:

```json
"text": "⌊1:1⌋ Παῦλος δέσμιος Χριστοῦ Ἰησοῦ …",
"words": ["Παῦλος", "δέσμιος", "Χριστοῦ", "Ἰησοῦ", …]
```

Hebrew uses the same array with one more level, per the ruling in §6.4 — a compound word is an
array of its morphemes, a simple word is the string itself, and a gap is `null` (§6.3):

```json
"words": [["וַ", "יְהִ֗י"], ["בִּ", "ימֵי֙"], "שְׁפֹ֣ט", ["הַ", "שֹּׁפְטִ֔ים"], …]
```

Nothing is keyed and nothing is repeated: the word is the concatenation of its morphemes, its
number is its position, and Greek — which has no compounds — falls out of the same rule as a
flat array of strings.

**Measured, against the anchors it replaces:**

| | PHM 1:1-7 | RUT 1:1 |
|---|---|---|
| anchors in USJ (`usj + [ids]` over bare `usj`) | 8,581 | 2,585 |
| word array, surface forms only | **936** | 283 |
| word array, `{id, surface}` per entry | 4,039 | 1,243 |
| word array, nested by word with composed form | — | 1,832 |

Milestone text plus a surface-only array is **1,601** codepoints for PHM 1:1-7 against **9,910**
for the anchored document — the same information, 6.2× cheaper, and both halves are readable.

**Are the ids derivable from position?** For Greek, measured over whole books: **yes, without
exception.** A word id is `n` + book + chapter + verse + index-within-verse, and across all
11,286 words of Mark and 334 of Philemon **no verse departs from `001…n`**. So a Greek array
needs no ids at all — the verse comes from the milestone, the index from the array.

For Hebrew, two-thirds yes and one exception that matters:

- **morph numbering never breaks** — every one of 2,404 words in Ruth and Genesis 1–3 numbers
  its morphemes `1…k`, at most four
- **word numbering has gaps.** Nine verses in Ruth skip a word number — 1:8, 2:1, 3:3, 3:4,
  3:12, 3:14, 4:4, 4:5, 4:6 (3:3 and 3:14 skip two each). Genesis 1–3 has none, which is why a
  small sample would have missed it

**What the gaps are — measured, then inferred, and the line between them matters.** Measured:
Ruth 1:8 has no word 10 at any layer of Macula — not in `macula-hebrew.tsv`, not in the lowfat
XML, not in the TEI, whose own reference notation runs `RUT 1:8!9` then `RUT 1:8!11`. Word 9 is
אִמָּ֑הּ and word 11 is יַ֣עַשׂ. So the gap is in the source, not in our reading of it. Also
measured: **Macula marks ketiv/qere nowhere in its data** — a search of the corpus returns only
transliterations of קֶרֶב.

**Ruled by the Captain, 2026-09-10**, which settles what the files do not state: *"I think these
gaps ARE related to Ketiv, leaving room for the Ketiv reading if we were to support them in the
future. which seems unlikely now."*

So the gap is a **reserved slot**, not an error and not an omission — Macula presents the qere
and keeps the ketiv's number free against a support it does not currently offer. Two things
follow for the design. The gaps are **permanent and principled**, so `null` is the right
representation rather than a workaround for a data fault. And a future that does support ketiv
would **fill** those slots rather than renumber, so an array indexed by word number survives
that change; anything that renumbered to close the gaps would not.

**Compounds are not the cause.** They are the `<m>` morphemes inside a `<w>` — Ruth 1:8 word 1
is `וַ` + `תֹּ֤אמֶר` — and they never skip a word number; morph numbering is `1…k` without
exception across 2,404 words. Compounds cost the array its nesting, and nothing else.

So **Greek can derive; Hebrew must carry the word id** — or carry the gaps, which is the same
information more cleverly and less legibly. That is the honest version of "arrays and indexes",
and it is still far cheaper than anchoring every word.

**One complication, in two guises.** Both cases reduce to the same thing: **an id that exists in
the annotation space and has no text in the rendered document.**

- **the elided article** — RUT 1:1 carries a morphology entry keyed `o080010010071ה`, the
  definite article swallowed into בָּ, glossed "the", with no surface form. It is not among the
  `w` nodes, so it is unjoinable today and an array of surface forms has no slot for it either
- **the skipped word numbers** — the nine Ruth verses above

An array indexed by position cannot represent either without a way to say *"there is an entity
here with no text"*. That is `say-which-kind-of-nothing` applied to words.

### 6.3 Ruled: `null` for the gaps — and it removes the asymmetry

**The Captain, 2026-09-10: *"use null for gaps in Hebrew."***

The array carries `null` at a word number the text does not render. It is consistent with
`say-which-kind-of-nothing`: `[]` is the empty collection, and for a single slot `null` is "no
value here" rather than "not looked for".

The consequence is larger than the representation. **With the gaps filled, position means the
word number again — so Hebrew ids become derivable exactly as Greek's are.** Verified over the
whole book of Ruth: 1,306 slots, 11 of them `null`, and every rendered word's index equals its
word number.

| whole Ruth | codepoints |
|---|---|
| `usj + [ids]` — the anchored document | 179,383 |
| `milestones` text | 12,370 |
| word array carrying ids, `{t, m}` objects | 70,163 |
| word array, null-filled, no ids, `{t, m}` objects | 41,739 |
| word array, null-filled, no ids, **two-level arrays** (§6.4) | **19,971** |
| **text + array, as ruled** | **32,341** — 5.5× cheaper than anchored, same information |

Carrying ids instead of `null` would cost 70,163 against 19,971: **the ruling is 3.5× cheaper**
than the alternative it replaced.

So Q6's asymmetry sub-question is answered by the ruling rather than by a preference: **neither
language carries word ids in the array.** Greek derives them because its numbering is gapless
(11,286 words of Mark, no exception); Hebrew derives them because `null` restores the
correspondence. One rule, both languages, and the id is still exact wherever a payload needs to
name a word.

**Still open, and different in kind:** the elided article. `o080010010071ה` is not a *hole* in
the numbering — it is an *extra* id hanging off morph 1 of word 7, and its id is not derivable
from any position. The ruling does not reach it. The obvious extension is a morph slot carrying
`null`, but that is a proposal, not a reading of the ruling — Q6.

### 6.4 Ruled: two-level arrays — and a correction about what "compound" means

**The Captain, 2026-09-10: *"and for compound words, two level arrays, the full compound
containing an array of morphs."*** (`[]` throughout — no keyed objects.)

**And his correction, the same day, which this section had got wrong:** *"in hebrew, we have
compound words like beth-lehem, but each part of that compound is an orthographic word that can
have its own set of morphs. a compound word is not the same as a word composed of multiple
morphs."*

He is right, and the data has a name for it. **`<c>` in the lowfat XML.** Ruth 1:1, מִבֵּ֧ית־לֶ֣חֶם:

```
<wg class="pp">
  <m id="o080010010101" class="prep">מִ</m>          ← word 10, morpheme 1
  <wg class="np">
    <c class="noun">                                  ← the compound
      <m id="o080010010102" lemma="בֵּית לֶחֶם">בֵּ֧ית</m>   ← word 10, morpheme 2
      <m id="o080010010111" lemma="בֵּית לֶחֶם">לֶ֣חֶם</m>    ← word 11, morpheme 1
```

**So a compound is a grouping that cuts across word boundaries, and it is not the same shape as
morpheme composition:**

| grouping | example | relation to words |
|---|---|---|
| a word of several morphemes | `וַ` + `יְהִ֗י` = וַיְהִי | nests inside one word |
| a compound | `בֵּ֧ית` + `לֶ֣חֶם` | spans two words, and takes only morpheme 2 of the first |

Measured: Ruth has 7 compounds, every one two morphemes across two words, all Beth-lehem.
Genesis 1–20 has 14 — thirteen of two morphemes across two words, one of three across three,
mostly place names (Beth-El, Tubal-Cain, Ashteroth-Karnaim) — and **4 of the 14 take only part
of a word**, as Beth-lehem does.

**Which means one nested array cannot carry both groupings.** Words nest morphemes; compounds
overlap words. Two structures over one sequence of atoms, crossing rather than containing —
no arrangement of arrays inside arrays expresses that.

**What rescues it: the compound is already in the data we ship, without any structure.** Both
morphemes carry the same `lemma` and the same `strong` in our own USJ output today:

```json
{"marker":"w","content":["בֵּ֧ית"],"srcloc":"o080010010102","lemma":"בֵּית לֶחֶם","strong":"1035"}
{"marker":"w","content":["לֶ֣חֶם"],"srcloc":"o080010010111","lemma":"בֵּית לֶחֶם","strong":"1035"}
```

A consumer that wants compounds reads them off the shared lemma; nothing in the array has to
change. So the ruled shape stands, with the level correctly named — **the array's two levels are
word and morpheme, not word and compound** — and compounds are lexical annotation rather than
document structure. Whether that is enough, or you want compounds marked explicitly as standoff
spans, is Q9.

**And both levels are derivable from the ids themselves.** The Captain, 2026-09-10: *"the
orthographic words are derivable from the word ids — dropping the `p` part, which is the last
digit."* Measured, the layouts differ by language and the rule is Hebrew's:

| | layout | length | part digit |
|---|---|---|---|
| Hebrew | `o` BB CCC VVV WWW **P** | 13, uniform over 2,026 ids in Ruth | yes — the last digit |
| Greek | `n` BB CCC VVV WWW | 12, uniform over 11,286 ids in Mark | **none** |

Dropping the final digit of Ruth's 2,026 morpheme ids yields **1,295 orthographic words —
exactly the count of `<w>` elements in Macula's own TEI for Ruth**, which is the cross-check
that the rule is real rather than a coincidence of these samples. It is Hebrew's rule only:
applied to Greek it would merge 11,286 words into 1,503 groups, because Greek's last digit is
part of the word number and a Greek word has one morpheme.

So the array needs to carry nothing at all beyond the text: **the word number is the outer
index, the part is the inner index, and both reconstruct the id**. The single thing not
derivable is the compound, which crosses words — and that arrives already, in the shared lemma.

A word slot is one of three things, and nothing else:

| the slot | means |
|---|---|
| `"שְׁפֹ֣ט"` | a simple word, one morpheme |
| `["וַ", "יְהִ֗י"]` | a word written in several morphemes, in order, index = morpheme number |
| `null` | a word number the text does not render (§6.3) |

The composed word is the concatenation of its morphemes, so it is never stored twice, and Greek
— which has no compounds — produces a flat array of strings from the same rule.

**Measured against the alternatives**, whole Ruth: two-level arrays **19,971**; every word
wrapped in an array for uniformity 21,179; `{t, m}` objects 41,739. So the ruled shape is
**2.1× cheaper than objects**, and 6% cheaper than the uniform variant. The uniform variant's
only advantage is that a consumer never type-checks a slot; at 6% that trade is available if
you want it, and the ruling as given is the cheaper one.

### 6.5 The alternative the Captain raised: milestone text alone

> *"would milestones be equally good and maybe cheaper?"* — 2026-09-10

If a word id already encodes book, chapter, verse and position, and the milestone text already
marks the verses, then counting words inside a verse resolves any id, and **no array is needed
at all**. Measured, and the answer differs by language.

**Greek: yes, and it is free.** Across every verse of Mark and Philemon — 698 verses — the
whitespace-token count of the milestone text equals the word count exactly, **zero
mismatches**. `n57001004003` is the third token after `⌊1:4⌋`. The array adds nothing that the
text does not already carry.

**Hebrew: no.** 70 of Ruth's 85 verses mismatch, because **maqqef joins words into one token**:
Ruth 1:2 has 18 tokens and 20 words, with `שְׁנֵֽי־בָנָ֣יו`, `שְׂדֵי־מוֹאָ֖ב` and
`וַיִּֽהְיוּ־שָֽׁם׃` each written as one token. Nor can it be repaired by splitting on maqqef:
18 tokens plus 3 splits is 21, not 20, so at least one maqqef-joined pair is a single word in
Macula's numbering. Morphemes are sub-token in any case, and `null` gaps shift the count.

### 6.6 The two approaches, and where each wins

| | milestone text alone | text + word array |
|---|---|---|
| **Greek addressing** | exact, 698/698 verses | exact |
| **Hebrew addressing** | fails, 70/85 verses | exact |
| **cost, PHM 1:1-7** | **665** | 1,601 |
| **cost, whole Ruth** | 12,370 (but wrong) | 32,341 |
| **morpheme addressing** | impossible — sub-token | native, the inner array |
| **readable by a person** | yes, it is prose | prose plus a list beside it |
| **what a model sees** | one clean text | a text and a parallel structure to keep aligned |
| **derivation required** | the reader counts tokens | none — the index is the address |
| **fails silently?** | **yes** — counting is a rule nothing enforces, and Hebrew breaks it | no — a mismatch is visible in the data |

**The honest summary.** For Greek, milestone text alone is equally good and strictly cheaper —
the array is redundant, and 936 codepoints per pericope of redundancy. For Hebrew it does not
work at all. So the real choice is between **one rule for both languages** (always the array,
paying for it in Greek where it is not needed) and **a rule per language** (Greek uses the
text, Hebrew adds the array).

Two considerations that are not cost, and by the §1 ordering they outrank it. Counting tokens
is a **derivation the consumer performs**, and `declared-not-inferred` is against it: the rule
holds today across 698 verses, but nothing declares it, and the day a text normalises
punctuation differently the count moves and nothing goes red. The array states the answer
instead of requiring it to be re-derived. Against that, an array is **a second structure to
keep aligned with the text**, and a model reading both must trust that they agree.

That is the trade, and Q8 is where it gets settled.

**Three alternatives, kept for comparison** and all more expensive or less legible than the
array: the payload carries its own surface form per entry
(`design-annotation-without-anchors.md` option C, 4,039 for PHM against 936); the engine
resolves a word id on demand (nothing stored, but a call per lookup and no use to a model
reading the artifact); or the segment keeps an explicit id-to-surface map (the literal
equivalent of the array with ids, 4,039).

**Checked against what `build-book.yaml` actually reads.** It uses seven named fields —
`canonical_reference`, `source_text`, `segments`, `sequence`, `title`, `opening_verse`,
`closing_verse` — plus the whole object as `scene`. The shape above supplies all seven, with
`source_text` becoming a segment-level `text` (§9 proposes how build-book reads it).

## 7. What the engine must provide — proposals for this repository

**E1 — `include` valid with `milestones` and `plain`.** Without it §6 is unreachable: a segment
cannot carry both milestone text and Levinsohn features. This is
`design-annotation-without-anchors.md` decision 1, and this document is its use case.

**E2 — a public way to cut running text by a span.** Both consumers need "the text from word id
A to word id B" and "the text of verse range R". discourse-flow has written it six times
(`slice_usj_content` and five walkers) and their inventory §2.1 asks for it by name. Under §6
the cut is over *text*, which is far simpler than cutting USJ.

**E3 — fix `usj_to_text`.** It loses the chapter when the document has no `chapter` node,
emitting `⌊?:1⌋` although each verse node's `sid` carries `PHM 1:1`; and it joins word nodes
with spaces, detaching punctuation. Both are visible in §3. This is worth fixing whatever else
is decided, because it is the sanctioned way to do what ears-to-hear hand-rolled.

**E4 — how lexical data is grouped. The proposal that stood here was aimed at the wrong
quarter.**

*It read: "separate `lemma` and `strong` from `morphology`", on the grounds that they were a
third of a consumer's inflation. That figure came from discourse-flow's published file, where
the annotation container has been stripped and only the `w`-node attributes remain. In the
engine's own output they are a quarter, and the grammatical categories are three quarters. The
proposal was measuring the consumer's leftovers.*

**The Captain's constraints, 2026-09-10:** *"Lemmas are crucial for dictionary lookup, indexing
into ACAI, and other things we have not done yet. And morphology seems the best place for it.
Strong's numbers ... sigh ... one of those things a LOT of resources rely on, so we need them
to be available, though they have many weaknesses."*

So neither is going anywhere: lemma stays available, strong stays available. What remains is
where they sit. **Measured on whole-book Philemon**, baseline `usj + [ids]` = 30,627:

| family | delta | of which |
|---|---|---|
| `morphology` | +43,712 | categories **31,957 (73%)**, lemma 5,778 (13%), strong 5,961 (14%) |
| `senses` | +14,700 | 272 entries |
| `glosses` | +24,276 | 334 entries |
| `referents` | +6,560 | 102 entries |

The categories are the cost, and they are irreducibly per-word: 334 entries over ten fields
(`class`, `type`, `number`, `gender`, `case`, `role`, `person`, `tense`, `voice`, `mood`), with
10,690 codepoints of repeated field names against 12,571 of values, and **no field constant
throughout** — so nothing is removable without losing information.

**The Captain's own alternative, raised the same day and explicitly undecided:** *"we could
decide to separate them into a different include ... lexical? which would also include semantic
domains. not sure if that's better or just more complexity."*

What the numbers say about it. A consumer doing dictionary lookup or ACAI indexing wants lemma,
strong and domains, and today must ask for `morphology` + `senses` = **58,412**, of which
**31,957 — 55% — is grammatical categories it never reads**. A `lexical` family carrying
lemma + strong + senses costs roughly **26,439**, and `morphology` reduced to categories costs
31,957 instead of 43,712. So the split saves the lexical consumer 55% and the grammatical
consumer 27%; it is a real saving in both directions, not a rearrangement.

Against it: a third family name; `glosses` arguably belongs in `lexical` too, which makes it
four families rearranged rather than one added; and folding `senses` into `lexical` **renames a
shipped family**, which is a breaking change for the one consumer already using it. Under
`one-design` that is a migration with a stated end, not an alias.

This is Q10.

**E6 — the output forms people actually want, with our extension optional in all of them.**
Added at the Captain's direction, 2026-09-10. Three findings, all checked against the code:

- **`FORMATS = ("plain", "milestones", "usj")`** (`scripture.py:39`). There are three formats,
  not four.
- **`print` is documented and raises.** The shipped `docs/ai-context/sp/scripture-representations.md`
  costs four forms and lists `print` — *"paragraphs, no annotation … the editorial shape, for a
  reader rather than a model"*. `resource_text(..., fmt="print")` answers
  `ValueError: unknown format 'print'`. That document ships into every project by `sp init`, so
  every consumer has been told a format exists that errors. It is `docs/ai-context/`, so it is
  yours; reporting it, not touching it.
- **`usx` and `usfm` do not exist.** Both raise. USFM is the form most of the translation world
  edits, and USX its XML serialisation; a pipeline that wants to hand text to Paratext, or to a
  typesetter, has nothing to ask for.

What this proposes: `usx` and `usfm` as formats, `print` either built or removed from the
document, and — the part W2 turns on — **a request for a standard form returns a standard
document**. Our `scripture_pipelines` container is an extension; it should be opt-in, and where
a consumer asks for annotation alongside a standard form the payload travels *beside* the
document rather than inside it. That is the same shape E1 needs for `milestones`, which is why
these are one proposal and not two.

**E5 — decide whether the engine assembles the segment object at all.** §6 is a *pipeline*
output shape, not necessarily an engine one. The engine could supply only E1–E3 and let a
pipeline build it, or a step could return text-per-span directly. This is Q3 below.

## 8. Proposed changes to `nida-institute/discourse-flow` — **their repository, their call**

Recorded here so the design is complete and so the collab in Appendix A has something concrete
to point at. None of it is ours to do, and none of it is committed to.

**D1 — give each segment its text, in the form its consumers want.** Under E1, fetch
`format: milestones` with the families and put a `text` string on each segment. This is *not* a
proposal to stop producing USJ: their published USJ is conformant and someone may want it. It
is a proposal that the *default* deliverable carries readable text, and that a USJ artifact be
produced because a consumer asked for one rather than because `include` forced it. Their only
current consumer, `build-book.yaml`, converts it to milestones on arrival.

**D2 — stop pretty-printing the deliverable.** 118,830 codepoints, 47.7% of the file, is
indentation. `separators=(",", ":")` on the export.

**D3 — retire `milestone_content.py` and the five duplicate walkers** once E2 exists. Their own
inventory ranks this first.

**D4 — `genre_markers` on verse nodes.** 19 of 25 are empty, and they are their key inside a
document whose schema we own. Under §6 there is no USJ to put them in, so they need a home in
the segment object.

**D5 — a note on `_strip_levinsohn_features`.** They fetch six families, strip the container,
and publish the anchors. Under §6 the annotation they keep travels in the segment; the rest is
never serialised.

**Expected effect on the artifact:** the 259 KB file becomes roughly 85 KB — analysis fields
(~82 KB) plus ~2 KB of text and translation, without indentation — and contains running Greek.

## 9. Proposed changes to `nida-institute/ears-to-hear` — **their repository, their call**

**H1 — delete `usj_to_milestone_string`.** Under D1 there is nothing to convert; until then,
`usj_to_text(usj, fmt="milestones")` from `llmflow.utils.scripture` is the fix for §3 and is one
line. **This is the urgent one** — it is the difference between grounded and ungrounded output
on the next run.

**H2 — read text from segments.** `${pericope_section.source_text}` becomes the concatenation of
its segments' `text`, or the prompts move to segment level where they are already segment-shaped
(`staging`, `bodies`, `hearts` all take `segments:`).

**H3 — route what each prompt receives, rather than trimming it.** `scene:
"${pericope_section}"` ships up to 30,312 characters into ten prompts; most of it is discourse
evidence for boundaries the prompt is not being asked to reconsider. **Nothing here proposes
deleting a field** — the evidence stays in the artifact, where a reviewer needs it. The proposal
is that each prompt names the fields it reads, as `prompt.inputs` already lets it, so a step
analysing sensory detail is not also handed the boundary argument. That is a focus change first
and a cost change second: a model given 30,000 characters of which it needs 3,000 attends worse,
which is the Captain's stated ordering rather than an economy. Entirely theirs to decide.

**H4 — a guard.** A test that fails when `source_text` contains no letter of the source
language. §3 was silent for a month; a four-line assertion catches it in seconds.

## 10. Decisions — ruled 2026-09-10

**The Captain's text after each `=>` is his and is quoted verbatim, never reworded.** What
follows each is the consequence for the work, written by the AI. Two items are **reopened** by
evidence found after the ruling was given; they are marked, and the ruling stands until he
rules again.

**Q1. Is §6 the target shape?** Specifically: segment holds `text`, pericope holds no
`source_text`, milestone format, word ids retained on boundaries and features.

=> Yes.

**Ruled.** §6 is the target. `design-annotation-without-anchors.md` decision 1 is answered with
it — option A ("leave it") is dead, because §6 cannot be built while `include` requires `usj`.

**Q2. Does the engine ship E1 first, or all of E1–E4 together?** E1 alone unblocks §6; E3 is
independent and cheap; E4 is a payload change that touches every consumer.

=>  E1-E4 together.  Implemented in stages so they can use E1 first on my machine before the other stages are done, but the release includes E1-E4.

**Ruled, with one carve-out the AI proposed and which needs your yes or no.** One release
carrying E1–E4; staged so that consumers on this machine get E1 through the editable install
before the rest lands (`consumer-repo-conventions.md` — that is what makes staging work).

**The carve-out: E3 should ship ahead of the bundle.** Appendix B tells ears-to-hear to fix a
live defect by calling `usj_to_text`, and today that function emits `⌊?:1⌋` on a sliced
document. Bundling E3 hands another team a remedy we know is broken for as long as E1–E4 takes.
E3 is independent of the rest and touches no payload.

=>

**Q3. Does the engine assemble the segment object (E5), or only supply text-by-span?** The first
makes `pericope → segments → text` an engine concept; the second keeps it a pipeline's business
and the engine's surface smaller.

=>  Discuss. I assume if the engine doesn't do  it, multiple clients will have to, they will each do it differently, and all that code needs to be maintained. If we do it, there is a standard format, one well tested implentation, and less overall code to maintain.

**Ruled: the engine does it — and the evidence supports the assumption rather than merely
matching it.** discourse-flow has written this six times (`milestone_content.py` plus five
walkers, their inventory §2.1), and `discourse-flow-hebrew` will need all four operations
before it needs anything else. That is the "each does it differently" outcome, already happened.

**The boundary the AI proposes, and the one thing to settle:** the engine owns **text-by-span
and the word array**, because those need maqqef handling, morpheme numbering and the id scheme
— knowledge no consumer should re-derive. The consumer keeps **the vocabulary**: the engine
does not know what a pericope is, and should not learn. Concretely, a step takes a list of
spans (verse range or word-id pair) and returns text plus array per span; `pericope holds
segments` stays discourse-flow's naming, assembled in their pipeline from what we return.

This also keeps the return shape clear of `verses-are-milestones`: a list of spans, never a
mapping keyed by verse.

**Q4. Is the cost item (H3) in scope for us at all?** It is the largest number in this document
and it lives entirely in their prompts. We can say what we measured and stop, or we can propose
a shape for what a prompt receives.

=>  Yes, we are the expert advisors for sp.

**Ruled: in scope.** Which means H3 owes them a **concrete field-routing proposal per prompt**,
not the measurement alone — for each of the ten steps, which fields it reads and which it is
merely being handed. That is real work against their prompts and it belongs in the collab
(Appendix B), which currently raises the issue without proposing a shape.

**Q5. Do the two collabs in the appendices go out as drafted, and in what order?** The
ears-to-hear one carries a live defect; the discourse-flow one carries a redesign.

=>  And perhaps we should share this entire document with them too, with a pointer to it from the collabs?

**Ruled: share it — and the AI raises one problem with the pointer.** Under
`plans-are-temporary` this file dies on **2026-09-18**. A collab pointing at a path that
disappears in eight days is worse than one that points nowhere: the reader follows it, finds
nothing, and cannot tell whether the reasoning was withdrawn or merely tidied.

Proposed handling, needing your yes: the collabs stay **self-contained on the substance** so
they survive alone; rulings move to the **CHANGELOG** as they land, which is the durable home
and the one thing that outlives this file; and the document goes to them as a **snapshot,
marked as a working document with its expiry date on it**, rather than as a live reference.

=>

**Q6. What remains open on the word array.** Two rulings have already landed — `null` for gaps
(§6.3) and two-level arrays for compounds (§6.4) — and between them they answered the
Greek/Hebrew asymmetry, since neither language now carries ids. Three things they do not reach:

- **The elided article** — `o080010010071ה`, an *extra* id with no text rather than a hole. A
  `null` morph slot loses its id, which is not derivable. Extend the ruling, or model these
  separately from the words?
- **Does `include: [ids]` keep its name?** It would no longer write anchors into a document; it
  would return the array beside it.

=> **Answered 2026-09-10 via discourse-flow's reply, by the Captain: `null` in the morpheme
slot** — `[null, "בָּ…"]`, not an empty string and not omitted.

**Ruled, and the reasoning is better than the AI's proposal.** It gives `null` one reading at
both levels — *the text does not render this* — where a word-level `null` is a word number the
text does not render and a morpheme-level `null` is a morpheme it does not render. The property
it protects is the one §6.2 turns on: **index alignment survives, so the ids stay derivable from
position.** Omitting the morpheme would have broken exactly that and left the annotation with no
slot to attach to. The AI's suggested alternative — a slot carrying `null` *plus its own id* —
is unnecessary: with alignment intact the id is derivable like every other.  Yes.

**Ruled on the name: `include: [ids]` keeps it.** It becomes "give me word addressing", and
under §6 that is the array rather than anchors — one name, one meaning, no migration for a
consumer already asking for it.

**Reopened — the first bullet is unanswered.** The elided article `o080010010071ה` is an
*extra* id with no surface text, not a hole in the numbering, so a `null` slot cannot hold it:
`null` says "no word at this position" and carries no id, and this id is not derivable from
any position. Three shapes:

- a morph slot carrying `null` **plus its own id** — the single exception to "no ids in the
  array"
- a separate list of text-less entities beside the words
- leave it unrepresented, and accept that the morphology payload carries an id that joins to
  nothing (which is the status quo, and is what `check_include` refuses for other families)

=>

**Q7. Which output forms ship, and in what order?** E6: `usx`, `usfm`, and `print` either built
or struck from the shipped document that promises it. And the rule behind them — is
"a standard form returns a standard document, extension beside it rather than inside it" the
ruling, or should the container stay in USJ where a consumer has explicitly asked for both?

=>  We need all of these, but usx and usfm come first.

**Ruled: all of them, `usx` and `usfm` first.** Which leaves `print` documented and raising in
the meantime. `scripture-representations.md` costs it as one of four forms and ships into every
project through `sp init`, so every consumer has been told about a format that errors.

**The AI proposes striking that row now**, as a one-line change independent of building
anything — but the file is `docs/ai-context/`, which is yours, so this is a request and not an
action. Your call: strike it, or leave it and let `print` arrive later.

=>

**Q8. One rule for both languages, or one per language?** §6.6, and it is the question your
"would milestones be equally good and maybe cheaper?" opened. **For Greek, milestone text alone
addresses every word exactly** — 698 verses, zero mismatches — so always emitting an array
spends 936 codepoints per pericope on redundancy. **For Hebrew it fails on 70 of Ruth's 85
verses**, because maqqef joins words into one token and cannot be split back out. So: a uniform
shape a consumer writes once, or the cheaper split where Greek and Hebrew read differently?

Two things that bear on it and are not cost. Counting tokens is **a derivation the consumer
performs and nothing declares** — it holds across 698 verses today, and the day a text
normalises punctuation differently it moves, silently. And an array is **a second structure to
keep aligned**, which a model reading both must trust.

=> One rule for both languages. So people do not need to learn more than one idiom.

**Ruled: one rule.** Greek emits the array too, though its ids are derivable without it.

**And the cost objection largely dissolves on inspection.** The array appears only when a
consumer asks for `include: [ids]` — that is, only when it has asked for word addressing. A
pipeline that wants text asks for none and pays nothing. So the 936 codepoints per Philemon
pericope are not imposed on anyone; they are what a Greek consumer pays for the same idiom a
Hebrew consumer needs, and by the §1 ordering one idiom beats a saving.

**Q9. Are compounds adequately carried by the shared lemma?** §6.4. `בֵּ֧ית` and `לֶ֣חֶם` both
arrive with `lemma: "בֵּית לֶחֶם"` and `strong: 1035`, so a consumer can recover the compound
without any structural marking — and structural marking is not available anyway, because
compounds cross word boundaries and take partial words (4 of 14 in Genesis 1–20). The
alternative is a standoff list of morpheme spans beside the array. Is the lemma enough?

=> **Answered 2026-09-10 via discourse-flow's reply, by the Captain: no — compounds must be
identifiable, the representation is ours to choose, and detection is `unicode`.**

They took our own measurement as decisive — `unicode` at 53 of 53 against `lemma` at 11 of 53 —
and explicitly are not asking for lemma-based matching. **One constraint on the
representation:** the index remains the address, so a shape that collapses `בֵּית` and `לֶחֶם`
into a single slot is refused — it gives up alignment and collides with the morpheme nesting,
which already uses the inner array. So a compound is standoff, not a third level.

Still ours to design: what carries it. Emitting `unicode` per morpheme is the cheapest and is
what detection already relies on; a standoff list of morpheme spans is the alternative.  The lemma is enough.  Some compounds  may not even have Strong numbers.

**Half confirmed, half reopened — the ruling was given on an example that turns out to be
unrepresentative, and the AI supplied that example.**

**Your Strong's point is confirmed, and understated.** Across 53 compounds in Genesis and
Exodus, **not one carries `strongnumberx` on all its morphemes**. Zero of 53. Strong's cannot
identify a compound at all.

**The lemma cannot either, and Beth-lehem was the exception.** §6.4 showed both its morphemes
carrying `lemma: "בֵּית לֶחֶם"`. Measured across the same 53:

| join key | identifies the compound |
|---|---|
| identical `lemma` | **11 of 53 (21%)** |
| identical `lemma` ignoring whitespace | 16 of 53 (30%) |
| identical `unicode` | **53 of 53 (100%)** |

It fails two ways. Whitespace — `תּוּבַל קַיִן` against `תּוּבַלקַיִן` on the halves of
Tubal-Cain. And genuinely per-morpheme lemmas: Rehoboth-Ir carries `רְחֹבֹת עִיר` on the first
and plain `עִיר` on the second.

**And your later point — *"many words in Hebrew have multiple spellings, especially proper
nouns"* — is confirmed and separates two questions the AI had run together.**

| compound | occurrences | distinct `lemma` | distinct `unicode` |
|---|---|---|---|
| Beth-El | 13 | 2 — `בֵּית אֵל`, `בֵּיתְאֵל` | 7 |
| Beer-sheba | 11 | 3 — `בְּאֵר`, `ה`, `שֶׁבַע` | 6 |
| Paddan-Aram | 10 | 3 — `אֲרָם`, `ה`, `פַּדָּן` | 8 |

- **Marking a compound within one occurrence:** `unicode` is exact, 53 of 53. Inside a compound
  it holds the *whole compound's* surface rather than the morpheme's own, so the test is
  "adjacent morphemes in different words whose `unicode` matches and exceeds their own text".
- **Identifying the lexeme across occurrences:** neither works. `unicode` varies with maqqef,
  accents and directional forms (7 spellings of Beth-El); the lemma varies too, and sometimes
  is not the compound's lemma at all.

So the reopened question is narrower than the original: **do we emit `unicode` (or a derived
compound marker) so a compound is detectable at all?** Lemma alone leaves four in five
undetectable. Cross-occurrence identity is a separate problem and is not solved by any field we
currently ship — see Q10.

=>

**Q10. A `lexical` family — better, or just more complexity?** E4, and your own question. The
case for: a dictionary/ACAI consumer pays 58,412 today for Philemon and would pay ~26,439, with
55% of what it currently receives being grammar it never reads; a grammar consumer drops 27%.
The case against: a fourth family boundary to explain, `glosses` probably has to move too, and
absorbing `senses` renames a family discourse-flow already uses — a migration, not an alias.

Three shapes, if you want it:

- **`lexical` = lemma + strong + senses**, `morphology` = categories. Cleanest concept, breaks
  `senses`.
- **`lexical` = lemma + strong only**, `senses` unchanged. No rename, no breakage, but the name
  then promises more than it holds.
- **status quo** — lemma and strong stay in `morphology`, which is where you said they seem to
  belong, and a lexical consumer overpays.

=>  If we do lexical, it should be the first option.  Let's discuss, but my initial instinct is to add [lexical].

**Ruled provisionally: add `lexical` = lemma + strong + senses; `morphology` becomes the
grammatical categories.** Two things the AI would add before it is built.

**Keep `glosses` out.** It is 24,276 codepoints for Philemon — larger than `senses` at 14,700 —
so folding it in makes `lexical` heavier than `morphology` and recreates one level up exactly
the complaint that motivated the split.

**A risk to the family's stated purpose, from the Q9 measurements.** The reason given for
`lexical` is dictionary lookup and ACAI indexing. For Hebrew proper nouns the lemma is not a
reliable key: Beth-El carries two lemma spellings across 13 occurrences, and Beer-sheba's
morphemes carry `בְּאֵר`, `ה` and `שֶׁבַע` rather than the compound's lemma. So a `lexical`
family will serve Greek dictionary lookup well and will need **normalisation, or an entity id,
before it serves ACAI indexing of Hebrew proper nouns**. ACAI has its own entity identifiers;
joining on them is a different design and is not in this document.

That does not argue against `lexical` — it argues that "lemma is the dictionary key" is true of
Greek and only partly true of Hebrew, and the family should not be sold as more than it is.

**Migration.** Absorbing `senses` renames a shipped family that discourse-flow uses. Under
`one-design` that is one pass with a loud failure and a named end, not an alias.

=>

## 11. Not in scope

Whether `include` keeps its name; how `ids` is spelled after E1; the Hebrew sources WLC does not
register (`discourse: null`, `syntax: null` — measured in the workbench); the repository rename.

---

# Appendix A — draft collab to `nida-institute/discourse-flow`

**Status: drafted by the AI, pending the Captain's review. Not sent.**
Destination: `collab/sp/2026-09-__-pericopes-hold-segments-and-segments-hold-text.md` in their
repository, or ours by their convention.

> # The text you publish, and the shape we think it should have
>
> **From:** an AI session in `nida-institute/LLMFlow`, at the Captain's direction.
>
> We measured `output/book-discourse/57-PHM-discourse.json` and then designed against it. Three
> things, of which only the first needs anything from you soon.
>
> **1. Your `source_text` is unreadable downstream, and part of that is ours.** `include:`
> forces `format: usj`, so the only way to have Levinsohn features is the word-object document.
> You then strip the annotation container and publish the shell: 43,938 codepoints carrying
> 1,942 characters of Greek. We are designing `include` to work with `milestones`
> (`design-annotation-without-anchors.md`), which removes the reason the shell exists.
>
> **2. Two things in the file are cheap to fix and are yours.** Indentation is 118,830
> codepoints — 47.7% of the file. And `genre_markers` appears on verse nodes, 19 of 25 empty; it
> is your key inside a USJ document, and under the shape below there is no USJ to put it in.
>
> **3. The shape we propose:** a pericope holds segments, and each segment holds its own text,
> with word ids kept on the boundaries and inside `levinsohn_features`. Your segments already
> carry `opening_word_id`/`closing_word_id`; what they lack is the text. We think that is the
> whole change on your side, plus dropping the pericope-level `source_text`, which is the
> concatenation of its segments' anyway.
>
> **To be clear about what we are not saying:** we are not proposing you stop producing USJ.
> What you publish today is conformant, extension-free USJ, and someone may well want it — we
> are adding `usx` and `usfm` as formats for exactly that reason. The proposal is that the
> default deliverable carries text a person and a model can read, and that a USJ artifact exists
> because a consumer asked for one rather than because `include:` forced it.
>
> **What replaces the anchors.** An anchored document can locate *any* word; a milestone string
> cannot. The proposal is that each segment carries its words as an ordered array beside the
> text, so the index is the address — measured at 1,601 codepoints for Philemon 1:1-7 against
> 9,910 for the anchored document, with nothing lost. Greek needs no ids in it: we checked all
> 11,286 words of Mark and every id is `n` + book + chapter + verse + position, without
> exception. Hebrew nests morphemes inside a word and does need the word id, because the word
> numbering has gaps — nine verses in Ruth, absent from every layer of Macula rather than from
> our reading of it. We think those are ketiv/qere with only the qere presented, but Macula
> marks neither anywhere in its data, so we would value your confirmation.
>
> Two cases we would want your view on, since you hit them before we will: a morpheme with no
> surface form (the article elided into בָּ, which has an annotation and no text), and whether
> the nested Hebrew shape matches how you would want to read it.
>
> **We are writing to ears-to-hear at the same time, and telling them the same thing.** They
> consume your output in `build-book.yaml`, so a change to your published shape is a change to
> their inputs; both of you should hear it from us at once rather than one of you discovering
> it. Their note also carries a defect of their own that this uncovered — their converter
> silently drops every word of your anchored USJ, so their next run would analyse punctuation.
> That is theirs to fix and they are being told directly; we mention it here only so you are
> not surprised to hear the two notes are related.
>
> What we would need from you: whether segment-level text is right for how you actually work,
> whether anything downstream of you reads the USJ we are proposing to remove, and your answer
> on word locatability. Nothing here is a request to change anything today — the engine change
> comes first.

# Appendix B — draft collab to `nida-institute/ears-to-hear`

**Status: drafted by the AI, pending the Captain's review. Not sent.**
Destination: `collab/sp/2026-09-__-source-text-is-punctuation.md`.

> # `build-book` will feed punctuation to every LLM step on its next run
>
> **From:** an AI session in `nida-institute/LLMFlow`, at the Captain's direction.
> **This one is urgent and the fix is one line.**
>
> `plugins/load_discourse.py:14`, `usj_to_milestone_string`, keeps only the bare strings in each
> `para`. discourse-flow now publishes anchored USJ, where the words are `char`/`w` nodes and
> the bare strings are the punctuation. Run through your own `extract_pericopes` against the
> current `57-PHM-discourse.json`:
>
> ```
> Philemon 1:1-7    51 chars   ⌊1:2⌋ ’ · ⌊1:3⌋ . ⌊1:4⌋ , ⌊1:5⌋ , ⌊1:6⌋ · ⌊1:7⌋ , ,
> Philemon 1:8-16   94 chars   ⌊1:8⌋ , , ⌊1:9⌋ , ⌊1:10⌋ , , ⌊1:11⌋ , ⌊1:12⌋ , ’ · …
> ```
>
> That is `${pericope_section.source_text}` for ten gpt-4.1 steps per pericope.
>
> **Both files the current discourse-flow pipeline produces do this** — Mark and Philemon, its
> 9 September output, zero Greek letters from either. Older files in that directory still
> convert, but they were written by an earlier version of the pipeline and regenerating them
> will not reproduce that.
>
> **Nothing of yours is damaged yet.** Every saved outline under `outputs/` is 30 July to
> 16 August and still carries its Greek. The damage arrives with the next run.
>
> **The fix:** `from llmflow.utils.scripture import usj_to_text`, then
> `usj_to_text(doc, fmt="milestones")`. It recovers all 672 characters of that pericope. Two
> caveats we are fixing on our side: on a sliced document with no `chapter` node it currently
> emits `⌊?:1⌋`, and it detaches punctuation with a space.
>
> **Worth adding either way:** a test that fails when `source_text` carries no letter of the
> source language. This was silent for a month.
>
> **The shape you consume is going to change, and we are telling discourse-flow so in a
> separate note.** You should know before you fix anything, because it decides how much to
> invest in the fix.
>
> What is coming: a pericope will hold **segments, and each segment will hold its own text** as
> a milestone string. The pericope-level `source_text` you parse today — the USJ document —
> goes away, because a pericope's text is the concatenation of its segments'. Word addressing
> survives as an ordered array beside the text rather than as `srcloc` anchors inside it.
> Nothing is lost; everything moves.
>
> **So `usj_to_text` is the right fix today and an interim one.** Do it anyway — your next run
> is ungrounded without it, and the change above needs an engine release first. But do not
> build anything larger on the USJ shape, because it is on its way out.
>
> **What we want from you, and it is the reason we are writing before rather than after.**
> `build-book.yaml` reads seven named fields off a pericope — `canonical_reference`,
> `source_text`, `segments`, `sequence`, `title`, `opening_verse`, `closing_verse` — plus the
> whole object as `scene`. We have designed the new shape to supply all seven. If that list is
> wrong, or if something else in the object is load-bearing for you, say so now: you are the
> consumer, and the shape should be settled with you in the room rather than handed to you.
> We will send you the working design document alongside this note.
>
> Separately, and not urgent: `scene: "${pericope_section}"` ships up to 30,312 characters into
> most of your prompts, against 1,942 characters of Greek in the whole book, and the discourse
> evidence fields are most of it. We raise it as a **focus** question rather than a cost one —
> a step analysing sensory detail is also being handed the argument for where the pericope
> starts. Naming the fields each prompt reads in `prompt.inputs` keeps every one of them in the
> artifact for your reviewers while putting only the relevant ones in front of the model. Yours
> to decide; we mention it because we had the numbers in front of us.
