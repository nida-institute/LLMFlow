# Target-language text for a span named by source word ids

**Status: ruled (2026-09-14), one decision open.** §2 carries sixteen rulings, R1–R16. D1–D8 are
answered; **D9 is open but does not block discourse-flow** — it blocks R13's twenty pairs.
`SBLGNT-BSB` and `WLCM-BSB`, the only pairs discourse-flow needs, join at 100%. **This is not authorization to build** — `plans-first` requires the Captain's explicit direction to begin, and
nothing here has been implemented.

Tracked as **#238**. Raised by
`collab/discourse-flow/2026-09-11-cutting-the-english-where-the-greek-is-cut.md`.
Alignment is the only known blocker for that project.

---

## 1. What is being built, and why here

A pipeline can already cut a source passage by word id — `spans:` on `type: scripture`, shipped in
`3ca7139`. It returns the Greek for `{from, to}` pairs of Macula word ids. There is no counterpart
for the translation: at a boundary falling inside a verse, a consumer has no handle on the English.

The engine builds it rather than the consumer, because the alignment data is organised by target
language and one implementation serves every pair in it. The same need exists against WLC for
Hebrew work, and for any project publishing analysis of a source text beside a translation.

**Vocabulary.** *Source* is the text the ids name (SBLGNT, WLCM). *Target* is the translation
(BSB, YLT). A *span* is a `{from, to}` pair of source word ids. A *record* is one entry in an
alignment file, pairing a set of source ids with a set of target ids.

**What a span covers.** A span is named on the source side; what it **covers** is a stretch of the
*target*. Because the alignment is filed per verse (R6), a span covers tokens **in each verse it
draws from**, and its target text is those stretches concatenated in verse order.

Within one verse, what a span covers is fixed in two steps:

1. **Aligned bounds** — from the lowest to the highest target token aligned to any source unit in
   the span, inclusive.
2. **Extension** — those bounds then move outward over any run of unaligned tokens at either end,
   stopping where a token belonging to a different source unit begins (D2).

Everything between the final bounds is part of the span's output. Stating it in two steps makes
clear that a span does not cover simply "first to last aligned token" — that was the reading that
dropped Ephesians 1:11's leading *"In Him"*.

A span's target tokens in a verse are **contiguous** when nothing between the first and the last
belongs to a different source unit. That fails only where a span opens or closes inside a verse.

*Unaligned* is used throughout for a token that aligns to no source unit at all. R1 includes the
unaligned tokens inside the span.

**Several words are deliberately absent, and no noun replaces them.** A token a span covers that
belongs to a different source unit is called exactly that — the phrase, not a name. Ruled by the
Captain, 2026-09-14, working through the vocabulary one term at a time:

- ~~`absorbed`~~ → "the unaligned tokens inside the span".
- ~~`refused`~~, ~~`foreign`~~ → "a token inside the span's range that belongs to a different
  source unit". These two named the same token from opposite sides, and *refused* also implied the
  span had a claim it declined — which R8 removed, since target order settles ownership outright.
- ~~`interleaved`~~ → retired with no replacement. Captain: *"don't use the term interleaved at
  all. use well-defined terms like contiguous, etc."* It had been carrying two meanings — tokens
  that are not contiguous, and a span merely covering several verses — and the second is not a
  defect but the
  ordinary case (R6). Contiguity is checkable; interleaving was never defined.

The vocabulary that remains is the Captain's or is standard: *span*, *contiguous*, *unaligned*,
*constituent*, *source order*, *target order*. No noun was coined for what a span covers; it is a
verb.

---

## 2. Rulings — settled, do not reopen

**R1 — a span returns its aligned tokens plus the unaligned tokens between them.**
Captain, 2026-09-13. An unaligned token inside the span — one aligning to *nothing* — is included;
a token the span covers that belongs to a *different* source unit is not. This is neither
"aligned only" (which returns fragments) nor "whole range" (which double-claims in a third of
cases).

**R2 — the engine reads its own declaration of supported pairs, not Clear's catalog.**
Captain, 2026-09-13. A file in this repository's `data/` names the pairs we support. Each is
validated at read time against the alignment file's own `documents` block. We do not depend on
`Clear/Alignments/data/catalog.tsv`.

