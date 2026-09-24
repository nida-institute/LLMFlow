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

2. **What we say to another project is the Captain's.** An AI drafts a collab note, a
   reply or an issue body when asked, and shows it in full before it is sent. It does
   not record in any document what a reply "must" contain, what another project "needs
   to know", or what they should be told next — those are the Captain's calls about a
   relationship he holds and the AI does not.

   Filed 2026-09-13 after a session wrote "that reply must carry §3.1" into a design
   document, converting the Captain's observation into a directive. The harm is that a
   plan is read later as authorization: a future session finds the sentence, cannot tell
   it from a ruling, and sends something nobody approved.

3. **Prefer a meaningful phrase to a new noun.** Coining a term obliges everyone who reads
   the project — people and models alike — to learn and maintain a definition. A phrase
   costs nothing and cannot drift from a meaning it never had. Coin a noun only when the
   phrase is genuinely unwieldy at the frequency it appears, and then define it where it
   is introduced.

   The Captain, 2026-09-14: *"Any time we create new vocabulary instead of a meaningful
   phrase, we have to define it, and both LLMs and people need to learn it. Avoid
   multiplying vocabulary where not needed."*

   Filed after a session coined `absorbed`, `refused`, `foreign`, `partition`,
   `clean run`, `gap` and `interleaved` for one small feature. `interleaved` silently
   carried two different meanings for hours and propagated into two documents, a generator
   and four worked examples before the Captain caught it. Every one was replaced by a
   phrase or deleted, and nothing was lost.

   This is the checkable form of the Terminology Capture countermeasure in
   `drift-patterns.md`. Of any coined noun, ask: **what phrase would this replace, and is
   the noun earning its keep?** An AI is especially prone to this because naming a concept
   feels like understanding it.
