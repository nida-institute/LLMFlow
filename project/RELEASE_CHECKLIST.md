# Release Checklist for LLMFlow

Follow this checklist when preparing a new release.

## The model (read this first)

As of 0.2.1.20 the release pipeline is **build-on-PR, promote-on-tag** — see
`project/plans/design-pr-build-promote.md` for the full design.

- **`build.yml`** runs on every **pull request**: tests + the Linux/macOS/Windows Nuitka
  builds, uploading the three binaries as artifacts (7-day retention). This is the merge
  gate — a red build blocks merge.
- **`release.yml`** runs on a **`v*` tag**: it does **NOT rebuild**. It finds the successful
  `build.yml` run for the tagged commit, downloads those exact binaries, attaches them to a
  GitHub Release, publishes, verifies the install scripts, and publishes the wheel to PyPI.

**Consequences that differ from the old flow:**
- The binaries are already built *before* you tag. Tagging promotes them.
- The tag **must point at the merge commit** whose `HEAD^2` is the PR head that was built.
- You must merge with a **merge commit** (not squash/rebase), or there is no `HEAD^2` to
  resolve and `release.yml` fails.
- Blessed artifacts expire after **7 days** — tag within that window or the build re-runs.

**CRITICAL:** Never claim "release succeeded" without watching `release.yml` to completion.
See Section 8.

---

## Pre-Release Validation

### 1. The PR build is green
- [ ] The release PR (dev → main) has a passing **`build.yml`** run on its head commit
- [ ] All three platforms succeeded — verify explicitly:
  ```bash
  gh run list --workflow build.yml --limit 1 --json headSha,conclusion
  gh run view <run-id> --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
  ```
- [ ] Tests job green (integration tests are deselected in CI via `-m "not integration"`)

**Note:** the build already happened here, on the PR — not at tag time. If this is red, fix
it before merging; do not tag hoping the release build will differ.

### 2. Blessed artifacts exist and are fresh
- [ ] The PR build uploaded `sp-linux`, `sp-macos`, `sp-windows.exe`:
  ```bash
  gh api repos/nida-institute/LLMFlow/actions/runs/<run-id>/artifacts \
    --jq '.artifacts[] | "\(.name)  \(.size_in_bytes) bytes  expires \(.expires_at[0:10])"'
  ```
- [ ] Expiry is in the future (7-day retention) — you must tag before then
- [ ] Binary sizes reasonable (~95–145 MB each)

### 3. Version & Changelog
- [ ] `CHANGELOG.md` has a section for this version (date, categorized changes, issue refs,
      breaking changes marked)
- [ ] Version bumped in `pyproject.toml` — **bump the 4th component** (e.g. 0.2.1.19 → 0.2.1.20)
      unless explicitly doing a minor/major
- [ ] The version-bump commit is part of the PR (so the tag lands on code with the right version)

### 4. Documentation sync
- [ ] Main docs reflect new features (`docs/*.md`, e.g. `docs/llmflow-language.md`)
- [ ] `INSTALL.md` / `README.md` examples still accurate
- [ ] Tutorial matches current CLI behavior
- [ ] (Propose updates to `docs/ai-context/` to the Captain if the workflow changed — do not
      edit those directly)

### 5. Code quality
- [ ] No stray debug prints / commented-out blocks that should go
- [ ] `sp lint` passes on example pipelines
- [ ] No consumer-specific coupling introduced into the core engine
      (see `project/audits/` cruft audit)

---

## Release Process

### 6. Merge the PR — **must be a merge commit**
- [ ] The PR is up to date with `main` (no divergence)
- [ ] Merge with a **merge commit** so `release.yml` can resolve `HEAD^2`:
  ```bash
  gh pr merge <pr-number> --merge --repo nida-institute/LLMFlow
  ```
  **Do NOT** use `--squash` or `--rebase` (they destroy the `HEAD^2` mapping).
  **Do NOT** use `--delete-branch` (the head branch is `dev`).
- [ ] Confirm the merge commit's second parent is the built PR head:
  ```bash
  git fetch origin main
  git rev-list --parents -n1 origin/main   # third SHA = HEAD^2 = the built commit
  ```

### 7. Tagging **[CRITICAL — TAG THE MERGE COMMIT, DELETE STALE TAGS FIRST]**

> ⚠️ Incident (2026-07-11): a pre-existing local `v0.2.1.20` tag caused `git tag` to fail
> silently; the stale tag (pointing at the old version-bump commit) got pushed instead,
> firing the retired workflow on stale code. **Always delete any existing tag first, and
> verify the tag dereferences to the merge commit before pushing.**

```bash
VERSION=$(grep '^version' pyproject.toml | head -1 | cut -d'"' -f2)
MERGE=$(git rev-parse origin/main)          # the merge commit

# Delete any existing tag (local + remote) — prevents the silent-stale-tag trap
git tag -d "v$VERSION" 2>/dev/null || true
git push origin ":refs/tags/v$VERSION" 2>/dev/null || true

# Create the annotated tag ON THE MERGE COMMIT
git tag -a "v$VERSION" "$MERGE" -m "Release $VERSION"

# VERIFY it points at the merge commit (annotated tags: use ^{commit})
git rev-parse "v$VERSION^{commit}"          # must equal $MERGE
git rev-list --parents -n1 "v$VERSION^{commit}"   # third SHA = built PR head

git push origin "v$VERSION"
```

