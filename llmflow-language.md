# 📘 LLMFlow Language Specification

An **LLMFlow** is a YAML file that describes a pipeline of steps to be executed using LLM prompts, variable substitution, iteration, and file output.

## 🧩 Structure

```yaml
pipeline:
  name: your_pipeline_name
  variables:
    key1: value1
    key2: value2

  rules:
    - name: step_name
      type: llm | function | for-each
      ...
```

## 🔧 Types of Steps

### type: `llm`

Runs a prompt using the `llm` CLI or another LLM API.

```yaml
- name: generate_intro
  type: llm
  prompt:
    file: prompt-template.gpt
    inputs:
      passage: "${passage}"
  outputs: [intro_text]
```

- `file`: Path to the `.gpt` template file
- `inputs`: Keys are substituted into the prompt using `{key}`
- `outputs`: Captured into context variables

---

### type: `function`

Calls a Python function.

```yaml
- name: save_output
  type: function
  function: llmflow.utils.io.save_leaders_guide
  inputs:
    passage: "${passage}"
    text: "${intro_text}"
  outputs: [output_path]
```

- Function must return a value or dict with named outputs.

---

### type: `for-each`

Loops over a list and executes substeps.

```yaml
- name: process_each_scene
  type: for-each
  input: "${scene_list}"
  item_var: scene
  steps:
    - type: llm
      prompt:
        file: step1.gpt
        inputs:
          scene: "${scene}"
      append_to: step1_list
```

- `input`: Name of list to iterate over
- `item_var`: Variable name to bind each item to
- `steps`: Nested steps to execute per item
- `append_to`: Collects results into a list

---

## 🔁 Variables

- Defined in `variables` block or via `--var`
- Use `${var}` for full substitution, or `{var}` inside prompt files

---

## 🧪 Example

```yaml
pipeline:
  name: test_pipeline
  variables:
    passage: "Psalm 23"

  rules:
    - name: get_intro
      type: llm
      prompt:
        file: prompts/intro.gpt
        inputs:
          passage: "${passage}"
      outputs: [intro]
```

---

## 💡 Notes

- File paths can be relative to project root or prompt directory
- All output is normalized to Unicode NFC
- The file itself is called an **LLMFlow**
