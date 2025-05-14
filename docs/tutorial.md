# 🧪 Writing and Running LLMFlow Pipelines: A Tutorial

This tutorial will walk you through how to **write, understand, and run an LLMFlow pipeline**, using a simple example with two steps:

1. **Retrieve the source text** (from SBLGNT or WLC)
2. **Generate a Markdown table** with one row per word, including:

   * word
   * transliteration
   * gloss
   * morphology
   * notes

This framework is useful for building GPT workflows for Bible study, language tools, or structured research outputs.

---

## 📦 What is LLMFlow?

LLMFlow is a **declarative framework** for composing and running GPT-based pipelines using YAML. Each pipeline consists of:

* **LLM-powered steps** using `.gpt` prompt templates
* **Function steps** (rendering, saving, etc.)
* **Looping constructs** (e.g. `for-each`) for structured workflows
* **Chained outputs and inputs**, where the output of one step feeds into the next

---

## 🧱 Simple Project Layout

```
project/
├── prompts/
│   ├── fetch-source.gpt
│   └── table-output.gpt
├── outputs/
├── simple-table.yaml
├── cli.py
├── runner.py
├── io.py
└── llm_runner.py
```

---

## 🔧 Writing a Minimal Pipeline (YAML)

```yaml
pipeline:
  name: simple_table

  variables:
    source: WLC

  llm_config:
    model: gpt-4o
    temperature: 0.3
    max_tokens: 4000

  steps:
    - name: get_passage
      type: llm
      prompt:
        file: fetch-source.gpt
        inputs:
          passage: "${passage}"
          source: "${source}"
      outputs: [source_text]

    - name: make_table
      type: llm
      prompt:
        file: table-output.gpt
        inputs:
          passage: "${passage}"
          source_text: "${source_text}"
      outputs: [markdown_table]
```

This pipeline:

* Uses `fetch-source.gpt` to retrieve the passage
* Uses `table-output.gpt` to format that text as a Markdown table

You can extend this to save files with a `function` step.

---

## 📝 Writing Prompt Files

### 📋 Prompt File Header Structure

Each `.gpt` file must begin with a YAML-style header block inside an HTML comment. This is enforced by the linter and required for the prompt file to be considered valid.

Variables in the prompt body must be written using single curly braces: `{variable}` not `{{ variable }}`.
. This is enforced by the linter and is required for the prompt file to be considered valid.

Example for `table-output.gpt`:

```gpt
<!--
prompt:
  requires:
    - passage
    - source_text
  optional: []
  format: Markdown
  description: Creates a Markdown table for each word in the passage, showing gloss, transliteration, and morphology.
-->
```

The pipeline step must declare inputs that match these:

```yaml
inputs:
  passage: "${passage}"
  source_text: "${source_text}"
```

### `fetch-source.gpt`

```gpt
<!--
prompt:
  requires:
    - source
    - passage
  optional: []
  format: text
  description: Retrieves the raw source text for the given passage from the specified corpus.
-->

Use the {source} corpus to retrieve the original text of {passage}.
Return the raw word sequence.
```

### `table-output.gpt`

```gpt
<!--
prompt:
  requires:
    - passage
    - source_text
  optional: []
  format: Markdown
  description: Creates a Markdown table for each word in the passage, showing gloss, transliteration, and morphology.
-->

For the passage {passage}, format the following source text as a Markdown table.

Text:
{source_text}

Create one row per word. Columns:
- Word
- Transliteration
- Gloss
- Morphology
- Notes (leave blank unless needed)
```

---

## 📃 Prompt and Pipeline Contract

Each `{{ variable }}` in the `.gpt` file must be matched by an entry in the `inputs:` of its pipeline step.

For `table-output.gpt`, these are:

```yaml
inputs:
  passage: "${passage}"
  source_text: "${source_text}"
```

---

## ▶️ Running the Pipeline

To run the simple pipeline:

```bash
python cli.py run simple-table.yaml --passage Genesis1:1
```

To check for issues:

```bash
python cli.py lint simple-table.yaml
```

---

## 📤 Sample Output

Here’s an example of what the final Markdown table might look like for `Genesis 1:1` (WLC):

```markdown
| Word     | Transliteration | Gloss       | Morphology     | Notes |
|----------|------------------|-------------|----------------|-------|
| בְּרֵאשִׁית | bereshit         | in the beginning | noun, feminine, singular construct |       |
| בָּרָא    | bara             | he created  | verb, perfect, 3ms |       |
| אֱלֹהִים  | elohim           | God         | noun, masculine, plural |       |
| אֵת      | et               | [object marker] | particle |       |
| הַשָּׁמַיִם | hashamayim       | the heavens | noun, masculine, dual |       |
| וְאֵת    | ve'et            | and [object marker] | conjunction + particle |       |
| הָאָרֶץ   | haaretz          | the earth   | noun, feminine, singular |       |
```

---

## ✅ Best Practices

* Match prompt variables with `inputs:` entries
* Validate pipelines before running
* Start simple and add complexity gradually

