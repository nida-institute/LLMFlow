<!-- This project's own map. Hand-authored; sp never overwrites it. -->
# Document Index — Scripture Pipelines, the engine repository

This is **this repository's** map. `docs/ai-context/sp/index.md` is the other one: it lists what
Scripture Pipelines ships into a project, and it is rendered from `data/file-catalog.yaml`.

The split is structural. Everything under `docs/ai-context/sp/` is regenerated and belongs to sp;
everything under `docs/ai-context/project/` is created once and belongs to this project. sp cannot
generate the file you are reading — in the Captain's words, *"we can't know what files a project
has created in advance"* — which is why it is hand-authored and why keeping it current is a human
job.

---

## Read first, every session

| Topic | Go to | When |
|---|---|---|
| What this repository *is* — the engine, not a project using it | [overview.md](overview.md) | Once, and whenever advice meant for a consumer repo seems to apply here |
| Live session state, next step, established facts | [project/HANDOFF.md](../../../project/HANDOFF.md) | **First** — before TODO.md |
| Active work, what is in flight, what not to touch | [project/TODO.md](../../../project/TODO.md) | Every session (rule `todo-is-the-session-cache`) |
| The rules every session here is held to | [../sp/rules.md](../sp/rules.md) | **Before any change** — authoritative |
| Constraints that hold in **this** repository and nowhere else | [rules.md](rules.md) | Alongside `sp/rules.md`; short, and it is where local prohibitions live |
| **Every module and function this engine has** | [docs/index.json](../../index.json) | **Before writing any function, and before adding a module.** Search it first — **duplicate code is buggy code**, and it diverges from the original the moment either changes |

### Search `docs/index.json` before you write

It carries one entry per module — `module`, `imports`, and every function with its signature and
docstring — so the question *"does this already exist?"* is answerable in one command rather than
by recalling the tree:

```bash
jq -r '.modules[] | select(.module | test("verse|version")) | .module as $m
       | .functions[] | "\($m).\(.name)\(.signature | sub("^[^(]*";""))"' docs/index.json
```

This is the file whose absence from this index let a session write its own verse-overlap check
while `llmflow.utils.verse_ranges.overlaps` and `verse_ranges.select` already existed — `select`
having been written precisely because four plugins had each hand-rolled that loop. `one-design`
and `read-the-docs` both bear on it; this row is how you comply with them cheaply.

**This guidance is engine-only and is deliberately not shipped.** A project using Scripture
Pipelines reaches it through **one** surface — the `sp` command line and the pipeline language
it reads — and never by importing the package, which carries no compatibility promise.
`index.json` maps the internals, so it answers a question only work *on the engine* is entitled
to ask. The consumer-facing half of this — the one surface, and that a project's tests belong on
it rather than on internals — lives in `templates/project/docs/ai-context/sp/overview.md`, which
ships, and is held there by `tests/test_shipped_context_names_one_surface.py`.

The `llmflow` Python API is real and supported, and it is **the engine's own**: `docs/python-api.md`
documents it for work in this repository. Narrowed from "two surfaces" on the Captain's ruling —
*"this absolutely needs to show only the cli command line and the CLI API"* — because a project
told about a second surface builds against a contract nobody offered it.

**It binds this repository's own tests too.** A test here exercises a step through the object
model or the CLI, not by handing a handler a dict (`rules.md` §1, and #250, which counts 29 files
against 12). Reading `index.json` is how you find the public call before writing a private one.

## This engine's own documentation

| Topic | Go to | Notes |
|---|---|---|
| Installing the CLI | [INSTALL.md](../../../INSTALL.md) | Standalone binaries; Gatekeeper and SmartScreen steps |
| Quickstart | [docs/tutorial.md](../../tutorial.md) | `sp init`, a greeting pipeline, a two-step example |
| Setup and CLI basics | [docs/getting-started.md](../../getting-started.md) | Environment variables, linting, the resource-repo pattern |
| YAML grammar and step types | [docs/llmflow-language.md](../../llmflow-language.md) | `llm` / `function` / `for-each` / `window`, variables, `append_to`, structured output |
| Architecture and modules | [docs/architecture.md](../../architecture.md) | CLI, runner, linter, telemetry, plugin hooks; §15 is the debug request/response dump |
| Python API | [docs/python-api.md](../../python-api.md) | `load_pipeline(...)` then `.resolve()` / `.lint()` / `.run()` / `.schemas()`; `PIPELINE_SCHEMA` and `api_catalog()` are the machine-readable syntax-to-API map. Prefer this over re-parsing pipeline YAML |
| Why this rather than something else | [docs/why-scripture-pipelines.md](../../why-scripture-pipelines.md) | Comparison with general-purpose orchestration frameworks |
| Moderation failures | [docs/moderation-handling.md](../../moderation-handling.md) | Provider blocks on biblical text, and the mitigation checklist |
| Design and plan documents | [project/plans/README.md](../../../project/plans/README.md) | Generated index of every design and plan with its status. **Consult before proposing a design.** A document marked *Implemented — historical record* explains why code looks as it does; one marked *Proposed* is not authorization to build |

## This project's own context

The four documents beside this one. They are this repository's, not sp's — they describe the
engine's internals and the data it reads, which no other project has.

| Document | Covers |
|---|---|
| [gui-architecture.md](gui-architecture.md) | The GUI's dual-location setup — `gui/backend` against `src/llmflow/gui` — and which one is live |
| [data-sources.md](data-sources.md) | Where the biblical datasets live and how to reach them: BaseX collections, file paths, DuckDB |
| [paratext-schemas.md](paratext-schemas.md) | Paratext metadata schemas |
| [data-shapes.md](data-shapes.md) | The shape of intermediate artifacts passed between steps |

## What Scripture Pipelines ships

Not listed here. [../sp/index.md](../sp/index.md) is rendered from the file catalog, so it cannot
go stale, and a second hand-kept copy of it is exactly the defect that index exists to avoid.

---

## Two things that are easy to get wrong here

**This repository is also a project.** It lives under the same layout it ships, so
`docs/ai-context/sp/` here is regenerated content, not authored content. An edit there is lost.

**Prose says Scripture Pipelines; `llmflow` is the import namespace only.** See
[project/plans/design-vocabulary.md](../../../project/plans/design-vocabulary.md), which is draft
but in force for user-facing text.
