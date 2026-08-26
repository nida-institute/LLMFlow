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

### `description:` (optional)
Human commentary on the pipeline. Use YAML block scalar (`|`) for multi-line content:

```yaml
name: storytelling-dictionary
description: |
  Generates storytelling definitions for biblical concepts.
  Run: sp run --pipeline pipelines/storytelling-dictionary.yaml
```

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

All steps accept an optional `description:` field for human commentary. Use YAML block scalar (`|`) for multi-line content. This field is ignored by the runner and produces no lint warnings:

```yaml
- name: define_term
  description: |
    Generates the full definition. Temperature 0.6 was chosen after testing
    showed lower values produced formulaic output.
  type: llm
  ...
```

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
  output: enriched_data
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
  output: intro_response
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
  output: scene_list
  log: debug
```

#### Structured JSON Output (Recommended for Production)

**CRITICAL:** For pipelines that produce JSON, use `response_format` with a JSON schema to guarantee valid output. This eliminates 40-60% failure rates caused by LLM-generated malformed JSON (missing commas, unescaped quotes, trailing commas).

**Scripture Pipelines automatically uses OpenAI's client directly when `response_format` is present**, ensuring 100% compatibility with structured outputs.

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
  output: analysis
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
  output: analysis
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
- **Model:** `gpt-4o-2024-08-06` or later. OpenAI's guide names the `gpt-4o-mini`,
  `gpt-4o-mini-2024-07-18` and `gpt-4o-2024-08-06` snapshots "and later", and does not
  enumerate later families either way. **`gpt-4.1` works** — four arms, 200+ calls, strict
  `json_schema`, zero schema failures, measured 2026-08-22 in `nida-institute/discourse-flow`.
  A revision of this line before that date claimed `gpt-4.1` was incompatible because it "uses
  a different API"; that was wrong, and `docs/ai-context/rules.md` rule 5 already said
  "GPT-4o/4.1 families".
- **`strict: true`** (recommended): Enables strict schema adherence
- **`additionalProperties: false`**: Prevents LLM from adding unexpected fields
- **All required fields documented**: Use `description` fields to guide LLM

##### Strict mode accepts only a subset of JSON Schema

Under `strict: true`, OpenAI rejects a schema outside its supported subset with **HTTP 400 at
request time** — not a worse answer, no answer. Since 0.2.1.24 `sp lint` checks these rules
before the run ([#196](https://github.com/nida-institute/LLMFlow/issues/196)), so you find out
before spending anything rather than partway through a pipeline.

**Errors** — lint fails:

| Rule | Notes |
|---|---|
| Every key in `properties` must appear in `required` | The most common mistake by far |
| Every object needs `additionalProperties: false` | Including nested objects and array items |
| The root must be an object | Not an array, not a scalar, not `anyOf` |
| `$ref`s must resolve within the document | Recursive `$ref: "#"` is fine |

**There are no optional fields.** A field you do not always want still goes in `required`; you
make it *nullable* instead:

```yaml
segmentation_rationale:
  type: ["string", "null"]     # optional in effect — but still listed in required
```

**Warnings** — reported, lint still passes: keywords outside the supported subset (`allOf`,
`not`, `if`/`then`/`else`, `patternProperties`, `default`, …), `oneOf` where `anyOf` is meant,
and the documented size limits. These are warnings rather than errors because OpenAI has
widened the accepted subset several times, and a stale rule in Scripture Pipelines must not block work the
provider would in fact accept.

Without `strict: true` the subset is not enforced, so the schema is advisory — lint says so
rather than failing. If a rule is wrong for your case, `linter_config.skip_strict_schema_check:
true` turns the check off.

The rules live in one dated table in `src/llmflow/utils/schema_preflight.py`.

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
  output: passage_info
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
  output: leaders_guide_markdown
  saveas: "outputs/leaders_guide/${passage_info.filename_prefix}_leaders_guide.md"
```

---

### type: `for-each`

Loops over a list and executes substeps for each item.

