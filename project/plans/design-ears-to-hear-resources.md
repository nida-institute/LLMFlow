# Design — ACAI, SDBG senses and the Tyndale Open Bible Dictionary, for Ears to Hear

**Status:** decided (2026-10-14) — §7 answered: A, A, C, A, A, A; step 2's D-G–D-L answered
2026-10-15. Step 1 built at `cb15dbc`; step 2 built.
**Issues:** #272.
**Author:** AI, from Ears to Hear's request
(`collab/ears-to-hear/2026-10-06-acai-sdbg-and-the-tyndale-bible-dictionary.md`) and measurements
of this repository, `~/.sp` and the clones on this machine, taken 2026-10-14.

---

## 1. The request

Ears to Hear's `scriptorium/pipelines/build-book.yaml` now reaches every resource through `sp`, and
is already written against two shapes that do not exist yet. Its five asks:

1. **ACAI** for a passage — the entities that occur in it. Proposed as `type: acai`, with
   `resource`, `passage`, `versification` and `output`, like `type: parallel-passages`.
2. **SDBG** — each Greek sense's definition and gloss, carried on `include: [senses]`. No new
   syntax.
3. **The Tyndale Open Bible Dictionary**, for a passage or for an entry. Not in their pipeline yet.
4. **A confirmation** that `senses` on `SBLGNT` carries the letter-level Louw-Nida code.
5. **`sp lint` refusing a step type it does not declare.**

**Scope ruled by the Captain 2026-10-06:** the release after 0.2.1.29 focuses on Helm and Ears to
Hear support.

**What we tell Ears to Hear is the Captain's** (project rule "What we say to another project is
the Captain's"). This document records findings; any reply is drafted only when he asks.

## 2. What is true today, measured 2026-10-14

### The letter-level code — ask 4 is already true

- `include: [senses]` copies Macula's `ln` column verbatim (`src/llmflow/utils/scripture.py:615-653`,
  columns from `data/include-families.json:35-42`). `SBLGNT/tsv/macula-greek-SBLGNT.tsv` line 4:
  `093001  93.169a` for Ἰησοῦς in MAT 1:1. 93.169a occurs 904 times.
- **A word can carry several codes, space-separated** — `10.24 33.19` with domain
  `010002 033003`, on 2,396 tokens. A join on the whole `ln` string misses every one of them.
- **No test pins the letter form.** `tests/test_scripture_families.py` and
  `tests/test_analysis_format.py` use bare codes only.

### ACAI

- **The data:** `BibleAquifer/ACAI`, release 2025-07-23, CC BY-SA 4.0. Eight categories,
  `{category}/json/*.json`: people 3,426, places 1,418, groups 307, deities 79, keyterms 868,
  fauna 97, flora 104, realia 345.
- **What it was made about.** Its README: aligned to *"the word segmentation of Macula Hebrew and
  the text of the SBL Greek New Testament"*, references in the `ORG` scheme. Word references are
  keyed by edition — `"explicit_instances": {"SBLGNT": [["n57001001009"]]}`, and lowercase `"wlc"`
  for the Old Testament — and they are Macula word ids: `n57001001009` is Φιλήμονι in PHM 1:1 in
  Macula's SBLGNT. Verse references are BCV8 strings (`"57001001"`), with `key_references` as a
  subset. Under `analysis-belongs-to-its-text`, ACAI is an analysis of **SBLGNT and WLC** and of
  no other text.
- **The catalog:** `acai` (`data/resources.json:578-591`) has no `provides` block, so `readable()`
  treats it as having no reader.
- **The engine already reads it, internally:** `get_acai_entities_for_passage`
  (`src/llmflow/utils/bible_data.py:177-240`) scans all eight categories by verse range. It finds
  the data at a hard-coded `~/github/BibleAquifer/ACAI`, applies no versification, and is not a
  surface for projects.
- **This machine's registration points at the wrong repository:** `~/.sp/datasets/ACAI.yaml` →
  `/Users/jonathan/github/Clear/ACAI`, the tooling repository, not the release.
