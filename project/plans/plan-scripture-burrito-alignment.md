# Plan — Scripture Burrito alignment conformance

Status: ruled (2026-09-11)

The Captain's rulings, recorded so they are not re-asked. Where a line quotes him, the quote
is the ruling and is not to be reworded.

## The goal

Make Bible alignment data conform to the Scripture Burrito alignment specification, and fix it
at the generator rather than in the data. Three things follow from that, and a fourth started it.

1. **`biblealignlib` is the generator** — Biblica's library, and the source of the published
   files. Work happens there: a branch, then pull requests to its author.
2. **The published data is `Clear-Bible/Alignments`**, which regenerates once the library is
   right.
3. **The specification is the proposed one** — *"this must follow the proposed alignment spec,
   that's the whole point of it"* — at https://github.com/bible-technology/alignment-spec,
   version 0.4, which the flavor page refers to:
   https://docs.burrito.bible/en/develop/flavors/alignment_flavor.html
4. **What raised it:** `discourse-flow` asked for a step type returning target-language text for
   a span named by source word ids. That step is named **`scripture-alignments`**, following the
   one multi-word precedent in the language, `for-each`.

## Rulings

| # | ruling |
|---|---|
| R1 | Use the **public** repository, `Clear-Bible/Alignments`, and read the public set. |
| R2 | The reader supplies the missing headers; a conversion capability exists alongside. |
| R3 | Fix the generator, not the data. Open a branch on `biblealignlib`, *"make changes to support the current spec, and then issue pull requests as needed"*. |
| R4 | **One branch per PR, cut from `main`.** `burrito-spec-0.4` is the local integration branch. |
| R5 | No plan file for the small library fixes; a short one for the TOML and container work. This file. |
| R6 | **The data source chooses the format for ids; the library does not.** |
| R7 | **The regex is derivable from the data.** The semantics may or may not be available — a source might use UUIDs. Both the regex and a place to document semantics are wanted. |
| R8 | The scheme **records the format used by the data source**. *"worst case, we simply record the format used by the data source, without knowing the semantics. best case, it's documented somewhere or easy to grok."* |
| R9 | A library may define its own identifier scheme — e.g. record `meta.id` — **as long as it documents it**. |
| R10 | **Mine the TOML when converting.** It carries copyright and licence, which a valid Scripture Burrito requires and which exist nowhere else. |
| R11 | **Hold the Working Group issues.** Discuss and resolve them in the group before baking anything into the specification's examples. |
| R12 | **Harvest real data** from the public repository to replace the toy examples in the spec — after R11. |
| R13 | Accumulate candidate issues in `tmp/issues`, organised by target repository. |
| R14 | **Copyright-restricted data** (`alignments-eng` and the other per-language repositories) never enters a public issue, PR, test fixture or example. |
| R15 | Commits, pushes and merges are the Captain's. Nothing is written into another organisation's repository without asking. |
| R16 | **`confidential` states whether the existence of a particular translation in a language is sensitive.** Most are not. **None of the public alignments are**, so `confidential: false` throughout. It is a security question, not a licensing one — a copyright-restricted translation is publicly known and merely licensed, which is a different fact from a project whose existence must not be revealed. |
| R20 | **R19 is about what gets written to disk, not about a library's internals.** *"I don't care about internal tokens, I only care about what gets written to disk. Leaving their internals alone as much as possible is good."* So a token model may normalize identifiers for its own lookups; what it must not do is emit a reshaped identifier into a file. The fix is at the serialization boundary, not through the object model. |
| R19 | **Keep the identifiers of the original source. This is data integration, and it is one of its first principles.** *"Identifiers are opaque, we have no right to change them, they belong to the data creator. If we change them, they no longer work in the original environment they came from, and those environments cannot use our alignments."* Reshaping a selector — stripping a prefix, truncating a part digit, inferring a prefix that was not there — makes the alignment unusable by the environment that produced the text. This governs every read and write path, not just conversion. It does **not** cover a library's own identifiers, such as an alignment record's `meta.id`, which R9 allows a library to define and document. |
| R18 | **Where the standard cannot represent something the data has, raise an issue against the standard in `tmp/issues` — and the reader and writer support it regardless.** The library does not wait for the specification to catch up, and the gap is not silently dropped. |
| R17 | **Identifiers are taken from the source translation, whatever it uses** — *"we normally take some id from the source translation, whatever it uses. Often some form of B+C+V+P?"* So for alignments being created, the format is not declared separately: it is inherited from the token files the ids come from, and the regex describing it is derived from those (R7). "Often" is precisely why it is derived rather than assumed. |

