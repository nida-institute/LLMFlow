# HANDOFF — 2026-10-06

## ▶ NEXT ACTION

**Confirm the staged commit landed.** Written while one commit was staged on `dev` against
`3e5b7de`, message in `tmp/commit-1.txt`, for the Captain to run. If `git log -1` still shows
`3e5b7de`, the commit is his to make — do not make it. Once it exists: `git show HEAD`, check
its files against the list below, then delete `tmp/commit-1.txt` by name.

After that, the next work is the next open item in **`project/TODO.md` → 🚢 THE NEXT RELEASE**.

---

## Active threads

### 1. The staged commit — #261 and the starter's cost, together (the Captain's choice)

- **#261, lint preflights resources:** `src/llmflow/utils/resource_preflight.py`, the offers in
  `cli.py` (`_offer_resources`, `_register_from_catalog`, `TermsNotAgreed`), `LintResult.resources`.
  Plan: `project/plans/plan-resource-preflight.md`.
- **Starter cost:** `format: analysis` (`utils/analysis_format.py`), `frequency_cutoff`, JSON and
  Unicode to models and disk, English context for parallels, and a value filled only under
  `# INPUT DATA` (`steps/llm.py`, `_input_data_segments`). Plan:
  `project/plans/plan-starter-cost.md`, measurements in §5a–§5b.
- **Verify:** `hatch run pytest tests/ -q -m "not integration" -p no:randomly --deselect
  tests/test_helm_sync.py --deselect tests/test_portable_skills.py` → 6,059 passed, 1 failed
  (`test_binary_bundles_its_data` — the parallel-passages wheel entry, deferred by the Captain to
  the release PR). With the Helm tests, 4 more fail: Helm design, his call.

### 2. Measured runs in `~/github/nida-institute/playground/sp-example`

MAT 19:1-11: original ~$1.00 → **$0.1281** with gpt-4.1 (ruled to stay, 2026-10-06).
gpt-4.1-mini invented counts and was not adopted. The checks covered coverage and counts only;
**the quality of the explanations and of the significance output is the Captain's to judge**:
`outputs/` (original), `outputs/labelled-4.1/`, `outputs/labelled-mini/`. The directories
`after-4.1/` and `fixed-*` predate fixes — ignore them. `pipelines/readers-guide-mini.yaml` there
is a scratch copy for the comparison, not part of the engine.

---

## In flight / not yet done

| whose | paths |
|---|---|
| **the Captain's — do not stage** | `data/models.json`, `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md` |
| **untracked, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/discourse-flow/` (8 notes, one new 2026-10-05), `collab/human-at-the-helm/`, `scripts/representation-grid/` |
| **stray** | `src/llmflow/templates/project/prompts/parallel-significance.gpt~` — not made this session |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

---

## Decisions

**Awaiting the Captain** (recorded in `plan-resource-preflight.md`):
- **Q6** — what `[A]ll` covers. Built as *install only*; each licence is still asked.
- **§4.4** — a registration made before #252 is offered its licence, nothing downloaded. My
  reading of *"that will help me now with licenses for my registered resources"*; unconfirmed.
- **§2a's three derivations** — conditional resources are warnings; missing analysis paths are
  reported with their command, not offered (nothing declares where Lowfat lives); the CLI makes
  the offers, never the linter.

**Settled — do not reopen:**
- **A value is filled only under `# INPUT DATA`** (his option A). Filling every `{{name}}` sent
  each input once per mention; the significance prompt sent its chapters eight times. The prompt
  discipline still teaches `{{var}}` under VARIABLES, and that is now harmless.
- **Every number in `analysis` is labelled** (`LN 34.22`, `12× in GNT · 83.69%`). Unlabelled, a
  sense number was read as a count — measured, §5a.
- **gpt-4.1 stays** — mini invents counts the contract forbids (§5b).
- **The USJ form is still saved**; `analysis` is what a prompt is handed.

## Do NOT

- **Do not commit, push or merge.** `/stage-commits`: stage by quoted path, message in `tmp/`.
- **Do not `sp run` unasked** — each run needs its own direction. Runs happen in the playground
  with `cd` and the hatch env's `sp`, which the Captain allowed for those runs.
- **Do not regenerate files under `docs/ai-context/sp/` without asking.** This session did twice
  without fresh approval (`command-line.md`, `scripture-representations.md`) and said so.
- **Do not add the parallel-passages dataset to the wheel lists** until the Captain says so.

## Key files & links

- `project/TODO.md` → 🚢 THE NEXT RELEASE (items 8 and 9 are this session's)
- `project/plans/plan-resource-preflight.md`, `plan-starter-cost.md`
- Measuring script (scratch, not committed): the checker used for §5b counted entries and counts
  against `greek-analysis.txt`; rebuild it from §5b's description if needed
