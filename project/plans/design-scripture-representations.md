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

### 4.3 The JSON representation — where the extra fields live

Checked against the USFM Technical Committee source, `usfm-bible/tcdocs` at `2fde7302`
("Merge branch '3.1.2'"). Not against BridgeConn's `usfm-grammar`, which carries a copy whose
own `$id` points back at tcdocs.

**Three of the annotations we want are spec attributes, and the rest have no spec home.**
`\w` — a `char` element with `marker: "w"` — takes exactly three:

```
grammar/usfm.ext:1325    \marker w
                         \attributes lemma? srcloc? strong?
                         \defattrib lemma
grammar/usx.rnc:965      usfm:propattribs="lemma? strong? srcloc?"
```

So `srcloc` is **not** a custom field. discourse-flow's use of it for the Macula `xml:id` is the
spec's own attribute used as intended. Same for `lemma` and `strong`. Every other marker's
attribute list is likewise a closed enumeration — `\rb` takes `gloss`, `\fig` takes
`src size ref alt? loc? copy?`, `\qt` takes `who?`.

**There is no general custom-attribute mechanism.** No `x-` convention, no namespacing, nothing
matching "custom attribute" or "user-defined" anywhere in `usx.rnc`, `usfm.ext` or `usfm_sb.sty`.

**The USJ schema does permit extra keys.** `grammar/usj.js` is 86 lines of draft-07 and declares
`additionalProperties` nowhere, which defaults it to `true`. `markerObject` requires only `type`;
the document requires `type`, `version`, `content`. A marker object carrying extra keys validates.

So the split is one the spec drew, not one we chose:

| | spec home | survives USJ → USX → USFM |
|---|---|---|
| `ids` | `srcloc` on `\w` | **yes** |
| lemma, Strong's | `lemma`, `strong` | **yes** |
| the parse — `morph`, case, tense, voice, mood | none | no |
| senses, domains — `domain`, `ln`, `sdbh` | none | no |
| glosses | `gloss`, but only on `\rb` | no |
| referents — `frame`, `subjref` | none | no |

**Ruled (Captain, 2026-08-23): one container, `scripture_pipelines`, holding all our extensions
as children.** Spec attributes stay in their spec places; everything else goes in the container.

```json
{
  "type": "char", "marker": "w",
  "srcloc": "n41001001001", "lemma": "ἀρχή", "strong": "746",
  "content": ["Ἀρχὴ"],
  "scripture_pipelines": {
    "morph": "N-NSF",
    "domain": "033005"
  }
}
```

*Why a container rather than flat keys:* it is strippable in one operation rather than by a
field-by-field allowlist, and it can never be mistaken for spec content by a later reader or tool.
The counter-example is on this machine — discourse-flow puts `levinsohn_features` and
`genre_markers` as flat keys on verse elements, which works and cannot be stripped without knowing
every name in advance.

*Why underscores.* The Captain's name for it is "scripture pipelines". The key is spelled
`scripture_pipelines` because `get_from_context` matches each dotted part against
`^([a-zA-Z0-9_]+)` (`utils/context.py:148`), so a space or hyphen ends the match early **and
returns a sentinel object rather than raising**. Measured:

```
${w.scripture pipelines.morph}    -> <object object>   silent miss
${w.scripture-pipelines.morph}    -> <object object>   silent miss
${w['scripture pipelines'].morph} -> 'N-NSF'           works
${w.scripture_pipelines.morph}    -> 'N-NSF'           works
```

The form a pipeline author would naturally type is the one that fails, and it fails without an
error — the defect class #208 exists for.

*On "never serialized".* Nothing round-trips this to USX or USFM, so no standards question arises.
It *is* written to disk as JSON by `saveas`, intermediate files and checkpoints — as
discourse-flow's `input/annotated/*-annotated-usj.json` already are — so the container is durable
on disk and will be read back by later steps and by people. Design it to be read.

### 4.4 `include` members

**Ruled (Captain, 2026-08-23): families, not columns.** Five members. Fine-grained members
(`lemma`, `strong`, `case`) would make `include` a column picker, which is what the TSV already is;
families keep the list short enough to document and coarse enough that an author picks by intent.