**R3 — the corrected catalog omits the bogus Hausa OT pair only.**
Captain, 2026-09-13. `WLCM-OHCB-manual` is dropped; `SBLGNT-OHCB-manual` is genuine and kept.

**R4 — direction is explicit.** Captain, 2026-09-13: *"alignments are directional. both `from` and
`to` must be specified."* Neither is inferred from the other, from a filename, or from a default.

**The keys are spelled `source:` and `target:`, not `from:`/`to:`** — decided in implementation
2026-09-14 and recorded because it departs from the Captain's wording. Two reasons, the first
absolute: **`from` is a Python keyword**, so the generated `Step` cannot expose it as an
attribute, and `tests/test_pipeline_model.py::test_step_attributes_match_schema` fails outright —
the guard doing exactly what rule 1 describes. The second is that Scripture Burrito's own `roles`
are `["source", "target"]`, so these are the format's words rather than ours. What R4 rules —
that both are named and neither inferred — is unchanged.

`{from, to}` remains the spelling *inside* a span, where it is an ordinary dict key and no
attribute is generated.

**R5 — reordering is into the target's own word order.** Captain, 2026-09-13, choosing between two
readings of *"reorders the target to use its word order"*: the aligned tokens are put back into the
translation's reading order, so the English reads as English. Not into source order — that is a
genuine permutation in 80% of spans and cannot be expressed as a range operation.

Verified by reconstruction rather than by inference: sorting Philemon 1:18–19's tokens by target id
and spacing them with `skip_space_after` yields *"But if he has wronged you in any way or owes you
anything, charge it to my account. I, Paul, write this with my own hand. I will repay it—not to
mention that you owe me your very self"*. The target TSV's file order is exactly its sorted id
order, so id order **is** reading order.

**Extended 2026-09-14**, Captain: *"for R5, I would like an option for source order vs. target
order, default = target order."* So both orderings are available and target order is what a caller
gets without asking. The 09-13 ruling stands as the default; source order is no longer rejected,
it is opt-in.

This separates cleanly from R8, and the two should not be confused: **R8 decides which tokens a
span holds, R5 decides what sequence they come back in.** Membership is settled by target order in
both modes, so asking for source order changes the sequence and never the content.

Say plainly what source order is for: it does **not** read as English, and is not meant to. It
puts the translation's words in the sequence of the text they translate, which is what a reader
comparing the two side by side wants and what a fluent rendering destroys. In 81% of spans the two
sequences differ.

**Who each serves**, Captain 2026-09-14: *"most people will prefer target order, period. the few
people who know Greek or Hebrew want both orders."* That is why target order is the default rather
than a coin-toss between two equals — it is what nearly every reader wants, and the rest of the
time the reader is working with the source language.

**So the request takes a set, not a choice.** Captain, 2026-09-14: *"you should be able to ask for
one or the other or both."* Three requests are legal — target alone, source alone, both — and the
default when nothing is asked is target alone. This is deliberately **not** an enum of two
alternatives: for a source-language reader the two are complementary views of one span, and an
either/or would force that reader to call the step twice for a single unit of work.

Where both are asked for, the result carries both sequences over the **same** token set: R8 fixes
membership, so the two differ only in order and never in content, and a reader can lay them
side by side knowing nothing has been added or dropped between them.

**One sub-question this raises and does not answer:** a target token aligning to several source
words has several source positions, so source order needs a rule for which one places it — the
earliest is the obvious candidate, but it is a choice, and 35% of spans contain such a token.

**R6 — the alignment is filed per verse; our units are not, so we read past verse scope.**
Captain, 2026-09-13: *"alignments are verse-scoped, so we have to look at every verse the source
draws from."* Corrected 2026-09-14, because the heading here previously read *"the unit of work is
the verse"* and inverted the point. The Captain: *"The alignment format does one record per verse,
but we do our work in linguistic units - clauses, phrases, sentences. So we have to read past the
verse scope."*

**The verse is how the data is filed, not what we analyse.** Measured: 80 of 115,008 records have
source and target outside a single verse — 0.070% — so the verse is a reliable *lookup key*. A
span is a clause, a phrase or a sentence, and crosses verses whenever the language does. The two
never had to agree, and the operation exists precisely because they do not.

