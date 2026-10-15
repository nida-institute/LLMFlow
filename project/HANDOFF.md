# HANDOFF — 2026-10-15

Written against `43b1f2c` (level with `origin/dev`), for the commit that follows it — build step 2
of the Ears to Hear resources, #272: SDBG entries on `include: [senses]`.

## ▶ NEXT ACTION

**Confirm that commit landed**, then `git show HEAD`. If `git log -1` still shows `43b1f2c`, the
commit is the Captain's to run (`git commit -F tmp/commit-1.txt`) — do not run it; once it exists,
delete `tmp/commit-1.txt` by name.

Then **build step 3 of `project/plans/design-ears-to-hear-resources.md`** — `type: acai` (§3),
test first, walking the Captain through each decision. Ears to Hear's `build-book.yaml` fails
`sp lint` until it exists.

---

## Active threads

### 1. Ears to Hear resources, #272 — steps 1 and 2 built

- **Design:** `project/plans/design-ears-to-hear-resources.md` — §7 decided, plus step 2's D-G to
  D-L (2026-10-15) with their measurements.
- **Step 1:** `cb15dbc`, pushed.
- **Step 2, in this commit:** `src/llmflow/utils/sdgnt.py` (new reader), `dictionary_entries()`
  and `_attach_entries()` in `src/llmflow/utils/scripture.py` (attached in `_emit`),
  `dictionaries` under `senses` in `data/include-families.json`, `tests/test_sdbg_senses.py`
  (19), `docs/sp-language.md`.
- **Verify:** `hatch run pytest tests -q -m "not integration"` → 6,287 passed, 0 failed.
- **Steps left:** 3 `type: acai`; 4 `type: dictionary` (Tyndale by entry).
- **Data on this machine is the Captain's to register** (§2): SDGNT is not registered as
  `ubs-sdgnt` — `sp dataset add ubs-sdgnt --path ~/github/ubsicap/ubs-open-license`;
  `~/.sp/datasets/ACAI.yaml` points at `Clear/ACAI`, and step 3 wants `BibleAquifer/ACAI`.

### 2. Helm, #271 — committed at `300728d`

Everything left is Helm's, in Helm.

---

## In flight / not yet done

| whose | paths |
|---|---|
| **not updated, deliberately** | `src/llmflow/templates/project/docs/ai-context/sp/scripture-representations.md` — its `senses` row could mention `entries`, but its copy under `docs/ai-context/sp/` must match (`test_this_repository_matches_its_own_templates`) and is not the AI's to regenerate. Captain's call. |
| **incoming, unread** | `collab/discourse-flow/2026-10-12-the-project-copy-of-the-rules-lags-the-machine-copy.md` (committed by the Captain at `43b1f2c`) |
| **modified, not this session's** | `docs/ai-context/project/data-sources.md`, `project/open-decisions.md` |
| **untracked here, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/`, `scripts/representation-grid/` |
| **`~/.claude`** | 2 uncommitted files — reported, diff offered, not reviewed |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

## Decisions

**Awaiting the Captain:** whether #270 is in 0.2.1.30; whether the stale
`.claude/skills/release/SKILL.md` goes into `project/TODO.md`; any reply to Ears to Hear (his, by
project rule).

**Settled — do not reopen:** #272's §7 and D-G to D-L — notably the join is lemma and code, not
code alone (1,393 codes are filed under several headwords), and definitions are verbatim;
Helm's design §6; `stage-commits` forked.

## Do NOT

- **Write anything in Helm's tree** outside `collab/scripture-pipelines/`.
- **Write to `~/.sp`** — registrations are the Captain's to run. A real-data check uses a
  throwaway `$SP_HOME` under `tmp/`.
- **Edit `docs/ai-context/sp/`**, or regenerate it unasked.
- **Commit, push, open a PR or merge.** `/stage-commits`.
- **Reply to Ears to Hear unasked.**
- **Do not `sp run` unasked.**

## Key files & links

- `project/plans/design-ears-to-hear-resources.md`, #272
- `collab/ears-to-hear/2026-10-06-acai-sdbg-and-the-tyndale-bible-dictionary.md`
- `project/TODO.md` → 🚢 THE NEXT RELEASE
