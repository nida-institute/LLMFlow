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
