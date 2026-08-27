# Plan — the `type: scripture` step, specified for implementation (#200)

**Status:** Proposed, 2026-08-26. **Targeted at the next release** (ruled 2026-08-26). Nothing
built beyond what is parked on the `wip/scripture-200` tag. **Awaiting review of this document as a
whole before code** (rule `plans-first`) — it was amended in place across a long session, and
section-by-section agreement is not the same as approving the plan.
**Issue:** #200.
**Design authority:** `project/plans/design-scripture-representations.md`. All six of its `=>` slots
are ruled, five on 2026-08-25 and the sixth the same day; further rulings on 2026-08-26 added the
`discourse` and `syntax` families, `format: print`, versification, and the whole-clause rule at
passage boundaries. This document decides nothing; it states the contract those rulings imply in
enough detail to write tests against.

**Scope note.** §5 is ordered simple-to-complex and each step ships green, so the release can cut at
any completed step rather than waiting for step 11. What "this feature" means for the release is
therefore a choice of how far down §5 to go, not all-or-nothing.

---

## 1. What this step is for

A pipeline says which edition, which passage, and what shape it wants. The engine reads the
edition and returns the text in that shape. Today four scripture-acquisition paths exist across two
consumer repositories, in two serializations of the same edition, with **three hand-written
milestone builders that disagree with each other** — measured: `nida-institute/ears-to-hear`'s two
implementations differ on all 131 Mark pericopes. Collapsing that is the point of the step; the
cost figures are a secondary argument.

---

## 2. The contract

```yaml
- name: fetch_source
  type: scripture
  edition: SBLGNT              # a registered edition
  passage: "${passage}"
  format: milestones           # plain | milestones | usj | print   (default: milestones)
  include: [senses, glosses]   # valid only with format: usj
  outputs: source_text
```

**`format:` is the shape knob, `include:` the payload knob** (Q1). Each names what the caller
wants, never the serialization it is served from.

| format | returns | notes |
|---|---|---|
| `plain` | running text, no addressing | the cheapest form; whole-book steps that cannot window read this |
| `milestones` | `⌊c:v⌋ text` | **the default.** 1.072x bare text, measured independently by a consumer |
| `usj` | USJ structure | 2.56x codepoints, 6.74x as escaped JSON. Annotation only via `include` |
| `print` | the print edition, with paragraph structure | served from a formatted serialization; **not annotatable** |

=> Need to mention our internal extensions to usj, in our own space.

**The `scripture_pipelines` container.** Everything `include` delivers, and everything the payload
says about itself, lives under one key that the USJ specification does not define and will never
define. Nothing is added anywhere else in the document.

| in the container | from |
|---|---|
| the `include` families that have no spec home — `morphology`'s parse, `senses`, `glosses`, `referents`, `discourse`, `syntax` | §3.0a, §3.5 |
| `versification` — the scheme the verse references are in | §3.-1 |
| the extent actually covered, when a whole clause overran the requested passage | §3.0a |

*Spec-defined fields stay where the spec puts them: `lemma` and `strong` are attributes on `\w`,
`ids` becomes `srcloc`. The container holds only what USJ has no place for — which is why a
consumer can ignore it entirely and still read valid USJ.*

*Two things follow, and both matter to a consumer more than to us. **One key to strip**: a consumer
wanting standard USJ removes `scripture_pipelines` and is done. And **one place to look**: an
extension outside that key would be an extension nobody could find, which is how
`genre_markers` — a non-standard attribute on `verse` nodes, 53 of them in Mark — came to sit
loose in a consumer's USJ and be dropped silently by its own flattener.*



**`include` members** — seven: `ids`, `morphology`, `senses`, `glosses`, `referents`, `discourse`
(§3.0a), `syntax` (§3.0a). A list, never a single word. Defaults to empty — `format: usj` with no
`include` returns the text in USJ structure with no annotation, because a payload nobody asked for
is a payload nobody checked.

**`versification:`** — names the scheme of the result (§3.-1). Implicit from the primary source when
one edition is named; required when two are to be compared. **Not a closed enum**, because a
Paratext project brings its own.

=> if no members are included, it should at least return the text, no?

*Yes — the wording was the defect, not the design. `format: usj` with no `include` returns **the
text, in USJ structure, with no annotation**: book, chapter, `para` and `verse` nodes and the words
themselves. "Structure and nothing more" read as though the text were withheld, which would be
absurd. Corrected here and at §5 step 2.*

---

## 3. What each format must do, and why it is not obvious

### 3.-2 `passage:` accepts ranges, and emitted milestones carry `sid` and `eid`

**Ruled 2026-08-26: "ranges are essential, and they are specified in USFM/USX/USJ 3.x."** So a
passage is not restricted to chapter:verse — a span addressed by word id is expressible, and the
mechanism is the standard's paired milestones rather than anything we invent.

*This answers a ranked ask from `nida-institute/discourse-flow` that an earlier revision of this
plan recorded as unaddressed: verse ranges are not safe slicing keys there, because boundaries fall
inside verses, so they key intermediates by word-id span.*

**Both ends are emitted, not just the start.** Ruled the same day: *"a lot of downstream apps use
the `eid` because they aren't good at parsing."* An end milestone is derivable — it is wherever the
next start appears — but deriving it is work we can do once instead of every consumer doing it,
badly, forever.

*`eid` is redundant, and that is the point — it is emitted **because** it is derivable, so nothing
downstream has to derive it. The same principle as the nested syntax tree (§3.0a): the payload states
what it could leave to be inferred, because inference is where a weak parser and a language model
both fail silently. Measured in the wild: the annotated USJ one consumer builds carries **689 `sid`
and no `eid`** in Mark, so every reader of it infers ends today.*

**USJ and USX are the form a span is expressed in. USFM is read, not modelled.** Ruled the same day:
*"usj / usx is the real solution here, usfm is an inferior serialization."* A span in USJ or USX is
attributes on structured nodes, unambiguous without marker semantics; the USFM equivalent is
positional markup that needs a bespoke parser and is exactly what weak parsers get wrong.

