# HANDOFF — 2026-10-07

## ▶ NEXT ACTION

**Confirm the fix commit landed, then that GitHub's Tests run on it is green.** Written while it
was being staged on `dev` against `065bf74`, for the Captain to run; if `git log -1` still shows
`065bf74`, the commit is his to make — do not make it. Once it exists: `git show HEAD`, delete
`tmp/commit-2.txt` by name, then after his push:

    gh run list --workflow test.yml --branch dev --limit 1

`065bf74` was red on CI (run 37710452936) for one reason: `sp init --update` had overwritten
`docs/ai-context/sp/rules.md` with the consumer version before it was staged. The fix
regenerates it with `tools/update_ai_context.py`; the defect itself is in `project/TODO.md` →
🚢 THE NEXT RELEASE, untriaged. **Do not run `sp init --update` in this repo until it is fixed**
without regenerating `rules.md` afterwards.

After that, the release mechanics in **`project/TODO.md` → 🚢 THE NEXT RELEASE** and
`project/RELEASE_CHECKLIST.md`.

---

## Active threads

### 1. Committed in `065bf74` — the workshop rulings and the models work

- **The workshop collab's rulings**, `collab/scripture-pipelines-workshop/2026-10-07-shipped-files-disagree-on-issues-commits-and-heredocs.md`.
  Untracked; it says it dies when its change lands — the Captain has not yet said whether to
  delete it or keep it.
  - **The agent may create issues** — rule `agent-may-file-issues` (replaces
    `issues-need-approval`). The note's ruling A said the opposite; the Captain reversed it.
  - **Commit, push, pull request and merge are the human's** — `commit-authority` (rulings B, F).
  - **No heredocs** — `inline-code-goes-in-a-file` (D).
  - **`/commit-ready` fits any project** — reads commands from `CLAUDE.md` and CI (C).
  - **`/load-context` reads `project/HANDOFF.md`** and checks its sha against `HEAD` (E).
  - **`release` ships nowhere** — now `.claude/skills/release/`, tracked by a `.gitignore`
    exception; `RETIRED_SKILLS` in `src/llmflow/cli_utils.py` removes it from `~/.sp/skills/` and
    never copies it into a project. An existing project copy stays until removed by hand.
- **Earlier this session, same commit:** `sp models --update` menu grouped by family;
  `data/models.json` gpt-4.1 limits and `gpt-6-astra` in the gpt-5 patterns (the Captain's);
  unknown OpenAI model names fall back to the direct call (`llm_runner.py`); version 0.2.1.29.
- **Verify:** `hatch run pytest -qq --tb=short -rf` → 6,247 passed, 26 skipped, 12 xfailed,
  1 failed — `tests/integration/test_mcp_batch_calls.py::test_single_batch_call`, a read timeout
  against the remote MCP server, not this change.

### 2. Helm parity for the changed shared files — next release

`github-authority.md`, `workflow.md`, `authorize`, `commit-ready`, `load-context` are in
`EXEMPT_KEYS` (`tests/test_helm_sync.py`). Recorded in `project/TODO.md` under "The release after
this one".

---

## In flight / not yet done

| whose | paths |
|---|---|
| **untracked, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/` (except as above), `scripts/representation-grid/` |
| **the Captain's, by hand** | delete `scripture-pipelines-workshop/.claude/skills/release/` — he said he would |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**
`CLAUDE.md` is git-ignored here (`.gitignore:82`); its two inline-code lines were refreshed by
`sp init --update` and by hand, and appear in no diff.

---

## Decisions

**Awaiting the Captain** — `project/TODO.md` → 🚢 THE NEXT RELEASE.

**Settled — do not reopen:**
- **The agent may create issues in the project it works in**; an issue on another
  organisation's repository is his decision. Reversal of the collab's ruling A, 2026-10-07.
- **Ruling F is his** — the human opens pull requests.
- **Urgency Injection stays** in `drift-patterns.md` as written.
- **Helm is an exemption in this release.**

## Do NOT

- **Do not commit, push, open a PR or merge.** `/stage-commits`.
- **Do not `sp run` unasked.**
- **Do not regenerate files under `docs/ai-context/sp/` without asking.**
- **Do not edit another repository** — the workshop's stale `release` copy is the Captain's to delete.

## Key files & links

- `project/TODO.md` → 🚢 THE NEXT RELEASE, and "The release after this one"
- `data/ai-rules.yaml` → `agent-may-file-issues`, `commit-authority`, `inline-code-goes-in-a-file`
- `.claude/skills/release/SKILL.md`
