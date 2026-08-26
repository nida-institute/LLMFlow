# Design: `sp clean` Command and Pipeline Directory Declaration

**Status:** Implemented — historical record. Describes why the code looks as it does; do not rebuild from it. Verify against the code before relying on any detail.

Shipped as `sp clean` (`cli.py`, `tests/test_clean_command.py`), together with the
`intermediate_file_directory` / `output_file_directory` declarations. The previous status,
"Approved, Awaiting Implementation Authorization", was stale and invited a rebuild.

---

## Problem

Pipelines produce two kinds of files:
- **Intermediate / debug files** — working artifacts (extracted XML, partial JSON, LLM request/response dumps) that are regenerated each run and can be safely deleted
- **Output files** — final deliverables that must not be automatically removed

Currently there is no way to declare this distinction in the YAML, and no `sp clean` command. Debug files are written to a hard-coded `outputs/debug/` path and auto-cleared at pipeline start — invisible to the user and not integrated with any clean command.

---

## Design: Two Declared Directories

Declare two root directories at the top of the pipeline YAML:

```yaml
intermediate_file_directory: "./output/work"   # optional — intermediate and debug files
output_file_directory: "./output/final"         # required — protected deliverables

steps:
  - name: extract
    saveas: "${intermediate_file_directory}/extracted.json"   # cleanable

  - name: draft
    saveas: "${intermediate_file_directory}/draft.md"         # cleanable

  - name: finalize
    saveas: "${output_file_directory}/final.md"               # protected
```

**`intermediate_file_directory`** — optional. If declared:
- All intermediate saveas files go here
- Debug files (LLM request/response dumps) are routed here instead of the hard-coded `outputs/debug/`
- Everything inside is deleted by `sp clean`

**`output_file_directory`** — required (pipelines should always declare where their outputs go).
- Protected from `sp clean`
- Linter warns if a saveas path falls outside both declared dirs

---

## `sp clean` Command

```bash
sp clean --pipeline foo.yaml                    # delete all contents of intermediate_file_directory
sp clean --pipeline foo.yaml --debug-only       # delete only debug/ subdirectory (or outputs/debug/ fallback)
sp clean --pipeline foo.yaml --intermediate-only # delete intermediate files, preserve debug/
sp clean --pipeline foo.yaml --dry-run          # show what would be deleted, don't delete
```

**Behavior:**
- If `intermediate_file_directory` is not declared: warn and exit cleanly
- `--debug-only`: deletes `intermediate_file_directory/debug/`; falls back to `outputs/debug/` if no `intermediate_file_directory` declared
- `--intermediate-only`: deletes everything in `intermediate_file_directory` except `debug/`
- No flag: deletes everything inside `intermediate_file_directory`
- Resolves `${variable}` references in `intermediate_file_directory`
- Deletes everything **inside** the target, leaving the directory itself intact
- Prints each deleted path (or would-delete path with `--dry-run`)
- Does NOT touch `output_file_directory` or any path outside `intermediate_file_directory`

---

## Debug File Routing

When `linter_config.log_level: debug` and `intermediate_file_directory` is declared,
route LLM request/response dump files to `${intermediate_file_directory}/debug/` instead
of the current hard-coded `outputs/debug/`.

If `intermediate_file_directory` is not declared, fall back to the existing `outputs/debug/` behavior.

This resolves the existing problems with debug file handling:
- No longer invisible (user declared `intermediate_file_directory`, so they know it's cleanable)
- Integrated with `sp clean`
- Path is no longer hard-coded

---

## Linter Warning

Warn when a `saveas` path falls outside both declared directories:

```
WARNING: step "extract" saveas path "./output/work/extracted.json"
  is not under declared intermediate_file_directory or output_file_directory.
  All saveas paths should be under intermediate_file_directory (cleanable)
  or output_file_directory (protected).
```

This is a warning, not an error — pipelines without these declarations are still valid.

---

## Implementation Scope

### Files to modify
- `src/llmflow/runner.py` — read `intermediate_file_directory` and `output_file_directory` at pipeline load; route debug files to `${intermediate_file_directory}/debug/` when declared
- `src/llmflow/cli.py` — add `sp clean` subcommand
- `src/llmflow/utils/linter.py` — add saveas-path-outside-declared-dirs warning

### Files to add
- `tests/test_clean_command.py` — unit tests for clean behavior

### Schema / docs
- Update pipeline YAML schema (if one exists)
- Update `docs/llmflow-language.md` with `intermediate_file_directory` / `output_file_directory` documentation

---

## Decisions Made

| # | Decision |
|---|---|
| 1 | Two fixed dirs: `intermediate_file_directory` (cleanable) and `output_file_directory` (protected) |
| 2 | `intermediate_file_directory` is optional; `output_file_directory` is required |
| 3 | `sp clean` deletes contents of `intermediate_file_directory`, leaves the directory itself |
| 4 | Debug files routed to `${intermediate_file_directory}/debug/` when declared |
| 5 | Linter warns when a saveas path falls outside both declared dirs |
| 6 | `sp clean --dry-run` shows what would be deleted without deleting |
