---
name: commit-ready
description: |
  Gate every commit against this project's definition of done: the issue and design trail,
  tests written first and passing, every suite CI runs passing locally, the version and
  changelog updated, and the commit message written to a file. Then hand over to the human,
  who commits and pushes; after the push, check every CI job.
  USE FOR: before committing; before opening a pull request; before closing an issue.
  DO NOT USE FOR: auditing code quality — use this project's audit skills for that.
---

# Commit-Ready Skill

## Core Principle: Every Gate Passes Before the Human Commits

Work through the checklist in order. Stop at any blocker and report it clearly.
Do not declare work done until every gate has been verified — not assumed.

**Who does what.** Rule `commit-authority`: the agent runs the gates, stages named paths, writes
the commit message to a file, and hands over the exact command. **The human commits, pushes,
opens the pull request and merges.** Passing every gate below is not authorization to do any of
those things.

Gates 1–5 happen before the commit. Gate 6 (CI) follows the human's push. Gate 7 (the pull
request) comes last.

**Every command in this skill comes from the project, not from this page.** This skill runs in
any repository, in any language. Where a gate needs a command — the test suite, the version, the
CI jobs — read it from the project's own `CLAUDE.md` and from its CI workflow. A command copied
from here into a project that does not use it is a gate that silently checks nothing.

---

## Gate 1: Issue & Documentation

- [ ] An issue exists for this work, if the project tracks work in issues
  ```sh
  gh issue view <N>
  ```
  If none exists, create one — body in `tmp/issue.md`, then
  `gh issue create --title "…" --body-file tmp/issue.md` — and report its URL
  (rule `agent-may-file-issues`).
- [ ] For non-trivial work: a design document exists where the project keeps them, or an audit
  finding where it keeps those
- [ ] The design (or a summary of its key decisions) is recorded in the issue thread, so the
  full trajectory is preserved where the work is tracked
- [ ] If the work required an audit first, the relevant audit skill was run and its findings
  addressed

**What counts as "non-trivial":** a new subsystem, a new extension point, a schema or
data-contract change, a new stage in an existing process. Bug fixes with a clear root cause
do not require a design doc. Each project records its own list in `docs/ai-context/`.

---

## Gate 2: Test-Driven Development

- [ ] Tests were written *before* or *alongside* the implementation (not after)
- [ ] There is a test that would have failed before this change and passes after
- [ ] Tests live where the project's test runner discovers them
- [ ] New tests have descriptive names (no `test_thing_1`, `test_thing_2`)
- [ ] Any testing constraint the project's `CLAUDE.md` names is respected

For bug fixes:
- [ ] A test reproducing the bug exists and is included in this commit

For features:
- [ ] Tests cover the new behavior, not just the happy path

---

## Gate 3: Every Suite CI Runs, Run Locally

**Run what CI runs.** Read the project's CI workflow — on GitHub, `.github/workflows/` — and
list every test, lint and type-check command its jobs run. Each one is a gate here. The
project's `CLAUDE.md` names the commands for its main suite; the workflow is what says whether
there are others.

A project can have more than one suite — a second language, a front end, a documentation
build. **A change can pass the suite you ran and still turn CI red on one you did not**, and the
local gate exists to be the check *before* the push.

**If the change touches a part of the project that only one suite covers**, that suite is
required for this commit. **If the change touches none of it**, it is not: a change to one part
does not need the toolchain of another installed to be committable. Where the project records
which paths each suite covers, follow that record.

- [ ] Every suite the change touches passes (0 failures, 0 errors)
- [ ] Skipped tests are pre-existing
- [ ] The test count is at or above the previous baseline (no tests silently deleted)

Keep the local commands identical to the workflow's. The local gate and CI describing the
definition of done in two different ways is how they drift apart.

Record the result — this line goes in the commit body:
```
Test coverage: XXXX passed, YY skipped (Z new tests added)
```

---

## Gate 4: Version & Changelog

Do this before committing so the version bump is in the same commit. A project with no
version, or no changelog, skips that half — and says so.

