# Design: LLMFlow Pipeline JSON Schema and Schema-Driven Runner

## Problem

LLMFlow is a declarative pipeline language. But its language definition is not itself declarative — it lives in imperative Python scattered across `runner.py` (what is dispatched), `linter.py` (what is validated), and several Markdown files (what is described). These three sources can and do drift. There is no single artifact that says: "here is the language, completely and authoritatively."

The consequence is ad-hoc growth. Each new step type adds code to the runner, adds conditions to the linter, and optionally adds prose to the language reference — with no formal relationship between them. This is how odd hack languages develop over time: the real definition is the implementation, not the specification.

The runner compounds this problem. Its core is a large `elif` chain — one branch per step type — where field resolution, validation, execution, and output binding are all interleaved by hand. Adding a step type means touching the runner in multiple places. Debugging means reading Python to understand what the pipeline is supposed to do.

## Goal

Define the LLMFlow pipeline language formally, once, in a machine-readable schema. The schema is not just a specification artifact — it is an **executable specification**. The runner reads the schema at startup and uses it to dispatch, validate, resolve, and bind every step. Adding a new step type means adding a schema entry and a handler function. The runner itself does not change.

---

## Chosen Format: JSON Schema (Draft 2020-12)

**Why JSON Schema:**

- Industry standard — editors already know how to use it
- VS Code YAML extension (`redhat.vscode-yaml`) reads `$schema` references and provides live autocompletion and inline error highlighting with zero additional tooling
- Can be submitted to [SchemaStore](https://www.schemastore.org/) so any editor gets autocompletion without configuration
- Can generate documentation (e.g. `json-schema-for-humans`)
- Supports discriminated unions via `if/then/else` or `oneOf` — exactly what we need to type-check individual step types

**Schema location:** `src/llmflow/schema/pipeline.schema.json`

**Pipeline YAML files** will reference the schema via a comment or via VS Code workspace settings:
```yaml
# yaml-language-server: $schema=../../src/llmflow/schema/pipeline.schema.json
name: my-pipeline
steps: ...
```

---

## Schema Structure

### Top-level pipeline object

```
Pipeline
  name:           string (required)
  description:    string (optional)
  variables:      map of string → string (optional)
  llm_config:     LlmConfig (optional)
  linter_config:  LinterConfig (optional)
  steps:          array of Step (required, min 1)
```

### Common step fields (`$defs/CommonStep`)

Every step, regardless of type, supports these fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | Unique within pipeline |
| `type` | string | yes | Discriminates step variant |
| `condition` | string | no | `${var}` expression; step skipped if falsy |
| `saveas` | string or SaveasConfig | no | Write output to disk |
| `append_to` | string | no | Accumulate into a list variable |
| `log` | enum: debug/info/warning/error | no | Per-step log level |
| `retry` | RetryConfig | no | Re-run on short/long/invalid responses |

### Step type registry

Each step type is a `$def` that `allOf`s `CommonStep` and adds its own required/optional fields. The `type` field value is a `const` that discriminates the variant.

| Step type | Status | Notes |
|-----------|--------|-------|
| `llm` | core | LLM call via `llm` package |
| `function` | core | Python function call |
| `for-each` | core | Iteration over a list |
| `if` | core | Conditional block |
| `json` | core | Assemble a JSON value from context |
| `save` | core | Write content to disk |
| `load_json` | core | Load JSON file into context |
| `load_yaml` | core | Load YAML file into context |
| `load_xml` | core | Load XML file into context (lxml) |
| `load_csv` | core | Load CSV into `list[dict]` |
| `load_tsv` | core | Load TSV into `list[dict]` |
| `load_text` | core | Load text/Markdown file into context |
| `load_directory` | core | Glob directory into a list |
| `basex` | core | XQuery against a BaseX database |
| `window` | core | Sliding/tumbling window over a list |
| `duckdb` | core | SQL query via DuckDB |
| `xpath` | plugin | XPath extraction from XML |
| `tsv` | plugin | TSV reader (legacy plugin; prefer `load_tsv`) |
| `xslt` | plugin | XSLT transform |

Plugin step types (`xpath`, `tsv`, `xslt`, and user-installed plugins) cannot be exhaustively enumerated in the schema, but their common shape can be described with `additionalProperties: true` and a note.

### Key step schemas (fields)

**`llm`**
```
prompt:
  file:    string (path to .gpt file) — required unless inline
  inputs:  map of string → string
model:          string
outputs:        string or array of string (required)
output_type:    enum: json
response_format: ResponseFormatConfig
max_tokens:     integer
temperature:    number 0–2
timeout_seconds: integer
```

**`function`**
```
function:  string (dotted module path, required)
inputs:    map of string → any
outputs:   string or array of string
```

**`for-each`**
```
input:    string (context var resolving to a list, required)
as:       string (loop variable name, required)
steps:    array of Step (required)
```

**`if`**
```
condition: string (required)
steps:     array of Step (required)
else:      array of Step (optional)
```

**`json`**
```
value:   any (required) — supports ${var} in strings
output:  string (required)
```

**`save`**
```
content: string (required)
path:    string (required)
```

**`load_json` / `load_yaml` / `load_xml` / `load_text`**
```
path:    string (required)
output:  string (required, or outputs)
```

**`load_csv` / `load_tsv`**
```
path:      string (required)
output:    string (required, or outputs)
delimiter: string (optional, default "," for csv, "\t" for tsv)
```

**`load_directory`**
```
path:    string (required)
pattern: string (required, glob)
format:  enum: json|yaml|xml|csv|tsv|text (required)
output:  string (required, or outputs)
```

**`basex`**
```
query_file: string — path to .xq file (one of query_file or query required)
query:      string — inline XQuery
params:     map of string → string
timeout:    integer (default 120)
outputs:    string or array of string (required)
saveas:     string (optional)
```

**`window`**
```
input:  string (context var, required)
size:   integer (required)
stride: integer (optional, default = size)
as:     string (window variable name, required)
steps:  array of Step (required)
```

**`duckdb`**
```
query:   string (required, SQL)
inputs:  map of string → string (context vars to register as tables)
outputs: string or array of string (required)
```

### Supporting $defs

**`LlmConfig`**
```
model:             string
max_tokens:        integer
temperature:       number
timeout_seconds:   integer
```

**`LinterConfig`**
```
warnings_as_errors: boolean
```

**`SaveasConfig`** (when `saveas` is an object)
```
path:     string (required)
format:   enum: json|yaml|text|markdown
encoding: string (default utf-8)
```

**`RetryConfig`**
```
max_attempts:  integer (default 3)
min_length:    integer
max_length:    integer
must_contain:  string or array of string
backoff_seconds: number
```

**`ResponseFormatConfig`** (OpenAI structured output)
```
type: enum: json_schema|json_object
json_schema:
  name:   string
  strict: boolean
  schema: object (JSON Schema)
```

---

## Schema-Driven Runtime Execution

### The core idea

Each step type definition in the schema carries `x-` annotations that tell the runner exactly how to execute it. JSON Schema allows custom keywords with an `x-` prefix; they are ignored by validators but readable by any tool that knows to look for them.

```json
{
  "$defs": {
    "LoadJsonStep": {
      "x-handler": "llmflow.steps.loaders.run_load_json",
      "x-resolve-fields": ["path"],
      "x-output-field": "output",
      "x-output-mode": "single",
      "properties": {
        "type":   { "const": "load_json" },
        "path":   { "type": "string", "description": "File path; supports ${var} substitution" },
        "output": { "type": "string", "description": "Context variable to store the result" }
      },
      "required": ["type", "path", "output"]
    }
  }
}
```

### Runtime annotations

| Annotation | Purpose |
|------------|---------|
| `x-handler` | Dotted Python path to the execution function |
| `x-resolve-fields` | Fields to run through `${var}` substitution before calling the handler |
| `x-output-field` | Which field names the output variable (`output`, `outputs`, or both) |
| `x-output-mode` | `single` (one var), `list` (multiple vars), `append` (accumulate) |
| `x-resolve-inputs-map` | For steps where `inputs:` is a map of name→expression, resolve each value |
| `x-nested-steps` | Field(s) containing nested step arrays (for `for-each`, `if`, `window`) |
| `x-condition-field` | Field holding a condition expression that may skip execution |

### Handler function contract

Handlers become pure functions. The runner resolves all declared fields before calling them; handlers receive clean, resolved values and return a result:

```python
def run_load_json(path: str, step: dict, context: dict) -> Any:
    """Load and return the parsed contents of a JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))
```

The runner handles:
- Field resolution (`${var}` substitution)
- Schema validation of the step
- Calling the handler
- Storing the return value in context under the declared output variable
- `saveas`, `append_to`, `condition`, telemetry, logging — all common cross-cutting concerns

Handlers handle only their own business logic. They do not touch the context directly.

### Generic runner loop

```python
def execute_step(step: dict, context: dict, schema: dict) -> None:
    step_type = step["type"]
    defn = schema["$defs"][step_type_to_def_name(step_type)]

    # 1. Validate step against its schema fragment
    validate(step, defn)

    # 2. Check condition (skip if falsy)
    if not evaluate_condition(step.get("condition"), context):
        return

    # 3. Resolve declared fields
    resolved = resolve_fields(step, defn["x-resolve-fields"], context)
    if defn.get("x-resolve-inputs-map"):
        resolved["inputs"] = resolve_map(step.get("inputs", {}), context)

    # 4. Call handler
    handler = import_handler(defn["x-handler"])
    result = handler(**resolved, step=step, context=context)

    # 5. Bind output
    bind_output(result, step, defn, context)

    # 6. saveas, append_to, telemetry — common for all steps
    handle_saveas(step, result, context)
    handle_append_to(step, result, context)
```

### What stays in the runner vs. what moves to the schema

**Stays in runner (generic, applies to all steps):**
- Field resolution loop
- Condition evaluation
- Output binding
- `saveas` / `append_to` handling
- Telemetry start/stop
- Error handling and retry

**Moves to schema (per-step-type declaration):**
- Which fields exist and their types
- Which fields get `${var}` resolution
- Which field names the output
- Which handler to call

**Moves to handler functions (pure execution logic):**
- The actual work: LLM calls, file I/O, SQL queries, function dispatch
- Step-type-specific validation that JSON Schema cannot express

### Adding a new step type

Before this design:
1. Add `elif step_type == "new_thing":` block to runner (interleaved with all other logic)
2. Add validation conditions to linter
3. Update language docs manually

After this design:
1. Add entry to `pipeline.schema.json` with `x-` annotations
2. Write a handler function in `llmflow/steps/new_thing.py`
3. Docs are generated from the schema automatically

---

## Step Semantics — A Formal Description Language

The `x-` dispatch annotations tell the runner *how* to execute a step. A separate `x-semantics` annotation tells the system *what* a step *means* — how it transforms the pipeline context, what kind of effects it produces, and whether it can be safely replayed.

This is a small, closed vocabulary. It is not Turing-complete. Its job is to make the operational behavior of every step type formally stated and machine-readable.

### The four semantic dimensions

#### 1. Flow — control structure

How many times does this step execute, and over what?

| Value | Meaning |
|-------|---------|
| `once` | Executes exactly once (most steps) |
| `foreach(over, as)` | Executes once per element of the list in `over`, binding each to `as` |
| `window(over, size, stride, as)` | Executes once per window of the list in `over` |
| `conditional(condition)` | Executes zero or one times depending on `condition` |

#### 2. Effect — I/O character

What does this step do outside the pipeline context?

| Value | Meaning |
|-------|---------|
| `pure` | No I/O; result is fully determined by context inputs |
| `file-read` | Reads from the filesystem |
| `file-write` | Writes to the filesystem |
| `llm` | Makes an LLM API call (non-deterministic, has cost) |
| `db` | Issues a database query (BaseX, DuckDB) |
| `function` | Calls arbitrary Python (effects unknown to the schema) |
| `contains-steps` | Effect is determined by its nested steps |

#### 3. Context — reads and writes

What does this step consume from the pipeline context, and what does it produce?

```
reads:  [list of field names or "inputs.*" for map inputs]
writes: [variable name(s) bound after execution]
write-mode: single | list | append
```

`reads` entries correspond to resolved fields — values that come from the context via `${var}` substitution. `writes` is the variable name taken from the step's output field. `write-mode` is:
- `single` — writes one scalar value
- `list` — writes a list value
- `append` — appends to an existing list (`append_to` pattern)

#### 4. Idempotent — replay safety

Can this step be safely re-run without unintended side effects?

| Value | Meaning |
|-------|---------|
| `true` | Re-running produces the same result; no durable side effects |
| `false` | Re-running may produce a different result or incur costs (LLM calls) |
| `depends` | Idempotency depends on the nested steps (for `for-each`, `if`) |

This drives resume and checkpoint logic: non-idempotent steps should declare `saveas` so the runner can skip them on replay.

---

### Semantic table — all core step types

| Step type | flow | effect | reads | writes | write-mode | idempotent |
|-----------|------|--------|-------|--------|------------|------------|
| `llm` | once | llm | inputs.* | outputs | single | false |
| `function` | once | function | inputs.* | outputs | single | unknown |
| `for-each` | foreach(in, for) | contains-steps | in | append_to? | append | depends |
| `window` | window(in, size, stride, for) | contains-steps | in | append_to? | append | depends |
| `if` | conditional(condition) | contains-steps | condition | — | — | depends |
| `json` | once | pure | value | output | single | true |
| `save` | once | file-write | content, path | — | — | true |
| `load_json` | once | file-read | path | output | single | true |
| `load_yaml` | once | file-read | path | output | single | true |
| `load_xml` | once | file-read | path | output | single | true |
| `load_csv` | once | file-read | path | output | list | true |
| `load_tsv` | once | file-read | path | output | list | true |
| `load_text` | once | file-read | path | output | single | true |
| `load_directory` | once | file-read | path | output | list | true |
| `basex` | once | db | params.* | outputs | single | true |
| `duckdb` | once | db | inputs.* | outputs | single | true |

---

### Schema annotation

In the JSON Schema, `x-semantics` sits alongside `x-handler`:

```json
{
  "$defs": {
    "LlmStep": {
      "x-handler": "llmflow.steps.llm.execute",
      "x-resolve-fields": ["model", "max_tokens", "temperature"],
      "x-resolve-inputs-map": true,
      "x-output-field": "outputs",
      "x-semantics": {
        "flow": "once",
        "effect": "llm",
        "reads": ["inputs.*"],
        "writes": "outputs",
        "write-mode": "single",
        "idempotent": false
      },
      "properties": { ... }
    },
    "ForEachStep": {
      "x-handler": "llmflow.steps.control.execute_foreach",
      "x-nested-steps": "steps",
      "x-semantics": {
        "flow": { "type": "foreach", "in": "in", "for": "for" },
        "effect": "contains-steps",
        "reads": ["in"],
        "writes": "append_to",
        "write-mode": "append",
        "idempotent": "depends"
      },
      "properties": { ... }
    },
    "LoadJsonStep": {
      "x-handler": "llmflow.steps.loaders.run_load_json",
      "x-resolve-fields": ["path"],
      "x-output-field": "output",
      "x-semantics": {
        "flow": "once",
        "effect": "file-read",
        "reads": ["path"],
        "writes": "output",
        "write-mode": "single",
        "idempotent": true
      },
      "properties": { ... }
    }
  }
}
```

---

### What the runtime can derive from semantics

#### Static analysis (linter)

- **Unresolved reads**: if step B reads a variable that no prior step writes and it is not declared in `variables:`, flag it.
- **Missing saveas on non-idempotent steps**: if a step has `idempotent: false` and no `saveas`, warn — it cannot be resumed.
- **Dead writes**: if a step writes a variable that no subsequent step reads and it has no `saveas`, warn (likely a bug).
- **Effect summary**: report how many LLM calls, file reads, and file writes a pipeline will perform — shown on `sp lint` and `sp run --dry-run`.

#### Dry-run

With semantics declared, a dry-run can trace the full pipeline execution symbolically — showing which variables are written at each step, which LLM calls would be made, and which files would be read or written — without invoking any handler.

#### Resume / checkpointing

The runner already supports `saveas`-based resume. With `idempotent` declared in the schema, it can:
- Automatically skip `idempotent: true` steps whose declared output already exists in context (re-derive from source rather than needing a checkpoint)
- Require `saveas` on `idempotent: false` steps that appear before any resumable boundary

#### Future: parallel execution

Steps whose `reads` and `writes` sets are disjoint and whose effects are both `file-read` or `pure` have no data dependency and no shared side effects. The runner could execute them concurrently. The semantics make this analysis possible without inspecting handler code.

---

## Integration Points

### 1. VS Code autocompletion (immediate value)

Add to `.vscode/settings.json`:
```json
{
  "yaml.schemas": {
    "./src/llmflow/schema/pipeline.schema.json": "pipelines/**/*.yaml"
  }
}
```

This gives all pipeline YAML files live field completion, unknown-field warnings, and required-field errors in the editor.

### 2. Linter migration (medium term)

`linter.py` currently encodes field requirements as Python conditionals. After the schema exists, the linter should:
1. Validate the pipeline against the JSON Schema first (using `jsonschema` package)
2. Layer semantic rules on top (things JSON Schema cannot express: "if `type: function`, the `function` key must resolve to an importable path"; "all `${vars}` in prompt inputs must be declared")

This replaces the ad-hoc field checks while retaining the semantic checks that require execution context.

### 3. Reference documentation (medium term)

A script (`tools/generate_schema_docs.py`) renders the schema into a Markdown reference table — one section per step type, all fields, types, and defaults. This becomes `docs/llmflow-step-reference.md` and replaces the hand-maintained sections in `docs/llmflow-language.md`.

### 4. SchemaStore submission (later)

Once stable, submit to [SchemaStore](https://www.schemastore.org/json/) so that any editor (JetBrains, Neovim, etc.) automatically associates `*.yaml` files containing LLMFlow pipeline structure with the schema.

---

## Language Inconsistencies Exposed by Formal Semantics

Formalizing the schema surfaces inconsistencies in the language as it currently exists. These should be resolved before the schema is written, not after — fixing them post-schema means breaking changes to pipeline YAML files already in use.

### 1. `output` vs `outputs` — singular vs plural ✅ DECIDED

**Decision: standardize on `output` (singular) everywhere.**

A step produces one result, even if that result is a list. The plural `outputs` was inherited informally and has no semantic justification. The runner will continue to accept `outputs` as a deprecated alias during a transition period; `sp lint` will warn on its use.

> **IMPLEMENTED 2026-08-13 (0.2.1.23), with one change: no alias.** `outputs` is a **lint error
> naming `output`**, not a deprecated alias — one syntax per concept, since a second accepted
> spelling reads as a bug. All ~1,100 sites across 15 repos were migrated in the same window
> rather than over a transition period. Pinned by `tests/test_one_syntax.py`; see
> `project/plans/design-schema-single-source.md`.
>
> Note for future sessions: this ruling was nearly reversed because a later design note proposed
> `outputs` as canonical without checking here first. Search this file's "Language
> Inconsistencies" section before changing keyword vocabulary.

### 2. `input` / `as` vs XQuery-aligned `for` / `in` ✅ DECIDED

**Decision: adopt `for:` / `in:` aligned with XQuery syntax, for both `for-each` and `window`.**

XQuery uses `for ... in` as the universal iteration construct — for regular iteration and for both tumbling and sliding windows:

```xquery
for $scene in $scene_list                          (regular)
for tumbling window $w in $items start … end …     (windowed)
for sliding window $w in $items start … end …      (sliding)
```

LLMFlow matches this with `for:`/`in:` on both step types:

```yaml
- type: for-each          - type: window
  for: scene                for: window_batch
  in: "${scene_list}"       in: "${scene_list}"
  steps:                    size: 3
    - ...                   stride: 1
                            steps:
                              - ...
```

Reads as: *for scene in scene_list* / *for window_batch in scene_list* — identical pattern to XQuery, without the `$`. The existing `input:` and `as:` fields are accepted as deprecated aliases during transition.

**Window semantics — fixed start, dynamic end:**

The `window` step has a specific semantic that is not fully captured by `size`/`stride` alone:

- **Start is fixed** — each window begins at a defined position (determined by the stride from the previous window's start).
- **End is not always known in advance** — a step inside the window can emit `!window_advance` to signal "the boundary is here; start the next window from this point." The window ends when that signal is received, not at a fixed size.

This is the correct model: the pipeline processes the window and discovers the boundary during processing. `!window_advance` is the current mechanism for that signal. In XQuery terms, this corresponds to `end … when` — a condition evaluated during processing — but LLMFlow's model is simpler: any step inside the window can trigger advancement rather than requiring a declarative condition expression.

This semantic must be captured in the schema's `x-semantics` annotation for `window` and documented in the step reference. The `for`/`in` field naming decision is independent of this design.

### 3. Three patterns for "resolve context values into a step" ✅ DECIDED

**Decision: two patterns, clearly distinguished. Rename `basex` `params:` to `inputs:`.**

The language has — and should retain — exactly two patterns for passing context values into a step:

| Pattern | Used by | Rule |
|---------|---------|------|
| Named top-level fields | `load_json` (`path:`), `save` (`content:`, `path:`) | The schema declares these fields by name. They are fixed for the step type. |
| `inputs:` map | `function`, `llm`, `basex`, `duckdb` | User-defined name→`${expression}` pairs. The step type does not know the key names in advance. |

`basex` currently uses `params:` for what is structurally identical to `inputs:`. **Rename `params:` to `inputs:`** for consistency. The old `params:` is accepted as a deprecated alias during transition.

**The rule, stated explicitly:** use named top-level fields when the schema knows the field names (they are part of the step type definition); use `inputs:` when the names are chosen by the pipeline author (they are passed through to a function, query, or prompt).

**Testing benefit:** consistent `inputs:` shape means handler functions can be unit-tested with a plain dict — no pipeline context, no runner, no YAML parsing. The schema-driven runner resolves `inputs:` to a flat dict before calling the handler, so tests call handlers directly with the same dict the runner would produce. One test fixture shape covers all `inputs:`-bearing step types.

### 4. `save` step vs `saveas` cross-cutting field ✅ DECIDED

**Decision: keep both; document the rule explicitly.**

- Use `type: save` when writing to disk *is the step* — a terminal action with no output variable.
- Use `saveas:` on any other step when writing to disk is a side effect alongside storing a result in context.

The rule in one sentence: `save` when the write is the whole point; `saveas` when you also need the value downstream.

### 5. `condition:` collision between step type and cross-cutting field ✅ DECIDED

**Decision: accept as intentional symmetry; document clearly. No rename.**

Both uses share the same semantics: evaluate the expression; if falsy, do not execute. The scopes are unambiguous syntactically — `condition:` inside an `if` step gates a nested block; `condition:` on any other step is a per-step skip guard. Renaming the per-step field would break existing pipelines for a minor readability gain.

### 6. `tsv` plugin vs `load_tsv` step type ✅ DECIDED

**Decision: bring `load_tsv` (and `load_csv`) to full parity, then deprecate the plugin.**

`load_tsv` and `load_csv` now support `where:`, `limit:`, `offset:`, and `columns:` — the full filtering capability of the `tsv` plugin. The plugin is simplified to a thin wrapper around the shared `apply_tabular_filters()` helper and remains for backwards compatibility. New pipelines should use the step types.

---

### Resolution before schema implementation

Items 1–3 affect the `x-output-field` and `x-resolve-fields` annotations on every step type and must be decided before the schema is written. Items 4–6 can be documented as intentional without schema impact, but should be resolved before the language reference is regenerated from the schema.

---

## What the Schema Does Not Cover

- **Prompt contract format** — the `requires:`/`optional:` frontmatter in `.gpt` files. This is a separate schema (`prompt.schema.json`) and a separate workstream.
- **Semantic validation** — the schema can say `path` must be a string; it cannot say the path must resolve to an existing file at lint time. The linter retains that responsibility.
- **Plugin step types** — user-installed plugins add step types the schema cannot enumerate. The schema will describe plugin steps loosely (required `name`, required `type` matching a registered plugin name, any additional fields permitted).

---

## Implementation Plan

### Phase 1 — Schema (foundation)
1. **Write `src/llmflow/schema/pipeline.schema.json`** — all core step types, all fields with `description`, all `x-` runtime annotations.
2. **Add `.vscode/settings.json`** — wire schema to `pipelines/**/*.yaml` for immediate editor autocompletion.
3. **Validate existing pipelines against the schema** — surface any gaps between the schema and real usage before the runtime depends on it.

### Phase 2 — Schema-driven runner
4. **Extract handler functions** — move each step type's execution logic out of the `elif` chain in `runner.py` into dedicated modules under `src/llmflow/steps/` (e.g. `steps/llm.py`, `steps/loaders.py`, `steps/control.py`).
5. **Write the generic execution loop** — `execute_step()` that reads `x-` annotations, resolves fields, calls handlers, binds outputs. Cross-cutting concerns (condition, saveas, append_to, telemetry, retry) live here once.
6. **Migrate step types one at a time** — start with the simplest (`load_json`, `json`, `save`), validate against existing tests, then move to complex ones (`llm`, `for-each`, `if`). The old `elif` chain shrinks to zero.

### Phase 3 — Linter and docs
7. **Migrate linter** — replace ad-hoc field checks with JSON Schema validation via `jsonschema` package; add semantic analysis (dependency ordering, missing saveas on non-idempotent steps, dead writes, effect summary).
8. **Write `tools/generate_schema_docs.py`** — render schema + semantics to `docs/llmflow-step-reference.md`; this becomes the authoritative reference, generated not hand-maintained.
9. **Submit to SchemaStore** (post-stabilization).

Phase 1 can ship alone and delivers immediate value (editor tooling). Phases 2 and 3 follow in order.

### Testing benefit of the schema-driven approach

Because the runner resolves all declared fields before calling a handler, handler functions become trivially testable in isolation:

```python
# Before: testing run_basex_step requires a full pipeline context and step dict
def test_basex(tmp_path):
    step = {"name": "s", "type": "basex", "query": "//verse", "params": {...}, "outputs": "result"}
    context = {"passage": "Mark 1"}
    run_basex_step(step, context)
    assert context["result"] == ...

# After: handler receives already-resolved inputs, returns a value
def test_basex_handler():
    result = execute_basex(query="//verse", inputs={"passage": "Mark 1"})
    assert result == ...
```

This also makes it possible to generate test cases from the schema: for each step type, the schema declares which fields are required — a test generator can produce a minimal valid input dict and verify the handler accepts it, and a missing-field dict and verify it raises.

### Semantic vocabulary stability

The semantic vocabulary (`flow`, `effect`, `reads`, `writes`, `write-mode`, `idempotent`) should be treated as a stable interface once Phase 2 ships. Changes to the vocabulary require updating every step type definition. Additions (new `effect` values, new `flow` types) are backward-compatible; removals are breaking.
