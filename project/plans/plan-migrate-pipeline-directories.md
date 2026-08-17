# Plan: Migrate Registered Pipelines to `sp clean` Directory Scheme

**Status:** ⚠️ **SUPERSEDED — DO NOT EXECUTE.** Its central rule is now inverted.

This plan says: *"Pick `output/` (singular) as the standard for repos that have both."* The
opposite is now true and shipped. The **directory** is plural `outputs/`; only the step **key** is
singular `output`. Commit `9345a00` — "scaffold `outputs/` (plural), remove the `output/` decoy" —
settled it, and every pipeline in this repo declares `output_file_directory: "outputs..."`.

Executing this plan as written would recreate the `output/` decoy that was deliberately removed.

Whether the remaining migration work is still wanted is an open Captain decision. If it is, the
plan needs rewriting around `outputs/` first.

Kept as a record of the directory-declaration rollout, not as instructions.

---

## Background

`design-clean-command.md` introduced `intermediate_file_directory` and `output_file_directory` as
top-level pipeline YAML keys. A previous session updated 9 pipelines in the LLMFlow repo and all
pipelines in discourse-flow and discourse-flow-hebrew before being interrupted.

This plan covers:
1. Adding declarations to all remaining pending pipelines
2. Moving existing data to the right directory in the new scheme
3. Resolving `output/` vs `outputs/` conflicts (standardize on `output/` unless pipeline intentionally uses both)

---

## Rule: `output` vs `outputs`

Pick `output/` (singular) as the standard for repos that have both. Exception: `discourse-flow`
intentionally uses both (`output/intermediate` for intermediate, `outputs/book-discourse` for
final) — leave as-is.

---

## Section 1: YAML-Only Changes (no data moves)

### LLMFlow repo — `pipelines/`

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

Pipeline already declares `intermediate_file_directory: "output/intermediate"`. Old runs wrote
intermediate data to `outputs/intermediate/`. Move old data to match the declared location.

**Data moves:**
- `outputs/intermediate/*` → `output/intermediate/` (merge; do not overwrite newer files already there)

**Leave untouched:**
- `outputs/book-discourse/` — declared `output_file_directory`, correct location
- `outputs/reader/` — final output, correct location

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
