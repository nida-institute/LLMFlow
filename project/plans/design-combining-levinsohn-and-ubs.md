# Design — combining Levinsohn and UBS into one quotation record

**Status:** proposed — **not authorization to build.** The design is stated in §6 as seven positions,
each with the rule or ruling it follows from, and **one** `=>` for correcting them. It held seven
option menus until 2026-09-02, when the Captain named the pattern: *"LLMs making assumptions and
asking me to make detailed decisions about those assumptions."*

**One question in §6 is genuinely his** — whether UBS's source attribution is complete for
composite quotations. It is a question about the data, not a design choice.

**This is one feature, in four parts, ruled so by the Captain on 2026-09-02:** *"j-m are all
aspects of the same single feature."* Those four parts, and their order is not a preference:

1. **the engine keeps both ends of a Levinsohn span** — §2, and the **span ends** position in §6. Nothing else can
   proceed without it, because a combined record cannot carry an extent that was discarded before
   it was built.
2. **the combined record** — Levinsohn's span joined to UBS's source. §3 to §5.
3. **the reply to the discourse project's report of 2026-09-01**, on references being shortened.
4. **the reply to their report of 2026-09-02**, which is what prompted this document.

Tracked as four items they read as four choices. They are one piece of work whose last two parts
are telling the people who reported it what was decided.

**The Captain has stated this feature is time-sensitive** (2026-09-02, of the Old Testament
references). No date has been given, and none is assumed here.

Origin, the Captain 2026-09-02: *"Ideally, I would like to be able to combine Levinsohn & UBS to
provide one result with more complete information."* And: *"that probably requires a design
document."*

Prompted by `collab/discourse-flow/2026-09-02-carrying-source-annotations.md`, which asks three
questions — is there a mechanism for carrying source-anchored annotation to output without a model
in the path (§4a), does anything preserve a word-level span through a structural transform (§4b),
and does a quotation dataset exist in the `sp` data layer already (§4c). This document answers 4b
and 4c as measurements, and proposes what 4a would be.

---

## 1. The two datasets, and why neither alone is enough

Both describe Old Testament quotations in the New Testament. They describe different halves of the
same fact, and neither can be derived from the other.

**Levinsohn's LGNTDF** (`biblicalhumanities/levinsohn/LGNTDF/OT_quotes.xml`, ©2016 SIL
International) says **exactly which words** are the quotation:

```xml
<reference osisRef="Mark.1.2!9-Mark.1.2!15" type="OT quotes" label="" verse="Mark 1:2"
           >ἀποστέλλω τὸν ἄγγελόν μου πρὸ προσώπου σου</reference>
```

Words 9 through 15 of Mark 1:2, with the Greek quoted so the index can be checked. What it never
says is **what is being quoted**: the `label` attribute is where a source would go, and it is empty
on all 691 references without exception — one distinct value across the whole file.

**UBS Parallel Passages** (`ubsicap/ubs-open-license/parallel passages/ParallelPassages.xml`,
CC BY-SA 4.0, © 2023 United Bible Societies) says **what is being quoted**, and grades each word:

```xml
<Passage>
  <Verse HEB="221222412111300000003000000030030000">MAL 3:1</Verse>
  <Verse GRK="222225222222225222222">MAT 11:10</Verse>
  <Verse GRK="12000005222222252222">MRK 1:2</Verse>
  <Verse GRK="22222522222225222222">LUK 7:27</Verse>
</Passage>
```

One digit per word: `0` no match, `1` partial match, `2` full match (`3`–`5` and `6`–`8` repeat
`0`–`2` while also suggesting one or two line breaks, which is presentation only). What it never
gives is an explicit span — the extent must be read off runs of non-zero digits.

**So the complementarity is exact:**

| | Levinsohn | UBS |
|---|---|---|
| which words | **stated as a span** | derivable from digit runs |
| what is quoted | **never** | **stated** |
| per-word match quality | no | **yes** |
| synoptic parallels | no | **yes** — 760 groups with no OT verse |
| Greek text quoted inline | **yes** | no |

For Mark 1:2 the UBS digits are worth reading closely, because they demonstrate that the grading is
real analysis and not a gloss-free restatement:

