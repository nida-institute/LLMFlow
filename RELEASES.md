# Release Process

## Overview

Releases are triggered by pushing a version tag (`v*`). The CI workflow:
1. Creates a **draft** GitHub Release
2. Builds binaries on Linux, macOS, and Windows in parallel using Nuitka
3. Smoke-tests each binary on its native platform
4. Uploads each binary **directly** to the draft release (no artifact storage used)
5. Publishes the release once all three platforms succeed

If any build or smoke test fails, the release stays draft and is never published.

## Steps to Make a Release

### 1. Work on `dev`

All development happens on `dev`. When ready to release, make sure `dev` is clean and tests pass:

```bash
hatch run pytest
```

### 2. Bump the version

Update `pyproject.toml` and `CHANGELOG.md`, then commit on `dev`:

```bash
# Edit pyproject.toml: version = "0.1.X.YY"
# Edit CHANGELOG.md: move Unreleased items to a new version section
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.1.X.YY"
git push
```

### 3. Merge dev → main

```bash
git checkout main
git merge dev
git push
git checkout dev
```

### 4. Tag and push

```bash
git tag v0.1.X.YY
git push origin v0.1.X.YY
```

This triggers the build workflow automatically.

### 5. Monitor the build

```bash
gh run list --workflow=build-release.yml --limit=1
```

Or watch it in the GitHub Actions UI.

### 6. Test the binaries (optional, before publish)

While the release is still draft you can download and test locally:

```bash
gh release download v0.1.X.YY --pattern "llmflow-macos*" --dir /tmp
/tmp/llmflow-macos --version
```

### 7. Release publishes automatically

Once all three platform builds and smoke tests pass, the `publish-release` job marks the draft public. No manual step needed.

## If a Build Fails

The draft release stays unpublished. Options:

**Re-run failed jobs** from the GitHub Actions UI (fastest).

**Or delete the draft and retag** after fixing the issue:

```bash
gh release delete v0.1.X.YY --yes
# fix the issue, commit, push
git tag -f v0.1.X.YY
git push --force origin v0.1.X.YY
```

## Artifact Storage

No GitHub Actions artifact storage is used. Binaries go straight from the build runner to the GitHub Release. Release assets are permanent and do not count against artifact storage quota.

## Verifying artifact storage is clean

```bash
gh api repos/nida-institute/LLMFlow/actions/artifacts --paginate \
  | jq '.artifacts | length, [.[].name]'
```

Should always return `0` and `[]`.