| member | Greek columns | Hebrew columns | lands in |
|---|---|---|---|
| `ids` | `xml:id` | `xml:id` | `srcloc` — **spec attribute** |
| `morphology` | `lemma`, `strong` | `lemma`, `strongnumberx`, `stronglemma` | `lemma`, `strong` — **spec attributes** |
| | `morph`, `normalized`, `person`, `number`, `gender`, `case`, `tense`, `voice`, `mood`, `degree`, `role`, `class`, `type` | `morph`, `pos`, `stem`, `state`, `person`, `gender`, `number`, `lang`, `type` | container |
| `senses` | `domain`, `ln` | `lexdomain`, `contextualdomain`, `coredomain`, `sdbh`, `sensenumber` | container |
| `glosses` | `gloss`, `english`, `mandarin` | `gloss`, `english`, `mandarin` | container |
| `referents` | `frame`, `subjref`, `referent` | `frame`, `subjref`, `participantref` | container |
| `discourse` | Levinsohn LGNTDF, 33 feature types | — | container |

**A sixth member, ruled in conversation 2026-08-25: `discourse`.** `nida-institute/discourse-flow`
named this as one of two things blocking adoption — Levinsohn's 33 LGNTDF discourse feature types
are merged into their USJ by `plugins/milestone_content.py:183` and are derivable from none of the
other five families. They asked for either a sixth family or permission to add a key to the
container, and said either would unblock them. The ruling is the sixth family, and its name is
**`discourse`**. Greek only today; Hebrew has no counterpart source.

**Textual variants, ruled the same day: list them, do not align them.** Their second blocker was
that Levinsohn's word indices are NA28-family while the text is SBLGNT, so where SBL chose
differently the index silently names a different word — every one of Mark's 147 mismatching
citations falls in a verse the apparatus flags. The ruling is to **list the variants from the
Logos SBLGNT apparatus**, not to build an alignment or mint ids for words in one edition and not
the other. That is the narrow version they said would unblock them: per verse, what the other
witness reads. Scoping it as an alignment problem was the alternative and is not being taken.

`morphology` deliberately straddles both homes: `lemma` and `strong` are spec attributes on `\w`
and go where the spec puts them, while the parse has no spec home and goes in the container. A
caller asking for `morphology` gets both without having to know which is which.

`glosses` is separate from `senses` because a Louw-Nida domain, an SDBH sense and an English gloss
are not interchangeable — a step doing lexical work may want the domain and not the gloss.

**The Greek/Hebrew asymmetry — proposed, not ruled.** One member name means different fields per
edition: `include: [senses]` yields `{domain, ln}` on SBLGNT and
`{lexdomain, contextualdomain, coredomain, sdbh, sensenumber}` on WLC.

Proposal: **the member name is stable across editions; the fields inside carry the source's own
column names, unnormalised, and the difference is documented per edition.** Normalising would mean
inventing an equivalence — Hebrew's three domain kinds do not collapse into one Greek `domain` —
and rule 25 puts that judgement in the Captain's domain, not an assistant's. A caller that needs
one shape across both languages can map it; a caller handed a normalised shape cannot recover what
was lost.

=>

*Ruled in conversation, 2026-08-25: **"this is inherent to the data"**, and **"the two cannot be
unified without solving the merged ontology problem, a known hard problem in computer science."**
So the proposal stands — unnormalised, each source keeping its own column names.*

*That second sentence is the one to quote when normalising is proposed again, and it will be.
Louw-Nida and SDBH are separate lexical ontologies; mapping one onto the other is ontology
merging, not a field rename, and it is unsolved in general rather than merely unfinished here. An
engine that emitted a shared key would be publishing an answer to it on every payload. The
asymmetry is not friction to be smoothed — it is what the sources say, and the engine is not
entitled to discard it.*

*Ruled in conversation, 2026-08-25: **"yes, identify the source."** The payload names the lexical
source explicitly rather than leaving a caller to infer it from which keys came back:*

```yaml
senses:
  source: sdbh          # or: louw-nida
  fields: {lexdomain: …, contextualdomain: …, coredomain: …, sdbh: …, sensenumber: …}
```

