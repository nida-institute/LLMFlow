# 📘 LLMFlow Pipeline Language Reference

LLMFlow is a framework for orchestrating AI workflows that seamlessly combines LLM calls, traditional functions, and iterative operations. This document defines the syntax and best practices for writing pipelines and prompts.

---

## 🧩 Pipeline YAML Structure

LLMFlow pipelines are YAML files that define a sequence of operations:

```yaml
pipeline:
  name: your_pipeline_name
  variables: { key: value, ... }
  llm_config: { model, temperature, max_tokens }
  steps:
    - name: step_name
      type: llm | function | for-each
      # Type-specific configuration
      outputs: output_var | [output1, output2]
      saveas: path/to/file.ext  # Optional
```

### ✅ Required Fields

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
```

---

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

```gpt
<!--
prompt:
  requires:
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
```

---

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