So: gather every verse the span draws from, resolve aligned tokens in each, and assemble across
them. Which tokens a span takes, and which belong to a different source unit, are settled per
verse because that is the scope the data gives them,
then concatenated in verse order — never treating the whole span as one stretch of the target,
which was the bug that
produced `wordTherefore` and dropped the leading *"In Him"* of Ephesians 1:11.

`verses-are-milestones` governs this and is what made the error visible: a verse may be a milestone
*on* a structure, never an element *of* one. Calling it a unit of work made it structural. Where a
span opens or closes **inside** a verse is the only place a token belonging to a different source
unit can fall inside what a span covers — and that is not a rare
case for linguistic units, it is the whole reason this step was asked for.

**R7 — a Psalm title is offered as a target-side convention, never as a correspondence.**
Captain, 2026-09-13: *"that works"*, answering D7. Where a span covers the source verse holding the
superscription **and** the target happens to carry a verse `000` for that psalm, the step offers it
as a **separately labelled** field — not merged into the span's text and not presented as aligned
to anything. It is positional and says so. Where the target has no verse `000` it degrades to
`null` — present and empty, never omitted (see R11) — which is the ordinary case in a
translation like YLT that carries titles for 11 psalms rather than 116. This deliberately does **not** make verse 000 a general mechanism; §5 D7 records
the measurements that rule that out.

**R8 — a shared target word: no token appears in two spans' text, but the constituent list shows
it in both.**
Captain, 2026-09-13, first: *"both spans get it."* Then, refining the same day: *"the word order of
the target determines which span gets it first in the span as a whole. So the target word order
tells us what span to put it in — or at least, the end user cannot see which span we drew it
from"*, and *"but a constituent list should show it both places."*

Both statements stand, because they govern different outputs:

- **The span's text.** Target word order is the tiebreak: the span whose target stretch the word
  falls in keeps it, and the neighbour does not. So **no token appears in two spans** — concatenating
  adjacent spans reproduces the passage with no word repeated, and a span read on its own does not
  overlap the one beside it. Which span a word was drawn from is not visible in the result, which
  is why target order can decide it without anyone needing to agree who "owns" it.
- **The constituent list**, and the correspondence map R9 makes opt-in. These show the word in
  **both** places, because that is what the alignment says. A diagnostic view that hid the
  many-to-many structure would be lying about the data it exists to expose.

886 adjacent-span pairs at 10-word spans are affected, plus 90 more where an unaligned token
inside the span is also shared. An earlier note here said a token could appear in two spans and that a consumer would see
shared wording twice; the refinement above supersedes that, and it was wrong for the text.

**R9 — the correspondence map is opt-in.** Captain, 2026-09-13, answering D3: *"by default, no,
but provide an option that does for debugging and transparency."* The step does not return the
source-word-to-target-token map unless asked. When asked, it carries the many-to-many structure
§3.1 shows is unrecoverable downstream, and its stated purposes are debugging and transparency
rather than routine consumption.

**R10 — a span reaches outward over unaligned tokens, and stops at a neighbour.** Captain,
2026-09-14, answering D2. Within each verse, the bounds move outward from the first and last
aligned token over any run of unaligned tokens at either end, and stop where a token belonging to a
different source unit begins.

Both halves are load-bearing, and each was established by a failure rather than by argument.
Reaching outward is what keeps verse-final punctuation and verse-initial words: without it the text
reads `wordTherefore` and `Theophilusso`, and Ephesians 1:11 loses its opening *"In Him"* — two
words that align to nothing and whose absence starts a sentence mid-clause. Stopping at a neighbour
is R8's principle applied to unaligned tokens: target order settles who gets them, so no token
appears in two spans.

Measured: 29,964 target tokens align to nothing, **98% punctuation and 2% words**. The 2% are the
ones whose absence breaks a sentence, so a rule that took only punctuation would not do.

**R11 — two kinds of nothing, told apart; and one key that may be omitted.** Captain, 2026-09-14,
answering D4, held to `rule say-which-kind-of-nothing`.

- **An empty collection** — the question was asked and the answer is nothing: the span's source
  units are in the alignment file and align to no target token.
- **`null`** — the question could not be answered: the source ids are not in the alignment file at
  all.

