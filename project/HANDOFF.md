# HANDOFF — 2026-10-15

Written against `dd58f4f`. This session's commits: `d667420` #270, `2b418f6` the public API's
step types, `dc934b7` GSP, `2faed54` `docs/ai-context/project/rules.md` rule 1 — tests drive
`sp`, `dd58f4f` this file's citations.

## ▶ NEXT ACTION

**Convert #272's test files to the `sp` CLI**, one file per step:
1. `tests/test_lint_refuses_undeclared_types.py` — **converted**, in the commit after `dd58f4f`:
   31 pass through `sp lint --json`; each claim shown to fail when broken.
2. `tests/test_sdbg_senses.py`, 3. `tests/test_acai_step.py`, 4. `tests/test_dictionary_step.py`
   — not started.

---

## Active threads

### 1. `2faed54` was RED

Its handoff cited a project rule by number without naming its file, which
`tests/test_rules_are_cited_by_id.py` refuses — the full suite had run before the handoff was
rewritten, not after. This file's citations are fixed in
the commit after it. Verify: `hatch run pytest tests/test_rules_are_cited_by_id.py`.

### 2. Tests drive the `sp` CLI — the Captain, 2026-10-15

Rulings, all A: **D1** drive `sp` in-process with `llmflow.cli.main([...])`, read `sp lint --json`,
the `saveas` file, `caplog` (pattern: `tests/test_resource_preflight.py:246`). **D2** a test with
no CLI form is dropped; the guards stay in the code. **D3** parametrized lists come from
`docs/cli-api.json` `step_types`. **D5** that list now holds all 28. **D8** the object model no
longer counts — the rule lives in `project/rules.md` rule 1, not the shipped rules. The older suite
is backlog, in `project/TODO.md` GOAL 2.

### 3. 0.2.1.30 — `project/TODO.md` → 🚢 THE NEXT RELEASE

Item 5 (version skew, design first) is not started.

---

## In flight / not yet done

| whose | paths |
|---|---|
| **not updated, deliberately** | `src/llmflow/templates/project/docs/ai-context/sp/scripture-representations.md` — its copy under `docs/ai-context/sp/` must match, and is not the AI's to regenerate |
| **pre-existing** | `ruff` I001 import order in `src/llmflow/runner.py` and `src/llmflow/utils/linter.py` |
| **modified, not this session's** | `docs/ai-context/project/data-sources.md`, `project/open-decisions.md` |
| **untracked here, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/`, `scripts/representation-grid/` |
| **`~/.claude`** | 2 uncommitted files — reported, diff offered, not reviewed |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

## Decisions

**Awaiting the Captain:** whether #250 is retitled or recounted under the new
`project/rules.md` rule 1; whether
`sp lint`'s raw traceback on a missing pipeline file is in 0.2.1.30; whether
`RELEASE_CHECKLIST.md` §6–7 should say the human runs the merge and the tag push.

**Settled — do not reopen:** D1–D9, all A. D9: `d667420` stays as pushed; commits 2 and 4 say in
their messages that their generated files landed there. #272's §7 and D-G to D-U in
`project/plans/design-ears-to-hear-resources.md`.

## Do NOT

- **Stage anything while a generated file's source sits changed in the tree.**
  `tools/hooks/pre-commit` regenerates `docs/index.json` and `docs/cli-api.json` from the working
  tree and `git add`s them to whatever is being committed. That is how `d667420` (#270) came to
  carry commit 2's `cli-api.json` and commit 4's `index.json` line.
- **Write anything in Helm's tree** outside `collab/scripture-pipelines/`.
- **Write to `~/.sp`**, or edit `docs/ai-context/` without the Captain's word.
- **Commit, push, open a PR or merge.** `/stage-commits`.
- **Reply to Ears to Hear, discourse-flow or BibleAquifer, or touch #250, unasked.**
- **Do not `sp run` unasked.**

## Key files & links

- `project/TODO.md` → 🚢 THE NEXT RELEASE, and GOAL 2
- `docs/ai-context/project/rules.md` rule 1; `docs/cli-api.json`
- `project/plans/design-ears-to-hear-resources.md`, #272
