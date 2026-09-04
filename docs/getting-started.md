# ⚙️ Getting Started with Scripture Pipelines

Scripture Pipelines is a declarative pipeline runner for LLM-assisted content generation. Install it once, use it across multiple resource repositories (lexicons, guides, exegetical notes). Resource repos contain domain pipelines, prompts, and edited outputs; this repo provides the engine.

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
cd Scripture Pipelines
pip install -e .
sp --version
sp --help
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

Install Scripture Pipelines once, then inside any resource repo:

```bash
sp run --pipeline pipelines/your-pipeline.yaml --var passage="Psalm 23"
```

### Consumer repo `pyproject.toml` — the editable-install pattern

A resource/consumer repo runs on Scripture Pipelines but does **not** vendor it. It installs the engine
as an **editable** dependency from your local clone, so engine changes propagate immediately.
The known-good Hatch pattern:

```toml
[project]
name = "your-project"
version = "0.0.0"
requires-python = ">=3.10"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.envs.default]
post-install-commands = ["pip install -e /path/to/your/LLMFlow"]
dependencies = [
  # your project's own runtime deps, e.g. "python-dotenv"
]
```

Replace `/path/to/your/LLMFlow` with the absolute path to your Scripture Pipelines clone — it is
machine-specific; there is no portable form for editable-installing a sibling checkout.
`post-install-commands` runs the editable install after Hatch builds the env, so `sp` /
Scripture Pipelines stays live in both `hatch run …` and inside `hatch shell`. A real `[build-system]`
plus `[project]` metadata is what lets `hatch shell` set the env up cleanly — no `skip-install`
gymnastics needed.

**Why editable — and why not to "fix" it:** Scripture Pipelines is developed alongside consumer repos on
the same machine, so the editable install (`pip install -e`) picks up upstream engine fixes the
moment they land. Pinning a version, or switching to a non-editable `llmflow @ file://…`
dependency, **freezes** the engine and silently breaks that propagation — this has repeatedly
caused stale-install bugs (e.g. a `response_format` crash, and a broken `sp clean`). AI agents
in particular tend to "helpfully" reformat this into a pinned or non-editable form; **do not.**
Consumer repos guard the invariant with a test such as
`tests/test_environment.py::test_llmflow_editable_install`, and the commit-ready version-bump
step does **not** apply to `pyproject.toml` here — update `CHANGELOG.md` only.

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
    output: intro_text
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
  format: Markdown
  description: Intro section for passage
-->
Generate an introduction for {{passage}} using {{source}}.
```

Linter enforces required inputs via `prompt.inputs` in the pipeline step.

---

## 7. Running & Linting

```bash
# Lint only (new command)
sp lint --pipeline pipelines/sample.yaml

# Lint with JSON output
sp lint --pipeline pipelines/sample.yaml --json

# Run (auto-lints unless --skip-lint)
sp run --pipeline pipelines/sample.yaml --var passage="Luke 1:1-4"

# Dry run (skips all LLM calls — useful for testing variable substitution)
sp run --pipeline pipelines/sample.yaml --var passage="Luke 1:1-4" --dry-run

# Stop after a specific step (useful for debugging mid-pipeline)
sp run --pipeline pipelines/sample.yaml --stop-after step-name

# Replay from checkpoints up to a step (skips re-running earlier steps)
sp run --pipeline pipelines/sample.yaml --rewind-to step-name

# Write log to a specific file (default: llmflow.log in cwd)
sp run --pipeline pipelines/sample.yaml --log /tmp/run.log

# Verbose logging
sp run --pipeline pipelines/sample.yaml -v
```

Add --skip-lint to bypass validation.

### `sp run` flag reference

| Flag | Description |
|------|-------------|
| `--pipeline PATH` | Path to the pipeline YAML (required) |
| `--var KEY=VALUE` | Set a pipeline variable; repeatable |
| `--dry-run` | Parse and validate without making LLM calls |
| `--skip-lint` | Skip linting before execution |
| `-v` / `--verbose` | Verbose logging |
| `--log PATH` | Write logs to this file (default: `llmflow.log` in cwd) |
| `--rewind-to STEP` | Replay checkpointed steps up to and including STEP, then continue |
| `--stop-after STEP` | Stop execution after STEP completes |

List pipelines (if implemented):

```bash
sp list
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
  output: guide_markdown
  saveas: "outputs/${passage}_guide.md"
```

---

## 9. Multi-Repo Workflow

1. Keep engine updated (`git pull` in scripture-pipelines).
2. Edit domain pipelines/prompts in resource repos.
3. Generate outputs (`sp run ...`).
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

​