That is the whole of it. An earlier draft called R7's Psalm title *"a third kind of nothing"*; it
is not one. Where a psalm has a title, the text field is full and the title field is full — nothing
is absent, so there is no nothing to report. Corrected 2026-09-14 when the Captain asked whether
R11 was compatible with the rule.

**Where a nothing does arise, and what it must be.** R7's title field applies wherever a span
covers the source verse holding a superscription, and the target has a verse `000` only for 116 of
150 psalms — never outside Psalms. So the field is often empty, and it must then be **`null` and
present**, never omitted: no request list governs it, it appears on the strength of the data, and
the rule permits omission only *"where another declaration explains the absence"*.

**Why R16 and R9 may omit and R7 may not.** `alignments` and `correspondence` are absent when not
asked for, and that is legal precisely because `returns:` and `correspondence:` **are** request
lists — the exemption the rule names. The title has no such declaration behind it. This is the
distinction that makes one omission fine and the other a defect.

**R12 — a span says whether its tokens are contiguous.** Captain, 2026-09-14, answering D5. One
boolean per span: true when, in every verse the span draws from, nothing between its first and last
token belongs to a different source unit. It is true for about 99% of units — discourse-flow
measured 4 of 390 in Mark — and false exactly at the boundaries this step was built to serve, so
the field is cheap and its false case is the interesting one. A list of the offending tokens was
considered and not taken: the flag says which boundaries to distrust, which is what a consumer
acts on.

**R13 — all twenty pairs ship.** Captain, 2026-09-14, answering D6 once it was reframed around
cost. R2 already validates every pair against the alignment file's declared `documents` at read
time, which is precisely what catches a file misdescribing itself — the Hausa case. So a declared
pair costs one row, and a bad file fails loudly on first use rather than silently returning the
wrong language. The check we were building anyway is what makes breadth safe.

Ten languages: `arb`, `asm`, `ben`, `eng`, `fra`, `hau`, `hin`, `por`, `rus`, `spa`. Twenty pairs,
after R3 drops the duplicate `WLCM-OHCB`.

**One flagged, not resolved:** `por/JFA11` is `SBLGNT-JFA11-transfer`, not `-manual`. It is
machine-transferred rather than hand-aligned, which is a provenance difference a consumer may care
about. Whether the declaration records provenance per pair, and whether a transferred alignment is
served without comment, is not decided here.

**R14 — a discontinuous unit is representable in the aligned text, not only in the raw records.**
Captain, 2026-09-14, on discontinuous source groupings: *"this is pretty common in Greek"*, and
then *"we need to support it in aligned text, too."*

A record may group source units that are **not adjacent**, and that grouping is a claim the
aligners made: these separated words together render as this English. Greek does it routinely —
hyperbaton — and the measurements bear the Captain out:

| | source units of one record not adjacent | that record's target tokens not a contiguous run |
|---|---|---|
| `SBLGNT-BSB` | **1,238 of 5,664 — 22%** | 309 of 37,653 — 1% |
| `WLCM-BSB` | **1,361 of 14,547 — 9%** | 3,976 of 180,183 — 2% |

    source : ἐκ  (n40001006013, "out of")
             τοῦ (n40001006015, "-")
    target : "by"
    between: τῆς (n40001006014, "the [wife]"), which aligns elsewhere

So the aligned text must be able to say that ἐκ and τοῦ are one unit rendered *by*, with τῆς
belonging to something else in between.

**This removed a unit the AI had invented.** The worked examples had grouped source words into
"blocks" by a contiguity heuristic of the AI's, and called those the constituents. But the
alignment already has constituents — its records, which are the aligners' own claim about what
corresponds to what. The derived blocks absorbed the words a discontinuous record skips, closing
the very gap this ruling exists to show, and asserted groupings the file does not make. Removed
2026-09-14 at the Captain's direction: *"yes, we should undo this."* The worked examples now carry
one entry per record.

Trying and reverting a merge established the reason it could not be patched: blocks are coarser
than records, and a gap cannot survive a coarsening that fills it.

The two sides are not symmetric and should not be handled as though they were. The **source** side
is discontinuous often — 22% in Greek — because Greek word order is free. The **target** side
almost never is, 1–2%, because English word order is rigid.

**How discontinuity is written into the text output is not settled here.** A marker between runs, a
list of runs instead of one string, and a flag alongside the text are all open.