*This settles what the asymmetry ruling deliberately left alone. Unnormalised fields say what each
project says; a declared `source` says which project is speaking. A consumer can branch on a value
the payload states instead of sniffing key names — and a consumer that meets an unfamiliar source
knows it has met one, rather than silently finding fields missing.*

### 4.5 What `include` does not carry

The **Lowfat syntax tree** (`wg` groups — 4,009 clauses in Mark) and **paragraph structure** are
not `include` members. Neither is a field on a word: USJ has nowhere to put a constituency tree,
and paragraphs change the `para` elements themselves rather than annotating anything inside them.
Both are shape, not payload — which is what #200's format table implied by listing `tokens`,
`syntax`, `senses` and `entities` as *formats*.

Where they go is unsettled. `format: syntax` is the obvious guess and is not a decision.

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
| `include:` takes a **list** | 2026-08-23 |
| Extensions live in one container, **`scripture_pipelines`**; spec attributes stay in their spec places | 2026-08-23 |
| `include` members are **families, not columns**: `ids`, `morphology`, `senses`, `glosses`, `referents` | 2026-08-23 |

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

**Closed 2026-08-25.** The two things this left hanging are both settled, so the question carries
no outstanding decision:

- **`include` takes a list.** Every example here, both consumer replies, and discourse-flow's
  request that families cost a word of YAML each all require it; a single word cannot express
  `include: [senses, glosses]`.
- **The member names are settled** — `ids`, `morphology`, `senses`, `glosses`, `referents`, and
  `discourse` as of today (§4.4).

**One hazard this question recorded and accepted, repeated here so it is not rediscovered as an
oversight:** `include_partial` is an existing key on the `window` step with an unrelated meaning.
Two keys one underscore apart in the same namespace, raised at the time and accepted.

### Q2. Does the apparatus get its own step type?

Or become a representation the `scripture` step serves? It is the only named source with no access
path today.

=>

**Ruled in conversation, 2026-08-25: no separate step type. The variants come with the text.**
The Captain's framing, and it is the reason: *"I'm thinking of this like a critical edition with
tc notes, where it does belong with the text"*, and then — *"after all, they are footnotes in
SBLGNT."*

*That second sentence settles the mechanism as well as the placement. They are not a second
document to be joined to the first; they are part of the edition, and **USJ already has a home for
them**: a footnote is a `note` element anchored at a position in the text. So they need no new
container key, no sibling step type, and no invention — `format: usj` can carry them where the
spec already puts a note.*

*An earlier draft of this section argued for a separate step type, on the grounds that every
`include` member decorates a word while a variant attaches to a place in a verse. That objection
was a programmer's taxonomy applied to a scholarly object organised the other way for two
centuries: a critical edition is text and apparatus in one artifact. Recorded because the same
argument will occur to the next reader.*

*Consequences worth stating before implementation:*

- *`format: plain` and `format: milestones` carry no notes. A caller asking for running text gets
  running text; a footnote is not part of it.*
- *Still to settle: whether a caller opts in with `include: [variants]` or receives them with the
  edition. They are the edition's own footnotes, which argues for the latter; the ruling that
  defaults stay lean argues for the former. Opting in is the safer default and can be relaxed.*
**How a note corresponds to the text — measured 2026-08-25, and it is tighter than assumed.**

*An earlier revision of this section said the Logos files are "verse-keyed prose, not
word-addressed", repeating `nida-institute/discourse-flow`'s characterisation without testing it,
and concluded that their need for word-addressable variants stays unmet. Both were wrong.*

*Each note carries its own anchor, and the anchor is the printed text of the edition — the words
before the `]`, with the supporting sigla between them and the bracket:*

```
<verse>Mark 1:2</verse>
<note>2 Καθὼς WH Treg NA28 ] Ὡς RP </note>
<note>• τῷ Ἠσαΐᾳ τῷ προφήτῃ WH Treg NA28 ] τοῖς προφήταις RP </note>
```

