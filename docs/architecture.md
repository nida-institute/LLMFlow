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
| `steps/for_each.py` | `for-each` | List iteration, `group_by`, parallel execution, loop context injection (`loop.index`, `loop.total`, `loop.first`, `loop.last`) |
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
  output: verification_result
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

## 15. Debug Request/Response Dumps

Setting `linter_config.log_level: debug` at the pipeline level makes every
`type: llm` step write its rendered request and raw response to disk — the
mechanism for seeing exactly what the model was sent and returned. There is no
`--debug` flag and no environment variable; the pipeline's `log_level` is the
switch.

- **Trigger:** `linter_config: { log_level: debug }` in the pipeline YAML
  (checked in `steps/llm.py` on the request and response save paths).
- **Location** (`utils/debug.py:_get_debug_dir`):
  `<intermediate_file_directory>/debug/<pipeline_name>/<run_key>/` when the
  pipeline declares `intermediate_file_directory` (resolved through `${...}`),
  otherwise `<cwd>/outputs/debug/<pipeline_name>/<run_key>/`. `<pipeline_name>` is
  the pipeline YAML file stem. `<run_key>` names the variables that distinguish
  this run, built from CLI `--var` values — `book-Ruth`, or `default` when there
  are none. The segment is always present, including for `default`: the directory
  is emptied at the start of a run, and without it that delete would target
  `debug/<pipeline_name>/`, wiping every sibling run (LLMFlow#198).
- **Layout** (`utils/debug.py:DebugRecorder`):

  ```
  outputs/debug/book-summary/book-Ruth/
    manifest.jsonl
    0001-segment_book-request.txt
    0001-segment_book-response.json
    0002-analyze-attempt2-request.txt
    llmflow.log
  ```

  Filenames are `<seq>-<step>[-attempt<n>]-(request|response).(txt|json)`. The
  sequence number is per run and makes each name unique and chronologically
  sortable; the attempt suffix appears from the second call to a step onward, so a
  retry no longer overwrites what it retried. Responses are written as `.json`
  when structured and `.txt` otherwise.
- **`manifest.jsonl`:** one line per model call — `seq`, `step`, `attempt`,
  `prompt_file`, `model` (the model actually called, after config merging, not the
  one declared), `passage`, `iteration`, `started`, `finished`, `status`,
  `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd` (rounded to
  micro-dollars, `null` when the model is unpriced), `request_file`,
  `response_file`. File paths are relative to the run directory so
  a run can be archived or moved intact. `sp tools replay` reads the pairing from
  here rather than inferring it from filenames; directories captured before
  0.2.1.24 have no manifest and fall back to filename matching.
- **Cleared per run:** `_clear_debug_dir` empties **this run's** directory at the
  start of the run (skipped on `--dry-run`), so a run directory reflects exactly
  one run. Sibling run directories are untouched.
- **Removed in 0.2.1.24:** `steps/llm.py:build_debug_filename` produced
  `<passage>_<prompt_stem>_(request|response).txt`. The step name appeared only
  when there was no prompt file, so two steps sharing a `.gpt` collided and the
  second overwrote the first; a retry did the same; and the timestamp — the only
  field that could order the files — appeared only when `passage` was absent. The
  sequence number now guarantees uniqueness and order.
- **Log co-location:** when `intermediate_file_directory` is declared,
  `llmflow.log` is redirected into `<debug_dir>/llmflow.log` (`runner.py`).
- **Cleanup:** `sp clean --debug-only` deletes only the debug directory;
  `sp clean --intermediate-only` preserves it.

## 16. The Declarative Schema as Single Source

The pipeline language is defined once, declaratively, in `PIPELINE_SCHEMA`
(`src/llmflow/pipeline_schema.py`). That single declaration drives everything downstream —
implementation *and* public API derive from it, so they cannot diverge.

The step schema is a **tagged union**: which keys a step may carry depends on its `type`.
Universal keys sit in `properties`; each type's own keys sit in an `allOf` branch
discriminated on `type` (`if type == "llm" then {…}`). Plugin and registered step types are
*permissive* — `run_plugin_step` hands the whole step dict to the plugin as a flat config, so
their keys cannot be enumerated. Three derived views are the only supported way to read the
vocabulary: `allowed_step_keys(step_type)` (keys valid on that type, or `None` when
permissive), `common_step_keys()`, and `step_keys()` (the union).

- **Validation** — `PipelineConfig` (Pydantic, same module) validates a loaded pipeline
  against the schema before the runner executes it.
- **Linting** — the linter derives its allowed keys **per step type** from `PIPELINE_SCHEMA`
  via `allowed_step_keys()`, and keeps no key list of its own. This is what closes the
  silent-ignore hole: a key that is real but belongs to another type — `output_type:` on a
  `function` step, `size:` on an `llm` step — is read by no handler, and a global allowed-set
  accepted it with no error, no warning, and no effect. It is now a lint error.
- **The public object model** — `Pipeline` / `Step` (`model.py`) expose one attribute per
  schema key (the `${...}` you can point to in the YAML). `Step`'s attributes are
  **generated** from the schema at import time, so drift is impossible by construction. The
  model is deliberately flat and generic: it exposes the union of every type's keys, while
  *validation* is per-type. A key that does not apply to a step's type reads as `None`.
- **Testing** — two schema-*derived* guards, both using the schema as their oracle rather than
  a hard-coded list. `tests/test_pipeline_model.py` asserts the object model's attribute set
  matches the schema in both directions (no missing keys, no invented names).
  `tests/test_schema_covers_runner_keys.py` closes the other loop: every step key the engine
  actually reads must be declared in the schema — the check a key missing from *both* the
  schema and the model would otherwise hide, since absence from both looks like agreement. It
  scans `steps/`, `runner.py`, `plugins/`, `utils/` and `modules/`; handlers pass the step dict
  to helpers, so scanning only the handlers is what let the loader filter keys
  (`key`/`where`/`limit`/`offset`/`columns`/`xpath`/`namespaces`/`output_format`, read in
  `utils/data.py`) stay undeclared. (Both tests are *derived* from the schema; we don't
  code-generate test files.)
- **The API catalog** — `api_catalog()` (`catalog.py`) enumerates the *verbs* (the computed
  methods the schema can't describe) by introspection, complementing the schema's *nouns*.

The consequence: to change the language you change `PIPELINE_SCHEMA`, and validation, linting,
the object model, and the API move with it.

### One syntax per concept

The language admits exactly **one spelling** for each concept — no aliases. A second accepted
spelling is indistinguishable from a bug to anyone reading a pipeline, and the engine had four:

| Concept | Spelling | Retired |
|---|---|---|
| bind a step's result to context | `output` | `outputs` |
| format the response through a template | `template` | `format_with` |
| abandon a call after N seconds | `timeout_seconds` | `timeout` |
| loop modifiers | `group_by`, `order_by` | `group-by`, `order-by` (the only hyphenated keys in an otherwise underscored vocabulary) |

Retired spellings are **lint errors that name their replacement** (via `COMMON_TYPOS`), not
silent aliases. `tests/test_one_syntax.py` pins this.

### The editor schema

`src/llmflow/schema/pipeline.schema.json` is a **second** declaration of the vocabulary — a
draft-2020-12 schema with per-type `$defs`, wired by `.vscode/settings.json` to
`pipelines/**/*.yaml`. It drives autocomplete and inline validation, so it is the vocabulary a
pipeline author actually sees while typing, and it is not read by any Python code.

That makes it the one place drift is invisible to the guards above, so
`tests/test_one_syntax.py` asserts it declares no retired spelling and no key
`PIPELINE_SCHEMA` would reject. The reverse direction is deliberately not asserted — it may
lag on newly added keys — but it must never teach a key the engine rejects. Generating it from
`PIPELINE_SCHEMA` is the deeper fix and is not yet done.

## 17. Machine-Readable Semantics for Programs and LLMs

The language's semantics are published in machine-readable form so a program — or an LLM — can
read the language and compose the corresponding API calls mechanically, without re-parsing
pipeline YAML or hard-coding the vocabulary:

- **`llmflow.PIPELINE_SCHEMA`** — the *nouns*: every syntax key, as JSON Schema, per step type
  (§16). Attribute accessors on the object model map to these one-to-one, with a total naming
  rule (leaf key; a hyphen becomes an underscore, e.g. `group_by:` → `step.group_by`, and a
  Python keyword gets a trailing underscore, e.g. `for:` → `step.for_`). Because the schema is
  type-discriminated, a reader gets the *true* per-type grammar — not a flat list implying that
  `query_file` is meaningful on an `llm` step.
- **`llmflow.api_catalog()`** — the *verbs*: `{node, name, signature, doc}` for every computed
  method (`resolve`, `run`, `lint`, `schemas`, `saveas`, `render_prompt`, …), generated by
  introspection so it can't drift from the code.

Together these make the syntax↔API mapping a *total, mechanical isomorphism*: read a pipeline,
and the calls follow. `docs/python-api.md` documents the resulting surface for humans; the two
artifacts above are the same contract for machines.

This complements the other two channels by which a pipeline's meaning reaches a model:

- **Prompt contracts** (§5) — each `.gpt` prompt declares the inputs it requires, and the
  linter enforces they are available before a step runs, so an LLM never reasons from data that
  wasn't put in front of it.
- **MCP** (§10) — structured data is served to models through typed tools rather than flattened
  into prose, keeping the model's job interpretation rather than parsing.

## 18. AI Context Distribution (Consumer Repos)

`sp init` populates AI context in repos that *use* the engine, and keeps sp's evolving standard
separate from a repo's own material so neither pollutes the other:

- **`CLAUDE.md`** — sp owns a delimited `<!-- BEGIN/END llmflow-init -->` block (upserted on
  `sp init`); everything outside it is the repo's.
- **`AGENTS.md`-first** — the vendor-neutral cross-tool context file (read by Codex, Gemini CLI,
  Cursor, Copilot, and others); `CLAUDE.md` imports it. See `docs/ai-assistants.md`.
- **`docs/ai-context/`** — two lanes:
  - *sp-managed* (`index.md`, `overview.md`, `rules.md`, `github-workflow.md`) — generated and
    refreshed by `sp init --update`; not hand-edited.
  - *project-owned* (`project.md`) — created once, **never** overwritten, wired into `index.md`;
    a repo's own project-specific context lives here.
- **`~/.sp/`** — machine-global conventions, skills, and user-context shared across all projects
  on the machine.

The managed/owned split — a delimited block for `CLAUDE.md`, a create-once `project.md` for
`docs/ai-context/` — is the pattern that lets sp update its context without touching yours. See
`docs/consumer-repo-layout.md`.
