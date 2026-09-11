# HANDOFF — 2026-09-11

## ▶ NEXT ACTION

**`project/TODO.md` → 🎯 THE GOAL. Its one unticked item is the next action** — the engine work
under it is done and committed, and the remaining item is the one that needs the Captain.

Nothing from this session is half-applied. This file is short because the tree is nearly clean.

## In flight — branch `dev`, in sync with `origin/dev`, head `3ca7139`

E1, E2 and E3 landed in `26ba1d3` and `3ca7139`, each with tests, CHANGELOG and a
`docs/llmflow-language.md` entry.

**Verify:** `hatch run pytest tests -q -m "not integration"` → **5,479 passed, 25 skipped,
1 failed**. The one failure is `test_product_name_in_prose`, on the untracked collab report
`2026-09-09-replay-cannot-read-a-schema-the-pipeline-declares.md:95`, which uses the deprecated
product name in prose. It predates this work and is not from it. *Describing* the token in this
file reproduces the failure, which is why the report is named rather than quoted.

| uncommitted here | what to do |
|---|---|
| `data/models.json` | leave — one line, and committing it restarts a 2h17m Windows build |
| `.cursorrules`, `.windsurfrules` | written by an `sp init --update` run; whether this repo ships assistant config is the Captain's call |
| `project/0x28.md` | the Captain's |
| `docs/index.json` | **`MM` — the staged copy is stale.** The pre-commit hook staged a regeneration that predates the E1/E2 source changes; the working tree has the current one. Commit the working-tree version with the next commit rather than the staged one |

**In `ears-to-hear`:** `scriptorium/collab/sp/2026-09-08-old-documents-are-deleted-not-sifted.md`
is untracked — an earlier session's note that had been stranded in a dead directory and was moved
into the live channel during this session. Their commit, not ours.

`ruff check src/` reports one pre-existing error in a file nobody here touched:
`cli_utils.py:736`, `re` imported but unused.

## Settled — do not reopen, and where the reasoning is

All of these are recorded; the pointer matters more than the summary.

- **The ten rulings Q1–Q10**, including two answered by discourse-flow's reply —
  `project/plans/design-pericope-segments-and-text.md` §10
- **Why word addressing is a map keyed by word id and not a positional array** — same document
  §6.2–§6.6, decided on Psalm 23:1, where the superscription is part of verse 1 and word 3 is
  the fourth morpheme
- **`save_json`'s `indent=2` stays.** The 47.7% of discourse-flow's artifact that is indentation
  is ours and deliberate — `project/TODO.md`, the section that closes it. Do not "fix" it
- **A collab note is written once, into the recipient's tree**, and has a death —
  `data/ai-rules.yaml`, rule `plans-are-temporary`

## Landmines

- **`ears-to-hear`'s live collab channel is `scriptorium/collab/sp/`.** A top-level `collab/`
  existed with **0 tracked files**; two notes were delivered into it and never read. It has been
  removed. Check `git ls-files` before writing into any repo's collab directory.
- **Running `sp init --update` turns the suite red** — it rewrites `docs/ai-context/sp/rules.md`
  through a second generator. Issue **#237**; the remedy is
  `hatch run python tools/update_ai_context.py`.
- **A pre-commit hook restages `docs/index.json`.** Check `git status --short` after every commit.
- **`git commit <paths>` refuses an untracked file** — `git add` it first. This cost one aborted
  commit.
- **Never run `sp run`** (costs money) or **`sp doctor`** here (unsafe until #210/#211).
- **`~/.sp/user-context/` has no backup** since `~/.sp` stopped being version-controlled, and it
  is the one part of that store `sp init` cannot regenerate.
- **Do not ask discourse-flow who consumes their output.** Their standing decree: *"downstream
  consumers are a black box to us."* A question of that shape was refused once already.
- `tmp/representation-grid/` regenerates with
  `hatch run python tmp/representation-grid/generate.py` — no network, no model.

## Key files

- `project/TODO.md` — the queue and the goal. Read before this file's next action
- `project/plans/design-pericope-segments-and-text.md` — the ruled design
- `collab/discourse-flow/2026-09-10-a-pericope-does-not-need-the-text-if-its-segments-have-it.md`
  — their reply: three rulings and two corrections, both of which were accepted
- `project/plans/plan-scripture-documentation.md` — shipped docs drafted, **not** installed; they
  land with the code, never before
