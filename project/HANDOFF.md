# HANDOFF — 2026-10-15

Written against `aa08edc` (one ahead of `origin/dev`, the push the Captain's), for the first of
three commits that follow it: #270, then the public API's missing step types, then the GSP rule.

## ▶ NEXT ACTION

**See which of the three commits exist** — `git log -4 --format="%h %s"` — and `git show` each new
one. They are the Captain's to run, from `tmp/commit-1.txt`, `tmp/commit-2.txt`,
`tmp/commit-3.txt`; delete each by name once its commit exists. Commit 3 waits on **D7**, below.

Then **convert this session's tests to the `sp` CLI**, one file per step, in this order:
`tests/test_lint_refuses_undeclared_types.py`, `tests/test_sdbg_senses.py`,
`tests/test_acai_step.py`, `tests/test_dictionary_step.py`.

---

## Active threads

### 1. Tests drive the `sp` CLI — the Captain, 2026-10-15

He asked "all tests should use the cli API. Do they?" — they do not. Rulings, all A:

- **D1** — drive `sp` in-process with `llmflow.cli.main([...])`; read `sp lint --json`, the
  `saveas` file, `caplog`. Pattern: `tests/test_resource_preflight.py:246`.
- **D2** — a test with no CLI form is dropped (the handler-reached-directly refusals; the
  plugin-constant-versus-`register()` test). The guards stay in the code.
- **D3** — parametrized lists come from `docs/cli-api.json` `step_types`.
- **D4** — the rule is written by extending `the-language-is-the-whole-surface` in
  `data/ai-rules.yaml`; not yet drafted.
- **D5** — the API first listed only 21 types; commit 2 adds the seven built-in plugin types.
- **Scope:** this session's four test files only. The older suite is the same pattern and is
  not in scope.

### 2. The three commits

1. **#270** — `install.sh`, `install.ps1`, `tests/test_install_scripts.py` (8), its
   `CHANGELOG.md` entry, `project/TODO.md`, this file. Verify: `hatch run pytest
   tests/test_install_scripts.py` → 8 passed.
2. **`docs/cli-api.json` lists every step type** — `src/llmflow/cli_api.py`,
   `src/llmflow/file_catalog.py`, `docs/cli-api.json`, `tests/test_cli_api_map.py`, its
   `CHANGELOG.md` entry. Verify: `hatch run pytest tests/test_cli_api_map.py` → 8 passed.
3. **GSP** — `data/ai-rules.yaml` rule `commit-status-is-gsp`, plus `docs/ai-context/sp/rules.md`
   regenerated. Until then `tests/test_ai_rules_single_source.py` has 2 RED.

Full suite on the tree holding all three: 6,391 passed, 27 skipped, the 2 RED above only.

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
`CHANGELOG.md` holds the entries for commits 1 and 2: each is staged alone with
`git apply --cached` from a one-hunk patch under `tmp/`.

## Decisions

**Awaiting the Captain:**
- **D7** — may the AI run `hatch run python tools/update_ai_context.py`? It rewrites
  `docs/ai-context/sp/rules.md`, which needs his explicit yes.
- Whether `sp lint`'s raw traceback on a missing pipeline file is in 0.2.1.30.
- Whether `RELEASE_CHECKLIST.md` §6–7 should say the human runs the merge and the tag push.

**Settled — do not reopen:** D1–D6 above, all A. #270 reads the tag from the
`releases/latest` redirect and prints a refused response (fixes 2 and 3). #272's §7 and D-G to
D-U in `project/plans/design-ears-to-hear-resources.md`.

## Do NOT

- **Write anything in Helm's tree** outside `collab/scripture-pipelines/`.
- **Write to `~/.sp`** — registrations are the Captain's to run.
- **Edit `docs/ai-context/sp/`**, or regenerate it, without his yes (D7).
- **Commit, push, open a PR or merge.** `/stage-commits`.
- **Reply to Ears to Hear, discourse-flow or BibleAquifer unasked.**
- **Do not `sp run` unasked.**

## Key files & links

- `project/TODO.md` → 🚢 THE NEXT RELEASE
- `project/plans/design-ears-to-hear-resources.md`, #272, #270
- `docs/cli-api.json` — the public API the converted tests read
