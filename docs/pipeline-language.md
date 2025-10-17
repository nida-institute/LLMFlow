# 📘 LLMFlow Pipeline Language Reference

<<<<<<< Updated upstream
LLMFlow is a framework for orchestrating AI workflows that seamlessly combines LLM calls, traditional functions, and iterative operations. This document defines the syntax and best practices for writing pipelines and prompts.
=======
This document defines the structure, rules, and best practices for writing pipelines and `.gpt` prompt files in the custom LLMFlow framework.
>>>>>>> Stashed changes

---

## 🧩 Pipeline YAML Structure

<<<<<<< Updated upstream
LLMFlow pipelines are YAML files that define a sequence of operations:
=======
Each LLMFlow pipeline is written in YAML and contains these top-level keys:
>>>>>>> Stashed changes

```yaml
pipeline:
  name: your_pipeline_name
  variables: { key: value, ... }
  llm_config: { model, temperature, max_tokens }
  steps:
    - name: step_name
      type: llm | function | for-each
<<<<<<< Updated upstream
      # Type-specific configuration
      outputs: output_var | [output1, output2]
      saveas: path/to/file.ext  # Optional
=======
      prompt/function: ...
      inputs: { key: value, ... }
      outputs: [output1, output2]
>>>>>>> Stashed changes
```

### ✅ Required Fields

<<<<<<< Updated upstream
* `name`: Unique identifier for the pipeline
* `steps`: List of operations to execute
* Each step must have `name` and `type`

---

## 🔗 Variable Resolution & Data Flow

### Context Variables
Steps communicate through a shared context. Outputs from one step become inputs to later steps:

```yaml
- name: parse_text
  type: function
  function: utils.parse_passage
  outputs: parsed_data

- name: analyze
  type: llm
  inputs:
    data: "${parsed_data}"  # Reference previous output
```

### Variable Syntax
- **Exact reference**: `"${variable}"` - Returns native type (list, dict, string)
- **Embedded**: `"Text with ${variable} inside"` - Always returns string
- **Nested access**: `"${user.name}"` or `"${items[0].title}"`

### Global Variables
Define defaults in `pipeline.variables` - available to all steps:

```yaml
variables:
  model: gpt-4
  temperature: 0.7
=======
* `name`: unique name for the pipeline or step
* `steps`: list of pipeline operations
* `type`: one of `llm`, `function`, or `for-each`

---

## 🪢 Context and Variable Substitution

### 🔁 Context

Each step may produce **outputs**, which are stored in the pipeline's context. These can be accessed by later steps using `${variable}` syntax.

```yaml
outputs: [source_text]
...
inputs:
  source_text: "${source_text}"
```

This allows values to flow from one step to the next.

### 📦 Global Variables

Defined in `pipeline.variables:` and available to all steps unless overridden.

```yaml
variables:
  source: WLC
>>>>>>> Stashed changes
```

---

<<<<<<< Updated upstream
## 🧠 Step Types

### LLM Steps
```yaml
- name: generate_content
  type: llm
  prompt:
    file: prompts/analyze.gpt
    inputs:
      passage: "${passage}"
      context: "${previous_result}"
  outputs: analysis
  llm_options:  # Optional, overrides pipeline defaults
    temperature: 0.3
```

### Function Steps
```yaml
- name: process_data
  type: function
  function: llmflow.utils.data.parse_bible_reference
  inputs:
    passage: "${passage_text}"
  outputs: passage_info
```

### For-Each Steps
```yaml
- name: process_items
  type: for-each
  input: "${scene_list}"  # Must be a list
  item_var: scene         # Variable name for current item
  steps:
    - name: analyze_scene
      type: llm
      prompt:
        file: prompts/scene.gpt
        inputs:
          scene: "${scene}"
      outputs: scene_analysis
      append_to: all_analyses  # Collect results
