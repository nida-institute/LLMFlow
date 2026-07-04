# LLMFlow Architecture

## 1. Purpose

LLMFlow is a declarative YAML-driven execution engine for LLM-assisted content
pipelines. It standardizes prompt contracts, variable resolution, iteration, and
output persistence while enabling domain-specific extensions and multi-repository
content management.

## 2. Core Goals

- Deterministic, inspectable pipelines (lint + contract validation before execution)
- Provider/model agnostic (via the `llm` package + plugins)
- Human-in-the-loop editing after generation (Git-managed outputs)
- Separation of engine (this repo) and resource collections (per-domain repos)
- Scalable to large content graphs (scene lists, lexicons, guides)
- AI-assistant-navigable codebase: one file per concern, named by what it does

## 3. Layers

```
CLI (cli.py)
  └── Pipeline Runner (runner.py)          # orchestration, dispatch, lifecycle
        ├── Steps (steps/)                 # executable semantics — one file per step type
        ├── Utils (utils/)                 # shared infrastructure
        ├── Plugins (plugins/)             # dynamic capability injection
        └── Modules (modules/)             # singletons: logger, telemetry, MCP client
```

### 3.1 CLI Layer — `cli.py`

Argument parsing and command dispatch. Entry point for `sp run`, `sp lint`,
`sp init`, `sp list`, `sp registry`, and `sp clean`. Delegates immediately to
`runner.py` or `cli_utils.py`; contains no pipeline logic.

### 3.2 Runner — `runner.py`

Pipeline orchestration. Responsibilities:

- Load and validate YAML (`lint_pipeline_full`)
- Initialize context from `variables:` and CLI overrides
- Drive the step sequence via `run_step()` — a dispatch table mapping step types
  to handler functions in `steps/`
- Manage the retry loop, rewind/checkpoint, and after-action signals
  (`exit`, `continue`)
- Accumulate telemetry and emit the post-run summary

`runner.py` owns the pipeline lifecycle. It does **not** contain the
implementation of any step type.

### 3.3 Steps Layer — `steps/`

This is the **executable semantics** of the LLMFlow pipeline language. Each
file defines exactly what one step type means when it executes. Reading
`steps/for_each.py` is the authoritative answer to the question "what does
`type: for-each` do?"

| File | Step type | Key responsibilities |
|---|---|---|
| `steps/llm.py` | `llm` | Prompt rendering, model config merging, debug file routing, output templates, MCP tool calls |
| `steps/for_each.py` | `for-each` | List iteration, group-by, parallel execution, loop context injection (`loop.index`, `loop.total`, `loop.first`, `loop.last`) |
| `steps/window.py` | `window`, `!window_advance` | Fixed/sliding/condition/token windows, partial-window handling |
| `steps/if_step.py` | `if` | Conditional branch execution |
| `steps/function.py` | `function` | Python function dispatch by dotted path |
| `steps/plugin.py` | `plugin` | Plugin registry dispatch |
| `steps/basex.py` | `basex` | BaseX XQuery execution |
| `steps/duckdb.py` | `duckdb` | DuckDB SQL execution |
| `steps/json_step.py` | `json` | JSON file loading |
| `steps/load.py` | `load` | Structured data loading (YAML, JSON, TSV, XML) |
| `steps/save.py` | `save` | Filesystem write with path resolution |

A new step type means a new file in `steps/`. The dispatch table in `runner.py`
gets one line.

### 3.4 Recursive Handlers and Dependency Injection

`for-each`, `window`, and `if` steps can contain nested steps. They receive
`run_step_fn` as an injectable callable rather than importing `run_step` from
`runner.py` directly. This prevents circular imports at module load time.
`runner.py` passes the real `run_step`; test code can pass a substitute or omit
it (a lazy import default fires at call time).

### 3.5 Utils — `utils/`

Shared infrastructure used by both `runner.py` and `steps/` modules.
`steps/` may import from `utils/`; `utils/` modules do not import from `steps/`
or `runner.py`.

| Module | Responsibility |
|---|---|
| `utils/context.py` | `resolve()` — `${var}` substitution, nested attr access, list indexing |
| `utils/io.py` | Prompt file loading, template rendering, `{{var}}` substitution |
| `utils/llm_runner.py` | `call_llm()`, `run_llm_with_mcp_tools()` — provider-agnostic LLM calls |
| `utils/linter.py` | Schema validation, prompt contract enforcement, path checks |
| `utils/guards.py` | `_safe_eval()`, `build_eval_locals()` — sandboxed expression evaluation |
| `utils/file_io.py` | `save_content_to_file()`, written-files registry |
| `utils/debug.py` | Debug directory management |
| `utils/step_outputs.py` | `handle_step_outputs()`, `handle_step_saveas()` |
| `utils/rewind.py` | Checkpoint-based replay from specific steps |
| `utils/data.py` | Domain utilities — Bible reference parsing, lexicon mapping |

### 3.6 Import Discipline

To prevent circular imports, layer boundaries are enforced:

- `steps/` imports from `utils/` and `modules/` only — never from `runner.py`
- `runner.py` imports from `steps/`, `utils/`, and `modules/`
- `utils/` modules do not import from `steps/` or `runner.py`
- Recursive handlers use dependency injection for `run_step`; when they must
  import it (lazy default for tests), the import is deferred inside the function

## 4. Variable Resolution

Two distinct syntaxes, resolved in different contexts:

| Syntax | Where used | Resolved by |
|---|---|---|
| `${var}` | Pipeline YAML | `resolve()` in `utils/context.py` |
| `{{var}}` | Prompt/template files (`.gpt`, `.md`) | `apply_template()` in `utils/io.py` |

