# A dataset provides resources: retiring "edition"

**Status:** proposal, awaiting the Captain. Nothing is built.
**Issue:** none yet — see §7.

**Ruled by the Captain during design:**

1. **"Edition" is the wrong word.** *"these are not, for instance, NA26 vs. NA27, so that
   vocabulary is confusing"*.
2. **The model is resources within a dataset.** *"aren't these resources within a dataset?"*, and
   then, having weighed `target` against `resource`: *"let's go with resource"*.

---

## 1. The defect

`SBLGNT` names a TSV file inside the `Clear-Bible/macula-greek` corpus, read as `kind: tsv`, whose
references are numbered `org`. It is not a critical edition of the Greek New Testament. The same
critical edition could be registered twice — once as Macula's TSV, once as its lowfat XML — and
that would be two of these things and one edition. The word claims a textual-criticism distinction
the data does not make.

**The second defect is a conflation, and it has already cost.** `sp resource` means two different
things depending on the subcommand, and our own help text says so without noticing:

```python
res_add.add_argument("id", help="Catalog id (e.g. WLC), or the name to register yours under")
res_dl.add_argument("id",  help="Catalog id (e.g. acai)")
```

`acai` is a catalog entry — a repository you obtain. `WLC` is an item inside one, declared in the
`provides` block of the entry `macula-hebrew`. Both are called "catalog id". A `discourse-flow`
session ran `sp resource list`, saw only items of the inner kind, and concluded the engine did not
know Levinsohn's corpus — then proposed hand-writing an absolute path into the store. The Captain
stopped it.

## 2. The model

| layer | what it is | where it lives | word |
|---|---|---|---|
| **dataset** | an obtainable body of data — a repository or a download | a catalog entry; `~/.sp/datasets/` once present here | **dataset** |
| **resource** | a named readable thing inside one, carrying a reader and a versification | the `provides` block; `~/.sp/registrations/` | **resource** |

A resource is more than a path, and the excess is the part that matters: `kind` says how to parse
it, `versification_scheme` says which verse `PSA 51:1` is. A wrong path fails loudly; a wrong
versification returns the wrong verses in silence.

A resource need not sit inside a dataset — `sp resource add MINE --path …` registers one by path —
so "within a dataset" is the common case rather than the definition.

## 3. This completes a migration already underway

Two thirds of the rename happened without being finished:

- `~/.sp/editions/` became `~/.sp/registrations/` at #217, with the old name kept only for
  migration (`LEGACY_REGISTRATION_DIRNAMES`).
- The error type is already `ResourceNotRegistered` (`utils/scripture.py:143`), not
  `EditionNotRegistered` as #217's traceback shows it.

So the codebase currently holds both vocabularies, which is the state `one-design` exists to
prevent.

## 4. The measured surface

Counted 2026-09-08; re-derive with `grep -rio edition <dir> | wc -l`.

| where | files | occurrences | disposition |
|---|---|---|---|
| `src/` | 13 | 185 | rename |
| `tests/` | 28 | 389 | rename |
| `docs/` | 12 | 111 | rename |
| `src/llmflow/templates/` | 3 | 15 | rename, and re-sync the shipped copies |
| `data/` | 4 | 19 | **mixed — see below** |
| `project/` | 16 | 197 | **do not rename — see below** |

Public API carrying the word: `edition_scheme()`, `edition_text()`, `resolve_edition()`,
`load_registry_editions()`, `EDITION_TABLE_FILENAME`, `_EDITION_TABLE`.

**The pipeline language key.** `edition` is a step key (`pipeline_schema.py:250`), so this is a
breaking language change and takes the shape `design-foreach-syntax-migration.md` established: one
syntax, no aliases, the old key failing loud with a message naming the new one.

### `data/` is mixed

- `data/resources.json` is **vendored** from `nida-institute/awesome-biblical-data` and is
  currently identical to upstream. Under this model it is a catalog of *datasets* despite its
  name — but it is not ours, and editing it here is reverted on the next sync. **Leave it.** If
  the upstream vocabulary should change, that is a conversation with that repository.
