# HANDOFF — 2026-09-10

## ▶ NEXT ACTION

**Commit the design document, then read the two unread collab reports.** Everything else this
session produced is already committed and pushed.

```
git -C ~/github/nida-institute/LLMFlow status --short
```

Five untracked or modified files. Two are the Captain's and stay untouched; the rest need a
decision each — see *In flight* below.

Then the work itself is in **`project/TODO.md` → 📐 THE GOAL THIS CYCLE**, which carries the
scripture-representation goal and the state of release 0.2.1.28. This file does not restate it,
because a queue item written here goes stale the moment somebody does it.

---

## In flight — uncommitted in this repository, branch `dev`, in sync with `origin/dev`

| file | state | what to do |
|---|---|---|
| `project/plans/design-annotation-without-anchors.md` | **untracked**, written this session, `Status: proposed` | commit it — it is the cycle's design and exists nowhere else |
| `project/TODO.md`, `project/HANDOFF.md` | modified this session | commit with it |
| `data/models.json` | modified — one line, `last_updated` re-verified | **deliberately held back.** Committing restarts a 2h17m Windows build for a re-verification. Belongs to the cycle after 0.2.1.28 |
| `collab/discourse-flow/*.md` — 4 files | untracked, written by *other* sessions | not mine to commit; two are unread, see below |
| `project/0x28.md` | untracked | the Captain's |

**Verify:** `git -C ~/github/nida-institute/LLMFlow log --oneline -1` → `80d864c`, and
`git status --short --branch` → `## dev...origin/dev` with no ahead/behind.

## Two collab reports nobody here has read

Both arrived from other sessions during this one, and neither has been assessed:

- **`2026-09-09-replay-cannot-read-a-schema-the-pipeline-declares.md`** — *"`sp tools replay`
  refuses every prompt we have, because the pipeline declares the schema"*. It claims `sp lint`
  validates an arrangement replay declines to read. If true that is a real defect; unexamined.
- **`2026-09-09-what-we-still-compute-that-other-projects-will-need.md`** — an inventory of what
  a consumer computes in plugins that the engine might absorb. **Bears directly on this cycle's
  goal** and is listed as a task in `TODO.md`.

The third, `2026-09-09-adapting-a-rolling-audit-to-the-document-lifecycle.md`, came from a
session in *this* repository.

## Elsewhere — each that repository's own commit, none of it mine to make

| repo | uncommitted | why it exists |
|---|---|---|
| `human-at-the-helm` | `disciplines/workflow.md`, `skills/stand-down/SKILL.md`, `skills/load-context/SKILL.md` | yesterday's syncs. The `load-context` change guards two `~/.sp` reads so a machine without that store does not open a session with errors |
| `discourse-flow` | `collab/sp/2026-09-09-audits-roll-they-do-not-accumulate.md` | tells them their six dated audit records followed a README **we** shipped, contradicting the pattern we also shipped |

**Verify:** `git -C ~/github/nida-institute/human-at-the-helm status --short`.

---

## Settled this session — do not reopen

- **Anchors are load-bearing only because the payload is opaque.** A per-word entry is keyed by
  word id and carries no surface form or reference, so the id cannot be resolved without finding
  `srcloc` in the document. Established by fetching `WLC Ruth 1:1`, not by reading comments — and
  it is the fact the whole design turns on.
- **`docs/audits/` is not shipped, and its absence is a decision** (#210): those checklists were
  one project's documents installed into everyone's repository. `audits-pattern.md` was corrected
  to stop referencing it, rather than the directory being re-added. A proposal to re-add it was
  approved and then withdrawn when the prior ruling surfaced.
- **`project/plans/README.md` ships**, matching `project/audits/README.md`. That absence *was* an
  oversight rather than a decision, which is why it went the other way.
- **A shared skill names no engine vocabulary.** A `stand-down` fix mentioning `sp doctor` was
  refused by `test_shared_skill_carries_no_engine_vocabulary`; rewording it neutrally made it
  true on both sides, so the divergence and the ruling permitting it both became unnecessary.
  A `differs` entry exempts a whole file from comparison indefinitely — identical copies are
  stronger.

## Landmines

- **Measure against `origin/main`, never a local `main`.** A local ref 27 commits stale put a
  false "35 commits" into a PR description this session.
- **A `cd` in one Bash call persists into the next.** One did, a test run started from the wrong
  directory, and five phantom failures were reported before it was caught. Pass absolute paths.
- **`gh run watch --exit-status` returned 0 on a *failed* run.** Read `.conclusion` and the
  per-job list.
- **`Logger.reset()` clears every handler on the `llmflow` logger** (`modules/logger.py:35`).
- **A killed pytest run leaves `tmp/pytest/` read-only** — `chmod -R u+w tmp/pytest` before
  removing. Two runs also collide there; one at a time.
- **Never run `sp run`** (costs money) or **`sp doctor`** in this repo (unsafe until #210/#211).
- **`paratext-copilot` is out of scope** by the Captain's instruction. Its work is committed and
  pushed; three issues (#229–#231) are open there. Do not pick it up from here.

## Key files

- `project/TODO.md` — **the queue, and the goal.** Read before this file's next action
- `project/plans/design-annotation-without-anchors.md` — the design, `proposed`, five decisions
  in §6 and the measurement to take first in §7
- `src/llmflow/utils/scripture.py` — `check_include:453`, `rows_to_output:495`, `rows_to_usj:519`
- `docs/ai-context/sp/scripture-representations.md` — the four forms and their measured costs
- `project/RELEASE_CHECKLIST.md` — reordered so its sections run in the order they are done
