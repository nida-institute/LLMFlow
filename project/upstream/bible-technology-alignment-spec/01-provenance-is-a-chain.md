---
Repository: bible-technology/alignment-spec
Status: DRAFT — not filed. Awaiting the Captain's approval.
Spec page: https://docs.burrito.bible/en/develop/flavors/alignment_flavor.html
Note: the "provenance outside the file" section was added after drafting and is easily
      struck if you would rather this issue stayed narrow.
---

# Title

```
meta specifies one `creator`, but provenance of alignment data is a chain
```

# Body

## The gap

The information model gives each alignment record "who is responsible for the alignment
(possibly a computer program)", and the serialization section recommends `creator` and a
timestamp. In practice an alignment corpus accumulates more parties than that single slot
can name:

- the party that produced the alignment
- the party publishing this particular copy
- a party that corrected or re-derived it
- the copyright holder, which may be none of the above

A single `creator` string forces all of that into one value, and whoever serialises the
file chooses which fact it records. Two publishers choosing differently produce files that
are not comparable, and a reader cannot tell which fact it is holding.

## Why this is more than tidiness

Alignment data in this space is commonly published under CC BY, where attribution is a
licence term rather than metadata hygiene. If the field a consumer reads for attribution
may hold the producer, the publisher, or the copyright holder depending on who wrote the
file, the obligation cannot be discharged programmatically — and a consumer who republishes
propagates whichever value happened to be there.

Organisational change makes this ordinary rather than exotic. A corpus routinely outlives
the name of the body that produced it; renames, transfers and mergers are normal over the
lifetime of a Bible alignment dataset, and a file recording one name at one date carries it
forward indefinitely.

## Provenance today often lives outside the file

Where publishers do record the fuller picture, they tend to do it in a sidecar — a catalogue
listing licence, team and scope per alignment, beside the alignment files rather than in
them. That works while the catalogue and the files travel together, and fails the moment a
single alignment file is passed to someone on its own, which is exactly what this format
makes easy. The information exists; the format has nowhere to put it.

## The spec anticipates the problem

Appendix 3:

> I think at a bare minimum we want a timestamp and who is responsible for the record. But
> there are other use cases to discuss including confident level, curation, etc.

And the appendix preamble is explicit about the cost of leaving it open:

> It has not yet been decided what reference schemes, alignment types, or alignment metadata
> are required to be supported by an implementation to be compliant with this specification.
> Interoperation will likely require compliance with this specification and with the
> particular reference scheme(s), alignment type(s), and alignment metadata field(s) used.

Extensibility is the right mechanism. The gap is that nothing standard occupies it, so each
publisher will invent its own keys and none will interoperate.

## The question

1. Should the format recommend named fields distinguishing the roles `creator` currently
   conflates — produced, published, corrected, copyright held?
2. Should a licence be expressible per file or per group, given that one file may aggregate
   data from parties on different terms?
3. If this belongs in the burrito's own metadata rather than the alignment format — is that
   adequate for alignment files that circulate on their own, outside a burrito?