## State

**Done — W1, the top-level envelope.** Committed `d85d846` on `spec-0.4-envelope`, pushed, open
as `Clear-Bible/biblealignlib` PR #4. The writer emits `{format, version, groups}`; `unwrap_group`
reads both that and a bare 0.3 group; `meta.conformsTo` is no longer written; the module docstring
points at the current spec. 371 tests pass, with three pre-existing errors needing an
`alignments-hin` repository not on this machine.

**Done — the TOML reader.** Committed `cece064` on `toml-metadata`, pushed, open as PR #5.
`TomlMetadata.from_path()` reads a sidecar into dataclasses that keep the five rights roles
distinct — source text, source tokenization, target text, target tokenization, alignment — and
raises `ValueError` naming the file when it cannot parse. The Python floor rises to 3.11 for
`tomllib`. 373 tests pass; verified against the corpus at 17 read and 4 refused.

**Raised — the container cannot scope rights to an artifact** (R18):
`tmp/issues/bible-technology-scripture-burrito/01-rights-cannot-be-scoped-to-an-artifact.md`.
Drafted, not filed.

**Not started — the scheme work.** Under R6 and R8 this is *not* deriving a semantic label: it is
carrying the format the source declares, and deriving a regex that describes it (R7). The library
currently invents the value in three places — `Document.scheme`'s default, `AlignmentsReader`'s
class attribute, and the docid-based downgrade in `Document.__post_init__` — and discards what the
file declares.

**Not started — the TOML and the burrito container.** Nothing in the library opens the TOML, and
no `metadata.json`, `flavorType` or ingredients are ever written.

## What a valid alignment burrito needs, against what the TOML holds

`source_metadata.schema.json` requires `format`, `meta`, `idAuthorities`, `identification`,
`confidential`, `type`, `copyright`, `ingredients`. (`languages` is required only for the
`scripture` flavor, so an alignment burrito is exempt.)

- **From the TOML:** `copyright` (`alignment.license` on all 17 readable files;
  `alignment.copyright` on 8), `identification` (`alignment.identifier`, `target.name`,
  `target.url`), and `type.currentScope` from `alignment.scope`.
- **Computed:** `ingredients`, from the files themselves.
- **Constant:** `format`, and `type.flavorType`.
- **Ruled, not mined:** `confidential` is `false` for every public alignment, per R16.
- **Absent everywhere:** `idAuthorities`.

Two known obstacles, recorded as facts rather than decisions:

1. The `copyright` block takes a URL, an ingredient path, or a prose statement — not a licence
   identifier. The TOML says `CC-BY-4.0`.
2. Four TOMLs do not parse (`arb/AVD` both, `arb/ONAV`, `eng/BSB/BGNT-BSB`), so those four have no
   provenance to mine.

## Open

Genuinely undecided, as distinct from things already ruled above:

- Whether the scheme-registry question (`tmp/issues/bible-technology-alignment-spec/03-*.md`) is
  settled in the Working Group before or after the library work that depends on it. R11 holds the
  issues; the library can carry and derive formats (R7, R17) without a registry, but cannot put a
  standard *name* on one until the group has a vocabulary.

Closed 2026-09-11 by R17: where a data source declares its format for alignments being created.
The ids come from the source translation, so there is nothing to declare separately.
