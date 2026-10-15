# HANDOFF — 2026-10-15

Written against `f2e3104` (level with `origin/dev`), for the commit that follows it — build step 4
of the Ears to Hear resources, #272: `type: dictionary`. With it, all four build steps of
`project/plans/design-ears-to-hear-resources.md` are in.

## ▶ NEXT ACTION

**Confirm that commit landed**, then `git show HEAD`. If `git log -1` still shows `f2e3104`, the
commit is the Captain's to run (`git commit -F tmp/commit-1.txt`) — do not run it; once it exists,
delete `tmp/commit-1.txt` by name.

Then ask the Captain what is next: the build for #272 is complete, and what remains of it is his
(below). The queue is `project/TODO.md` → 🚢 THE NEXT RELEASE.

---

## Active threads

### 1. Ears to Hear resources, #272 — all four steps built

- **Design:** `project/plans/design-ears-to-hear-resources.md` — §7, plus D-G to D-U
  (2026-10-15) with their measurements.
- **Steps 1–3:** `cb15dbc`, `51b6fff`, `f2e3104`, pushed.
- **Step 4, in this commit:** `data/tyndale.json`, `src/llmflow/utils/dictionary.py`,
  `src/llmflow/steps/dictionary.py`, a schema branch, runner dispatch, the dataset in
  `src/llmflow/utils/resource_preflight.py`, `tests/test_dictionary_step.py` (15),
  `docs/sp-language.md`, `docs/cli-api.json`, `pyproject.toml`, `.github/workflows/build.yml`.
- **Verify:** `hatch run pytest tests -q -m "not integration"` → 6,344 passed, 0 failed.
- **On real data:** all 6,010 Tyndale articles load in 0.13 s; every article ACAI names for
  MRK 1:1-8 (18) and PHM 1:1 (8) resolves.
- **The Captain's, outstanding:**
  - register SDGNT — `sp dataset add ubs-sdgnt --path ~/github/ubsicap/ubs-open-license`;
  - check Ears to Hear's `scriptorium/pipelines/build-book.yaml` with `sp lint` (never checked
    from here);
  - any reply to Ears to Hear, and any report to BibleAquifer about 2CO 13:14 (D-P).
- **Not done, deliberately:** lint does not refuse a `dictionary` step with neither or both of
  `entries`/`acai` — the step refuses at run time. The schema's per-type branches carry keys
  only, so lint would need new machinery; a separate change if wanted.

### 2. Helm, #271 — committed at `300728d`

Everything left is Helm's, in Helm.

---

## In flight / not yet done

| whose | paths |
|---|---|
| **not updated, deliberately** | `src/llmflow/templates/project/docs/ai-context/sp/scripture-representations.md` — its copy under `docs/ai-context/sp/` must match, and is not the AI's to regenerate |
| **pre-existing** | `ruff` I001 import order in `src/llmflow/runner.py` and `src/llmflow/utils/linter.py` |
| **incoming, unread** | `collab/discourse-flow/2026-10-12-the-project-copy-of-the-rules-lags-the-machine-copy.md` |
| **modified, not this session's** | `docs/ai-context/project/data-sources.md`, `project/open-decisions.md` |
| **untracked here, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/`, `scripts/representation-grid/` |
| **`~/.claude`** | 2 uncommitted files — reported, diff offered, not reviewed |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

## Decisions

**Awaiting the Captain:** whether #270 is in 0.2.1.30; whether the stale
`.claude/skills/release/SKILL.md` goes into `project/TODO.md`.

**Settled — do not reopen:** #272's §7 and D-G to D-U — notably SDGNT joins on lemma and code;
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
