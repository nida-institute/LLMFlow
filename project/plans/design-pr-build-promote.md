# Design: Build-on-PR, Bless-on-Merge, Promote-on-Tag

**Status:** Proposed — awaiting Captain review
**Author:** AI (at Captain's direction)
**Date:** 2026-07-07
**Related:** PR #173 (Release 0.2.1.20), `.github/workflows/build-release.yml`, `.github/workflows/test.yml`

## Problem

The 3-platform Nuitka build (`build-release.yml`) only fires on a `v*` **tag** — i.e.
*after* merge to `main`. Consequences:

1. **Broken builds are discovered too late.** v0.2.1.19's build failed at tag time,
   with the code already merged. ("Why merge code that fails to build?")
2. **The expensive build runs at the worst moment** — post-merge, when it's hardest to
   back out.
3. **No pre-merge signal.** PRs only run `test.yml` (Linux-only pytest), never a build.

## Goal

- Build the Linux/macOS/Windows binaries **on the PR**, and make that build a
  **required check** so a failing build blocks merge.
- **Reuse those exact binaries** as the release assets on tag — build once, not twice.
- Keep the release step **deliberate** (explicit `v*` tag push).

## Decisions (confirmed with Captain, 2026-07-07)

| Decision | Choice |
|----------|--------|
| Blessing mechanism | **PR approval + merge.** Green required build + merge = blessed. No Environment gate. |
| Publish trigger | **Push a `v*` tag.** Merge to main does not auto-release. |
| Ship *.20 | **Dogfood the new flow** on PR #173. |

## Non-goals

- Auto-releasing on merge to `main`.
- Byte-reproducible builds (see Risk R1 — we *reuse* the artifact precisely because
  Nuitka output is not reproducible).
- Changing what the binaries contain or how Nuitka is invoked.

## Architecture

Split the monolithic `build-release.yml` into two workflows.

### `build.yml` — the merge gate (build once)

```
on:
  pull_request:            # the gate
  workflow_dispatch:       # manual smoke build on any branch
  # (optionally) push: branches: [dev]  -- see Open Question Q1
```

Jobs (largely lifted from today's `test` + `build` jobs):

- **test** — frontend tests, tsc, GUI build, Pyright, backend pytest (with empty API-key
  env, as today).
- **build** (matrix: ubuntu / macos / windows) — install deps, build GUI, Nuitka build,
  **smoke-test the binary** (`--version`, `lint`, `run --dry-run`), then
  **`actions/upload-artifact`** each binary (**retention 7 days** — see Q2). No release
  upload here.

**Required-check wiring:** add `build.yml`'s jobs to branch protection on `main` as
required status checks (Captain / repo-admin action — see Rollout step 5).

### `release.yml` — promote the blessed artifacts (no rebuild)

```
on:
  push:
    tags: ['v*']
```

Jobs:

1. **resolve-build** — determine the commit whose artifacts to promote, find the
   successful `build.yml` run for it, expose its `run_id`. (See "Artifact correlation".)
2. **create-release** — `gh release create --draft --generate-notes`.
3. **promote** — `gh run download <run_id>` to fetch the three binaries, then
   `gh release upload` them to the draft. **No Nuitka build.**
4. **publish-release** — flip draft → published.
5. **verify-install** (matrix 3 OS) — unchanged from today.
6. **publish-pypi** — unchanged from today (`hatch build` + PyPI publish; this one *does*
   rebuild the wheel, which is cheap and correct).

## Artifact correlation (the crux)

To promote the PR-built binary at tag time we must map the tag back to the build run.

**The `pull_request` gotcha:** for `pull_request` events, `github.sha` is an ephemeral
merge-preview commit. But the **workflow run's `head_sha` is the PR head commit**, so
`gh run list -w build.yml -c <pr-head-sha> -s success` locates the run.

**Making the mapping deterministic — two constraints:**

1. **Require PR branches be up-to-date with `main` before merge** (branch protection).
   Then the merge-preview tree the build ran against == the tree that lands on `main`.
2. **Use merge commits** (not squash/rebase) when merging to `main`. Then on the tagged
   commit, `git rev-parse HEAD^2` == the PR head SHA that was built.

**resolve-build logic:**
```
candidates = [HEAD^2 (if merge commit), HEAD]      # cover merge-commit and FF cases
for sha in candidates:
    run_id = gh run list -w build.yml -c <sha> -s success --limit 1 --json databaseId
    if run_id: break
fail loudly if none found (do NOT silently rebuild — surface it)
```

**To also reflect the exact PR head in the binary** (belt-and-suspenders): in `build.yml`,
for `pull_request` events check out `${{ github.event.pull_request.head.sha }}` rather
than the merge ref, so the artifact is built from the head commit that will become
`HEAD^2`.

## Risks

- **R1 — Nuitka not byte-reproducible.** Mitigated by *reusing* the artifact rather than
  rebuilding. This is strictly safer than today's rebuild-at-tag.
- **R2 — Artifact retention window.** Set to **7 days** (Captain: a PR not merged within a
  week is stale). A tag pushed after that finds artifacts expired; `resolve-build` fails
  loudly (never silently rebuilds), so this is visible, not silent — and correctly forces
  a fresh build for a stale branch.
- **R3 — `gh run list -c` matching PR runs by head_sha.** High confidence, but validate
  during implementation (Rollout step 3).
- **R4 — Fork PRs** can't write artifacts with the needed token scope. Not a concern:
  this is a single-maintainer repo; PRs come from branches, not forks.

## Prerequisite (separate scope): fix the 2 failing tests

`test.yml` is currently red on `dev` — this blocks *.20 regardless of CI redesign:

1. `test_cost_fallback_gpt5.py::test_gpt5_cost_estimation_when_usage_missing` — makes a
   real `gpt-5` call, dies on missing `OPENAI_API_KEY`. Needs mock or key-gated skip.
2. `test_prompt_path_resolution.py::test_cli_run_reports_prompt_error_not_pipeline_error`
   — `SystemExit: 1` on missing prompt; expectation mismatch.

Each gets its own TDD fix under the authorization workflow. **Not** part of this CI design.

## Rollout (dogfooding *.20 on PR #173)

1. Fix the 2 failing tests on `dev` (separate authorization).
2. Add `build.yml` + `release.yml`; retire `build-release.yml`. Because `pull_request`
   runs use the workflow from the PR branch, PR #173 immediately gets a real 3-platform
   build.
3. Validate on the PR: build matrix green, artifacts uploaded; confirm R3 (`gh run list -c`
   finds the run by PR head sha).
4. Confirm both required checks (test + build) are green on PR #173.
5. **Captain / repo-admin:** set branch protection on `main` — require `test` and `build`
   checks, require branches up-to-date. Confirm merge method = merge commit.
6. Merge PR #173 to `main` (the blessing).
7. Tag `v0.2.1.20` → `release.yml` resolves the build run, downloads + promotes the
   blessed binaries, publishes, verifies install, publishes to PyPI.
8. Update `RELEASE_CHECKLIST.md` to reflect promote-not-rebuild.

## Resolved decisions (Captain, 2026-07-07)

- **Q1 — PR-only.** Build on `pull_request` + `workflow_dispatch`. No push-to-`dev`
  trigger.
- **Q2 — Retention 7 days.** A PR not merged within ~a week is stale; a stale branch
  *should* be forced to rebuild rather than promote old binaries.
- **Q3 — Keep `verify-install` sequential** after `publish-release`, as today.
- **Branch protection — deferred.** The Captain will configure the required checks +
  up-to-date + merge-commit settings later; not a blocker for landing the workflows.
  See caveat below.

### Caveat: workflows land before branch protection

Until the Captain enables branch protection, the `build` check runs on PRs but does **not
mechanically block** merge, and the "up-to-date + merge commit" constraints aren't
enforced. For the *.20 dogfood this is fine — we follow them **manually**: confirm the PR
build is green before merging, ensure #173 is up-to-date with `main`, and merge with a
merge commit. The promotion machinery works regardless; branch protection just makes the
discipline automatic later.
