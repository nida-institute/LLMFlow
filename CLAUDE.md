# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Protocol

**Address the user as "Captain" or "Sir"** — this implements the Captain Kirk model:
- The user commands (decides strategy, sets direction)
- AI implements (executes tactics, provides analysis)
- Establishes clear authority: **The Captain's problem, not the AI's inference**

**Why this matters:**
- Shows AI has read and internalized these instructions
- Prevents AI from "solving the wrong problem" by assuming intent
- Reinforces that AI serves the user's goals, not its own pattern-matching impulses
- Creates accountability: AI solutions must align with Captain's actual requirements

## Repository Context

This is the **LLMFlow core engine** — a declarative YAML-driven pipeline runner for AI-assisted biblical and linguistic scholarship. The CLI entry point is `sp` (Scripture Pipelines). Do not confuse this with repositories that *use* LLMFlow (e.g., ears-to-hear, which has LLMFlow/ as a subdirectory).

Key indicators you're in the correct repo: `src/llmflow/cli.py`, `src/llmflow/runner.py`, and `pyproject.toml` defining the `llmflow` package.

**Before making changes:**
1. **Check `docs/ai-context/index.md` FIRST** — maps every topic to the right file, prevents duplicating existing tested code
   - Example: Biblical reference parsing already exists at `llmflow.utils.data.parse_bible_reference()`
   - Example: GUI has dual-location setup (gui/backend vs src/llmflow/gui) - see gui-architecture.md
2. Consult `docs/index.json` — code architecture and module structure

## Commands

**This project uses Hatch for dependency management. Always run commands inside the Hatch environment.**

```bash
hatch shell              # Enter managed environment
hatch run pytest         # Run all tests without entering shell
hatch run pytest tests/test_runner_full.py -v          # Single test file
hatch run pytest tests/ -k "test_specific_name"        # Single test by name
hatch run pytest -m "not slow"                         # Skip slow tests
hatch run pytest --cov=src/llmflow                     # With coverage

ruff check src/          # Lint
ruff format src/         # Format

pip install -e .         # Install in editable mode (inside hatch shell)
sp --version             # Verify CLI works
sp run --pipeline pipelines/your-pipeline.yaml         # Run a pipeline
sp lint --pipeline pipelines/your-pipeline.yaml        # Validate pipeline
sp run --pipeline pipelines/your.yaml --dry-run        # No LLM calls
```

**Test configuration** is in `pytest.ini`. Tests live in `tests/`, discovered as `test_*.py`.

## Architecture

### Core Execution Flow

```
CLI (cli.py)
  → Pipeline Runner (runner.py)        # Main orchestrator, step dispatch, context evolution
      → Variable Resolution (resolve()) # ${var} substitution, nested attrs, list indexing
      → Prompt Rendering (io.py)        # .gpt files, {{var}} substitution
      → LLM Adapter (utils/llm_runner.py) # call_llm(), wraps `llm` package
      → Plugin System (plugins/)        # XPath, BaseX, JSON schema, XSLT, TSV
      → Output Persistence (saveas)     # Auto-creates directories
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `src/llmflow/runner.py` | Pipeline orchestration, step dispatch, context management |
| `src/llmflow/cli.py` | CLI argument parsing, command handlers |
| `src/llmflow/utils/llm_runner.py` | LLM provider integration (OpenAI, Anthropic, Gemini via `llm` package) |
| `src/llmflow/utils/linter.py` | Schema validation, prompt contract enforcement |
| `src/llmflow/utils/io.py` | `render_prompt()` and `render_markdown_template()` |
| `src/llmflow/modules/logger.py` | Singleton logger (CRITICAL — see below) |
| `src/llmflow/modules/telemetry.py` | Cost tracking per step |
| `src/llmflow/plugins/` | Plugin registry + contrib plugins |
| `src/llmflow/registry.py` | Global resource registry (`~/.sp/`) |
| `src/llmflow/utils/rewind.py` | Checkpoint-based replay from specific steps |

### Variable Substitution

Two distinct syntaxes, used in different contexts:
- **`${var}`** — YAML pipeline configs, resolved by `resolve()` in `runner.py`. Supports nested access (`${scene.Citation}`), list indexing (`${items[0]}`).
- **`{{var}}`** — Template/prompt files (`.gpt`, `.md`), resolved by `apply_template()` in `io.py`.

**Never import Jinja2** — this project uses its own custom template resolution.

### Config Merging Order

`universal defaults → llm_config → step_options → step_config`

Apply model-specific defaults AFTER merging. Different models use different token params (`max_tokens` vs `max_completion_tokens`).

### Prompt Contract Model

Prompt files declare their dependencies in a metadata header:
```
<!--
prompt:
  requires:
    - passage
    - scene