- **What Ears to Hear keeps from an entity:** `id`, category, English label, first English
  description, `lemmas`, and whether the verse is a key reference. They skip records whose `id`
  differs from `primary_id`. They group by verse and cap per verse and per pericope themselves —
  *"a judgment about our prompts, not about ACAI"*.

### SDBG

- **Ears to Hear read** `marble-lexicon/SDBG/SDBG-NN.XML`, a 2021 clone with **no licence file**;
  a 2025 clone also sits at `~/github/ubsicap/marble-lexicon`.
- **The catalog's `ubs-sdgnt`** acquires `ubsicap/ubs-open-license`, CC BY-SA 4.0, whose
  `dictionaries/greek/XML/UBSGreekNTDic-v1.1-en.XML` is *"extracted from the Semantic Dictionary of
  the Greek New Testament … Adapted from Semantic Dictionary of Biblical Greek"*.
- **Their question — the same data? Established: yes, the open file is an extract of the same
  database.** Same schema, same `Id` and `EntryCode` scheme, same letter-suffixed codes
  (`93.169a`–`e` in both), the same English definition, gloss and references for the entry
  checked (Rahab, `93.306`), the same entry count (5,507), and 9,178 meanings against 9,179.
  **Not established:** an entry-by-entry comparison. **Differences:** one file per language rather
  than 24 split files; `Code` attributes on domains; part-of-speech strings; newer edit dates; and
  the licence — stated in the open repository, absent from `marble-lexicon`.
- **A third copy:** Macula's own extracts, `macula-greek/sources/MARBLE/SDBG/`
  (`sdbg-senses.xml`, `sdbg-domains-glosses.xml`), inside a dataset already registered here as
  `macula-greek-lowfat`. Their content was not examined.

### The Tyndale Open Bible Dictionary

- **The release:** `TyndaleOpen/tyndale-open-bible-dictionary`, 2023, CC BY-SA 4.0 — about 6,010
  articles in `Articles/A.xml`…`Z.xml`, passages as inline links (`?bref=Phlm.1.2`), 44,133 of them.
  The catalog entry (`data/resources.json:477-491`) describes it as *"Addressed by topic rather
  than by passage"*.
- **Aquifer's adaptation:** `BibleAquifer/AquiferOpenBibleDictionary`, CC BY-SA 4.0, per language,
  with structured `associations.passage` (`"start_ref_usfm": "PHM 1:1"`) and
  `associations.acai` on each article.
- **ACAI links to it:** `alternate_sources.aquifer` = `"7708|Philemon (Person)|TyndaleBibleDictionary"`,
  and 7708 is the Aquifer article's `content_id`.
- `design-basex-collections.md` (proposal) already noted that a `provides` block cannot describe a
  dictionary today.

### Lint

`type: acai` passes because an undeclared type is treated as a plugin: `allowed_step_keys` returns
`None` (`src/llmflow/pipeline_schema.py:539-540`) and `_lint_step_keys` stops after a typo check
(`src/llmflow/utils/linter.py:2108-2119`). Nothing compares the type with `declared_step_types()`;
only the runner refuses it (`runner.py:382-383`). The constraint on a fix: lint must keep accepting
plugin types without loading plugins (`tests/test_lazy_plugin_discovery.py:59-73`). Built-in plugin
names are listed statically in `src/llmflow/plugins/loader.py:11-35`; a step carrying `plugin:`
dispatches by that key instead (`runner.py:376-378`).

## 3. ACAI — proposed

**A step type, `type: acai`, in the shape Ears to Hear proposed.** A relation to a passage, like
`parallel-passages`, so the same files change (§6).

```yaml
- name: acai_nt
  type: acai
  resource: SBLGNT            # SBLGNT or WLC — the texts ACAI was made about
  passage: "MRK 1:1-8"
  versification: org
  output: pericope_acai
```

- **Served only against SBLGNT and WLC.** Any other `resource` returns `null` with a warning —
  `analysis-belongs-to-its-text`. Which resource is which edition key (`SBLGNT`, `wlc`) is declared
  in the catalog's `provides` block for `acai`, not inferred.
