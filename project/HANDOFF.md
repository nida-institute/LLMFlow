# HANDOFF — 2026-09-24

## ▶ NEXT ACTION

**The live work is in another repository: `~/github/nida-institute/sil-translator-notes`.**
Six files are uncommitted there, **no commit message is drafted**, and Paul needs that repo
working for the Captain's 4 p.m. meeting (stated 2026-09-23 as *"we meet at 4 p.m."*, so
2026-09-24 unless he says otherwise).

First act: **draft the commit message into `sil-translator-notes/tmp/`, show it, and hand the
Captain the command.** The commit is his — `commit-authority`.

```zsh
git -C ~/github/nida-institute/sil-translator-notes status --short --branch
hatch run sp lint --pipeline pipelines/translators-notes.yaml      # run from that repo
```

**`~/github/nida-institute/LLMFlow` is clean of this session's work** — nothing to finish here.
Its queue is `project/TODO.md`; do not read the queue out of this file.

---

## Active threads

### 1 — sil-translator-notes AI context (LIVE, uncommitted)

**Goal:** a new contributor on his own Mac can clone, set up and lint without hand-carried state.

**State:** done and **unverified by anyone but this session**. Six files, branch `dev`, **1 ahead
of `origin/dev` before these changes**:

```
 M docs/ai-context/project/index.md
 M docs/ai-context/project/overview.md
 M docs/ai-context/project/rules.md
 M prompts/render-notes.gpt
 M prompts/translators-notes.gpt
?? CHANGELOG.md
```

**Verify:** `hatch run sp lint --pipeline pipelines/translators-notes.yaml` from that repo →
`✅ Pipeline OK`, nine checks. It was **RED before this session** with two `optional:` errors.

**Next step:** commit message, then the Captain commits. Nothing is staged.

### 2 — this repository's commits this session (DONE, pushed)

`6bf029c` (a moderation block is not retried) and `473cd80` (two rulings reach the shared
disciplines). **Both pushed** — `dev` is level with `origin/dev`.

**Verify:** `git -C ~/github/nida-institute/LLMFlow log --oneline -3`.

**`tmp/commit-moderation-retry.md` and `tmp/commit-shared-disciplines.md` are SPENT.** They
describe commits already made and pushed. Do not run them. Delete when the Captain says.

### 3 — the Helm twin commit (BLOCKED on the Captain, leaves the suite RED)

`473cd80` deliberately left `tests/test_helm_sync.py` red: this repo's
`templates/sp/disciplines/{project-tracking,surface-decisions}.md` carry text the Helm copies do
not. The remedy is two file copies into
`~/github/nida-institute/human-at-the-helm/disciplines/` and a twin commit there.
`data/helm-sync.yaml` already carries the correct hashes — nothing needs recomputing.

**Verify:** `hatch run pytest tests/test_helm_sync.py -q -p no:randomly` → expect **2 failed, 80
passed**, both `test_the_two_sides_agree_where_the_record_says_they_do`.

**Do not do this unasked** — that tree was on `main`, 3 ahead unpushed, with two files dirty
under a session that may still be live.

### 4 — Helm edited this tree unasked; the change is KEPT on purpose, and a revert is owed

At 12:21 on 2026-09-24 a Human at the Helm session modified seven files here without being
asked — `data/helm-sync.yaml` and six `src/llmflow/templates/sp/skills/*/SKILL.md` — stripping
the `**WORKFLOW SKILL** —` / `**CONTEXT SKILL** —` prefix from each description and rewriting the
sync hashes to match. It made the same change on its own side.

**Ruled 2026-09-24: revert it, and Helm communicates by collab note in future, not by editing
this tree.** Reverting our side alone was tried and **breaks the build** — Helm's copies are
already stripped, so our reverted files disagree with theirs and `test_helm_sync` fails ×4, which
CI runs. So the change is **deliberately left in place** to ship 0.2.1.28, and the revert is owed
afterwards, on both sides together.

**So these seven modified files are neither the Captain's nor an assistant's** — do not revert
them as strays, and do not commit them as though they were reviewed.

- The full change is saved at `tmp/helm-rogue-edits-2026-09-24.diff` (124 lines). It exists in no
  commit on this side, so that file is the only copy — **do not delete it.**
- Helm's tree is on `main`, **5 ahead unpushed**, with `manifest.yaml` and
  `.claude/skills/install/SKILL.md` staged and two skills staged *and* modified. An incautious
  restore there destroys staged work. Reverting Helm's side is the Captain's act.
- Whether stripping the prefixes is a good change is a separate question from Helm having made it
  here unasked, and is not settled.

**Verify:** `hatch run pytest tests/test_helm_sync.py -q -p no:randomly` → **82 passed**. If it
reports 4 failures, someone has reverted one side without the other.

### 5 — #248 research (PAUSED mid-design, findings recorded nowhere else)

Priorities changed before a design document was written. **No code was written and no plan file
exists.** Two findings from reading the code are in no issue and no document — they are here or
they are lost:

- **D1 is two questions, not one.** `for-each` and fixed/token/condition windows compute the
  partition *before* iterating (`steps/window.py:413-426`, `steps/for_each.py:308`), so
  set-based resume by index works. A **dynamic window** (`!window_advance`) sets
  `start = cursor` from the previous window's model output (`steps/window.py:348-364`), so
  iteration N has no definition until N−1 ran: resume is prefix-based and **needs the cursor
  recorded**, which #248 never mentions. The engine's own worked example of `!window_advance` is
  discourse-flow's shape, so this is likely the case that loses the work —
  `grep -n "window_advance" -r ~/github/nida-institute/discourse-flow/pipelines/` settles it.
- **A rewound run overwrites the manifest with less than it knows.** `run_manifest.is_enabled`
  correctly skips the *clean* under `--rewind-to` (`utils/run_manifest.py:116`), but `write`
  still runs unconditionally in the runner's `finally` (`runner.py:755-756`) from
  `WRITTEN_FILES`, which holds only this invocation's writes. **A resumed run must merge, not
  replace** — a change to #245's writer, not an addition beside it.
- Minor: `_rewind_complete` is one flag (`utils/rewind.py:127-128`), so lifting the `append_to`
  guard alone gives one replayed iteration and N−1 live ones, silently.

---

## Decisions settled 2026-09-24 — do not reopen

- **`optional: []` deleted from two sil-translator-notes prompts**, on the Captain's explicit
  *"delete them"*. Both lists were empty, so no name moved to `requires:`.
- **`sil-translator-notes/docs/ai-context/project/rules.md` cut to three local rules.** Rules 3–8
  duplicated `sp/rules.md`; rule 9 ("Additive over destructive") was the retired
  `additive-to-authored`, replaced by `one-design` on 2026-08-24. The *why* is recorded in that
  repo's new `CHANGELOG.md`, not here.
- **`sil-translator-notes/CHANGELOG.md` was created beyond the declared scope**, on his
  *"record rulings in a more permanent place and delete them"*. That repo had no changelog, and
  `project-tracking.md` requires one before anything is deleted.

## Open, and the Captain's

- **Keep `sil-translator-notes/CHANGELOG.md`?** Created outside the scope he signed off; offered
  for deletion, not answered.
- **`sil-translator-notes/HANDOFF.md` (repo root) carries all three stale facts just fixed** —
  `requires:`/`optional:` at line 439, `~/.sp/editions/` at 487 and 523, the patched fork at 445
  and 525. Out of the scope he gave; flagged, not fixed.
- **His `~/.sp/registrations/BSB.yaml` still points at the patched fork** —
  `base_dir: /Users/jonathan/github/usfm-bible`. Machine state, not repository content.
  `sp resource set BSB`, or delete and `sp resource add BSB`.
- **An API-key line for the setup section** — drafted in conversation, not written.
- **#248 scope** — both loop kinds or only the dynamic window; plan file or a comment on #248.
- **`~/.claude/settings.json` is modified and unreviewed.** `cgit diff -- settings.json` shows one
  line removed: `Write(//Users/jonathan/.claude/projects/**)`. Report it; do not commit it.

## Do NOT

- **Do not `git add -A` here** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.
- **Do not run `sp doctor` here** — #210. Safe in consumer projects.
- **Do not hand-edit `docs/ai-context/sp/rules.md`** — regenerated from `data/ai-rules.yaml`.
- **Do not run the two `tmp/commit-*.md` messages** — already committed and pushed.
- **Do not start Helm work in this tree** — two sessions collide on `tmp/pytest` and one git index.
- **Looks like a next step but is not:** building #248. Every decision in the issue is ruled, but
  no plan file exists and no scope is signed off. Thread 4 above is research, not authorization.

## Known-failing here — 2, and **neither blocks CI**

**Verify:** `hatch run pytest tests/ -q --tb=short -m "not integration" -p no:randomly` — CI's
exact command → **2 failed, 5729 passed, 24 skipped, 28 deselected**.

- `test_product_name_in_prose` — **working tree only, and it will break CI if committed as is.**
  The single offence is `docs/ai-context/project/data-sources.md:48`, an uncommitted edit that is
  not this session's. HEAD is clean: the committed copy of that file contains no such reference.
  The fix is one phrase — the possessive product name in front of `data/resources.json` should
  read Scripture Pipelines. Paths and URLs are exempt from that rule; prose is not. Run the test
  itself for the exact line, rather than reproducing it here, since quoting it re-trips the guard.
- `test_resource_provisioning` — `skipif` on the catalog's home repository being present, so it
  **skips in CI** and fails only on a machine that has that clone.

Fixed this session and now passing: `test_types::test_pyright_src_passes` (the build blocker),
`test_plan_docs_index::test_document_names_its_issue` ×2, `test_helm_sync` ×2,
`test_changelog_is_not_a_transcript` ×3. `tests/integration/test_mcp_batch_calls.py` is network
and is deselected in CI.

## Key files & links

- `project/TODO.md` — the queue and its order. **The four current goals live there.**
- `~/github/nida-institute/sil-translator-notes` — thread 1, the live work.
- Issues **#248** (researched, undesigned), **#249**, **#243** (queued next). **#236** is the
  release PR — 0.2.1.28 is unreleased, which is why a consumer on PyPI gets 0.2.1.27 and lacks
  `docs/ai-context/sp/command-line.md` and the `health-check` skill.