- `data/versification-editions.json` is ours, and its `known_editions` key with it.
- `data/ai-rules.yaml` and `data/include-families.json` mention the word in prose.

### `project/` is the record, and records keep their own words

197 of the 616 occurrences are in plans, handoffs, `TODO.md` and audits. `one-design` says the
record *"is corrected by adding alongside, dated, never by rewording"*, and the test it gives is
whether changing the text makes a statement about the past false. It does: those documents record
what was decided when the word was "edition". **They stay as written.** This document is the entry
that supersedes them.

## 5. What the surface becomes

```yaml
- name: fetch
  type: scripture
  resource: SBLGNT            # was: edition:
  passage: "MRK 1:14"
  include: [ids, discourse]
  output: source
```

```bash
sp resource list                    # unchanged: the resources this machine can open
sp resource add SBLGNT              # unchanged
sp dataset search discourse         # was: sp resource search — it searches the outer layer
sp dataset add levinsohn-lgntdf --path ~/github/biblicalhumanities/levinsohn
```

`sp resource search` has **not shipped** — it was written this session and is uncommitted. Renaming
it now costs nothing; renaming it later costs a deprecation.

## 6. Consumers

Measured on this machine:

| repository | pipelines using `edition:` |
|---|---|
| `discourse-flow` | 3 |
| `sil-translator-notes` | 1 |
| `ears-to-hear` | 0 |
| `discourse-flow-hebrew` | 0 |

Four files across two repositories. Both install this tree editable, so the day the old key starts
failing is the day it is committed here — which argues for the failure message naming the new key
and for telling both repositories before the commit rather than after.

## 7. Decisions for the Captain

Answer inline after each `=>`.

### D1. Does the pipeline key change in this pass, or later?

Changing it is the breaking half. The rest — internals, CLI, docs — can land first and alone, and
would leave the language saying `edition:` while everything else says resource.

- **A** — one pass, key included. Coherent, and four consumer files need a commit each.
- **B** — internals and CLI now, the key in a later release with its own migration note.

=> **A. "in this pass."**

### D2. Is `sp resource` split into `sp resource` and `sp dataset`?

Today one command noun covers both layers, which is the conflation in §1. Splitting fixes it and
adds a second top-level noun.

=> **Yes.**

### D3. Does `data/versification-editions.json` get renamed, and its `known_editions` key with it?

It is ours. The rename touches `EDITION_TABLE_FILENAME`, the packaged data list and any consumer
reading it directly.

=> **Withdrawn — the Captain asked "why?", and the honest answer is that there was no good
reason.** It was proposed for vocabulary consistency, which is the weakest kind of reason for
moving a data file.

Checking it found something better. `known_editions` is **empty**, and
`tests/test_resource_provisioning.py:418` asserts it stays empty: the catalog answers that
question now, and *"only one may"*. So the key is a husk kept alive by the guard that asserts it
is a husk, and the file's only live content is `paratext_versification_numbers` — Paratext's
numeric codes mapped to scheme names, which concerns neither editions nor resources. **The file is
misnamed for a different reason than the one proposed**, and fixing that is its own small change:
delete the dead key, and name the file for what it now holds. It does not belong in a vocabulary
migration, where it would be noise in a diff that already touches 700 occurrences.

### D4. A GH issue, or this document alone?

`plans-first` accepts either. An issue gives the consumer repositories something to watch.

=> **A GH issue.**

**Superseded once the work was done, before the issue was filed.** The Captain, seeing the
drafted body: *"since its already implemented, just put it in the changelog"*. No issue exists;
the CHANGELOG entry carries the record, including what consumers must change. The earlier answer
stands above as what was ruled at the time.

## 8. Not in scope

The upstream vocabulary in `awesome-biblical-data`, whose catalog file is named for the inner word
while holding the outer kind. Renaming `~/.sp/registrations/`, which #217 already settled and which
this model does not disturb — a registration is the *file*, a resource is the *thing registered*.