*So `print_format: usfm` stays — many Paratext projects are USFM on disk and reading them is
useful — but nothing in the design is shaped around its constraints, and the internal model is USJ.
`utils/data.py` already converts with `_usx_to_usj`, so this costs nothing.*

### 3.-1 `passage:` is meaningless without a versification scheme — #203

**This section was absent from the first draft of this plan and from
`design-scripture-representations.md`.** It was recovered from `0bb1d5b`, a commit reachable only
through the `wip/scripture-200` tag, whose ten lines of `project/TODO.md` carry the one requirement
neither document states: *"Editions must declare their scheme; `type: scripture` must map before
fetching."* Today's `TODO.md` condensed that entry and the requirement did not survive the
condensation.

**The defect it names, in this step's own terms.** `passage: "PSA 51:1"` against WLC and against
BSB returns text **two verses apart**, and the step reports success. Verified against the
Copenhagen Alliance mappings:

| | |
|---|---|
| `PSA 51:1-19` in `eng` | → `PSA 51:3-21` in `org` |
| `PSA 51:0` (superscription) | → `PSA 51:2` |
| `MAL 4:1-6` in `eng` | → `MAL 3:19-24` — Malachi has 4 chapters in English, **3 in Hebrew** |

So a reference is not a location until a scheme is named. Any pipeline pairing an
original-language text with a translation of "the same" reference is silently comparing unrelated
verses — which is also the mechanism under the pairing question in §6.

**What we use, ruled 2026-08-26: the Copenhagen Alliance versification specification.**
Cloned at `~/github/copenhagen-alliance/versification-specification`; rule 12 already names it as
canonical for cross-versification work and records that Paratext `.vrs` files are semantically
compatible. The data is declarative and needs no interpretation layer:

| field | what it gives |
|---|---|
| `maxVerses` | book → per-chapter verse counts, so an out-of-range reference is detectable |
| `mappedVerses` | `"PSA 51:1-19"` → `"PSA 51:3-21"`; 265 entries in `eng` |
| `excludedVerses` | references that do not exist in that scheme (empty in `eng` and `org`) |
| `partialVerses` | verses split across a boundary |

Standard schemes shipped: **`org`, `eng`, `lxx`, `vul`, `rsc`, `rso`**, plus a custom Ethiopian
mapping. `org` is the hub: every scheme maps to and from the original-language versification.

**What this adds to the contract.** Each registered edition declares its scheme, and the step maps
before fetching rather than after. An unmappable reference is an error, never an empty result —
the parked code already holds that line for out-of-range passages
(`test_a_passage_outside_the_edition_errors_rather_than_returning_empty`), and this extends it.

=> Approved.

**Ruled in conversation, 2026-08-26:**

> *"if you ask for two editions to use in parallel, you have to specify the versification you want
> to use in the result if you want them to match up. or if you ask for the Hebrew 'with BSB', you
> get the Hebrew versification, whatever the primary source is for the USJ. we need both explicit
> controls and sensible implicit defaults."*

*So the scheme of the **result** is the thing under control, and it is governed by the **primary
source** unless the pipeline says otherwise:*

| case | scheme of the result |
|---|---|
| one edition | that edition's own — implicit, and needs no key |
| a primary edition with a companion translation | **the primary's**, whatever it is |
| two editions to be compared or aligned | **must be stated**, or they will not line up |

*This corrects a mischaracterisation in the previous revision of this slot, which called
"the edition's own scheme" the behaviour #203 reports as a defect. #203's defect is that **nothing
declares anything and the mismatch is silent**. A primary source whose scheme governs the result,
declared, is the opposite of that.*

***Two things still to name***, both small and both the Captain's:

- *the key that states the result's scheme — `versification:` is the obvious candidate, taking a
  scheme id (`org`, `eng`, `lxx`, `vul`, `rsc`, `rso`) or a path to a custom mapping;*
  
  => Yes, "versification"

  *Named. And refined below: two fields rather than one, so a project naming a standard scheme
  **and** customizing it needs no overloading — `versification_scheme` and `custom_versification`,
  either or both, with a bare custom mapping meaning `org`.*
  
- *how the primary is designated once a step can return a pair. With a single `edition:` the
  primary is unambiguous; the pairing shape is unbuilt (§6) and the designation should be settled
  with it rather than guessed at now.*
  
  => Perhaps there is always a primary and a parallel, not two pairs on the same level. When would we need "a pair," and why?

  *Agreed, and it simplifies the design rather than only naming it. Every case identifiable today
  is asymmetric: a source text with a translation riding along (`nida-institute/ears-to-hear`'s
  `source_text` plus BSB), or a translation checked against its source. The one case that would be
  symmetric — two editions of the same language collated — is what the apparatus already serves,
  as footnotes in one edition (§3.6), so it needs no pair.*

  ***So: `primary` and `parallel`, never two on the same level.** The versification ruling above
  already presupposed this — "you get the Hebrew versification, whatever the primary source is."*

  ***Consequence worth stating: the key becomes an override and is never required.** The table
  above has a row for "two editions to be compared — must be stated", and that was the only case
  forcing the key. With asymmetry it disappears: the primary's scheme always governs by default, and
  `versification` exists to override it. `sp lint` therefore has nothing to catch here, which
  retires the observation two paragraphs below.*

*Not a ruling, and stated as a consequence to be checked: on this design `sp lint` can catch the
case that matters — two editions requested for comparison with no `versification:` stated — because
it is visible in the YAML without running anything.*

**The emitted USJ states which versification it used.** Ruled 2026-08-26. It goes in the
`scripture_pipelines` container, beside the other things the payload says about itself.

