# HANDOFF — 2026-10-15

Written against `51b6fff` (level with `origin/dev`), for the commit that follows it — build step 3
of the Ears to Hear resources, #272: `type: acai`.

## ▶ NEXT ACTION

**Confirm that commit landed**, then `git show HEAD`. If `git log -1` still shows `51b6fff`, the
commit is the Captain's to run (`git commit -F tmp/commit-1.txt`) — do not run it; once it exists,
delete `tmp/commit-1.txt` by name.

Then **build step 4 of `project/plans/design-ears-to-hear-resources.md`** — `type: dictionary`,
Tyndale by entry (§5), test first, walking the Captain through each decision. The `dictionary`
ids `type: acai` now returns are what it looks up.

---

## Active threads

### 1. Ears to Hear resources, #272 — steps 1–3 built

- **Design:** `project/plans/design-ears-to-hear-resources.md` — §7, plus D-G to D-P (2026-10-15)
  with their measurements.
- **Step 1:** `cb15dbc`. **Step 2:** `51b6fff`. Both pushed.
- **Step 3, in this commit:** `data/acai.json` (declaration), `src/llmflow/utils/acai.py`
  (reader), `src/llmflow/steps/acai.py` (handler), a schema branch in
  `src/llmflow/pipeline_schema.py`, dispatch in `src/llmflow/runner.py`, the `ACAI` dataset in
  `src/llmflow/utils/resource_preflight.py`, `tests/test_acai_step.py` (18), `docs/sp-language.md`,
  `docs/cli-api.json` (regenerated), `acai.json` in `pyproject.toml` and both Nuitka commands in
  `.github/workflows/build.yml`.
- **Verify:** `hatch run pytest tests -q -m "not integration"` → 6,317 passed, 0 failed.
- **On real data:** MRK 1:1-8 → 23 entities, 28 verse rows, as the design measured; a load takes
  0.77 s, a lookup 0.51 s.
- **Steps left:** 4 `type: dictionary`.
- **Registered on this machine by the Captain:** `ACAI` → `~/github/BibleAquifer/ACAI`.
  **Not yet:** `ubs-sdgnt` — `sp dataset add ubs-sdgnt --path ~/github/ubsicap/ubs-open-license`.

### 2. Helm, #271 — committed at `300728d`

Everything left is Helm's, in Helm.

---

## In flight / not yet done

| whose | paths |
|---|---|
| **the Captain's, if wanted** | a report to BibleAquifer that ACAI names 2CO 13:14, which `org` lacks (D-P) |
| **not updated, deliberately** | `src/llmflow/templates/project/docs/ai-context/sp/scripture-representations.md` — its copy under `docs/ai-context/sp/` must match, and is not the AI's to regenerate |
| **pre-existing** | `ruff` I001 import order in `src/llmflow/runner.py` and `src/llmflow/utils/linter.py` — both predate this work |
| **incoming, unread** | `collab/discourse-flow/2026-10-12-the-project-copy-of-the-rules-lags-the-machine-copy.md` |
| **modified, not this session's** | `docs/ai-context/project/data-sources.md`, `project/open-decisions.md` |
| **untracked here, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/`, `scripts/representation-grid/` |
| **`~/.claude`** | 2 uncommitted files — reported, diff offered, not reviewed |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

## Decisions

**Awaiting the Captain:** whether #270 is in 0.2.1.30; whether the stale
`.claude/skills/release/SKILL.md` goes into `project/TODO.md`; any reply to Ears to Hear (his, by
project rule).

**Settled — do not reopen:** #272's §7 and D-G to D-P — notably SDGNT joins on lemma and code;
definitions are verbatim; ACAI is declared in `data/acai.json` rather than the vendored catalog;
`dictionary` is a list of `{id, title}`; a reference outside `org` is dropped with one warning.
Helm's design §6; `stage-commits` forked.

## Do NOT

- **Write anything in Helm's tree** outside `collab/scripture-pipelines/`.
- **Write to `~/.sp`** — registrations are the Captain's to run. Real-data checks read only.
- **Edit `docs/ai-context/sp/`**, or regenerate it unasked.
- **Commit, push, open a PR or merge.** `/stage-commits`.
- **Reply to Ears to Hear, or report to BibleAquifer, unasked.**
- **Do not `sp run` unasked.**

## Key files & links

- `project/plans/design-ears-to-hear-resources.md`, #272
- `collab/ears-to-hear/2026-10-06-acai-sdbg-and-the-tyndale-bible-dictionary.md`
- `project/TODO.md` → 🚢 THE NEXT RELEASE
