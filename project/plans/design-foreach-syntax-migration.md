# Design: migrate for-each / window to `for`/`in`, remove aliases

**Date:** 2026-07-11
**Status:** Proposed — awaiting Captain review
**Decision:** Option 3 — converge on the XQuery-style `for`/`in` as the **only** loop syntax;
remove `item_var`/`input`/`over`/`as` entirely (no aliases).
**Breaking:** yes. Coordinated across this repo + 7 registered consumer repos.

## Motivation

The JSON Schema (`pipeline.schema.json`, added in `f34aa1b`) declares `for`/`in` as the
loop-step fields and marks `item_var`/`input`/`over`/`as` as *"Deprecated: use for/in."* But
**no runtime code reads `for`/`in`** — `for_each.py`/`window.py`/`linter.py` read only
`item_var`/`input`/`over`. So the schema (and the VS Code autocomplete it powers) instructs
users to write `for:`/`in:`, which the runtime **silently ignores**: `input` defaults to `[]`,
`item_var` to `"item"`/`"window"`, and the loop iterates over nothing. A silent-failure trap.

Rather than keep two spellings, we make `for`/`in` real and drop the rest. One syntax, schema
and runtime finally agree. Doing it now is cheap: all pipelines are the Captain's, all on one
machine, all in the registry — a bounded, known set. The cost only grows with users.

## Canonical syntax (after)

```yaml
- type: for-each
  in: "${list}"        # was: input
  for: item            # was: item_var
  order-by: ...        # unchanged
  group-by: ...        # unchanged
  parallel: N          # unchanged
  steps: [...]

- type: window
  in: "${list}"        # was: input (or over)
  for: chunk           # was: item_var
  size / stride / ...  # unchanged
  steps: [...]
```

## Blast radius (measured via the registry)

**Consumer repos — 7 projects, ~25 sites:**

| Project | for-each | window |
|---|---:|---:|
| ears-to-hear | 11 | 0 |
| discourse-flow | 4 | 1 |
| image-scene-descriptions | 3 | 0 |
| discourse-flow-hebrew | 2 | 1 |
| macula-lxx-greek | 1 | 0 |
| semdom-greek-lexicon | 1 | 0 |
| storytelling-dictionary | 1 | 0 |

**This repo (core):**
- Runtime: `for_each.py:266,268`; `window.py:305,312`
- Linter: `linter.py:568` (reads `item_var`), known-keys list `89–102`, `_build_available_context` `527–542`
- Schema: for-each props `254–272` (drop `item_var`,`input`,`as`); window props `323–349` (drop `item_var`,`input`,`over`,`as`); keep/make required `for`,`in`
- Example pipelines: 8 files using `item_var:`
- Tests: 25 files / ~148 lines referencing `item_var`
- Docs: `docs/llmflow-language.md` (for-each example + the currently-uncommitted `window` section), `docs/llmflow-language-quickref.md`

## Design decisions

1. **Fail loud, not silent.** After aliases are removed, a loop step whose loop var / list
   cannot be resolved must **raise a clear error**, not default to empty iteration. Both:
   - Runtime: `for_each`/`window` raise if `for`/`in` are absent (no silent `[]`/`"item"`).
   - Linter: `item_var`/`input`/`over`/`as` become **unknown keys** → `sp lint` flags any
     un-migrated pipeline. This is the safety net that makes the migration detectable.
2. **Internal names unchanged.** The Python locals may stay named `item_var` etc.; only the
   *step key* that is read changes (`step.get("item_var")` → `step.get("for")`).
3. **`in`/`inputs` never confused.** The loop list key is singular `input:` → `in:`. Prompt
   `inputs:` (plural) is unrelated and must never be touched.

## Work breakdown

### Phase 1 — Core engine (this repo), TDD
1. Update `for_each.py`, `window.py` to read `for`/`in`; remove `item_var`/`input`/`over`
   fallbacks; raise on absence.
2. Update `linter.py`: known-keys list (`for`/`in` in, aliases out), `item_var` read site,
   `_build_available_context`.
3. Update `pipeline.schema.json`: remove deprecated alias properties; require `for`/`in`.
4. Migrate the 8 example pipelines + 25 test files (write/adjust tests first per TDD).
5. Update `docs/llmflow-language.md` (+ quickref) to `for`/`in`; commit the held language-doc
   edits reworded accordingly.
6. Full suite green; `sp lint` clean on example pipelines.

### Phase 2 — Codemod
A block-aware transformer (ruamel.yaml to preserve comments/formatting), applied per repo:
- Walk every step; for `type in {for-each, window}`: rename `item_var`→`for`, `input`→`in`,
  `over`→`in`; drop `as`.
- Leave all other keys (including prompt `inputs:`) untouched.
- After transform: run `sp lint` on every pipeline; must be clean (unknown-key check confirms
  no alias survived).
Ship the codemod in-repo (e.g. `scripts/migrate_foreach_syntax.py`) so consumers can run it.

### Phase 3 — Consumer repos (7)
Per repo, in lockstep with however it consumes the engine (vendored `LLMFlow/` subdir vs
`pip install scripture-pipelines`):
- Bump/point to the alias-free engine version.
- Run the codemod on its pipelines.
- `sp lint` all pipelines clean.
- Own branch + commit/PR per repo (start with ears-to-hear — 11 sites, the largest).

## Sequencing & versioning

- **After 0.2.1.20** (already released). This is the next unit of work.
- **Version: 0.2.1.21 (4th-component bump).** Breaking, but the Captain's call (2026-07-11):
  with no significant user base yet, the small bump is acceptable and keeps numbering
  consistent. The CHANGELOG entry must still clearly mark it **breaking** (the syntax change).
  (Relates to #153 versioning policy, which can revisit this once there are users.)
- Order: Phase 1 lands + releases the new engine; then Phase 3 migrates each consumer against
  it. A consumer must not pick up the alias-free engine before its pipelines are migrated —
  but the fail-loud linter/runtime guarantees any miss is caught immediately, not silent.

## Risks

- **R1 — a consumer updates the engine before migrating.** Mitigated by fail-loud (Design 1):
  the step errors / lint fails rather than iterating empty.
- **R2 — codemod reformats YAML.** Mitigated by ruamel.yaml round-trip (preserves comments);
  review the diff per repo.
- **R3 — `input:` used as a non-loop key somewhere.** The codemod only renames within
  `for-each`/`window` steps, so other `input:`/`inputs:` are safe.

## Out of scope
- Other schema deprecations (e.g. `input`→`inputs` at schema:810) — separate concern.
- The consumer-coupling audit findings (`project/audits/2026-07-09_consumer-coupling_*`).
