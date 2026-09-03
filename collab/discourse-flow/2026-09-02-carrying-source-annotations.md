# Given data with word-level spans is reaching our output through an LLM, and losing a quarter of itself

**From:** an AI session in `nida-institute/discourse-flow`, 2026-09-02.
**Status: drafted by the AI, pending the Captain's review.**

This is the same theme as `2026-09-01-verse-reference-handling.md` — word spans versus verse
granularity — arriving from a different direction. That note asked where verse ordering belongs.
This one asks whether the engine has, or should have, a way to carry **source-anchored
annotations** to output without a model in the path.

## 1. The data

Levinsohn's LGNTDF ships `OT_quotes.xml`: **691 references**, one per Old Testament quotation in
the NT. Each is exact:

```xml
<reference osisRef="Mark.1.2!9-Mark.1.2!15" type="OT quotes" verse="Mark 1:2"
           label="">ἀποστέλλω τὸν ἄγγελόν μου πρὸ προσώπου σου</reference>
```

Greek text, NT verse, and a **word-level span** — `!9-!15`, words 9 through 15 of Mark 1:2. Which
words constitute the quotation is not a judgement; it is stated.

Mark 1:2-3 carries five of them:

```
1:2   ἀποστέλλω τὸν ἄγγελόν μου πρὸ προσώπου σου      (Mark.1.2!9-!15)
1:2   ὃς κατασκευάσει τὴν ὁδόν                        (Mark.1.2!16-!19)
1:3   φωνὴ βοῶντος ἐν τῇ ἐρήμῳ                        (Mark.1.3!1-!5)
1:3   ἑτοιμάσατε τὴν ὁδὸν κυρίου                      (Mark.1.3!6-!9)
1:3   εὐθείας ποιεῖτε τὰς τρίβους                     (Mark.1.3!10-!13)
```

## 2. What our pipeline does with them

They are handed to an LLM inside a window of annotated text, and come back as free-text entries
in a `levinsohn_features` array. For the segment covering Mark 1:1-3, the shipped output carries
**one** of the five:

```
"OT quotes: 'ἀποστέλλω τὸν ἄγγελόν μου πρὸ προσώπου σου' (1:2) — citation of prophecy"
```

Measured against the source, on a full Mark run completed today:

| | Levinsohn | our output |
|---|---|---|
| OT quotations in Mark | 47 | **35** |
| verses where fewer are emitted than exist | — | **11** |
| verses where *more* are emitted than exist | — | 2 (12:10, 12:11) |
| word-level spans carried through | 47 | **0** |
| entries abbreviated with an ellipsis | 0 | 2 |

The ellipsis case, which our own prompt checklist forbids:

```
"OT quotes: 'ἵνα βλέποντες βλέπωσι ... μήποτε ἐπιστρέψωσιν καὶ ἀφεθῇ αὐτοῖς' (4:12)"
```

`Mark.4.12!5-!11` becomes `(4:12)`. The `— citation of prophecy` half is model commentary
appended to given data, indistinguishable in the output from the data itself.

**This is ours to fix and we are not asking you to fix it.** We report it because it is the
evidence for the question in §4: every one of Levinsohn's 33 feature types reaches output this
way, as a composite string produced by a model restating data it was given.

## 3. What is *not* a defect, checked before claiming it

The Captain asked whether Malachi — credited alongside Isaiah for Mark 1:2 in most Bible editions
— survives our pipeline. It does not, and nothing dropped it:

| where | Isaiah | Malachi |
|---|---|---|
| Mark's Greek text | named: *ἐν τῷ Ἠσαΐᾳ τῷ προφήτῃ* | not named |
| SBLGNT XML as we ingest it | that text only | absent |
| Levinsohn `OT_quotes.xml` | `label=""` on all 691 | absent |
| our annotated USJ | only as Macula's gloss on the word Ἠσαΐᾳ | absent |

SBLGNT's `Mark.xml` contains exactly seven element types — `book`, `title`, `p`,
`verse-number`, `w`, `suffix`, `prefix`. **No `note` elements and no cross-references at all**;
zero occurrences of "Mal", "Isa" or "40:3" in the file. The quotation-source attribution is
scholarship, and Mark himself attributes the composite citation to Isaiah alone.

So a quotation-source reference cannot come from any input we currently load. Whether to load one
is a data decision for the Captain, not a pipeline question.

## 4. The questions for you

**4a. Is there an engine mechanism for carrying source-anchored annotation to output without a
model in the path?** What we want for these 691 is arithmetic: a span either falls inside a
structural unit or it does not. We already resolve Levinsohn's word indices deterministically in
`plugins/reference_resolution.py` — 51,699 of 51,722 NT-wide — so the machinery for *locating*
them exists on our side. What we lack is a declared way to say "these annotations belong to this
unit, carried verbatim", as opposed to passing them through a prompt and hoping.

If that is a plugin's job, say so and we will build it and stop asking. If `type: scripture`,
milestones, or the anchored-note work from our #88 already covers it, we would rather use yours.

**4b. Does anything in the engine preserve a word-level span through a structural transform?**
The previous note reported that `parse_bible_reference` narrows `1JN 2:5b-6` to `1 John 2:5`
silently. This is the same edge from the other side: our units are verse-bounded, the annotations
are word-bounded, and every transform between them is lossy. If the engine's reference model has
a word-span representation we should be using, we are using the wrong thing.

**4c. Do you have, or plan, a cross-reference or OT-quotation dataset?** Not asking you to build
one. Asking whether one exists in the `sp` data layer that we should load rather than sourcing
separately — the same question our #64 asks internally about approved datasets.

## 5. Re-derivation

Both figures above come from a single command over the shipped artifact and the LGNTDF source.
It is recorded with the numbers in our `project/measurements.md` under "Levinsohn OT quotations,
source against output". Nothing here is quoted from memory or from a prior session.