-->
```
The linter validates all `requires` are available in `prompt.inputs` before execution.

### For-Each Loops

Each iteration receives an isolated context merge; `append_to` collects results. Each iteration's context is independent.

## Critical Patterns

### Logger (CRITICAL)

```python
from llmflow.modules.logger import Logger
logger = Logger()  # Singleton — instantiate once per module
```

- **Never** use `logging.basicConfig()` — breaks pytest's `caplog` fixture
- **Never** modify file handlers or logging configuration globally
- Logger writes to both console and `llmflow.log`

### Telemetry

Start telemetry **after** config merging, not before:
```python
# WRONG: captures step.get("model") which may be None
telemetry.start_step(name, "llm")

# CORRECT: captures the actual model after merging
telemetry.start_step(name, "llm", model=final_model)
```

### Reading Pipeline YAML Before Discussing Paths

**Never guess file paths or output locations.** The pipeline YAML is the source of truth for inputs, outputs, and processing. Variables like `${output_dir}` mean paths aren't literal — always read the pipeline config first.

## AI Authority Boundaries

**Do not declare output "production ready", "approved", or "suitable for use with groups."**

These materials are used by real communities. Deployment decisions require human accountability.

- ✅ "Technical compliance verified. Human review should assess appropriateness for intended communities."
- ✅ "Generation completed successfully. Quality assessment requires domain expert review."
- ❌ "Production ready" / "Approved" / "Suitable for immediate use with small groups"

This boundary was documented after a real violation (GitHub issue #75, March 2026).

## Workflow Guidelines

**Explain before implementing** — describe which files you'll modify, what patterns are affected, and any trade-offs. Wait for approval before making changes.

**Test-driven** — for bugs, write a test that reproduces the bug first; for features, write the failing test first.

**Scope discipline** — do not improve code outside the requested scope. If something else needs fixing, note it and create a separate issue. Unsolicited improvements create hidden dependencies.

**Before modifying these patterns, stop and explain your plan:**
- Singleton patterns (Logger, etc.)
- Module-level initialization
- Test compatibility (pytest fixtures, caplog)
- File handlers or logging configuration
- Database/state management

## Common Pitfalls

- Confusing `${var}` (YAML) with `{{var}}` (templates) — both are valid but in different contexts
- Importing Jinja2 — use the project's own template resolution
- Starting telemetry before config merging
- Using `logging.basicConfig()`
- Assuming `step.model` is the final model — always check `merged_config`
- Making changes without verifying you're in the core engine repo, not a consumer repo

## File Organization

**tmp/ Directory — Temporary and Design Files**

ALWAYS use `tmp/` for temporary files, design docs, and release tracking. NEVER clutter the repository root.

**What goes in tmp/:**
- Design documents (design-*.md)
- Release tracking (release-*.md)
- Temporary Python scripts
- Issue drafts before posting to GitHub

**Cleanup rules:**
1. Delete tmp/issue-*.md after creating GitHub issue
2. Delete tmp/release-*.md after release published
3. Move design docs to docs/ or create GitHub issues
4. Delete temporary scripts after use

See .github/copilot-instructions.md for detailed conventions.
