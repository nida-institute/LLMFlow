# Design: Scripture Representations

Epic: [#200](https://github.com/nida-institute/LLMFlow/issues/200). Guidance standard: [#208](https://github.com/nida-institute/LLMFlow/issues/208).
Predecessor: `design-scripture-editions.md`, which exists only on the local tag `wip/scripture-200`.

**Status:** sources and precedence ruled; representation shape ruled; the schema shape and several
inherited decisions are open. Measurements below were taken 2026-08-22 against the data on this
machine and are reproducible.

---

## 1. Problem

One edition is held in several serialisations, and no single one is convenient for every purpose.
A project that picks one inherits that serialisation's shape — which is how three consumer repos
each arrived at a per-verse container, the form `docs/ai-context/rules.md` rule 12 forbids.

The engine's job is therefore not to forward a file. It is to serve a named edition in the
representation a step actually needs, and to keep those representations joinable.

---

## 2. The serialisations

Verified against `~/github/Clear/macula-greek/SBLGNT`, `~/github/Clear/macula-hebrew/WLC`,
`~/github/Logos/SBLGNT` and `~/github/usfm-bible/examples.bsb`.

| | Macula `tsv` | Macula `lowfat` | Macula `tei` | SBLGNT (LogosBible) |
|---|---|---|---|---|
| word id | `xml:id` (`n41001001001`), `ref` (`MRK 1:1!1`) | same | — | **none** — bare `<w>` |
| inter-word material | `after` column | `@after` | significant whitespace | `<suffix>` |
| morphology, lemma, Strong's | 27 columns | **all of it** | — | — |
| senses / domains | `domain`, `ln`; Hebrew `lexdomain`, `contextualdomain`, `coredomain`, `sdbh` | same | — | — |
| participant reference | `frame`, `subjref`, `referent` | same | — | — |
| syntax tree | no | **`wg` groups** — in Mark: 4,009 `cl`, 2,421 `np`, 789 `pp`, 29 `vp` | no | no |
| paragraphs | no | no | no | **`<p>`** — 86 in Mark |
| text variants | no | no | no | **apparatus**, 540+ variation units vs WH / Treg / NA28 / RP |
| disputed-text brackets | 0 occurrences | — | — | **`⟦ ⟧`** |
| already in textual order | **yes** | **no** — §6.1 | yes | yes |

**Lowfat is a content superset of the TSV.** It carries the text, `after`, `ref`, `xml:id` and the
full morphology *and* the tree. The TSV's advantage is convenience: flat, and already in textual
order. The Captain's word for this was "convenient", and that is the accurate one — an earlier
draft of this document claimed a content boundary between them, which the data does not support.

**`tei` is referenced by none of `ears-to-hear`, `discourse-flow` or `discourse-flow-hebrew`** —
zero files in all three.

**Apparatus source:** `Logos/SBLGNT/data/sblgntapp/xml/`, 27 books, CC BY 4.0, v1.2 (2023-07-10,
which added John 7:53–8:11). Structure is flat: `<verse>Mark 1:1</verse>` followed by `<note>`
elements. Mark has 507 verse markers and 930 notes. A note reads

    1:1 χριστοῦ WH ] + υἱοῦ θεοῦ Treg NA28; υἱοῦ τοῦ θεοῦ RP

— SBLGNT's reading and the editions agreeing, then `]`, then competing readings with sigla;
`+` addition, `–` omission, `;` between variants, `•` between units within a verse.

---

## 3. Identity and alignment

`xml:id` and `ref` are the spine, and `ref` carries a word index (`MRK 1:1!1`). All `@ref` values
parse cleanly across Matthew, Mark and John — 0 unparsed of 45,240 words.

**The spine survives into a synthesised representation.** `discourse-flow`'s
`plugins/milestone_content.py` emits `srcloc` on each word element, so USJ built from Macula
morphology stays joinable to lowfat, the lexicons and the entity data.

**SBLGNT (LogosBible) has no word ids**, so joining its apparatus and paragraphs to Macula identity
is positional. It is verifiable only where both agree on word count per verse; both include
`MRK 16:9-20` and `JHN 7:53-8:11`, and both count 11,286 words in Mark, so the sequences do
correspond. An alignment that cannot be verified for a given verse must fail rather than guess.

**Precedence (Captain, 2026-08-22): Macula Greek's text rules, even where SBLGNT (LogosBible)
carries a variant reading.** The apparatus is information *about* the text, never a competing text
to use. This needs stating in any guidance an LLM reads: handed both, a model could easily treat a
variant as an alternative reading to adopt.

---

## 4. What reaches the model

Measured on `discourse-flow/input/annotated/41-MRK-annotated-usj.json`, the whole of Mark:

| representation | chars | × milestone |
|---|---|---|
| raw Greek text, no markers | 69,413 | 0.93× |
| milestone string `⌊ch:v⌋` | 74,283 | 1.00× |
| USJ, bare structure, no ids | 316,744 | 4.26× |
| USJ + `srcloc` word ids | 421,192 | 5.67× |
| USJ + discourse-flow annotations, as shipped | 874,925 | 11.78× |
| full morphology, a "tokens" view | 3,179,674 | 42.80× |

Two readings matter. The milestone form costs **7%** over bare text — the markers are nearly free.
And the USJ container costs **4.26× before any metadata**, with metadata then the larger cost again:
one repo's verse-level annotations take 421k to 875k.

**Ruled (Captain, 2026-08-22): both representations, produced per pipeline according to need.**

### 4.1 Choosing one — guidance that needs no measurement

> **If the model's output must reference individual words, the input must carry word identity.**
> Annotating, aligning or pointing at words needs `usj` with `srcloc`. A judgment, prose, or a
> segmentation expressed in verse references needs only `milestones`, at a fourteenth of the size.

A step that asks a model for word-level output from a representation carrying no word ids cannot
be satisfied; the model will invent ids. That is detectable from the pipeline before any spend.

### 4.2 One direction only

**Derive the milestone form from USJ, never the reverse.** USJ → milestone keeps the text and drops
ids; milestone → USJ cannot invent ids or paragraphs. Two independently produced representations
can drift; a derived one cannot.

---

## 5. Prior art — reference, not baseline

Per the Captain's instruction, `ears-to-hear` and `discourse-flow` are consulted as evidence.

| | ears-to-hear | discourse-flow |
|---|---|---|
| form sent to the model | `⌊ch:v⌋` markers in a running-text string | USJ 3.1 object, verse markers as inline milestones |
| word identity | none | `srcloc` on each word element |
| built from | verse text plus markers (`book_scene_text.py:280,354`) | Macula morphology, `text` + `after` (`milestone_content.py`) |
| paragraphs | n/a | one `para` per chapter, explicitly unsourced (their §5.1) |
| specification | convention living in code | 453-line ratified design doc, 14 numbered decisions |

`⌊ ⌋` appears in **30** files in `ears-to-hear`, **1** in `discourse-flow` (a design document
describing the ears-to-hear form), and **0** in `discourse-flow-hebrew`. The engine's parked
`utils/scripture.py` implements the ears-to-hear answer — `MILESTONE_TEMPLATE`,
`FORMATS = ("plain", "milestones")`.

### 5.1 Which of discourse-flow's decisions survive multiple sources

Their decisions are settled and working *there*. They were settled against one source.

| their decision | under multiple sources |
|---|---|
| §5.4 addressing by Macula word ids | **fails** — SBLGNT (LogosBible) and BSB USFM have no word ids |
| §5.1 paragraph unit: none, one `para` per chapter | **fails** — SBLGNT (LogosBible) has `<p>` (86 in Mark) and BSB USFM has paragraphs plus `\s1` headings |
| §5.7 inter-word material: the `after` field | principle holds, field name does not — `after`, `<suffix>`, or already in the text |
| §5.9 chain validation on word ids | conditional on ids existing |
| §5.5 markers at verse start only | holds |
| §5.11 chunk shape: USJ pieces | holds |
| §5.13 slice-and-wrap primitive | holds |
| §5.2, §5.3 window sizing physical, unit not paragraphs | hold, though §5.3's reasoning partly rested on paragraphs not being real |

Their §5.6, §5.8, §5.10 and §5.14 are that repo's housekeeping, not engine design.

---

## 6. Traps measured

### 6.1 Lowfat is not in document order

Words are reordered to display grammatical structure, so document traversal is not textual order.

| book | words | out-of-order transitions | verses affected |
|---|---|---|---|
| Mark | 11,286 | 334 | 268 of 673 (~40%) |
| John | 15,625 | 642 | 480 |
| Matthew | 18,329 | 840 | 632 |

Backward jumps are overwhelmingly one word position — 270 of Mark's 334 — so it presents as
adjacent transposition, which in Greek is not obvious to a reader skimming output. Sorting on the
`!n` index in `@ref` recovers textual order.

This is the shape of the `window` cursor defect fixed in `c1647af`: naive use is correct in the
majority of verses, so it survives casual testing. It belongs in the step documentation as a stated
failure mode — see #208.

### 6.2 Locale collation merges apparatus markers

`sort` and `uniq` under a UTF-8 locale treat `⸀`, `⸂` and `⸁` as equivalent. Counting or deduping
them requires `LC_ALL=C`, or distinct variation-unit types silently merge. Observed while counting
markers in Mark: a UTF-8 locale reported one marker type where there are five.

### 6.3 `format: usj` is specified and unimplemented

`FORMATS = ("plain", "milestones")` in the parked `utils/scripture.py`, and the schema `enum`
matches, while `design-scripture-editions.md` specifies three formats including `usj`.

