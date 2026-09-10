# HANDOFF — 2026-09-10

## ▶ NEXT ACTION

**Commit and push, in four places. Nothing from this session is committed anywhere.** The work
itself is in `project/TODO.md` → 🎯 **THE GOAL**; this file does not restate it.

Order matters only for the third row — the note in it is a live defect another team hits on
their next run.

| repo | what is uncommitted |
|---|---|
| this repository (the engine) | 10 modified, 9 untracked — see below |
| `discourse-flow` | `collab/sp/2026-09-10-pericopes-hold-segments-and-segments-hold-text.md` |
| `ears-to-hear` | `scriptorium/collab/sp/2026-09-10-source-text-is-punctuation.md` |
| `~/.claude` | `CLAUDE.md`, `settings.json` — `cgit status --short` |

**Verify:** `git -C ~/github/nida-institute/LLMFlow status --short --branch` → `## dev...origin/dev`,
head `4e35890`.

## In flight — branch `dev`, in sync with `origin/dev`, head `4e35890`

**Modified here:** `data/ai-rules.yaml` (the `plans-are-temporary` extension),
`data/file-catalog.yaml` + `src/llmflow/templates/project/docs/ai-context/sp/scripture-representations.md`
(the `print` removal), the three regenerated `docs/ai-context/sp/*` copies, `project/TODO.md`,
`project/plans/README.md`, and `data/models.json` (**still deliberately held back** — one line,
and committing it restarts a 2h17m Windows build).

**Untracked here:** three new plan documents (`design-pericope-segments-and-text.md`,
`design-representation-workbench.md`, `plan-scripture-documentation.md`), five collab notes
including their reply of today, `project/0x28.md` (yours), and `.cursorrules` / `.windsurfrules`
— written by an `sp init --update` run at 12:09 that predates this session's work.

**Verify the suite:** `hatch run pytest tests -q -m "not integration"` → **5,445 passed, 25
skipped, 1 failed**. The one failure is `test_product_name_in_prose`, pre-existing all session,
on the untracked collab report `2026-09-09-replay-cannot-read-a-schema-the-pipeline-declares.md`,
whose line 95 uses the deprecated product name in prose. It is not from this work — and note
that describing the offending token in *this* file reproduces the failure, which is why the
file names the report rather than quoting it.

**Also uncommitted, not mine:** `human-at-the-helm` is **ahead 1** with three modified files from
yesterday's syncs.

## Two things I got wrong that are now fixed — do not re-do them

- **The ears-to-hear note was delivered to a dead directory.** `ears-to-hear/collab/` has **0
  tracked files**; the live channel is `scriptorium/collab/sp/` (14 tracked). Moved. **An earlier
  session's note is still stranded there** — `collab/sp/2026-09-08-old-documents-are-deleted-not-sifted.md`,
  two days undelivered. Not mine to move; ask.
- **The indentation in their artifact is ours, not theirs.** `utils/io.py:409` hardcodes
  `indent=2` in `save_json`. Their tree has no `json.dump` at all. **Corrected in their tree:**
  a dated banner at the top of the original note (left standing, not reworded — they had
  already answered it) plus
  `collab/sp/2026-09-10-pericopes-hold-segments-and-segments-hold-text-reply.md`, which concedes
  both their corrections and asks which replacement for `indent=2` they would rather live with.
  Now a work item in `TODO.md`.

## Settled this session — do not reopen

- **`plans-are-temporary` now covers collab notes**, with age measured from the later of the
  declared date and the last commit — **never mtime**, because a clone rewrites every mtime and
  nothing would ever be old enough to delete. Written once into the recipient's tree, no sender
  copy; our two duplicates were deleted for that reason.
- **Tracked, then deleted** is the shape, not untracked: this rule's own safety argument is that
  git keeps every deleted file. Verified live —
  `git show 52e45c9^:docs/ai-context/sp/json-reliability.md` returns a document deleted in August.
- **`print` never existed.** `FORMATS = ("plain", "milestones", "usj")`; the shipped context
  document had promised a fourth format for months. The code was always right — `pipeline_schema.py:256`
  builds the enum from `FORMATS`, so `sp lint` would always have rejected it.
- **`~/.sp` is no longer treated as version-controlled.** Hook and global `CLAUDE.md` both scoped
  to `~/.claude`.

## Landmines

- **`~/.sp/user-context/` now has no backup** — the one part of that store `sp init` cannot
  regenerate, and where `sp-workflow.md` says your machine GitHub account lives.
- **Running `sp init --update` flips `docs/ai-context/sp/rules.md` and turns the suite red** —
  two generators, different wrappers. That is issue **#237**; the remedy is
  `hatch run python tools/update_ai_context.py`.
- **Never run `sp run`** (costs money) or **`sp doctor`** here (unsafe until #210/#211).
- **Measure against `origin/main`, never a local `main`.**
- **A killed pytest run leaves `tmp/pytest/` read-only** — `chmod -R u+w tmp/pytest` first.
- `tmp/representation-grid/` holds 27 generated payloads and a script; regenerate with
  `hatch run python tmp/representation-grid/generate.py`, no network and no model.

## Key files

- `project/TODO.md` — **the queue and the goal.** Read before this file's next action
- `project/plans/design-pericope-segments-and-text.md` — the ruled design, §10 Q1–Q10
- `collab/discourse-flow/2026-09-10-a-pericope-does-not-need-the-text-if-its-segments-have-it.md`
  — their reply, containing three rulings and two corrections
- Issue **#237** — the `rules.md` two-generator defect, opened today
