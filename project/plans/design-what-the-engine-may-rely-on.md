# Design — what the engine may rely on

**Status: the general form of three rulings the Captain made on 2026-09-03 and 2026-09-04.** Each
was made separately, about a different subsystem, and each turned on the same distinction. Written
down because the fourth case will arrive and nobody should have to re-derive it.

Not a proposal. The rulings are already in force; this states what they have in common.

---

## 1. The line

**The engine may rely on anything declared with an authority — a publisher's format, one of our own
declarations, or a measurement anyone can re-derive. It may not rely on anything inferred from
shape, layout, naming, or how often something occurs.**

The three sources below are what "declared with an authority" means. The failures in §3 are what
inference looks like when it is wrong, and all four happened within two days.

---

## 2. What may be relied on

### 2.1 A published format

Someone outside this project wrote it down, and other tools depend on it. Strongest of the three,
because it is falsifiable against a document we did not write.

- **Macula word ids are `BBCCCVVVWWWP`** in Hebrew and `BBCCCVVVWWW` in Greek — `WWW` the word
  index within the verse, `P` the word part (*MACULA Hebrew Treebank for OSHB* §2.1). This is what
  licenses `_word_identifier` dropping the part to address a word. An earlier draft refused to,
  on the grounds that the trimmed id appears in no row and would therefore be invented. The
  Captain: *"isn't that already documented in the macula hebrew documentation as the format?"* It
  is. Reading a declared component of an id is not inventing an identifier.
- **`ref` carries the word index in both corpora**, so `RUT 1:1!4` *is* word 4. This is what
  `resolve_citation` now reads instead of counting rows. `discourse-flow`'s framing is the one to
  keep: it *removes an assumption* rather than adding a per-edition flag.
- USFM and USX, OSIS ids, the SBL abbreviations, the Copenhagen versification specification.

**The test:** could a reader check the claim against a document this project did not write?

### 2.2 One of our own declarations

Reliable because a check can read the declaration itself rather than a copy of it — which is rule
`check-the-source-not-the-rendering`.

`data/include-families.json`, the pipeline schema, `data/ai-rules.yaml`, `data/file-catalog.yaml`,
`data/helm-sync.yaml`, an edition's registry entry, a role map.

**The test:** does the check read the declaration, or a list someone keeps beside it? A hand-kept
copy is not a declaration — it is an inference about one, and it drifts. Three of those were found
inert in one afternoon.

### 2.3 A measurement anyone can re-derive

Weakest of the three and still sound, provided the command is recorded beside the claim.

`design-declaring-field-roles.md` §4 opened *"A model generates properties in schema order"* — an
AI-written claim in an AI-written document, which is no evidence at all. `discourse-flow` measured
it: 166 of 166 responses matching schema order exactly, 0 deviating. Their Captain's response to
the unsourced sentence — *"I have no idea where that sentence came from"* — is the correct response
to every claim of that kind.

**The test:** is the command to re-derive it written next to the number? Their HOTDF-LS counts are
recorded in `design-combining-levinsohn-and-ubs.md` §5 with theirs, and marked unverified here.

---

## 3. What may not be relied on

Each of these produced a wrong answer within two days of this being written.

| inference | what happened |
|---|---|
| **the code and file tree as specification** | #38 was closed as completed on an AI's conversational claim, with no commit and no test, while the repository's own design document listed the work as unresolved throughout. Five plan documents asserted state that was false. `design-authority.md` already says running code is not designed code; this is the same rule for records. |
| **a plausible mechanism** | 79 Hebrew citations still failed after the index fix. Maqqef-joined words were the obvious cause — Hebrew joins words with it, Macula counts the parts separately. Measured: false. `RUT 1:1` fails at index 11 with no maqqef in the verse, and `RUT 1:10`'s first failure precedes its maqqef. |
| **frequency as meaning** | "55.2% of signals never reach the claim they support" was accurate and was described as a failure rate. `discourse-flow` withdrew the word while keeping the count: every feature type sits between 21% and 78% cited, and the instruction being measured against was a line in their own prompt that no design ratifies. |
| **what a value means to whoever receives it** | why `empty_expected`, occupancy reporting, severity and audience are all out of the role map. Each needs a judgment about somebody else's data. |

---

## 4. The same line, one layer up

The Captain, ruling on the field-role vocabulary:

> Prescribing the application semantics of downstream clients you don't even know about is
> generally a bad idea, and it makes the design much more complicated.

> it's analogous to sp trying to own the application semantics of the pipelines that use it.

That is §1 applied to layers rather than to facts. Each layer may rely on what it has been told and
on what it can check; it may not infer what the layer below means by it. The engine declares a
vocabulary; a pipeline declares which of its fields are which; a consumer decides what to do.

**It cuts both ways, and the second direction is easier to miss.** An earlier draft of the role-map
design offered to un-conflate `ears-to-hear`'s display categories from inside the engine — the same
error, pointed downward. It was withdrawn.

---

## 5. Worked example: the coverage check

`identifies` names the field that carries an item's identity, so "did everything I asked for come
back?" becomes a generic check. Three parts, and they sort cleanly:

| the fact | source | whose |
|---|---|---|
| each `segments[]` entry is identified by `canonical_reference` | a declaration in the role map | **engine-checkable** |
| the set that was asked for is the list in a named variable | the pipeline knows it; the engine cannot | **the pipeline declares it** |
| twelve of ninety-nine coming back is a failure | neither | **the application's** |

So the comparison is a set difference, which is mechanical, and the reporting is mechanical.

**And it rejects an option that looked reasonable.** *Infer the requested set from the `for-each`
list* would have the engine assume that "requested" means "whatever you iterated over" — an
inference from pipeline shape, which is exactly §3. The pipeline states it instead.

**It also settles the declaration site.** `identifies` is a fact about a schema, so it lives in the
role map. Where the requested set comes from is a fact about a *step* — the same schema may serve
two steps asking for different sets — so it lives on the step. Each fact goes where it is known.

---

## 6. What this does not say

- Not that inference is forbidden while working. Forming a hypothesis is how the maqqef question
  got answered; what is forbidden is *shipping* one, or reporting it as a finding, without the
  measurement.
- Not that a declaration is always right. `data/include-families.json` declared `frame` as
  belonging with `syntax`, and that was wrong once `include: [syntax]` was ruled standoff. A
  declaration can be corrected; an inference cannot even be located.
- Not a new constraint. Every case above was already ruled. This is where to look when the next one
  arrives.
