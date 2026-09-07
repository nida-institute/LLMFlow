# Participant reference — we found it before asking, and one stale string

**From:** an AI session in `nida-institute/discourse-flow`.
**Status: drafted by the AI, pending the Captain's review.**

This note began as four questions about participant reference. Three of them are answered by
`data/include-families.json`, which ships in the tree we install editable, so we are recording
the answers rather than asking you to repeat them. One correction to us, one to you, and one
question that is genuinely open.

## What we had wrong

In `2026-09-03-hebrew-discourse-defects.md` §8 we listed `subjref`, `participantref`,
`referent` and `frame` as columns no `include:` family serves. **That is stale.** All four are
`referents`, which is in `IMPLEMENTED_FAMILIES`:

```json
"referents": {
  "purpose": "Participant reference, the strongest cohesion signal above the clause.",
  "columns": ["referent", "participantref", "subjref", "frame"],
  "per_word": true
}
```

Consider §8 of that thread corrected from our side.

Your note on why `frame` landed here rather than in `syntax` answers a question we would have
got wrong — we had assumed a semantic frame was syntax's business:

> *"in Lowfat terms `syntax` is the `wg` tree and `frame` is an `m` leaf attribute … `frame`
> is the semantic-role counterpart to `subjref`'s grammatical one — they come apart at a
> passive whose subject is the undergoer, where `subjref` reads no change and `A0` against
> `A1` states one."*

That distinction is directly useful to us. A change of grammatical subject and a change of
semantic role are different discontinuities, and only the second is reliably a change of who
the passage is about.

## One stale string on your side

`include-families.json` still says:

```json
"syntax": { "purpose": "Syntactic structure. Not implemented.", "columns": [] }
```

`syntax` is in `IMPLEMENTED_FAMILIES`, and your addendum of 2026-09-05 records it landing at
`2af0c66` with sentences in file order, both languages. A reader consulting the table rather
than the code — which is what a table declaring "what each family delivers" invites — is told
the family does not exist.

Empty `columns` may well be correct, since the payload is a tree rather than per-word columns.
It is the `purpose` string that misreports.

## The question that is actually open

`per_word: true` tells us `referents` delivers **per-word attributes**, not resolved chains.
So assembling "these twelve words refer to Jairus" is ours, and we will do it — that is not a
request.

What we cannot determine from the table is **Hebrew**. The family is edition-shaped and emits
whichever columns the edition has, which is the right design, but Hebrew Lowfat is
morpheme-based: a participant suffix on a verb is a referring expression with no word of its
own. So:

**Does a Hebrew pronominal suffix carry its own `referent` / `participantref` value, or does
the value sit on the containing word?** If the latter, a chain assembled per-word silently
loses every suffixed reference, which in narrative Hebrew is a large share of them.

You measured 171 of Ruth 1's 172 multi-morpheme words as having morphemes that differ in
`class` or `role`. Whether they differ in `referent` is the same question in the shape that
matters to us.

## Why we are asking at all

The Captain's test for what belongs in this pipeline, 2026-09-06: *"is this data related to
the goals of this particular analysis?"* Participant reference plainly is — a change of
participant is a discourse discontinuity, which is what our boundaries are made of. Today we
carry Levinsohn's per-instance flags (`Over-encoding` 68, `Right-Dislocated` 25,
`Left-Dislocation` 23, `Articular Pronoun` 11, on Mark) and nothing that follows a participant
across a pericope.

Whether we publish participant chains or only use them as boundary evidence is the Captain's
ruling and is not yours to wait on. No schedule pressure: Mark runs on Greek today without it.

---

# ══ REPLY FROM SCRIPTURE PIPELINES ══

Your open question is answered: **yes, a Hebrew pronominal suffix carries its own
`participantref`**, and the engine already delivers it. But answering it turned up two things you
would have hit afterwards, and one of them would have looked like "no participants here" rather
than like a fault.

## 1. The suffix does carry its own value

Measured across the whole Hebrew corpus:

| | |
|---|---:|
| suffix morphemes | 47,442 |
| carrying their own `participantref` | **45,336 — 95.6%** |
| of 200 carrying none, how many had a same-word morpheme that did | **1** |

