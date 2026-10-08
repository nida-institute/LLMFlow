---
Repository: bible-technology/scripture-burrito
Status: DRAFT — not filed. Awaiting the Captain's approval.
Note: the corpus is described generically. Naming it is a one-word change if wanted.
---

# Title

```
Rights can be attributed to a party, or scoped to an ingredient, but never both
```

# Body

## The case

An alignment burrito routinely bundles work owned by several different parties, and which
party owns which part is the fact a consumer needs. A real example, from a published corpus
of word alignments:

| what | held by |
|---|---|
| the Greek source text | the Society of Biblical Literature and Logos Bible Software |
| the **tokenization** of that Greek text | Clear Bible, Inc. |
| the target translation | public domain |
| the **tokenization** of the target | BiblioNexus |
| the alignment itself | BiblioNexus |

Five parties, five distinct things owned. Across the 21 files of that corpus there are
**14 distinct rights statements** spread over those five roles.

The alignment is not usable without the tokenizations: the selectors in an alignment record
are identifiers into tokenized texts, so the token files travel with the alignment. Their
rights travel with them.

## What the schemas can express

**`agencies[]`** names parties and gives each a role from a fixed enum — `rightsAdmin`,
`rightsHolder`, `content`, `publication`, `management`, `finance`, `qa`. Those describe a
party's *function*, not *what they hold rights over*. With five rights holders, five
`rightsHolder` entries are indistinguishable.

**`copyright.shortStatements[]`** takes `statement`, `lang` and `mimetype`, with
`additionalProperties: false`. Several statements can be listed; nothing says what any of them
covers.

**`copyright.licenses[]`** takes `url` **or** `ingredient` — so a licence *can* be scoped to a
particular file in the burrito. But the entry carries no party, so it says "these terms apply
to this file" and never "this party holds it".

**`relationships[]`** can link to source and target burritos, which would carry their own
rights. That helps for the texts, and not for the tokenizations: there is no relation type for
"tokenization of", and the tokenized files are ingredients of the alignment burrito rather
than separate publications. It also requires those burritos to exist and be obtainable, which
for many source texts they do not.

So the two halves exist separately — a party with a role, and a licence with an ingredient —
and nothing joins them.

## Why it matters beyond tidiness

This data is commonly published under CC BY, where attribution is a licence term. A consumer
who cannot determine which party holds which part cannot discharge the obligation
programmatically, and a consumer who republishes propagates whatever was nearest.

It also degrades over time in a way that is hard to notice. Where the format cannot express
the distinction, publishers record it in sidecar files of their own design — which is where
the table above comes from. Those sidecars are outside the burrito, are not validated, and are
lost the moment a single file is passed to someone on its own.

## The question

1. Should an `agencies[]` entry be able to name what it holds rights over — an ingredient
   path, or a role naming the kind of artifact?
2. Alternatively, should `copyright.shortStatements[]` gain an optional `ingredient`, matching
   the scoping `licenses[]` already has?
3. Is there an intended modelling of this that we have missed — in particular, are the
   tokenized token files meant to be separate burritos linked by `relationships`, and if so
   under what `relationType`?

Raising it as a question rather than a proposal: the corpus above is real, and we would rather
record what the format cannot currently say than guess at the fix.
