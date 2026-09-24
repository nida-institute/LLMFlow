# Decisions — regenerating the alignment corpus in burrito form

Status: proposed (2026-09-13) → #238. Nothing here is built. Every `=>` is the Captain's.

Rulings already made are in `plan-scripture-burrito-alignment.md` (R1–R18) and are **not**
re-opened here. This document holds only what is still open, and only decisions large enough
that getting them wrong means redoing work or republishing data twice.

---

## Background, for reading this cold

**A Scripture Burrito** is a container: a directory with a `metadata.json` describing what is
inside, plus the files themselves, called *ingredients*. The metadata says who made it, who
owns it, what licence applies, and what kind of thing it is — its *flavor*. `alignment` is one
of the defined flavors.

**The alignment format** is a separate specification, held in
`bible-technology/alignment-spec`, describing the JSON inside an alignment burrito. It is at
version 0.4. Its model is small:

- a **selector** is an identifier into some document — a word, usually
- a **reference unit** is a set of selectors acting as one thing, e.g. a multi-word phrase
- a **record** joins two or more reference units, with roles like `source` and `target`
- a **group** collects records sharing a type, documents and metadata
- a file declares `format`, `version`, and an array of `groups`

Selectors are **opaque** to the specification. What they mean belongs to whoever published the
text they point into. A `scheme` names which identifier system is in use.

**The corpus** is `Clear-Bible/Alignments`: 21 published alignment files across 10 languages,
each with a TOML sidecar carrying copyright, licences and team. The JSON files are not
currently valid 0.4 — they are bare groups, a shape 0.3 allowed and 0.4 removed.

