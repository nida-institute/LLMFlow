# Design: Named Scripture Editions in the Engine

## Status: Sources approved; core implemented, wiring outstanding

Main target for the next version. Issue [#200](https://github.com/nida-institute/LLMFlow/issues/200).

All three sources and their serialisations are the Captain's, ruled 2026-08-17. `utils/scripture.py`
is built and tested against the real data in both languages. Outstanding: the `type: scripture`
step, edition registration, the pericope reader, and docs.

---

## Problem

Every project that needs scripture text builds its own loader, and they converge on the one
shape the conventions forbid — a list of verse objects. Measured across three consumer repos,
each of these is independently implemented in all three:

| Capability | ears-to-hear | discourse-flow | discourse-flow-hebrew |
|---|---|---|---|
| scripture text / USJ | 16 files | 33 | 19 |
| Macula morphology / syntax | 7 | 47 | 18 |
| lexicons | 13 | 10 | 6 |
| ACAI entities | 19 | 6 | 4 |
| reference parsing | 71 | 89 | 45 |

`parse_bible_reference()` is imported 23 times, so the engine's offering is known and used —
and 49 files still define their own reference parser. The engine gives a piece; the pipeline
needs the job.

Two consequences worth naming precisely:

**The engine has the format machinery but no notion of a named edition.** `load_usfm_passage()`,
`_extract_verse_range_usj()` and `_usx_to_usj()` all require a `base_dir` and `project_name` —
you must already know where a text lives. There is no way to ask for "SBLGNT, MRK 1:1-8".

**Because each project loads raw assets itself, each inherits the asset's shape.**
`discourse-flow/plugins/source_language.py::_load_bsb` returns `{"Mark 1:1": "…"}` — a
verse-keyed dict. That is not carelessness: the file it is handed, `bsb-vline-refs.txt`, is
verse-per-line. While projects load raw assets, "verses are milestones, not containers" stays a
rule assistants are told while the data contradicts it.

---

## Sources — the Captain's, not the assistant's

Named by the Captain, 2026-08-17. **An assistant must not substitute a "reliable" source on its
own judgement.**

| Edition | Project | Status |
|---|---|---|
| WLC (Hebrew) | `~/github/Clear/macula-hebrew` | chosen |
| SBLGNT (Greek) | `~/github/Clear/macula-greek/SBLGNT` | chosen |
| BSB | `~/github/usfm-bible/examples.bsb` | chosen |

Rejected by the Captain: unfoldingWord UGNT and UHB.

### Serialisation — RESOLVED 2026-08-17: TSV for WLC and SBLGNT

The Captain named the `tei/` directories. Each Macula project also ships `lowfat/`, `nodes/` and
`tsv/`, and they are not equivalent for this purpose:

| Form | Carries `@after`? | Notes |
|---|---|---|
| `tei/` | **no** — 0 occurrences in either language | Verse milestones present. Hebrew uses `<verse>` wrappers and significant whitespace; Greek uses milestones only and is pretty-printed, so whitespace must be normalised. Two dialects, two rules. |
| `lowfat/` | yes, on `<m>` (Hebrew) and `<w>` (Greek) | Hebrew `<p>` already holds finished running text per verse. Hebrew is per-chapter (933 files), Greek per-book (32). |
| `tsv/` | **yes, an `after` column** | One flat table: `ref`, `text`, `after`. Identical handling for both languages. |

The TSV route was tested and produces correct text in both languages:

```
⌊1:1⌋ בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃
⌊1:2⌋ … וְחֹ֖שֶׁךְ עַל־פְּנֵ֣י תְה֑וֹם …          ← maqqef joins, sof pasuq attaches

⌊1:1⌋ Ἀρχὴ τοῦ εὐαγγελίου Ἰησοῦ χριστοῦ.
⌊1:2⌋ Καθὼς γέγραπται ἐν τῷ Ἠσαΐᾳ τῷ προφήτῃ·Ἰδοὺ ἀποστέλλω …
```

`text + after`, concatenated. No whitespace inference, no per-language branching, ~40 lines.

**Captain's ruling, 2026-08-17: WLC and SBLGNT read straight from the TSVs for running text.**

So the engine carries two backends, because the three chosen sources are not one shape:

| Edition | Source | Backend |
|---|---|---|
| WLC | `macula-hebrew/WLC/tsv/macula-hebrew.tsv` | TSV — `text` + `after` |
| SBLGNT | `macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv` | TSV — `text` + `after` |
| BSB | `usfm-bible/examples.bsb` (Captain, 2026-08-17) | USFM → USJ → milestones |

Both backends produce the same contract: running text, verse positions marked, never a per-verse
container.

### BSB — RESOLVED 2026-08-17: `usfm-bible/examples.bsb`

The prompt in `sil-translator-notes` quotes BSB, so the first consumer needs it.

- `sp`'s own catalog entry `berean-usx` points at `Freely-Given-org/OpenEnglishBible`, which
  **404s**, and is mislabelled — OEB is a different translation, which the Captain has said is
  not wanted. Filed as #201.
- `discourse-flow` currently uses `Clear/internal-Alignments/data/bsb/bsb-vline-refs.txt`,
  verse-per-line.
- **Chosen by the Captain: `usfm-bible/examples.bsb`** — per-book USFM, which
  `load_usfm_passage()` already reads via `usfmtc`. Book codes come from file *content*, so the
  BSB/discourse-flow book-numbering mismatch does not arise on this path.
- It carries `\s1` section headings — editorial pericope boundaries for all 66 books. Mark has 96,
  against discourse-flow's 94 analysed pericopes, so the granularity is comparable. Not adopted as
  a pericope source; recorded because it exists.
- **Defect found and fixed upstream:** `21ECCBSB.usfm` had no `\id` line, the only one of 66
  missing it, so parsers skipped Ecclesiastes entirely and a request for `ECC 3:1` returned "no
  text found" — indistinguishable from a bad reference. Upstream PR
  [#7](https://github.com/usfm-bible/examples.bsb/pull/7), closing their #4. **Until it merges, the
  local checkout depends on a patch on its `dev` branch**; lose that branch and Ecclesiastes
  silently disappears again. An argument for checking `\id` completeness at registration time.
- The repository has **no licence file**. The BSB text is freely usable, but that is worth
  confirming before the engine hard-depends on this repository.

---

## Design

### A step, not a function

```yaml
- name: fetch_source
  type: scripture
  edition: SBLGNT              # named; the engine resolves the location
  passage: "${passage}"        # book, chapter, or verse range
  format: milestones           # usj | milestones | plain
  output: source_text
```

Editions resolve through the registry (`~/.sp/`), never a literal path. Two reasons: the
absolute paths currently embedded in `ears-to-hear` and `discourse-flow` pipelines mean those
pipelines run on one laptop; and the *source* then stays configuration the Captain controls
rather than a constant an assistant chose.

### Representations, this version

| `format` | Shape | For |
|---|---|---|
| `milestones` | `⌊1:1⌋ …` running text | LLM prompts — text intact, verse positions marked |
| `plain` | running text, no markers | quotation, display |
| `usj` | USJ object | structural work, other USJ-aware steps |

**Deliberately absent: a list of verse objects.** Not offered, so it is not the default path. A
caller who genuinely needs per-verse records can derive them.

Deferred to a later version: `tokens`, `syntax`, `senses`, `entities`. Those are the rest of
#200 and want their own design.

### Pericopes

Chunking on pericope boundaries is the Captain's decision for `sil-translator-notes`.
Authoritative lists are produced by `discourse-flow` and `discourse-flow-hebrew`:

| | Books |
|---|---|
| Greek | MAT, MRK, LUK, JHN, PHM, 1JN, REV |
| Hebrew | GEN, RUT, PSA, OBA |

Eleven books. Requesting any other book must **error, naming the books that are available** —
not fall back to arbitrary chunks. Generating more is a `discourse-flow` run: time and money,
and the Captain's call.

Two hazards recorded:

- The two repos store them at different paths, both currently under singular `output/`. Those
  paths will change when those repos are migrated. **Consuming them by path is fragile** —
  another argument for a registry entry (#201 asks whether produced resources belong in the
  registry at all).
- The sources number books differently — BSB USFM uses MAT=41, discourse-flow uses MAT=40.
  **Join on the three-letter code. Book numbers are not authoritative** (Captain, 2026-08-17).

---

## Implementation Plan

Test-driven, per CLAUDE.md.

1. **Failing tests first**, asserting real text for both languages: maqqef joining
   (`עַל־פְּנֵ֣י` with no space), sof pasuq attachment, Greek punctuation attachment, and
   `⌊ch:v⌋` placement at verse boundaries. Fixtures drawn from the chosen source.
2. `utils/scripture.py` — reference range → rows → running text. Pure, no network.
3. Edition resolution from the registry, with a clear error when an edition is not registered.
4. `steps/scripture.py` plus the schema branch and linter keys.
5. Pericope reader, with the available-books error.
6. `sp lint` checks the edition is registered and the passage is within the text — before spend,
   consistent with #196.
7. Docs: `docs/llmflow-language.md` gains the step; `docs/architecture.md` gains the resolution
   path.

### Out of scope

- Migrating `ears-to-hear`, `discourse-flow`, `discourse-flow-hebrew` off their own loaders.
  Worth doing, separate decision, and two of those repos have their own AI.
- `tokens`, `syntax`, `senses`, `entities`.
- Dataset freshness and version tracking — #201.

---

## Questions for the Captain

1. ~~Serialisation~~ — resolved: TSV for WLC and SBLGNT.
2. ~~BSB source~~ — resolved: `usfm-bible/examples.bsb`.
3. **`type: scripture`, or a `load` variant** (`type: load_scripture`) alongside the existing
   loader steps?
4. Is `⌊ch:v⌋` the canonical milestone delimiter, or an ears-to-hear convention that should be
   reviewed before the engine adopts it?
