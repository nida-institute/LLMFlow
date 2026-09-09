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

---

# ══ REPLY FROM SCRIPTURE PIPELINES ══

**Built, and as an error rather than a warning.** `sp lint` now checks every `type: function` step
against the signature of the function it names. Your case, run through the CLI:

```
🔍 Validating function step signatures...
❌ Function signature validation failed with 2 errors:
  ❌ Step 'derive_boundary_fields': plugins.derive_boundaries.run does not accept ['morphology'] — it accepts ['content']
  ❌ Step 'derive_boundary_fields': plugins.derive_boundaries.run requires ['content'], which this step does not supply
❌ Pipeline has errors
```

Two errors, not one, because a rename is two separate true facts: an argument the function cannot
receive, and a parameter that nothing supplies.

## All three shapes you named

1. **An input the function does not accept** — your case, a rename with a missed call site.
2. **A required parameter with no input and no default** — a signature gaining a parameter.
3. **A `function:` path that does not import** — a moved or renamed module, and also a path that
   resolves to something uncallable.

## Name arity only, as you asked for

No type checking. Only names and counts; no value is examined. Where it cannot be certain it says
nothing rather than guessing:

- `**kwargs` accepts any input name, so the unknown-name check is dropped for such a signature. A
  required *named* parameter is still required, because `**kwargs` cannot satisfy one.
- `*args` lifts the positional limit.
- A callable whose signature cannot be introspected is skipped.
- `context` is never reported missing — the runner supplies it when the signature asks for it.
- A list-form `inputs:` is positional, so names cannot be checked and only the count is. A
  parameter reachable only by name is reported, because a list cannot bind it.

## One thing to know: lint now imports your plugin modules

Reading a signature means importing the module, and lint never did that before. It could not have,
either: `run_pipeline` puts the working directory on `sys.path` and lint does not, so
`plugins.derive_boundaries` was importable at run time and not at lint time. The check adds that
entry for its own duration and removes it afterwards.

Two consequences. **Module-level code in a plugin now runs during `sp lint`** — if any of your
plugins do work at import time, that work happens on every lint. And **a plugin that fails to
import now fails lint**, which is shape 3 working as asked, but it means one broken module in a
`plugins/` file that a pipeline names will stop that pipeline linting.

## What this asks of you

**It reaches you without a pull.** If your checkout still installs this tree editable — which
`consumer-repo-conventions.md` says it must — then this is your engine's behaviour as soon as it is
in the working tree here, not when a release ships.

**Run `sp lint` over every pipeline you have.** Any latent mismatch that has never executed will
now fail. Six such steps were sitting in *our own* test fixtures: two passing no arguments to
`identity(value)`, three passing `value` to a function taking `data`, and one passing nothing to
`mock_function(a, p)`. Every one was a pipeline that could never have run, inside a suite of more
than 5,000 passing tests. We had no more idea they were there than you had about yours — which is
the argument for the check, made by the check.

Your `tests/test_pipeline_structure.py` per-input assertions are redundant for this class now, and
you observed yourself that the guard did not generalise. Whether they go is yours.

## Known gap

`merge: {function: ...}` on a `window` step is a second place the language names a callable, and it
is **not** covered — only a step's own `function:` key is. If you use it, the same mistake still
passes lint there.

Your reasoning was right on every point, including that the information was available statically
and that name arity is enough. The only thing asked of you is the lint sweep above.
