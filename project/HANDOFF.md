# HANDOFF — 2026-09-22

## ▶ NEXT ACTION

**Commit #246.** It is built, green, and nothing else should start on top of it. `dev` is at
`427a086`, **level with `origin/dev`** (0 ahead, 0 behind).

This session's files, and only these:

- `src/llmflow/steps/window.py` — the three fixes
- `tests/test_window_step.py`, `tests/test_window_advance.py` — the tests
- `project/plans/plan-window-token-defects.md` (**new, untracked**) — the work order
- `project/plans/design-scripture-window-by-token-budget.md` → `design-usj-operations.md`
  (**a rename — stage both halves or history does not follow**)
- `project/TODO.md`, `project/plans/README.md` (regenerated)

**One box in the plan is unticked and it needs your ruling first:** the CHANGELOG entry for
#246. `CHANGELOG.md` carries both a dated `## 0.2.1.28 — 2026-09-09` heading *and* an
`## Unreleased` section above it, so which one this belongs under is the Captain's call. Everything
else in `plan-window-token-defects.md` is ticked with its evidence beside it.

**Verify before committing:** `hatch run pytest -q` → **5710 passed, 6 failed**, every failure
pre-existing: `test_types` (npx broken — it reports *nothing*, not clean),
`test_plan_docs_index::test_document_names_its_issue` ×2, `test_product_name_in_prose`,
`test_resource_provisioning`, and `tests/integration/test_mcp_batch_calls.py` (network).

**Then `project/TODO.md`.** Its Active section carries the queue and its order. Do not read the
queue out of this file.

---

## Active threads

### 1. #246 — built, uncommitted

**State: done and green.** Three defects in token windowing:

- partiality decided by **fill** (`total < size_by_tokens`), not by position
- `include_partial` honoured under `!window_advance` — **ruled A by the Captain**
- one `_token_counter` (`steps/window.py:73`), both call sites; `_slice_window_from_pos` now
  returns `(slice, total)`

**Verify:** `hatch run pytest tests/test_window_advance.py tests/test_window_step.py -q` → 95
passed. Both behavioural tests were seen RED before their fix, and the converted dynamic test was
re-verified RED with the guard disabled.

**Next step:** the CHANGELOG ruling above, then the commit.

### 2. Five issues filed today — #246 is the only one with code