`${var}` supports nested access (`${scene.Citation}`), list indexing
(`${items[0]}`, `${items[-1]}`, `${items[:-1]}`), and wildcard extraction
(`${items[*].Title}`). Jinja2 is never used.

## 5. Prompt Contract Model

Prompt files declare their input requirements in a metadata header:

```
<!--
prompt:
  requires:
    - passage
    - scene
  optional: []
  format: Markdown
-->
```

The linter validates that all `requires` entries are present in `prompt.inputs`
before execution. This is the boundary where the pipeline's runtime contract
meets the prompt author's declared intent.

## 6. Context

The pipeline context is a plain `dict` that evolves as steps execute. Each step
reads from it (via `resolve()`) and writes to it (`outputs:` / `append_to:`).
For-each iterations receive an isolated copy; `append_to` collects results back
into the parent. The context is the only communication channel between steps —
there are no side channels.

## 7. Configuration Merging

LLM step configuration merges four layers in order:

```
universal defaults → llm_config (pipeline) → step_options → step_config
```

Model-specific defaults (e.g., `max_tokens` for GPT-4,
`max_completion_tokens` for o1-series) are applied after merging. Telemetry
starts after merging, not before, so it captures the actual model used.

## 8. Output Strategy

- **Engine repo (this repo):** runtime, shared utilities, plugin API. Public.
- **Resource repos** (e.g., `ears-to-hear`): pipelines and generated artifacts
  for a specific content domain. Consumer repos install the engine as an
  editable `file:///` dependency so engine changes are immediately live.
- Generated artifacts are committed in resource repos. Human editors refine
  content in Git; `saveas` paths and `intermediate_file_directory` /
  `output_file_directory` declarations keep intermediate and final files
  organized and auditable.

## 9. Obsidian Vault Integration

Pipelines generate Obsidian vaults by writing structured file hierarchies via
`saveas`. Each note is a `.md` file; the vault is the output directory opened
in Obsidian. No special plugin or API is required.

The `semdom-greek-lexicon` pipeline illustrates the pattern: one `.md` per
Greek lemma is written into `obsidian/grc/markdown/`, with `group_by_prefix`
creating subdirectory hierarchies by first character for navigation. The vault
is browseable in Obsidian immediately after the pipeline runs.

Front-matter metadata (e.g., `status: needs-review`, semantic-domain tags)
can be included in generated notes and maintained by human editors in Git.
Index notes (lexicon indices, scene catalogs) are generated by function steps.

## 10. MCP Integration

`type: llm` steps can configure MCP tool access via the `mcp:` block:

```yaml
- name: verify-citation
  type: llm
  mcp:
    enabled: true
  prompt:
    file: verify.gpt
    inputs:
      passage: "${passage}"
  outputs: verification_result
```

When `mcp.enabled: true`, the step is dispatched through
`run_llm_with_mcp_tools()` in `utils/llm_runner.py` rather than the plain
`call_llm()` path. The MCP client is initialized via `modules/mcp.py` and
provides the LLM with dynamic tool access during inference (e.g., Bible text
lookup, lexicon queries).

## 11. AI Context — Navigating the Codebase

This section is specifically for AI assistants working on the LLMFlow engine.

**To understand what a step type does:** read `src/llmflow/steps/<type>.py`.
That file is the authoritative definition. The language documentation describes
the YAML surface; the steps module defines the execution semantics.

**To understand variable resolution:** read `src/llmflow/utils/context.py`.

**To understand prompt rendering:** read `src/llmflow/steps/llm.py` and
`src/llmflow/utils/io.py`.

**To understand the linter:** read `src/llmflow/utils/linter.py`.

**To add a new step type:**
1. Create `src/llmflow/steps/<type>.py` with a `run_<type>_step()` function
2. Add one line to the dispatch table in `runner.py`
3. Add linter validation in `utils/linter.py` if the step type has required keys
4. Add tests in `tests/test_<type>_step.py` importing from `llmflow.steps.<type>`

**Mock patch targets** must name the module where the function is defined,
not a module that re-exports it:

```python
# correct — patches where call_llm is actually called
@patch("llmflow.steps.llm.call_llm")

# wrong — patches runner's namespace, does not intercept steps/llm.py calls
@patch("llmflow.runner.call_llm")
```

**Step type YAML contracts** are documented in `docs/llmflow-language.md`.
The implementation of each contract is in the corresponding `steps/` file.

## 12. Testing Philosophy

The steps layer enables module-level test isolation. Tests for `for-each`
iteration import directly from `llmflow.steps.for_each`; tests for window
slicing import from `llmflow.steps.window`. Integration tests that exercise a
full step through `run_pipeline()` verify the dispatch path.

Tests for recursive step types (`for-each`, `window`, `if`) can call the
handler directly with a substitute `run_step_fn`, or omit it and let the lazy
import default fire.

## 13. Error Handling

- **Lint failures:** stop before execution (schema / contract errors)
- **Step failures:** `StepExecutionError` with full context; retry logic
  in `runner.py` if `retry:` is configured on the step
- **After-action signals:** `"exit"` terminates the pipeline cleanly;
  `"continue"` skips remaining steps in the current for-each iteration or
  window pass

## 14. Security

- No embedded secrets; key management delegated to the `llm` package
- `_safe_eval()` in `utils/guards.py` uses AST-based allowlisting for pipeline
  condition expressions — no `eval()` on arbitrary strings
- Output repositories are separate from the engine — generated content is
  auditable and reviewable independently
- Apache 2.0 license with institutional copyright (Biblica, Inc.)
