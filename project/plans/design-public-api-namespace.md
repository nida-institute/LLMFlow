# Design — the public API's import namespace

**Issue:** [#265](https://github.com/nida-institute/LLMFlow/issues/265), filed 2026-09-29. #209
renames the *repository* and explicitly leaves the import namespace standing; this is the gap
beside it. The issue is the record outsiders read and holds no `=>` slots; this document carries
the working and the open slots.

**Status:** proposed (2026-09-29). Two rulings recorded; D1, D2 and D3 open.

**Ruled 2026-09-29:** the name is `import scripture_pipelines as sp` (§1), and **`llmflow` does
not survive** — no shim, no alias, no grace period (§8). `proposed` is thinking aloud and is
**not authorization to build.** Every `=>` in §5 is the Captain's.

## 1. The ruling

**`import scripture_pipelines as sp`.** Ruled by the Captain 2026-09-29, approving the
recommendation in those words. `scripture_pipelines` is the real package; `sp` is the documented
convention, the `numpy as np` pattern.

His framing the same day, and the reason this is now urgent rather than tidy:

> *"we have been trying to retire the name llmflow. the new public api is the one we want people
> to use, including the clients we ourselves write."*

> *"we publish to PyPi, so the api will be broadly available."*

## 2. Why this name, and why not the alternatives

**The distribution is already `scripture-pipelines`** (`pyproject.toml:2`), and PEP 8
normalization makes `scripture_pipelines` its matching module name. So `pip install
scripture-pipelines` → `import scripture_pipelines` is the coherent form. What ships today is the
incoherent one — the same shape as `scikit-learn` → `sklearn`, which nobody defends.

**A short name as the real package was rejected.** `sp` or `scripture` as the actual top-level
module claims a very generic name on a public index and invites collision. As an *alias* it costs
no claim, evokes the `sp` command, and reads well in client code: `sp.load_pipeline(...)`.

**Publishing is what makes this urgent.** PyPI already carries `scripture-pipelines`, and
`pypi.org/project/llmflow` does not exist (#209). The moment anyone outside imports `llmflow`,
the name is permanent. The Captain in #209, 2026-08-24: *"We have very few users now, this is the
time to make clean changes before it's too late."* That argument was made about the repository
name; it binds harder here, because a repository rename is redirected by GitHub and an import
name is not.

## 3. What #209 settles, and what it leaves

#209 covers the repository, remotes, CI trusted publishing, ~50 URLs and the `LLMFlow/` path
component. It lists **"the `llmflow` import namespace"** among what was *left standing
deliberately* in the 2026-08-24 prose sweep. So this document is not a duplicate of it; it is the
piece that sweep set aside.

The two should be sequenced rather than merged — #209's own first step is a plan naming the order
of operations, and a namespace rename has a different blast radius from a repository rename.

## 4. What it costs, measured 2026-09-29

| what | measured |
|---|---|
| `pyproject.toml:76` | `packages = ["src/llmflow"]` — one line |
| `src/llmflow/__init__.py:19` | `__all__` exports **10** names |
| test files importing the package | **~230** of roughly 260 |
| dotted engine paths in docs and AI context | **7** sites |
| `function: llmflow.*` in **pipeline YAML** | present in this repo's context docs; **not measured in consumer repos**, which is where the cost actually lands |

**The expensive part is the last row, and it is not a Python break — it is a pipeline-language
break.** A `function:` step names a dotted path, so consumer pipelines stop resolving.

**That cost is already shrinking for another reason.** `the-language-is-the-whole-surface`
requires shipped material to show a step type and a command, never one of our dotted paths. If
built-in functions gain plain names first, a rename touches far less YAML. Sequencing is
therefore a real decision, not a detail — it is D3.

## 5. Decisions

Answer inline after each `=>`.

### D1. Does `the-language-is-the-whole-surface` get its scope narrowed?

As ruled on 2026-09-27 it says a project reaches the engine **one way** — the `sp` command line
and the pipeline language — and that importing the package is not supported. The intent stated on
2026-09-29 is that clients, including ones we write, build on a public Python API. **Those cannot
both stand as written.**

This is not a technicality: a session on 2026-09-29 cited that rule against this very work before
being corrected. Until the rule says which surfaces are offered and to whom, the next one will do
the same.

- **A** — narrow the rule: the *pipeline language* is the whole surface for expressing a pipeline,
  and a separate, named Python API is offered for clients.
- **B** — leave the rule and record the public API as an exception with a stated boundary.
- **C** — something else.

=>

### D2. What is in the public API?

Today `__all__` carries ten names: `load_pipeline`, `Pipeline`, `ResolvedPipeline`, `Step`,
`call_llm`, `parse_bible_reference`, `resolve_book`, `model_metadata`, `PIPELINE_SCHEMA`,
`api_catalog`.

That list was not designed as a client surface. `PIPELINE_SCHEMA` and `api_catalog` sit in it
under a comment calling them a *"published machine-readable mapping (Decision 2)"* — a relic of
the two-surface era the 2026-09-27 ruling ended. Blessing the list as it stands and designing a
client-facing surface are different jobs with different costs.

=>

### D3. Order: namespace first, or plain names for built-in functions first?

Renaming first breaks `function: llmflow.*` in every consumer pipeline on the day it lands.
Giving built-in functions plain names first removes most of those paths, so the rename touches
little YAML — at the price of doing two migrations in sequence rather than one.

**Sharpened by the §8 ruling.** With no shim, there is no other lever on that break, so this
question now carries the whole cost of the rename rather than a scheduling preference.

=>

## 6. What this does not change

The `sp` command line, the pipeline language, and every pipeline that does not name a dotted
path. A pipeline written to `the-language-is-the-whole-surface` — step types and commands, no
imports, no dotted paths — is unaffected by anything here.

## 7. How to do it safely — the method, and what proves each part

Measured 2026-09-29. **The risk is not evenly spread**, and three of the four tiers have an
objective check. Written before anyone starts, so the verification is chosen rather than
improvised.

### Tier 1 — proves itself

Every `from llmflow import …` and `import llmflow.x`. Python fails loudly and immediately, and
the suite is **5,956 tests**. Green before and green after closes this tier with no judgement
involved. It is the bulk of the work and the least of the risk.

### Tier 2 — strings inside the package, exercised by the suite

The compiler cannot see these, but the suite runs them and they fail loudly:

- **nine `importlib.resources.files("llmflow")`** — `file_catalog.py:141`, `books.py:43`,
  `resources.py:75`, `prompt_structure.py:56`, `ai_rules.py:38`, `telemetry.py:35`,
  `alignment.py:24`, `utils/scripture.py:338`, `cli_utils.py:836`
- **`importlib.import_module(f"llmflow.plugins.{name}")`** — `plugins/loader.py:42`

### Tier 3 — packaging layout, and the suite cannot see it

**`importlib.resources.files("llmflow")` resolves against the source tree in an editable install
and against the packaged layout in a wheel or a Nuitka binary.** So the nine calls above and the
packaging destinations below must move together, and a mismatch is invisible to pytest:

- `pyproject.toml:78-86` — eight `force-include` lines mapping data to `llmflow/…` inside the wheel
- `pyproject.toml:92-93` — `sp = "llmflow.cli:main"`, `sp-gui = "llmflow.gui_launcher:main"`
- `pyproject.toml:76` — `packages = ["src/llmflow"]`
- `.github/workflows/build.yml:135-165` — about fifteen Nuitka flags, every one mapping into `llmflow/…`
- `build_gui.py:24` — `src / "llmflow" / "gui"`

**A green suite and a broken artifact are the expected outcome if this tier is skipped**, which is
the failure `CLAUDE.md` already names twice under "Common Pitfalls". Its check is not pytest: build
the wheel, install it into a clean virtual environment, run `sp --version` and one `--dry-run`
pipeline.

### Tier 4 — outside this repository, provable by nothing here

`function: llmflow.*` in a consumer's pipeline YAML, resolved by `steps/function.py:27` from a
string. It fails when a pipeline runs, on someone else's machine. Consumer editable installs are
the same shape. **This is the irreducible risk, and it is what D3 asks about** — giving built-in
functions plain names first is what shrinks it.

### The order

1. **A branch.** The whole change is one `git checkout` from undone.
2. **`git mv src/llmflow src/scripture_pipelines` as its own commit, nothing else** — git records
   renames, history follows, and the diff stays readable.
3. Mechanical rewrite: imports, the nine resource strings, the plugin loader string.
4. **Full suite** → closes tiers 1 and 2.
5. `pyproject.toml`, `build_gui.py`, `.github/workflows/build.yml`.
6. **Build, install into a clean venv, `sp --version` and one `--dry-run` pipeline** → closes
   tier 3, and nothing else does.

Tier 4 remains open after all six steps. That is a property of the change, not of the method.

## 8. Ruled — `llmflow` does not survive

The Captain, 2026-09-29: **"llmflow should not survive."**

So there is no deprecation shim, no alias module, and nothing published under the old name. This
is `one-design` applied as written rather than as a migration: the new name replaces the old, the
superseded path goes, and tests and docs move in the same change. The rule's escape hatch — an
older path kept with named dependants and a stated end — is **not taken**, so nothing needs to be
named or dated.

**What follows, and it is the whole cost of the ruling.** A consumer pipeline naming
`function: llmflow.*` stops resolving on the day this lands, with no grace period, and a consumer
repo's editable install fails at import until that repo changes in step. There is no softening
mechanism left, by design.

**This makes D3 the load-bearing decision rather than a detail.** Sequencing is now the only
lever on that break: with no shim, giving built-in functions plain names *first* is the one thing
that can reduce how much consumer YAML stops working. That is an argument for an order, not a
ruling on it — D3 is still open.

**What still must be measured before the day is chosen:** how many `function: llmflow.*` paths
exist in the consumer repos, and in which pipelines. Named but not measured here; nobody has
counted, and the count is what tells the consuming projects what they are being asked to do.
