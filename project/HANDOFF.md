# HANDOFF — 2026-10-05

## ▶ NEXT ACTION

**#252** — the next item in **`project/TODO.md` → 🚢 THE NEXT RELEASE**, in the order the
Captain set on 2026-10-02 (#244 done, then #252, then #261). Its plan is
`project/plans/plan-terms-on-download-and-register.md`; read it and the TODO entry before
proposing anything.

Verify the starting point: `git status --short --branch` → `## dev...origin/dev`, with
`git log -1` at the commit that carries this file (its parent is `70e8a7b`).

---

## Active threads

### 1. #244 — the starter example — committed and pushed at `70e8a7b`

The Captain ran it in `playground/sp-example` and ruled 2026-10-05: *"The sample output looks
great, and examples are now done."* Evidence: `project/plans/plan-starter-examples.md`.

**One loose end, deferred by the Captain to the release PR:** `data/parallel-passages.json` is
not in `pyproject.toml`'s force-include or `.github/workflows/build.yml`'s data lists — two lines,
beside the `lemma-frequency-*` entries. Until then one test is red.

**Verify.** `hatch run pytest tests/ -q -m "not integration" -p no:randomly` → 6,038 passed,
5 failed at `70e8a7b`: `test_helm_sync` ×3 and `test_portable_skills` (Helm design), and
`test_binary_bundles_its_data` (the deferred entry above).

---

## In flight / not yet done

Nothing of this session's is uncommitted beyond this file and `project/TODO.md`. Not staged, and
not this session's:

| whose | paths |
|---|---|
| **the Captain's — do not stage** | `data/models.json`, `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md` |
| **untracked, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/discourse-flow/` (7 notes), `collab/human-at-the-helm/` |
| **deliberately unstaged** | `scripts/representation-grid/{cells/,grid.json,grid.tsv}` |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

---

## Decisions settled this session — do not reopen

- **Frequency is `include: [frequency]` on `type: scripture`**, from tables generated once and
  committed in `data/`. No query, and no BaseX, at run time — the Captain rejected a run-time join
  twice: *"we generate these files, once, and save them in our repository."*
- **The parallel-passages database is a committed dataset**, read for every resource;
  `parallel_passages_path` and `--parallel-passages-path` are gone (his option A). CC BY-SA 4.0,
  attributed in `NOTICE`.
- **`counted.text` is a closed enum** (BHS, Rahlfs, UBSGNT5), extended when an edition is added.
- **The example uses discourse-flow's model settings** — `gpt-4.1`, 32,768 tokens, 0.35, 300 s.
  gpt-4o overflowed; gpt-5 returned nothing usable.
- **Cut-offs are a rank among lemmas**, defaults Greek 80, Hebrew 90.

## Do NOT

- **Do not commit, push or merge.** `/stage-commits`: stage by quoted path, message in `tmp/`,
  review with `git diff --cached` — never `--stat`.
- **Do not add the parallel-passages dataset to the wheel lists** until the Captain says so.
- **Do not edit `data/models.json`** — his uncommitted file, though its `gpt-4.1` window is wrong.
- **Do not run `sp run`** unasked.

## Key files & links

- `project/TODO.md` → 🚢 THE NEXT RELEASE, and the untriaged findings list beneath it, which
  gained eleven engine findings this session
- Issues filed this session: **#267** (whole sentences, built), **#268** (Septuagint, deferred)
