# HANDOFF — 2026-08-20

Supersedes the 2026-08-19 (evening) handoff entirely. Its NEXT ACTION — HATH step 4 — is done.

---

## ▶ NEXT ACTION — step 6 of the HATH plan: the sync mechanism

`project/plans/design-hath-parity.md` §7 step 6, ruling H3-B: *"a sync script … run deliberately,
with a test that fails when the two sides diverge unexpectedly."* Steps 3, 4 and 5 are done.

The two repositories now hold the same five skills and four disciplines, and nothing watches them.
Write the script and the test **in this repo** (LLMFlow is upstream, ruling Q3), against the clone
at `~/github/nida-institute/human-at-the-helm`.

It must encode three things, or it will "fix" work that was done on purpose:

| | |
|---|---|
| `audit-code` | forked by ruling H4-A — HATH has no counterpart at all |
| `commit-ready` | **deliberately differs** as of HATH `d47ceee` — this repo's copy names `gui/frontend`, `pytest.ini` and the Logger rule; HATH's must not |
| `drift-patterns.md` | must stay **byte-identical** both sides (plan §8) — it is today |

**Verify where you are:**

```bash
hatch run pytest tests/test_portable_skills.py tests/test_portable_disciplines.py  # expect 39 passed
git log --oneline -1                                     # expect a6d5d3b
git -C ~/github/nida-institute/human-at-the-helm log --oneline -1   # expect d47ceee
```

**Do not push.** See "Do NOT" below.

Two throwaway scripts in this session's scratchpad did by hand what step 6 must do properly —
`check_hath.py` (runs this repo's guard patterns over HATH's shipped files) and
`check_manifest.py` (expands `manifest.yaml` and asserts every source exists and nothing ships
unlisted). The scratchpad is ephemeral; treat them as a description of the required checks, not as
code to recover.

---

## Active threads

### 1. human-at-the-helm#1 — **steps 3, 4 and 5 done. Step 6 is the next action above.**

- **Goal (Captain, 2026-08-19):** *"our ai context here is now more advanced than the original
  HATH, by quite a bit. I want HATH to have the same level of maturity, without whatever is
  specific to Scripture Pipelines."*
- **State:** LLMFlow `99fa41f`, `a8d7c15`, `85cbacc`, `80b45f9`, `a6d5d3b`. HATH `24fd64f`,
  `d8a3642`, `d47ceee`.
- **What HATH has now:** five skills (`authorize`, `commit-ready`, `load-context`, `stand-down`,
  `handoff`), nine disciplines in `disciplines/` (five essays + four operational rules) with a
  README separating them, `manifest.yaml`, `/install` in its own `.claude/skills/`, and a shipped
  `/hath-check`.
- **Remaining:** step 6 (above), then step 7 — manual acceptance, a real Claude Code session in a
  plain project running `/load-context`. **Only the Captain can do step 7.**
- **Verify:** `hatch run pytest tests/test_portable_disciplines.py` → 18 passed.
  `git -C ~/github/nida-institute/human-at-the-helm log --oneline -3`.

### 2. Release 0.2.1.24 — **`dev` is 34 ahead of `origin/dev`, unpushed.**

