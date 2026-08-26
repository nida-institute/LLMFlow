---
name: commit-ready
description: |
  **WORKFLOW SKILL** — Gate every commit/merge against this project's full definition of done:
  design or audit doc posted to a GH issue, TDD tests written and passing, full pytest suite
  clean, the GUI's TypeScript suite clean when the change touches gui/frontend, CHANGELOG
  updated, commit message properly formatted with issue refs and version bump,
  GitHub Actions passing after push, and branch merged + cleaned up.
  USE FOR: before committing; before merging a branch; before closing an issue.
  DO NOT USE FOR: auditing code quality — use this project's audit skills for that.
applyTo:
  - "**/*.py"
  - "**/*.yaml"
  - "CHANGELOG.md"
---

# Commit-Ready Skill

## Core Principle: Every Gate Must Pass Before Merging

Work through the checklist in order. Stop at any blocker and report it clearly.
Do not declare work done until every gate has been verified — not assumed.

Gates 1–5 happen before the commit. Gate 6 (Actions) requires the push.
Gate 7 (merge + cleanup) comes last.

---

## Gate 1: Issue & Documentation

- [ ] A GitHub issue exists for this work
  ```bash
  gh issue view <N>
  ```
- [ ] For non-trivial work: a design doc or audit doc exists in `docs/design/`,
  `docs/audits/`, or `tmp/` (to be moved before close)
- [ ] The design/audit doc (or a summary of key decisions) has been posted as a
  comment on the issue — so the full trajectory is preserved in the issue thread
- [ ] If the work required an audit first, confirm the relevant audit skill was run and
  findings addressed

**What counts as "non-trivial":** a new subsystem, a new extension point, a schema or
data-contract change, a new stage in an existing process. Bug fixes with a clear root cause
do not require a design doc. Each project records its own list in `docs/ai-context/`.

---

## Gate 2: Test-Driven Development

- [ ] Tests were written *before* or *alongside* the implementation (not after)
- [ ] There is a test that would have failed before this change and passes after
- [ ] Tests live in `tests/test_*.py` and are discovered by `pytest.ini`
- [ ] No test uses `logging.basicConfig()` or modifies file handlers
  (breaks `caplog` fixture — see CLAUDE.md Logger section)
- [ ] New tests have descriptive names (no `test_thing_1`, `test_thing_2`)

For bug fixes:
- [ ] A test reproducing the bug exists and is included in this commit

For features:
- [ ] Tests cover the new behavior, not just the happy path

---

## Gate 3: Full Test Suite (Local)

Run the full suite — not just the new tests:

```bash
hatch run pytest
```

- [ ] All tests pass (0 failures, 0 errors)
- [ ] Skipped tests are pre-existing (check `git stash && hatch run pytest` on main if unsure)
- [ ] Test count is at or above the previous baseline (no tests silently deleted)

Record the result — this line goes in the commit body:
```
Test coverage: XXXX passed, YY skipped (Z new tests added)
```

### The GUI's TypeScript suite

`hatch run pytest` does not run it. `gui/frontend/` is a separate TypeScript project with
its own Vitest tests, and CI runs them on every push — so a change there can pass every
check on this page and still turn the build red.

**If the change touches `gui/frontend/`, run what CI runs** (`.github/workflows/test.yml`):

```bash
cd gui/frontend
npm ci
npm test -- --run
npx tsc --noEmit
```

- [ ] Frontend tests pass
- [ ] `npx tsc --noEmit` reports no type errors

