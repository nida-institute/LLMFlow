# Plan: Migrate Registered Pipelines to `sp clean` Directory Scheme

**Status:** Rule corrected and **executed 2026-08-17** — see the survey section at the foot for what was done, what was deliberately left, and by whom.

The rule this plan turned on was inverted and is now fixed (see below): the **directory** is
plural `outputs/` everywhere, the **keyword** is singular `output:`. The earlier
`discourse-flow` exception is withdrawn — per the Captain it was chaos, not intent.

The scope was mostly *other repositories*, so it needed a read-only survey before any edits. Two
repos have their own AI working in them (`discourse-flow`, `discourse-flow-hebrew`) and were left
to it.

One correction to an earlier reading: the uncommitted pipeline changes found in several consumer
repos were **not** other people's work in progress. They were this session's own keyword rename
(`outputs:` → `output:`, `timeout:` → `timeout_seconds:`, `llmflow run` → `sp run`), which had also
added `output_file_directory: "output"` — the singular spelling — by following this plan's original
rule. The decoy was introduced here and corrected here.

That survey has since been run and the migration carried out — **the per-repo sections below are
superseded by the "Survey and execution — 2026-08-17" section at the foot of this file.** Read that
first; the sections below record what was believed true when the plan was written.

Within the Scripture Pipelines repo itself the migration appears complete: every pipeline declares
`output_file_directory: "outputs..."`.

---

## Background

`design-clean-command.md` introduced `intermediate_file_directory` and `output_file_directory` as
top-level pipeline YAML keys. A previous session updated 9 pipelines in the Scripture Pipelines repo and all
pipelines in discourse-flow and discourse-flow-hebrew before being interrupted.

This plan covers:
1. Adding declarations to all remaining pending pipelines
2. Moving existing data to the right directory in the new scheme
3. Resolving `output/` vs `outputs/` conflicts (standardize on `output/` unless pipeline intentionally uses both)

---

## Rule: `output` vs `outputs` — corrected 2026-08-17

**Two different things, and conflating them is what made this plan wrong:**

| | Spelling | Why |
|---|---|---|
| The **keyword** in pipeline YAML | `output:` — **singular** | one step, one named result |
| The **directory** on disk | `outputs/` — **plural** | a directory holds many |

So: `output: scene_list` names a result; `output_file_directory: "outputs/..."` names a place.

This plan originally said *"Pick `output/` (singular) as the standard for repos that have both."*
That was wrong for directories, and following it would recreate the `output/` decoy that `9345a00`
removed from `sp init`. **The directory is `outputs/` everywhere, with no exceptions.**

The earlier exception for `discourse-flow` — recorded as an intentional split between
`output/intermediate` and `outputs/book-discourse` — was not intentional. Per the Captain,
2026-08-17: it is chaos, not design. It gets normalised like everywhere else.

Where a pipeline currently declares a singular path, **fix the declaration, not the data.** Moving
data into `output/` to match a wrong declaration is the opposite of the fix.

---

## Section 1: YAML-Only Changes (no data moves)

### Scripture Pipelines repo — `pipelines/`

| File | Declaration(s) to add |
|------|----------------------|
| `hello-llmflow.yaml` | `output_file_directory: "output"` |
| `hello.yaml` | `output_file_directory: "output"` |
| `json-response-openai.yaml` | `output_file_directory: "outputs/json-response"` |
| `json-schema-example.yaml` | `output_file_directory: "outputs/json-schema-example"` |
| `storyflow-test.yaml` | skip — function-only, no saveas |

### demo — `pipelines/`

| File | Declaration(s) to add |
|------|----------------------|
| `hello-llmflow.yaml` | `output_file_directory: "output"` |

### hebrew-poetry-features — `pipelines/`

| File | Declaration(s) to add |
|------|----------------------|
| `psalm-analysis.yaml` | `output_file_directory: "output"` |
| `hebrew-poetry-features.yaml` | `output_file_directory: "output"` |
| `hello-llmflow.yaml` | `output_file_directory: "output"` |

