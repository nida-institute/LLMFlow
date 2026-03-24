## Summary

The `type: basex` step currently uses a `params:` block whose values are substituted into the XQuery string via Python `str.format_map`. This collides with XQuery's own `{ }` curly-brace syntax (used in computed element constructors, map/array literals, etc.), forcing query authors to either avoid computed content or double-escape every brace — a constant source of bugs.

## Proposed change

Replace `params:` with an `inputs:` block (consistent with `type: function`) whose resolved values are injected as BaseX **external variable bindings** via the CLI `-b` flag:

```
basex -blemma=הָיָה -bbook=MAT query.xq
```

XQuery declares variables as external:

```xquery
declare variable $lemma external;
declare variable $book  external;
```

No Python string manipulation of the query; no brace escaping; no collision with XQuery syntax.

## YAML before (current)

```yaml
- name: query-corpus
  type: basex
  query_file: queries/verb-clauses-by-subject.xq
  params:
    lemma: "${lemma}"
  timeout: 180
  outputs: corpus_json
```

## YAML after (new)

```yaml
- name: query-corpus
  type: basex
  query_file: queries/verb-clauses-by-subject.xq
  inputs:
    lemma: "${lemma}"
  timeout: 180
  outputs: corpus_json
```

## Implementation scope

- `src/llmflow/plugins/basex.py` — replace `str.format_map` substitution with `-b<key>=<value>` CLI args
- `src/llmflow/runner.py` `run_basex_step()` — read `inputs:` instead of `params:`
- `queries/acai-verse-range.xq` — rewrite to use `declare variable ... external`
- `tests/test_basex_plugin.py` — new tests for inputs binding, no-inputs path, error paths

## Affected repos

- `nida-institute/LLMFlow` (core change)
- `nida-institute/sdbh-helpers` must be migrated: its basex step uses no `params:` today (query pre-processed by Python), so the migration mainly means updating the XQuery to declare externals if `-b` bindings are desired
