# Python API

LLMFlow's supported Python API is the top-level `llmflow` namespace. Everything listed in
`llmflow.__all__` is a stable, documented surface for programs that embed the engine.
Anything reached through `llmflow.*` submodules is internal and may change without notice.

**Principle.** Each public function is backed by the *same* code the engine runs — never a
parallel reimplementation — so a program using the API sees exactly what a real run sees.
Consumers should never re-parse pipeline YAML to re-derive what the engine already
resolves; that copy inevitably drifts. If you find yourself reaching into `llmflow.*`
internals or re-reading a pipeline file, that is a gap in this surface worth reporting.

## The object model — `load_pipeline()`

`load_pipeline(path)` returns a `Pipeline` whose attributes mirror the pipeline YAML 1:1,
so the calls are guessable directly from the syntax. Attributes are the declared keys
(raw); computations are methods.

```python
from llmflow import load_pipeline

p = load_pipeline("pipelines/build-book.yaml")   # -> Pipeline
p.name
p.variables                       # declared {...}
p.output_file_directory           # declared, raw "${base}/out"
p.steps[0].saveas                 # == the YAML path steps[0].saveas
p.steps[0].steps                  # nested steps (for-each / if)
```

Reserved words get a trailing underscore: `for:` → `step.for_`, `in:` → `step.in_`.

### `Pipeline.resolve(vars=None) -> ResolvedPipeline`

Resolution expands `${...}` and applies `--var`, so it is a method whose result is a
same-shaped view with resolved attributes — directory keys as `Path`:

```python
r = p.resolve()                                   # defaults
r.output_file_directory                           # Path("outputs/out")  (${base} expanded)
r.variables["book_dir"]                           # derived vars resolved transitively

# Honor the same overrides `sp run --var` would apply:
r = p.resolve(vars={"output_file_directory": "acceptance/out"})
r.output_file_directory                           # Path("acceptance/out")
```

Precedence, low to high: root-level directory keys → the pipeline's `variables:` block →
`vars` (which win). Directory keys the pipeline does not declare come back as `None`.

`resolve()` uses the engine's own context builder and resolver, so the result matches a
real run — replacing the pattern of re-parsing a pipeline YAML in consumer code (a copy
that drifts: misses `--var`, hard-pins one pipeline, invents non-YAML constants).
