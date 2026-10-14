# HANDOFF — 2026-10-14

Written against `663a7fd`, staged into the commit that follows it (`tmp/commit-1.txt`,
"chore: dev becomes 0.2.1.30…").

## ▶ NEXT ACTION

**Confirm that commit landed, then get the Captain's go on rule 4.** If `git log -1` still shows
`663a7fd`, the commit is his to run (`git commit -F tmp/commit-1.txt`) — do not run it. Once it
exists: `git show HEAD`, then delete `tmp/commit-1.txt` by name.

Then the step he is walking through next: **rule 4, "the version number is not a question"**, for
`docs/ai-context/project/rules.md`. Drafted and shown to him 2026-10-12; not written, because
`CLAUDE.md`'s project block says `project/` is writable and its lower section forbids anything
under `docs/ai-context/`. His go is the tiebreak. His words, to quote in the rule: *"I will only
ever bump the version number this way, can I get the LLM to stop making this my responsibility to
decide every time?"*

After that, step 3 of his walk-through: **the macOS install check** — file an issue (rule
`agent-may-file-issues`). Then the queue in `project/TODO.md`.

---

## Active threads

### 1. 0.2.1.29 — shipped

- Tag `v0.2.1.29` on merge commit `ea8d86c` (parents `df4ee96`, `663a7fd`). Release run
  `38073882426`.
- **PyPI: done.** `https://pypi.org/pypi/scripture-pipelines/0.2.1.29/json` → 200, wheel and
  sdist uploaded 2026-10-12T16:09Z.
- **GitHub release: published**, three binaries — `gh release view v0.2.1.29`.
- **`Verify install script on macos-latest` failed**: `install.sh` got `curl: (56) … error: 403`
  on all 5 attempts at "Fetching latest Scripture Pipelines release…" (job `114276822461`).
  Ubuntu and Windows passed against the same release. Likely an unauthenticated GitHub API call
  refused on the macOS runner — **not confirmed**. A re-run was in progress 2026-10-12; check
  `gh run view 38073882426`. No issue filed yet.

### 2. dev is 0.2.1.30 — in this commit

- `CHANGELOG.md`'s top section is `## 0.2.1.30 (Not yet released)`, the Captain's wording.
- `tests/test_changelog_covers_the_version.py`: an undated top section passes on `dev`;
  `test_a_release_pr_dates_its_section` fails when `GITHUB_BASE_REF=main` (the release PR).
- `tests/test_changelog_is_not_a_transcript.py` checks the `(Not yet released)` section.
- `project/RELEASE_CHECKLIST.md` §1 and §12 match; the minor/major option is removed.
- **Verify:** `hatch run pytest tests -q -m "not integration"` → 6,227 passed, 25 skipped,
  12 xfailed, 0 failed (2026-10-12).

---

## In flight / not yet done

| whose | paths |
|---|---|
| **untracked, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/`, `scripts/representation-grid/` |
| **modified, not this session's** | `docs/ai-context/project/data-sources.md` |
| **`~/.claude`** | 2 uncommitted files (`CLAUDE.md`, `settings.json`) — reported, diff offered, not reviewed |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

## Decisions

**Awaiting the Captain:** rule 4's go (above). Whether `.claude/skills/release/SKILL.md`, which
still describes the retired `build-release.yml` and `hatch publish` of `llmflow`, goes into
`project/TODO.md` — asked, unanswered.

**Settled — do not reopen:**
- **The version is always the 4th component, and is not his to be asked about** — the Captain,
  2026-10-12, quoted above.
- **The next release's heading is `## <version> (Not yet released)`**, opened right after a
  release, with `pyproject.toml` bumped to match — the Captain, 2026-10-12.

## Do NOT

- **Commit, push, open a PR or merge.** `/stage-commits`.
- **Approve the `pypi` environment** — only `jonathanrobie` can, and it is his act.
- **Do not run `sp init --update` here** without regenerating `docs/ai-context/sp/rules.md` after.
- **Do not `sp run` unasked.**

## Key files & links

- `project/TODO.md` → 🚢 THE NEXT RELEASE (describes 0.2.1.29, now shipped — needs rewriting
  for Helm + Ears to Hear once the Captain sets scope)
- `project/RELEASE_CHECKLIST.md`
- https://github.com/nida-institute/LLMFlow/actions/runs/38073882426
