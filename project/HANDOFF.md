# HANDOFF — 2026-10-14

Written against `300728d` (the Helm half of 0.2.1.30, #271), for the commit that follows it — the
Ears to Hear design and its build step 1, #272.

## ▶ NEXT ACTION

**Confirm that commit landed**, then `git show HEAD`. If `git log -1` still shows `300728d`, the
commit is the Captain's to run (`git commit -F tmp/commit-1.txt`) — do not run it; once it exists,
delete `tmp/commit-1.txt` by name.

Then **build step 2 of `project/plans/design-ears-to-hear-resources.md` §6** — SDBG on senses:
a `provides` block for `ubs-sdgnt`, and the join onto `include: [senses]` as an `entries` list
(D-B A, D-D A). Test first. Steps 2–4 need data registered on this machine, which is the
Captain's to run (§2: `~/.sp/datasets/ACAI.yaml` points at `Clear/ACAI`; SDGNT and Tyndale are not
registered).

---

## Active threads

### 1. Ears to Hear resources, #272 — design decided, step 1 built

- **Design:** `project/plans/design-ears-to-hear-resources.md`, decided — §7 answered A, A, C, A,
  A, A, the Captain, 2026-10-14. D-C's option C (entities once, plus a verse index) was added in
  the discussion.
- **Step 1, in this commit:** `sp lint` refuses an undeclared step type (`_lint_step_type`,
  `src/llmflow/utils/linter.py`; `BUILTIN_STEP_TYPES` in `src/llmflow/plugins/loader.py`);
  `tests/test_lint_refuses_undeclared_types.py`; letter-level and two-code Louw-Nida pinned in
  `tests/test_scripture_families.py`.
- **Consequence:** Ears to Hear's `build-book.yaml` uses `type: acai`, which now fails `sp lint`
  until step 3.
- **Verify:** `hatch run pytest tests -q -m "not integration"` → 6,262 passed, 0 failed.
- **Steps left:** 2 SDBG on senses; 3 `type: acai`; 4 `type: dictionary` (Tyndale by entry).

### 2. Helm, #271 — committed at `300728d`

Everything left is Helm's, in Helm: commit its own work, adopt the four `pending` files, its
checksums and CI job, D3 in its rules, its `=>` slots D1–D4.

---

## In flight / not yet done

| whose | paths |
|---|---|
| **unpushed** | `82fc834`, `e3abece`, `300728d` on `dev` — the push is the Captain's |
| **incoming, unread** | `collab/discourse-flow/2026-10-12-the-project-copy-of-the-rules-lags-the-machine-copy.md` |
| **modified, not this session's** | `docs/ai-context/project/data-sources.md`, `project/open-decisions.md` |
| **untracked here, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/`, `scripts/representation-grid/` |
| **`~/.claude`** | 2 uncommitted files — reported, diff offered, not reviewed |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

## Decisions

**Awaiting the Captain:** whether #270 is in 0.2.1.30; whether the stale
`.claude/skills/release/SKILL.md` goes into `project/TODO.md`; any reply to Ears to Hear (his, by
project rule).

**Settled — do not reopen:** #272's §7 answers; Helm's design §6; `stage-commits` forked.

## Do NOT

- **Write anything in Helm's tree** outside `collab/scripture-pipelines/`.
- **Write to `~/.sp`** — the registrations steps 2–4 need are the Captain's to run.
- **Commit, push, open a PR or merge.** `/stage-commits`.
- **Reply to Ears to Hear unasked.**
- **Do not `sp run` unasked.**

## Key files & links

- `project/plans/design-ears-to-hear-resources.md`, #272
- `collab/ears-to-hear/2026-10-06-acai-sdbg-and-the-tyndale-bible-dictionary.md`
- `project/TODO.md` → 🚢 THE NEXT RELEASE