*This is the third application of one principle today, and it is worth naming so it is applied
deliberately rather than rediscovered: **the payload declares its own provenance.** `senses` carries
`source: sdbh` rather than leaving a consumer to infer the lexical project from which keys came
back; `format:` names what the caller wants rather than the serialization it was served from; and a
payload now names the scheme its verse references are in. In each case the alternative is a consumer
inferring provenance from shape, and a wrong inference is silent — which is exactly how the two USJ
payloads reaching `nida-institute/ears-to-hear` came to be paragraphed and versified incompatibly
with nothing in either saying so.*

**And the scheme identifier cannot be a closed enum.** Ruled 2026-08-26: *"in the future, we will
want to also support Paratext sources here, which can have their own custom versifications."*

*Paratext projects ship a `.vrs` file, and rule 12 already records that those are semantically
compatible with the Copenhagen specification — it is derived from them. The specification treats
custom mappings as first-class rather than an extension: the clone carries
`versification-mappings/sample-custom-mappings/` and a worked `ethiopian_custom.json` alongside the
six standard schemes.*

*So `versification:` accepts a standard scheme id **or** a reference to a mapping the project
supplies, and the six standard ids must not be hardcoded as the only legal values. A schema `enum`
would foreclose Paratext support; validation belongs against the set of resolvable schemes, which
is data.*

=> It  might be cleaner to have two separate fields, "versification_scheme" and  "custom_versification", for the two purposes, they can both be present, or only one may be present. Custom versification without specifying a scheme refers to 'org'

**Adopted.** *Two fields, both optional, either or both present:*

```yaml
versification_scheme: eng           # a named standard mapping
custom_versification: ./my.json     # this project's deviations; alone it means basedOn: org
```

*Better than the single key it replaces, and not merely tidier: it **mirrors the specification's own
structure**, where a custom mapping declares `basedOn` and carries only its deviations. The common
case — a project naming a standard scheme and customizing it — is then two fields with obvious
meanings rather than one field that must be parsed to discover which kind of value it holds.*

*`custom_versification` alone meaning `org` matches the hub model: every standard scheme maps
through `org`, so it is the only defensible default for a mapping that names no base.*

*Both are overrides. Neither is ever required — see the asymmetry note above.*

**The data model, and it is the specification's own — not ours to invent.** Ruled 2026-08-26:
*"copenhagen provides maps for 'standard mappings', which are named. Project custom versification
could use the name of the project. In practice, many projects name a standard mapping and also
customize it."* That shape is native:

```json
{ "basedOn": "org",
  "mappedVerses": {"SIR 34:19-22": "SIR 34:16-19"},
  "excludedVerses": [...], "maxVerses": {...},
  "mergedVerses": [...], "partialVerses": {"SIR 36:13": ["a"]} }
```

| field | what it carries |
|---|---|
| `basedOn` | the named standard mapping a project's scheme starts from |
| `mappedVerses` | reference-range → reference-range |
| `maxVerses` | book → per-chapter verse counts |
| `excludedVerses` | references absent from this scheme |
| `mergedVerses` | verses joined together |
| `partialVerses` | verse segments — `SIR 36:13a` |

*A scheme is therefore **named**: one of the standard ids, or a project's own name. A project's
scheme resolves as `basedOn` plus its deviations, so a partial file is normal rather than
incomplete — `ethiopian_custom.json` declares 30 books where `eng.json` declares 92. **The engine
must not treat absence as an error**; it resolves through the base.*

*`mergedVerses` and `partialVerses` are unused by all six standard mappings and are the fields most
likely to be skipped and then needed. Verse segments in particular bear on rule 12: a segment is a
finer location than a verse, and a milestone form has nowhere to put `36:13a` unless the design says
where.*

**Licensing, ruled 2026-08-26: *"all code should be Apache, all data should be CC by SA."***

*That is the same split the specification itself uses — Apache 2.0 for code, CC BY-SA 4.0 for data
— which makes vendoring the mappings clean rather than merely permitted. ShareAlike requires an
adaptation to carry the same licence; if our data is CC BY-SA anyway, that is satisfied by
construction, and we may reshape the mappings rather than only redistribute them verbatim.*

***A defect this surfaced, and it is not this step's to fix:** `LICENSE` states Apache 2.0
(Copyright 2025 Biblica, Inc.) while `pyproject.toml` declares MIT in two places — `license = {text
= "MIT"}` and the OSI classifier — and that metadata is what PyPI publishes. Two encodings of one
fact, and this one legal. It belongs with #212.*

### 3.0a A seventh `include` family: `syntax` — and it reverses §4.5

**Ruled 2026-08-26:** *"we probably want to allow usj to specify 'syntax' in addition to
morphology, providing a JSON equivalent to the Lowfat trees."*

*`design-scripture-representations.md` §4.5 ruled the syntax tree **out** of `include`, on the
grounds that "USJ has nowhere to put a constituency tree". That reasoning does not survive: the
`scripture_pipelines` container is precisely a home for what USJ cannot hold, and a tree of node
objects keyed to word ids fits there as readily as a sense does. §4.5 stands for **paragraphs**,
which Q4 settled the other way — they arrive through `format: print`, not through `include`.*

*So the families are seven: `ids`, `morphology`, `senses`, `glosses`, `referents`, `discourse`,
**`syntax`**.*

**Measured, lowfat Mark:**

| | |
|---|---|
| `wg` groups | **8,173** |
| words | 11,286 |
| nodes a JSON tree would carry | **19,459** — 1.7x the words alone |
| maximum nesting depth | **17** |
| `wg` attributes in use | `class`, `role`, `rule`, `Rule`, `type`, `clauseType`, `junction`, `predication`, `articular`, `nodeId` |

*§4.5 cited "4,009 clauses in Mark"; the file has 8,173 `wg` groups, so that figure counted a
subset — clauses rather than all groups. Recorded because the smaller number understates the
payload by half.*

**Note `rule` and `Rule` both occur.** Two attributes differing only in case, in the same
serialization. That is a data question for the source rather than something the engine should
silently merge or silently pick between.

**The shape: nested objects mirroring the tree, with an id on every node.** Ruled 2026-08-26.