**R15 — a gap in a discontinuous unit is written with a marker in the phrase.** Captain,
2026-09-14, answering how R14 is represented. The source words of one unit are written together
with a marker where words belonging to something else were skipped:

    ἐκ … τοῦ  ↔  by

rather than split into two entries that each claim *by* and lose the fact that they are one unit.
The marker is a reading convention, not structure: it says a gap is there without saying how wide.
Structured runs were considered and not taken.

**R16 — the request takes a set: the alignments, the aligned text, or both.** Captain,
2026-09-14, answering D8 and then extending it: *"I should be able to get just the sb alignments,
the aligned text, or both."* Three legal requests, the same shape as R5's orderings and for the
same reason — they are complementary views of one span, not alternatives, and an either/or would
make a client call the step twice for one unit of work.

The **alignments** are the Scripture Burrito records themselves. The **aligned text** is what R1,
R5, R10 and R12 produce. Neither is derived from the other by the client: the records cannot be
rendered into text without the target token file and the spacing column, and the text cannot be
turned back into records at all.

The records are parsed already, so the cost is passing them through.

What they carry that nothing derived does: the **grouping** a record asserts, including the
discontinuous ones R14 is about; **per-record provenance** in `meta.origin` and `meta.status`,
which is uniform in `SBLGNT-BSB` but varies across the corpus since `por/JFA11` is `-transfer`; and
`meta.id`, a stable handle back into the published data.

R9's correspondence map is kept alongside both rather than replaced. It is strictly weaker — it cannot express grouping
or discontinuity — but it is the shape a consumer wanting per-word correspondence actually asks
for, and the raw records make it a convenience rather than the only view.

**The exposure this accepts, stated plainly:** the records are an upstream format we do not
control, so a `conformsTo` change at Clear reaches consumers directly instead of being absorbed
here. Three defects were filed against that repository on 2026-09-13, so this is not hypothetical.
It is opt-in partly for that reason.

---

## 3. What was measured, and how to re-derive it

All figures from `Clear/Alignments/data/eng/alignments/BSB/SBLGNT-BSB-manual.json` (115,008
records) against `data/eng/targets/BSB/nt_BSB.tsv` (201,136 tokens), 2026-09-13.

| fact | figure | why it matters |
|---|---|---|
| adjacent source-order steps running backward in target order | **17.0%** | alignment is not monotonic; a span's English is not a contiguous run |
| records whose source and target are not all in one verse | **80 / 115,008 (0.070%)** | alignment is verse-scoped; the exceptions look like versification divergences |
| spans that are one verse: tokens contiguous | **7,933 / 7,934 (100%)** | a span covering whole verses always is |
| spans from arbitrary word tiling: tokens contiguous | **~49%**, flat at 5/10/20/50/100 words | **an artifact of the harness, not of the data** — nobody tiles arbitrarily |
| target tokens aligned to no source word | **29,964 / 201,136 (15%)** | overwhelmingly punctuation; these are the unaligned tokens R1 includes |
| alignment target ids joining the target TSV | **171,172 / 171,172 (100%)** | the join is clean; no identifier reshaping needed |
| records with more than one source word | **5,664 / 115,008 (4.9%)** | the cause of genuinely shared tokens in §5 D1 |
| adjacent-span collisions under R1, 10-word spans | **1,575 / 12,229 (12.9%)** | down from 33% under whole-range, not zero |
| spans where source order disagrees with target order | **9,912 / 12,255 (81%)** | a consumer cannot recover word correspondence by position |
| spans where 2+ source words share an identical target set | **4,343 / 12,255 (35%)** | correspondence is many-to-many; one target token can belong to several source words |

### 3.1 Ordering — the fact a consumer will get wrong

Two separate questions get conflated, and they have different answers.

**Assembling readable target text works by sorting target ids.** Verified: the target TSV's file
order is exactly its sorted id order, and reconstructing Philemon 1:18–19 under R1 yields
*"But if he has wronged you in any way or owes you anything, charge it to my account. I, Paul,
write this with my own hand. I will repay it—not to mention that you owe me your very self"*.

**Recovering which target words correspond to which source word does not.** Source order does not
predict target order, in 81% of spans. The first two Greek words of that same span invert —
`57001018001` is *"if"*, `57001018002` is *"But"* — and three consecutive Greek words
(`…008`, `…009`, `…010`) each map to the whole phrase *"charge it to my account"*, so no token in
it belongs to any one of them.