```yaml
- name: process_each_scene
  type: for-each
  for: scene
  in: "${scene_list}"
  steps:
    - name: bodies
      type: llm
      prompt:
        file: leadersguide-bodies.gpt
        inputs:
          scene: "${scene.WLC}"
          citation: "${scene.Citation}"
      output: bodies_content
      append_to: bodies_list
```

**Required Fields:**
- `for`: Name bound to each list element (XQuery-style: `for $x in $list`)
- `in`: The list to iterate over
- `steps`: Nested steps to execute for each element

**Using `append_to` in substeps:**
Within `for-each` loops, use `append_to` to accumulate results across iterations:

```yaml
- name: process_each_scene
  type: for-each
  for: scene
  in: "${scene_list}"
  steps:
    - name: analyze_scene
      type: llm
      prompt:
        file: analyze.gpt
        inputs:
          scene: "${scene}"
      output: analysis
      append_to: all_analyses  # Creates list: [analysis1, analysis2, ...]
```

**Loop context variable:**

Every iteration injects a `loop` dict into the step context:

| Variable | Type | Value |
|---|---|---|
| `${loop.index}` | int | 1-based position in the list |
| `${loop.total}` | int | total number of items |
| `${loop.first}` | bool | `true` on the first iteration |
| `${loop.last}` | bool | `true` on the last iteration |

```yaml
- name: process_each_scene
  type: for-each
  for: scene
  in: "${scene_list}"
  steps:
    - name: log_progress
      type: function
      function: builtins.print
      inputs:
        text: "Scene ${loop.index} of ${loop.total}"
```

For nested `for-each` loops, the inner loop's `loop` variable shadows the outer one — consistent with how the `for` variable works.

**Important notes:**
- Each iteration has its own isolated context
- Variables from outer scope are accessible via `${var}`
- Use `append_to` to collect results into a list variable
- Nested `for-each` loops are supported

**Optional modifiers** — reshape the list before iterating:

| Field | Type | Effect |
|---|---|---|
| `order_by` | expression | Sort the list by this expression before iterating |
| `group_by` | expression | Group iterations by this expression before processing |
| `parallel` | integer | Number of iterations to run concurrently (default `1` = sequential); results are kept in input order |

```yaml
- name: analyze_pericopes
  type: for-each
  for: pericope
  in: "${pericopes}"
  order_by: "${pericope.sequence}"   # iterate in sequence order
  parallel: 4                        # up to 4 iterations at once
  steps:
    - name: analyze
      type: llm
      prompt: { file: analyze.gpt, inputs: { p: "${pericope}" } }
      output: analysis
      append_to: analyses
```

---

### type: `window`

Groups a list into **windows** (sliding, tumbling, or condition-based) and runs substeps
for each window. Like `for-each`, but each iteration binds a *list* of elements rather than a
single item — useful for chunking long inputs (e.g. by token budget) before an LLM step.

```yaml
- name: chunk_verses
  type: window
  for: chunk               # binds each window (a list) to ${chunk}
  in: "${verses}"          # the list to window over
  size: 10                 # 10 elements per window
  stride: 10               # advance 10 each time (tumbling); < size = sliding/overlap
  steps:
    - name: summarize_chunk
      type: llm
      prompt: { file: summarize.gpt, inputs: { verses: "${chunk}" } }
      output: chunk_summary
      append_to: summaries
```

#### Physical windows, logical units

`size` and `size_by_tokens` bound a **physical** block — items or tokens, arithmetic on the
input list, knowable before the call. What the LLM finds inside that block — pericopes,
clauses, sections — is **logical**, and knowable only after the call returns. So where the
next window should begin cannot be computed in advance: it depends on where the logical units
fell, which is an output, not an input.

You can decide in advance to read the next fifty pages. You cannot decide in advance to stop
at the end of a chapter, because you do not know where the chapter ends until you have read
it.

**A fixed `stride` asserts knowledge you do not have.** It is right when list items are
independent — summarise every 10 reviews, embed every 500 tokens. It is wrong whenever the
LLM's job is to find structure *inside* the block, because a fixed cut lands mid-unit and the
model must either split a unit across two calls or drop it. For that case, use
`!window_advance` and drive the next start from the model's own output.

**The corollary is the load-bearing half.** In a non-final window the last logical unit the
model returns is untrustworthy — the physical cut may have truncated it, so its beginning is
known and its end is not. Therefore:

1. **Discard the last logical unit** from your accumulated output.
2. **Resume from the trailing edge of the last unit you kept** — never from the opening of
   the unit you dropped. Those two positions coincide only when the model's output has no
   gaps, and a model that can leave gaps will. When it does, a cursor set to the dropped
   unit's opening skips the uncovered region and no later window ever sees it.
3. **The final window keeps everything** — nothing truncated it.

Half of this is worse than none: a cursor without the discard accumulates a unit and then
re-processes it, producing duplicates; the discard without a cursor loses it.

**The engine does not enforce any of step 1–3.** It advances the cursor you give it and
raises only on a cursor that is not a non-negative integer, or that fails to advance beyond
the current start. Keeping the right units is pipeline-side discipline, and a run that gets
it wrong loses content silently — the guards will not catch it.

The cursor is **a list index into `in:`**, not a domain identifier. Converting a domain
boundary (a verse id, a section name) to a position is the pipeline's job.

#### `size` and `stride` are resolved once, before the loop starts

`size` and `stride` accept a literal or a `${...}` expression. An expression is resolved
**once, at step entry** — the same point `in:` is resolved, before anything has iterated — and
never again. `include_partial`, `size_by_tokens` and `stride_by_tokens` remain literal-only.

**Why resolution happens there and nowhere later.** These fields describe the partition, and
the partition has to be knowable at the start of the loop: `sp lint` can then check the shape
before a single call is made, and a reader can see from the YAML how the input will be divided.
A value that changed *during* loop execution would make the partition depend on state
accumulated by earlier iterations — and because each iteration's `outputs` overwrite the outer
variable (last-iteration-wins, see below), that state is not visible in the pipeline file. Two
runs of the same pipeline over the same input could then window it differently, and
`--rewind-to` could replay it differently again. A variable fixed before the loop cannot do
that: it is still a constant for the loop.

**What lint can and cannot verify.** The variable's *name* is checked as usual — an undefined
`${typo}` is an error. Its *value* cannot be, so lint emits a warning saying so and naming the
run-time consequence:

| `size:` | `sp lint` |
|---|---|
| `50` | silent — verified |
| `"${window_size}"`, name defined | **warning** — cannot verify it is a positive integer; a bad value fails when the step starts |
| `"${typo}"`, name undefined | **error** |
| `0` | **error** — must be a positive integer |
| `"10"` | **error** — a quoted literal is not an expression, and is not coerced; coercing it would hide a typo |

A `--var` value arrives as a string, so `--var window_size=50` resolves to `"50"` and is
coerced to `50`. Anything that does not resolve to a positive integer fails at step entry,
before the first call, naming both the expression and what it resolved to.

**Variation from what a run discovers has its own mechanism, and it is guarded.**
`!window_advance` is how the partition depends on the model's output. It is auditable — the
cursor is one named value, computed by one declared step, per iteration — and the engine
rejects a cursor that is not a non-negative integer or that fails to advance. Resolving `size`
per iteration would be a second, unguarded route to the same effect, which is why resolution
is pinned to step entry and not repeated.

So the rule is: **the physical block is declared before the loop; the logical boundary is
discovered inside it.** A variable may set the block, because a value fixed before the first
iteration is still declared. Nothing may change the block once iteration has begun. Keep those
two apart and a misbehaving run has one place to look.

If that changes, the safe form is narrow and stays narrow: resolve **once, at step entry,
from values fixed before the run** — never per iteration. Per-iteration resolution is a
different feature with a different argument to win.

**Fields:**

| Field | Type | Meaning |
|---|---|---|
| `for` | string | Loop variable bound to each window — a *list* of elements. |
| `in` | expression | The list to window over. |
| `size` | integer | Fixed window size in elements. Omit to end windows dynamically via `!window_advance`. |
| `stride` | integer | Elements to advance after each window. Default: same as `size` (tumbling); less than `size` = sliding. |
| `include_partial` | boolean | Include a final window smaller than `size`. Default: `true`. |
| `start_when` | expression | Begin a window when this evaluates true. |
| `end_when` | expression | End a window when this evaluates true. Alternative to `!window_advance`. |
| `size_by_tokens` | integer | Token-based window size instead of element count. Requires `model`. |
| `stride_by_tokens` | integer | Token-based stride. Default: `0`. |
| `model` | string | Model used for token counting when `size_by_tokens` is set. |
| `steps` | array | Steps to execute for each window. |

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
      output: cultural_notes

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