```json
{"id": "n41001001001-cl3", "class": "cl", "role": "s", "children": [
  {"id": "n41001001001", "ref": "MRK 1:1!1"},
  {"id": "...-wg7", "class": "np", "children": [...]}
]}
```

*Nested rather than a flat node list with parent pointers, for a reason specific to this engine
rather than general preference: **the payload's primary consumer is a language model**, and
pointer-chasing is the kind of mechanical inference a model performs unreliably and without saying
so. Containment shown directly beats containment described by reference. The second argument is the
one both consumer repositories already made about milestone builders — do not make every consumer
rebuild what the engine can hand it correctly — and it does not weaken because the structure is a
tree rather than a string.*

*The id on every node takes the one real advantage a flat list had. It gives addressability
alongside containment: a node can be named without a path, a consumer can index the whole tree by
id in a single pass if it wants a flat view, and an audit finding can cite a constituent. Lowfat
already carries `nodeId` on `wg`, so this needs no invention.*

*Recorded against this ruling: **depth 17 nesting remains hard to diff and hard to quote.** Ids
mitigate that rather than removing it. If audit-ability of the tree turns out to matter more than
assumed, that is the argument that would reopen this.*

**When `passage:` cuts through a clause, the whole clause is returned.** Ruled 2026-08-26:
*"provide the entire syntax tree for the clause, even if it contains extra text."*

*Three options were on the table — truncate the node; include the whole clause; truncate and declare
the loss. An earlier revision of this section argued for the third, on the grounds that it is the
only one that does not misrepresent itself. That reasoning was wrong in its premise: **a truncated
constituent is not a smaller truth, it is a false one.** Syntax is constituency. A clause missing
its verb does not tell a model less about the clause; it invites a confident wrong analysis, and
nothing in the payload would prevent that even with the loss declared.*

*Extra text past the boundary is honest surplus. It is also cheap: the unit is a clause, and
`passage:` is normally a pericope or larger, so the overrun is a few words at each edge.*

*Two consequences worth stating so they are not discovered:*

- ***The tree is always valid.*** *There is no partial node, no incompleteness marker, and no
  consumer code for handling a truncated constituent. That is a simpler contract than the option
  this replaces, which would have required every consumer to handle a case that now cannot arise.*
- ***So the response must say what it actually covers.*** *`passage:` becomes a request rather than
  a guarantee, and the payload declares its true extent — the same principle as the versification
  scheme and the sense `source`. A consumer comparing a `syntax` payload against a `milestones`
  payload for the same `passage:` will otherwise find more words in one than the other, with
  nothing explaining why.*

### 3.0 Which serialization the step reads — TEI as spine, TSV for attributes, lowfat for syntax

**`xml:id` joins all three, verified 2026-08-26 on Mark:** 11,286 ids in the TEI, 11,286 in
lowfat, 11,286 in the TSV, **complete three-way intersection, and zero cases where the same id
carries a different `ref`**. So the join key genuinely carries the architecture, and `syntax` needs
no new addressing scheme — a tree node names the words it spans by the same ids every other family
uses.

**Measured 2026-08-25, after this plan was first drafted around the TSV.** Macula ships three
serializations of SBLGNT and they are not equivalent for this purpose:

| | lowfat (trees) | TSV | **TEI** |
|---|---|---|---|
| document order == reading order | **no** | yes | **yes** — 11,286 tokens, zero out-of-order |
| word ids | yes | yes | yes — `xml:id` and `ref` on every `<w>` |
| paragraphs | no | no | **yes** — 91 in Mark |
| inter-word material | attribute | `after` column | **`pc` nodes in document order** |
| apparatus reference marks | no | no | **yes — 931 in Mark** |
| editorial brackets `⟦ ⟧` | no | no | yes |
| word attributes (lemma, morph, senses…) | yes | yes | **no** |

**The TEI is token-complete against the Logos SBLGNT edition:** all 27 books, **137,741 words in
each, zero books differing**. Its paragraphing agrees with Logos at **98.5%** — 1,282 of 1,302
breaks at the same word offset. The 20 Logos-only breaks are all a book's closing benediction set
as its own paragraph, a typographic convention; 18 of the 20 are the final verse of their book.

**So the TEI is the spine and the TSV supplies word attributes**, joined on `xml:id`. The TEI
carries no lemma, morphology or senses — `<w>` has only `ref` and `xml:id` — which is also why
`format: print` is not annotatable (§3.4): there is nothing in that file to annotate with.

### 3.1 Verse placement comes from each token's own `ref`

**Never from tree nesting.** Measured 2026-08-25 on `macula-greek/SBLGNT/lowfat/02-mark.xml`:

| | |
|---|---|
| verse milestones in document order | 826 for 673 verses — **non-decreasing: 153 adjacent repeats, 0 reversals** |
| words in document order == reading order | **False** |
| words sorted by `xml:id` == reading order | **True** |
| tokens whose enclosing milestone contradicts their own `ref` | **1,501 of 11,286**, all forward, none backward |

***"Non-decreasing" not "strictly ascending", and the difference is not pedantry.*** *An earlier
revision claimed "826, strictly ascending, zero out-of-order transitions". A repeat is not a
reversal, and a `sorted()` comparison cannot tell them apart — so the check passed while the wording
was wrong. `nida-institute/ears-to-hear` re-tested counting repeats as out-of-order, got 153, and
appeared to contradict the finding. State it as: **826 milestones for 673 verses, non-decreasing,
153 adjacent repeats, 0 reversals.** The repeats are the mechanism, not noise — a verse is
milestoned again each time it resumes.*

*For contrast, the TEI has **673 milestones for 673 verses, no repeats, strictly increasing** — which
is another reason it is the easier spine.*

The milestones are sound; a document-order walk of a **syntax** tree is not. 826 milestones serve
673 verses because a verse is milestoned each time it resumes. A consumer carrying `current_verse`
across such a walk misplaces one verse in seven.

