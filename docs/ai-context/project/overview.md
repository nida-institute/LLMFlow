<!-- Created once by sp init. This file is yours; sp never overwrites it. -->
# What this repository is

**This is the Scripture Pipelines engine itself** — the package that provides the `sp` command.
It is not a project that *uses* Scripture Pipelines. Repositories that do — `ears-to-hear`,
`discourse-flow`, `discourse-flow-hebrew`, `sil-translator-notes` — consume this one, and the
distinction matters because advice that is right for a consumer is often wrong here.

You are in the right repository if `src/llmflow/cli.py` and `src/llmflow/runner.py` exist and
`pyproject.toml` defines the `llmflow` package. The published distribution is
`scripture-pipelines`; `llmflow` remains the Python package and import namespace only.

## Layout, and what each part is for

| | |
|---|---|
| `src/llmflow/` | the engine. `runner.py` orchestrates, `cli.py` parses, `steps/` holds one handler per step type, `plugins/` the registered extensions, `utils/` the shared readers |
| `src/llmflow/templates/` | what `sp init` writes. `templates/sp/` lands in `~/.sp`, `templates/project/` in a project — the paths mirror their destinations |
| `data/` | declarative sources of truth: `file-catalog.yaml` (every file sp manages), `ai-rules.yaml` (the rules), `models.json`, `versification-editions.json` |
| `docs/` | human- and AI-facing documentation. `llmflow-language.md` is the language reference |
| `project/` | plans, audits and tracking — `plans/`, `audits/`, `TODO.md`, `HANDOFF.md` |
| `tests/` | the suite, including a number of guardrails that assert structure rather than behaviour |
| `gui/` | the frontend, whose backend files are copied into the package at build time |

## Two ideas that explain most of the design

**One declaration, read by everything.** Where a fact can be stated as data it is stated once and
the code reads it: `data/file-catalog.yaml` drives what `sp init` writes, what `sp doctor`
repairs, and what the generated `.gitignore` contains; `pipeline_schema.py` drives the linter's
per-type validation *and* the object model's attribute set. A second hand-kept list is treated as
a defect, because the two always drift and the shorter one wins by being closer to hand.

**Silence is the failure to design against.** The recurring failure in this domain is not a
crash but a confident answer about the wrong input — a reference resolved in the wrong
versification, a footnote flattened into scripture, a pericope boundary that came from a
publisher's heading rather than an analysis. So the engine prefers a loud error to a plausible
result, and where it cannot be certain it says which of several answers it found rather than
choosing one.

## What to read next

`docs/ai-context/project/index.md` maps the topic documents on this side —
data shapes, data sources, the GUI's dual-location build, and the Paratext schemas.
`docs/ai-context/sp/` is the generated half and is regenerated on every `sp init`; a change
there is lost, and the fix belongs in the template or constant it came from.
