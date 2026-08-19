# HANDOFF — 2026-08-19 (evening)

Supersedes the 2026-08-19 (morning) handoff entirely. **That file's NEXT ACTION — "merge release
PR #199" — is now wrong.** See decision 3 below.

---

## ▶ NEXT ACTION — step 4 of the HATH plan: split the conventions

`project/plans/design-hath-parity.md` §7 step 4. Steps 1–3 are done and committed (`a2de0c5`).

Break `~/.sp/conventions/sp-workflow.md` into its general and engine-specific halves, and classify
the rest per §4 of that plan. The classification is already written and ruled; this is execution.

**Verify where you are:**

```bash
hatch run pytest tests/test_portable_skills.py   # expect 21 passed
git log --oneline -1                              # expect a2de0c5
```

**Do not push.** See "Do NOT" below.

---

## Active threads

### 1. human-at-the-helm#1 — bring HATH to current maturity. **In flight, steps 1–3 done.**

- **Goal (Captain, 2026-08-19):** *"our ai context here is now more advanced than the original
  HATH, by quite a bit. I want HATH to have the same level of maturity, without whatever is
  specific to Scripture Pipelines."*
- **State:** plan written and fully ruled (`project/plans/design-hath-parity.md`); guard tests
  written (step 2); five skills generalized (step 3). All committed in `a2de0c5`.
- **Next step:** step 4, the conventions split — the NEXT ACTION above.
- **Verify:** `hatch run pytest tests/test_portable_skills.py` → 21 passed. `git show a2de0c5 --stat`.

**Remaining sequence** (§7 of the plan): 4 conventions split → 5 manifest, then `/install`, then
`/hath-check` → 6 sync mechanism → 7 manual acceptance in a real Claude Code session.

### 2. Release 0.2.1.24 — **6 commits added today, unpushed.**

- **State:** `dev` is **28 ahead** of `origin/dev`. PR #199 is `OPEN` / `CLEAN`, head still
  `cb72cb7` — i.e. the PR does **not** contain today's work.
- **Next step:** nothing, until the Captain says the release contents are complete.
- **Verify:** `git log --oneline origin/dev..dev | wc -l` → 28. `gh pr view 199 --json mergeStateStatus`.

Today's commits, all targeting 0.2.1.24:

| SHA | |
|---|---|
| `bc87b00` | fresh clone gets skills; `sp doctor` repairs; file catalog as data (#204) |
| `4f7a2cf` | install instructions named a package not on PyPI (#33) |
| `f420e1c` | Python API listed in this repo's AI context (#175) |
| `0e5f350` | unresolved `${var}` in a write path raises instead of becoming a directory |
| `538f304` | `commit-ready` gates the GUI's TypeScript suite (#206) |
| `a2de0c5` | methodology skills carry no engine vocabulary (HATH#1) |

Suite: **2705 passed, 13 skipped** (was 2621 at session start).

### 3. #204 fresh-clone onboarding — **substantially done, two pieces left.**

- **State:** `sp init` now copies skills into `<repo>/.claude/skills/`, writes a `.gitignore` when
  absent, and prompts for nothing. `sp doctor` repairs sp-owned files that are missing or diverged.
  The file catalog is `data/file-catalog.yaml` — data, not code.
- **Left:** (a) the `_is_generated` call sites still decide ownership by marker string rather than
  by the catalog — the rest of D7; (b) the manual acceptance step, a real Claude Code session
  against a fresh clone running `/load-context`. Only the Captain can do (b).
- **Verify:** the fresh-`HOME` harness in the plan's D8 section, or
  `hatch run pytest tests/test_catalog.py tests/test_doctor.py tests/test_init_noninteractive.py`.

### 4. ears-to-hear — **two documents written, uncommitted by the Captain's instruction.**

- `scriptorium/collab/sp/2026-08-06-public-api-for-resolved-pipeline-paths.md` — the #186 follow-up:
  migration map for the five scripts importing `utils/pipeline_paths.py`, and a **correction** to
  our own 2026-08-11 note, which said *"You can delete `utils/pipeline_paths.py`"*. Not quite right:
  `REVIEW_DIR` and `SEGMENTATION_REVIEW_DIR` have no YAML source and two scripts use them.
- `scriptorium/collab/sp/2026-08-17-unresolved-variable-becomes-a-directory.md` — the sp answer to
  the stray-directory report, now fixed here in `0e5f350`.
- **Captain, 2026-08-19: "no, don't commit it."** Leave both as working-tree edits.
- **Verify:** `git -C ~/github/nida-institute/ears-to-hear status --short`. That repo is 31 ahead of
  its origin with much unrelated in-flight work; a third collab doc (`2026-08-12-…`) is modified by
  someone else and is **not** ours.

### 5. #205 CLI schema discipline — **filed, not started.** Six questions await the Captain.

### 6. Scripture editions #200 / versification #203 — **parked, unchanged.** #200's code is on the
local-only tag `wip/scripture-200` and is not on `dev`.

---

## Decisions settled today — do not reopen

**On the HATH plan** (all recorded with the Captain's words in `design-hath-parity.md` §5):

- **H1 — there is no installer.** Adoption is: clone HATH, `cd`, start Claude Code, `/install
  <destination>`. *Why:* every alternative was a runtime we would have to ship and test on
  platforms the Captain does not own (he has Mac and Linux, but Windows users). Claude Code is the
  one dependency the audience already has. A **manifest** — declared source→target paths with
  `create-only` / `create-or-replace` — is the installer; Claude Code is only the runtime. The
  install skill lives in **HATH's own** `.claude/skills/`, so it never has to be installed. The
  documented copy-by-hand path stays in the README as the fallback.
- **H2 — conventions live in `docs/ai-context/conventions/`.** *Why:* a project must be able to
  tell shipped methodology from its own writing.
- **H3 — a sync script with a test that fails on unexpected divergence.** *Why:* the drift happened
  because a copy existed with nothing watching it.
- **H4 — one shared text for five skills; `audit-code` forked.** *Why:* the engine vocabulary was
  clustered, not woven, and in `load-context` it duplicated `rules.md` items the skill's own Step 4
  already reads. `audit-code`'s engine content is the subject matter, so it is a different skill in
  HATH rather than a generalization.
- **Q3 — LLMFlow is upstream for shared skills, for now.** *Why:* sp accumulates real-world
  experience fastest. Explicitly provisional.
- **Q4 — no `~/.sp` for HATH projects; its contents live in the repo.**
- **Ecosystem parity, not silence.** A shared skill may name `pytest` — it must then also name
  `vitest`. *Why:* "run the test suite" teaches nobody anything. **Vitest** is confirmed as the
  org's framework by `gui/frontend/package.json` and `paratext-copilot`, not chosen generically.

**On the release:**

- **Today's work folds into 0.2.1.24**, not a new version. The CHANGELOG heading was retargeted and
  a **duplicate `## 0.2.1.24` heading merged** — verified no content lost.
- **#192 stays open: the Captain wants `else` implemented.** Removing it from the editor schema was
  the right short-run fix for the discrepancy; the feature is still wanted. Moved to the bottom of
  Todo at his instruction.

**On the board:** seven issues closed and moved to Done — #178, #189, #195, #196, #198, #186, #175
— each verified against code and tests, not against the CHANGELOG. #33 retitled and narrowed to the
three files never created. Todo is 11, all genuinely open.

---

## Do NOT / deferred

- **Do not push.** The single push waits until the Captain says the release contents are complete.
  Pushing retargets PR #199 and restarts a ~2h Windows build.
- **Do not merge PR #199.** It no longer contains the release; merging it now would ship an
  incomplete 0.2.1.24. This reverses the morning handoff.
- **Do not commit the two ears-to-hear documents.** Explicit instruction.
- **Do not treat the bodyless HTTP 400 as diagnosed.** Three candidate mechanisms across two
  sessions; two refuted by test, the third (an API key used to run Claude Code) never confirmed.
  Captain: *"let's not worry about bodyless HTTP 400 until we encounter it in the wild again."* A
  claim asserting its cause was removed from `load-context` today for this reason.
- **Do not remove `from llmflow.plugins.echo import echo` from `utils/io.py`.** It reads as unused
  to static analysis; pipelines name `llmflow.utils.io.echo` as a `function:` step and
  `steps/function.py:28` resolves it by attribute lookup. Removing it broke four tests today. A
  comment now says so.
- **Looks like a next step but isn't:** *the remaining 49 lint errors in `src/llmflow/utils/`.*
  They are in files untouched by this work (`llm_runner.py`, `markdown_cleaner.py`,
  `step_outputs.py`). Sweeping them would bury correctness fixes in an unreviewable diff. Offer it
  as its own commit.
- **Do not add rules to `docs/ai-context/rules.md` without explicit direction.** It is generated by
  `tools/update_ai_context.py` and under the Captain's authority. One rule was added today at his
  explicit instruction; that is not standing permission.

---

## Process notes worth carrying

- **Verify issues against code, not the CHANGELOG.** Seven of eighteen Todo items were already
  implemented. Two of them had been recommended to the Captain as fresh work before checking — a
  mistake caught only because he asked *"can you verify that they are all actually implemented and
  working, not just documented as working?"*
- **The recurring defect this session, found four times:** a check applied to N-1 of N paths reads
  as consistent, because the guarded paths agree with each other. The `${var}` write guard (lint
  and rewind, not the path that writes), `.cursorrules` (lost the `sp run` prohibition),
  `commit-ready` (#206, gated Python but not the GUI's TypeScript), and `resolve_pipeline_paths`.
- **Shell conventions.** The Captain corrected the same drift twice: `cd <path> && …` and piping
  through `head`/`awk`. CLAUDE.md says pass the path as an argument and use the file tools. The
  `Grep` tool is unavailable in this session; use `grep` via Bash with a path argument, no pipes.

---

## Key files & links

**Plans / tracking**
- `project/plans/design-hath-parity.md` — the live plan. §4 classification, §5 H1–H4 with the
  Captain's answers inline, §6 tests, §7 sequence.
- `project/plans/design-onboarding-fresh-clone.md` — #204, D1–D10 ruled.
- `project/RELEASE_CHECKLIST.md` — merge/tag/gate order.

**Code touched today**
- `data/file-catalog.yaml`, `src/llmflow/file_catalog.py` — the managed-file catalog (data + loader)
- `src/llmflow/doctor.py`, `src/llmflow/cli_utils.py`
- `src/llmflow/utils/{io,context,rewind,linter}.py` — the unresolved-`${var}` guard
- `src/llmflow/templates/sp-skills/*` — the five generalized skills
- `tests/test_{catalog,doctor,init_noninteractive,unresolved_path_guard,install_instructions,commit_ready_gate,portable_skills}.py`

**Issues** — #204 onboarding · #205 CLI schema · #206 commit-ready GUI gate (fixed) · #200 editions
· #201 dataset versioning · #203 versification · #192 implement `else` · #33 missing project files ·
human-at-the-helm#1

**PRs** — nida-institute/LLMFlow#199 (release, OPEN/CLEAN, head `cb72cb7`, does not contain today's work)

**Board** — 13 (LLMFlow Roadmap). Todo: 11 items.