**Consequences for implementation:**

- **From the TSV, no sorting is needed.** `ref` is a per-row column and all 11,286 Mark tokens are
  already in strict reading order — zero out-of-order transitions.
- **From the trees, sort by `xml:id` first**, then read each token's `ref`.

### 3.2 Token joining is edition data, not logic

Greek `after` **replaces** the space; Hebrew `after` **accompanies** it. `~/.sp/editions/WLC.yaml`
already records the Hebrew half — *"`after` carries the space, maqqef and sof pasuq, so word
joining is data rather than logic"* — and it is false for Greek. A consumer applying the Hebrew
rule to Greek produces `προφήτῃ·Ἰδοὺ`; that defect exists in a consumer today.

TSV `after` counts across the Greek corpus: `' '` 117,020 · `','` 8,978 · `'.'` 5,320 · `'·'` 4,242
· `'’'` 1,218 · `';'` 963 — **never a punctuation-plus-space pair.**

This is the single thing most likely to be got subtly wrong once per consumer, which is why both
consumer repositories asked for it in the engine. **The joining rule belongs in the edition
declaration**, not in the step's code.

=> Amen to that last sentence.

**Reading the TEI instead makes this structural, and the question dissolves.** Its `pc` elements
carry inter-word material as nodes in document order — 2,741 in Mark, reconciling exactly with
Logos's 933 `prefix` plus 1,808 non-empty `suffix`. Concatenating `w` and `pc` in order reproduces
the text with no rule about whether `after` replaces or accompanies a space, because the question
is not asked.

*The `after` rule still matters for anyone reading the TSV directly, and the counts above stay in
this document for that reason. It stops being the engine's problem.*

**Correction, 2026-08-26, from building it: the heading is wrong and the question did not
dissolve.** Neither serialization carries enough to render running text. The TSV's `after` holds
bare punctuation with no following space, and the TEI's `pc` nodes sit adjacent to `w` with no
whitespace between them either — so *both* produce `χριστοῦ.Καθὼς` under a faithful
concatenation, and reading the TEI does not avoid the rule, it only hides it.

Ruled: **a space follows punctuation that ends a word, except where the mark itself joins.** The
declarative half survives — *which* marks join is data — but that a word-ending mark takes a
following space is a rule the engine applies. Full `after` census, both corpora:

| Greek | | Hebrew | |
|---|---|---|---|
| `' '` | 117,013 | `' '` | 237,414 |
| `','` | 8,978 | `''` **(empty)** | 170,393 |
| `'.'` | 5,320 | `'־'` maqqef | 42,569 |
| `'·'` | 4,245 | `'׃'` sof pasuq | 20,120 |
| `'’'` elision | 1,221 | `'׀'` paseq | 2,274 |
| `';'` | 964 | `'׃ס'` · `'׃פ'` · `'ס'` · `'פ'` | 1,888 · 1,164 · 77 · 12 |

`after` plays **three** roles, not one: a space, a mark that joins, or punctuation that ends a
word. Hence `JOINING_MARKS = {’, ־}` plus empty; everything else non-empty takes a space. A
uniform `" ".join(text + after)` was considered and rejected: it would put a space inside
`בְּרֵאשִׁית` (170,393 cases), `κατ’αὐτοῦ` (1,221) and `עַל־פְּנֵי` (42,569).

*Two marks are handled but imperfectly, and are named rather than hidden: the paseq `׀` takes a
space after but not before, so it renders `word׀ word` rather than `word ׀ word`; and the
`partialVerses` field that would describe segment-level text is unread. Both are small, both
affect Hebrew only, and neither is silent.*

### 3.3 `usj` carries no paragraph structure

One `para` per chapter, as a container the USX grammar requires (Q4). The source has none, so there
is nothing to carry. A caller wanting editorial structure asks for `format: print`.

=> A case we haven't discussed. USX/USJ/USFM can represent everything in the print edition too, and is what most publishers actually use to publish. Do we need a way to support a "print edition" in USX format, the most likely format to be used?

**Yes. Ruled 2026-08-26: `print_format: [usx, usfm, usj, tei]`, and `html` under conditions.**

*The question exposed an inconsistency worth naming: `plain`, `milestones` and `usj` say what shape
the bytes take, while **`print` is the only intent in the enum** — it says what the content is and
leaves the encoding open. `print_format` fills that gap rather than hiding it.*

*It also shows Q4's ruling was about the **source**, not about USJ. "You can't have paragraph
structure in this USJ" holds of USJ built from Macula, which has none. USJ built from a print
serialization carries them, so `print` with `print_format: usj` is exactly "USJ with paragraphs"
and contradicts nothing.*

*Three of the four are one data model — USFM is the markup, USX its XML, USJ its JSON — so this is
mostly wiring: `utils/data.py` already has `_usx_to_usj`, `load_usfm_passage`,
`_extract_verse_range_usj` and a `_format_result` switch, and the parked `usfm` backend uses them.
**TEI is the only new reader**, and it is the one already measured (§3.0).*

**`html`: semantic markup only, and it is a serialization on those terms.** Proposed and accepted
the same day — the engine emits structure and a stylesheet formats it. Two conditions, because
without them it stops being a serialization:

- **No presentational choices in the markup.** No `<i>`, no inline styles, no font selection. Rule
  31 forbids slanting scripts with no italic tradition, and markup that emits emphasis has made that
  decision where no stylesheet can retract it.
- **`lang` and `dir` are required**, because they are semantic rather than presentational. Hebrew
  without `dir="rtl"` is not styled badly, it is structurally wrong, and a consumer's stylesheet
  cannot repair a missing direction. Both drive font fallback as well.