### type: `json`

Constructs a JSON value (object, array, or scalar) from variables already in context and stores it under a named key. Use this when you need to assemble a structured value mid-pipeline from step outputs.

```yaml
- name: build_scene
  type: json
  output: scene_object          # required — context key to store the result
  value:                        # required — any YAML value; ${var} resolved at execution time
    scene_id: "${scene.scene_id}"
    canonical_reference: "${scene.canonical_reference}"
    sensory_items: "${scene.sensory_items}"
    characters: "${scene.characters}"
```

Arrays are also valid:

```yaml
- name: collect_ids
  type: json
  output: id_list
  value:
    - "${scene.scene_id}"
    - "${passage.id}"
```

**Required Fields:**
- `outputs`: Name of the context variable the result is bound to.
- `value`: Any YAML value — object, array, or scalar. `${var}` references are resolved via the same `resolve()` mechanism used throughout the pipeline. Exact `${var}` references (nothing else on the line) return the native Python value, so a list stays a list.

**Notes:**
- `value` may be nested arbitrarily deep; resolution is recursive.
- For static objects that do not depend on step outputs, use the pipeline-level `variables:` section instead.

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

### type: `scripture`

Fetches one passage from one **named** edition. The edition is a name resolved through the
registry in `~/.sp/editions/`, never a path in the pipeline — so the same pipeline runs on a
machine where the sources live somewhere else.

```yaml
- name: fetch-source
  type: scripture
  edition: SBLGNT             # a registered edition
  passage: "${passage}"       # MRK · MRK 1 · MRK 1:1 · MRK 1:1-8 · MRK 1:40-2:12
  format: milestones          # plain | milestones | usj   (default: milestones)
  versification: eng          # optional; the scheme `passage` is written in
  output: source_text
```

**Required Fields:**
- `edition`: Name of a registered edition
- `passage`: A reference, in any of the five forms above
- `output`: Variable name to store the result

**Optional Fields:**
- `format`: The shape of the result (see below). Default `milestones`.
- `versification`: The scheme `passage` is written in. See *Versification*.
- `saveas`, `append_to`: as for any step.

#### Choosing a format

Verses are **milestones, not containers**: the result is running text with verse positions
marked, never a mapping keyed by verse. Chopping text at verse boundaries destroys the sentence
and clause structure that analysis depends on, and a verse-keyed shape makes that the easy path.

| format | what you get | size | reach for it when |
|---|---|---|---|
| `plain` | running text, no addressing | 1.0× | the prompt never needs to cite a verse — the cheapest form, and the only one a whole-book step can afford |
| `milestones` | `⌊1:1⌋ text` | 1.07× | **the default.** The model can cite a verse, and the cost over bare text is under a tenth |
| `usj` | a USJ document | 2.56× codepoints, 6.74× as escaped JSON | something downstream must address individual words, or you need a standard interchange format |

The multipliers are measured, not estimated. `usj` costs roughly six times `milestones` once
escaped into a JSON payload, which is why it is not the default: pay for structure when
something consumes the structure.

`format: usj` returns a **dict**, not a string — one `chapter` node per chapter, one `para`
inside each, `verse` nodes and text. The Macula sources carry no paragraph structure, so there
is none to represent; a `para` per chapter is the least the USX grammar allows. Flattening the
document reproduces `format: milestones` exactly, and that equivalence is a test.

#### Versification

**A reference is not a location until a scheme is named.** `PSA 51:1` is `PSA 51:3` in the
original-language numbering and `PSA 50:3` in the Vulgate; Malachi has four chapters in English
and three in Hebrew. A pipeline that asks two editions for "the same" reference without saying
which numbering it means is comparing unrelated verses, and nothing reports an error.