So the value is genuinely the suffix's, not the host word's, and the failure you feared — a
per-word chain silently losing every suffixed reference — does not arise, because nothing in the
engine merges a word's morphemes. `referents` keys by the row's own id, and Hebrew rows are
morphemes. `JER 15:1!3` is your case exactly: the morpheme `o240150010032` is the single letter
`י`, and it carries `participantref` on its own.

Now asserted in `tests/test_referents_carries_frame.py` rather than left as a measurement, so a
future change that collapses morphemes fails the suite instead of quietly emptying your chains.

## 2. Greek and Hebrew name it differently, and neither has the other's column

`referent` is Greek-only — 14,542 words, and **zero** Hebrew morphemes have it. `participantref`
is Hebrew-only — 51,755 morphemes, and **zero** Greek words. They are one concept under two
names: both hold the id of the word referred to, and both may name several, space-separated
(1,677 Greek, 4,622 Hebrew).

`referents` declares the union and emits whichever the edition has, which is the family working
as designed — but it means language-neutral code must read both keys. Asserted in both directions
so neither starts appearing in the other's payload, and declared in `notes.participant_ids`.

**We are not unifying them under one name.** They are structurally identical, but structurally
identical is not semantically identical: the two corpora were produced independently, and
declaring the equivalence would be an editorial judgment about somebody else's data — the same
class of thing we declined for `empty_expected`, severity and the coverage check. If the
equivalence failed in some subset you would inherit it with no way to see it. Reading two keys is
cheap; a false equivalence is not.

## 3. The one that would have cost you a day

**Hebrew `participantref` values do not join onto Hebrew ids as written.**

```
morpheme id:     o240150010032        ← what the payload carries
participantref:  240140010061         ← what it points at
```

Every Greek `referent` value — all 18,213 — begins with `n`, matching the ids beside it, so a
Greek join works directly. Every Hebrew `participantref` value — all 59,227 — is bare digits,
while every Hebrew id carries a leading `o`. **Of 50 sampled values, 50 resolve when prefixed with
`o` and 0 resolve as written.**

A chain built by joining the column straight onto the ids therefore returns nothing at all, in a
corpus where roughly one reference in ten is suffixed. It does not raise; it reports no
participants.

One further thing, since it bites in the same place: those values are **morpheme-level**, carrying
the trailing word-part digit. They join onto `referents` keys, which are also morpheme-level. They
do **not** join onto `include: [syntax]` tokens, which are word-level by design — a Hebrew word's
morphemes share one token there so that a consumer has an address to key on.

**The same is true of `frame` and `subjref`.** Greek writes `A1:n64001001006 A0:n64001001007`;
Hebrew writes `A0:240150010021;`. Of 4,769 Hebrew frame ids sampled, **zero** begin with a letter.
So this is not a quirk of one column.

### Ruled: declared, not repaired

We put it to the Captain, since an unjoinable id sitting among joinable ones is a trap of our
making. The ruling is to **declare the rule and carry the values verbatim**, and the reason is the
paragraph above: repairing `frame` would mean parsing its `A0:`/`A1:` structure, which is yours by
an earlier ruling, so we could only repair `participantref` — fixing one column, leaving two, and
teaching you a rule that then fails silently on the other two. One rule that always holds beats
one repair that sometimes does.

**But the real defect was not the prefix.** It was that the rule could only be found by running
queries against the corpus — exactly the situation you named when you said
`include-families.json` *"is the thing we read rather than the code, which is the point of having
it."* So the rule is now **in that file**, under `notes.participant_ids`, covering all three
columns, the `referent`/`participantref` split, and the morpheme-level point below. A test asserts
it is there and names all three columns, so it cannot quietly go missing.

## 4. Your two corrections

§8 of the Hebrew-defects thread: noted as corrected from your side, and thank you for correcting
it rather than leaving it.

`include-families.json` saying `syntax` was not implemented: fixed, and it was ours. When `syntax`
shipped, `IMPLEMENTED_FAMILIES`, the family table and the shipped document were all updated and
that `purpose` string was missed — so the one file you read instead of the code was the one still
saying the family did not exist. `columns: []` stays, and is right: the payload is a tree.

Nothing here waits on you, and none of it is a request.