- **A default stylesheet ships with it.** An earlier revision of this section argued for shipping
  none, on the grounds that rule 31 would govern it. That was avoidance rather than caution:
  semantic HTML with no stylesheet renders as an undifferentiated wall, so shipping nothing does not
  avoid the typography question — it hands it to every consumer, who then rediscovers the rule the
  hard way. **The default is a reference implementation**: it shows which classes exist and how to
  target them, and it is the one place where rule 31 can be demonstrated instead of merely stated.
  It must therefore mark emphasis with weight, colour or size and never `font-style: italic` on a
  script with no italic tradition, scope by `lang` and `dir`, say in a comment why, and stay minimal
  — a starting point, not a design system.

**Default: `usx`.** Ruled 2026-08-26 — *"defaulting to usx is probably best for most publishers."*

*An earlier revision defaulted to `tei`, on the grounds that it is the serialization measured here.
That was reasoning from what we had verified rather than from who asks. A default should fit the
common caller, and for a print edition that caller is publishing: USX is what publishing tooling
consumes, and USJ and USFM are the same data model beside it. TEI remains available and is the right
choice for scholarly work, but it is the specialist answer, not the ordinary one.*

### 3.4 `print` is not annotatable

`include` with `format: print` is a **lint error**, not a warning (Q4). It is a category confusion:
a caller who asked for the print edition asked for editorial structure, and a payload that is both
editorial and analytical invites reading structural meaning out of an editor's paragraphing.

### 3.5 Senses keep their source's own names, and say whose they are

```yaml
senses:
  source: sdbh
  fields: {lexdomain: …, contextualdomain: …, coredomain: …, sdbh: …, sensenumber: …}
```

Unnormalised, because unifying Louw-Nida and SDBH is **ontology merging** — a known hard problem,
not a field rename. The declared `source` lets a consumer branch on a stated value rather than
sniff which keys came back.

### 3.6 Variants are footnotes, and they carry their own anchor

They are the edition's footnotes (Q2), so in USJ they are `note` elements at a position in the
text. **Measured 2026-08-25:** 889 of Mark's 930 apparatus notes — **95.6%** — resolve to a
contiguous token span by matching the printed forms before the `]`. 315 anchors (34%) are
multi-word.

**But lemma matching is the fallback, not the method.** Measured after the above: the printed
edition's own **apparatus reference marks are already in the TEI**, as `pc` nodes at exact
positions. **Count only the marks that introduce a note** — `⸀ ⸁ ⸂ ⸄ ⸆ ⸇ ⸈ ⸉` — and never the
closers `⸃ ⸅ ⸊`, which end a span rather than starting an entry. In Mark: `⸀` 607, `⸁` 8, `⸂` 314,
`⸄` 1 — **930 introducing marks against 930 notes.**

**The join is ordinal, and its scope is the chapter, not the verse.**

| scope | agreement, 27 books |
|---|---|
| verse | 4,463 of 4,473 — **10 disagree** |
| **chapter** | **260 of 260 — no exceptions** |
| NT totals, marks / notes | **6,934 / 6,934**, differing in 0 of 27 books |

*The ten verse-level disagreements are five adjacent pairs, each +1 on verse N and −1 on N+1:
Matthew 16:2–3, Matthew 26:60–61, Luke 22:19–20, Luke 22:43–44, Philippians 1:16–17. They are
variants spanning a verse boundary — the apparatus files the note under the opening verse while the
TEI's mark falls after the next verse milestone. Reported by `nida-institute/discourse-flow` and
verified here independently.*

***Verse-scoped joining is worse than wrong, it is silent.*** *The counts differ on those ten, but
each side is individually plausible, so an entry lands at a confidently wrong word rather than
raising. Chapter scope removes the failure instead of detecting it.*

*So walk a chapter's marks in document order, walk its notes in order, pair them. Each mark sits
between `<w>` elements carrying `xml:id`, so every entry lands at an exact word position by
construction. `⸂…⸃` is a span in the text itself and needs no parsing.*

***Two corrections to an earlier revision of this section**, both found by
`nida-institute/discourse-flow` and confirmed here. It gave Mark's `⸃` as 205; it is **314**, exactly
balanced against `⸂` — the 205 counted only `pc` elements whose text is exactly `⸃`, missing 109
where the closer is combined with punctuation (`⸃·` 29, `⸃.` 43, `⸃,` 24, `⸃;` 10, `⸃—` 2, `;⸃` 1).
An unbalanced substitution bracket would have been a genuine data alarm, so the wrong figure would
have sent someone hunting a defect that does not exist. And it reported "14 verses needing a human
in 6 books"; the true number is **zero**, once closers are excluded and the join is chapter-scoped.*

`format: plain` and `format: milestones` carry no notes: a footnote is not running text.

**This also solves what an earlier revision recorded as unsolvable.** It said words present only in
another witness have no id and cannot be given one without minting, so
`nida-institute/discourse-flow`'s second blocker — *"per verse, the words NA28 has that SBLGNT does
not, in order, addressable"* — stayed out of reach. With the marks in place a variant attaches
between two identified words, which is exactly addressable. Recorded as a correction rather than
edited away, because the claim was made twice.

---

## 4. Lint rules

Each is a test before it is code.

| rule | severity |
|---|---|
| `include` with `format: print` | **error** — category confusion (§3.4) |
| `include` with `format: plain` or `milestones` | **error** — nowhere to put it |
| `include` naming an unknown member | error |
| `edition` not registered | error |
| `include` requesting a family the edition has no data for | **warning** — e.g. `discourse` on Hebrew |
| `format` absent | none — defaults to `milestones` |

---

## 4a. Definition of done for every step in §5

Ruled 2026-08-26: a step is not done when its tests pass. **It is done when a reader can choose
between the representations without reading the code**, which means each step ships documentation
covering the feature *and* the reasoning — when you would use this form, and what it costs against
the others.

| document | what it gains | how it is written |
|---|---|---|
| `docs/llmflow-language.md` | the step's grammar: keys, formats, `include`, `versification` | directly; this repository's own |
| `docs/llmflow-language-quickref.md` | the same, compressed — it is what a project reads | **via `LANGUAGE_QUICKREF_DOC`**, then regenerate. Never hand-edit the file |
| `docs/architecture.md` | how the step resolves an edition, maps a reference, reads a serialization | directly |
| `docs/ai-context/sp/` | the AI-facing account, so a session picks a representation deliberately | **via its template or constant**, then regenerate — the directory is generated and a hand edit is lost |

