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
7. **Migrate linter** — replace ad-hoc field checks with JSON Schema validation via `jsonschema` package; retain semantic checks (path existence, variable references, prompt contracts).
8. **Write `tools/generate_schema_docs.py`** — render schema to `docs/llmflow-step-reference.md`; this becomes the authoritative reference.
9. **Submit to SchemaStore** (post-stabilization).

Phase 1 can ship alone and delivers immediate value (editor tooling). Phases 2 and 3 follow in order.
