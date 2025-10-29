# 📘 LLMFlow Tutorial (Updated)

This tutorial shows how to write and run a minimal LLMFlow pipeline that:
1. Fetches a passage (LLM-assisted)
2. Builds a Markdown word table

---

## 🧩 What Is LLMFlow?

LLMFlow is a declarative YAML workflow engine for LLM-assisted content generation:
- Steps: type llm | function | for-each
- Variable resolution: `${var}`, nested access, list indexing
- Prompt contracts: `.gpt` files declare required inputs
- Output persistence: `saveas:` on any step
- Accumulation: `append_to:` inside loops

---

## 📂 Suggested Example Layout

```
examples/
  pipelines/
    simple-table.yaml
  prompts/
    fetch-source.gpt
    table-output.gpt
  templates/
    word-table.md
  outputs/
```

---

## 📝 Pipeline YAML (Correct Structure)

```yaml
name: simple-table

variables:
  source: WLC

llm_config:
  model: gpt-4o
  temperature: 0.3
  max_tokens: 3500

steps:
  - name: get_passage
    type: llm
    prompt:
      file: fetch-source.gpt
      inputs:
        passage: "${passage}"
        source: "${source}"
    outputs: passage_text

  - name: make_table
    type: llm
    prompt:
      file: table-output.gpt
      inputs:
        passage: "${passage}"
        passage_text: "${passage_text}"
    outputs: markdown_table

  - name: save_table
    type: function
    function: llmflow.utils.io.render_markdown_template
    inputs:
      template_path: "examples/templates/word-table.md"
      variables:
        passage: "${passage}"
        markdown_table: "${markdown_table}"
    outputs: final_markdown
    saveas: "examples/outputs/${passage}_table.md"
```

---

## 🧾 Prompt File Header & Body

Prompt files use double curly braces: `{{variable}}`.

`examples/prompts/fetch-source.gpt`:
```gpt
<!--
prompt:
  requires:
    - passage
    - source
  optional: []
  format: text
  description: Retrieve the raw passage text from the given source (approximate)
-->
Retrieve the passage {{passage}} using corpus {{source}}.
Return ONLY the plain text words separated by spaces.
```

`examples/prompts/table-output.gpt`:
```gpt
<!--
prompt:
  requires:
    - passage
    - passage_text
  optional: []
  format: Markdown
  description: Produce a markdown word table with transliteration, gloss, morphology, notes.
-->
Create a Markdown table for passage {{passage}} using this text:

{{passage_text}}

Columns:
| Word | Transliteration | Gloss | Morphology | Notes |
Return ONLY the table (no extra commentary).
```

---

## 🧪 Template File

`examples/templates/word-table.md`:
```markdown
# Word Table for {{passage}}

{{markdown_table}}
```

---

## 🔍 Prompt Contract Validation

Linter checks:
- All `prompt.requires` appear under the step’s `prompt.inputs`
- Missing required inputs → error
- Optional inputs (if listed) may be omitted

---

## ▶️ Running & Linting

```bash
# Run (pass variable at CLI)
llmflow run --pipeline examples/pipelines/simple-table.yaml --var passage=Genesis1:1

# Lint before running
llmflow lint examples/pipelines/simple-table.yaml
```

Dry run:
```bash
llmflow run --pipeline examples/pipelines/simple-table.yaml --dry-run
```

---

## 📤 Sample Output (Excerpt)

```
# Word Table for Genesis1:1

| Word | Transliteration | Gloss | Morphology | Notes |
| בְּרֵאשִׁית | bereshit | in the beginning | noun fs construct | |
| בָּרָא | bara | he created | verb perf 3ms | |
...
```

---

## ✅ Key Points

- Use `variables:` at root (not `pipeline:` wrapper).
- Use `{{var}}` inside `.gpt` and template files.
- Pipeline YAML uses `${var}` to reference context.
- Function steps can render and save outputs.
- `saveas:` path can include `${variables}`.
- `append_to:` is only needed for accumulating list outputs in loops.

---

## 🔄 Extending

Add a `for-each` loop around a word list:
```yaml
- name: process_words
  type: for-each
  input: "${words_list}"
  item_var: word
  steps:
    - name: enrich_word
      type: llm
      prompt:
        file: enrich-word.gpt
        inputs:
          word: "${word}"
      outputs: enriched
      append_to: enriched_words
```

---

## 🛠 Troubleshooting

- Empty output: check required inputs match prompt header
- Variables not substituted: confirm `{{var}}` spelling and step inputs
- File not saved: ensure `saveas:` path directory exists or let LLMFlow create it
- JSON parsing: add `output_type: json` if expecting structured output

---

## 🧭 Next Steps

- Introduce scene iteration for passages with internal divisions
- Add lexicon enrichment function steps
- Integrate MCP (planned) for selective regeneration & diff tooling

---

## 🏁 Summary

This example demonstrates the minimal viable pipeline: LLM prompt → LLM transform → template render → persisted output. Expand using loops, functions, and contracts for larger scholarly or lexical workflows.

