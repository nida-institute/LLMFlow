# HANDOFF — 2026-10-15

Written against `d667420` (#270, level with `origin/dev`), for the three commits that follow it:
the public API's missing step types, the GSP rule, and the tests rule.

## ▶ NEXT ACTION

**See which of the three commits exist** — `git log -4 --format="%h %s"` — and `git show` each new
one. They are the Captain's to run, from `tmp/commit-2.txt`, `tmp/commit-3.txt`,
`tmp/commit-4.txt`, staged one at a time; delete each by name once its commit exists.

Then **convert #272's test files to the `sp` CLI**, one file per step, in this order:
`tests/test_lint_refuses_undeclared_types.py`, `tests/test_sdbg_senses.py`,
`tests/test_acai_step.py`, `tests/test_dictionary_step.py`.

---

## Active threads

### 1. The three commits after `d667420`

2. **`docs/cli-api.json` lists every step type** — `src/llmflow/cli_api.py`,
   `src/llmflow/file_catalog.py`, `tests/test_cli_api_map.py`, its `CHANGELOG.md` entry, this
   file. **`dev` is RED at `d667420` until this lands** — see the landmine below. Verify: `hatch
   run pytest tests/test_cli_api_map.py` → 8 passed.
3. **GSP** — `data/ai-rules.yaml` rule `commit-status-is-gsp`, `docs/ai-context/sp/rules.md`
   regenerated with the Captain's yes. Verify: `hatch run pytest tests/test_ai_rules_single_source.py`.
4. **Tests drive `sp`** — `docs/ai-context/project/rules.md` rule 1 (written by the AI at the
   Captain's word), `tools/index_signatures.py`, `tests/test_internals_map_declares_itself.py`,
   `docs/python-api.md`, `project/TODO.md` GOAL 2. Verify: `hatch run pytest
   tests/test_internals_map_declares_itself.py`.

Full suite on the tree holding all three: 6393 passed, 27 skipped.

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

**Awaiting the Captain:** whether #250 is retitled or recounted under the new rule 1; whether
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