The correspondence is a many-to-many graph. It cannot be derived from the assembled text, from
token position, or from source position, and a consumer that sorts and zips will be wrong in four
spans out of five. Whatever the step returns has to carry it explicitly or discard it explicitly —
`say-which-kind-of-nothing` applies.

Collisions under R1 decompose as: **886** where a target word genuinely aligns to source words in
both spans, **599** where only an unaligned token inside the span is shared, **90** both.

**Two defects in the upstream data**, filed against `Clear-Bible/Alignments` on 2026-09-13 and not
ours to fix: `hau/alignments/OHCB/WLCM-OHCB-manual.json` is byte-identical to its SBLGNT sibling
while its filename and TOML claim Hebrew/OT; and `data/catalog.tsv` is an orphaned Git LFS pointer
whose contents do not describe the tree. R2 and R3 exist because of these.

---

## 4. Proposed shape

A new step type, because an alignment step reads three resources — source text, target text and
alignment file — where `type: scripture` reads one. **Flags on a type, not methods**: settled in
#241, because an alignment return cannot stand alone (each needs a pair and spans to mean
anything), which is the test that decides between the two.

**Key names below are illustrative and are not ruled.** What is ruled is which choices exist.

```yaml
- name: english_for_segments
  type: alignment
  source: SBLGNT               # R4 — both named, never inferred; SB's own role names
  target: BSB                  # R4
  spans: ${segment_bounds}     # [{from: n57001018001, to: n57001019017}, ...]
  returns: [text]              # R16 — text | alignments | both.      default [text]
  order: [target]              # R5  — target | source | both.        default [target]
  correspondence: false        # R9  — opt-in
  outputs: segment_english
```

One result per span, in request order, so a `for-each` joins it to the `type: scripture` result for
the same spans without matching on anything.

**What one result carries**, by ruling:

| field | ruling | when |
|---|---|---|
| the assembled text | R1, R5, R10, R12 | when `returns` includes text |
| the same text in source order | R5 | when `order` includes source |
| whether the tokens are contiguous | R12 | always, with text |
| the Scripture Burrito records | R16 | when `returns` includes alignments |
| source-unit → target-token map | R9 | when `correspondence` is true |
| the target-side title | R7 | only where the target has a verse `000` |

**Three kinds of nothing** (R11): an empty collection where the question was asked and nothing
aligned; `null` where the source ids are not in the alignment file; a separately named field where
the target has the text but outside the alignment's reach.

`source` and `target` are checked against the alignment file's declared `documents` and `roles`
(R2). A mismatch is a loud error, which is what catches the Hausa file.

---

## 5. Decisions for the Captain

### D1 — who gets a target word that aligns into two spans

886 cases at 10-word spans, plus 90 more where an unaligned token inside the span is also shared. A single English
word is aligned to source words that fall in two different spans; 4.9% of records name more than
one source word, which is how this arises. Options: give it to both spans (the English appears
twice); give it to the earlier span; give it to the span holding more of its source words; or
return it in both and mark it shared so the consumer decides.

This is about meaning rather than mechanism, which is why it is not proposed here.

=> *"both spans get it"*, refined the same day to *"the target word order tells us what span to put it in"* and *"but a constituent list should show it both places"* — Captain, 2026-09-13. In the span **text** no token appears in two spans, decided by target order; the **constituent list** shows the word in both. Recorded as **R8**.

### D2 — how far the unaligned tokens inside a span reach

R1 includes the unaligned tokens "between" a span's aligned tokens. Two readings. **Range:** take any
unaligned token between the span's lowest and highest aligned id — simple, and produces the 599
such collisions. **Interior:** take an unaligned token only where the nearest aligned
token on each side belongs to this span — removes those 599, costs a little more work per span,
and drops trailing punctuation where a token belonging to a different source unit intervenes.

=> Reach outward over unaligned runs at both ends, stopping at a neighbour — Captain, 2026-09-14.
Recorded as **R10**.

### D3 — what the step returns

Raised by the Captain, 2026-09-13: *"when it gets the aligned tokens, it still needs to figure out
what part of the BSB correspond to the Hebrew or Greek. and sorting the English by word order only
works if the word order increases monotonically — not always a given."* §3.1 measures it: 81% of
spans invert, so this is the normal case rather than an edge.

