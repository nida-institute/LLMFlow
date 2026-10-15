---
name: release
description: |
  Release Scripture Pipelines itself, by project/RELEASE_CHECKLIST.md — the one procedure in force.
  USE FOR: cutting a release of this engine; checking a release run; preparing release notes.
  CRITICAL: NEVER claim a release succeeded without watching release.yml to completion, every job.
  DO NOT USE FOR: releasing any other project — this skill is about this repository only.
---

# Scripture Pipelines Release Skill

## The procedure is the checklist

**Follow `project/RELEASE_CHECKLIST.md`, top to bottom.** It is the procedure in force, and this
skill does not restate it: a second copy of the steps is the copy that goes stale. This one did —
until 2026-10-15 it described a retired workflow, the package's old PyPI name and a publish
command nobody runs any more.

The model in one paragraph, so the checklist reads in the right order: **build on the PR, promote
on the tag.** Opening the `dev` → `main` PR runs `build.yml`, which builds and tests the three
binaries. Merging it with a merge commit, then tagging that merge commit, runs `release.yml`,
which promotes those exact binaries to a GitHub Release, checks the install scripts, and publishes
the wheel to PyPI behind the `pypi` environment.

## Who does what

Rule `commit-authority`: the agent verifies, drafts and hands over commands; it does not take the
outward acts. **The human runs every one of these:**

| act | why it is the human's |
|---|---|
| `git push` of `dev`, and opening the release PR | a push is authenticated as the person who runs it |
| merging the PR (`gh pr merge --merge`) | a merge to `main` is a protected-branch act |
| `git tag` and `git push` of the tag | a tag push is a push, and it publishes |
| approving the `pypi` environment | publishing to PyPI is irreversible |
| `gh release edit` and `gh release delete` | they change what users download |

Where the checklist shows one of these as a command, the agent prints it for the human and waits.

## Before anything: which branch

A tag belongs on `main`'s merge commit, never on `dev`. Confirm where you are before reading a
version or a SHA:

```sh
git rev-parse --abbrev-ref HEAD
git fetch origin main
```

## Verifying — what "done" means

- **A green step is not a green release.** Watch `release.yml` with `gh run watch --exit-status`
  and read every job's conclusion (checklist §8). `verify-install` runs on three systems, and one
  failing is a failed release.
- **PyPI is checked at its source:** `https://pypi.org/project/scripture-pipelines/`.
- **Report what each job concluded,** with the run id. Never "the release succeeded" on less.

## This skill is not shipped

It releases Scripture Pipelines itself, so it lives in this repository's `.claude/skills/release/`
and `sp init` installs it nowhere. `tests/test_release_skill_stays_with_the_engine.py` holds that.