**The reasoning is the part most likely to be skipped, so it is named explicitly.** Every format
and every `include` family carries a cost, and those numbers already exist rather than needing
invention:

| form | cost | when it is the right choice |
|---|---|---|
| `plain` | baseline | a whole-book step that cannot window — one consumer reads 32 KB where the annotated form is 1.3 MB, a 43x difference |
| `milestones` | **1.072x** bare text | the default, and enough whenever a verse reference is all the addressing needed |
| `usj`, no `include` | 2.56x codepoints, **6.74x as escaped JSON** | structure is needed but annotation is not |
| `usj` + families | to **11.78x** as one consumer ships it | only the families a step actually reads |
| `syntax` | 19,459 nodes against 11,286 words, depth 17 | constituency is the subject of the analysis |
| `print` | paragraphs, no annotation | the editorial shape, for a reader rather than a model |

**State the unit beside every multiplier.** The same book measures 2.56x in codepoints, 1.78x in
UTF-8 bytes and 6.74x as escaped JSON. A consumer measured all three and asked for the unit to be
stated, because a reader who assumes bytes and gets escaped JSON mis-costs every decision
downstream.

---

## 5. Implementation order — simple to complex

**Ruled 2026-08-26: build stepwise, simple to complex.** Two principles order the list, and both
are worth stating because they are what make a step *simple* rather than merely *small*:

- **Machinery before payload.** Versification and the container come before any family, because
  every family is delivered through them and a family built first would be rebuilt.
- **Prefer a step with an oracle.** Where an existing implementation already produces the right
  answer, the new one can be tested against it rather than against a hand-written expectation.
  Two steps below have that property and are placed early for it.

Each step ends green, with tests written first, before the next begins.

---

**0. Land what already exists — no new code.** `plain`, `milestones`, `milestones` as the default,
placement from each token's `ref`, the edition registry, the `tsv` and `usfm` backends, the schema
entry and 13 tests are **built and tested** on the `wip/scripture-200` tag — `05d75a5` and
`34c7931`. No branch contains them and `dev` has moved 57 commits since their base at `cb72cb7`.
Cherry-pick the two code commits; `0bb1d5b` is `TODO.md`-only and its one durable line is recorded
in §3.-1.

**1. A `kind: tei` backend producing `plain` and `milestones`.** The simplest possible new work —
concatenate `w` and `pc` in document order, milestone from each token's `ref` — and **it has an
oracle**: the TSV backend already produces the correct string, so the test is that both backends
return identical text for the same passage. A test with a known-good comparison is worth more than
one with a hand-typed expectation.

*This also retires §3.2's joining question rather than answering it: `pc` nodes are already in
document order, so no `after` rule is consulted.*

**2. Versification.** Self-contained, no payload shape, no dependency on any format: read the
Copenhagen mappings, resolve `basedOn`, map a reference between named schemes. A pure function with
a pure test. It comes before every format because they are all keyed by verse, and building on
unmapped references means every Old Testament passage is quietly wrong. Tests: `PSA 51:1` maps
`eng`→`org` as a two-verse offset; `MAL 4:1` resolves to `MAL 3:19`; a partial custom mapping
resolves through its base rather than erroring; an unmappable reference raises rather than
returning empty; same-scheme mapping is identity.

**3. `format: usj`, structure only.** No `include`, no container contents. One `para` per chapter,
verse milestones from `ref`, words. **Also has an oracle**: flattening the emitted USJ must
reproduce `format: milestones` exactly for the same passage.

**4. The container, and `include: [ids]`.** The smallest possible family — `xml:id` per word — so
the step that introduces the `scripture_pipelines` container and the `include` machinery carries
almost no payload logic of its own. Tests: the container appears only when `include` is non-empty;
`format: usj` with no `include` returns the text in USJ structure and no annotation.

**5. `include: [morphology]` and `include: [glosses]`.** The first real join — TSV to TEI on
`xml:id`, verified exact in §3.0. Per-word records, no new machinery. Tests per family: the declared
columns arrive, nothing undeclared does, and `morphology` reaches `role`, `class` and `type`, which
`nida-institute/discourse-flow` ranked as blocking.

**6. `include: [senses]`.** Same join, plus one new thing: the declared `source` (§3.5). Tests:
Greek yields `{domain, ln}` under `source: louw-nida`, Hebrew its five fields under `source: sdbh`,
and neither is normalised into the other.

**7. `include: [referents]`.** Per-word, same shape as 5. Last of the straightforward families.

**8. `format: print`.** TEI paragraphs, and the lint rule that `include` with `print` is an error
rather than a warning (§3.4). Tests: paragraphs present; the benediction divergence documented, not
asserted as agreement; `include` rejected at lint.

**9. `include: [discourse]`.** First family needing a source outside Macula — Levinsohn's 33 LGNTDF
feature types, Greek only. Tests: features attach at word ids; a Hebrew edition warns rather than
failing (§4).

*Measured in the source, 2026-08-26, because three of these facts change the algorithm:*

| | |
|---|---|
| feature files | **33** (plus `levinsohn.xml`, which only `xi:include`s them, and a dangling emacs lock file) |
| citations | **52,257** |
| books | 27, keyed by **OSIS** code — `Matt`, `Mark`, `1John` — not USFM, so a mapping is needed |
| quote length | 37,975 are one word; the longest is **509** |
| `type` | `propositions` (Main clauses), `markup` (31 features), `annotations` (1) |
| `level` | 0–6 on Main clauses; absent on 25,644 citations |

*Each citation is `<reference osisRef="Matt.1.1!1" type="…" level="0" verse="Matt 1:1">quote</reference>`
— the `!n` index is 1-based within the verse, matching Macula's `ref`, and **the quote is
lowercased**.*