### image-scene-descriptions — `pipelines/`

| File | Declaration(s) to add |
|------|----------------------|
| `visual-commentary.yaml` | `output_file_directory: "output"` |
| `hello-llmflow.yaml` | `output_file_directory: "output"` |

### macula-lxx-greek — `pipelines/`

| File | Declaration(s) to add |
|------|----------------------|
| `annotate-lemmas.yaml` | `output_file_directory: "output"` |
| `hello-llmflow.yaml` | `output_file_directory: "output"` |
| `hello.yaml` | `output_file_directory: "output"` |

### paratext-pipelines — `pipelines/`

| File | Declaration(s) to add |
|------|----------------------|
| `backtranslation.yaml` | `output_file_directory: "output"` |
| `list-projects.yaml` | `output_file_directory: "output"` |
| `multi-project-comparison.yaml` | `output_file_directory: "output"` |
| `test-builtin.yaml` | `output_file_directory: "output"` |
| `hello-llmflow.yaml` | `output_file_directory: "output"` |
| `hello.yaml` | `output_file_directory: "output"` |

### sdbh-helpers — `pipelines/`

| File | Declaration(s) to add |
|------|----------------------|
| `verb-subject-report.yaml` | `output_file_directory: "output"` |

### semdom-greek-lexicon (project repo) — `pipelines/`

| File | Declaration(s) to add |
|------|----------------------|
| `semlex-singlepass.yaml` | `intermediate_file_directory: "obsidian/grc/intermediate"`, `output_file_directory: "obsidian/grc/markdown"` |

---

## Section 2: YAML Changes + Data Moves

### catenae-dev

Pipeline `annotate-book.yaml` already uses `intermediate_dir: "output/intermediate"` and
`final_dir: "output/final"`. Existing data is at `output/Jas/` and `output/Matt/` (older run
with different naming). Standardize on `output/`.

**Data moves:**
- `output/Jas/` → `output/final/Jas/`
- `output/Matt/` → `output/final/Matt/`
- `outputs/debug/` is empty → remove

**YAML declarations to add:**

| File | Declaration(s) to add |
|------|----------------------|
| `annotate-book.yaml` | `intermediate_file_directory: "output/intermediate"`, `output_file_directory: "output/final"` |
| `hello-llmflow.yaml` | `output_file_directory: "output"` |
| `hello.yaml` | `output_file_directory: "output"` |

### hebrew-phrasing

`output/` has real data. `outputs/debug/` is empty. Standardize on `output/`.

**Data moves:**
- `outputs/debug/` is empty → remove

**YAML declarations to add:**

| File | Declaration(s) to add |
|------|----------------------|
| `macula-hebrew.yaml` | `intermediate_file_directory: "output/debug"`, `output_file_directory: "output"` |
| `macula-format.yaml` | `output_file_directory: "output"` |
| `macula-prepare.yaml` | `output_file_directory: "output"` |
| `hello-llmflow.yaml` | `output_file_directory: "output"` |

### internalization-questions

`output/` has real data (debug parse files + final question files). `outputs/debug/` has old LLM
request/response dumps — these should move to `output/debug/`.

**Data moves:**
- `outputs/debug/*.txt` → `output/debug/`
- `outputs/debug/` → remove (now empty)
- `outputs/` → remove (now empty)

**YAML declarations to add:**

| File | Declaration(s) to add |
|------|----------------------|
| `internalization-questions.yaml` | `intermediate_file_directory: "output/debug"`, `output_file_directory: "output/internalization-questions"` |
| `hello-llmflow.yaml` | `output_file_directory: "output"` |

---

## Section 3: Data Moves Only (YAML already done)

### discourse-flow

**Inverted 2026-08-17.** This section previously said to move `outputs/intermediate/*` into
`output/intermediate/` so the data matched the declaration. Under the corrected rule the
declaration is what is wrong.

