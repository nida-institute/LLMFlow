# `sp lint` passes a pipeline whose function steps cannot run

**From:** an AI session in `nida-institute/discourse-flow`.
**Status: drafted by the AI, pending the Captain's review.**

One finding, from a mistake of ours that lint could have caught and did not.

## What happened

We converted `plugins/derive_boundaries.py` from a verse-keyed morphology map to the running
text — renaming the parameter `morphology` to `content` — and did not update the three pipeline
steps that call it.

```yaml
- name: derive_boundary_fields
  type: function
  function: plugins.derive_boundaries.run
  inputs:
    morphology: "${annotated_book.morphology}"   # the parameter is now `content`
```

`hatch run sp lint` reported:

```
✅ All 4 step contracts valid
✅ All variable references can be resolved
✅ Pipeline validation completed successfully
✅ Pipeline OK
```

Our own test suite was green too — 1,232 passing — because nothing there exercises the
pipeline's wiring. So the pipeline was unrunnable and everything said otherwise. It would have
failed at the first call with `TypeError: run() got an unexpected keyword argument
'morphology'`, after the fetch and the genre-marker step had already done their work.

## Why lint cannot see it

`utils/linter.py:298`:

```python
        # Only validate contracts for LLM steps
        if step_type == "llm":
```

`validate_all_step_contracts` resolves the prompt file, parses its header and checks the step's
inputs against `requires:`. That is a real contract check and it is thorough — for LLM steps.
A `type: function` step has a contract too: the callable's signature. Nothing compares the two.

The three checks that did pass are each answering a different question:

| check | answers |
|---|---|
| "step contracts valid" | do LLM steps supply what their prompt's `requires:` names |
| "variable references can be resolved" | does `${annotated_book.morphology}` resolve in context |
| "template variables match" | do `{{...}}` placeholders have pipeline variables |

None asks whether the function accepts the arguments the step passes. `${...}` resolving says
the value exists, not that anything can receive it.

## Why it seems worth having

The information is available statically. `function:` is an import path, so the signature is
reachable with `inspect.signature` at lint time, without executing anything — the same
introspection `docs/ai-context/project/rules.md` already recommends for asking a pipeline what
it wires.

Three shapes are checkable and all three are real mistakes we have made or could make:

1. **an input the function does not accept** — this one, a rename with a missed call site
2. **a required parameter with no input and no default** — a signature gaining a parameter
3. **a `function:` path that does not import** — a moved or renamed module

The cost of missing it is proportional to where the step sits. Ours was step 6 of 28, so the
run died in seconds. The same mistake at `package_pericope` would surface an hour and $12 into
Mark, because `analyze_discourse` runs 103 times before it.

## What we are not asking for

Not type checking. A parameter annotated `Mapping[str, Any]` receiving a list is a different
problem and needs the value, which lint does not have. **Name arity is enough** — the three
shapes above are all name-level, all static, and all catch the class of mistake that a rename
produces.

And we are aware this is a request from a project with a lot of `type: function` steps, which
is a large surface for exactly this error. About **1,397 lines** of ours sit in territory your
step types already cover — `reference_resolution` 423, `macula_greek` 377, `levinsohn` 307,
`source_language` 290 — plus most of a 555-line USJ helper. We are reducing that surface:
`book-discourse-flow.yaml` now fetches its own document through `type: scripture`, and those
loaders are on their way out.

The rest of our plugin code is segmentation, subdivision, boundary derivation and assembly —
ours to own, and staying. So this is not a check that becomes unnecessary once we finish
adopting your step types; the steps that remain are the ones most specific to us and least
likely to be caught by anything you or we can check about a prompt.

## What it would have cost us to catch ourselves

Nothing we would have thought of. Our test suite reads the pipeline YAML in
`tests/test_pipeline_structure.py` and asserts specific inputs exist by name — which is a guard
we wrote *after* a previous drift, and it did not generalise: it asserts `content` is present
now because we changed it when we changed the pipeline. A guard written per-input catches the
input someone remembered to write a guard for.

No schedule pressure. We caught this one in seconds and the conversion is committed and green.
