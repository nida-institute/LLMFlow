# Design: LLMFlow Public Python API — an object model that mirrors the pipeline

**Status:** Implemented — historical record. Describes why the code looks as it does; do not rebuild from it. Verify against the code before relying on any detail.

Shipped in `model.py` — `Pipeline`, `ResolvedPipeline`, `Step`, `load_pipeline()` — and
documented in `docs/python-api.md`. The previous status said "No code until the Captain
approves"; that approval was given and the code exists.

gives the go-ahead to implement.**
**Tracks:** epic #187 (Public Python API). Supersedes the flat-function candidate list.
**Reframes:** #186 (shipped `resolve_pipeline_paths`, unreleased) is replaced by this model.

---

## Governing principle (Decision 1 — binding)

> **A program can map pipeline syntax to API calls mechanically, both directions.**

Not merely "a human can guess the call" — a *total, mechanical isomorphism*: pipeline YAML ⇄
API calls, traversable with zero human judgment. A smart Python program (or an agent) can
read a pipeline and compose the equivalent API calls directly from the syntax; you could
transpile a pipeline to equivalent Python.

This is binding, not aspirational. Its consequence is discipline: **no clever or semantic
names, ever** — every accessor name is forced by the schema. (`predicted_outputs` stays
dead: it named a purpose, not the `saveas:` key.) Any rule that would require judgment
("depending", "unless ambiguous", "documented case") is disqualified — every rule must be
total.

It auto-locks three things as *total* rules:

- **Attribute vs. method** (below) — mechanical, from the schema.
- **Reserved words** — append `_` to *any* Python keyword: `in`→`in_`, `for`→`for_`. No
  case-by-case.
- **Naming** — the attribute is the **leaf** schema key (`s.saveas`), always. Path-
  qualification is permitted only where the schema makes a collision *impossible*, so the
  rule stays total.

## The idea in one sentence

A pipeline YAML is an object tree (`pipeline → steps → step → saveas`); the public API is an
object graph of the **same shape**. `step.saveas` is not *like* the YAML path
`steps[i].saveas` — it **is** it.

## Why this, not flat functions

#186 shipped a flat accessor (`resolve_pipeline_paths(p)`), and #187's first draft continued
that shape (`pipeline_saveas(p)`, …). Flat functions don't mirror structure, so their names
are *invented* rather than *read off the document* — and invented names drift (the
`predicted_outputs` misfire). An object graph removes the invention: the accessor name is the
syntax key at that node, and the nesting is the pipeline's nesting.

## The object model

```python
from llmflow import load_pipeline

p = load_pipeline("pipelines/build-book.yaml")   # -> Pipeline

# attributes = keys declared in the YAML
p.name
p.description
p.variables                 # declared {...}
p.output_file_directory     # declared, raw "${base}/out"
p.steps                     # [Step, Step, ...]

s = p.steps[0]              # -> Step
s.type                      # "llm"
s.prompt
s.inputs
s.saveas                    # declared saveas spec
s.steps                     # nested Steps (for-each / if) — nesting mirrors YAML
```

### The one rule: attribute vs. method

> **If you can point to it in the YAML, it's an attribute. If the engine has to compute it,
> it's a method (with `()`).**

| `object.attribute` — stored in the YAML | `object.method()` — computed by the engine |
|---|---|
| `p.name`, `p.description` | `p.resolve(vars=...)` — expand `${...}`, apply `--var` |
| `p.variables` (declared) | `p.run(vars=..., dry_run=...)` |
| `p.output_file_directory` (raw) | `p.lint(vars=...)` |
| `p.steps` | `p.schemas()` — derived across json steps |
| `s.type`, `s.prompt`, `s.inputs`, `s.saveas`, `s.condition` | `s.render_prompt(context)` |

A program classifies every node with this rule alone: schema keys → attributes; the fixed,
published verb set → methods.

### Resolution is a method → resolved values live on its result

Resolution needs `--var` and expands `${...}`, so it is a computation. `.resolve()` returns a
**same-shaped view** whose attributes are resolved:

```python
p.output_file_directory                    # "${base}/out"          (declared)
p.resolve().output_file_directory          # Path("outputs/out")    (resolved, defaults)
p.resolve(vars={"output_file_directory": "acc/out"}).output_file_directory   # Path("acc/out")
p.resolve(vars=...).steps[0].saveas        # resolved; group_by_prefix flagged runtime-dependent
```