| # | subject | state |
|---|---|---|
| [#246](https://github.com/nida-institute/LLMFlow/issues/246) | token windowing defects | **built, uncommitted** |
| [#247](https://github.com/nida-institute/LLMFlow/issues/247) | truncation reported as malformed JSON, retried 3× identically | no code |
| [#248](https://github.com/nida-institute/LLMFlow/issues/248) | `--rewind-to` cannot resume a loop | no code, **D3a open** |
| [#249](https://github.com/nida-institute/LLMFlow/issues/249) | `parallel:` untested past `type: function`; telemetry loses records | no code, not scheduled |
| [#250](https://github.com/nida-institute/LLMFlow/issues/250) | 29 test files bypass the object model against 12 that use it | no code |

**The Captain's goal is #246, #247, #248, all for discourse-flow** — recorded in
`project/TODO.md`.

**Verify:** `gh issue view 247 --repo nida-institute/LLMFlow`.

### 3. `project/plans/design-usj-operations.md` — ruled, renamed, unbuilt

**State: D1–D4 and D3a/D3b/D4a all answered by the Captain. One slot open: D3c.**

Renamed and retitled this session from `design-scripture-window-by-token-budget.md`, because D2
ruled there is no verse-sid cursor and D4a ruled the subject is not windowing. **Nothing is
built** — it is still a design, not authorization.

**Verify:** `grep -n "^Status:" project/plans/design-usj-operations.md`. Not `git log --follow` —
the document was rewritten as well as renamed, so git records it as a delete plus an add rather
than a rename, and `--follow` does not reach the old history. Use
`git log --diff-filter=D -- project/plans/design-scripture-window-by-token-budget.md` for that.

### 4. The reply to discourse-flow is sent — and they have already answered in code

`discourse-flow/collab/sp/2026-09-22-segment-text-landed-and-the-windowing-ask-is-ruled.md`.
**Tracked and committed in their tree** at `0bfc786`, not untracked. Our draft was deleted so the
note has one home.

**They acted on #249 within the hour.** `0bfc786` — *"every for-each runs one iteration at a time,
and it is guarded (#98)"* — pins `subdivide_candidates` from `parallel: 5` to `parallel: 1` and
adds a test walking every step, nested loops included, that fails on any `parallel` above 1. Their
commit message cites LLMFlow#249 and the telemetry race.

**And they have disconfirmed a claim this session made.** Our note said #247 was *"the one we
expect you have felt"*. Their commit message records the opposite, measured: *"the segment defect
is not truncation. All 13 generate_segments responses of the last run parse as complete JSON, and
the 21-verse pericope returned 32,741 characters holding one segment, so the model chose one.
LLMFlow#247 is real and is not this."* Their open candidate is `supporting_evidence`, at 35-83% of
each response.

**#247 stands on its own evidence** — the engine genuinely does report truncation as malformed
JSON and retry it three times identically — but **it is not discourse-flow's segment defect**, and
nothing in this repository should be built on the assumption that it is.

**Verify:** `git -C ../discourse-flow show 0bfc786 | head -30`.

---

## In flight / not yet done

- **Nothing pushed this session.** `dev` == `origin/dev` at `427a086`. A push is the Captain's own
  act and has not been requested.
- **`project/TODO.md`'s `Tell them it has landed` is now ticked** — done 2026-09-22.
- **Uncommitted and the Captain's, not this session's:** `data/models.json`,
  `docs/ai-context/project/data-sources.md`, `docs/ai-context/sp/github-workflow.md` and its
  template twin, `.cursorrules`, `.windsurfrules`, `project/0x28.md`.
- **Three inbound collab notes still untracked** in `collab/discourse-flow/`, all 2026-09-21.
  `plans-are-temporary` wants them tracked.
- **`~/.claude/settings.json` is still modified** — the unreviewed one-line change reported at
  session start (a `Write(//Users/jonathan/.claude/projects/**)` permission removed). Not this
  session's; `cgit restore settings.json` reverts it.

## Decisions settled — do not reopen

- **`include_partial` under a cursor: honour it (A), not refuse it (B).** The Captain's ruling.
- **The three operations are USJ operations, not windowing operations** — nothing in flatten,
  locate or rebuild mentions a window, so they are grouped as USJ and the group is open.
- **`window` stays domain-blind.** *"Windowing has no idea what an sid is."* The cursor stays a
  list index; translating a domain identifier to a position is the pipeline's.
- **Remote token counting is dropped, and not for cost.** The budget that breaks a run is the
  **output** one; no input-side count predicts it, and the exact input count comes back free in
  `usage`. Recorded in the design document so it is not re-proposed.
- **Auto-raising `max_tokens` on truncation was rejected** — it is the engine spending the
  Captain's money unasked. #247 reports the derivable ceiling instead and forbids a guessed number.
- **A pure helper may be tested by direct call** — `project/rules.md` rule 1's carve-out. That is
  why `_build_windows_token`'s test was left as a direct call while the two step-level tests were
  converted to `load_pipeline(...).run()`.

## Do NOT

- **Do not run two pytest processes at once** — they share `tmp/pytest`, and it happened this
  session. Recovery: `chmod -R u+w tmp/pytest` then `rm -rf tmp/pytest`; the fake `~/.sp` inside it
  is read-only by `sp`'s own `_lock_sp_dir()`, so `rm -rf` alone fails.
- **Do not `git add -A`** — `gui/frontend/node_modules` is tracked, ~8,000 deletions.
- **Do not run `sp doctor` in this repository** — #210. Safe in consumer projects.
- **Do not read a passing suite as type-checked** — `npx` is broken, so `test_types` reports
  nothing rather than reporting clean.
- **Do not fix the two pre-existing `test_document_names_its_issue` failures** by inventing issue
  numbers; assigning them is the Captain's.
- **Looks like a next step but is not:** merging PR #236, and building #247/#248 — both wait on
  the commit above and, for #248, on D3a.

## Key files & links

- `project/TODO.md` — the queue and its order.
- `project/plans/plan-window-token-defects.md` — #246's work order and its evidence list.
- `project/plans/design-usj-operations.md` — ruled, unbuilt, D3c open.
- `utils/rewind.py:77-88` — #248's guard, and a **dangling pointer** to `docs/TODO.md`, which does
  not exist in this repository.
- Issues **#246**, **#247**, **#248**, **#249**, **#250**; **#236** is the release PR.
