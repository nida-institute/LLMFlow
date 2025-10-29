# ⚙️ Getting Started with LLMFlow

LLMFlow is a declarative pipeline runner for LLM-assisted content generation. Install it once, use it across multiple resource repositories (lexicons, guides, exegetical notes). Resource repos contain domain pipelines, prompts, and edited outputs; this repo provides the engine.

---

## 1. Prerequisites
- Python 3.10+
- An LLM provider key (e.g. OPENAI_API_KEY) supported by the `llm` package
- Git

(Optional for contributing: Hatch)

---

## 2. Clone Engine (Public Repo)

```bash
git clone https://github.com/nida-institute/LLMFlow.git
cd LLMFlow
pip install -e .
llmflow --version
llmflow --help
```

For contributors using Hatch:

```bash
pip install hatch
hatch shell
```

---

## 3. Set Environment Variables

Create `.env` in any resource repo (or export in shell):

```env
OPENAI_API_KEY=sk-your-key
```

Load manually:

```bash
export OPENAI_API_KEY=sk-your-key
```

---

## 4. Resource Repository Pattern

Each resource repo (e.g. leaders-guides, lexicon) has:

```
pipelines/
prompts/
templates/
outputs/        # Generated + human-edited
```

Install LLMFlow once, then inside any resource repo:

```bash
llmflow run --pipeline pipelines/your-pipeline.yaml --var passage="Psalm 23"
```

---

## 5. Pipeline Basics

Example snippet:

```yaml
name: sample
variables:
  source: WLC

steps:
  - name: guide_intro
    type: llm
    prompt:
      file: intro.gpt
      inputs:
        passage: "${passage}"
        source: "${source}"
    outputs: intro_text
    saveas: "outputs/${passage}_intro.md"
```

Variable reference syntax in YAML: `${var}`
Prompt/template variable syntax: `{{var}}`

---

## 6. Prompt Contract (.gpt)

Header:

```gpt
<!--
prompt:
  requires:
    - passage
    - source
  optional: []
  format: Markdown
  description: Intro section for passage
-->
Generate an introduction for {{passage}} using {{source}}.
```

Linter enforces required inputs via `prompt.inputs` in the pipeline step.

---

## 7. Running & Linting

```bash
# Dry run (no LLM calls / saves)
llmflow run --pipeline pipelines/sample.yaml --dry-run

# Lint only
llmflow lint --pipeline pipelines/sample.yaml

# Run with CLI variable override
llmflow run --pipeline pipelines/sample.yaml --var passage="Luke 1:1-4"
```

List pipelines (if implemented):

```bash
llmflow list
```

---

## 8. Templates

Markdown templates can use:

```markdown
# {{passage}} Guide

{{intro_text}}
```

Function step:

```yaml
- name: assemble
  type: function
  function: llmflow.utils.io.render_markdown_template
  inputs:
    template_path: "templates/guide.md"
    variables:
      passage: "${passage}"
      intro_text: "${intro_text}"
  outputs: guide_markdown
  saveas: "outputs/${passage}_guide.md"
```

---

## 9. Multi-Repo Workflow

1. Keep engine updated (`git pull` in LLMFlow).
2. Edit domain pipelines/prompts in resource repos.
3. Generate outputs (`llmflow run ...`).
4. Human edits outputs → commit changes.
5. Regenerate selective steps as needed.

---

## 10. Troubleshooting

| Issue | Check |
|-------|-------|
| Missing variable | Name mismatch in `${var}` or `{{var}}` |
| Lint failure | Ensure all `requires` present in `prompt.inputs` |
| File not saved | Confirm `saveas` path directory writable |
| Unsubstituted placeholder | Verify braces: `{{var}}` in .gpt/.md |
| API error | Validate OPENAI_API_KEY or provider key |

---

## 11. Planned Enhancements

- MCP adapter (selective step regeneration, diff tools)
- Unified `{{var}}` substitution in prompt rendering
- Response caching

---

## 12. License Notice

Apache 2.0
Copyright 2025 Biblica, Inc.

See LICENSE for full terms.

---

## 13. Next Steps

- Create a resource repo and add a first pipeline.
- Add unit tests around critical transformations.
- Introduce `for-each` for multi-scene or lexicon entries.
- Prepare for MCP integration (context/tool exposure).

