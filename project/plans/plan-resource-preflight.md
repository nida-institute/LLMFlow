# Plan — lint preflights the resources a pipeline names, and offers to install them

**Status:** built 2026-10-05. Two things await the Captain: Q6 (§2, last item), and
§4.4 as I read it. Three derivations made while building are in §2a.
**Issue:** #261. **Depends on:** #252 (built 2026-10-05), whose licence display and agreement
this calls rather than repeats.
**Author:** AI, from the issue, the Captain's rulings in conversation on 2026-10-05, and the code
as measured the same day.

---

## 1. Goal

`sp lint` answers, before anything runs: **which resources does this pipeline need, which can this
machine open, and what would get the rest** — and offers to get them. `sp run` lints first unless
`--skip-lint`, so a run inherits it.

## 2. Ruled by the Captain, 2026-10-05

1. **An unregistered resource is a lint error.** The run cannot succeed, and lint costs nothing.
2. **A requested `include:` family whose path is missing is a lint error** — `syntax` without
   `lowfat_path`, `discourse` without `discourse_path`. *Derived, not asked:* with ruling 4 it comes
   with the offer to fix it, so the error costs one keystroke. The runner keeps its warning for a
   `--skip-lint` run.
3. **The resource table is printed only when something is missing**, not on every run.
4. **`sp lint` itself offers to install** — *"if lint can, it's best for the user."* Lint stops being
   strictly read-only for this one case, and only with a person at a terminal or a flag that says so.