- **Selection by verse**, from `references`, mapped through the request's versification into ACAI's
  `org` the way `parallel-passages` maps into its own scheme. Primary records only.
- **The payload — each entity once, plus a verse index** (D-C, C):
  `{"entities": {"<id>": {"type", "label", "description", "lemmas", "dictionary"}},
  "verses": {"<USFM verse>": [{"id", "key"}]}}`, verses in order. `key` is true where the verse is
  one of the entity's `key_references`. `dictionary` carries the Tyndale article id from
  `alternate_sources.aquifer`, or is absent (§5).
- **No capping.** Ears to Hear caps; the engine serves what ACAI says.
- **The data:** a `provides` block on the catalog's `acai` entry, and the dataset registered from
  the release repository. This machine's `~/.sp/datasets/ACAI.yaml` is the Captain's to correct.

## 4. SDBG — proposed

**SDBG's fields joined onto each Greek sense, from a registered SDGNT.** `include: [senses]` on
`SBLGNT` keeps `domain` and `ln` as today and gains, per Louw-Nida code in `ln`:

```json
"senses": {"domain": "093001", "ln": "93.169a",
           "entries": [{"code": "93.169a", "domain": "Names of Persons and Places",
                        "subdomain": "Persons", "definition": "…", "glosses": ["Jesus"],
                        "lemma": "Ἰησοῦς", "biblical_term": "Y"}]}
```

- **One entry per code**, so the 2,396 words with two codes get both. A code SDBG lacks is omitted
  from `entries` and named in a warning.
- **Joined on the word's lemma and the code** (D-H), because a code is not unique to one headword:
  1,393 of SDGNT's 7,103 codes are shared by several lemmas — `1.13` by ὑψηλός, ὕψιστος, ὕψος and
  ὕψωμα, each with its own definition. Where the lemma does not match, a code SDGNT files under
  exactly one headword still joins; a code shared by several is omitted and named in a warning
  (D-I). Each entry carries SDGNT's own `lemma`, so a fallback is visible.
- **From the open-licence SDGNT** (D-B, A), with the `{N:001}`-style suffix stripped from **both**
  sides before the join: Macula's `ln` writes `12.5`–`12.9` that way (616 occurrences of
  `12.9{N:001}` alone), and so do 5 of SDGNT's `EntryCode`s.
- **Declared in `data/include-families.json`** on the `senses` family, per resource, reached through
  a dataset registered as `ubs-sdgnt` (D-G) — the way `frequency` names its tables. Not a catalog
  `provides` block: the catalog is vendored and must equal its source, and a `provides` item is a
  text with kind `tsv`, `tei` or `usfm`.
- **SDGNT not registered:** `senses` as today, without `entries`, and one warning naming what to
  register (D-J).
- **English only**, in this release.
- **Greek only.** The Hebrew senses are SDBH domains; this does not touch them.
- **Served only on resources whose senses come from Macula's `ln`** — today `SBLGNT`.

## 5. Tyndale — proposed

**By entry, through ACAI; by passage, not in this release.**

- **By entry:** a step `type: dictionary`, `resource: tyndale-open-bible-dictionary`,
  `entry: <id>` or `entries: [...]` — returns each article's title and body.
- **By passage, through ACAI:** each ACAI entity carries its `dictionary` article id (§3), so "the
  articles for the people and places in this passage" is an `acai` step followed by a
  `dictionary` step, with no passage index of the dictionary at all.
- **Not by its own passage links.** 44,133 inline links include every verse an article cites in
  passing; an article that mentions MRK 1:4 is not thereby about it. Choosing which links count is
  a judgment the engine should not make silently — D-E.

## 6. Lint, and the confirmation

- **Lint refuses a step type that is neither declared in the schema nor a built-in plugin name**,
  unless the step carries `plugin:`. The plugin names are read from the static list, so no plugin
  is loaded. Message: the type, and the nearest declared type.