**The resolution rules, from `nida-institute/discourse-flow`'s `plugins/reference_resolution.py`,
which is the reference implementation and the oracle for this step:**

| condition | outcome | id returned |
|---|---|---|
| quote matches at the index | `verified` | the indexed word |
| index usable, quote matches elsewhere | `disagrees` — **the index is kept** and flagged | the indexed word |
| index impossible, quote found **exactly once** | `rescued` | the quote's position |
| index impossible, quote found more than once | `ambiguous` | none |
| index impossible, quote absent | `not_found` | none |
| quote empty, index usable | `unverifiable` | the indexed word |

*Two requirements their prose did not state, both found in the code and both load-bearing:*

- **Normalise before comparing**: NFD, strip combining marks, lowercase, trim edge punctuation.
  Case-folding is unavoidable — every LGNTDF quote is lowercased while the text capitalises
  sentence-initial words. The diacritic half was justified by SBLGNT encoding the acute two ways,
  oxia and tonos, rendering identically (`Clear-Bible/macula-greek#109`). **Measured 2026-08-26:
  that is now fixed — the corpus is 42,112 tonos and zero oxia, and LGNTDF is 39,280 tonos and
  zero oxia.** So the hazard is dormant rather than absent, and stripping stays: Macula was
  re-normalised on 2026-08-25, which is the argument for not letting the comparison depend on
  either side's encoding.
- **A phrase may run past the verse end.** A range ref quotes across verses —
  `Matt.6.9!5-Matt.6.13!61` is the whole Lord's Prayer — and only the opening is cited, so the
  comparison is against the prefix that fits, with a minimum length before a truncated match counts.

*The `disagrees` row is the one that cost them a corrected pass: `Main clauses` indexes the clause
**onset** while quoting the constituent Levinsohn cites — Mark 1:14 indexes `Καὶ` and quotes
`μετὰ`. Treating that as an error and moving the index relocated 84 clause boundaries. **Only an
impossible index is ever moved** (31 NT-wide).*

*Their per-book figures are the acceptance target: Mark 4,400 citations at 96.7% verified, 2.1%
rescued, 1.3% unresolved; NT-wide 51,699 of 51,722 resolve, and the 23 refusals are real textual
differences.*

**10. Variants as notes.** Apparatus parsing plus the ordinal join (§3.6). More complex than any
family because it reads a second file with its own conventions. Tests: marks pair with notes per
verse; an entry resolves to a word position; Mark 8:35's mismatch is handled explicitly rather than
silently; notes absent from `plain` and `milestones`.

**11. `include: [syntax]`.** Lowfat as a third source, a nested tree with an id on every node,
19,459 nodes for Mark at depth 17, and the whole-clause rule at passage boundaries — which means the
response must declare the extent it actually covers.

**12. `print_format: html`, and its default stylesheet. Last, ruled 2026-08-26.** It is the only
step that leaves data serialization for presentation, and the only one carrying a typography
constraint — rule 31, demonstrated in the shipped stylesheet rather than merely stated. Everything
before it is reachable without it, and a consumer already builds its own reader HTML today, so
nothing waits on this. Tests: emphasis is never `font-style: italic` on a script with no italic
tradition; `lang` and `dir` present on every language-bearing element; the markup carries no inline
style.

---

**Not in this sequence, and deliberately:**

- **Fixing the TEI upstream** to carry its own apparatus and a `teiHeader` — filed as
  **`Clear-Bible/macula-greek#110`**, 2026-08-26, where that repository's own AI will pick it up.
  The measurements behind it live in that issue rather than here, so there is one copy: 6,940 marks
  against 6,934 notes across 27 books, 99.7% of verses agreeing, 14 needing a human. **What we asked
  for concretely is that every entry names the word ids it applies to** — inline or standoff is
  theirs to choose, but an entry without ids leaves a consumer string-matching the lemma, which is
  the position we are in today. If it lands before step 10 that step gets simpler; if after, step 10
  keeps working and the ordinal join becomes redundant.
- **Reading the trees for anything but `syntax`.** No other format needs them, and §3.1 makes that
  path strictly harder — sort by `xml:id` first, never trust nesting.
- **Pairing a source text with a translation.** §6.

## 6. What this does not cover

  => But you can get the syntax tree by declaring syntax in members.

*Correct, and this entry was stale — removed. `syntax` became an `include` family on 2026-08-26
(§3.0a), which is what reversed §4.5's reasoning: the container is a home for what USJ cannot hold.
No separate `format: syntax` is needed, and nothing about the tree is uncovered.*

- **Pairing a source text with a translation.** `nida-institute/ears-to-hear` showed the two
  payloads do not carry the same verse set — four verses in BSB and not in SBLGNT for Mark — and
  are not the same shape. Their §7 asks whether pairing belongs in the engine at all. Unruled.
  
- **Word-addressable variants**, per §3.6.

- **Licensing.** `#212`. Named here only because a consumer reported shipping a book's complete
  original-language text with no attribution against a CC BY source, and the engine emitting text
  is the natural place for a credit line to originate. Not this step's scope, and time-sensitive
  independently of it.

- **An `edition:` that names a Paratext project code, with the projects directory given once.**
  Raised by the Captain, 2026-08-26, and deliberately out of this release. Most of it exists: a
  `kind: usfm` edition already takes `base_dir` and `project`, and versification is already read
  from that project's `Settings.xml`. What is missing is the shape — the projects directory
  wants to be **one pipeline-level parameter** rather than repeated in every edition entry, so
  that a pipeline names project codes and a machine says once where its projects live. That is
  also what makes such a pipeline portable between two people who each have rights to the same
  project but keep it in different places.

  *Two things to settle when it is built: a project's `custom.vrs` overlay is read by nothing
  today and 29 of 39 projects on the Captain's machine carry one; and rights are per-project, so
  a pipeline naming a code the runner cannot read must fail with that reason rather than as a
  missing file.*
