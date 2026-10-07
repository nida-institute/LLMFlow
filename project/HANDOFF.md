# HANDOFF — 2026-10-07

## ▶ NEXT ACTION

**Confirm the commit that carries this file landed, and that GitHub's Tests run on it is green.**
Written while that commit was being staged on `dev` against `5b1ea3e`, for the Captain to run. If
`git log -1` still shows `5b1ea3e`, the commit is his to make — do not make it. Once it exists:
`git show HEAD`, check its files against the commit message, delete `tmp/commit-1.txt` by name,
then after his push:

    gh run list --workflow test.yml --branch dev --limit 1

**Green is the expected result and has not yet been seen** — the first run with the Helm
exemptions and the wheel entry in place. If it is red, the failure is new and worth reading:
`gh run view <id> --log-failed`.

After that, the release mechanics in **`project/TODO.md` → 🚢 THE NEXT RELEASE** and
`project/RELEASE_CHECKLIST.md`.

---

## Active threads

### 1. The commit being staged — everything since `5b1ea3e`

- **Item 10, a green build:** Helm checks `xfail(strict=True)` (`HELM_EXEMPT` in
  `tests/test_portable_skills.py`); `data/parallel-passages.json` in the wheel and both Nuitka
  commands; `RELEASE_CHECKLIST.md` §3 requires a green `test.yml` on `dev` before the PR.
- **#176 / option A:** the header is stripped before the model call; `description` is the
  prompt's Markdown documentation; `# VARIABLES` refused; lint warns on an input `description`
  does not name. Design: `project/plans/design-prompt-description.md`.
- **`/stage-commits`** now brings the handoff and changelog up to date before grouping (its new
  Step 2) — the Captain's direction 2026-10-07: *"handoff and change log need to be updated
  first."*
- **Verify:** `hatch run pytest tests/ -q -m "not integration" -p no:randomly`, nothing deselected
  → 6,181 passed, 24 skipped, 4 xfailed, 0 failed at the last full run (before the CHANGELOG and
  skill edits, which tests also cover and pass).

### 2. Notes written into the consumer repos, uncommitted there

`discourse-flow/collab/sp/` and `ears-to-hear/scriptorium/collab/sp/`,
`2026-10-06-description-is-for-people-and-the-model-reads-only-the-prompt.md`. Theirs to commit.
Discourse-flow's `tests/test_prompt_structure.py` requires `# VARIABLES` and will disagree with
lint after it upgrades; the note says so.

---

## In flight / not yet done

| whose | paths |
|---|---|
| **the Captain's — do not stage** | `data/models.json`, `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its template twin, `project/open-decisions.md` |
| **untracked, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/`, `scripts/representation-grid/` |
| **stray** | `src/llmflow/templates/project/prompts/parallel-significance.gpt~` |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**
`~/.sp`'s copies of the changed skills and discipline refresh with `sp init --update`; this
repo's `.claude/skills/` copies are git-ignored and were synced by hand.

---

## Decisions

**Awaiting the Captain** — `project/TODO.md` → 🚢 THE NEXT RELEASE lists them: `data/models.json`
(still gives gpt-4.1 a 128k window; it is 1M), whether `sp-language.md` ships, #261 Q6 / §4.4 /
§2a, the `license_url` issue draft, the quality of the cheaper starter.

**Settled — do not reopen:**
- **Helm is an exemption in this release**; the next release is Helm and Ears to Hear support.
- **Nothing for maintainers reaches the model** — header stripped, `description` is
  documentation, `# DATA SOURCES` says how to read an input and not where it came from.
- **A value is filled only under `# INPUT DATA`**; every number in `analysis` is labelled;
  gpt-4.1 stays. Reasons: `plan-starter-cost.md` §5a–§5b.

## Do NOT

- **Do not commit, push or merge.** `/stage-commits` — now with its Step 2 first.
- **Do not `sp run` unasked.**
- **Do not regenerate files under `docs/ai-context/sp/` without asking.**
- **Do not open the release PR before `test.yml` is green on `dev`** — `RELEASE_CHECKLIST.md` §3.

## Key files & links

- `project/TODO.md` → 🚢 THE NEXT RELEASE, and "The release after this one"
- `project/plans/design-prompt-description.md`, `plan-resource-preflight.md`, `plan-starter-cost.md`
- `collab/ears-to-hear/2026-10-06-acai-sdbg-and-the-tyndale-bible-dictionary.md` — next release's
  request