Honesty by construction: *declared* values hang off `Pipeline`/`Step`; *resolved* values hang
off `.resolve()`. "What files will actually be written" is a runtime question
(`group_by_prefix` depends on runtime filenames) and is surfaced as such — never a static
attribute pretending certainty.

## The published mapping is a first-class artifact (Decision 2)

For a program to compose calls, the mapping is a **published, machine-readable spec**, not
prose:

- **`PIPELINE_SCHEMA`** (`llmflow/pipeline_schema.py`) becomes a **public, versioned export**.
  It already enumerates every syntax key and is already the linter's allowed-key source. The
  attribute half of the API is *derivable* from it + the total rules above, so a smart program
  needs nothing more for attributes.
- **A versioned method catalog** — the verbs (`resolve`, `run`, `lint`, `schemas`,
  `render_prompt`, …) with signatures and which node each attaches to. This is the half the
  schema *cannot* describe (the schema is syntax, not verbs), so it must be published
  explicitly and treated as first-class, not left to docstrings.
- **Deferred:** a fully-materialized JSON manifest enumerating every accessor (attribute paths
  + method signatures). It is only a generated projection of schema + catalog, so it can be
  added the moment a consumer wants the fully-explicit form.

## Staying in lockstep with the schema (Decision 3 — hand-write + drift test)

The `Pipeline`/`Step` classes are **hand-written**, thin, richly typed, and docstring'd — not
generated. They are kept honest by a **drift test**: every `PIPELINE_SCHEMA` property has a
matching attribute and vice-versa; a schema change that isn't mirrored fails CI.

The commitment that makes hand-writing safe: **`PIPELINE_SCHEMA` + the method catalog is the
one oracle.** The classes and any future JSON manifest are *both* projections validated against
that oracle by the drift test. Hand-written never means "may silently disagree."

(Codegen was considered and rejected: machine-composability is about the *consumer* reading
our published mapping, not about *our* classes being generated. Hand-written buys readability,
real type signatures, and inline docs that a generated surface fights.)

## Prerequisites to close first

- **Schema gap:** `intermediate_file_directory` / `output_file_directory` are **not** in
  `PIPELINE_SCHEMA`'s top-level `properties` — they pass through as `additionalProperties` and
  are read directly by the runner. For "schema is the complete vocabulary" to hold, add them to
  the schema first. Small, and it also tightens linting.
- **Reserved words:** map `in`→`in_`, `for`→`for_` per the total rule.

## Fate of the shipped #186 code (Decision 4 — replace outright)

`resolve_pipeline_paths` / `ResolvedPipelinePaths` shipped in `eddb4ff` but are **unreleased**,
so back-compat cost is zero.

- **Delete** `resolve_pipeline_paths` and `ResolvedPipelinePaths`. The object model is the only
  public path: `load_pipeline(p).resolve(vars).output_file_directory`.
- **Keep** `build_run_context` (internal) — shared by the runner *and* `.resolve()`, so the
  anti-drift guarantee #186 established is preserved, just behind the object.
- **Rewrite** `docs/python-api.md` and the ears-to-hear collab-doc note to the object model
  (they currently document the flat function).

## Implementation: facade over existing functions

The public objects add **shape + delegation, zero logic**. Every verb already has exactly one
internal implementation that the CLI/runner already call; the facade is a naming/navigation
layer over them, never a second copy.

| API surface | Existing implementation | Kind |
|---|---|---|
| `Pipeline`/`Step` attributes | dict field reads | no logic |
| `p.resolve()` | `build_run_context` + `resolve` (`context.py`) | exact delegation (shared w/ runner) |
| `p.run()` | `run_pipeline` (`runner.py:424`) | exact delegation (CLI calls same) |
| `p.lint()` | `lint_pipeline_full` (`linter.py:926`) | exact delegation (CLI calls same) |
| `s.render_prompt()` | `render_prompt` (`steps/llm.py:70`) | exact delegation (runner calls same) |
| `call_llm()` | `call_llm` (`llm_runner.py:275`) | exact delegation (runner calls same) |
| `load_pipeline()` | inline `yaml.load(LLMFlowLoader)` (`runner.py:496`, `pipeline_paths.py:44`) | extract to one function |
| `p.schemas()` | none (per-prompt `schema_ref`, `tools/replay.py:111`) | small new derivation |