**An edition's scheme is a property of that edition, and there is no global default.** A
Byzantine Greek text and a critical text are numbered differently; so are two English
translations. Guessing would be wrong exactly where schemes differ. The scheme is found in
three ways, in order:

1. **`versification_scheme` in the edition's registry entry** — always wins.
2. **A Paratext project's `Settings.xml`**, for `kind: usfm` editions. Paratext records a
   number; `data/versification-editions.json` maps it to a scheme. A project carrying a
   `custom.vrs` overlay is reported, because that overlay is not read.
3. **The table of editions we construct**, in the same file — `SBLGNT` and `WLC` are `org`,
   `BSB` is `eng`, each with the evidence recorded beside it.

If none of the three answers and you ask for a cross-scheme mapping, that is an **error** naming
the field to add. Without `versification:` no mapping happens, so an edition with an unknown
scheme keeps working for everything else.

`versification:` on the step names the scheme **your `passage` is written in**. When it differs
from the edition's, the reference is mapped *before* any text is read:

```yaml
- name: hebrew-by-english-reference
  type: scripture
  edition: WLC                # numbered `org`
  passage: "PSA 51:1"         # ...but I am counting in English
  versification: eng
  output: psalm               # returns org PSA 51:3 — the verse an English reader means
```

Omit it and the edition's own scheme governs, which is the right default for a single edition.

Schemes are the Copenhagen Alliance mappings, installed into `~/.sp/versification/` by
`sp init`. Six ship: `org` (the hub every scheme maps through), `eng`, `lxx`, `vul`, `rsc`,
`rso`. A custom scheme is a JSON file you place in that directory; it may set `basedOn` to
inherit from another and list only what it changes.

Three behaviours are deliberate, because the alternative in each case is a silent error:

- **An unmappable reference raises.** A verse outside its scheme's bounds is an error, never an
  empty result that reads like an absence of text.
- **An ambiguous reverse mapping raises**, naming every candidate. Where a scheme divides what
  another joins, one verse can correspond to several — `DAN 4:4` is reached from both `DAG 4:1`
  and `DAG 4:7`, which are not adjacent — so there is no single answer to return and no span
  that would be true.
- **A mapping entry whose two sides cover different numbers of verses is skipped and reported.**
  Seven such entries ship in the standard schemes. Guessing what one meant would put a passage
  somewhere the data does not say.

Two fields of the specification, `mergedVerses` and `partialVerses`, are **not yet
interpreted**; loading a scheme that carries either says so. `lxx` carries 74 `partialVerses`.

---

### type: `basex`

Runs an XQuery against a local BaseX database via the `basex` CLI.

```yaml
- name: query-verses
  type: basex
  database: acai                        # bound as $database in the query
  query_file: queries/get-passage.xq    # path to .xq file
  inputs:                               # bound as XQuery external variables
    passage: "${passage}"
    source: "${source}"
  timeout_seconds: 120                  # optional, seconds (default: 120)
  output: query_result
  saveas: "outputs/passages/${passage}.json"
```

**Required Fields:**
- `database`: Name of the BaseX database
- `query_file`: Path to the `.xq` file
- `output`: Variable name to store the result

**Optional Fields:**
- `inputs`: Key-value pairs resolved from pipeline context and passed to BaseX as **external
  variable bindings** (`-b<key>=<value>`). The query must declare each one, e.g.
  `declare variable $passage external;`. The query file is never modified — no string
  substitution is performed, so XQuery curly braces (computed constructors, maps, arrays) are
  safe.
- `timeout_seconds`: Seconds before the BaseX process is killed (default 120).
- `saveas`: File path to save the output (supports `${var}` substitution).

**Selecting the database.** `database:` is bound as the external variable `$database`. The
keyword and the XQuery variable are deliberately the same word:

```xquery
declare variable $database external;
...
for $e in collection($database)//entity
```

Do not also pass `database` through `inputs` — both bind `$database`, and that is a lint
error rather than a precedence rule. BaseX accepts duplicate `-b` flags for one variable,
takes the last silently and exits 0, so a pipeline could name one database while the query
read another and still report success.

