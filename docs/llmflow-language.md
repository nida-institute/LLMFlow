# 📘 LLMFlow Language Specification

An **LLMFlow** is a YAML file that describes a pipeline of steps to be executed using LLM prompts, variable substitution, iteration, and file output.

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

---

### type: `function`

Calls a Python function from the LLMFlow library or custom code.

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
- `llmflow.utils.data.parse_bible_reference` - Parse Bible references
- `llmflow.utils.io.render_markdown_template` - Render markdown templates
- `llmflow.utils.io.save_json` - Save JSON to file
- `llmflow.utils.data.flatten_json_to_markdown` - Convert JSON to markdown
- `llmflow.utils.data.identity` - Pass through data unchanged

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
llmflow run --pipeline pipeline.yaml --var passage="Psalm 23"
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
- Array mapping: `"${scene_list[*].Title}"` - extracts all Title fields

**In prompt / template files (`.gpt`, `.md`):**
- Use `{{var}}` for substitution
- Access nested fields with dot notation: `{{scene.WLC}}`
- Index into lists: `{{items[0]}}`

---

## 💾 Saving Outputs

### `saveas:` field

Any `llm` or `function` step can save its output to a file:

```yaml
- name: save_leaders_guide
  type: function
  function: llmflow.utils.io.render_markdown_template
  inputs:
    template_path: "templates/leadersguide_template.md"
    variables:
      passage: "${passage}"
  outputs: leaders_guide_markdown
  saveas: "outputs/leaders_guide/${passage_info.filename_prefix}_leaders_guide.md"
```

**Features:**
- Automatically creates parent directories if they don't exist
- Supports variable substitution in paths: `${variable}`
- Works with both `llm` and `function` steps

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
llmflow run --pipeline pipelines/storyflow-psalms.yaml --var passage="Psalm 23"
```

### Dry run (preview without execution)
```bash
llmflow run --pipeline pipelines/storyflow-psalms.yaml --dry-run
```

### Set multiple variables
```bash
llmflow run --pipeline pipelines/my-pipeline.yaml \
  --var passage="Mark 1:1-8" \
  --var source="WLC"
```

### Skip linting
```bash
llmflow run --pipeline pipelines/my-pipeline.yaml --skip-lint
```

### Rewind to a step (replay from saved artifacts)

`--rewind-to <step-name>` replays the pipeline from disk instead of calling the LLM again. Every step up to and including the named step is satisfied by reading its previously saved file; every step after it executes normally. This is useful when you want to change a later step without re-running expensive upstream LLM calls.

```bash
# Re-run everything after `generate_discourse_outline`, loading that step and
# all earlier steps from their saved artifacts instead of calling the LLM.
llmflow run --pipeline pipelines/discourse-flow.yaml \
  --var passage="Mark 11:12-25" \
  --rewind-to generate_discourse_outline
```

**Requirements for a rewindable step:**
- The step must declare `saveas:` pointing to the file that holds its output.
- The step must declare a single `outputs:` variable name.
- The `saveas` path must be fully resolvable (no unresolved `${...}` variables).
- Steps that use `append_to:` are not rewindable.

If the saved file is missing LLMFlow raises a clear error rather than silently re-running.

### Stop after a step

`--stop-after <step-name>` halts the pipeline immediately after the named step completes, without running any subsequent steps. Combine with `--rewind-to` to re-run exactly one step of a long pipeline.

```bash
# Replay up through enrich_passage from disk, re-run generate_discourse_outline,
# then stop — useful to inspect the outline before continuing.
llmflow run --pipeline pipelines/discourse-flow.yaml \
  --var passage="Mark 11:12-25" \
  --rewind-to enrich_passage \
  --stop-after generate_discourse_outline
```

### Validate a pipeline
```bash
llmflow lint pipelines/my-pipeline.yaml
```

### Show version
```bash
llmflow --version
```

---

## 🤖 LLM Configuration

LLMFlow uses the [`llm` package](https://llm.datasette.io/) by Simon Willison, which supports multiple LLM providers through plugins.

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
llmflow lint pipelines/my-pipeline.yaml
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
- **Array mapping**: `"${scene_list[*].Title}"` - extracts all Title fields

### Template Engine Implementation

LLMFlow uses a **custom template engine** with regex-based substitution:
- In prompt and template files, `{{variable}}` placeholders are
  replaced using values from the current context.
- In pipeline YAML, `${variable}` expressions are resolved when
  constructing step inputs and file paths.
- Dot notation (`scene.WLC`) and simple indexing (`items[0]`) are
  supported in both forms.

**Summary of syntax by context:**
- **Pipeline YAML**: `${var}` with dollar sign.
- **Prompt / template files**: `{{var}}` double curly braces.