```

---

## 📄 Prompt Files (.gpt)

Prompts use a YAML header for contract definition:
=======
## 🧾 .gpt Prompt File Format

Each `.gpt` file must start with a **YAML header block** wrapped in an HTML comment, followed by the prompt body. This is required by the linter.

### Example:
>>>>>>> Stashed changes

```gpt
<!--
prompt:
  requires:
<<<<<<< Updated upstream
    - passage      # Required variables
    - source_text
  optional:
    - style        # Optional variables with defaults
  format: markdown # Expected output format
  description: Analyzes biblical text and creates detailed table
-->

Analyze the following passage: {passage}

Source text:
{source_text}

{?style}Style: {style}{/style}
```

### Prompt Syntax
- **Required vars**: `{variable}`
- **Optional vars**: `{?variable}...{/variable}` - Only rendered if present

---

## 💾 Output Handling

### Save to Files
```yaml
- name: generate_report
  type: llm
  outputs: report
  saveas: "outputs/${passage_info.filename_prefix}_report.md"
```

### Multiple Outputs
```yaml
saveas:
  - path: "outputs/report.md"
    content: "${report}"
  - path: "outputs/metadata.json"
    content: "${metadata}"
    format: json
=======
    - passage
    - source_text
  optional: []
  format: Markdown
  description: Creates a table with word-level info from the passage.
-->

For the passage {passage}, analyze the following:

{source_text}
```

### ❗ Rules for Prompt Files

* Header must be present and valid YAML
* `requires`: lists required variables
* `optional`: lists optional ones
* `format`: output type (e.g., Markdown, text, JSON)
* `description`: short explanation of what the prompt does
* Use **single curly braces** (`{variable}`) in the prompt body

---

## 🧠 Prompt–Pipeline Contract

Every `requires:` field in a `.gpt` file must be satisfied in the `inputs:` block of the step that uses it. The linter will fail if:

* A required variable is missing from the step
* The prompt uses a variable not listed in `requires` or `optional`

### ✅ Example

```gpt
# table-output.gpt
<!--
prompt:
  requires: [passage, source_text]
  optional: []
  format: Markdown
  description: Generate a table from biblical text.
-->
```

```yaml
# Pipeline step
inputs:
  passage: "${passage}"
  source_text: "${source_text}"
>>>>>>> Stashed changes
```

---

<<<<<<< Updated upstream
## 🔍 Validation & Testing

### Linting
Validates contracts between prompts and pipelines:
```bash
llmflow lint pipelines/your_pipeline.yaml
```

### Dry Run
Test without making LLM calls:
```bash
llmflow run pipelines/your_pipeline.yaml --dry-run
```

### With Variables
```bash
llmflow run pipelines/your_pipeline.yaml --var passage="John 3:16"
```

---

## 🎯 Best Practices

1. **Name steps clearly** - Use descriptive names that explain the operation
2. **Keep prompts focused** - One task per prompt for better results
3. **Use contracts** - Define all variables in prompt headers
4. **Test incrementally** - Use dry-run to validate before full execution
5. **Handle errors gracefully** - Check for required outputs before using them

---

## 🔧 Advanced Features

### Conditional Logic (Plugin)
```yaml
- name: check_condition
  type: plugin
  plugin: conditional
  condition: "${score} > 0.8"
  if_true:
    - name: high_score_path
      type: function
      ...
```

### Custom Plugins
Register custom operations by creating plugins that integrate with the framework.

=======
## 🔍 Linter Behavior

The linter validates:

* That all `.gpt` files begin with a valid YAML header block
* That required inputs are declared and provided
* That there are no unused or undefined inputs/outputs
* That variable names in the prompt match the contract

---

## 🧪 Testing and Debugging

Use lint and dry-run commands to validate:

```bash
hatch run llmflow lint --pipeline yourfile.yaml
hatch run llmflow run --pipeline yourfile.yaml --var passage="Genesis 1:1"
```

>>>>>>> Stashed changes