| word | Greek | digit | |
|---|---|---|---|
| 1–2 | Καθὼς γέγραπται | `1 2` | |
| 3–7 | ἐν τῷ Ἠσαΐᾳ τῷ προφήτῃ | `0 0 0 0 0` | **no match in Malachi** — Mark's own attribution |
| 8 | Ἰδοὺ | `5` | full match, opens a line |
| 9–15 | ἀποστέλλω … σου | `2 2 2 2 2 2 2` | full match |
| 16 | ὃς | `5` | full match, opens a line |
| 17–20 | κατασκευάσει τὴν ὁδόν σου | `2 2 2 2` | full match |

The two line-break digits fall on `Ἰδοὺ` and `ὃς` — precisely the openings of Levinsohn's two spans
`!9-!15` and `!16-!19`. Two independently produced datasets agreeing on where the quotation breaks
is the strongest evidence available that a join is meaningful rather than merely arithmetic.

---

## 2. What the engine already does, and the one thing it throws away

**§4c is already partly answered: the engine reads Levinsohn today.** `include: [discourse]`
(`src/llmflow/utils/scripture.py:82`) attaches Levinsohn items to a passage through
`src/llmflow/utils/discourse.py`, and `load_citations` reads *every* LGNTDF feature file in the
directory — so `OT_quotes.xml` is already being loaded, already reconciled against the Greek, and
already emitting a word identifier. No model is in that path. It is deterministic, and
`resolve_citation` reports what it established through an eight-value `Outcome`: verified,
disagrees, rescued, ambiguous, not_found, unverifiable, out_of_range, anchored.

That is most of the mechanism §4a asks for, and it is worth saying plainly to the reporting
project: they are asking for something that largely exists.

**But the span end is discarded, by design and in writing.** `parse_osis_ref` documents it at
`discourse.py:111-112` — *"A range reference keeps its opening: only that end is the citation"* —
because `OSIS_REF` (`discourse.py:38`) is anchored at the start and matches one index. So
`Mark.1.2!9-Mark.1.2!15` becomes index **9**, and *through 15* is gone.

**This is not a quotation problem. It is engine-wide.** Measured across every LGNTDF feature file
the engine loads:

| | |
|---|---|
| references loaded in total | **52,257** |
| of those, single-word anchors | 38,504 |
| of those, **spans whose end the engine drops** | **13,753** |
| words sitting inside a dropped extent | **82,574** |
| spans that cross a verse boundary | 657 |
| references the parser fails on | 0 |

Twenty-six of the thirty-three feature types carry spans. The largest are `Focus+` (2,753),
`Referential PoD` (2,066) and `Reported Speech` (2,050); `OT quotes` is 655 spans plus 36
single-word anchors.

**So the answer to §4b is: no.** Nothing in the engine preserves a word-level span through a
structural transform, and the loss is 13,753 spans rather than the 47 the reporting project
measured in Mark. Their pipeline loses spans through an LLM; the engine loses them before the LLM
is reached. Fixing only the former would still leave every span truncated to its first word.

**This is the same defect shape as decision 7 on the ruling sheet.** `parse_bible_reference` narrows `1JN 2:5b-6` to
one verse by matching a prefix; `parse_osis_ref` narrows `!9-!15` to one word by matching a prefix.
Two parsers, both silently keeping the opening of a range, both contradicting
`project/overview.md`: *"the engine prefers a loud error to a plausible result."* Whatever is ruled
for one bears on the other: decision 7 is the ruling sheet's one genuinely open decision, and the
**span ends** position in §6 is the same shape of choice already derived.

---

## 3. Does the join actually work? The measurement

The join has one serious failure mode. Levinsohn numbers SBLGNT `<w>` elements; UBS numbers
space-separated UBSGNT5 words. **If those two word counts ever disagree, a word-index join
silently corrupts** — and silent corruption of a reference is the failure this project's rules
exist to prevent.

There is a cheap one-sided test. If Levinsohn's highest word index for a verse **exceeds** UBS's
digit count for that verse, the two disagree, provably. Across the 266 NT verses where both
datasets give word-level data on a single verse (ranges excluded):

| | |
|---|---|
| Levinsohn's highest index **equals** UBS's digit count | **207** |
| Levinsohn's highest index **below** it (quote ends before verse end) | 59 |
| Levinsohn's highest index **exceeds** it — proof of misalignment | **0** |

