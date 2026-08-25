# HANDOFF — 2026-08-25

Supersedes the 2026-08-24 handoff, which was never committed.

Reconstructed from the working tree, not carried forward: the previous session hit a context
limit and hung, so there was no clean handoff. Every figure below was measured today and the
commands to re-measure are in "Verify" at the end.

---

## ▶ NEXT ACTION — commit, then `format: usj`

**106 changed paths, nothing committed, suite green.** Two commit messages are written and the
split is verified at 69 paths and 7:

```bash
git add -A -- . ':!project/plans/*' ':!project/HANDOFF.md' \
                ':!project/REVIEW.md' ':!project/tmp-context.md'
git commit -F tmp/commit-1-engine.txt
hatch run pytest -q                      # confirm commit 1 stands alone
git add project/plans/ project/HANDOFF.md project/REVIEW.md project/tmp-context.md
git commit -F tmp/commit-2-records.txt
rm tmp/commit-1-engine.txt tmp/commit-2-records.txt
```

Commit 2 is separate because `test_index_is_current` compares the plans index against the
documents present, so the index and the documents it names must land together.

**The commit is the human's** (rule `commit-authority`). `project/REVIEW.md` says what to read
and in what order.

Then `format: usj` (#200). What it needs first is in "USJ, before any code" below.

---

## What is in the tree

Seven pieces, all green, all uncommitted. `project/REVIEW.md` ranks them for review.

- **#207 — the suite no longer writes outside the project.** `$SP_HOME` relocates the store and
  one resolver in `src/llmflow/paths.py` replaces eleven call sites. Intermediates go to
  `tmp/pytest/`, declared in `pytest.ini`, git-ignored, announced at startup; only failing tests'
  directories survive a run. A green run leaves 328 KB in the repository instead of 35 MB
  outside it, and nothing of ours remains in `/private/tmp` or `$TMPDIR`.
- **#210 — the ai-context layout**, two halves with three standard documents each.
- **#211's writer loop** — `sp init` writes what the catalog declares, keyed on `policy`.
- **#214 — the audit method ships**, as the first template-sourced project document.
- **The template tree mirrors its destinations**, `templates/sp/` and `templates/project/`.
- **sp's block in a shared file carries a warning** and sits at the top of the file.
- **`sp doctor --help` no longer claims to be read-only.**

---

## Ruled 2026-08-25 — do not reopen, and do not re-derive

- **The catalog holds only what sp itself specifies.** A document a project invented is not sp's
  to create. `project.md` and the three `docs/audits/` checklists are removed, with their
  constants; a project reaches its own files by naming them in
  `docs/ai-context/project/index.md`.
- **`source: constant` goes.** All 19 remaining entries become template files, **in one pass**.
  `sp/rules.md` becomes `derived`, being rendered from `data/ai-rules.yaml`.
- **`block` stays.** Those four paths are fixed by external tools and the project has content in
  the same file, so one file genuinely has two owners. What was missing was the warning, now
  built. Project content goes **below** the block; a block previously appended at the bottom is
  relocated to the top on the next run.
- **`scope` goes**, because the directory structure already states which root a file lands in.
  Which structure is Q5, open.
- **No design, rulings or version history in docstrings or comments.** They go stale and are
  trusted over the design documents. The declaration carries the semantics.
- **CHANGELOG entries are high level** — see `docs/ai-context/sp/github-workflow.md`. Two to four
  lines, one completed change each, `(#XX)`.

---

## Open — the human's, and blocking nothing else

Four `=>` slots in `project/plans/design-one-source-for-shipped-files.md`:

- **Q3** — what `scope` should be called, pending a shared understanding of what it is for. It
  answers exactly one question, "which of the two root directories does this path hang off", and
  nothing consults it for ownership.
- **Q5** — which directory structure states the root once `scope` is gone.
- **Q6** — may a project change a file that lives in its own directory? Today it may not:
  `.claude/skills/` is overwritten on every `sp init`.
- **Q1 and Q2 are closed**, and Q1 was closed the opposite way from how it was asked.

---

## USJ, before any code (#200)

1. **`ears-to-hear` has replied** and no session has read it:
   `~/github/nida-institute/ears-to-hear/scriptorium/collab/sp/2026-08-24-usj-is-coming.md`, from
   §141. Two corrections to the premise, answers to Q1–Q6, a licensing section, and §7 on what
   is the human's to rule. That repository consumes USJ second-hand and is the only one that
   publishes, so it carries the licensing exposure (#212).
2. **`discourse-flow`'s reply** names two blockers the design does not cover — Levinsohn's 33
   discourse feature types have no home in the five `include` families, and variants are not a
   file to load but a second witness to align into the word sequence.
3. **§4.4 of `design-scripture-representations.md` is unruled** — the Greek/Hebrew asymmetry.
   Five `=>` remain open there. Implementable as written, but a normalising ruling changes the
   payload and anything built first is wrong.
4. Start from the parked tag `wip/scripture-200` (`0bb1d5b`), which is on the remote.

---

## Parked, recorded, and not started

- **#211's migration itself** — 19 constants, 1,047 lines of content, one pass as ruled.
- **`docs/ai-context/sp/index.md` is stale**: four entries left the catalog and it has not been
  regenerated. `sp doctor` or `sp init --update` fixes it.
- **Consumer projects need the catalog changes made for them**, since they cannot know to do it.
- **The docstring sweep** — 21 test files and 7 modules under `src/llmflow/` still carry rulings
  and version history in comments. A guard test was proposed and is unapproved.
- **The unused `update` parameter** in the three `_configure_*` functions, which is why `sp init`
  rewrites those blocks without `--update`.
- **The `llmflow-init` marker name** — retired as a product name, and changing it is a migration
  because `read_delimited_block` matches it literally.

---

## Verify before trusting this file

```bash
git log --oneline -1                                     # 8d8ac2a, if not yet committed
git status --short | wc -l                               # 106
hatch run pytest -q                                      # 2970 passed, 26 skipped
du -sh tmp/pytest                                        # ~328K after a green run
ls /private/var/folders/*/*/T/pytest-of-* 2>/dev/null     # nothing
ls -l /private/tmp/llmflow.log 2>/dev/null                # nothing
grep -c '^=>' project/plans/design-scripture-representations.md   # 5
git ls-remote --tags origin wip/scripture-200            # 0bb1d5b
```

---

## Do NOT

- **Do not commit, push or merge.** Gates yes; the commit is the human's.
- **Do not run `sp doctor` here** without being asked. It writes, and step 7 of
  `design-ai-context-layout.md` — running it clean in this repository — has not been done.
- **Do not fill in a `=>`.** Only the human writes in those slots.
- **Do not record design, rulings or history in docstrings or comments.**
- **Do not commit or push `~/.claude`**, and do not restore the deleted memory files. 82
  uncommitted there is deliberate: it keeps the unfinished memory migration visible.
- **`~/.sp` has one dirty file**, `skills/load-context/SKILL.md`, byte-identical to this
  repository's template for it. Committing that store is the human's act.

---

## Key files

**Design** — `design-one-source-for-shipped-files.md` (the catalog's fields; four open) ·
`design-ai-context-layout.md` (#210) · `design-shipping-the-audit-method.md` (#214) ·
`design-scripture-representations.md` (§4.4 blocks #200) · `design-source-licensing.md` (#212)

**Issues, all open** — #200 USJ · #207 the suite writing outside the project · #210 the layout ·
#211 constants to templates · #212 licensing · #213 `sp clean` several pipelines · #214 the audit
method · #209 repository rename (unscheduled)

**Measured, so it is not re-derived** — a full run is 2970 tests in ~90 seconds and leaves 328 KB
in `tmp/pytest/` · 19 catalog entries still hold 1,047 lines of embedded content · 5 of 12
`generated` documents carry the generated marker and 5 of 9 `create-once` documents do · USJ costs
4.26x a milestone string before metadata and 11.78x as `discourse-flow` ships it · Lowfat departs
from document order in ~40% of Mark's verses