5. **#244 did not wait for this** — it shipped.
6. **Without a terminal: `--install-missing` on `sp lint` and `sp run`, alongside `--accept-terms`.**
   One flag per consent — downloading is one, agreeing to someone's licence is another. Without a
   terminal and without `--install-missing`, a missing resource is an error naming that flag. With
   it and without `--accept-terms`, the install proceeds and #252's gate fails closed naming
   `--accept-terms` (a bare pointer whose text cannot be fetched excepted, as in #252).
   The Captain: *"that will help me now with licences for my registered resources"* — see §4.4.

**Awaiting — Q6, what `[A]ll` covers.** Asked as "does `[A]ll` also accept the licences?" and
answered "yes", against a table that said the issue leans *no*; put back to him as (a) install only,
each licence still asked, or (b) install and agree to every remaining licence. Until answered,
§4.3 builds (a), which is the reading `[A]ll` cannot make worse.

## 2a. Derived while building — for the Captain to confirm or overrule

1. **A resource, or a family, named only under a `condition:` is a warning, not an error.**
   Ruling 1's reason is that the run cannot succeed; a step whose condition may be false does
   not stop it. The starter fetches SBLGNT or WLC by `${passage_info.testament}`, a value lint
   cannot compute, and as an error every Greek reader would have had to install WLC. It is still
   reported and offered. Conditionality is per family: the starter names SBLGNT always, and asks
   for `syntax` only in its Greek step.
2. **A missing path is reported with its command, not offered** (§4.2 bullets 2 and 3, not
   built). Nothing declares where Lowfat or discourse data lives — the catalog's `provides`
   names only `path`, and no file in `data/` or `src/` records a Lowfat location — so an offer
   would have to invent a path for the user to accept. The lasting fix is `provides` declaring
   it, upstream (`awesome-biblical-data#5`); then the offer is one line.
3. **The CLI makes the offers; the linter only returns findings** (`LintResult.resources`), so
   `pipeline.lint()` as a library call never prompts or writes. JSON output (`sp lint --json`)
   makes no offers, since a prompt would corrupt it.

## 3. What exists today, measured 2026-10-05

| what | where |
|---|---|
| Lint entry, returns `LintResult` and does no I/O beyond logging | `utils/linter.py:1452` `lint_pipeline_full` |
| `sp run` lints, then runs with `skip_lint=True` | `cli.py:1169-1187` |
| The precedent: a dependency checked at lint instead of at request time | `utils/schema_preflight.py`, called from `linter.py:959` |
| Runtime failure for an unregistered resource, with a good message | `utils/scripture.py:914-942` `resolve_resource` |
| Runtime warning and `null` for a missing analysis path | `utils/scripture.py:1171` |
| Steps that name a registered resource | `steps/scripture.py:28`, `steps/parallel_passages.py:30` (`resource:`) |
| `sp resource add` writes neither `lowfat_path` nor `discourse_path` — the catalog's `provides` names only `path` | `data/resources.json`, the three `provides` entries |

**Corrected from the issue:** `type: alignment`'s `source:` and `target:` are **not** registered
resources. They are document ids looked up in the declared alignment pairs, whose corpus is a
*dataset* registration (`steps/alignment.py:44-62`, `resolve_pair`). The preflight checks that
dataset is registered and reports it as a dataset, with `sp dataset add`, not `sp resource add`.

## 4. The work

### 4.1 `utils/resource_preflight.py` — what is needed and what is missing

Beside `schema_preflight.py`. Pure: reads the pipeline and the registry, writes nothing.

- Walks every step, nested `for-each` included, and collects `resource:` on `scripture` and
  `parallel-passages`, with the `include:` families each asks for; and, for `alignment`, the
  declared pair's dataset.
- A `resource:` that is a `${var}` is resolved with the lint's `--var` values and the pipeline's
  `variables:`; one still unresolved is reported as such rather than guessed.
- Per resource: registered or not; in the catalog or not (only a catalog resource can be offered);
  for each requested family needing a path, whether the registration names one that exists.
- Returns findings; `lint_pipeline_full` turns them into errors. The table (§2.3) is built from the
  same findings and printed only when there is one.

### 4.2 The offer — in the CLI, not the linter

The linter returns findings and does no prompting, so `sp lint` and `sp run` stay testable and the
library call `pipeline.lint()` stays read-only. The CLI, given errors that carry a fix:

- **A missing catalog resource:** `Install and register BSB? [Y]es / [N]o / [A]ll`. **Y** calls the
  same code `sp resource add` calls — download, #252's licence and agreement, registration. One
  function, extracted from the `resource add` handler, called from both.
- **A missing `lowfat_path` whose data is on disk** (the Lowfat sits inside the same download):
  `Record SBLGNT's Lowfat at <path>? [Y/n]`, through the `sp resource set` code.
- **A missing `discourse_path`:** its data is another dataset (`levinsohn-lgntdf`), so the offer is
  an install of that dataset — with its own licence — then the path is recorded.
- After the offers, lint runs again; what was declined stays an error.

### 4.3 Without a terminal

`--install-missing` answers every install offer yes; `--accept-terms` is passed through to #252's
gate unchanged. Neither implies the other. With neither, the error names `--install-missing`.

### 4.4 Registrations made before #252 — the Captain's "help me now"

*My reading of his remark, for him to confirm:* a resource the pipeline names that is registered
but carries no `terms:` record (registered before #252) is reported, and offered the same licence
display and agreement — recorded with no download. `--accept-terms` answers it without a terminal.
Not an error: the resource opens; only the record is missing.

## 5. Tests, written first

Pipelines constructed through the object model, the registry under a temporary `SP_HOME`, the
network faked as in `tests/test_terms_on_download_and_register.py`.

- an unregistered resource is a lint error naming `sp resource add` — and the run never starts
- a `syntax` request with no `lowfat_path` is a lint error; with one, clean
- a resource inside a `for-each` is found; a `${var}` resource is resolved from `--var`
- an alignment's dataset, unregistered, is reported as a dataset
- nothing missing → no table printed
- `[Y]` registers through the `resource add` path, licence shown and agreed; `[N]` leaves the error
- `[A]` installs the rest without asking again, and still asks each licence (pending Q6)
- no terminal, no flag → error naming `--install-missing`; with it but without `--accept-terms`
  → the terms gate fails closed naming `--accept-terms`
- `pipeline.lint()` called as a library never prompts and never writes

## 6. Not in this

- **Catalog `provides` declaring `lowfat_path`**, so `sp resource add` writes it — the lasting fix
  for the Lowfat case, upstream in `awesome-biblical-data#5`.
- **The runner's own warning** for a `--skip-lint` run is unchanged.
