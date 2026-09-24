# Shipped documentation for the new text and addressing model

**Status:** proposed (2026-09-10) — **drafts for review, nothing installed.** Part A is a new
shipped document as it would read; Part B is the set of replacement passages for an existing
one. Both describe behaviour ruled in `design-pericope-segments-and-text.md` §10 and **not yet
built**, so neither ships until E1–E4 land. Per `plans-are-temporary` this file dies once the
text is in the templates.
**Issue:** #200.
**Where these go, if approved:**

| draft | template to edit | rendered as |
|---|---|---|
| Part A | `src/llmflow/templates/project/docs/ai-context/sp/word-addressing.md` (new, needs a `data/file-catalog.yaml` entry) | `docs/ai-context/sp/word-addressing.md` |
| Part B | `src/llmflow/templates/project/docs/ai-context/sp/scripture-representations.md` | `docs/ai-context/sp/scripture-representations.md` |

**Never edit the rendered copies.** They are `policy: generated, source: template`, and an edit
there is lost on the next `sp init`.

**Two things are deliberately absent from both drafts**, because they are not settled: how a
compound is *identified* in the payload (Q9, reopened) and whether the annotation container may
sit inside a standard USJ document (Q7's second half, unanswered). Where a draft needs them it
says so in a bracketed note rather than inventing an answer.

Vocabulary check applied throughout: these ship to every project, so they teach **spans**, not
pericopes. No project's naming appears in either draft.

---

# Part A — new document: `word-addressing.md`

> Draft. This is the text as it would ship.

## Finding a word in a passage

Annotation is keyed by word: a sense, a morphological analysis, a discourse feature all say
*"this applies to word `n57001004003`"*. To use any of it you need to know which word that is.

This document is about how the engine answers that, and why it answers it the way it does.

## The short version

Ask for text in whatever form suits you. Add `include: [ids]` and you also get **the words of
that passage as an ordered array**, beside the text rather than inside it.

```yaml
- name: passage
  type: scripture
  resource: SBLGNT
  passage: "PHM 1:1-7"
  format: milestones
  include: [ids, senses]
```

```
text:  "⌊1:1⌋ Παῦλος δέσμιος Χριστοῦ Ἰησοῦ καὶ Τιμόθεος ὁ ἀδελφὸς Φιλήμονι …"
words: ["Παῦλος", "δέσμιος", "Χριστοῦ", "Ἰησοῦ", "καὶ", "Τιμόθεος", …]
```

**The index is the address.** Word `n57001004003` is the third entry among that verse's words.
Nothing has to be searched for, and the text stays text — a person can read it, a model can
quote it, and neither has to reassemble a sentence from fragments.

## Why not put the addresses in the text

The alternative is to mark every word in the document itself, which is what USJ's `srcloc`
attribute is for. It works, and it is expensive in a way that compounds:

| Philemon 1:1–7 | codepoints |
|---|---|
| `plain` | 623 |
| `milestones` | 665 |
| `usj`, no annotation | 1,329 |
| `usj` with every word marked | 9,910 |
| `milestones` + the word array | 1,601 |

Marking the words costs more than the annotation it exists to serve: on that passage the
markers add 8,581 codepoints, while the entire sense payload adds 4,805. The reason is that
marking a word turns it into an object, so 622 characters of Greek prose arrive as 107 word
objects separated by 106 punctuation strings, with no running text anywhere in the document.

The array carries the same information for a sixth of the cost, and leaves the prose intact.

## Greek: an array of words

One word, one entry, in document order.

```json
["Παῦλος", "δέσμιος", "Χριστοῦ", "Ἰησοῦ", "καὶ"]
```

A Greek word id is `n` + book + chapter + verse + position-within-verse, so the entry's
position and the verse it falls in reconstruct the id exactly.

## Hebrew: the same array, one level deeper

A Hebrew word is often written in several morphemes, and the annotation is per morpheme. So an
entry is either a word written as one morpheme, or the array of its morphemes:

```json
[["וַ", "יְהִ֗י"], ["בִּ", "ימֵי֙"], "שְׁפֹ֣ט", ["הַ", "שֹּׁפְטִ֔ים"]]
```

Ruth 1:1 begins with וַיְהִי — the conjunction וַ and the verb יְהִי, two morphemes carrying
separate glosses, separate lemmas and separate morphological analyses. The word is the
concatenation of its morphemes and is never stored twice.

A Hebrew word id is `o` + book + chapter + verse + word + **part**, the part being the final
digit. Dropping it gives the orthographic word — which is the outer index — and the part itself
is the inner index.

## `null` — a word number the text does not render

Some word numbers have no word:

```json
[…, "אִמָּ֑הּ", null, "יַ֣עַשׂ", …]
```

This is not a fault in the data and not a gap to be closed. Where a Hebrew text has both a
written form and a read form, the source presents the read form and **leaves the written form's
number free**, against support that may come later. The slot is reserved, not missing.

Which is why the array carries `null` rather than skipping the position: keeping the slot keeps
every following index correct, so the word number and the array index stay the same thing. Nine
verses of Ruth have such a slot, eleven in total; most chapters have none.

An empty array `[]` and a `null` mean different things here as everywhere in this engine: `[]`
is a lookup that ran and found nothing, `null` is a slot with nothing in it.

## Three things that are easy to conflate

| | what it is | in the array |
|---|---|---|
| morpheme | the unit annotation attaches to | an entry, or a member of an entry |
| orthographic word | what is written between spaces, minus joining marks | an entry |
| compound | a lexical unit spanning more than one orthographic word — a place name like בֵּית־לֶחֶם | **not a level** |

A compound is not a bigger word. `בֵּית` is the second morpheme of one word and `לֶחֶם` is the
first morpheme of the next, so the compound covers part of one word and part of another. Word
boundaries and compound boundaries cross rather than nest, which is why the array has two
levels and not three: it carries the writing, and the compound is a fact about the lexicon.

*[Pending Q9: this section will say how a compound is identified in the payload once that is
ruled. Do not ship Part A with this note in it.]*

## One idiom for both languages

Greek could do without the array — its numbering has no gaps and its words are single
morphemes, so counting words in a verse would find any of them. It gets the array anyway, so
that a person or a program learning this learns it once. The same three cases — a string, an
array of morphemes, `null` — describe both languages; Greek simply never produces the second
and third.

The array appears only when you ask for `include: [ids]`. A step that wants text asks for none
and pays nothing.

## Reading a payload against the array

Every per-word family is keyed by the same ids the array reconstructs:

```
senses:  {"n57001001001": {"domain": "093001", "ln": "93.294a"}}
words:   ["Παῦλος", …]
```

`n57001001001` is book 57, chapter 1, verse 1, word 1 — the first entry among verse 1's words,
which is Παῦλος. For Hebrew, `o080010010012` is word 1, part 2 of Ruth 1:1: the second member
of the first entry, יְהִ֗י.

---

# Part B — replacement passages for `scripture-representations.md`

> Each block below replaces a passage in the existing template. Everything not listed stays as
> it is.

## B1 — replaces the cost table under "What each form costs"

**Reason:** `include` no longer requires `usj` (E1), two forms are added (E6), and the
multipliers were measured on one book at one moment. Re-measure before shipping; the figures
below are Philemon 1:1–7 and are marked as such rather than presented as universal.

> ## What each form costs
>
> Measured on Philemon 1:1–7, **with the unit stated** — the same text is 623 codepoints as
> `plain`, 1,238 UTF-8 bytes and 3,180 as escaped JSON. A reader who assumes bytes and gets
> escaped JSON mis-costs every decision downstream, and for Greek and Hebrew the escaping alone
> is roughly five times the codepoint count.
>
> | form | cost | choose it when |
> |---|---|---|
> | `plain` | baseline | the prompt never cites a verse |
> | `milestones` | **1.07×** | **the default.** A verse reference is all the addressing most work needs |
> | `usj` | 2.13× | you need the document structure — paragraphs, characters, the markup itself |
> | `usx` | *(pending E6)* | the XML serialisation, for tools that read USX |
> | `usfm` | *(pending E6)* | the form most of the translation world edits |
>
> **Annotation is independent of the form.** `include:` works with any of them: the payload
> travels beside the text under one key, not inside it. Asking for senses does not commit you
> to a marked-up document.
>
> **Asking for a family you do not read is still pure cost** — `include` defaults to empty
> deliberately, because a payload nobody asked for is a payload nobody checked.

## B2 — deletes the `print` row

**Reason:** `FORMATS = ("plain", "milestones", "usj")`. `resource_text(..., fmt="print")`
raises `unknown format 'print'`. The document has promised a format that errors, in every
project it ships to.

This is true **today** and does not wait for E1–E4. It is the one change in this file that
should land immediately.

The catalog's `purpose:` for this document also names `print` and needs the same edit:

> Choosing between `plain`, `milestones`, `usj`, `usx` and `usfm`, what each costs with the
> unit stated, and how to read a discourse item's `outcome`.

## B3 — replaces "Which families are built"

**Reason:** the family list changes if `lexical` is added (Q10, provisionally ruled), and the
`ids` entry no longer describes anchors.

> | family | what it carries |
> |---|---|
> | `ids` | the words of the passage as an ordered array — see `word-addressing.md` |
> | `morphology` | the resource's own grammatical categories |
> | `lexical` | lemma, Strong's number, and the resource's sense system — Louw-Nida on Greek, SDBH on Hebrew |
> | `glosses` | the resource's gloss columns |
> | `referents` | the resource's referent columns |
> | `discourse` | Levinsohn's features, each with the `outcome` field described below |
> | `syntax` | the constituency tree, standoff — one entry per sentence |
>
> A family emits whichever of its declared columns the resource actually has, and nothing
> merges the two systems: a Greek verb has `tense`, `voice` and `mood`; a Hebrew verb has
> `stem` and `state`. Field names are the source's column names verbatim.

*[If Q10 lands as `lexical` = lemma + strong + senses, the `senses` row goes and this table is
correct as written. If it lands narrower, `senses` stays and `lexical` describes less.]*

## B4 — adds a short section after the container section

**Reason:** E6's rule, and the reason `include` can now accompany any form.

> ## The annotation never sits inside a standard document
>
> A request for a standard form returns a standard document. Everything `include` delivers
> travels beside it, under `scripture_pipelines` — one key to find, one key to drop, and
> nothing for a USJ or USX consumer to strip before handing the document to a tool that
> expects the specification and nothing else.
>
> This is why choosing annotation no longer chooses a text form.

*[Pending Q7's second half: if the container may sit inside USJ when a consumer explicitly asks
for both, this section needs the exception stated. Do not ship it as absolute until that is
ruled.]*

## B5 — the one rule that is not a trade-off

**Reason:** unchanged in substance, but the reference to a USJ document is now one option among
several. Suggested wording change only:

> **Verses are milestones, not containers.** The step returns running text with `⌊1:1⌋`
> markers, or a document in one of the markup forms. It never returns a mapping keyed by verse,
> and analysis must not restructure it into one: chopping text at verse boundaries destroys the
> sentence and clause structure the analysis depends on.

---

# What still has to happen in the language reference

`docs/llmflow-language.md` carries the *syntax* of `type: scripture` and is not AI context. The
same change adds `usx` and `usfm` to the format list, adds `lexical` to the family list, and
removes the sentence saying `include:` is valid only with `format: usj`. If the grammar and
this guidance disagree, the grammar is what `sp lint` enforces and the guidance is what a
reader believes — so they land together or not at all.
