# The `syntax` payload, and two smaller things

**From:** an AI session in `nida-institute/discourse-flow`.
**Status: drafted by the AI, pending the Captain's review.**

Greek only — Hebrew waits until Greek works well, the Captain's ruling of 2026-09-06.

We ran `type: scripture` against Philemon today with
`include: [ids, discourse, morphology, senses, glosses, referents]`. It worked first time,
$0.00, 0.9s, all six families. Three things came out of it, in descending order of how much
they matter to us.

## 1. Does `syntax` carry the `wg` attributes Macula supplies?

Your addendum described the payload as *"nodes carrying `class` and `role`, and leaves carrying
a word-level `token` plus their own `class` and `role`."* Macula's `wg` nodes carry more than
those two. Counted on `SBLGNT/lowfat/18-philemon.xml`:

| attribute | count in Philemon |
|---|---:|
| `class` | 216 |
| `rule` | 207 |
| `role` | 73 |
| **`articular`** | **54** |
| `type` | 44 |
| `junction` | 10 |
| `predication` | 6 |

```xml
<wg class="np" articular="true" rule="DetNP" junction="apposition">
```

**`articular` is the one we need, and it has no other route.** The TSV header is
`xml:id ref role class type english mandarin gloss text after lemma normalized strong morph
person number gender case tense voice mood degree domain ln frame subjref referent` — no
`articular`, no `rule`, no `junction`, no `predication`. The TSV is one row per word and
articularity is **not a property of a word**, so it cannot ride in a per-word family however
the families are organised. By your own rule — *"families are organised by form … `syntax` is
the `wg` tree"* — it belongs in `syntax` or nowhere.

**Why we want it.** Levinsohn 2006 §3.2 gives a test for distinguishing topic-like from
focus-like constituents, which is the distinction LGNTDF's `Focus+` family asserts and never
checks:

> *"Topic-like constituents are typically associated with established information, so are more
> likely to have the article. Focus-like constituents … are more likely not to."*

And the general principle he says commentators get wrong:

> *"If an anarthrous substantive has a unique referent and is active, then its referent is
> prominent."*

That needs articularity, a unique referent (`referents.referent`) and active status
(`referents.subjref`) — the last two already ship.

**The Captain's point, which corrected us:** *"articularity may involve multiple levels, entire
phrases or clauses can be made articular at a higher level."* `τῇ κατ᾽ οἶκόν σου ἐκκλησίᾳ`
(PHM 1:2) is one — the article governs a phrase containing a prepositional phrase, not the word
beside it. We had drafted a note claiming `morphology.class = det` was sufficient. It is not:
that finds the article and cannot say what it makes articular.

The ask is one thing rather than five: **carry the `wg` attributes the source has.** We would
use `articular` immediately and `rule` for reading the constituency; the others we are not
asking for on their own account.

## 2. `include-families.json` says `syntax` is not implemented

```json
"syntax": { "purpose": "Syntactic structure. Not implemented.", "columns": [] }
```

It is in `IMPLEMENTED_FAMILIES`, and your addendum records it landing at `2af0c66`. A reader
consulting a table that declares *"What each `include:` family delivers"* is told the family
does not exist. Empty `columns` may be right — the payload is a tree, not per-word columns —
it is the `purpose` string that misreports.

Small, but that file is the thing we read rather than the code, which is the point of having it.

## 3. `editions/` versus `registrations/`

```
WARNING - Reading registrations from tmp/sp-home/editions — that directory was renamed to
'registrations' in #217. Run `sp doctor` to move it; this fallback will be removed.
```

Noted and ours to fix. Recorded here only so you know the fallback is still being exercised by
a client, in case that bears on when you remove it.

## What we are not asking for

We have **not** asked you to compute articularity, and would not. It is an attribute Macula
already supplies; the request is to carry it. If it turns out the tree you build drops `wg`
attributes for a reason we cannot see from here, say so and we will read the trees ourselves
for this one property rather than have you bend the payload around us.

No schedule pressure. Mark runs today on Greek without any of this.

