# Python API

LLMFlow's supported Python API is the top-level `llmflow` namespace. Everything listed in
`llmflow.__all__` is a stable, documented surface for programs that embed the engine.
Anything reached through `llmflow.*` submodules is internal and may change without notice.

**Principle.** Each public function is backed by the *same* code the engine runs — never a
parallel reimplementation — so a program using the API sees exactly what a real run sees.
Consumers should never re-parse pipeline YAML to re-derive what the engine already
resolves; that copy inevitably drifts. If you find yourself reaching into `llmflow.*`
internals or re-reading a pipeline file, that is a gap in this surface worth reporting.

## `resolve_pipeline_paths(pipeline_file, vars=None) -> ResolvedPipelinePaths`

Resolve a pipeline's directories and variables from *outside* a run, with the same
precedence and `${...}` expansion a real run uses.

```python
from llmflow import resolve_pipeline_paths

paths = resolve_pipeline_paths("pipelines/build-book.yaml")
paths.intermediate_file_directory   # pathlib.Path | None
paths.output_file_directory         # pathlib.Path | None
paths.variables                     # dict[str, Any], resolved

# Honor the same overrides `sp run --var` would apply:
acc = resolve_pipeline_paths(
    "pipelines/build-book.yaml",
    vars={"output_file_directory": "acceptance/out"},
)
```

Precedence, low to high: root-level directory keys → the pipeline's `variables:` block →
`vars` (which win). Directory keys the pipeline does not declare come back as `None`.

This replaces the pattern of opening a pipeline YAML in consumer code and re-deriving
paths by hand — a copy that inevitably drifts from the engine (misses `--var`, hard-pins
one pipeline, invents non-YAML constants).

### `ResolvedPipelinePaths`

A dataclass with three fields:

| Field | Type | Notes |
|-------|------|-------|
| `intermediate_file_directory` | `Path \| None` | Resolved; `None` if not declared. |
| `output_file_directory` | `Path \| None` | Resolved; `None` if not declared. |
| `variables` | `dict[str, Any]` | The pipeline's `variables:` block, resolved. |