*Matching those anchors against the SBLGNT token stream for their verse, normalising Greek and
ignoring elision apostrophes: **889 of Mark's 930 notes — 95.6% — resolve to a contiguous token
span.** 315 of the anchors (34%) are multi-word, which is what a footnote attaches to in any case.*

*The 41 that did not resolve are not unanchorable. They use two apparatus conventions the probe did
not implement, both of which are more precise than plain matching:*

- ***`…`** marks a discontinuous span — `αὐτὸν … σάββασιν παραπορεύεσθαι` is a range whose middle
  is elided.*
- ***`⸀` and `⸁`** disambiguate a repeated word — Mark 3:8 carries `⸀καὶ` and `⸁καὶ`, the apparatus
  itself resolving which occurrence is meant.*

*So attaching a note needs no alignment machinery and no minted ids: the anchor is in the note.
That largely meets what discourse-flow ranked as blocking — "per verse, the words NA28 has that
SBLGNT does not, in order, addressable" — because the words after `+` attach at a resolved span, in
document order.*

***Superseded the same day, and lemma matching turns out to be the fallback rather than the
method.*** *This section twice recorded that addressing a variant's own words was out of reach
without minting ids. Measured afterwards: **the printed edition's apparatus reference marks are
already in the Macula TEI**, as `pc` nodes at exact positions — `⸀` 607, `⸂` 314, `⸃` 205, `⸁` 8,
`⸄` 1 in Mark. Pairing them with the apparatus notes:*

| | |
|---|---|
| verses with marks in the TEI | **507** |
| verses with notes in the apparatus | **507 — the same verses** |
| verses where the counts agree | **506 of 507 (99.8%)** |
| marks / notes | 931 / 930 |

*So the join is **ordinal**: walk a verse's marks in document order, walk its notes in order, pair
them. Each mark sits between `<w>` elements carrying `xml:id`, so an entry lands at an exact word
position by construction — which is what `nida-institute/discourse-flow` ranked as blocking:
"per verse, the words NA28 has that SBLGNT does not, in order, addressable."*

*Recorded as a correction rather than edited away, because the wrong claim was made twice and a
reader may have acted on it.*

*Re-derivation: the probe reads `Logos/SBLGNT/data/sblgntapp/xml/Mark.xml` against
`macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv`, strips a leading verse number or `•`, treats any
Latin-script token as a siglum, and looks for the remaining Greek words as a contiguous run in the
verse.*

### Q3. The default form when a pipeline does not say

§4.1 gives a test an author can apply, but a default is still needed. Deciding it well depends on
which form a model handles better, which is not measurable from the repository — it wants the same
passage and task in both forms, with the Captain judging the outputs.

=>

**Ruled in conversation, 2026-08-25: *"text with milestones as a default."*** A pipeline that omits
`format:` gets `milestones`, and `usj` is never reachable by omission.

*Two things settled this without the experiment the question asks for. `nida-institute/discourse-flow`
ruled that defaults stay lean — "defaults should not make it as bloated as possible" — with the
reasoning that generalises: a payload nobody asked for is a payload nobody checked. And the cost
ladder is now corroborated from outside this repository: `nida-institute/ears-to-hear` independently
measured milestones at **1.072x** bare text, against USJ's 2.56x in codepoints and **6.74x** as
escaped JSON, which is how it travels to a model. Forgetting the key now costs 7% rather than 574%.*

*It is also the form all three hand-rolled builders already produce, so the default is what every
consumer was building for itself.*

***The experiment is not cancelled, and it is not a blocker.*** *Which form a model handles better
decides what we **recommend**, not what happens when a key is absent. Tying the default to it would
have blocked implementation on a run costing money and the Captain's time.*

### Q4. Where does paragraph structure come from?

`discourse-flow` synthesises one `para` per chapter because Macula has none. SBLGNT (LogosBible)
and BSB USFM both carry real paragraphs. The same passage would gain different structure depending
on which source served it, unless something rules otherwise.

=>

**Ruled in conversation, 2026-08-25: *"you can't have paragraph structure in this USJ."***