**YAML change:**
- `intermediate_file_directory: "output/intermediate"` → `"outputs/intermediate"`

**Data moves:** none — the data is already in `outputs/intermediate/`, which is now the correct
location. Any files that a previous partial migration moved into `output/intermediate/` move back.

**Leave untouched:**
- `outputs/book-discourse/` — declared `output_file_directory`, correct location
- `outputs/reader/` — final output, correct location

**Whose change:** discourse-flow has its own AI working in it (Captain's instruction, 2026-08-16).
This is a note of what needs doing there, not a licence to do it from here.

### discourse-flow-hebrew

Pipeline already done. `outputs/debug/` is empty.

**Data moves:** none

**Cleanup:**
- `outputs/debug/` → remove (empty)
- `outputs/` → remove if now empty

---

## Execution Order

1. Section 1 YAML-only (fastest, lowest risk — no data touched)
2. Section 2 data moves, then YAML
3. Section 3 data moves (discourse-flow)

---

## Done Criteria

- [ ] Every pipeline listed above has the correct declarations
- [ ] All `outputs/` directories are gone or intentional (discourse-flow)
- [ ] No data deleted — only moved or left in place
- [ ] `sp lint` passes on all updated pipelines

---

## Survey and execution — 2026-08-17

Read-only survey of every pipeline in every sibling repo, then the migration. 44 pipelines
across 14 repos; 26 were declaring the singular directory.

### Executed

Twenty pipelines in eight repos now declare `outputs`, and their data moved with them.
`output/` no longer exists in any of them.

| Repo | Pipelines fixed | Files moved `output/` → `outputs/` |
|---|---|---|
| `hebrew-phrasing` | 4 | 339 |
| `internalization-questions` | 2 | 25 |
| `image-scene-descriptions` | 2 | 18 |
| `storytelling-dictionary` | 1 | 13 |
| `sdbh-helpers` | 1 | 6 |
| `macula-lxx-greek` | 3 | 3 |
| `demo` | 1 | 1 |
| `paratext-pipelines` | 6 | 0 (directory was empty) |

Each move was a rename into a destination that did not exist, so nothing was merged or
overwritten.

Two `.gitignore` files needed the same correction — `internalization-questions` and
`paratext-pipelines` both ignored `output/`, so renaming the directory briefly exposed 25
generated files to git. Both now ignore `outputs/`.

`hebrew-poetry-features` held a stale `output/analysis/19023001-19023006/` — 22 files, a
complete seven-stage analysis of Psalm 23:1-6, never committed and not duplicated in
`outputs/`. Moved to `outputs/analysis/`, the path the pipeline itself declares, rather than
deleted: it is the only sample output of that pipeline, and the repo is being handed to a new
user who needs a reference.

Nothing was committed in any consumer repo — those repos' own AIs commit their own work.

### Deliberately not touched

| Repo | Why |
|---|---|
| `discourse-flow`, `discourse-flow-hebrew` | Their own AI is working in them (Captain, 2026-08-16). Both still declare `intermediate_file_directory: "output/intermediate"` **and** a variable named `output_dir` — singular in both places. A note for that AI, not work to be done from here. |
| `semdom-greek-lexicon` | Captain's instruction, 2026-08-17: leave as is. Declares `obsidian/grc/...` — a real Obsidian vault, 448 files, with its own `.obsidian/` config. The vault root is the deliverable; it is not a directory named `output`. |
| `llmflow-historical-pipelines` | Archive extracted in `8caf8be`. Its eight pipelines declare no directories at all. They exist to be read, not run. |

### Findings worth acting on separately

- `prepare-book-data.yaml` (both discourse-flow repos) declares
  `intermediate_file_directory: "input/annotations"` — an *input* path as the intermediate
  directory. Looks like a mistake, unrelated to this migration.
- `hebrew-poetry-features/pipelines/hello.yaml` declares no output directory.
- `ears-to-hear` was already correct throughout, as was this repo.
