# 📘 Scripture Pipelines Language Specification

An **Scripture Pipelines** is a YAML file that describes a pipeline of steps to be executed using LLM prompts, variable substitution, iteration, and file output.

## 🧩 Structure

```yaml
name: your_pipeline_name

variables:
  key1: value1
  key2: value2

llm_config:
  model: gpt-4o
  max_tokens: 4096
  temperature: 0.4
  timeout_seconds: 60

linter_config:
  enabled: true
  treat_warnings_as_errors: true
  log_level: debug

steps:
  - name: step_name
    type: llm | function | for-each | save
    ...
```

## 🔧 Root-Level Configuration

### `variables:`
Defines pipeline-level variables that can be referenced in steps.

### `llm_config:` (optional)
Global LLM settings applied to all LLM steps:
- `model`: Model identifier (e.g., `gpt-4o`, `claude-3-opus-20240229`)
- `max_tokens`: Maximum tokens in response
- `temperature`: Randomness (0.0 - 1.0)
- `timeout_seconds`: Timeout for LLM API calls

### `linter_config:` (optional)
Controls pipeline validation:
- `enabled`: Enable/disable linting
- `treat_warnings_as_errors`: Fail on warnings
- `log_level`: Logging verbosity (`debug`, `info`, `warning`, `error`)

---

## 🔧 Types of Steps

### Common Step Options

All step types accept an optional `retry` block to re-run the step when a condition stays true or the step raises:

```yaml
retry:
  max_attempts: 3          # default 3
  delay_seconds: 2         # wait between attempts
  condition: "${len(payload or '') < 2000}"
```

- Retries trigger on any exception raised by the step or when `condition` evaluates truthy.
- Context/output changes are rolled back between attempts, so only the final successful run (or failure) mutates state.
- During retries, the current attempt number is available as `${_retry_attempt}`.

#### Retry best practices

- Keep the `condition` expression side-effect free; it runs with the current context after a successful attempt. Use helpers like `len(...)`, `any(...)`, or custom functions already on the context.
- Use `${_retry_attempt}` to tailor prompts (`"attempt ${_retry_attempt}"`, adjusting instructions, etc.) or to gate additional tooling on later attempts.
- Assume every attempt starts from a clean slate: `append_to` lists, derived variables, and function outputs are restored to their pre-step values unless the attempt ultimately succeeds.
- Log *why* a retry is configured (missing verse, short summary, etc.) so future maintainers know the guardrail’s intent.
#### Step-level `condition:` (skip guard)

Any step (any type) accepts an optional `condition:` field. When present, the expression is evaluated before the step runs; if it evaluates to false the step is silently skipped.

```yaml
- name: enrich_if_needed
  type: llm
  condition: "${needs_enrichment}"
  prompt:
    file: enrich.gpt
    inputs:
      data: "${raw_data}"
  outputs: enriched_data
```

The expression is resolved through the normal `resolve()` / `_evaluate_condition_expression()` pipeline:
- A bare variable reference: `"${my_flag}"` — truthy/falsy of its value
- A Python eval expression: `"${len(results) < 3}"` — evaluated in the current context
- A boolean literal `true` / `false`

**Note:** This is a *skip* guard. The step is either fully executed or fully skipped — no partial execution. For a conditional *block* of multiple steps, use `type: if` (see below).
### type: `llm`