Deliberately conditional: a change that touches no TypeScript does not need Node installed
to be committable. Equally, a change that *does* touch it is not done because Python is
green — that was the gap this closed (#206).

Keep these commands identical to the workflow's. The local gate and CI describing the
definition of done in two different ways is how they drifted apart in the first place.

---

## Gate 4: Version & CHANGELOG

Do this before committing so the version bump is included in the same commit.

**Version increment** — 4th component only, never propose minor/major bumps:
```bash
grep "^version" pyproject.toml        # current version
grep "^## " CHANGELOG.md | head -5    # recent versions
```

- [ ] `pyproject.toml` version incremented
- [ ] `CHANGELOG.md` entry added at the top:

```markdown
## X.X.X.YY — YYYY-MM-DD

### New Features / Bug Fixes

- **Short title** — description. (Issue #XX)

### Test Coverage

- Added `tests/test_foo.py` with N tests
- Full test suite: **XXXX tests passing** (N new tests added)
```

- [ ] Issues referenced with `(Issue #XX)` notation in CHANGELOG

---

## Gate 5: Commit Message & Push

Follow the format from `docs/ai-context/github-workflow.md`:

**Subject line:**
```
feat: description (#93, #94)
```
or
```
fix: description (#97)
```

**Body:**
```
- Key change 1 (file:line)
- Key change 2 (file:line)
- Key change 3 (file:line)

Test coverage: XXXX passed, YY skipped (Z new tests added)

Closes #XX
Version: X.X.X.YY
```

Checklist:
- [ ] Subject line under 72 characters
- [ ] Issue number(s) in subject line parentheses
- [ ] Key changes listed with file references
- [ ] Test coverage line included
- [ ] `Closes #XX` or `Fixes #XX` for each issue being resolved
- [ ] Version line present with correct increment (4th component only)
- [ ] Commit created and branch pushed to origin

---

## Gate 6: GitHub Actions

Check after the push — Actions cannot run before the branch exists on origin.

```bash
gh run list --branch <branch-name> --limit 5
gh run view <run-id>
```

- [ ] All workflow jobs pass — not just the test job
- [ ] Build/release workflows pass if they exist
  ```bash
  gh workflow list
  ```
- [ ] If any job failed: read the failure log, fix, push again, recheck
  ```bash
  gh run view <run-id> --log-failed
  ```

**CRITICAL:** A passing local test suite does NOT mean GitHub Actions passed.
Check every job in every workflow that ran. Do not assume.

---

## Gate 7: Branch & Merge

First, identify the branching model for this repo:
- **Two-branch model** (main + dev): feature branches merge into dev; dev periodically merges to main. `dev` is permanent — never delete it.
- **Feature-branch model**: feature branches merge directly to main.

```bash
git branch -r | grep -E "origin/(main|dev|master)"   # identify model
```

- [ ] Branch is up to date with its target (main or dev — no conflicts)
  ```bash
  git fetch origin && git log HEAD..origin/<target> --oneline
  ```
- [ ] PR exists (or merge is direct — confirm with Captain)
  ```bash
  gh pr view
  ```
- [ ] PR description summarizes the change and links the issue
- [ ] After merge: delete the feature branch if it is a feature branch
  (never delete `main`, `dev`, or `master`)
  ```bash
  git branch -d <feature-branch>
  gh api repos/{owner}/{repo}/git/refs/heads/<feature-branch> -X DELETE
  ```
- [ ] Verify the issue was auto-closed by the merge
  ```bash
  gh issue view <N>
  ```
  If not auto-closed: `gh issue close <N> --comment "Fixed in vX.X.X.YY — <one-line summary>"`

---

## Blocking vs. Non-Blocking Findings

**Blockers (do not proceed until resolved):**
- Test suite has failures or errors
- GitHub Actions job failed
- No issue exists for the work
- `Closes #XX` missing from commit body when an issue should close
- Version not incremented

**Non-blockers (flag for Captain, proceed if acknowledged):**
- Design doc exists locally but not yet posted to issue thread
- Skipped test count increased (may be intentional)
- Branch not yet deleted (can do after verifying issue closed)

---

## Quick Reference

```bash
# Check issue
gh issue view <N>

# Run full test suite
hatch run pytest

# Check version
grep "^version" pyproject.toml

# Check GitHub Actions (after push)
gh run list --branch <branch> --limit 5
gh run view <run-id>
gh run view <run-id> --log-failed

# Verify issue closed after merge
gh issue view <N>

# Close issue manually if auto-close missed
gh issue close <N> --comment "Fixed in vX.X.X.YY"

# Delete remote branch after merge
gh api repos/{owner}/{repo}/git/refs/heads/<branch> -X DELETE
```

---

## Related Skills

- `/authorize` — Pre-work gate: declare scope and get sign-off before touching a file
- `/handoff` — When the session ends with work still in flight

Projects add their own audit skills. Where a project has them, they belong in
`docs/ai-context/` — a shared gate that names skills a particular project happens to have
sends every other reader after commands that do not exist.