---

## 7. Rulings

| ruling | date |
|---|---|
| Local assets are primary; MCP is a fallback, never the default path | 2026-08-17 |
| Staging: text representations first, then tokens, syntax, senses, entities | 2026-08-17 |
| Running text for WLC and SBLGNT comes from the TSV (`text` + `after`) | 2026-08-17 |
| BSB source is `usfm-bible/examples.bsb` | 2026-08-17 |
| Sources are the Captain's; an assistant does not substitute one on its own judgement | 2026-08-17 |
| `format: usj` for TSV editions is synthesised from the TSV — verses and text, no structure | 2026-08-22 |
| Macula Greek's text rules, even where SBLGNT (LogosBible) carries a variant reading | 2026-08-22 |
| Nestle1904 out of scope; HOT is BHS and WLC, minimal diffs, the only two in widespread use | 2026-08-22 |
| Both representations, produced per pipeline according to need | 2026-08-22 |
| Two knobs, not one: `format:` for the shape, **`include:`** for what rides along | 2026-08-23 |

### 7.1 Purpose → representation (Captain, 2026-08-22)

| purpose | representation |
|---|---|
| running text | Macula TSV, `text` + `after` |
| USJ | synthesised from the TSV |
| morphology | Macula TSV — "usually most convenient" |
| syntax | Lowfat — "often in BaseX where it can be queried easily" |
| text variants, other editions | SBLGNT (LogosBible) apparatus — "extremely helpful" |

---

## 8. Questions for the Captain

Answer inline after each `=>`.

### Q1. One knob or two?

`format:` alone, or structure (`milestones` | `usj`) and metadata (`none` | `ids` |
`ids+annotations`) as separate keys?

- **One knob** makes invalid states unrepresentable and gives one thing to document — but the cost
  ladder in §4 has four points, so the enum either drops annotations or becomes `usj`, `usj-ids`,
  `usj-annotated`, which encodes two dimensions in one string and the linter cannot reason about
  the parts.
- **Two knobs** match the cost structure, since payload dominates container, and make the two lint
  checks separable: metadata nothing reads is a warning, word ids requested from a representation
  without them is an error. The objection — that two knobs create meaningless pairings, which is
  what an LLM writes — is answerable with the `allOf` / `"if": {"properties": {"type": …}}` pattern
  `pipeline_schema.py` already uses per step type, so an invalid pairing fails `sp lint`.

=>

**Ruled (Captain, 2026-08-23): two knobs — B. The second parameter is `include`.**

On the name: `carry:` and `include:` were the finalists. He chose `include`, with the reason —
*"context disambiguates it from, say, an include file."* Considered and rejected: `with:` (reads
as step arguments to anyone arriving from GitHub Actions), `layers:` (already means analytical
layers in discourse-flow), `detail:`/`level:` (a scalar ladder, which stops working once
`senses` and `syntax` become independently selectable), `annotations:` (wrong for word ids,
which are identity rather than annotation).

Note `include_partial` is an existing key on the `window` step with an unrelated meaning. The two
are one underscore apart in the same namespace; that was raised and accepted.

So the step reads:

```yaml
- name: fetch_source
  type: scripture
  edition: SBLGNT
  passage: "${passage}"
  format: usj            # milestones | plain | usj
  include: [ids]         # valid only when format: usj
  outputs: source_text
```

Still to settle before implementation: whether `include` takes a list or a single word, and the
exact member names. The cost ladder measured `ids` and `ids+annotations`; #200's format table
implies `senses`, `syntax`, `entities` and `tokens` follow later, which argues for a list.

### Q2. Does the apparatus get its own step type?

Or become a representation the `scripture` step serves? It is the only named source with no access
path today.

=>

### Q3. The default form when a pipeline does not say

§4.1 gives a test an author can apply, but a default is still needed. Deciding it well depends on
which form a model handles better, which is not measurable from the repository — it wants the same
passage and task in both forms, with the Captain judging the outputs.

=>

### Q4. Where does paragraph structure come from?

`discourse-flow` synthesises one `para` per chapter because Macula has none. SBLGNT (LogosBible)
and BSB USFM both carry real paragraphs. The same passage would gain different structure depending
on which source served it, unless something rules otherwise.

=>

---

## 9. Out of scope

- The guidance standard for step documentation, and single-sourcing the two language references — #208.
- BaseX collection naming, where #38 (semantic, `macula/gnt-lowfat`) and #52 (provenance,
  `github/<org>/<repo>/<path>`) propose different schemes and both call theirs canonical.
- `tokens`, `syntax`, `senses`, `entities` as served representations — later stages of #200.
- Versification across editions — #203. Dataset versions and catalog validation — #201.
- Migrating consumer repos off their own loaders.