*This is a fact about the data rather than a preference, and it dissolves the question's premise.
The paragraphs the question points at live in a **different serialization** — SBLGNT's source XML
and BSB's USFM. The `scripture` step reads Macula, which carries none, so the USJ it builds has
nothing to carry. The inconsistency the question was written to guard against cannot arise: there
is no source-dependent paragraphing, because there is one source and it has no paragraphs.*

*So the emitted USJ carries **one `para` per chapter**, as a container the USX grammar requires and
nothing more. `nida-institute/discourse-flow` arrived at the same shape from the other direction —
they built paragraph sourcing from the SBLGNT source XML, 1,307 paragraphs across 27 books,
ratified it, then reversed it and deleted the plugin, and their design now reads "Do not
reintroduce paragraph sourcing." Their reason is theirs and stands on its own: paragraph and verse
divisions are editorial artifacts and must not drive structural analysis.*

**And paragraphs are available — as a different `format:`, not as an `include` member.** Ruled in
the same conversation: *"you can also get the print edition with paragraph structure if that's what
you want — a different format request. it returns the tei or closest formatted version we have."*

*This stays inside the design's own logic. Q1 ruled `format:` to be the **shape** knob and
`include:` the **payload** knob; §4.5 says paragraphs are shape rather than payload. So a caller
who wants the print edition asks for a different shape, and the two knobs keep their meanings.*

*What we have, measured 2026-08-25 — `macula-greek/SBLGNT/tei/02-mark.xml`:*

| | |
|---|---|
| `<p>` paragraph elements in Mark | **91** |
| `<w>` elements | **11,286** — the same token count as the TSV |
| word addressing | `xml:id="n41001001001"`, `ref="MRK 1:1!1"` |
| verse addressing | `<milestone unit="verse" ref="MRK 1:1"/>` |

*So the print serialization carries paragraphs, the same word set, and both kinds of address. It is
a real alternative rather than a lossy one.*

***"But you can't mix the two."** Confirmed 2026-08-25: the print shape and the analytical shape
are **alternatives**. Annotation families do not layer onto the print format; a caller gets one or
the other. This extends what Q1 already ruled — that `include` is valid only with `format: usj` —
to a general principle: `include` applies to the analytical shape alone.*

***Note that this is a design choice, not a data limitation**, and the distinction should not be
lost. The TEI carries the same 11,286 tokens with both `xml:id` and per-word `ref`, so layering
annotation onto it would be technically possible. It is ruled out because a caller who has asked
for the print edition has asked for editorial structure, and a payload that is both editorial and
analytical invites exactly the inference the paragraph ruling exists to prevent — reading
structural meaning out of an editor's paragraphing. `sp lint` should therefore reject `include`
with the print format as an error rather than a warning: it is a category confusion, not an
unsatisfiable request.*

***Named 2026-08-25: `format: print`.*** *It names what the caller wants, like every other member
of the enum — `plain`, `milestones`, `usj` — rather than the serialization it happens to be served
from. That matters here because the serialization is not fixed: the ruling was "the tei **or
closest formatted version we have**", so the format is a promise about shape and the source behind
it may differ per edition.*

***Two serializations, not one, and they are not the same thing.*** *Corrected in the same
conversation: **the Logos SBLGNT is not TEI.** The file measured above is Macula's TEI at
`macula-greek/SBLGNT/tei/`; the Logos SBLGNT is a separate serialization, and it is the one whose
apparatus files §Q2 reads. Q4's original text — "SBLGNT (LogosBible) and BSB USFM both carry real
paragraphs" — names Logos, not the TEI, so at least three formatted sources are in play. Which one
`format: print` serves per edition is a per-edition fact for the catalogue, not a single answer.*

*§4.5 said "where they go is unsettled". For this step, they do not go anywhere, and that section
should be read in light of this ruling.*

---

## 9. Out of scope

- The guidance standard for step documentation, and single-sourcing the two language references — #208.
- BaseX collection naming, where #38 (semantic, `macula/gnt-lowfat`) and #52 (provenance,
  `github/<org>/<repo>/<path>`) propose different schemes and both call theirs canonical.
- `tokens`, `syntax`, `senses`, `entities` as served representations — later stages of #200.
- Versification across editions — #203. Dataset versions and catalog validation — #201.
- Migrating consumer repos off their own loaders.
