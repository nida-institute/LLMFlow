# Design: split the overloaded `format` keyword

**Status:** Design note — **not approved, nothing built.** Requested 2026-08-12 as item 4 of the
keyword-consistency pass (`design-schema-single-source.md`), the one item judged too disruptive
to decide on the spot.
**Companion:** the other four inconsistencies (`output`/`outputs`, `template`/`format_with`,
`timeout`/`timeout_seconds`, hyphenated loop keys) were unified in that pass. `format` was held
back because, unlike those, it is genuinely in use.

---

## The problem

`format:` is one keyword carrying **three unrelated meanings**, selected by which step type it
appears on. Verified in the engine:

| Meaning | Where | Values | Read by |
|---|---|---|---|
| **How to serialize** what is written to disk | any step with `saveas:` | `auto`, `json`, … | `utils/step_outputs.py:81,95` (`step.get("format", "auto")`) |
| **How to parse** each file loaded | `load_directory` (and the loader dispatch) | `json`, `yaml`, `xml`, `csv`, `tsv`, `text` | `steps/load.py:58`, validated in `utils/linter.py` against `_LOADER_FORMATS` |
| **What shape** the result takes in context | `duckdb` | `records` | `steps/duckdb.py:32` (`step.get("format", "records")`) |

Three contracts, three value vocabularies, three defaults — one name. Nothing in the YAML tells
a reader which one they are looking at; they have to know the step type's semantics first.

### Why this is worse than an alias

The retired aliases were *redundant* — two names, one meaning, so a reader who guessed wrong
still got the right behaviour. `format` is the inverse: **one name, three meanings**, so a reader
who guesses wrong is simply wrong. And because per-type linting now applies, `format` is *valid*
on all three families, so nothing flags a confusion between them.

Concretely, this is legal and means two different things in one step:

```yaml
- name: load_and_save
  type: load_directory
  path: "${data_dir}"
  pattern: "*.csv"
  format: csv                    # parse each file as CSV
  outputs: rows
  saveas:
    path: "${out}/rows.json"
    format: json                 # serialize the result as JSON
```

The step-level `format` is the parser; the `saveas.format` is the serializer. They are different
keywords that happen to share a name, and the only thing distinguishing them is nesting depth.

## Options

### A. Three distinct keywords

| Meaning | Proposed |
|---|---|
| serialize on write | `serialize_as` |
| parse on read | `parse_as` |
| result shape | `result_shape` |

Truest to the language. Each name says what it does, and a reader never has to know the step
type first. Highest migration cost (see below).

### B. Split only the ambiguous pair, keep `format` for one meaning

Keep `format` for **parsing** (the loader meaning, where it is most used and most intuitive),
rename the other two: `saveas.serialize_as` and duckdb's `result_shape`. Cheaper, and it removes
the genuine collision — the loader/saveas overlap shown above. Leaves `format` meaning one thing.

### C. Leave it, document it

Add a table to `llmflow-language.md` stating the three meanings. Zero migration; the ambiguity
stays, and a machine reading `PIPELINE_SCHEMA` still cannot tell which contract applies.

## Migration cost — must be measured before deciding

The other four renames were nearly free (0-98 usages, all mechanical). `format` is **not**
known to be cheap, and no count has been taken. Before choosing, count `format:` across:

- this repo's `pipelines/` and `docs/`
- `ears-to-hear`, `discourse-flow`, `discourse-flow-hebrew`, `semdom-greek-lexicon`,
  `sdbh-helpers`, and any other repo with `pipelines/*.yaml`

split by **which of the three meanings** each usage carries — a raw count is not enough here,
because the three meanings migrate to different names. The `saveas.format` usages are nested and
need a separate pass from the step-level ones.

## Recommendation

**B**, if the count supports it — it fixes the real collision (loader vs `saveas` in the same
step) at roughly half the churn of A, and leaves `format` meaning exactly one thing rather than
retiring a keyword everybody knows. Fall back to **A** if the counts turn out small enough that
full precision is cheap.

Whichever is chosen, follow the pattern that worked for the other four: retired spellings become
**lint errors naming their replacement**, never silent aliases, and consumer pipelines migrate in
the same window.

## Open questions for the Captain

1. Which option — and is `serialize_as` / `parse_as` / `result_shape` the right vocabulary? (These
   are proposals, not decisions; `write_as` / `read_as` are equally available.)
2. Does the `saveas.format` → nested rename count as part of this, or is nested-key naming a
   separate concern?
3. Same-window consumer migration as before, or staged this time given `format` is genuinely used?
