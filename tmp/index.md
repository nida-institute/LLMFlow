# What is in `tmp/`, and why each thing is still here

`tmp/` is for throwaway files, and `.gitignore` here ignores everything by `*`. So **nothing in
this directory is recoverable once deleted** — git never had it. That is the whole reason this
index exists: the survivors are not obviously different from the scratch that surrounded them,
and without a note saying why each one stayed, the next sweep takes them.

Reviewed 2026-09-26. Everything not listed below was deleted that day.

## Kept because a tracked document points at it

Deleting any of these breaks a reference in a committed file, which is the failure
`docstrings-say-what-not-why` calls *a pointer with nothing behind it* — it still reads as
authority.

| | what it is | named by | when it can go |
|---|---|---|---|
| `issues/` | candidate issues against **external** standards and repositories, one directory per target: `bible-technology-alignment-spec`, `bible-technology-scripture-burrito`, `Clear-Bible-Alignments`, `Clear-Bible-biblealignlib`. Has its own `README.md`. | `project/plans/plan-scripture-burrito-alignment.md` R13 and R18, which *designate* this path and cite files inside it | when each is filed upstream, or the plan is retired |
| `representation-grid/` | the generator and outputs behind the 72-cell representation measurement — `generate.py` writes `grid.tsv`, `grid.json` and one file per cell | `project/plans/design-representation-workbench.md:18,21`; `project/TODO.md:709` | when that design document goes. §Q5 there asks whether it should become a committed fixture instead |
| `gen_alignment_demo.py` | regenerates the alignment worked examples — `hatch run python tmp/gen_alignment_demo.py` | `project/TODO.md:613` | with the alignment work (#238) |
| `alignment-worked-examples.md` | Luke 1:1–4, Ephesians 1:3–14, Psalm 23:1–4, Ruth 1:1–4, Greek and Hebrew | `project/TODO.md:611` | regenerable from the script above, so it may go **only if the script stays** |

## Kept because it is unsent work for another repository

`project/TODO.md:643` records these as outstanding: *"Five issue drafts and two pull request
bodies sit unfiled in `tmp/`."* They are the only copies. All target
`Clear-Bible/Alignments`, and the fixes they describe are committed on local branches with no
upstream.

| | what it reports |
|---|---|
| `issue-hin-roles.md` | `hin WLCM-IRVHin` declares no `roles` key, so our `validate_pair` refuses a real pair |
| `issue-spa-docid-case.md` | `spa WLCM-RV09` declares its source as lowercase `wlcm`; same effect |
| `pr-portuguese-source-ids.md` | adds the `n` prefix to `JFA11` source ids — 99,258 of 99,258 then join |
| `pr-wlcm-declarations.md` | the declaration fixes for the two defects above |
| `alignments-declaration-fix.txt` | working notes sitting with them |

## What was deleted on 2026-09-26, and why it was safe

Recorded so the next reader knows this directory was reviewed rather than left to grow.

- **~15 issue drafts whose issues are filed** — each traced to its number (#223, #238, #239, #240,
  #241, #252, #253, #254, #255, #256, and Clear-Bible/Alignments #12, #13, #14). `CLAUDE.md`'s
  cleanup rule says a draft goes once the issue exists; GitHub is the durable copy.
- **`issue-empty-null-absent.md`** — superseded the day after it was written by rule
  `say-which-kind-of-nothing`.
- **Twelve unverified drafts and PR bodies**, deleted on instruction after being listed: three
  comment bodies for #110 and #230, a discourse-flow draft, five PR bodies, a diff of the
  2026-09-24 Helm edits (now described by #259), and one script.
- **Sent collab messages** (`msg-*.txt`, `*-msg.txt`, `collab-reply-df.md`) — a note is written
  once into the recipient's tree and the sender keeps no second copy to drift
  (`plans-are-temporary`).
- **Machine litter** — `pytest/`, `pytest-tempfile/`, `gen.err`, `lint-files.txt`, `.DS_Store`,
  and one diff its own filename called discarded.

## Two pointers that are already broken

Found during the same review, not caused by it. Both name `tmp/` files that no longer exist:

- `project/HANDOFF.md:24` and `:167` — `tmp/commit-a.txt`, `tmp/commit-b.txt`
- `project/REVIEW.md:136-147` — `tmp/commit-1-engine.txt`, `tmp/commit-2-records.txt`

Both are rolling documents, so the fix is to update them rather than delete them. This is
`sp doctor`'s case in #260, happening in this repository's own files.

## The rule for anything added here later

If it is genuinely throwaway, add nothing to this file — that is what `tmp/` is for. If it
survives a sweep, it needs a row above saying what names it and when it can go. A file nobody can
justify is a file the next sweep is right to take.