**5 exact delegations; attributes are free; only 2 need code** — `load_pipeline` (which *removes*
existing inline duplication) and `schemas` (a small aggregation over an existing extractor).

**Three rules keep it single-source:**

1. **Never reimplement — always delegate.** A facade method that contains logic means a second
   copy exists; that's a bug. (The `build_run_context` anti-drift principle, applied everywhere.)
2. **Extract the two inlined spots into one shared function**, called by both CLI and API:
   `load_pipeline()` and the `schemas()` walk.
3. **Landmine:** `sp clean`'s deletion logic is inline (`cli.py:325-387`) with no extracted
   function. Not in the API surface today — but if `pipeline.clean()` is ever exposed, extract it
   first, or CLI and API diverge there.

### Decision 5 — CLI is a facade client (approved)

The CLI is reoriented to call the facade rather than the core functions in parallel: `sp run` →
`load_pipeline(path).run(...)`, `sp lint` → `.lint(...)`, etc. (`sp clean` already does this via
`resolve_pipeline_paths`.) One path per operation; CLI/API divergence becomes structurally
impossible. Cost: touch each CLI handler once.

### Decision 6 — Tests are layered, not wholesale-rebased (approved)

Test each behavior **once, at the layer that owns it** — do not route logic tests through the
zero-logic facade (indirection, and it couples core tests to the API shape):

- **Core/unit tests stay on the implementation** functions (`run_pipeline`, `lint_pipeline_full`,
  `build_run_context`, `resolve`, `render_prompt`, `call_llm`) — where the logic lives.
- **A thin facade test layer is added:** object-model correctness (attributes ↔ config, plus the
  schema-mirror drift test), delegation wiring (each method calls the right function with the
  right args), and a few end-to-end "public path works" checks.
- **CLI tests keep testing the CLI**; since the CLI now goes through the facade, they double as
  integration coverage — a bonus, not a reason to rewrite them.
- **Rebase only** tests tied to a deleted public entry — `tests/test_resolve_pipeline_paths.py`
  moves from `resolve_pipeline_paths(...)` to `load_pipeline(...).resolve(...)`.

## Resolved decisions (summary)

| # | Decision | Resolution |
|---|---|---|
| 1 | Machine-composability | **Binding requirement.** Auto-locks attr/method rule, `in_`/`for_`, leaf-naming — all total. |
| 2 | Published mapping | **First-class artifact:** public versioned `PIPELINE_SCHEMA` + versioned method catalog; JSON manifest deferred. |
| 3 | Class ↔ schema sync | **Hand-write + drift test**, schema + catalog as single oracle. Not codegen. |
| 4 | Shipped #186 | **Replace outright**; `build_run_context` stays internal; docs rewritten. |
| 5 | CLI vs. API | **CLI is a facade client** — `sp <verb>` → `load_pipeline().<verb>()`. One path per operation. |
| 6 | Tests | **Layered, not wholesale-rebased** — logic on core functions; thin facade wiring/drift tests; rebase only deleted-entry tests. |

## Rollout (slices of #187)

1. Close the schema gap (dir keys) + reserved-word rule. **Extract `load_pipeline()`** from the
   inline loader (removes existing duplication).
2. Read-only `Pipeline`/`Step` (declared attributes) + schema-mirror drift test + thin facade
   wiring tests; publish `PIPELINE_SCHEMA` and the method catalog.
3. `.resolve(vars=None)` → `ResolvedPipeline`/`ResolvedStep`; **delete** `resolve_pipeline_paths`
   and **rebase** `tests/test_resolve_pipeline_paths.py` onto `load_pipeline().resolve()`.
4. Delegating methods, each its own PR: `p.lint()`, `p.run()`, `s.render_prompt()`, `call_llm`
   (#175), and `p.schemas()` (the one new derivation).
5. Reorient the CLI onto the facade (`sp run/lint/...` → `load_pipeline().<verb>()`), one handler
   at a time; CLI tests stay as integration coverage.
6. Rewrite `docs/python-api.md` to lead with the object model; rewrite the #186 example and the
   collab-doc note.

---

**Nothing here is built yet. Awaiting the Captain's go-ahead to implement.**
