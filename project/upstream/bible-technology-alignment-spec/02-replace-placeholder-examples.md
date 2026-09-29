---
Repository: bible-technology/alignment-spec
Status: DRAFT — not filed. Awaiting the Captain's approval.
Spec page: https://docs.burrito.bible/en/develop/flavors/alignment_flavor.html
Depends on: 03-no-normative-scheme-definitions.md — the `scheme` values shown in the
            worked example below are whatever that issue settles on. This issue should not
            be filed in a form that bakes in the current names, which are wrong.
---

# Title

```
Replace the placeholder examples with real, openly-licensed alignment data
```

# Body

## The examples show the shape but not the substance

Every JSON example in the serialization section uses placeholders — `<reference unit 1>`,
`"selector1"`, `"some-aligner"`, `"..."` for `scheme` and `docid`. A reader can see the
structure but not what a real selector looks like, what a realistic record contains, or
which cases are hard.

Of the three concrete examples in Appendix 1, two use `mydoc.txt`. The third is real but has
two problems:

```json
{ "scheme": "BCVWP", "docid": "NA27", "selectors": ["410040030011"] }
```

1. **The text is not openly licensed**, so a reader cannot obtain the corpus the example
   refers to and check it against the specification.
2. **The prose and the example disagree on length** — the text says "an 11-character
   `BBCCCVVVWWWP` string"; the selector shown is 12 characters, and the Scripture Burrito
   flavor page says 12. (Raised separately in the scheme-definition issue.)

## What one real record shows that no placeholder does

A single genuine alignment, from an openly-licensed Greek New Testament and an
openly-licensed English translation, at Matthew 1:1:

```json
{
  "format": "alignment",
  "version": "0.4",
  "groups": [
    {
      "type": "translation",
      "documents": [
        { "scheme": "<per the scheme-definition issue>", "docid": "SBLGNT" },
        { "scheme": "<per the scheme-definition issue>", "docid": "BSB" }
      ],
      "roles": ["source", "target"],
      "records": [
        { "source": ["n40001001001"],
          "target": ["40001001001", "40001001002", "40001001003", "40001001004"] }
      ]
    }
  ]
}
```

The single Greek word **Βίβλος** aligned to the four English words **"This is the record"**.
That one record demonstrates what the present examples do not:

- **a genuine one-to-many alignment**, which is the ordinary case rather than an edge case —
  the placeholder `["selector1", "selector2"]` gestures at this without showing why it
  matters;
- **selectors a reader can look up** in a published corpus and verify against the text;
- **source and target on different tokenisations** — the Greek is addressed per word, the
  English per word of a different text, so the two selector spaces are unrelated and the
  alignment is the only bridge between them. Nothing in the current examples makes that
  visible.

## Harder cases worth showing too

A specification's examples set expectations about what is normal. Three cases that occur
throughout real alignment data and appear nowhere in the current examples:

- a source unit aligned to a **non-contiguous** run of target tokens, which is ordinary
  wherever word order differs between languages;
- target tokens inside an aligned range that **no source token aligns to** — punctuation and
  supplied words — so a consumer reconstructing text from an alignment has to decide what to
  do with them;
- a **many-to-many** unit, which the information model explicitly distinguishes from several
  one-to-one alignments, and which no example illustrates.

## Offer

An openly-licensed corpus of alignments in this format already exists and is maintained as a
working proposal for this specification. Worked examples could be drawn from it directly and
kept in step as the specification develops.
