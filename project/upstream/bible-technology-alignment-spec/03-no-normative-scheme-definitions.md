---
Repository: bible-technology/alignment-spec
Status: DRAFT — not filed. Awaiting the Captain's approval.
Spec page: https://docs.burrito.bible/en/develop/flavors/alignment_flavor.html
---

# Title

```
Reference schemes are referenced by name but never defined
```

# Body

## A scheme name is a reference with nothing to resolve against

Every reference in this format depends on its scheme. A record's selectors are
uninterpretable without it — `40001001001` is eleven digits and nothing more until
something says how to divide them. The format handles this correctly in structure:
`scheme` is hoisted to the group's `documents` array, so each document declares which
scheme its selectors use.

```json
"documents": [
  {"docid": "SBLGNT", "scheme": "BCVWP"},
  {"docid": "BSB",    "scheme": "BCVW"}
]
```

But `"BCVWP"` is a *name*, and names resolve against definitions. There is no place in
this specification where a scheme is defined normatively. The only description of
`BCVWP` anywhere is in Appendix 1, under a heading that opens:

> The following are examples.

And there is no JSON Schema for the alignment content format. The schema in the
Scripture Burrito repository — `schema/alignment/alignment.schema.json` — constrains only
the `flavor` field in `metadata.json`; it says nothing about the content of an alignment
file.

So a consumer meeting `scheme: "BCVWP"` has nothing authoritative to look it up in, and a
producer writing it is asserting nothing checkable.

## What that costs, measured

In a published corpus of 21 alignment files in this format, `BCVWP` is declared for **four
different selector shapes**:

| declared | actual selectors |
|---|---|
| `BCVWP` | a letter prefix followed by 11 digits |
| `BCVWP` | a letter prefix followed by 12 digits |
| `BCVWP` | 11 bare digits |
| `BCVWP` | 12 bare digits |

The same corpus also declares two *different* names, `BCVWP` and `BCVW`, for selectors of
identical shape. Nothing detected any of this, because there is nothing to detect it
against. The declarations carry no information.

The specification's own description is internally inconsistent in the same way. Appendix 1
says:

> an 11-character `BBCCCVVVWWWP` string

and gives a 12-character example selector, `"410040030011"`. The Scripture Burrito flavor
page says 12. A reader cannot determine the intended width from the specification.

## Two things are missing

**1. A place where schemes are defined.** The format already treats a scheme as a shared
vocabulary — that is what hoisting a name into `documents` means. What it lacks is the
registry that name refers to. Defining schemes inline in each file would work but
duplicates one definition across every file that uses it, and copies drift; a registry
referenced by name is what the current syntax already implies.

**2. A notation for a scheme's shape.** `BCVWP` gestures at a layout without stating it.
A notation would need to express three distinct things, not two:

- **digit placeholders** — repetition showing field width, as `BBCCCVVVWWWP` does
- **true literals** — characters that appear verbatim in every selector
- **enumerated non-digit fields** — a position drawn from a fixed set of values

That third case is not hypothetical. In the corpus above, source selectors begin with a
single letter marking the testament: one value for Old Testament documents, another for
New. Within any one document it is constant and behaves as a literal; in a scheme spanning
both it is a field with two permitted values. A notation handling only literals and digits
cannot express it.

Four candidate forms:

| form | example | trade-off |
|---|---|---|
| quoted literals | `'n'BBCCCVVVWWW` | familiar from ICU and `SimpleDateFormat`; needs an escape for a literal quote. The prefix can only be a literal, so a cross-testament scheme is inexpressible |
| declared alphabet | `nBBCCCVVVWWW` | shortest, and width is visible at a glance; a literal `B` becomes unexpressible, the alphabet must be closed and published, and again the prefix can only be a literal |
| explicit fields | `{T:1}{B:2}{C:3}{V:3}{W:3}` | unambiguous and self-documenting; the width is stated rather than shown; requires the specification to define a new mini-language |
| **regular expression with named groups** | `^(?<T>[no])(?<B>\d{2})(?<C>\d{3})(?<V>\d{3})(?<W>\d{3})$` | invents nothing — every implementation language already has an engine; named groups give the field names and character classes give the enumerated values directly; verbose, and it admits patterns that are not fixed-width, so a validator can no longer assume one |

**The first two cannot name the prefix as a field at all.** A testament marker written as a
literal character is correct for a single-testament document and wrong for a scheme covering
both, so one logical scheme would need two names. The last two each make it a field with a
declared value set, and one scheme then covers both testaments.

Between those two, the regular expression has the decisive practical advantage of requiring
no new notation to be specified, implemented and tested — the specification would name an
existing flavour of regex rather than define a language of its own.

## A scheme definition has two parts, and the format has neither

A pattern says how to *split* a selector. It does not say what the pieces mean, where the
numbering comes from, or which edition the identifiers belong to — and a consumer deciding
whether two corpora can be compared needs exactly that. So a scheme entry needs both: a
machine-readable pattern, and a place to document the semantics.

```json
{
  "name": "...",
  "pattern": "^(?<T>[no])(?<B>\\d{2})(?<C>\\d{3})(?<V>\\d{3})(?<W>\\d{3})$",
  "description": "Word-level identifier used by <corpus>. Numbering follows <versification>.",
  "fields": {
    "T": {"values": {"o": "Old Testament", "n": "New Testament"}},
    "B": {"description": "book number"},
    "W": {"description": "word index within the verse, from 1"}
  }
}
```

Sketched to make the shape concrete, not as a proposal on the syntax. The two halves are the
point: the pattern is what a validator reads, the description is what a human reads when
deciding whether two datasets are talking about the same thing.

## The question

1. Should the specification carry a normative registry of reference schemes, rather than
   examples in an appendix?
2. What notation should a scheme use to state its shape? **Our recommendation is a regular
   expression with named groups** — it invents no new language, every implementation already
   has an engine, and it is one of only two candidates that can express the enumerated
   non-digit field every real scheme we have measured needs.
3. Should each scheme entry carry a prose description of its semantics as well as a pattern?
   A pattern alone does not let a consumer decide whether two corpora are comparable.
4. Should `BCVWP`'s stated length be corrected to match its example, independently of the
   larger question?

The appendix preamble already anticipates this:

> It has not yet been decided what reference schemes, alignment types, or alignment
> metadata are required to be supported by an implementation to be compliant with this
> specification. Interoperation will likely require compliance with this specification and
> with the particular reference scheme(s), alignment type(s), and alignment metadata
> field(s) used.

Interoperation requires agreement on the schemes used — and there is currently no document
in which that agreement could be written down.