> **Changed in 0.2.1.24** ([#189](https://github.com/nida-institute/LLMFlow/issues/189)):
> `database:` was previously required by the linter and then discarded, so queries hardcoded
> the database name or smuggled it through an ad-hoc `inputs: db:` entry. If you have queries
> declaring `$db`, rename the variable to `$database` and drop the `inputs` entry; `db` is now
> reported as a typo for `database`. Note that BaseX silently ignores a binding for a variable
> the query does not declare, so a stale `db:` fails quietly rather than loudly.

**Prerequisites:** The `basex` executable must be on `PATH` with a running BaseX instance.

---

### type: `duckdb`

Runs a SQL query against an in-process DuckDB engine, registering context values as tables
or parameters. Useful for joins, aggregation, and filtering over tabular data (e.g. rows
from `load_csv`/`load_tsv`).

```yaml
- name: top-lemmas
  type: duckdb
  query_file: queries/top-lemmas.sql   # path to a .sql file
  inputs:
    words: "${morphology_rows}"   # registers the context list as a DuckDB table `words`
  format: records                 # list of dicts (default)
  output: top_lemmas
```

**Required Fields:**
- `query_file`: Path to the `.sql` file. Relative paths resolve against `queries_dir`
  (default `queries`). Inline SQL via `query:` is **not** implemented — see
  [#190](https://github.com/nida-institute/LLMFlow/issues/190).
- `outputs`: Variable name to store the result

**Optional Fields:**
- `inputs`: Map of table/parameter name → context key. Context values (e.g. `list[dict]`)
  are registered as DuckDB tables so the query can reference them by name.
- `format`: Output shape. `records` (default) returns a `list[dict]`.

**Prerequisites:** the `duckdb` Python package (installed with Scripture Pipelines).

---

### type: `load_json` / `load_yaml` / `load_xml` / `load_csv` / `load_tsv` / `load_text`

Load a file into the pipeline context without writing a Python function. These first-class step types are discoverable and replace `type: function` with an explicit loading primitive.

```yaml
- name: load_book_summary
  type: load_json
  path: "${intermediate_book_dir}/book-summary.json"
  output: book_summary
```

| Step type | Returns |
|-----------|---------|
| `load_json` | `dict` or `list` — parsed JSON |
| `load_yaml` | `dict` or `list` — parsed YAML |
| `load_xml` | `lxml.etree._Element` — full lxml tree; supports XPath/XSLT downstream |
| `load_csv` | `list[dict]` — one dict per row, keys from header row |
| `load_tsv` | `list[dict]` — shorthand for `load_csv` with `delimiter: "\t"` |
| `load_text` | `str` — full file contents |

**Required fields:**
- `path`: File path; supports `${var}` substitution
- `outputs`: Context variable name to store the result

**Optional fields:**
- `delimiter`: For `load_csv`, overrides the default `,`. Use `"\t"` to parse TSV files via `load_csv`.

**Path substitution:** `${var}` references are resolved from the pipeline context at runtime. Static paths (no `${...}`) are checked for existence at lint time.

**Raises:** `FileNotFoundError` at runtime if the file does not exist.

---

### type: `load_directory`

Load all files matching a glob pattern from a directory into a list — one parsed item per file, in sorted order.

```yaml
- name: load_acai
  type: load_directory
  path: "${acai_dir}/${book_ref.book_number}/"
  pattern: "*.json"
  format: json
  output: acai_files
```

**Required fields:**
- `path`: Directory path; supports `${var}` substitution
- `pattern`: Glob pattern relative to `path` (e.g. `*.json`, `*.md`)
- `format`: How to parse each file — one of `json`, `yaml`, `xml`, `csv`, `tsv`, `text`
- `outputs`: Context variable; always receives a `list`

Files are loaded in **sorted filename order** for reproducibility.

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
  output: verse_list
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
  output: term_rows
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
  output: my_var  # Now available as ${my_var}
```

### Using Variables

**In YAML:**
- Simple: `"${passage}"`
- Nested object: `"${scene.WLC}"` or `"${scene.Citation}"`
- Array indexing: `"${scene_list[0]}"` — single item by index (supports negative: `"${scene_list[-1]}"`)
- Array slicing: `"${scene_list[-3:]}"` — last 3 items, `"${scene_list[:5]}"` — first 5,  `"${items[2:8]}"` — range, `"${items[::2]}"` — every 2nd item
- Array mapping: `"${scene_list[*].Title}"` — extracts all `Title` fields as a flat list, one entry per item
- Combined operations: `"${pericope_results[-3:][*].analysis}"` — slice then extract field

**In prompt / template files (`.gpt`, `.md`):**
- Use `{{var}}` for substitution
- Access nested fields with dot notation: `{{scene.WLC}}`
- Index into lists: `{{items[0]}}`
- Slice notation: `{{items[-3:]}}`

---

## 💾 Saving Outputs

### `outputs:` — storing results in context

`outputs` controls what variable name(s) the step result is stored under in the pipeline context.

```yaml
output: my_var          # string — stores result as context["my_var"]
output:                 # list of one — same effect
  - my_var
output:                 # list of N — unpacks result tuple/list into N variables
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
    output: passage_info

  # Generate exegetical background
  - name: generate_exegetical_culture
    type: llm
    prompt:
      file: exegetical-pericope-psalms-e1.gpt
      inputs:
        source: "${source}"
        passage: "${passage}"
    output: exegetical_culture
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
    output: scene_list
    log: debug

  # Process each scene
  - name: process_each_scene
    type: for-each
    for: scene
    in: "${scene_list}"
    steps:
      - name: bodies
        type: llm
        prompt:
          file: leadersguide-bodies.gpt
          inputs:
            passage: "${passage}"
            scene: "${scene.WLC}"
            citation: "${scene.Citation}"
        output: bodies_content
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
        output: leadersguide_scene_markdown
        append_to: leadersguide_scenes_markdown_list

  # Concatenate all scenes
  - name: concat_leadersguide_scenes_markdown
    type: function
    function: llmflow.utils.data.flatten_json_to_markdown
    inputs:
      data: "${leadersguide_scenes_markdown_list}"
    output: leadersguide_scenes_markdown

  # Save final guide
  - name: save_leaders_guide
    type: function
    function: llmflow.utils.io.render_markdown_template
    inputs:
      template_path: "templates/leadersguide_template.md"
      variables:
        passage: "${passage}"
        leadersguide_scenes_markdown: "${leadersguide_scenes_markdown}"
    output: leaders_guide_markdown
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

#### Prompt Mixins

Reuse shared text across multiple prompt files with inline mixin directives:

```
{{mixin:../mixins/output-language.md}}
```

The directive is replaced at render time with the full contents of the referenced file. Paths are relative to the prompt file that contains the directive.

**Conventions:**
- Mixin files are plain Markdown fragments — no headers required, no frontmatter
- Place shared mixins in a `prompts/mixins/` directory alongside your prompt files
- Mixins do not need to be listed in the prompt contract (`requires:`) — they are expanded before contract validation

**Example:**
```
<!--
prompt:
  requires:
    - passage
-->

Analyze the following passage: {{passage}}

{{mixin:../mixins/output-language.md}}
```

The linter skips `{{mixin:...}}` patterns — they are not treated as missing variables.

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
- **Array access**: `"${scene_list[0]}"` — single item (supports negative: `[-1]` for last)
- **Array slicing**: `"${scene_list[-3:]}"`, `"${items[:5]}"`, `"${items[2:8]}"`, `"${items[::2]}"` — Python slice syntax
- **Array mapping**: `"${scene_list[*].Title}"` — extracts all `Title` fields as a flat list
- **Combined**: `"${results[-5:][*].analysis}"` — slice then extract field from each item

### Template Engine Implementation

Scripture Pipelines uses a **custom template engine** with regex-based substitution:
- In prompt and template files, `{{variable}}` placeholders are
  replaced using values from the current context.
- In pipeline YAML, `${variable}` expressions are resolved when
  constructing step inputs and file paths.
- Dot notation (`scene.WLC`), indexing (`items[0]`), and slicing (`items[-3:]`) are
  supported in both forms.

**Summary of syntax by context:**
- **Pipeline YAML**: `${var}` with dollar sign.
- **Prompt / template files**: `{{var}}` double curly braces.
