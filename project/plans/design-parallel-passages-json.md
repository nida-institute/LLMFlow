# A JSON form for the UBS Parallel Passages database

**Status:** proposed (2026-09-27)

`proposed` is thinking aloud and is **not authorization to build**. D1–D6 are ruled. **Two
questions are open**, each marked with a bare `=>`: whether `counted_in` is a closed set (under
D3), and D7 — the shape that carries both verse numbers. The document's own status is the
Captain's to change, and has not been changed.

**What this is.** A design for presenting the UBS Parallel Passages database as JSON that says
what it means. Its source format packs a semantic claim and a layout instruction into one
character; this prises the two apart, keeps the semantics, and discards the layout (ruled, D2).

**What this is not.** It does not unblock `returns: [words]` on `type: parallel-passages`. That
is blocked on the MARBLE identifier join (#258, open questions 1 and 2), and nothing here
touches it. This document designs a *shape*; it does not solve *which word a score belongs to*.
A reader who takes this as licence to ship word-level scores by counting positions will be
wrong about one row in eleven, silently — which is the measurement that caused `words` to be
refused rather than approximated in the first place.

---

## 1. What is wrong with the source format

The database is `parallel passages/ParallelPassages.xml` in `ubsicap/ubs-open-license`,
CC BY-SA 4.0. Its entire vocabulary is three elements and two attributes:

```
Passages → Passage → Verse    attribute HEB= or GRK=, text is the reference
```

2,193 groups over 5,266 verse rows. There is no schema of any kind in that repository — no
`.xsd`, `.dtd`, `.rng` or `.rnc` — and no version field. The format is defined by three
worked examples in a 54-line README.

Five defects, in the order they bite:

**A single character carries two unrelated facts.** A score digit decomposes arithmetically:
`digit % 3` is the match strength (0 none, 1 partial, 2 full) and `digit // 3` is the number
of line breaks to insert before that word. So `5` means "full match, and start a new line
here". This is the conflation the present design exists to undo.

**The layout half is real structure, and is disclaimed.** In `LUK 11:2` the breaks fall on
`Πάτερ`, `ἁγιασθήτω` and `ἐλθέτω` — the openings of the prayer's cola. The source README
nonetheless calls the breaks *"purely for presentation purposes and … not in any intentional
way based on the published source texts"*, so the structural information demonstrably present
cannot be relied upon. It is either usable structure or it is not, and the format does not say
which.

**Scores are positional, with no identifier.** Digit *N* means word *N* of a text the file does
not ship and names only in an attribute. A digit string of the wrong length still parses and
still aligns, just against the wrong words.

**The attribute name misdescribes the one case that matters most.** In a group mixing Hebrew
and Greek members, the `HEB` row is counted against the *Septuagint* wording, not the Hebrew.
This is the source README's own statement, not an inference from the data: *"the actual text
that is quoted is from the Greek translation of the Hebrew text, the Septuagint (LXX). So the
numbering applies to the LXX words, not the Hebrew."*

**References are unparsed strings.** 647 rows carry a range and 10 carry a comma list.
`MRK 1:32,34` names two verses and not the one between them. A lookup keyed on string
equality misses a verse that sits inside a range row — quietly.

The source README also contains an arithmetic error worth knowing about before implementing
against it: it states *"The numbers 3-5 are equivalent to 0-3."* Three digits cannot be
equivalent to four; `0-2` is what the data shows.

---

## 2. Two orthogonal axes

The design has two independent dimensions, and the source format expresses neither explicitly.

| axis | scope | values |
|---|---|---|
| **match strength** | one word | `no_match`, `partial`, `full` — ruled, D1 |
| **relation kind** | one group | OT↔OT parallel, NT↔NT parallel, OT quoted in NT — a real axis, but **not a declared field**: ruled D3, it is read off `editions` |

They do not interact. A word scores the same way in a Genesis↔Chronicles parallel as in a
Septuagint quotation. Folding the digits and declaring the kind are therefore separate pieces
of work on separate fields, not alternatives — both are in scope here.

**What is constrained is the cross-product of relation kind against the text a member's scores
are counted in**, and the Hebrew/Greek split makes most of it impossible. Four cells of nine
occur:

| relation kind | attribute | scores counted in | members |
|---|---|---|---|
| `ot-parallel` | `HEB` | BHS | 2,522 |
| `nt-parallel` | `GRK` | UBSGNT5 | 2,101 |
| `quotation` | `GRK` | UBSGNT5 | 377 |
| `quotation` | `HEB` | **Rahlfs** | 266 |

The fourth row is the whole argument for making the index text an explicit field: it is the
only cell where the attribute name and the text actually counted disagree, and it is the cell
a consumer most wants.

Group counts by kind: `ot-parallel` 1,184, `nt-parallel` 760, `quotation` 249.

**A third independence, and the design should state it rather than let a reader infer it: group
membership does not depend on word matching.** 11 of 5,266 rows score `no_match` on every word
while their passages remain members of the group — `1KI 3:10`, `MRK 12:38-40`, `LUK 20:46-47`
and `MAT 23:14` among them, the last being a single word scoring `no_match` in a three-member
group. So the group relation is a passage-level claim and the scores are a word-level claim, and
a group is not the sum of its matches.

**One reading is inferred rather than declared.** In a group of three or more members — 494 of
2,193 — the value must mean "in none of the others". The source states that maximum-over-members
rule only for full matches: *"a word is marked as a full match if that match is found in at least
one of the other passages."* Nothing states it for partial versus none. The natural reading is
that the value is a maximum throughout, but that is inference from symmetry, and
`declared-not-inferred` says it travels as such until someone confirms it with UBS.

---

## 3. The proposed shape

One object per group; one object per member; the match array carries only match.

```json
{
  "source": {
    "name": "UBS Parallel Passages Database",
    "license": "CC BY-SA 4.0",
    "origin": "ubsicap/ubs-open-license — parallel passages/ParallelPassages.xml"
  },
  "groups": [
    {
      "editions": ["Rahlfs", "UBSGNT5"],
      "members": [
        {
          "reference": "GEN 1:27",
          "verses": ["GEN 1:27"],
          "counted_in": "Rahlfs",
          "match": ["no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "full", "full", "full", "full", "full"]
        },
        {
          "reference": "GEN 5:2",
          "verses": ["GEN 5:2"],
          "counted_in": "Rahlfs",
          "match": ["full", "full", "full", "full", "full", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match"]
        },
        {
          "reference": "MAT 19:4",
          "verses": ["MAT 19:4"],
          "counted_in": "UBSGNT5",
          "match": ["no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "no_match", "partial", "full", "full", "full", "full", "full", "full", "full"]
        },
        {
          "reference": "MRK 10:6",
          "verses": ["MRK 10:6"],
          "counted_in": "UBSGNT5",
          "match": ["full", "no_match", "full", "partial", "full", "full", "full", "full", "full"]
        }
      ]
    }
  ]
}
```

That is the second `Passage` element of the source file, converted. Its raw digit strings are
`0000003000052222`, `222223003000003000`, `0000300012252222` and `202152222`; the arrays above
were generated by `digit % 3` named through the enum, not transcribed by hand.

**The arrays are shown unabbreviated on purpose.** They are what the ruled shape actually looks
like, and eliding them would hide the one real cost of words over integers behind an ellipsis.
The whole database in this form is 796 KB against 182 KB as integers — see §5.

**What each field settles**

| field | why it exists |
|---|---|
| `editions` | The distinct texts this group's members are counted in — ruled D3, replacing `kind`. **Derived at conversion from the members' `counted_in` values, never authored**, so the two cannot disagree. A consumer wanting "is this a quotation" reads it from here. |
| `counted_in` | Names the text whose words the positions index — `BHS`, `Rahlfs` or `UBSGNT5`. Fixes in one field the trap where a `HEB` row is counted in Greek, rather than in a paragraph every consumer must read. **`Rahlfs` is the Captain's identification, not the source's**: UBS says only "the Septuagint (LXX)", once, and names no edition anywhere in its repository. The printing is unrecorded and stays unrecorded. |
| `verses` | The reference expanded. A range becomes its verses, a comma list becomes its two verses, so a lookup cannot miss a verse inside a row. `reference` keeps the source's own string so nothing is lost. |
| `match` | Match strength only, as the `Match` enum — ruled D1. The line-break component is discarded at conversion — ruled D2. The value is a **maximum over the other members**: it says how strongly this word corresponds to anything else in the group, never to which member. |

**Identity, and why there is no `id`.** A group's identity is its **ordered list of member
references** — ruled D4. Ordered rather than a set, because one group repeats a reference (§6),
and a set would silently collapse it. Nothing is minted: a consumer needing a key builds it from
data it already holds, and any id of ours would break on the next release of the database, which
is the one thing an id would exist to survive.

**Everything here is positional, and that is the whole contract.** A score is positional within
its member, and a member is positional within its group. So a score is a fact about a word *in
this group* and nowhere else — the same verse in another group carries different scores, and 207
`(edition, reference)` pairs actually do. There is no place in this shape to key scores by verse,
and flattening them into one is the failure the nesting exists to prevent — ruled D6.

**Kinds of nothing.** Every member has a `match` array and it is never empty; a group always
has at least two members. The one absence that can arise is a reference this engine cannot
parse, and that is an error at conversion rather than a `null` in the output — a member whose
verses are unknown is a member nothing can look up. Rule `say-which-kind-of-nothing`.

**What it replaces.** Nothing shipped. `utils/parallel_passages.py` reads the XML directly and
returns `{"references": [...]}` per group, carrying no scores at all; this is a strictly wider
shape and the reference-only result remains a projection of it. Rule `one-design`: if this is
built, the XML is read in exactly one place.

---

## 4. Decisions

Answer inline after each `=>`.

### D1. `match` as integers, or as words?

Integers `0|1|2` with the meaning declared once in a `match_values` header — or a word per
word. Words are self-describing; integers are 182 KB across the database and words 796 KB, a
measured 4.4×, on arrays that run to 66 entries at the longest. (The question as first posed
said "roughly triple" and named `"none"` as the negative value; both are corrected here from
the measurements in §5.)

=>   Use an enum:  no_match / partial / full.

**What follows.** A header cannot be relied on to travel: `saveas` writes a step's output,
`for-each` binds one group per iteration, `append_to` collects bare results, and a prompt input
is bound from the context. In every one of those the legend is left behind and the value arrives
alone — which is the source format's own defect at shorter range, since `5` was opaque because
its meaning lived in a README and `2` would be opaque because its meaning lived in a sibling key.
So `match_values` is removed from the payload and the value is self-describing at point of use.

The negative value is `no_match` rather than `none` because this project reserves the vocabulary
of absence: `null` means the question could not be asked and an empty collection means it was
asked and found nothing. A value spelled `none` is ambiguous between exactly those two, in a
codebase that has ruled the distinction must stay visible. `no_match` says the assessment ran and
came back negative — which is always true here, because every word of a scored row carries a
value and the database has no representation for "not assessed".

The closed set is declared once, as an `enum.Enum` in `src/llmflow/utils/parallel_passages.py`,
in the form `llmflow.utils.discourse.Outcome` already uses — lowercase snake_case values, a class
docstring stating the question the enum answers:

```python
class Match(enum.Enum):
    """The strongest correspondence a word has with any other member of its group."""

    #: Assessed, and corresponding to nothing in any other member — not "unassessed",
    #: which this database has no value for.
    NO_MATCH = "no_match"
    PARTIAL = "partial"
    FULL = "full"
```

**One declaration, not two.** If a JSON Schema is ever wanted it is *derived* from this enum,
never hand-written beside it — two encodings of one fact agree until they silently do not, which
is what `design-is-declarative` names and what `PIPELINE_SCHEMA` exists to avoid.

**What this means for the other value sets.** `kind` no longer exists — ruled D3 — so the only
remaining candidate is `counted_in` (`BHS` · `Rahlfs` · `UBSGNT5`). Whether it takes an enum is
**open**: see the unanswered question under D3. If it names *this* database's counting texts it
is closed and an enum is right; if it is meant to name editions generally it is open and a plain
string is right. Either way its derivation rule wants one home, because it is not obvious —
Greek members are always UBSGNT5, Hebrew members are BHS in an OT parallel and Rahlfs in a
quotation.

### D2. Discard the line breaks, or separate them?

The instruction was to ignore formatting, and §3 does. But the conflation is fixed by
*separating* the two facts, and discarding is a second, independent choice. Keeping them costs
one optional array of word indices — `"line_starts": [6, 11]` for `GEN 1:27` above — plainly
marked as presentation-only and disclaimed by the source. 2,876 of 5,266 rows carry at least
one.

Against keeping: the source says they are not grounded in the published texts, so a consumer
may read structure into them that UBS does not stand behind.

=>  Discard.  We don't do formatting in a back end engine.

**What follows.** `line_starts` is not in the shape, and §3 is settled: a member carries
`reference`, `verses`, `counted_in` and `match`, and nothing else. The conversion computes
`digit % 3` and throws `digit // 3` away at the point of reading, rather than carrying it to a
field nobody may use — a discarded value cannot be misread, and an optional one eventually is.

**This also disposes of the standing temptation in §6.** The line breaks do appear to coincide
with colon boundaries, and the pull will be to keep them "just in case" because they look like
free linguistic structure. Under this ruling they are not ours to carry even if the hypothesis
is confirmed: a consumer wanting colon or line structure takes it from a source that declares
it, not from a presentation hint its own publisher disclaims. That is `analysis-belongs-to-its-text`
— an analysis is served from a resource's declared sources or from nowhere — and
`declared-not-inferred`.

**The principle is more general than this document**, and may be worth recording where it binds
future work rather than only here: *"we don't do formatting in a back end engine."* It is not
currently stated in `docs/ai-context/project/rules.md`. Proposing it there is a separate act and
is not done here.

### D3. The vocabulary for `kind`

`ot-parallel` / `nt-parallel` / `quotation` names the relation, which is what a reader wants —
but "quotation" is UBS's framing of mixed groups, not something the file states per group. The
conservative alternative declares only what is observable, e.g. `"editions": ["Rahlfs","UBSGNT5"]`,
and leaves naming to the consumer.

=>  Use "editions".  We also have WLC and SBLGNT and Nestle1904 ... 

**A consequence you may not have intended.** The ruling removes `kind`. But the field proposed
as its replacement — `"editions": ["Rahlfs","UBSGNT5"]` on the group — is exactly the set of its
members' `counted_in` values. That is two encodings of one fact, which `design-is-declarative`
names as the defect: they agree until they silently do not. Two ways to honour the ruling
without duplicating — **drop the group-level field entirely**, since a consumer wanting "is this
a quotation" computes it from the member values it already holds; or **keep `editions` and
derive it at conversion**, documented as derived and never authored. The first is preferred
here: the second is a convenience index over a set of at most two.

**The WLC / SBLGNT / Nestle1904 point lands somewhere else, and is the more important half.**
Those are *our* resources. `BHS`, `Rahlfs` and `UBSGNT5` are the texts *UBS counted in*. They are
not the same texts — SBLGNT is not UBSGNT5 — and that difference is precisely the 180-of-2,030
row mismatch that keeps `returns: [words]` refused. So `counted_in` must name the edition UBS
counted in, never a registered resource name, or the two collapse and the error stops being
visible.

**That opens a question against D1's consequence**, which said every closed set gets an enum.
For this database `counted_in` has three values. If the field names *this* database's counting
texts, it is closed and an enum is right. If it is meant to name editions generally — across a
second source later — it is open, and an enum would be wrong.

=>  Remove "kind" entirely.  Use "editions" instead.

**Applied.** `kind` is gone from §3, replaced by `editions`, derived at conversion from the
members' `counted_in` values and documented as derived so the two cannot disagree.

**One question from the discussion above is still unanswered**, and it is the last open point in
this document: **is `counted_in` a closed set or an open one?** An `enum.Enum` like `Match` if it
names this database's three counting texts; a plain string if it is meant to name editions
generally, across a second source later. D1's consequence paragraph currently promises an enum
for it, and that promise is unbacked until this is settled.

=>

### D4. Group identity

The XML gives groups no id; position in the file is the only handle, and `id: 2` above is
positional. That is fragile across any future release of the database. Alternatives: a content
hash of the member references, or no id at all.

=> Discuss. Do we need ids?  If so, why?

**Recommendation: no `id` field.**

**The concrete case for one is deduplication.** A range query returns every group any verse in
the range takes part in, so a passage and a verse inside it give overlapping answers, and a
pipeline merging two queries may need to tell "the same group" from "a similar group".

**That case is already served without inventing anything.** A group's identity *is* its ordered
list of member references. A consumer needing a key builds it from data it already holds; an
`id` would precompute a tuple rather than supply information.

**Any id we mint is ours, not the source's.** A positional id breaks on the next UBS release —
the one thing an id would exist to survive. A content hash is stable but opaque, and still
changes when UBS edits a single member, so it does not deliver the stability that motivates it.

**One wrinkle any key must handle.** Exactly one group in the database repeats a reference:

```xml
<Verse HEB="2222">EZK 21:1</Verse>
<Verse HEB="2222">EZK 21:1</Verse>
```

It is the 39-member group carrying the `וַיְהִי דְבַר־יְהוָה אֵלַי לֵאמֹר` formula, four words
scoring `full` throughout. So identity must be the ordered **list**, never a set — a set would
silently collapse that group to 38 members. Whether the duplicate is a source error or a verse
genuinely carrying the formula twice is **not established**, and is recorded in §6 rather than
guessed at.

=>  OK, no ID field. 

### D5. What is this, once built?

Three readings, and they are different pieces of work:

- **(a)** a conversion artifact generated once and shipped as data;
- **(b)** the in-memory shape `utils/parallel_passages.py` produces, with the JSON as its
  `saveas` form;
- **(c)** a published proposal to UBS about how the data could be distributed.

(b) is the smallest and needs no new file to ship. (a) is a second encoding of a fact that
already exists, which `design-is-declarative` warns against unless it buys something.

=>  This is (b), but (a) is an implementation detail.  We can do the conversion once and be done with it, but when would we do this, given our curerent architecture?

**The question "when would we do this" is settled by measurement, not by architecture.**

| | |
|---|---|
| source | 328 KB XML, 2,193 groups |
| parse + full conversion to the ruled shape | **12 ms**, mean of five runs |

**So the conversion happens in the reader, on every run, and there is no artifact.**
`load_parallel_passages` already parses the XML at call time; converting while it parses costs
twelve milliseconds against a step that otherwise runs a verse-range comparison. Nothing in the
architecture needs to gain a build phase, and nothing needs a new hook.

That is also why (a) stays an implementation detail rather than a plan. A prebuilt artifact
would be a second copy of the data, requiring a conversion hook that does not exist — there is
none at `sp dataset add` or `sp resource set` — in order to save twelve milliseconds. If that
cost ever matters, the answer is a cache, which is a different thing from a shipped artifact and
needs no design document.

=> Agreed. the semantics are (b), implemention can change as long as the result is correct.

**Ruled 2026-10-03, superseding the recommendation above.** The Captain: *"I said generate it once
and save it as a dataset in this repository."* So the JSON is a dataset, generated once by a
generator committed in `tools/`, saved in this repository, and read by the `parallel-passages`
step in place of the XML. The paragraphs above recommending conversion in the reader on every run,
with no artifact, are withdrawn; they had answered the Captain's D5 instruction with the opposite
of it.

### D6. Do the 207 unstable rows need saying in the output?

222 `(edition, reference)` pairs appear in more than one group, and **207 of them carry a
different score string in each**. That is correct — a score is a fact about a word *within its
group* — but it surprises anyone who expects to key scores by verse. Options: say nothing and
let the nesting speak, or carry an explicit note on such members.

=>  Discuss

**Recommendation: say it in the field documentation, not in the data.**

**The nesting already states it.** A marker on each affected member has three costs: it is noise
on 207 of 5,266 rows; it implies the other 5,059 are "stable" when they are merely unrepeated;
and it states a fact about the *shape* while sitting inside one instance of it.

**A marker would not prevent the failure it targets.** A consumer who has flattened scores into
a verse-keyed map has already left the structure behind, and a field inside the structure cannot
reach them.

**The `EZK 21:1` duplicate makes the rule simpler and truer.** Reference is not a unique key even
*within* a single group, so the statement is not "scores are unstable across groups" but "a score
is positional within its member, and a member is positional within its group." That belongs in
§3's description of `match`, which already half-says it.

So: no field; one sentence in §3; and the `EZK 21:1` case recorded in §6 as an unexplained source
oddity rather than something the shape is bent to accommodate.

=>  Agreed. 

### D7. Both verse numbers, and what shape carries them

**The requirement, in the Captain's words:** *"we should supply BOTH the Hebrew verse number and
the verse number according to Rahlfs in our data."* And on the text: *"I don't know the edition,
so just say Rahlfs."*

**Why it is load-bearing rather than tidy.** A quotation group's Hebrew member is addressed in
`org` and counted in Rahlfs, and those two frames disagree for **69 of 266** references — 26%.
A consumer assuming they agreed would be right three times in four and silently wrong the rest.

**The mapping is corroborated, not assumed.** Mapping `org → lxx` and comparing each digit count
against Rahlfs word counts in `macula-lxx-greek`:

| 243 single-verse quotation OT rows | |
|---|---|
| digit count equals Rahlfs words at the **mapped** reference | **219 — 90.1%** |
| at the **raw** `org` reference (control) | 169 — 69.5% |

The mapping is worth 20 points, and 90.1% matches the order of #258's Greek-side figure against
SBLGNT (90.7%), so the residual is ordinary editorial difference rather than a mapping failure.
Re-derive with:

```python
import csv, glob
from collections import Counter, defaultdict
from llmflow.utils.versification import map_reference, packaged_mappings_dir
counts = defaultdict(Counter)
for path in glob.glob("<macula-lxx-greek>/Rahlfs/tsv/*/*.tsv"):
    trad = path.split("/tsv/")[1].split("/")[0]
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            counts[trad][row["ref"].split("!")[0]] += 1
# then, per single-verse quotation OT row (reference r, digit string s):
#   lxx = map_reference(r, "org", "lxx", packaged_mappings_dir())
#   any(counts[t].get(lxx) == len(s) for t in counts)
```

**Two things still to settle.**

**The shape.** Either four flat siblings —

```json
"reference": "PSA 45:7", "numbered_in": "org",
"counted_in": "Rahlfs",  "counted_reference": "PSA 44:7",
```

— or a pair of blocks, each naming a number *and* the scheme that makes it a location:

```json
"addressed": { "reference": "PSA 45:7", "verses": ["PSA 45:7"], "versification": "org" },
"counted":   { "reference": "PSA 44:7", "verses": ["PSA 44:7"], "versification": "lxx",
               "text": "Rahlfs" },
```

The second makes the source's own mistake structurally impossible — a number cannot be read
without its scheme, because they sit in one object. Its cost is that the two blocks are identical
for the ~5,000 members outside the quotation-Hebrew cell, so 95% of rows carry a duplicate. That
is honest duplication: each block asserts something different that happens to coincide.

**The one reference that will not map.** `PSA 116:10` in `org` corresponds to two verses in
`lxx` — Hebrew Psalm 116 is two psalms in Greek and this verse lands on the seam — so the engine
refuses to choose, which is correct. The counted reference therefore needs a state meaning
*asked, and there is no single answer*, distinct from *not applicable*. Rule
`say-which-kind-of-nothing`.

**One caveat that survives the measurement.** The scheme is Copenhagen's `lxx`, which nowhere
names Rahlfs; the 90.1% agreement is evidence they coincide, not a declaration that they are the
same thing. And that scheme declares 74 `partialVerses` the engine does not interpret, warning on
every load, so a small number of these second references rest on an approximation the engine
itself flags.

=> Yes, use "Rahlfs" and the Copenhagen Alliance's LXX mapping

---

## 5. Measurements

Every figure above comes from the script below, run 2026-09-27 against
`ubsicap/ubs-open-license` at the working-tree state of that clone. Nothing here is estimated.
Paste it into `hatch run python` from the repository root to re-derive all of it.

```python
from collections import Counter, defaultdict
from lxml import etree

XML = "<path to>/parallel passages/ParallelPassages.xml"
tree = etree.parse(XML)

groups = []
for p in tree.iter("Passage"):
    ms = [(n, (v.text or "").strip(), v.get(n))
          for v in p.findall("Verse") for n in ("HEB", "GRK") if v.get(n) is not None]
    if ms:
        groups.append(ms)

def kind(ms):
    eds = {e for e, _, _ in ms}
    return "quotation" if eds == {"HEB", "GRK"} else ("ot-parallel" if "HEB" in eds else "nt-parallel")

print(Counter(kind(g) for g in groups))                      # 1184 / 760 / 249
rows = [(kind(g), e, r, s) for g in groups for e, r, s in g]
print(len(rows))                                              # 5266
print(Counter(k for k, e, r, s in rows if "-" in r))          # 647 range rows: 417/184/46
print(Counter(k for k, e, r, s in rows if "," in r))          # 10 comma rows: 9/1
print(Counter(c for k, e, r, s in rows for c in s))           # digits 0-5 only; 6-8 absent

brk = set("345")                                              # the discarded presentation band
print(sum(1 for k, e, r, s in rows if any(c in brk for c in s)))   # 2876 rows carry a break
print(sum(1 for k, e, r, s in rows if s and s[0] in brk))          # 1 — a break precedes its word
print(sum(1 for k, e, r, s in rows if s and s[-1] in brk))         # 7

seen = defaultdict(set)
for k, e, r, s in rows:
    seen[(e, r)].add(s)
print(sum(1 for v in seen.values() if len(v) > 1))            # 207 unstable pairs

print(sum(1 for k, e, r, s in rows
         if all(int(c) % 3 == 0 for c in s)))                 # 11 rows scoring no_match throughout
print(sum(1 for g in groups if len(g) >= 3))                  # 494 groups with 3+ members
NAME = {0: "no_match", 1: "partial", 2: "full"}
print(Counter(NAME[int(c) % 3] for k, e, r, s in rows for c in s))       # 29724 / 14248 / 49447

cells = Counter()
for g in groups:
    k = kind(g)
    for e, r, s in g:
        cells[(k, e, "UBSGNT5" if e == "GRK" else ("Rahlfs" if k == "quotation" else "BHS"))] += 1
print(cells)                                                  # 4 live cells of 9

print(sum(1 for g in groups
          if len({r for e, r, s in g}) != len(g)))            # 1 group repeats a reference

import time                                                   # D5: cost of converting at read time
t0 = time.perf_counter()
for _ in range(5):
    t = etree.parse(XML)
    [[(n, (v.text or "").strip(), [int(c) % 3 for c in v.get(n)])
      for v in p.findall("Verse") for n in ("HEB", "GRK") if v.get(n) is not None]
     for p in t.iter("Passage")]
print((time.perf_counter() - t0) / 5)                         # ~0.012 s
```

Figures relied on above and re-derived by this script:

| | |
|---|---|
| groups | 2,193 — `ot-parallel` 1,184, `nt-parallel` 760, `quotation` 249 |
| verse rows | 5,266 |
| rows carrying a range | 647 — `nt-parallel` 417, `ot-parallel` 184, `quotation` 46 |
| rows carrying a comma list | 10 — `nt-parallel` 9, `ot-parallel` 1 |
| digit alphabet present | `0` 27,966 · `1` 13,178 · `2` 45,842 · `3` 1,758 · `4` 1,070 · `5` 3,605 |
| digits `6`–`8` | **0 occurrences**, though the source README documents them |
| rows carrying a break digit | 2,876 of 5,266 |
| break on the **first** word | 1 row — so a break precedes the word it marks |
| break on the **last** word | 7 rows |
| `(edition, reference)` pairs in >1 group | 222, of which **207** differ in score |
| rows scoring `no_match` on every word | 11 of 5,266 |
| groups with 3+ members | 494 of 2,193 — where the maximum-over-members reading applies |
| word-score values in total | 93,419 — `no_match` 29,724 (31.8%), `partial` 14,248 (15.3%), `full` 49,447 (52.9%) |
| `match` arrays as integers | 186,838 bytes — **182 KB** |
| `match` arrays as ruled words | 815,573 bytes — **796 KB**, 4.4× |
| groups repeating a reference | **1** — the 39-member `EZK`/`JER` formula group, `EZK 21:1` twice |
| source size | 328 KB |
| parse + full conversion at read time | **12 ms**, mean of five runs — D5 |

The two byte figures are computed from the value counts in the row above — two bytes per
integer element (`0` plus a comma), and `len(word) + 3` per word element (two quotes plus a
comma) — so they are arithmetic on measured counts rather than a separate measurement.

---

## 6. What this leaves untouched

- **The identifier problem.** Positions still index UBSGNT5, BHS and Rahlfs. #258 open questions
  1 and 2 govern, and `returns: [words]` stays refused until the MARBLE join exists. The Rahlfs
  side is a *different* blockage from the Greek one and should not be reported as the same: the
  Greek rows are a measured discrepancy between two identified texts, while the Rahlfs rows rest
  on an identification the source never made.
- **The source repository.** The README's arithmetic error and its phantom `6`–`8` band are
  UBS's; telling them is a separate act and not proposed here.
- **`EZK 21:1` appearing twice in one group.** Exactly one group in the database repeats a
  reference — the 39-member group carrying the `וַיְהִי דְבַר־יְהוָה אֵלַי לֵאמֹר` formula,
  where `EZK 21:1` is listed twice with identical scores. Whether that is a duplicated row or a
  verse genuinely carrying the formula twice is **unestablished**; it is recorded because it
  forces a group's identity to be an ordered list rather than a set (D4), not because the shape
  accommodates it.
- **`docs/ai-context/project/data-sources.md`**, which has no row for this database at all and
  is already 237 lines / 10.3 KB against its own declared budget of 200 lines / 8 KB. Adding one
  means splitting that file first, which is its own decision.
- **The line-break structure as linguistic evidence.** That the breaks coincide with colon
  boundaries is a hypothesis from one worked example plus the distribution across books
  (PSA 172, 1CH 190, 2CH 164, 2SA 160, ISA 110). Testing it means comparing break positions
  against a declared colon structure. `declared-not-inferred` — it is not a finding yet, and
  under D2 it would not change this design if it were: colon structure would come from a source
  that declares it, not from this one.