Three candidates, and they are cumulative rather than exclusive.

**Text.** The assembled target string, ordered by target id, spaced with `skip_space_after`. The
engine can do this correctly and a caller cannot, because the spacing column is ours to read. This
is what was asked for.

**Token ids.** The ordered list behind the text, so a consumer can re-cut without re-deriving.

**Correspondence.** A map from each source word id to the target token ids it aligns to — the
thing §3.1 shows is unrecoverable downstream. Without it a consumer either does not attempt word
correspondence, or attempts it by position and is wrong four times in five. With it, the
many-to-many case is visible: three source words each carrying the same five target ids says
plainly that no one of them owns a token.

The question is which of the three ship, and whether correspondence is always present or requested.
Note that it is the expensive one in payload terms, and that a per-word map keyed by source id is
the shape `verses-are-milestones` and the 2026-09-10 word-addressing ruling already established
elsewhere in this engine.

=> *"by default, no, but provide an option that does for debugging and transparency"* — Captain,
2026-09-13, on **correspondence**. Recorded as **R9**. This answers whether the map is default or
requested; it does not settle whether the **token ids** ship alongside the text by default, which
is still open and is the smaller half of this decision.

### D4 — how a span with no alignment reports itself

`say-which-kind-of-nothing` requires the two cases be distinguishable: a span whose source words
exist but align to no target token, versus a span whose source ids are not in the alignment file
at all. Proposal is an empty collection for the first and `null` for the second, with the reason
named. Confirm or replace.

=> Empty collection and `null`, told apart per `say-which-kind-of-nothing` — Captain,
2026-09-14. Recorded as **R11**. A third "kind" the AI had listed was a populated field, not a
nothing, and was removed when the Captain checked R11 against the rule.

### D5 — whether the step reports that a span's tokens are not contiguous

**The question had to be restated, because it was asked in a word that has since been retired.**
Captain, 2026-09-14: *"crossing a verse boundary is not interleaved"*, and then *"don't use the
term interleaved at all."*

A span's target tokens in a verse fail to be contiguous when a token it covers belongs to a
different source unit. That
happens **only where a span opens or closes inside a verse**. A span covering several verses is not
affected — it covers tokens in each verse separately (R6), and each stretch is contiguous on its
own.

The earlier wording here would have fired on every multi-verse span, which is the ordinary case,
making the signal useless. The figure was stale too: this section carried **~50%**, which §3
withdrew as an artifact of arbitrary word tiling. Measured properly, discourse-flow found 4 of 390
units in Mark, about **1%**, and in all four worked examples the tokens are contiguous in every
verse.

So: should a span carry a signal for that 1%, and if so is it a boolean, or the list of tokens
it covers without belonging to it?

=> A boolean — Captain, 2026-09-14. Recorded as **R12**.

### D6 — which pairs ship first

The tree holds 20 usable pairs across 10 languages after R3. Shipping all of them means declaring
20 rows we cannot each verify. Shipping `SBLGNT-BSB` and `WLCM-BSB` covers both known consumers
and is testable. Name the set.

=> All twenty pairs; R2's read-time check makes declaring one nearly free and
catches a file that misdescribes itself — Captain, 2026-09-14. Recorded as **R13**.

### D7 — target content the span cannot reach: Psalm titles at verse 000

Found 2026-09-13 while working Psalm 23:1–4, and it is a class rather than a case.

The Hebrew superscription מִזְמוֹר לְדָוִד is part of Hebrew verse 1. BSB renders it as a psalm
title and the target file carries that title as tokens numbered **verse 000** —
`19023000001`–`005`, reading *A Psalm of David*. Neither side is aligned to the other: the three
Hebrew morphemes report as aligning to nothing, and the English sits in the file claimed by nobody.

Because a span's bounds start at the first *aligned* token of a verse, the span covers no tokens
in verse 000 at all and the title falls outside. The title
is dropped with no signal — content present in both texts that the operation cannot reach.

**116 of the 150 psalms carry a verse-000 title, 1,303 tokens in all**, and verse 000 appears in no
other book of the Old Testament. The Captain, 2026-09-13: *"BSB uses a title for the first half of
Psalm 23:1. so that part has to be missing or drawn from the title, which is not aligned"*, and
*"this is common in English translations of Psalms."*