**CHECKLIST:**
- [ ] Deleted any existing `v$VERSION` tag locally and remotely
- [ ] Created annotated tag on the **merge commit** (not the version-bump commit)
- [ ] `v$VERSION^{commit}` equals the merge commit SHA
- [ ] `HEAD^2` of that commit is the PR head that `build.yml` built
- [ ] Pushed the tag

### 8. Watch `release.yml` **[MANDATORY VERIFICATION]**

```bash
sleep 15
RUN=$(gh run list --workflow release.yml --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$RUN" --exit-status
gh run view "$RUN" --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
```

**CHECKLIST (do not claim success unless ALL pass):**
- [ ] The **Release** workflow (not the old "Build and Release Executables") triggered, on
      the merge-commit SHA
- [ ] `resolve-build` found the build run (if it fails here: the tag isn't on the merge
      commit, or artifacts expired — it fails loud, nothing is published)
- [ ] `create-release` → `promote` attached all three binaries (no rebuild)
- [ ] `publish-release` flipped the draft to published
- [ ] `verify-install` passed on all three OSes
- [ ] `publish-pypi` succeeded — confirm at https://pypi.org/project/scripture-pipelines/
- [ ] Release assets present: `sp-linux`, `sp-macos`, `sp-windows.exe`
  ```bash
  gh release view "v$VERSION" --json isDraft,assets --jq '{isDraft, assets:[.assets[].name]}'
  ```

**IF `release.yml` FAILS:** it never publishes a partial/bad release. Diagnose, then:
```bash
gh run view "$RUN" --log-failed
gh release delete "v$VERSION" --yes 2>/dev/null || true   # if a draft was created
git tag -d "v$VERSION"; git push origin ":refs/tags/v$VERSION"
# fix, re-merge if needed, re-tag from Section 7
```

### 9. Release notes
- [ ] Review the auto-generated notes on the published release
- [ ] Add a highlights section; call out breaking changes; link `CHANGELOG.md`
- [ ] Verify the binary download links work

---

## Post-Release Validation

### 10. Installation testing
- [ ] `install.sh` (Linux/macOS) and `install.ps1` (Windows) install a runnable `sp`
      (largely covered by the `verify-install` job, but spot-check once)
- [ ] `pip install scripture-pipelines` gets the new version
- [ ] `sp init` on a fresh directory works; an example pipeline runs

### 11. Documentation & announcement
- [ ] Update any external docs pointing at release downloads
- [ ] Announce (if there's a communication plan)

### 12. Prepare `dev` for the next cycle
- [ ] `git checkout dev && git pull`
- [ ] Bump `pyproject.toml` to the next 4th-component version
- [ ] Start a fresh `CHANGELOG.md` section for the next release
- [ ] Commit and push to `dev`

---

## Rollback

If a critical issue is found post-release:
1. Mark the GitHub release as pre-release (or delete it)
2. Yank the PyPI release if the wheel is broken (`pip` users are affected):
   see https://pypi.org/help/#yanked
3. Delete the tag: `git tag -d vX; git push origin :refs/tags/vX`
4. Fix on `dev`, open a PR (rebuilds on the PR), then re-release from Section 6

---

## Common failure modes (learned the hard way)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `release.yml` didn't run; old "Build and Release Executables" did | Tag points at a pre-CI-split commit | Tag the **merge commit**; delete the stale tag first |
| `git tag` "already exists", stale tag pushed | Didn't delete the existing tag first | Always `git tag -d` + delete remote before re-tagging (Section 7) |
| `resolve-build` fails, no release | Squash/rebase merge (no `HEAD^2`), or tag not on merge commit, or artifacts expired | Merge-commit only; tag the merge commit; tag within 7 days |
| PyPI publishes but binaries missing | (shouldn't happen — `publish-pypi` needs `promote`) | Check the job graph in `release.yml` |
| `publish-pypi` fails: "Trusted publishing exchange failure: invalid-publisher" | PyPI trusted publishing matches on the **workflow filename**; renaming/splitting the release workflow breaks the OIDC claim | On PyPI (project → Manage → Publishing) set the trusted publisher's workflow to the current filename (`release.yml`) + environment `pypi`, then re-run `Publish to PyPI` (re-approve the `pypi` gate). **If you ever rename the release workflow, update the PyPI publisher first.** |
| `verify-install` 403s on one OS while the others pass | Transient GitHub release-asset 403 on that runner — not a code bug | Re-run the failed job (`gh run rerun <run> --failed`); it clears |

## Version numbering
- Always increment the **4th component** (`0.2.1.19` → `0.2.1.20`). Never propose minor/major
  unless explicitly asked.

## Quick reference (happy path)
```bash
# 1. Confirm the PR build is green (Section 1) and artifacts are fresh (Section 2)
# 2. Merge as a merge commit
gh pr merge <pr-number> --merge --repo nida-institute/LLMFlow
# 3. Tag the merge commit (delete any stale tag first)
git fetch origin main
VERSION=$(grep '^version' pyproject.toml | head -1 | cut -d'"' -f2)
git tag -d "v$VERSION" 2>/dev/null; git push origin ":refs/tags/v$VERSION" 2>/dev/null
git tag -a "v$VERSION" "$(git rev-parse origin/main)" -m "Release $VERSION"
git rev-parse "v$VERSION^{commit}"    # sanity: == origin/main
git push origin "v$VERSION"
# 4. Watch the release (Section 8)
gh run watch "$(gh run list --workflow release.yml --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
```