Zero counterexamples in 266 attempts. That is not proof of alignment — the test cannot detect a
compensating pair of differences, and it says nothing about the 59 — but a join with no
counterexample in 266 verses is worth designing, and the test itself is worth keeping as a guard.

**Coverage.** Neither dataset is a superset of the other, which is the substantive case for
combining them rather than choosing one:

| | |
|---|---|
| UBS passage groups in total | 2,193 |
| of those, OT-and-NT (a quotation) | 249 |
| OT-only (parallels inside the OT) | 1,184 |
| NT-only (synoptic parallels) | 760 |
| distinct NT verses — Levinsohn | 367 |
| distinct NT verses — UBS with an OT source | 340 |
| **in both** | **291** |
| **Levinsohn only** | **76** |
| **UBS only** | **49** |

**Treat 340 / 291 / 49 as approximate.** 647 UBS verse references are ranges (`MAT 3:1-2`) whose
digit string spans two verses; the coverage figures collapse those to the first verse, and the
alignment test excluded them entirely. What a range means on the UBS side is the **UBS verse ranges** position in §6.

Every figure here is reproducible from the two files with `lxml` and no network access.

---

## 4. What a combined record would carry

A record per quotation, not per verse. Naming the fields is a design choice, so this is shape
rather than schema:

```
NT location      MRK 1:2, words 9-15          Levinsohn span, both ends
Greek            ἀποστέλλω τὸν ἄγγελόν μου…   Levinsohn text
word ids         the xml:id of each word      engine, via resolve_citation
OT source        MAL 3:1                      UBS
match quality    per word: full / partial     UBS digits
outcome          verified | disagrees | …     engine, existing Outcome enum
```

Four constraints from the project's own rules bear on this and should be settled before anything is
built, not discovered afterwards:

**`verses-are-milestones`.** A verse-keyed structure must be a mapping keyed by verse identifier,
never a list of verse objects — a list invites a model to treat the verse as the unit. That is a
live risk here: the natural shape for "quotations in this passage" is a list, and the natural shape
for "what is in verse 3" is a mapping. Both are needed and they must not be the same structure.

**`reference-data-is-json`.** If the combined data is written to a file, it is JSON. PyYAML reads a
bare `1:1` as the integer `61` and `NO` as `False`, silently, and a coerced verse number is
plausible enough to survive review. This rule exists because of exactly this kind of file.

**`design-is-declarative`.** The join rules — which dataset governs extent, what a missing source
means, how a UBS range is read — should be stated once as data that the code reads, not encoded a
second time in logic. Two encodings of one fact agree until they quietly do not.

**`no-italics-in-non-italic-scripts`.** The OT side of every UBS record is Hebrew. Anything that
renders these records must never italicise it. Greek is unaffected; Hebrew is not, and pointed
Hebrew becomes unreadable when slanted. This applies to templates and stylesheets that *could*
carry such text, not only ones that do today.

---

## 5. What this cannot deliver, stated so it is not assumed

**Composite quotations stay incomplete.** Mark 1:2 is conventionally read as Exodus 23:20 fused
with Malachi 3:1. `EXO 23:20` appears **nowhere** in the UBS file — the string is absent entirely.
UBS gives one OT source per group, so the combined record for Mark 1:2 will name Malachi and stop.
A reader who assumes the record is the complete set of sources will be wrong, and the record must
say so rather than leaving the assumption available — the **a source the data lacks** position in
§6, and the one question in §6 that is the Captain's.

**The extents disagree in places.** UBS grades words 8–20 of Mark 1:2 as matching Malachi,
including `Ἰδοὺ` and the final `σου`; Levinsohn's spans are 9–15 and 16–19, excluding both. Neither
is wrong — they answer different questions, one "what is the quotation" and one "which words
match" — but a merged record needs one rule, which is the **extent** position in §6.

**Neither dataset covers the Old Testament in Hebrew or the Septuagint as texts.** UBS's OT side is
a reference plus digits against BHS or, where the NT quotes the LXX, against the LXX. Making that
text available is separate work and is not proposed here.

---

## 6. The design, and what each position follows from

The Captain, 2026-09-02: *"drift drift drift ... LLMs making assumptions and asking me to make
detailed decisions about those assumptions."*

