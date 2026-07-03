# LLMFlow Language Quick Reference

This file is a compact, self-contained reference to the LLMFlow
pipeline language for day-to-day work in this repository.

If you have access to the engine repo, the full specification lives
in `docs/llmflow-language.md` there, but this quickref is designed to
be enough to author and review pipelines on its own.

## 1. Pipeline structure

```yaml
name: my_pipeline
description: |
  One-line or multi-line description of what this flow does.

variables:
  output_dir: "output"

llm_config:
  model: gpt-4o-mini
  max_tokens: 1024
  temperature: 0.2

linter_config:
  enabled: true
  treat_warnings_as_errors: true

steps:
  - name: first-step
    type: llm | function | for-each | save | load_json | load_yaml | load_csv | load_tsv | load_text | load_xml | load_directory
    # ...
```

Key sections:

- `name`, `description`: human-readable name and summary for the flow.
- `variables`: global variables available to all steps.
- `llm_config`: default model parameters for `llm` steps.
- `linter_config`: controls validation behavior for this pipeline.
- `steps`: ordered list of operations that make up the flow.

## 2. Referencing variables and templates

In pipeline YAML, use `${var}` syntax to reference variables and
step outputs:

- `${output_dir}` – root-level variable.
- `${greeting}` – value produced by a previous step.
- `${scene.WLC}` – field access on an object.
- `${scene_list[0]}` – first element of a list.
- `${scene_list[-1]}` – last element (negative indexing).
- `${scene_list[-3:]}` – last 3 elements (Python slice syntax).
- `${scene_list[:5]}` – first 5 elements.
- `${scene_list[2:8]}` – elements 2 through 7.
- `${scene_list[::2]}` – every 2nd element.
- `${scene_list[*].Title}` – extract one field from every item; returns a flat list.
- `${pericope_results[-3:][*].analysis}` – slice then extract field from each item.

In prompt and template files (`*.gpt`, `*.md`), use `{{var}}`:

- `{{language_count}}`
- `{{greeting_markdown}}`
- `{{scene.WLC}}`

Prompt files usually include a small contract (often in a comment
block) that documents which inputs they expect ("requires" / "optional").
Make sure every required value is provided by the pipeline step
via `prompt.inputs`.

## 3. Common step types

### type: `llm`

Runs a prompt through an LLM and stores the response.

```yaml
- name: generate_text
  type: llm
  prompt:
    file: "template.gpt"
    inputs:
      topic: "${topic}"
  outputs: draft
  saveas:
    path: "${output_dir}/draft.md"
```

- `prompt.file` points to a prompt in `prompts/`.
- `prompt.inputs` provides values that the prompt template expects.
- `outputs` names the variable that will hold the LLM response.
- `saveas.path` writes that response to disk.

Optional extras you may see:

- `output_type: json` – ask the engine to parse the response as JSON.
- `log: debug` – per-step log level.

### type: `function`

Calls a Python function as part of the flow.

```yaml
- name: parse_data
  type: function
  function: some.module:callable
  inputs:
    raw: "${raw_text}"
  outputs: parsed
  saveas:
    path: "${output_dir}/parsed.json"
```

Use `function` steps for deterministic utilities: parsing, loading
files, rendering templates, reshaping JSON, etc.

### type: `for-each`

Loops over a list variable and runs nested steps for each item.

```yaml
- name: process_each_item
  type: for-each
  input: "${items}"
  item_var: item
  steps:
    - name: handle-item
      type: llm
      prompt:
        file: "item.gpt"
        inputs:
          item_text: "${item}"
      outputs: item_result
      append_to: all_results
```

- `input` points to a list value.
- `item_var` is the name used to refer to each element.
- `${loop.index}`, `${loop.total}`, `${loop.first}`, `${loop.last}` are available inside every iteration.
- Use `append_to` in nested steps to build a list across iterations.

### type: `json`

Constructs a JSON value from variables in context and stores it under a named key.

```yaml
- name: build_scene
  type: json
  output: scene_object
  value:
    scene_id: "${scene.scene_id}"
    characters: "${scene.characters}"
```

Use `json` to assemble a structured value mid-pipeline from step outputs.
For static objects that don't depend on step outputs, use `variables:` instead.

### type: `save`

Writes literal content to disk without calling an LLM.

```yaml
- name: write-confirmation
  type: save
  content: |
    ✅ LLMFlow is installed and running.
    2 + 2 = ${total}
  saveas:
    path: "${output_dir}/hello-llmflow.txt"
```

Use `save` when you just need to materialize a small message or
artifact from existing variables.

### type: `load_json` / `load_yaml` / `load_xml` / `load_csv` / `load_tsv` / `load_text`

Load a file into pipeline context — no Python function required.