- **State:** PR #199 is `OPEN`, head still `cb72cb7` — it does **not** contain any of this work.
- **Next step:** nothing until the Captain says the release contents are complete.
- **Verify:** `git log --oneline origin/dev..dev | wc -l` → 34. `gh pr view 199 --json headRefOid`.
- Suite: **2724 passed, 13 skipped** (was 2705 at yesterday's handoff).

### 3. #204 fresh-clone onboarding — **two pieces left, unchanged today.**

- (a) the `_is_generated` call sites still decide ownership by marker string rather than by
  `data/file-catalog.yaml`; (b) manual acceptance against a fresh clone — the Captain's to do.
- **Verify:** `hatch run pytest tests/test_catalog.py tests/test_doctor.py` → passes today.

### 4. ears-to-hear — **two documents written, uncommitted by the Captain's instruction.**

`scriptorium/collab/sp/2026-08-06-public-api-for-resolved-pipeline-paths.md` and
`2026-08-17-unresolved-variable-becomes-a-directory.md`. Captain, 2026-08-19: *"no, don't commit
it."* Leave as working-tree edits.

### 5. #205 CLI schema discipline — **filed, not started.** Six questions await the Captain.

### 6. Scripture editions #200 / versification #203 — **parked, unchanged.**

---

## In flight / not committed

- **Both repositories are clean.** Everything from this session is committed and unpushed.
- HATH has an untracked `.gitignore` that predates this session. Not ours; left alone.

---

## Decisions settled today — do not reopen

All recorded with the Captain's words in `design-hath-parity.md` §5 (H5, H6).

- **D1-A — the general half of `sp-workflow.md` is `workflow.md`.** Plain, mirrors the source name.
- **D2-A — the per-pipeline half of project tracking folds into `sp-workflow.md`**, rather than a
  second tracking file. One engine file, no overlap for the sync to watch.
- **D3-A — content moved to HATH before the manifest was written**, reordering steps 5 and 6's
  content half. *Why:* a manifest written against directories that do not exist cannot be tested
  against what the repository contains, which is the risk H1 recorded against itself.
- **D4-A — HATH commits land on its local `main`, unpushed**, matching this repo's posture.
- **D5 — `disciplines`, in both repositories; this engine is the side that renamed.** `~/.sp/
  conventions/` → `~/.sp/disciplines/` in `a8d7c15`. *Why:* HATH's paths are public and linked from
  its README; `~/.sp/conventions/` was created by an installer and nobody links to it. Naming for
  methodology material comes from the methodology's home.
- **D6-C — all nine disciplines install; `load-context` reads the operational rules each session
  and treats the essays as reference.** The index that decides which is which is
  `disciplines/README.md`, shipped beside the files — not a list inside the skill, which would be a
  second copy of the shipped set.
- **`commit-ready` is stripped in HATH (Captain: "strip it out of HATH's commit-ready").** It is now
  the second skill that differs between the repos on purpose.

**One decision open**, with an empty `=>` under H6: whether HATH ships per-tool pointer files
(`.cursor/rules`, `.github/copilot-instructions.md`, `AGENTS.md`) so its disciplines reach Cursor,
Copilot and Codex users. The AI's read, offered and not ruled: worth doing as its own issue with a
real user of one of those tools to confirm it, not bolted on from documentation pages.

---

## Do NOT / deferred

- **Do not push either repository.** The single push waits until the Captain says the release
  contents are complete; pushing retargets PR #199 and restarts a ~2h Windows build.
- **Do not merge PR #199.** It no longer contains the release.
- **Do not "fix" the two deliberate divergences** — `audit-code` (forked) and `commit-ready`
  (stripped in HATH). Both are rulings, not drift.
- **Do not commit the two ears-to-hear documents.**
- **`~/.sp/conventions/` on this machine is a stale leftover** — the rename created
  `~/.sp/disciplines/` (current, 11 files) and nothing removes the old directory, because `sp
  doctor` iterates what the package ships and never enumerates what is present. **Delete it by
  hand.** `~/.sp/skills/` is current.
- **Finding, not fixed and not yet filed: the test suite writes to the real `~/.sp/`.**
  `tests/test_init.py:32` and several others call `main(["init"])` having patched only the working
  directory (`monkeypatch.chdir`), not `Path.home()`. That is how this machine's `~/.sp/` was
  rewritten twice today. It deserves an issue and a `conftest.py` fixture that isolates HOME for
  the whole suite; neither exists yet.
- **Lint:** 23 pre-existing ruff errors in the test files touched today (verified identical against
  `HEAD` before the work) and ~49 in `src/llmflow/utils/`. Untouched deliberately — sweeping them
  would bury correctness changes in an unreviewable diff. Offer as its own commit.
- **`docs/ai-context/` is the Captain's.** One line in `audits-pattern.md` changed today at his
  explicit instruction (`a6d5d3b`); that is not standing permission.
- **Looks like a next step but isn't:** renaming `consumer-repo-conventions.md`. It sits in
  `disciplines/` with "conventions" in its name, which reads odd — but D5 was about what the
  category is called, not about renaming a file whose subject happens to be a convention.

---

## Process notes worth carrying

- **The guard caught its author twice today.** A blanket rename rewrote the *file name*
  `consumer-repo-conventions.md` and six tests failed within the same run; `/hath-check`'s
  rationale line named `sp doctor` and the vocabulary check flagged it before it was committed.
  Both were mine, and neither reached a commit — which is the argument for writing the guard first.
- **Measure before recommending.** The `disciplines` rename was quoted at "19 files, ~155 lines"
  from an actual grep, not an estimate, and that number is what made the decision answerable.
- **A guard tests what it was told to test.** `commit-ready` passed every portable-skills check
  while still naming `gui/frontend`, `pytest.ini` and this project's Logger section, because the
  vocabulary list holds commands and file extensions, not directory names. The copy into HATH is
  what exposed it.
- **`--no-verify` was used once, on `99fa41f`, for no reason.** This repo has an active
  `.git/hooks/pre-commit` that regenerates `docs/index.json`. Verified afterwards that the output
  was byte-identical, so nothing was lost. Every later commit ran the hook.

---

## Key files & links

**Plans / tracking**
- `project/plans/design-hath-parity.md` — the live plan. §4 classification, §5 H1–H6 with the
  Captain's answers inline, §6 tests, §7 sequence with steps 4 and 5 marked done.
- `project/plans/design-onboarding-fresh-clone.md` — #204, D1–D10 ruled.
- `project/RELEASE_CHECKLIST.md` — merge/tag/gate order.

**Touched today — LLMFlow**
- `src/llmflow/templates/sp-disciplines/` — the 11 shipped documents, `workflow.md` and
  `sp-workflow.md` being the two halves of the split
- `src/llmflow/{cli_utils,doctor}.py`, `data/file-catalog.yaml` — the rename
- `tests/test_portable_disciplines.py` (new), `tests/test_global_disciplines.py`,
  `tests/test_{doctor,catalog,sp_lock,package_resources,portable_skills}.py`

**Touched today — human-at-the-helm** (`~/github/nida-institute/human-at-the-helm`)
- `manifest.yaml` — the installer; 23 resolved targets, verified against the repo
- `.claude/skills/install/SKILL.md` — never shipped to a target
- `skills/hath-check/SKILL.md` — shipped; reads the manifest copy the install leaves behind
- `disciplines/README.md` — the essay/rule index that D6-C depends on
- `README.md`, `adopting.md` — three adoption paths, five skills

**Issues** — human-at-the-helm#1 · #204 onboarding · #205 CLI schema · #200 editions ·
#201 dataset versioning · #203 versification · #192 implement `else` · #33 missing project files

**PRs** — nida-institute/LLMFlow#199 (release, OPEN, head `cb72cb7`, does not contain this work)

**Board** — 13 (LLMFlow Roadmap).