**Version** — read it from wherever the project declares it, and increment it the way the
project's own conventions say. Never propose a larger bump than the convention calls for.

- [ ] Version incremented
- [ ] Changelog entry added, in the project's existing format:

```markdown
## X.X.X.YY — YYYY-MM-DD

### New Features / Bug Fixes

- **Short title** — description. (Issue #XX)

### Test Coverage

- Added <test file> with N tests
- Full test suite: **XXXX tests passing** (N new tests added)
```

- [ ] Issues referenced in the changelog
- [ ] The handoff, if the project keeps one, describes the tree after this commit — not before
  it. `/stage-commits` checks this before staging

---

## Gate 5: Commit Message, Staging & Handover

Follow the commit-message convention in `docs/ai-context/sp/github-workflow.md`, or the
project's own where it has one.

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
- [ ] Version line present with the correct increment
- [ ] Message written to a file under `tmp/`, paths staged by name, and the command handed
  over — `/stage-commits` does all three
- [ ] **The human ran the commit and the push.** The agent did not.

Once the commit exists, run `git show HEAD` and read it before the human pushes.

---

## Gate 6: CI

Check after the human's push — CI cannot run before the commit exists on the remote.

```sh
gh run list --branch <branch-name> --limit 5
gh run view <run-id>
```

- [ ] All workflow jobs pass — not just the test job
- [ ] Build and release workflows pass, if they exist
  ```sh
  gh workflow list
  ```
- [ ] If any job failed: read the failure log, fix it, and hand the next commit over through
  Gates 3–5 again
  ```sh
  gh run view <run-id> --log-failed
  ```

**CRITICAL:** A passing local suite does NOT mean CI passed.
Check every job in every workflow that ran. Do not assume.

---

## Gate 7: Pull Request & Merge

First, identify the project's branching model from its AI context. The default is
`branching-workflow`: work on `dev`; `main` holds what has been released and reaches it by a
`dev` → `main` pull request.

- [ ] The branch is up to date with its target
  ```sh
  git fetch origin
  git log HEAD..origin/<target> --oneline
  ```
- [ ] The pull request's title and body are drafted in `tmp/pr.md` — summarizing the change and
  linking the issue — and the command handed over:
  `gh pr create --base <target> --title "…" --body-file tmp/pr.md`. **The human opens it**; the
  pull request is what runs CI, so opening it is the act that submits the work
- [ ] Once it exists, check it:
  ```sh
  gh pr view
  ```
- [ ] **The human merges.** The agent does not merge, and does not delete branches on the remote
- [ ] After the merge, the issue was auto-closed
  ```sh
  gh issue view <N>
  ```
  If it was not, say so and ask. Closing an issue is the human's call.

---

## Blocking vs. Non-Blocking Findings

**Blockers (do not proceed until resolved):**
- A suite the change touches has failures or errors
- A CI job failed
- No issue exists for the work, where the project tracks work in issues
- `Closes #XX` missing from the commit body when an issue should close
- Version not incremented, where the project versions

**Non-blockers (flag for the human, proceed if acknowledged):**
- Design doc exists locally but is not yet recorded in the issue thread
- Skipped test count increased (may be intentional)
- A merged feature branch not yet deleted

---

## Quick Reference

```sh
# Check the issue
gh issue view <N>

# Find every suite CI runs
ls .github/workflows/

# Check CI (after the human's push)
gh run list --branch <branch> --limit 5
gh run view <run-id>
gh run view <run-id> --log-failed

# Read what the commit holds, before the push
git show HEAD

# Verify the issue closed after the merge
gh issue view <N>
```

The test, lint and version commands are the project's — read them from its `CLAUDE.md`.

---

## Related Skills

- `/authorize` — Pre-work gate: declare scope and get sign-off before touching a file
- `/stage-commits` — Stage named paths, write the message to a file, hand over the command
- `/handoff` — When the session ends with work still in flight

Projects add their own audit skills. Where a project has them, they belong in
`docs/ai-context/` — a shared gate that names skills a particular project happens to have
sends every other reader after commands that do not exist.
