# HANDOFF — 2026-10-15

Written against `fd01eee` (level with `origin/dev`), for the commit that follows it — the release
skill reduced to a pointer at `project/RELEASE_CHECKLIST.md`, and `project/TODO.md` brought up to
the Captain's 2026-10-15 rulings. All four build steps of #272 are in, through `fd01eee`.

## ▶ NEXT ACTION

**Confirm that commit landed**, then `git show HEAD`. If `git log -1` still shows `fd01eee`, the
commit is the Captain's to run (`git commit -F tmp/commit-1.txt`) — do not run it; once it exists,
delete `tmp/commit-1.txt` by name.

Then **#270**, item 3 of `project/TODO.md` → 🚢 THE NEXT RELEASE — the Captain's chosen fixes are
recorded there. Test first, one step at a time.

---

## Active threads

### 1. Ears to Hear resources, #272 — all four steps built

- **Design:** `project/plans/design-ears-to-hear-resources.md` — §7, plus D-G to D-U
  (2026-10-15) with their measurements.
- **Steps 1–4:** `cb15dbc`, `51b6fff`, `f2e3104`, `fd01eee`, all pushed. The Captain registered
  `ACAI`, `ubs-sdgnt` and `tyndale-open-bible-dictionary` on this machine.
- **Ears to Hear's `build-book.yaml` lints clean of everything these touch** (2026-10-15, run by
  the Captain from `ears-to-hear/scriptorium`); its two remaining errors are its own uncommitted
  edit, which dropped `pericope_index` from `narrative_profile`.
- **The Captain's, outstanding:** any reply to Ears to Hear, and any report to BibleAquifer about
  2CO 13:14 (D-P).

### 2. The rest of 0.2.1.30 — `project/TODO.md` → 🚢 THE NEXT RELEASE, items 3–5

- **Item 4, the release skill, in this commit:** `.claude/skills/release/SKILL.md` is a pointer
  at `project/RELEASE_CHECKLIST.md` plus the authority table; three new tests in
  `tests/test_release_skill_stays_with_the_engine.py` refuse the retired names. **Verify:**
  `hatch run pytest tests/test_release_skill_stays_with_the_engine.py` → 15 passed.
- **Raised, not changed:** `RELEASE_CHECKLIST.md` §6–7 show `gh pr merge` and the tag push
  without saying the human runs them. The Captain's call.
- **Items 3 (#270) and 5 (version skew)** are not started.
- **Not done, deliberately:** lint does not refuse a `dictionary` step with neither or both of
  `entries`/`acai` — the step refuses at run time. The schema's per-type branches carry keys
  only, so lint would need new machinery; a separate change if wanted.

### 3. Helm, #271 — committed at `300728d`

Everything left is Helm's, in Helm.

---

## In flight / not yet done

| whose | paths |
|---|---|
| **not updated, deliberately** | `src/llmflow/templates/project/docs/ai-context/sp/scripture-representations.md` — its copy under `docs/ai-context/sp/` must match, and is not the AI's to regenerate |
| **pre-existing** | `ruff` I001 import order in `src/llmflow/runner.py` and `src/llmflow/utils/linter.py` |
| **modified, not this session's** | `docs/ai-context/project/data-sources.md`, `project/open-decisions.md` |
| **untracked here, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/`, `scripts/representation-grid/` |
| **`~/.claude`** | 2 uncommitted files — reported, diff offered, not reviewed |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

## Decisions

**Awaiting the Captain:** whether `sp lint`'s raw traceback on a missing pipeline file is in
0.2.1.30 (raised in `project/TODO.md`); the `RELEASE_CHECKLIST.md` authority lines above.

**Settled — do not reopen:** 0.2.1.30 also takes #270 (fixes 2 and 3), the release skill, and
discourse-flow's version-skew report — the Captain, 2026-10-15, recorded in `project/TODO.md`.
#272's §7 and D-G to D-U — notably SDGNT joins on lemma and code;
ACAI and Tyndale are declared in `data/*.json`, not the vendored catalog; the dictionary text is
**Tyndale's own release** (D-Q, B — the Captain chose it over the Aquifer adaptation the ids belong
to), reached by title with `*` disregarded; bodies and definitions are verbatim. Helm's design §6;
`stage-commits` forked.

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
