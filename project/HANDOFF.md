# HANDOFF — 2026-10-14

Written against `e3abece` ("docs(project): the version number is not a question"), for the
commit that follows it — the Helm half of 0.2.1.30, #271.

## ▶ NEXT ACTION

**Confirm the Helm commit landed**, then show it with `git show HEAD`. If `git log -1` still
shows `e3abece`, the commit is the Captain's to run (`git commit -F tmp/commit-1.txt`) — do not
run it; once it exists, delete `tmp/commit-1.txt` by name.

Then the queue: `project/TODO.md` → 🚢 THE NEXT RELEASE. The Helm half's remaining work is all
Helm's, done in Helm; the Ears to Hear half has no design yet.

---

## Active threads

### 1. Helm coordination, #271 — built, staged for one commit

- **Design:** `project/plans/design-helm-coordination.md`, decided — §6 answered A throughout,
  `stage-commits` forked, both the Captain's, 2026-10-14.
- **Built:** `pending` status in `data/helm-sync.yaml`; `tests/test_helm_sync.py` checks only this
  repository against its record; `tools/sync_helm.py` reads both sides at `HEAD`, `--note`
  replaces `--apply`; `tests/test_sync_helm_tool.py` (20); `EXEMPT_KEYS`/`HELM_EXEMPT` deleted;
  project rule "Human at the Helm is written in Helm".
- **Four files `pending` on Helm:** `disciplines/github-authority.md`, `project-tracking.md`,
  `workflow.md`, `skills/authorize`, each with its date and note.
- **Verify:** `hatch run pytest tests -q -m "not integration"` → 6,225 passed, 0 failed, **0
  xfailed** once the design document is tracked. `hatch run python tools/sync_helm.py` reports
  without writing.

### 2. An incident during the build — resolved

The first, deliberately failing run of `test_apply_is_gone` called `main(["--apply"])` on the
**old** script, against the real Helm clone. It overwrote four Helm files and refreshed this
record. Restored at the Captain's go: three disciplines from Helm's `HEAD`, one hunk removed
from `skills/authorize/SKILL.md` (now blob `4248b5c`, its prior state). Helm's status matched
its earlier listing line for line. The test now points at a throwaway clone.

---

## In flight / not yet done

| whose | paths |
|---|---|
| **Helm's, in Helm** | 7 commits unpushed; 7 `skills/*/SKILL.md` modified; untracked `skills/stage-commits/`, plans, `collab/`. Its handoff is dated 2026-10-01 |
| **untracked here, origin unknown — ask** | `.cursorrules`, `.windsurfrules`, `project/0x28.md`, `tests/test_stage_commits_checks_the_handoff.py`, `collab/`, `scripts/representation-grid/` |
| **modified, not this session's** | `docs/ai-context/project/data-sources.md` |
| **`~/.claude`** | 2 uncommitted files — reported, diff offered, not reviewed |

`gui/frontend/node_modules` is tracked and shows ~8,000 deletions. **Never `git add -A`.**

## Decisions

**Awaiting the Captain:** Helm's `=>` slots D1–D4 in its
`project/plans/design-coordinating-changes-with-sp.md` are empty; his answers are in this
repository's design §1, and filling Helm's is his or a Helm session's. Whether #270 is in
0.2.1.30. Whether the stale `.claude/skills/release/SKILL.md` goes into `project/TODO.md`.

**Settled — do not reopen:** B and A for Helm; D1–D4 and D-A–D-D as recorded in the design;
`stage-commits` forked; version bumps per the project rule "The version number is not a
question".

## Do NOT

- **Write anything in Helm's tree** outside `collab/scripture-pipelines/` — project rule
  "Human at the Helm is written in Helm". `--note` is the one sanctioned write, and only when
  asked.
- **Commit, push, open a PR or merge.** `/stage-commits`.
- **Do not run `sp init --update` here** without regenerating `docs/ai-context/sp/rules.md` after.
- **Do not `sp run` unasked.**

## Key files & links

- `project/plans/design-helm-coordination.md`, #271
- `tools/sync_helm.py`, `data/helm-sync.yaml`
- `project/TODO.md` → 🚢 THE NEXT RELEASE
