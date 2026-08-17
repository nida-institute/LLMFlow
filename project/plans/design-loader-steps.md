# Design: Generic Loader Step Types

**Status:** Implemented — historical record. Describes why the code looks as it does; do not rebuild from it. Verify against the code before relying on any detail.

Shipped as `steps/load.py` (`tests/test_loader_steps.py`).

## Problem

Loading a file into pipeline context currently requires a `type: function` step
with a module path the pipeline author must know and spell correctly:

```yaml
- name: load_book_summary
  type: function
  function: llmflow.utils.data.load_json_file
  inputs:
    file_path: "${intermediate_book_dir}/book-summary.json"
  outputs: book_summary
```

This is not discoverable. There is no `sp functions` command, no tab completion,
and no way to find `llmflow.utils.data.load_json_file` without reading the docs
or asking an AI assistant. Pipeline authors who are not developers cannot be
expected to know or remember these paths.

A second problem: the same loading functions are currently being called from
inside plugin functions (F8–F13 in the build-book audit), violating the
"no file I/O in pipeline step functions" rule. Having first-class loader step
types makes the correct pattern obvious and easy.

---

## Proposed Step Types

First-class step types for loading files into context:

```yaml
- name: load_book_summary
  type: load_json
  path: "${intermediate_book_dir}/book-summary.json"
  outputs: book_summary
```

Full set:

| Step type        | Returns | Notes |
|------------------|---------|-------|
| `load_json`      | `dict` or `list` | Parses JSON; raises on missing file |
| `load_yaml`      | `dict` or `list` | Parses YAML |
| `load_xml`       | `lxml.etree._Element` | Full lxml tree; supports XPath/XSLT |
| `load_csv`       | `list[dict]` | CSV with optional `delimiter` (default `,`) |
| `load_tsv`       | `list[dict]` | Shorthand for `load_csv` with `delimiter: "\t"` |
| `load_text`      | `str` | Plain text, Markdown, USFM — full file contents |
| `load_directory` | `list` | All files matching `pattern` in `path`; each parsed per `format` |

### Common schema

```yaml
- name: <step_name>
  type: load_json        # or load_yaml, load_xml, load_csv, load_tsv, load_text
  path: "${some_path}"   # supports ${var} substitution
  output: <var_name>     # or outputs: — pipeline author's choice; runner handles both
```

`load_csv` and `load_tsv` support an optional `delimiter` key.

### Directory loader schema

```yaml
- name: load_acai
  type: load_directory
  path: "${acai_dir}/${book_ref.book_number}/"
  pattern: "*.json"      # glob pattern; required
  format: json           # how to parse each file: json, yaml, xml, text
  output: acai_files     # always a list — one parsed item per matched file
```

`format` accepts the same values as the single-file step type names. Files are
loaded in sorted order for reproducibility.

---

## Discoverability

Step types appear in `sp lint` error messages, the language reference, and
tab completion (future). A pipeline author who knows `type: llm` and
`type: function` will guess `type: load_json` without consulting documentation.
The function path `llmflow.utils.data.load_json_file` is not guessable.

---

## Relation to Existing Functions

The loader steps are thin wrappers over functions that already exist in
`llmflow.utils.data`:

| Step type   | Underlying function |
|-------------|---------------------|
| `load_json` | `llmflow.utils.data.load_json_file` |
| `load_yaml` | `llmflow.utils.data.load_yaml` |
| `load_xml`  | `llmflow.utils.data.load_xml_file` |
| `load_csv`  | `llmflow.utils.data.load_csv_file` |
| `load_tsv`  | `llmflow.utils.data.load_csv_file` with `delimiter="\t"` |
| `load_text` | `llmflow.utils.data.load_text_file` |

No new loading logic needed — just a new dispatch path in `runner.py`.

---

## Relation to the Build-Book Audit (F8–F13)

The audit identified plugin functions that open files directly instead of
receiving loaded data as inputs. First-class loader steps are the clean fix
for all Group X findings (F8, F9, F11) and for the Group Y findings where
a single load primitive fits (F10 TSV, F13 ACAI directory):

| Finding | Violation | Fix |
|---------|-----------|-----|
| F8 | `passage_enriched.py` reads annotated book JSON | `type: load_json` upstream step |
| F9 | `book_scene_text.py` reads Macula JSON | `type: load_json` upstream step |
| F11 | `leaders_guide_markdown.py` reads two JSON files | Two `type: load_json` steps |
| F10 | `book_scene_text.py` reads verse-words TSV | `type: load_tsv` upstream step |
| F13 | `book_acai_lookup.py` globs ACAI directory | `type: load_directory` with `format: json` |
| F12 | `check_prompt_compliance.py` inspects files | Allowlist — file inspection is its job |

---

## Linter Validation

`sp lint` validates loader steps as follows:

- **Required keys:** `path` and (`output` or `outputs`) must be present.
- **`load_directory`:** `pattern` and `format` must also be present; `format`
  must be one of `json`, `yaml`, `xml`, `csv`, `tsv`, `text`.
- **Path existence:** if `path` contains no unresolved `${...}` references
  after substituting pipeline-level variables, `sp lint` checks that the file
  (or directory) exists on disk and reports an error if not. Paths that depend
  on step outputs (e.g. `${book_ref.book_code}`) cannot be checked at lint time
  and are skipped.

---

## Implementation

1. Add `run_load_step(step, context)` to `runner.py` — dispatches on step type,
   calls the appropriate `llmflow.utils.data` function, stores result in context
   under `output`/`outputs` (handle both).
2. Register `load_json`, `load_yaml`, `load_xml`, `load_csv`, `load_tsv`,
   `load_text`, `load_directory` in the step dispatch block.
3. Update `sp lint` to recognize and validate the new step types per the rules
   above.
4. TDD: write failing tests first, then implement.
