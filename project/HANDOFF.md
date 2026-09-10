# HANDOFF — 2026-09-10

## ▶ NEXT ACTION

**Start E3 — the `usj_to_text` fixes**, first item under `project/TODO.md` → 🎯 THE GOAL. Two
defects, both reproducible against files already on disk, both test-first. It goes first because
ears-to-hear has been told to fix a live defect by calling that function, and it is currently
flawed in two ways.

Everything from the previous session is committed and pushed. This file is short because of
that.

## In flight — nothing

Branch `dev`, in sync with `origin/dev`, head `e3c5f42`. Four commits landed:
`f7b79bd` (the `print` strike), `4bff857` (the rule), `f525da0` (one YAML serialiser),
`e3c5f42` (the design record).

**Verify:** `git status --short --branch` → `## dev...origin/dev` and only the three rows below.

| still uncommitted, all deliberately | why |
|---|---|
| `data/models.json` | one line; committing restarts a 2h17m Windows build |
| `.cursorrules`, `.windsurfrules` | written by an `sp init --update` run; whether this repo ships assistant config is the Captain's call |
| `project/0x28.md` | the Captain's |

**Verify the suite:** `hatch run pytest tests -q -m "not integration"` → **5,456 passed, 25
skipped, 1 failed**. The single failure is `test_product_name_in_prose` on the untracked collab
report `2026-09-09-replay-cannot-read-a-schema-the-pipeline-declares.md`, line 95, which uses
the deprecated product name in prose. It predates this work. Note that *describing* the token in
this file reproduces the failure, which is why the report is named rather than quoted.

Also red, and pre-existing in a file nobody here touched: `ruff check src/` reports
`cli_utils.py:736`, `re` imported but unused.

## One loose end in another repo

`ears-to-hear` shows `?? collab/` — a directory with **0 tracked files**, holding
`collab/sp/2026-09-08-old-documents-are-deleted-not-sifted.md` from an earlier session. Their
live channel is `scriptorium/collab/sp/`. That note has been undelivered since 8 September. It
is not this session's file, so it was reported rather than moved.

## Landmines

- **Running `sp init --update` turns the suite red** — it rewrites `docs/ai-context/sp/rules.md`
  through a second generator. Issue **#237**; the remedy is
  `hatch run python tools/update_ai_context.py`.
- **A pre-commit hook restages `docs/index.json`.** After each commit, check `git status --short`
  so it does not accumulate unnoticed.
- **`git commit <paths>` refuses an untracked file** — `git add` it first. This cost one aborted
  commit today.
- **Never run `sp run`** (costs money) or **`sp doctor`** here (unsafe until #210/#211).
- **`~/.sp/user-context/` has no backup** since `~/.sp` stopped being version-controlled, and it
  is the one part of that store `sp init` cannot regenerate.
- `tmp/representation-grid/` regenerates with
  `hatch run python tmp/representation-grid/generate.py` — no network, no model.

## Key files

- `project/TODO.md` — the queue and the goal. Read before this file's next action
- `project/plans/design-pericope-segments-and-text.md` — the ruled design, §10 Q1–Q10
- `collab/discourse-flow/2026-09-10-a-pericope-does-not-need-the-text-if-its-segments-have-it.md`
  — their reply: three rulings, two corrections
