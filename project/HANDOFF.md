# HANDOFF — 2026-08-25 (evening)

Supersedes the morning's handoff of the same date.

---

## ▶ NEXT ACTION — commit two repositories, then USJ

**Nothing is committed in either repository.** Both are green and both are the human's to commit.

```bash
# 1. the engine — 106+ paths, suite green at 2970 passed / 26 skipped
cd ~/github/nida-institute/LLMFlow
git add -A -- . ':!project/plans/*' ':!project/HANDOFF.md' ':!project/REVIEW.md' ':!project/tmp-context.md'
git commit -F tmp/commit-1-engine.txt
hatch run pytest -q
git add project/plans/ project/HANDOFF.md project/REVIEW.md project/tmp-context.md
git commit -F tmp/commit-2-records.txt
rm tmp/commit-1-engine.txt tmp/commit-2-records.txt

# 2. discourse-flow — its ai-context migration, on top of in-flight work
cd ~/github/nida-institute/discourse-flow
git status --short          # migration + their own uncommitted work, tangled
```

`project/REVIEW.md` says what to read in the engine commit and in what order. It is current for
the code but predates the catalog rulings recorded below.

---

## Done today

**The engine** — #207 (the suite writes only inside the repository, and nothing lands in
`~/.sp`, `$TMPDIR` or `/private/tmp`), #210 (the ai-context layout), #211's writer loop, #214
(the audit method ships), the template tree mirroring its destinations, the block warning, and
`sp doctor --help` no longer claiming to be read-only.

**The catalog holds only what sp specifies** — `project.md` and the three `docs/audits/`
checklists are gone from it, with their constants.

**`nida-institute/discourse-flow` is migrated** to the two-half layout: `project/` holds their
index, overview, `project.md` and rules; `sp/` holds sp's five. Their 12 KB `project.md` moved
inside `project/` by `git mv` and their map now names it — it was unreachable before. Four broken
pointers repaired in `AGENTS.md`, `project/TODO.md` and `rst-implementation-plan.md`. Their 27
doc-hygiene tests pass. **`CLAUDE.md` there is now writable** — it was `-r--r--r--` and crashed
`sp init`; re-lock it if that was deliberate protection.

**#215 filed** — three defects in `sp init`'s write paths, found by that migration.

---

## USJ (#200) — both replies are in, and both change the design

Neither had been read by any session before today. **Read the documents, not this summary,**
before designing: `discourse-flow/collab/sp/2026-08-24-usj-is-coming.md` from §148, and
`ears-to-hear/scriptorium/collab/sp/2026-08-24-usj-is-coming.md` from §141.

### The producer — `discourse-flow`, three blockers

1. **Levinsohn has no home.** 33 LGNTDF discourse feature types, merged at
   `plugins/milestone_content.py:183`, are derivable from none of the five families. They need a
   sixth family *or* explicit permission to add a key to the `scripture_pipelines` container.
   Either answer unblocks them; silence does not.
2. **Variants, and it is an alignment problem rather than a file to load.** Levinsohn's indices
   are NA28-family; where SBL chose differently the index silently names the wrong word — every
   one of Mark's 147 mismatching citations falls in an apparatus-flagged verse, none in a clean
   one. But the Logos apparatus is **verse-keyed prose**, so making it usable means aligning a
   second witness into the word sequence and minting ids. Their narrow version: per verse, the
   words NA28 has that SBLGNT does not, in order, addressable.
3. **`morphology` must reach Macula's `role`, `class` and `type`** — syntactic, not inflection.

**Also theirs:** inter-word material must survive exactly · id density is the caller's choice ·
`include` defaults lean, opt in never opt out · `plain`/`milestones` must stay cheap, because
synthesis cannot window and reads 32 KB instead of 1.3 MB · `passage:` needs word-id spans, not
only chapter:verse · senses unnormalised, and they decline to answer for Hebrew · **they want no
paragraph source at all** — they built one, ratified it, and reversed it.

### The consumer — `ears-to-hear`, two corrections to our premise

