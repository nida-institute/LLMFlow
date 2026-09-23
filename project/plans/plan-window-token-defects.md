# Fixing the three token-windowing defects

Status: ruled (2026-09-22) → #246. Defect 2 ruled **A** by the Captain; the other two need no ruling.

Work order for #246. The issue carries the evidence and the reasoning; this carries the order of
work and what each change must not touch.

## Order of work, test first in every case

**1. Partiality by fill, not position.** `steps/window.py:112`.

- Failing test first, in `TestBuildWindowsToken` (`tests/test_window_step.py`, around line 995):
  6 single-token items at 3 per window with `include_partial=False` must return **2** windows.
  Today it returns 1, because the final window reaches the end of the input and is therefore
  called partial regardless of how full it is.
- Fix: decide partiality from the accumulated token total against `size_by_tokens`, the way
  `_build_windows_fixed:34` decides it from `len(window) == size`.
- `test_include_partial_true` and `test_include_partial_false` must stay green — both use 5 items
  at 3 per window, where the last window is genuinely short.

**2. `include_partial` under `!window_advance` — ruling A: honour it.** `steps/window.py:272`.

- Failing test first: a dynamic window whose final slice is short, with `include_partial: False`,
  must not yield that final window.
- Fix: read the parameter in `_run_window_dynamic`, where it is currently accepted and never
  used.
- **The cursor still governs when the loop ends.** `include_partial` decides only whether a final
  short window is *yielded*, never whether iteration continues — a null cursor stops the loop as
  it does today.

**3. One token counter.** `steps/window.py:81-96` and `133-149`.

- No new test: this is a refactor with identical behaviour, and the existing
  `TestBuildWindowsToken` cases plus the new ones above are the guard.
- Fix: one helper owning the tiktoken import, the encoding lookup and `count_tokens`; both
  callers use it.
- Do it **last**, so the two behavioural fixes land against the code they were written for.

## What does not change

- The encoding fallback to `cl100k_base` for an unrecognised model. That is D3a of
  `project/plans/design-usj-operations.md`, ruled *warn and approximate*, and
  it is not this issue.
- What the budget counts — per-item `json.dumps` rather than the assembled payload. D3b/D3c of
  the same document.
- `size_by_tokens` and `stride_by_tokens` remaining literal-only.
- `_build_windows_fixed`, `_build_windows_condition`, and every non-token windowing path.
- `docs/llmflow-language.md`, unless the Captain wants the fill-versus-position behaviour stated
  there — the field table does not currently define what "partial" means.

## Verification

- `hatch run pytest tests/test_window_step.py tests/test_window_advance.py -q`
- `hatch run pytest -q` against the known baseline: `test_types` (npx broken, reporting nothing
  rather than clean), `test_plan_docs_index::test_document_names_its_issue` ×2,
  `test_product_name_in_prose`, `test_resource_provisioning`.
- No pipeline in `pipelines/` or in the shipped templates uses `size_by_tokens`, so nothing in
  this repository exercises the changed path end to end; `nida-institute/discourse-flow` sets
  `include_partial: true` and is unaffected by change 1.

## Done when

Every box below carries its evidence beside it, not the word *done*.

- [x] a final token window that exactly fills the budget survives `include_partial: false` —
      `test_window_step.py::TestBuildWindowsToken::test_exactly_full_final_window_survives_include_partial_false`.
      Seen red first (1 window, expected 2); `steps/window.py` now decides partiality with
      `total < size_by_tokens`
- [x] `include_partial: false` drops a short final dynamic window —
      `test_window_advance.py::TestIncludePartialUnderACursor::test_false_drops_a_short_final_window`,
      with `test_true_keeps_a_short_final_window` as the control so the drop is the flag and not
      the cursor. Both driven through `load_pipeline(...).run()` per `project/rules.md` rule 1,
      and re-verified red with the guard disabled
- [x] one counter, both call sites — `_token_counter` at `steps/window.py:73`, called from
      `_build_windows_token` and `_slice_window_from_pos`. `_slice_window_from_pos` now returns
      `(slice, total)` so a caller can tell a filled window from one that ran out of input
- [x] full suite at the baseline — **5710 passed, 6 failed**, every failure pre-existing:
      `test_types` (npx broken), `test_plan_docs_index::test_document_names_its_issue` ×2,
      `test_product_name_in_prose`, `test_resource_provisioning`, and the network-dependent
      `tests/integration/test_mcp_batch_calls.py`
- [ ] CHANGELOG entry referencing #246 — **not written.** `project/TODO.md` records that the file
      carries both a dated `## 0.2.1.28 — 2026-09-09` heading and an `## Unreleased` section above
      it, so which one this belongs under is the Captain's call
