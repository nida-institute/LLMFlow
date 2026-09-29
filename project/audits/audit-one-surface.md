# Audit — can the one-surface guard also police the engine's own tests?

Rolling record. Findings carry their own dates; the file is rewritten in place.

## The question, and where it came from

`project/TODO.md`, goal 2, box "Is it guardable?": whether
`tests/test_shipped_context_names_one_surface.py` can be extended to *"refuse a test that
imports an internal named only in `index.json`"*. The box says this is **worth asking before
assuming it cannot**, which is why it was measured rather than answered from the shape of things.

## What was examined, and how — 2026-09-29

**Stated in full, because a finding is usable only if the reader knows how far to trust it.**

| | |
|---|---|
| examined | `tests/` — file-level presence of four patterns, by `grep -rlE` |
| how | four greps, listed below with their results. No file was read in full |
| **not** examined | what each matching file *does* with the import; whether a match is a step-behaviour test or a helper test; `tests/integration/` beyond what the recursive grep reached |
| would raise confidence | reading the 26 files and classifying each as dict-passing or `Step`-passing. That is the number a ratchet would actually pin, and it is not yet measured |

**The four measurements.**

1. Test files importing the package at all — `grep -rln "^from llmflow\|^import llmflow\|from llmflow\."` → **~230 files** of roughly 260.
2. Test files calling a step handler directly — `grep -rlE "run_[a-z_]+_step\("`, over eleven
   enumerated handler names → **26 files**.
3. Test files using the object model — `grep -rlE "^from llmflow import .*(Pipeline|Step|load_pipeline)"` → **14 files**.
4. Test files passing a dict *literal* at the call site — → **1 file**,
   `tests/test_basex_database_binding.py`. The other 25 pass a variable, so a guard keyed on
   call-site syntax would see almost none of them.

**A correction to an earlier query in the same session.** Measurement 3 first returned **0**,
from a query for `from llmflow.model import` and `llmflow.model.Step`. Nobody writes those — the
package root re-exports, and the real form is `from llmflow import Pipeline, Step, load_pipeline`.
A zero from a wrong query reads exactly like a zero from a true absence, which is the failure
`check-the-source-not-the-rendering` names: a derived set that silently becomes empty.

**Against #250 — resolved 2026-09-29, and it was a false comparison.** That issue counts **29
against 12**; this audit counts **26 against 14**. They are not the same measurement, which the
issue's own printed commands settle:

| | #250, 2026-09-22 | here, 2026-09-29 |
|---|---|---|
| handlers | four names, **any mention** | eleven names, **call sites only** |
| object model | `from llmflow.model import\|llmflow.model\|load_pipeline` | `^from llmflow import .*(Pipeline\|Step\|load_pipeline)` |

Mentions are always at least as many as call sites, which is the direction the two figures go.
One flaw in each: #250's object-model pattern matches **`load_pipeline_config`** as a substring,
so its 12 includes files importing the YAML loader rather than the object model; and the pattern
here requires an import line to begin `from llmflow import`, so it misses `import llmflow`
followed by `llmflow.Pipeline`, and any multi-line import.

**Neither number is the problem, and #250 says so of its own**: *"The 29 above is an upper bound
on the problem, not the problem"* — rule 1 carves out pure helpers (`resolve_citation`,
`normalize_greek`, `map_reference`, and `_build_windows_token`, which takes items and a budget
rather than a step). So a ratchet must pin a **classified** count, not either grep. That is the
measurement neither this audit nor #250 has taken.

This entry replaces one that recorded the difference as unexplained and guessed at drift or a
short name list. Both guesses were wrong; the commands were printed in the issue the whole time.

## Finding — not guardable as posed, for three reasons

**1. The premise does not hold in this repository.** ~230 of ~260 test files import `llmflow`,
and that is correct: `the-language-is-the-whole-surface` binds what a *project* may build against,
not what the engine's own tests may use. A guard refusing "a test that imports an internal" would
refuse almost the entire suite.

**2. `index.json` does not select a meaningful subset.** It lists 881 functions across 93
modules — close to everything the engine has. "Named only in `index.json`" is therefore not a
filter; it is a synonym for "in the codebase".

**3. It is the wrong guard to extend.** `test_shipped_context_names_one_surface.py` reads
*shipped* material — what a project receives. Policing the engine's own tests is
`docs/ai-context/project/rules.md` rule 1, a different rule with a different subject. Folding
them together would put two rules in one guard, and a reader of a failure could not tell which
had been broken.

## Proposed fix — a ratchet, with precedent already in the tree

Rule 1 is currently attention only, and `audits-pattern.md` rule 6 asks for the opposite:
*"prefer a red test to a written rule."*

`tests/test_docstrings_say_what_not_why.py` is the precedent. It carries a **measured backlog of
49 files that predate its rule, and forces that backlog to shrink rather than persist**. The same
shape applies: pin the count of test files calling a step handler directly, and fail when it
grows. A test added the old way then costs a deliberate edit to the pinned number, which is where
the conversation belongs.

**What must be settled before building it**, and none of it is an audit's to decide:

- the number to pin — measurement 2 gives 26, but the classification in "not examined" above is
  what a ratchet should really count;
- whether the ratchet counts files or call sites;
- whether it belongs beside rule 1's other guards or in the one-surface file.

**Not built.** A guard is a new test and needs its own authorization.