**The library** is `Clear-Bible/biblealignlib`, which reads and writes these files. It is the
generator, so fixing the data means fixing it (R3). Three fixes exist: the 0.4 envelope
(PR #4), a TOML reader (PR #5), and taking identifier schemes from the data rather than
inventing them (uncommitted).

**What is now proposed** is to run the fixed library over the corpus and rewrite all 21 files,
as a pull request for the library's author to review. Doing that forces a set of choices,
because a rewrite is not neutral: the writer makes decisions the original files did not.

---

## A. What regeneration changes besides the envelope

Rewriting a file through the library changes several things that have nothing to do with the 0.4
envelope. **The first is not a decision — it is a defect that blocks regeneration entirely.**

### A0. The library does not round-trip identifiers — BLOCKER

Ruled by the Captain, 2026-09-13: *"Identifiers are opaque, we have no right to change them,
they belong to the data creator. If we change them, they no longer work in the original
environment they came from, and those environments cannot use our alignments."*

Measured on the published `SBLGNT-BSB` file — read it and write it back, changing nothing else:

```
ORIGINAL     source: ['n40001001001']
ROUNDTRIPPED source: ['40001001001']
```

The reader strips the Macula prefix on load (`macula_unprefixer`, `alignments.py:179`) and the
writer never restores it, because `AlignmentRecord.asdict` defaults to
`withmaculaprefix=False` and `_record_dict` does not override it. **19 of the 21 files have
prefixed source selectors** — 13 Greek `n`, 6 Hebrew `o` — so regeneration would strip the
prefix from every source selector in the corpus.

A second mechanism does the same to targets (A2 below), and a third can *invent* a prefix:
`macula_prefixer` infers one from the book number rather than carrying what was there, so a
source that legitimately has no prefix could acquire one.

This is not a formatting question. Until the library preserves identifiers exactly,
regeneration produces alignments that no longer resolve against the texts they describe.

**A round-trip test now exists and fails**, in `TestIdentifierRoundTrip`: it reads the published
`SBLGNT-BSB` file, writes it back, and compares every reference unit. Result: **115,008 source
units altered**, which is all of them.

*(My first version of that test passed while checking nothing — it matched records by `meta.id`,
which the writer renumbers, so every lookup missed and it compared two empty sets. Rewritten to
assert the comparison is non-empty before comparing.)*

**That this must be fixed is not in question. How is.** The stripping is load-bearing, not
gratuitous: `SourceReader` keys its tokens by the bare identifier — `"40001001001"` resolves and
`"n40001001001"` does not — so simply not stripping would break every token lookup in the
library. Three shapes:

- **Record what was stripped and restore it on write.** The reader already knows whether a
  prefix was present; the writer restores exactly that. Smallest change, and it is restoration
  rather than inference, so the two unprefixed files stay unprefixed. Costs a serialization
  detail stored on the group or the document.
- **Keep the published identifiers verbatim and derive the bare form at each lookup.**
  Nothing is ever mutated, which is R19 taken literally. Touches every lookup site, and there
  are several.
- **Make the token readers accept either form**, so no normalization is needed anywhere.
  Largest change, and it removes the whole class of bug rather than this instance.

Also to decide: whether the fix ships as its own pull request ahead of the others, or alongside.

=>

### The rest of section A

Each of the following is a genuine decision, because each is visible in the published data.

### A1. Record identifiers are renumbered — the library's own, not the source's

This one is **not** governed by R19. `meta.id` names an alignment record, which the library
mints; it is not an identifier taken from anyone's source text. R9 allows a library its own
scheme provided it documents it. So this is a genuine choice about churn, not a question of
ownership.


Every record carries `meta.id`. The published files use three digits after the verse; the
writer emits two.

```
published:   "id": "40001001.001"
regenerated: "id": "40001001.01"
```

This touches **every record in all 21 files** — over a hundred thousand lines — and will
dominate the diff, burying the structural change a reviewer actually needs to see.

`meta.id` is the library's own identifier scheme, not something the specification governs, so
either width is legitimate (R9). The question is only what to do on this rewrite.

- **Accept the renumbering.** One-time churn, and afterwards the files match what the library
  produces. The reviewer sees a diff in which almost every line changed.
- **Preserve existing ids.** The diff shows only the structural change. Costs a change to
  `_record_dict` to reuse an id when one is present.
- **Widen the writer to three digits.** Matches the published corpus, so most ids stay put,
  but any file whose ids were assigned differently still churns.

=>

### A2. Target part digits are stripped — the same violation as A0

`AlignmentsReader._targetid` truncates a 12-character target selector to 11 unless
`keeptargetwordpart=True`. Their own comment calls it `# bad hack here to drop word parts`.

```
published in BGNT-BSB:   "target": ["400010010011"]
regenerated by default:  "target": ["40001001001"]
```

Under R19 this is not a choice between settings. A flag that defaults to discarding part of an
identifier is the library deciding it owns identifiers it did not create — the same defect as
A0, in a different direction, against the target rather than the source.

So the fix is to stop truncating, not to pass a flag: a caller who genuinely wants a bare word
identifier can derive one, but the reader must not hand out a mutated identifier as though it
were what the file said.

The one thing still to decide is **what happens to `keeptargetwordpart` itself** — three call
sites pass it through (`AlignmentsReader`, `Manager`, `TargetReader`), and some caller may
depend on the truncation.

- **Remove the parameter**, and let anything needing a bare identifier do its own derivation.
- **Keep it, inverted**, so preserving the identifier is the default and truncating is the
  opt-in that must be asked for by name.

=>

### A3. Records are re-sorted

The writer sorts records before writing. At least one published file is known not to be sorted
— there is a comment in the library saying so. Sorting is stable and loses nothing, but it
moves lines.

- **Accept.** Sorted output is easier to diff in future, at the cost of noise in this diff.
- **Preserve existing order** for this rewrite, and sort only new files.

=>

### A4. Rejected records are dropped

`read_alignments(keeprejected=False)` is the default and removes records whose status is
`rejected`. On a rewrite that is silent data loss.

I intend to read with `keeprejected=True` and to use `AlignmentsReader` rather than `Manager`,
because the reader does not filter bad records while `Manager` does. Confirming rather than
assuming, since it is the difference between a format change and a content change.

=>

---

## B. The TOML sidecar

### B1. Does `alignment.format` survive?

Each sidecar declares the format of the file beside it. Across 21 files there are three
spellings of one claim:

```
12 files:  format = "Scripture Burrito v0.3"
 7 files:  format = "Scripture Burrito 0.3"
 2 files:  format = "grapecity"
```

Once the JSON declares `"version": "0.4"` at its top level, this field is a second encoding of
the same fact — the situation we just removed from `meta.conformsTo`, on the grounds that two
copies drift apart. These already have.

- **Drop the field.** The file declares its own version; the sidecar stops repeating it.
- **Keep and update it**, accepting that it must be maintained in step by hand.
- **Keep it but change its meaning** — not a version, but which *family* of format the file
  belongs to, which is how the two `grapecity` files appear to be using it.

=>

### B2. Where does the sidecar's content end up?

A valid burrito needs `copyright`, `identification` and the rest in `metadata.json`. The TOML
is where that information exists today and is the reason to mine it (R10). Two futures:

- **The TOML becomes the source and `metadata.json` is generated from it.** The sidecar stays
  as the human-edited input; the burrito metadata is derived output.
- **The TOML is migrated once into `metadata.json` and then deleted.** One place, no drift,
  but hand-editing JSON metadata is worse than hand-editing TOML.

This decides whether the converter is a one-time migration or a permanent part of the build.

=>

### B3. The four sidecars that cannot be parsed

`arb/AVD/SBLGNT-AVD-manual`, `arb/AVD/WLCM-AVD-manual`, `arb/ONAV/SBLGNT-ONAV-manual` and
`eng/BSB/BGNT-BSB-manual` all fail with a duplicated key — no standard TOML parser will read
them. Their provenance cannot be mined, so no valid burrito can be produced for them.

```
tomllib: Cannot overwrite a value (at line 32, column 105)
```

- **Fix the four by hand first**, then regenerate all 21.
- **Regenerate the 17 that parse**, and leave the four until their sidecars are repaired.

=>

---

## C. The two files that are not burritos

### C1. `BGNT-BSB` and `WLCM-BSB` declare `format = "grapecity"`

These are the same two files that are anomalous everywhere else: `BGNT-BSB` is one of the four
unparseable sidecars *and* the only file with 12-digit targets. Read together, the likeliest
explanation is that they are pre-burrito GrapeCity exports that were never converted, and are
still honestly saying so.

If that is right, then running the regeneration over them is not a rewrite but a **migration**,
and treating their 12-digit targets as a defect to normalise (A2) would be discarding a real
distinction rather than fixing an inconsistency.

- **Migrate them deliberately**, as a separate piece of work with its own review.
- **Exclude them** from this regeneration and leave them declaring what they are.
- **Treat them as ordinary** and regenerate with everything else.

I should say plainly that "pre-burrito exports never converted" is my reading of three
correlated facts, not something the data states. You know this history and I do not.

=>

---

## D. What a burrito actually is here

This is the largest set of decisions and I have not previously put it in front of you.

### D1. One burrito per alignment, or fewer?

A burrito is a directory with a `metadata.json`. The corpus has 21 alignment files in a tree
organised by language and target:

```
data/eng/alignments/BSB/SBLGNT-BSB-manual.json
data/eng/alignments/BSB/WLCM-BSB-manual.json
data/spa/alignments/RV09/SBLGNT-RV09-manual.json
```

- **21 burritos**, one per alignment — matches the sidecars, which are already per-alignment,
  and lets each carry its own copyright. Means 21 `metadata.json` files and a directory
  restructuring.
- **One burrito per target translation**, so `SBLGNT-BSB` and `WLCM-BSB` share one — matches
  the directory layout, but the two may have different rights holders.
- **One burrito for the repository** — simplest, but a single copyright block would have to
  cover work owned by everyone in the corpus.

=>

### D2. Does the burrito layout change the repository layout?

A burrito expects its ingredients under its `metadata.json`. The present tree was not built
that way. Converting may mean moving files, which breaks every existing path reference — and
the library hardcodes many of them.

- **Restructure** to the burrito layout.
- **Keep the layout and place metadata alongside**, if the specification permits it.

=>

### D3. Are the token files ingredients?

An alignment's selectors point into tokenized texts. Without those TSVs the alignment cannot be
resolved. Whether they belong *inside* the alignment burrito decides whose rights the burrito
must state, which is the whole of section E.

- **Include them as ingredients**, making the burrito self-contained and putting the
  tokenization rights squarely inside it.
- **Reference them as separate burritos** via `relationships`, which requires those burritos to
  exist.

=>

---

## E. Rights

`confidential` is ruled: false throughout (R16). These are not.

### E1. A licence identifier is not a form the schema accepts

The sidecars say `license = "CC-BY-4.0"`. The burrito `copyright` block requires exactly one of
three things, and an identifier is none of them:

```json
"copyright": {"publicDomain": true}
"copyright": {"shortStatements": [{"statement": "Copyright 2024 by ...", "lang": "en"}]}
"copyright": {"licenses": [{"url": "https://creativecommons.org/licenses/by/4.0/"}]}
```

- **Map identifiers to canonical URLs** — `CC-BY-4.0` becomes the CC BY 4.0 deed URL.
- **Bundle the licence text** as an ingredient and point at it by path.
- **Use `shortStatements`**, carrying the sidecar's `copyright` prose where it exists — but it
  exists in only 8 of the 17 readable sidecars.

=>

### E2. Five rights holders, one copyright block

A single sidecar routinely names five parties:

| section | covers | example |
|---|---|---|
| `[source]` | the Greek text | Society of Biblical Literature and Logos |
| `[source.metadata]` | its tokenization | Clear Bible, Inc. |
| `[target]` | the translation | public domain |
| `[target.metadata]` | its tokenization | BiblioNexus |
| `[alignment]` | the alignment | BiblioNexus |

Across the corpus that is 14 distinct rights statements. The container cannot express who holds
what: `agencies[]` gives a party a functional role but not an artifact, and
`copyright.shortStatements[]` cannot be scoped at all. R18 says raise it against the standard
*and* support it anyway — this is how we support it in the meantime.

- **One `shortStatement` per holder**, each naming its scope in prose. Human-readable, not
  machine-readable, and honest about being a workaround.
- **An `x-` extension field** carrying the structured chain, which is what the spec's
  extensibility is for but which nothing else will read.
- **Only the alignment's own rights** in the burrito, with the rest reached through
  `relationships` — clean, and loses the tokenization rights entirely (see D3).

=>

### E3. `idAuthorities` is required and exists nowhere

Every burrito must declare it. It names the authority behind the identifiers used in
`identification`. Nothing in the corpus or the sidecars supplies one.

- **Mint one for Biblica** and use it throughout.
- **Use an existing authority** if one already covers this data.

=>

---

## F. Scheme names

### F1. Is there an interim name, or do we wait?

`BCVWP` is declared on all 21 sources including the 15 whose identifiers have no part digit. It
is wrong, and under R6/R8 the scheme should record the format the source uses — `macula-greek`,
`macula-hebrew` and so on.

But no registry defines such names (the held Working Group issue). Renaming now replaces a wrong
name with an undefined one.

- **Wait for the Working Group**, leaving the declarations as the data states them.
- **Adopt provisional `x-` names** now, which the specification explicitly permits for
  extension, and align them with the registry later.

=>

---

## What I will not do without an answer

Nothing in this document is started. The regeneration in particular writes to another
organisation's repository, and section A alone changes over a hundred thousand lines.

Once A and C are answered the regeneration can run as a reviewable pull request. B, D and E are
needed before anything writes a `metadata.json`. F is independent of both.