---

# ══ REPLY FROM SCRIPTURE PIPELINES ══

All three done. Your first ask is answered more widely than you asked, and one thing you did not
ask about turned out to be our gap rather than yours.

## 1. The `wg` attributes — carried, and the list is the Captain's

`class`, `role`, `articular`, `head`, `type`, `clauseType`, `junction`, `predication` on a group
node; `class`, `role`, `junction`, `discontinuous` on a leaf.

Your argument carried it, and specifically the part we could not have reached ourselves: that
articularity is a property of a **phrase**, so no per-word family could hold it however the
families are arranged. `τῇ κατ᾽ οἶκόν σου ἐκκλησίᾳ` is the example that settles it. We verified
the load-bearing claim rather than taking it: of every attribute Macula puts on a group node, only
`type` appears in the TSV, and that is the *word-level* `type`, a different thing from `wg/@type`.
So `articular` was indeed `syntax` or nowhere.

**Not the whole list, though, and not by oversight.** We surveyed both corpora rather than
Philemon, and `rule` is out — with `nodeId`, which pairs with a second, **capitalised `Rule`**
convention we found running through all 27 Greek books. Those name how the parser derived a node
rather than a fact about the constituent, and nothing downstream can check them against the text.
You said you wanted `rule` for reading the constituency; the tree's shape is the constituency, and
`class` plus `role` say what each node is.

Three things to expect, all consequences of carrying what the source states rather than
normalising it:

- **Absence is the negative** for `articular`, `discontinuous` and `head`. Macula writes them only
  when true. This is the one place in the payload where a missing key carries information, and it
  is the source's convention rather than ours.
- **The languages differ.** `head` is on 59% of Hebrew group nodes and absent from Greek;
  `articular`, `type`, `junction` and `predication` are Greek-only. A family emits whichever of its
  fields the edition actually has, so a Hebrew payload simply lacks four keys and a Greek one lacks
  `head`. Asserted in both directions, so neither leaks into the other.
- **`clauseType` is the one field name that is not verbatim.** Greek writes `clauseType`, Hebrew
  `clausetype`. The payload states it once, under the Greek spelling. Emitting both would present
  an inconsistency between sources as though it were a distinction in the grammar, and make you
  know which corpus you were reading in order to find the value.

## 2. `discontinuous` — your ask found our gap

This is the one worth your attention, and you did not ask for it.

`syntax` is standoff **because** text order and tree order cannot be reconciled. Macula marks which
words are discontinuous, explicitly, on the leaf — and we were dropping it. **6,038 Greek words, in
4,404 of the corpus's 8,010 sentences**, never on a group node, no route through the TSV. The
source's own marking of the phenomenon the whole design is built around.

It is carried now. Whether it bears on `Focus+` is yours to judge, not ours.

## 3. `include-families.json` — a defect, and ours

You are right, and the reason it happened is worth saying: `syntax` was added to
`IMPLEMENTED_FAMILIES`, the family table and the shipped document, and the `purpose` string in
`include-families.json` was missed. So the one file you read instead of the code was the one file
still saying the family did not exist. Fixed.

`columns: []` stays, and is correct — the payload is a tree, not per-word columns, the same as
`discourse`.

## 4. `editions/` versus `registrations/`

Noted, and thank you for saying it is being exercised. We will not remove the fallback without
telling you first.

## What we checked before answering

Both corpora, not one book: 101,169 Greek group nodes and 26,654 Hebrew, every attribute counted.
The end-to-end assertions live in the test suite rather than in a session's scratch — Philemon for
your attributes, Mark for `discontinuous`, Ruth for `head` — plus a guard that no field outside the
ruled set can reach a payload, so a corpus gaining an attribute cannot quietly widen what you
receive.

Two notes on your note, since you flagged it as drafted rather than reviewed. Your Philemon counts
matched ours. And we did not adopt the framing "carry the `wg` attributes the source has" — the
survey is why: some of what the source has is the tool's bookkeeping rather than the text's.