Runs a prompt through an LLM API using the [`llm` package](https://llm.datasette.io/).

```yaml
  type: llm
  prompt:
    file: leadersguide-intro.gpt
    inputs:
      passage: "${passage}"
      exegetical_culture: "${exegetical_culture}"
  outputs: intro_response
  log: debug
```

**Required Fields:**
- `outputs`: Variable name (string) or list of names to store result(s)

**Optional Fields:**
- `model`: Override the pipeline-level model for this specific step.
- `max_tokens`, `temperature`, `timeout_seconds`: Per-step LLM overrides when a step has different needs than the global defaults.
- `output_type: json` - Parse LLM response as JSON
- `response_format`: **Structured output specification (GPT-4 family only)** — guarantees valid JSON conforming to a schema. See "Structured JSON Output" section below.
- `log`: Log level for this step (`debug`, `info`, `warning`, `error`)
- `saveas`: File path to save the output
- `append_to`: List variable name to append result to (used in `for-each`)
- `retry` (see above) to re-run when a response is too short/long, missing data, etc.

```yaml
- name: generate_scene_list
  type: llm
  prompt:
    file: leadersguide-scenes.gpt
    inputs:
      passage: "${passage}"
      source: "${source}"
  outputs: scene_list
  log: debug
```

#### Structured JSON Output (Recommended for Production)

**CRITICAL:** For pipelines that produce JSON, use `response_format` with a JSON schema to guarantee valid output. This eliminates 40-60% failure rates caused by LLM-generated malformed JSON (missing commas, unescaped quotes, trailing commas).

**LLMFlow automatically uses OpenAI's client directly when `response_format` is present**, ensuring 100% compatibility with structured outputs.

**OpenAI GPT-4 family** (gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini) supports structured outputs via `response_format`:

**Inline schema** (schema defined in pipeline YAML):

```yaml
- name: analyze_discourse
  type: llm
  model: gpt-4o-2024-08-06  # Requires 2024-08-06 or later
  output_type: json
  response_format:
    type: json_schema
    json_schema:
      name: discourse_analysis
      strict: true
      schema:
        type: object
        properties:
          book:
            type: string
            description: "Book name (e.g., 'Mark')"
          pericopes:
            type: array
            items:
              type: object
              properties:
                title:
                  type: string
                passage:
                  type: string
                theme:
                  type: string
              required: ["title", "passage", "theme"]
              additionalProperties: false
        required: ["book", "pericopes"]
        additionalProperties: false
  prompt:
    file: analyze.gpt
    inputs:
      book_text: "${text}"
  outputs: analysis
```

**File-based schema** (recommended for reusability):

```yaml
- name: analyze_discourse
  type: llm
  model: gpt-4o-2024-08-06
  output_type: json
  response_format:
    type: json_schema
    json_schema:
      name: discourse_analysis
      strict: true
      schema_file: schemas/discourse_analysis.json  # Path relative to current directory
  prompt:
    file: analyze.gpt
    inputs:
      book_text: "${text}"
  outputs: analysis
```

Using `schema_file` keeps pipelines clean and allows schema reuse across multiple pipelines. The schema file should contain a standard JSON Schema object:

```json
{
  "type": "object",
  "properties": {
    "book": {
      "type": "string",
      "description": "Book name"
    },
    "pericopes": {
      "type": "array",
      "items": { ... }
    }
  },
  "required": ["book", "pericopes"],
  "additionalProperties": false
}
```

**Why this matters:**

| Without `response_format` | With `json_schema` |
|---|---|
| ❌ 40-60% failure rate (intermittent) | ✅ 100% valid JSON |
| ❌ Wasted retries (3 attempts × cost) | ✅ No retries needed |
| ❌ Unpredictable errors at different positions | ✅ Guaranteed schema compliance |
| ❌ Manual JSON formatting rules in prompts | ✅ Schema enforced by API |

**Key requirements:**
- **Model:** Must use `gpt-4o-2024-08-06` or later (not `gpt-4.1` — uses different API)
- **`strict: true`** (recommended): Enables strict schema adherence
- **`additionalProperties: false`**: Prevents LLM from adding unexpected fields
- **All required fields documented**: Use `description` fields to guide LLM

**Basic JSON mode (less reliable):**

For simple cases where you don't need schema validation:

```yaml
response_format:
  type: json_object  # Forces JSON output, but no schema enforcement
```

**When to use which:**
- ✅ **Use `json_schema`**: Production pipelines, complex nested structures, critical data extraction
- ⚠️ **Use `json_object`**: Quick prototypes, simple flat objects, non-critical output
- ❌ **Use neither**: Text/markdown output only, human-readable responses

**Alternative: Gemini models**

Gemini 1.5+ uses different parameters for structured output:

```yaml
model: gemini-2.0-flash
response_mime_type: "application/json"
response_schema:
  type: object
  properties:
    # ... schema definition
```

See `pipelines/json-response-openai.yaml` for working examples.

---

### type: `function`

Calls a Python function from the Scripture Pipelines library or custom code.

```yaml
- name: parse_passage_reference
  type: function
  function: llmflow.utils.data.parse_bible_reference
  inputs:
    passage: "${passage}"
  outputs: passage_info
```

**Required Fields:**
- `function`: Fully qualified Python function name (e.g., `module.submodule.function_name`)
- `inputs`: Arguments passed as keyword arguments
- `outputs`: Variable name(s) to store the return value
  - If function returns a dict, keys become the output variable
  - If function returns a single value, it's stored under the output name

**Optional Fields:**
- `saveas`: File path to save the output
- `append_to`: List variable name to append result to (used in `for-each`)
- `log`: Log level for this step

**Common functions:**
- `llmflow.utils.data.load_json_file(file_path)` — load and parse a JSON file from disk; raises `FileNotFoundError` if missing
- `llmflow.utils.data.load_json(file_path)` — alias for `load_json_file` in the data module
- `llmflow.utils.io.load_json(file_path)` — load JSON; same behaviour, different module (prefer `data.load_json_file` for new pipelines)
- `llmflow.utils.data.load_yaml(file_path)` — load and parse a YAML file from disk; safe to use in pipelines
- `llmflow.utils.data.load_text_file(file_path)` — read a plain-text or Markdown file; returns the full contents as a `str`. Useful for injecting static context into prompts.
- `llmflow.utils.data.load_csv_file(file_path, delimiter=",")` — read a CSV or TSV (`delimiter="\t"`) file; returns a `list[dict]` compatible with `for-each`
- `llmflow.utils.data.load_xml_file(file_path)` — parse an XML/USX/TEI file via **lxml**; returns the root `lxml.etree._Element`. Supports XPath/XSLT and full tree traversal. Raises `lxml.etree.XMLSyntaxError` on malformed input.
- `llmflow.utils.data.list_usfm_books(base_dir, project_name)` — list book codes in a Paratext project directory, in canonical USFM order (GEN → REV). Returns `list[str]`.
- `llmflow.utils.data.load_usfm_book(base_dir, project_name, book, format)` — load a single book from a Paratext project. `format="usx"` returns `lxml.etree._Element`; `format="usj"` returns `dict`. Reads USFM (`.sfm`/`.usfm`) files via `usfmtc`; always writes USX/USJ 3.1.
- `llmflow.utils.data.load_usfm_passage(base_dir, project_name, passage, format)` — load a passage by reference string: `"LUK"` (whole book) or `"LUK 1"` (chapter). Verse ranges (`"LUK 1:1-10"`) raise `NotImplementedError` (Phase 2). Same format options as `load_usfm_book`.
- `llmflow.utils.data.export_usx(base_dir, project_name, output_dir)` — convert all books in a Paratext project to USX 3.1 files in `output_dir`, preserving project numeric filename prefixes. Returns `output_dir` string.
- `llmflow.utils.data.load_project_file(base_dir, project_name, file)` — load Paratext project metadata files. Auto-detects format: `.json` returns `dict` (Scripture Burrito), `.xml` returns `lxml.etree._Element` (Paratext XML). Supports `metadata.json`, `Settings.xml`, `BiblicalTerms.xml`, etc.
- `llmflow.utils.data.xpath_text(element, path)` — extract text from XML element using XPath query. Returns first match or `None` if not found.
- `llmflow.utils.data.parse_bible_reference` — parse Bible references
- `llmflow.utils.io.render_markdown_template` — render markdown templates
- `llmflow.utils.io.save_json` — save JSON to file
- `llmflow.utils.data.flatten_json_to_markdown` — convert JSON to markdown
- `llmflow.utils.data.identity` — pass through data unchanged

> ⚠️ The module prefix is always `llmflow.utils.*` — never `sp.utils.*`

> ℹ️ All built-in loaders use **lxml** for XML/USX parsing. There is no stdlib `xml.etree` use in this engine.

**Example with template rendering:**
```yaml
- name: render_guide
  type: function
  function: llmflow.utils.io.render_markdown_template
  inputs:
    template_path: "templates/leadersguide_template.md"
    variables:
      passage: "${passage}"
      intro: "${intro_response}"
      summary: "${summary_response}"
  outputs: leaders_guide_markdown
  saveas: "outputs/leaders_guide/${passage_info.filename_prefix}_leaders_guide.md"
```

---

### type: `for-each`

Loops over a list and executes substeps for each item.

```yaml
- name: process_each_scene
  type: for-each
  input: "${scene_list}"
  item_var: scene
  steps:
    - name: bodies
      type: llm
      prompt:
        file: leadersguide-bodies.gpt
        inputs:
          scene: "${scene.WLC}"
          citation: "${scene.Citation}"
      outputs: bodies_content
      append_to: bodies_list
```

**Required Fields:**
- `input`: Variable name containing the list to iterate over
- `item_var`: Variable name to bind each list item to
- `steps`: Nested steps to execute for each item

**Using `append_to` in substeps:**
Within `for-each` loops, use `append_to` to accumulate results across iterations:

```yaml
- name: process_each_scene
  type: for-each
  input: "${scene_list}"
  item_var: scene
  steps:
    - name: analyze_scene
      type: llm
      prompt:
        file: analyze.gpt
        inputs:
          scene: "${scene}"
      outputs: analysis
      append_to: all_analyses  # Creates list: [analysis1, analysis2, ...]
```

**Important notes:**
- Each iteration has its own isolated context
- Variables from outer scope are accessible via `${var}`
- Use `append_to` to collect results into a list variable
- Nested `for-each` loops are supported

---

### type: `if`

Evaluates a `condition:` and, when true, executes a nested `steps:` block. When false the entire block is skipped.

```yaml
- name: add_cultural_notes
  type: if
  condition: "${include_culture}"
  steps:
    - name: generate_culture
      type: llm
      prompt:
        file: culture.gpt
        inputs:
          passage: "${passage}"
      outputs: cultural_notes

    - name: save_culture
      type: save
      content: "${cultural_notes}"
      saveas: "outputs/${passage_info.filename_prefix}_culture.md"
```

**Required Fields:**
- `condition`: Expression evaluated before any nested step runs (same syntax as the step-level skip guard above)
- `steps`: List of steps to execute when the condition is true

**How it works (implementation detail):**
The `condition:` is evaluated in the shared `run_step()` dispatcher. If false the `type: if` step returns immediately. If true, `run_if_step()` iterates over the nested `steps:` list, propagating any `after:` directives (`exit`, `continue`) upward.

**Difference from step-level `condition:`:**
| | `condition:` on any step | `type: if` |
|---|---|---|
| Skips what | That single step | The entire nested block |
| Has `steps:` sub-list | No | Yes (required) |
| Can produce outputs | Via normal `outputs:` | Via nested steps' `outputs:` |

---

### type: `save`

Writes content directly to a file. No LLM call, no Python function — just a write.

```yaml
- name: write-result
  type: save
  content: "${my_variable}"        # required — supports ${var} resolution
  path: "outputs/result.md"       # required — supports ${var} substitution
```

**Required Fields:**
- `content`: The value to write. Supports `${variable}` references. If omitted, falls back to `context["content"]`.
- `path`: Output file path. Parent directories are created automatically.

**Format auto-detection:**
- `.json` paths: Python dicts/lists are serialized with 2-space indentation; JSON strings are re-serialized for consistent formatting.
- `.md` paths: `clean_markdown()` normalization is applied and a trailing newline is added.
- All other extensions: written as-is.

---

### type: `basex`

Runs an XQuery against a local BaseX database via the `basex` CLI.

```yaml
- name: query-verses
  type: basex
  query_file: queries/get-passage.xq  # path to .xq file
  # query: "for $v in //verse return $v"  # alternative: inline XQuery
  params:                               # optional — resolved and substituted into query
    passage: "${passage}"
    source: "${source}"
  timeout: 120                          # optional, seconds (default: 120)
  outputs: query_result
  saveas: "outputs/passages/${passage}.json"
```

**Required Fields:**
- `query_file` **or** `query` (exactly one)
- `outputs`: Variable name to store the result

**Optional Fields:**
- `params`: Key-value pairs resolved from pipeline context, then substituted into the query via Python `str.format_map`.
- `timeout`: Seconds before the BaseX process is killed (default 120).
- `saveas`: File path to save the output (supports `${var}` substitution).

**Prerequisites:** The `basex` executable must be on `PATH` with a running BaseX instance.

---

### type: `plugin` (registered step types)

Built-in plugins are invoked by using their registration name as the step `type`. The step type itself _is_ the plugin name.

**Built-in plugins:**

| Step type | Purpose |
|---|---|
| `xpath` | Extract elements/text/attributes from XML files using XPath expressions |
| `tsv` | Read TSV or CSV files row by row into the pipeline context |
| `xslt` | Apply an XSLT stylesheet to an XML file |

**`xpath` example:**
```yaml
- name: extract-verses
  type: xpath
  inputs:
    path: "${xml_file}"
    xpath: "//verse"
    output_format: text        # text | xml_string | attribute
  outputs: verse_list
```

**`tsv` example:**
```yaml
- name: load-terms
  type: tsv
  inputs:
    path: "data/terms.tsv"
    delimiter: "\t"            # optional, default "\t"
    limit: 100                 # optional — stop after N rows
    from: 10                   # optional — start at row N (0-indexed)
  outputs: term_rows
```

**How plugin steps work:**
- All fields on the step are resolved via `${var}` and passed as a flat config dict to the plugin function.
- The return value is handled by the normal `outputs:` / `saveas:` / `append_to:` mechanics.

---

## 🔁 Variables

### Defining Variables

1. **In the pipeline file:**
```yaml
variables:
  passage: "Psalm 23"
  output_dir: outputs
  source: WLC
```

2. **Via command line:**
```bash
sp run --pipeline pipeline.yaml --var passage="Psalm 23"
```

3. **From step outputs:**
```yaml
- name: get_data
  type: function
  function: some.function
  outputs: my_var  # Now available as ${my_var}
```

### Using Variables

**In YAML:**
- Simple: `"${passage}"`
- Nested object: `"${scene.WLC}"` or `"${scene.Citation}"`
- Array indexing: `"${scene_list[0]}"`
- Array mapping: `"${scene_list[*].Title}"` — extracts all `Title` fields as a flat list, one entry per item.

**In prompt / template files (`.gpt`, `.md`):**
- Use `{{var}}` for substitution
- Access nested fields with dot notation: `{{scene.WLC}}`
- Index into lists: `{{items[0]}}`

---

## 💾 Saving Outputs

### `outputs:` — storing results in context

`outputs` controls what variable name(s) the step result is stored under in the pipeline context.

```yaml
outputs: my_var          # string — stores result as context["my_var"]
outputs:                 # list of one — same effect
  - my_var
outputs:                 # list of N — unpacks result tuple/list into N variables
  - first_thing
  - second_thing
```

- A string value is always accessible as `${my_var}` in later steps.
- If a function returns a dict, the whole dict is stored; access fields with `${my_var.key}`.
- `outputs` is required for any step that uses `saveas:` or `append_to:`.

### `saveas:` — writing results to disk

Three forms are supported:

**String (simplest):**
```yaml
saveas: "outputs/${passage}.md"   # path supports ${var} substitution
```

**Dict (with subdirectory grouping):**
```yaml
saveas:
  path: "outputs/verses/${verse_id}.json"
  group_by_prefix: 2              # integer — group files into 2-char prefix subdirectories
  # group_by_prefix:              # or object form:
  #   prefix_length: 3
  #   prefix_delimiter: "-"       # split on delimiter instead of character count
```
`group_by_prefix` is useful when writing thousands of files to avoid filesystem limits — it automatically creates subdirectories like `AB/AB123.json`.

**List (multiple output files from one step):**
```yaml
saveas:
  - path: "outputs/${name}.md"
  - path: "outputs/${name}.json"
    content: "${json_data}"       # optional — override which context var to write
    format: json                  # optional — json | text | auto (default: auto)
```

**Format auto-detection** (all forms):
- `.json` extension → serialize as indented JSON
- `.md` extension → apply `clean_markdown()` normalization + trailing newline
- Anything else → write as-is

Override with `format: json|text|auto` on the step or in a list-form entry.

### `append_to:` — accumulating results across iterations

Used inside `for-each` loops to build up a list across iterations:

```yaml
assemble: the result of each iteration
append_to: all_results   # creates context["all_results"] as a growing list
```

- If the list variable doesn't exist yet, it is created automatically.
- Can be combined with `outputs:` — the named output is appended to the list.
- State is rolled back if a `retry` attempt fails.

---

## 🧪 Complete Example

From the actual `storyflow-psalms.yaml` pipeline:

```yaml
name: storyflow-psalms

variables:
  prompts_dir: prompts/storyflow
  output_dir: outputs/storyflow
  source: WLC
  passage: "${passage}"

llm_config:
  model: gpt-4o
  max_tokens: 4096
  temperature: 0.4
  timeout_seconds: 60

linter_config:
  enabled: true
  treat_warnings_as_errors: true
  log_level: debug

steps:
  # Parse the Bible reference
  - name: parse_passage_reference
    type: function
    function: llmflow.utils.data.parse_bible_reference
    inputs:
      passage: "${passage}"
    outputs: passage_info

  # Generate exegetical background
  - name: generate_exegetical_culture
    type: llm
    prompt:
      file: exegetical-pericope-psalms-e1.gpt
      inputs:
        source: "${source}"
        passage: "${passage}"
    outputs: exegetical_culture
    log: debug

  # Generate scene list (JSON)
  - name: generate_scene_list
    type: llm
    prompt:
      file: leadersguide-scenes.gpt
      inputs:
        passage: "${passage}"
        source: "${source}"
        exegetical_culture: "${exegetical_culture}"
    output_type: json
    outputs: scene_list
    log: debug

  # Process each scene
  - name: process_each_scene
    type: for-each
    input: "${scene_list}"
    item_var: scene
    steps:
      - name: bodies
        type: llm
        prompt:
          file: leadersguide-bodies.gpt
          inputs:
            passage: "${passage}"
            scene: "${scene.WLC}"
            citation: "${scene.Citation}"
        outputs: bodies_content
        append_to: bodies_list

      # Render scene markdown
      - name: assemble_leadersguide_scene_markdown
        type: function
        function: llmflow.utils.io.render_markdown_template
        inputs:
          template_path: "templates/leadersguide_scene_template.md"
          variables:
            scene_title: "${scene.Title}"
            step1: "${bodies_content}"
        outputs: leadersguide_scene_markdown
        append_to: leadersguide_scenes_markdown_list

  # Concatenate all scenes
  - name: concat_leadersguide_scenes_markdown
    type: function
    function: llmflow.utils.data.flatten_json_to_markdown
    inputs:
      data: "${leadersguide_scenes_markdown_list}"
    outputs: leadersguide_scenes_markdown

  # Save final guide
  - name: save_leaders_guide
    type: function
    function: llmflow.utils.io.render_markdown_template
    inputs:
      template_path: "templates/leadersguide_template.md"
      variables:
        passage: "${passage}"
        leadersguide_scenes_markdown: "${leadersguide_scenes_markdown}"
    outputs: leaders_guide_markdown
    saveas: "outputs/leaders_guide/${passage_info.filename_prefix}_leaders_guide.md"
```

---

## 🎯 Command Line Interface

### Run a pipeline
```bash
sp run --pipeline pipelines/storyflow-psalms.yaml --var passage="Psalm 23"
```

### Dry run (preview without execution)
```bash
sp run --pipeline pipelines/storyflow-psalms.yaml --dry-run
```

### Set multiple variables
```bash
sp run --pipeline pipelines/my-pipeline.yaml \
  --var passage="Mark 1:1-8" \
  --var source="WLC"
```

### Skip linting
```bash
sp run --pipeline pipelines/my-pipeline.yaml --skip-lint
```

### Write logs to a specific file

By default logs go to `llmflow.log` in the current directory. Use `--log` to redirect — useful when running multiple pipelines concurrently in separate terminals.

```bash
sp run --pipeline pipelines/rd-ears2hear.yaml \
  --var passage="Psalm 23" \
  --log outputs/debug/psalm23-run.log
```

### Rewind to a step (replay from saved artifacts)

`--rewind-to <step-name>` replays the pipeline from disk instead of calling the LLM again. Every step up to and including the named step is satisfied by reading its previously saved file; every step after it executes normally. This is useful when you want to change a later step without re-running expensive upstream LLM calls.

```bash
# Re-run everything after `generate_discourse_outline`, loading that step and
# all earlier steps from their saved artifacts instead of calling the LLM.
sp run --pipeline pipelines/discourse-flow.yaml \
  --var passage="Mark 11:12-25" \
  --rewind-to generate_discourse_outline
```

**Requirements for a rewindable step:**
- The step must declare `saveas:` pointing to the file that holds its output.
- The step must declare a single `outputs:` variable name.
- The `saveas` path must be fully resolvable (no unresolved `${...}` variables).
- Steps that use `append_to:` are not rewindable.

If the saved file is missing Scripture Pipelines raises a clear error rather than silently re-running.

### Stop after a step

`--stop-after <step-name>` halts the pipeline immediately after the named step completes, without running any subsequent steps. Combine with `--rewind-to` to re-run exactly one step of a long pipeline.

```bash
# Replay up through enrich_passage from disk, re-run generate_discourse_outline,
# then stop — useful to inspect the outline before continuing.
sp run --pipeline pipelines/discourse-flow.yaml \
  --var passage="Mark 11:12-25" \
  --rewind-to enrich_passage \
  --stop-after generate_discourse_outline
```

### Validate a pipeline
```bash
sp lint pipelines/my-pipeline.yaml
```

### Show version
```bash
sp --version
```

---

## 🤖 LLM Configuration

Scripture Pipelines uses the [`llm` package](https://llm.datasette.io/) by Simon Willison, which supports multiple LLM providers through plugins.

### Install LLM Package and Providers

```bash
# Install the llm package
pip install llm

# Install provider plugins as needed
llm install llm-claude-3      # For Anthropic Claude
llm install llm-gemini        # For Google Gemini
llm install llm-gpt4all       # For local models

# Configure API keys
llm keys set openai
llm keys set anthropic
```

### Supported Providers

Through the `llm` package and its plugins:
- **OpenAI**: gpt-4, gpt-4o, gpt-3.5-turbo
- **Anthropic**: claude-3-opus, claude-3-sonnet, claude-3-haiku
- **Google**: gemini-pro
- **Local models**: via llm-mlc, llm-gpt4all
- **Many others**: See [llm plugins directory](https://llm.datasette.io/en/stable/plugins/directory.html)

### Configure Default Model

In your pipeline:

```yaml
llm_config:
  model: gpt-4o                    # Any model from llm package
  max_tokens: 4096
  temperature: 0.4
  timeout_seconds: 60
```

---

## 🔍 Validation & Linting

The `lint` command validates:
- Pipeline structure and syntax
- Step contracts (inputs/outputs)
- Template file existence
- Prompt file existence
- Variable references

```bash
sp lint pipelines/my-pipeline.yaml
```

Configure linting behavior in your pipeline:

```yaml
linter_config:
  enabled: true
  treat_warnings_as_errors: true
  log_level: debug
```

---

## 💡 Implementation Notes

### Prompt File Format

Prompt files (`.gpt` extension) use **double curly brace syntax** with
`{{variable_name}}` placeholders:

```
<!--
prompt:
  requires:
    - passage
    - scene
    - citation
  optional: []
  format: Markdown
  description: Description of what this prompt does
-->

# Your Prompt Title

Your prompt instructions here. Reference variables using
`{{variable_name}}`.

Supports:
- Simple variables: `{{passage}}`
- Dot notation: `{{scene.WLC}}`
- Array access: `{{items[0]}}`
```

**Key features:**
- **Contract in HTML comments**: YAML frontmatter defines `requires:`, `optional:`, `format:`, `description:`
- **Variable syntax**: `{{variable_name}}` for substitution
- **Validation**: Linter checks that all `requires:` inputs are provided

### Template File Format

Template files (`.md` extension) use the same **double curly brace
syntax** with `{{variable_name}}` placeholders:

```markdown
# {{passage}} Leader's Guide

## Scene 1: {{scene_title}}

{{step1}}

---

{{step2}}
```

**Variable substitution**: `{{variable_name}}`. `${variable}` is used
inside pipeline YAML, not inside `.md` or `.gpt` files.

### Pipeline Variable Reference Syntax

In pipeline YAML files:

- **Simple reference**: `"${variable}"`
- **Nested object**: `"${scene.WLC}"`, `"${scene.Citation}"`
- **Array access**: `"${scene_list[0]}"`
- **Array mapping**: `"${scene_list[*].Title}"` — extracts all `Title` fields as a flat list

### Template Engine Implementation

Scripture Pipelines uses a **custom template engine** with regex-based substitution:
- In prompt and template files, `{{variable}}` placeholders are
  replaced using values from the current context.
- In pipeline YAML, `${variable}` expressions are resolved when
  constructing step inputs and file paths.
- Dot notation (`scene.WLC`) and simple indexing (`items[0]`) are
  supported in both forms.

**Summary of syntax by context:**
- **Pipeline YAML**: `${var}` with dollar sign.
- **Prompt / template files**: `{{var}}` double curly braces.