This section held **seven option menus of the author's construction**. Every one is answerable from
a rule or a ruling already given, so each is now stated as a position together with the thing it
follows from, and there is **one** `=>` at the end rather than seven.

A derived position can be wrong, and saying so is welcome. What it cannot be is authority —
nothing here is built until the Captain says to build it.

| | the position | what it follows from |
|---|---|---|
| **span ends** | The engine carries **both** ends of a Levinsohn span. | Today it produces a plausible wrong answer — a seven-word feature is indistinguishable from a one-word feature — which `project/overview.md` names as the failure to design against. Carrying ends for some features only would put two shapes in one payload, which `one-design` forbids. Leaving it leaves every consumer parsing LGNTDF themselves, which is what #169 exists to end. |
| **where it lives** | Mechanism here. The join, and the two dataset names, in the resource layer. | The Captain's ruling of 2026-09-01: the engine gains mechanism, not knowledge of particular resources. This was *also* decision 14 on the ruling sheet — one question in two places, which `design-is-declarative` calls the defect itself. It is answered, and is not asked again. |
| **UBS verse ranges** | Ranged records are carried whole and marked as covering a range. No per-word grades are produced for them. | 647 references are ranges whose digits run across two verses. Splitting them on assumed word counts would yield per-word grades that may be off by a verse — a plausible wrong result, ruled out by the same sentence. |
| **extent** | Levinsohn governs extent. UBS supplies the source and the grading. | Levinsohn *states* extent; UBS's extent is *inferred* from runs of digits. Preferring an inferred value where an explicit one exists is strictly worse. Carrying both would hand the disagreement to every consumer. |
| **a source the data lacks** | The record states that it names attested sources, not necessarily all of them. | `project/overview.md` — where it cannot be certain, the engine says what it found rather than choosing. Adding missing sources by hand would make this engine a place where scholarship is authored, which `ask-about-the-data` puts outside its remit. |
| **match quality** | Carried per word, as UBS gives it. | The engine's payloads are already per word. Pre-aggregating discards the very thing that separates a verbatim quotation from a loose allusion. |
| **synoptic parallels** | Out of scope. | Not what was asked for; widening the request is the drift pattern *The Helpful Addition*. Recorded in §8. |

### One thing here is genuinely the Captain's — and it is a fact, not a preference

Mark 1:2 is conventionally read as Exodus 23:20 fused with Malachi 3:1. UBS names only Malachi, and
`EXO 23:20` appears nowhere in its file.

**Is UBS's attribution incomplete for composite quotations generally, or is Malachi the whole of it
here?**

`ask-about-the-data` puts that in the Captain's domain, and it is asked rather than assumed because
a guess about what data means is indistinguishable from knowledge once it reaches output. It changes
what the record may honestly claim, not how the record is built.

### Anything above wrong?

=>

## 7. Where each position gets built, once the Captain says to build it

| the position | where it lands |
|---|---|
| **span ends** | `src/llmflow/utils/discourse.py` and its tests. `docs/ai-context/sp/scripture-representations.md` describes the payload, so amending it needs the Captain's per-file permission |
| **where it lives** | already ruled — mechanism here, the join in the resource layer described by `design-biblical-text-conventions.md` (#226) |
| **ranges, extent, missing sources, match quality** | the combined record, wherever the **where it lives** position puts it |
| **synoptic parallels** | nowhere; §8 |

**Nothing here is built.** No code has been written, no dataset has been built, and no reply has
been sent to discourse-flow.

## 8. Out of scope, stated so it is not inferred

- **Fixing discourse-flow's own pipeline.** They report the LLM restatement as theirs and
  explicitly do not ask us to fix it.
- **Loading the Old Testament text**, Hebrew or Septuagint, as a readable edition.
- **The other datasets in `ubs-open-license`** — `HOTTP`, `ubs-bible-routes`, `dictionaries`,
  `flora-fauna-realia`. Present in the same repository; not surveyed.
- **Synoptic parallels** — the 760 New Testament groups, per the **synoptic parallels** position in §6.
- **Attribution and licence mechanics.** The UBS data is CC BY-SA 4.0, which is a share-alike
  licence and therefore a constraint on anything derived from it. Decision 3 on the ruling sheet is
  the general form of this question and should settle it, not this document.
