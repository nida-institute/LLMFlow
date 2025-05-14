# 📘 LLMFlow Pipeline Language Reference

This document defines the structure, rules, and best practices for writing pipelines and `.gpt` prompt files in the custom LLMFlow framework.

---

## 🧩 Pipeline YAML Structure

Each LLMFlow pipeline is written in YAML and contains these top-level keys:

```yaml
pipeline:
  name: your_pipeline_name
  variables: { key: value, ... }
  llm_config: { model, temperature, max_tokens }
  steps:
    - name: step_name
      type: llm | function | for-each
      prompt/function: ...
      inputs: { key: value, ... }
      outputs: [output1, output2]
```

### ✅ Required Fields

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
```

---

## 🧾 .gpt Prompt File Format

Each `.gpt` file must start with a **YAML header block** wrapped in an HTML comment, followed by the prompt body. This is required by the linter.

### Example:

```gpt
<!--
prompt:
  requires:
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
```

---

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