Options: leave verse 000 out and say so in the result rather than silently; include it whenever the
span covers the Hebrew verse that contains the superscription; or treat it as a separate named
field so a caller can use it or ignore it. Note this interacts with D4 — a source unit reporting
"aligns to nothing" here means "the target has this, somewhere the alignment does not go", which is
a third kind of nothing the current two do not distinguish.

**Feasibility measured before deciding.** Verse 000 cannot carry a general mechanism: it is a
per-translation artifact (BSB **116** of 150 psalms, YLT **11**), the Hebrew source uses it
**never**, and **no verse-000 token is aligned anywhere** in the Hebrew–BSB corpus. It appears in
no book but Psalms.

=> *"that works"* — Captain, 2026-09-13, ruling for the narrow target-side option and against
verse 000 as a general mechanism. Recorded as **R7**.

---

### D8 — whether a client can ask for the raw alignment records

Raised by the Captain, 2026-09-14: *"can a client also get the raw sb alignments?"*

R9 makes the **correspondence map** opt-in, but that map is a reshaping of ours: source id → target
token ids. The Scripture Burrito records are the file's own, and they carry three things the map
cannot express.

**Grouping.** A record pairs a *set* of source units with a *set* of target tokens, and that
grouping is the aligners' claim about what corresponds to what. Flattening it to one entry per
source id asserts each separately and loses the unit. 5,664 records group two or more source units,
and **1,240 of those — 22% — group source words that are not adjacent**:

    source : ἐκ  (n40001006013, "out of")
             τοῦ (n40001006015, "-")
    target : "by"
    between: τῆς (n40001006014, "the [wife]"), which aligns elsewhere

ἐκ and τοῦ jointly render as *by*, discontinuously. The map states two independent facts and cannot
say they are one unit, nor that the unit has a hole in it.

**Per-record provenance.** Each record carries `meta: {id, origin, status}`. In `SBLGNT-BSB` every
record is `manual`/`created`, so it looks redundant — but `por/JFA11` is `-transfer`, so origin
varies across the corpus, and a client weighing whether to trust an alignment may want it per
record rather than per file.

**A stable record id.** `meta.id` is a handle back into the published data, which nothing we derive
provides.

Cost is near zero: the records are parsed already, so this is a matter of whether to pass them
through, and under what key. Against: it is the largest payload of anything the step can return,
and it exposes an upstream format we do not control — a `conformsTo` change upstream would reach
consumers directly rather than being absorbed by us.

Note this interacts with R9: if the raw records are available, the correspondence map is a
convenience over them rather than the only way to see correspondence, and whether both are needed
is part of this decision.

=> Yes — and as a set: *"I should be able to get just the sb alignments, the aligned text, or
both."* Captain, 2026-09-14. Recorded as **R16**; R9's map is kept alongside rather than replaced.


## 6. Work, in order

1. **`data/alignment-pairs.json`** — the declaration R2 requires, twenty pairs per R13. Blocked on
   D9: whether it records identifier form and provenance.
2. **Failing tests first.** One per ruling that can fail silently: unaligned tokens inside a span
   kept (R10, both ends — the `wordTherefore` and `In Him` cases); a span crossing verses (R6); a
   span whose tokens are not contiguous (R12); a discontinuous record surviving with its gap
   (R14, R15, both sides); a `from`/`to` mismatch against `documents` (R2); the three kinds of
   nothing (R11); Portuguese returning something rather than silently nothing (D9).
3. **The reader** — alignment file, target TSV, source TSV. Identifier normalisation on read is a
   precondition, not a refinement; see D9.
4. **The step handler and its schema entry**, with the flags §4 lists.
5. **`docs/llmflow-language.md`** — the new step, and the two stale `include`/`format: usj` claims
   at lines 802 and 961, which `3ca7139` made false.
6. **Tell discourse-flow**, closing the reply promised in `project/TODO.md`.

## 7. Separate deliverable

Fixing `data/catalog.tsv` on the local `dev` branch in `Clear/Alignments`, per R3. This is a
contribution to offer upstream, not something the engine reads — R2 settles that. That branch has
no upstream today.