1. **There are two USJ payloads per pericope**, not one: `source_text` and `translation` (BSB),
   both USJ, 131/131 in Mark. A design modelling one text per step models half of what arrives.
2. **What reaches them carries no word-level annotation at all** — no `char` nodes, no ids, no
   morphology. So "you pay 4.26x for structure you then flatten" is not what happens there;
   there is nothing to discard.

**The cost figure needs a unit.** Same books, three ways of counting: Mark 2.56x codepoints,
1.78x UTF-8 bytes, 6.74x escaped JSON. Our 4.26x sits in that band matching none of it. Our
milestone figure they corroborate exactly at 1.072x.

**Their real argument for the feature** is better than ours: four scripture-acquisition paths in
one repo, two serializations of the same edition, and two hand-written milestone builders that
**disagree on all 131 Mark pericopes** — Greek `after` replaces the space rather than
accompanying it, and their code applies the Hebrew rule to both.

**Two traps worth more than the rest:** Macula's verse milestones contradict their own tokens'
`ref` for **1,501 of 11,286 Mark tokens, 100 of 673 verses** — derive milestones from each
token's `ref`, never from nesting. And a hand-rolled USJ flattener silently drops what it does
not recognise, so the moment `format: usj` ships anything richer than today's, every consumer
with its own flattener starts losing text quietly.

**And one finding that is not about USJ at all.** Their reader HTML ships a book's complete
Greek or Hebrew text — 102,739 and 14,944 characters — with **zero attribution**, while SBLGNT
as they consume it is CC BY 4.0. Our own catalogue note calling SBLGNT's licence restrictive is
out of date for that copy: the condition is attribution, which is mechanically satisfiable. The
exception is MARBLE sense data (`@ln`, `@domain`), held under permission rather than a licence,
and it feeds their published background layer. No record of anyone checking before today. This
is time-sensitive in a way the engine work is not — artifacts are being generated now.

### Still the human's to rule

§4.4 of `design-scripture-representations.md`, the Greek/Hebrew asymmetry — five `=>` remain
open there. `discourse-flow` answered for Greek (unnormalised) and declined for Hebrew.
`ears-to-hear`'s §7 lists five rulings they are waiting on, including whether they adopt
`type: scripture` at all and whether pairing moves into the engine.

Start from the parked tag `wip/scripture-200` (`0bb1d5b`), which is on the remote.

---

## Open, recorded, not started

Four `=>` slots in `project/plans/design-one-source-for-shipped-files.md`: **Q3** what `scope`
should be called, **Q5** which directory structure states the root, **Q6** whether a project may
change a file in its own directory. Q1 and Q2 are closed.

**#211's migration itself** — 19 constants, 1,047 lines, one pass as ruled. **#215** — the three
`sp init` write-path defects. **`docs/ai-context/sp/index.md` is stale**, four entries having left
the catalog. **The docstring sweep** — 21 test files and 7 modules still carry rulings and history
in comments. **`ears-to-hear` has not been migrated** to the two-half layout; discourse-flow was
the first.

**Unread:** `discourse-flow/collab/sp/windowing-semantics-gap.md`, 482 lines.

---

## Verify

```bash
hatch run pytest -q                              # 2970 passed, 26 skipped
git status --short | wc -l                       # 106+
gh issue view 215                                # the init write-path defects
grep -c '^=>' project/plans/design-scripture-representations.md   # 5
git ls-remote --tags origin wip/scripture-200    # 0bb1d5b
```

---

## Do NOT

- **Do not commit, push or merge.** Gates yes; the commit is the human's.
- **Do not fill in a `=>`**, and do not record a ruling the human did not give.
- **Do not put design, rulings or version history in docstrings or comments.**
- **Do not run `sp doctor` here** — step 7 of `design-ai-context-layout.md` is undone.
- **Do not commit or push `~/.claude`**; its 82 uncommitted files are deliberate.
- **`~/.sp` has one dirty file**, `skills/load-context/SKILL.md`, identical to this repository's
  template for it. Committing that store is the human's act.