```yaml
- name: load_summary
  type: load_json
  path: "${output_dir}/summary.json"
  output: summary
```

- `path` supports `${var}` substitution; static paths are checked at lint time.
- `load_csv` accepts an optional `delimiter:` key (default `,`); `load_tsv` uses `\t`.
- `load_xml` returns an `lxml.etree._Element` (or a list if `xpath:` is used).

`load_json` and `load_yaml` accept a `key:` dot-path to extract a nested value:

```yaml
- name: load_pericopes
  type: load_json
  path: "${book_summary}"
  key: pericopes          # or "book.chapters" for nested access
  output: pericopes
```

`load_xml` accepts `xpath:` to filter the tree and return a list of matching nodes:

```yaml
- name: load_verses
  type: load_xml
  path: "${book_xml}"
  xpath: "//verse[@chapter='1']"
  output_format: element   # element (default) | xml-string | text
  namespaces:              # optional, for namespace-aware XPath
    usx: "http://usx.org/"
  output: verses
```

`load_csv` and `load_tsv` support filtering after the file is loaded:

```yaml
- name: load_genesis
  type: load_tsv
  path: "${macula_tsv}"
  output: genesis_rows
  where: "book(ref) == 'GEN' and chapter(ref) == '1'"
  limit: 50
  offset: 0
  columns: [ref, text, lemma]
```

- `where` — filter expression; supports `${var}` substitution. Forms (joined by `and`):
  - `column == 'value'`
  - `column startswith 'prefix'`
  - `book(column) == 'GEN'` / `chapter(column) == '1'` / `verse(column) == '1'` / `word(column) == '1'`
- `limit` — max rows to return (applied after `where`).
- `offset` — rows to skip (applied after `where`).
- `columns` — list of column names to include; omit for all columns.

### type: `load_directory`

Load all files matching a glob from a directory into a list.

```yaml
- name: load_files
  type: load_directory
  path: "${data_dir}"
  pattern: "*.json"
  format: json
  output: items
```

- `pattern`: glob relative to `path` (required)
- `format`: one of `json`, `yaml`, `xml`, `csv`, `tsv`, `text` (required)
- Files are loaded in sorted order.

### type: `if`

Conditionally executes a block of steps.

```yaml
- name: add-detail
  type: if
  condition: "${include_detail}"
  steps:
    - name: generate-detail
      type: llm
      prompt:
        file: "detail.gpt"
        inputs:
          topic: "${topic}"
      outputs: detail_text
```

- `condition` is evaluated first; if falsy the whole block is skipped.
- Any step type is valid in the nested `steps:` list.

### Step-level `condition:` (skip guard)

Any step (any type) can be skipped individually:

```yaml
- name: optional-step
  type: llm
  condition: "${run_optional}"
  prompt:
    file: "optional.gpt"
    inputs:
      data: "${data}"
  outputs: optional_result
```

The expression follows the same rules as `type: if` — variable reference,
Python eval expression, or boolean literal.

## 4. Saving outputs with `saveas`

Any step can write its primary output (or literal content) to a file:

```yaml
- name: save_report
  type: llm
  prompt:
    file: "report.gpt"
    inputs:
      data: "${analysis}"
  outputs: report_md
  saveas:
    path: "${output_dir}/report.md"
```

Notes:

- Parent directories are created automatically.
- You can include `${variables}` and nested fields inside the path.
- If you need multiple files, add more steps, each with its own
  `saveas`.

## 5. Running and linting pipelines

From the project root (where `pipelines/` lives):

```bash
sp run --pipeline pipelines/my-pipeline.yaml
```

To pass variables from the CLI:

```bash
sp run --pipeline pipelines/my-pipeline.yaml   --var passage="Psalm 23"   --var output_dir="output"
```

To validate a pipeline without running it:

```bash
sp lint pipelines/my-pipeline.yaml
```

The `linter_config` block in the pipeline controls how strict
validation should be (for example, whether warnings become errors).

## 6. Prompt file format (`.gpt`)

Every `.gpt` file must begin with a YAML frontmatter block that declares
the variables it expects. The linter enforces this contract.

```
---
requires:
  - language_count
optional: []
format: Markdown
description: Brief description of what this prompt does.
---
system: |
  You are a helpful assistant.
user: |
  Do something with {{language_count}} items.
```

Key rules:

- `requires:` — list of variable names the caller *must* provide via `prompt.inputs`.
- `optional:` — list of variable names the caller *may* provide.
- Variables in the body use `{{double_braces}}`.
- If `requires:` is missing, the linter cannot validate the contract and will
  emit warnings about undeclared inputs.

**Mixins** — include shared text from another file:

```
{{mixin:../mixins/output-language.md}}
```

Paths are relative to the `.gpt` file. The mixin's contents are inlined at render time. Mixin directives are not treated as missing variables by the linter.
