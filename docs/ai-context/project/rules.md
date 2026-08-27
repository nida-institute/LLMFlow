<!-- Created once by sp init. This file is yours; sp never overwrites it. -->
# This project's rules

Constraints that hold in **this** project and nowhere else. `sp` creates this file once and
never touches it again, so it is safe to write here.

## What belongs here

Things an AI session would otherwise get wrong, and that no general rule covers:

- domain constraints — *"never italicise anything that could contain Hebrew text"*
- data facts that change what is correct — *"this dataset's identifiers are not unique"*
- local conventions — naming, layout, what must never be regenerated
- prohibitions with a reason — what went wrong before, so it is not repeated

Write the reason, not only the rule. A constraint whose *why* is missing gets argued with, or
quietly dropped when it becomes inconvenient.

## What does not belong here

- **General practice** — how to run pipelines, how to write prompts, how to use git. That is in
  `sp/rules.md` and in the shipped disciplines, and a copy here would drift from them.
- **What is in flight** — that is `project/TODO.md`.
- **Description** — what this project *is* goes in `project/overview.md`.

## The rules

1. **A test for step behaviour goes through the object model, not a raw dict.** Build a `Step`
   or `Pipeline` from `llmflow.model` and exercise the handler through it.

   The API is generated from `pipeline_schema`: `step_keys()` unions the common keys with every
   per-type branch, so a new step key becomes an attribute with no code written. That is why a
   key which reaches the runner but is absent from the API — or sits in the API and is never
   read by the runner — is a real defect rather than a cosmetic one.

   A test that hands `run_*_step` a hand-written `{"type": ..., ...}` dict cannot see either
   case, because the dict satisfies both sides by construction. Two guards already close the
   loop between the *declarations* — `test_pipeline_model.py` for schema ↔ object model and
   `test_schema_covers_runner_keys.py` for schema ↔ runner. This rule is about the third edge:
   the tests that *exercise* a step should use the surface a consumer uses.

   **Direct calls remain right for pure helpers.** `resolve_citation`, `normalize_greek` and
   `map_reference` take values rather than steps; routing them through a `Pipeline` would test
   the pipeline instead of the helper.