- **A test pins the letter-level code** on `SBLGNT` senses, and another the two-code case.

**Files a new step type touches** (measured on `parallel-passages`): `pipeline_schema.py`, a handler
in `steps/`, a reader in `utils/`, `runner.py`, `resource_preflight.py`, the catalog,
`docs/cli-api.json` (regenerated, test-guarded), `docs/sp-language.md` and the quickref (not
test-guarded), and tests on the three `parallel-passages` test files.

## 7. Decisions for the Captain

Answer after each `=>`.

### D-A. Which ACAI copy is the registered source?

- **A — the release, `BibleAquifer/ACAI`** (recommended): what Ears to Hear reads, CC BY-SA, dated
  releases.
- **B — the tooling repository, `Clear/ACAI`**, which this machine registers today: more data
  (events, images, maps) and no release.

=> A — the Captain, 2026-10-14

### D-B. Which SDBG copy is the registered source?

- **A — `ubs-open-license`'s SDGNT** (recommended): already the catalog's `ubs-sdgnt`, CC BY-SA
  4.0, one file per language, an extract of the same database. Not yet compared entry by entry —
  the build would add that check for every Macula code.
- **B — `marble-lexicon`'s SDBG**: what Ears to Hear used; no licence stated.
- **C — Macula's own MARBLE extracts**: already registered here; not examined.

=> discuss — the Captain, 2026-10-14; then **A** — the Captain, 2026-10-14, after the
measurement below.

**Measured for the discussion, 2026-10-14.** Macula's SBLGNT carries 7,018 distinct Louw-Nida codes
(131,028 occurrences, multi-code words split). Codes each copy fails to resolve:

| copy | licence | unresolved |
|---|---|---|
| `marble-lexicon`, 2021 clone (Ears to Hear's) | none stated | 0 |
| `marble-lexicon`, 2025 clone | none stated | 1 code, 2 occurrences (`33.403`) |
| `ubs-open-license` SDGNT v1.1 | CC BY-SA 4.0 | 7 codes, 638 occurrences — but 6 of them, `12.5`–`12.9`, are written `12.5{N:001}` there; stripping the `{…}` suffix leaves only `33.403` |
| Macula's own MARBLE extract | Macula's | not comparable — keyed by word id (`<word id="04000100100000">`), not by code |

So with the suffix normalised, the open copy and the 2025 clone cover the same codes.

### D-C. ACAI's payload: grouped by verse, or one list?

- **A — grouped by verse** (recommended): what Ears to Hear's working tree already consumes.
- **B — one list of entities**, each with its verses: closer to ACAI's own shape; Ears to Hear
  regroups.
- **C — each entity once, plus a verse index** — added in the discussion, 2026-10-14:
  `{"entities": {"<id>": {…}}, "verses": {"MRK 1:4": [{"id": "<id>", "key": true}]}}`. No text
  repeated; the by-verse view and key-reference flags kept. Ears to Hear looks each id up.

=> discuss — the Captain, 2026-10-14; then **C** — the Captain, 2026-10-14, after the measurement
below.

**Measured for the discussion, 2026-10-14** — primary ACAI entities whose `references` fall in the
pericope, and the rows grouping by verse produces:

| pericope | entities | rows by verse | repetition |
|---|---|---|---|
| MRK 1:1-8 | 23 | 28 | 1.2× |
| MAT 19:1-12 | 18 | 20 | 1.1× |
| MAT 5:1-48 | 44 | 88 | 2.0× |
| JHN 11:1-44 | 31 | 97 | 3.1× |

### D-D. SDBG on each sense: an `entries` list, or flat fields?

- **A — `entries`, one per code** (recommended): one shape, and two-code words keep both.
- **B — flat `definition`, `gloss`, `subdomain` on the sense**: what Ears to Hear's code reads
  today; a two-code word gets only its first code.

=> A — the Captain, 2026-10-14

### D-E. Tyndale in this release?

- **A — by entry, and by passage through ACAI** (recommended), as §5.
- **B — also by its own passage links**, from Aquifer's `associations.passage`, accepting that a
  cited verse is not a topic.
- **C — not in this release**: Ears to Hear's pipeline does not use it yet.

=> A — the Captain, 2026-10-14

### D-F. Lint on an undeclared step type: error or warning?

- **A — error** (recommended): what Ears to Hear expected, and a misspelt type stops at lint.
- **B — warning**: a project-local plugin that registers its own type at load time still lints
  clean.

=> A — the Captain, 2026-10-14

### Step 2's decisions, 2026-10-15

Raised while preparing build step 2, from what the code and data showed.

**D-G. Where SDGNT is declared.** A — in `data/include-families.json` on `senses`, through a
dataset registered as `ubs-sdgnt` (recommended); B — a new catalog `provides` kind, `lexicon`,
made upstream first.

=> A — the Captain, 2026-10-15

**D-H. The join key.** Code alone gives a word another lemma's definition wherever a code is
shared; lemma and code (recommended), with the match rate measured first.

=> lemma and code — the Captain, 2026-10-15

**D-I. A word whose lemma does not match.** A — fall back to the code where SDGNT has one lemma
for it, omit and warn where it has several, and carry SDGNT's `lemma` on each entry (recommended);
B — strict, omit and warn on every mismatch; C — as A, but an ambiguous code gets every candidate.

=> A — the Captain, 2026-10-15

**D-J. SDGNT not registered.** A — `senses` without `entries`, and one warning (recommended); B —
lint or the run fails.

=> A — the Captain, 2026-10-15

**D-K. Glosses on an entry.** 6,504 of SDGNT's 9,178 meanings carry more than one gloss, up to
seven (`1.16`: "Abraham's bosom", "heaven"). A — `glosses`, a list in SDGNT's order
(recommended); B — `gloss`, the first only, as §4's example had it.

=> A — the Captain, 2026-10-15

**D-L. The markup inside a definition.** SDGNT's definitions carry `{N:001}` note markers,
`{L:εὐαγγελίζω<SDBG:εὐαγγελίζω:000000>}` lemma links and `{D:33.215}` cross-references — found
running the built join on MRK 1:1-8. A — verbatim, as the family table already rules for
participant ids (recommended); B — rendered to plain text; C — both, as `definition` and
`definition_source`.

=> A — the Captain, 2026-10-15

**Measured for D-H and D-I, 2026-10-15.** Every Louw-Nida code on a Macula SBLGNT word (`ln`, split
on spaces, `{N:…}` stripped), against SDGNT v1.1's `(Lemma, EntryCode)`, both NFC:

| result | occurrences | share |
|---|---|---|
| lemma and code match | 128,223 | 97.86% |
| code matches, SDGNT files it under one other lemma | 2,055 | 1.57% |
| code matches, SDGNT files it under several other lemmas | 747 | 0.57% |
| code absent from SDGNT — `33.403` (2), `3.21` (1) | 3 | 0.00% |

The commonest mismatches: spelling (τις / τὶς, 379; οὕτω(ς) / οὕτω, 149), a meaning filed under
another headword (ἑαυτοῦ `92.11` under αὐτός, 440; Ἰερουσαλήμ `93.480a` under Ἱεροσόλυμα, 71;
φοβέομαι under φοβέω, 77), and genuine ambiguity (ἰδού `91.13` under ἄγω and ὁράω, 195). With D-I
A, 99.43% of codes get an entry.

**Corrects D-B's table:** the suffix is on both sides, not on SDGNT's alone; and `3.21` is absent
as well as `33.403`, which the earlier count missed.

## 8. Not in this design

- **The catalog is vendored from `awesome-biblical-data`.** `provides` blocks added here belong
  upstream too; that is the open item already in `project/TODO.md`.
- **ACAI by word** (`explicit_instances`, pronominal and subject referents) — available, not asked
  for.
- **Hebrew senses** joined to SDBH definitions — the same idea for WLC, not asked for.
- **A reply to Ears to Hear** — the Captain's, when he asks for one.
