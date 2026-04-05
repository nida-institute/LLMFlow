# Release Checklist for LLMFlow

Follow this checklist when preparing a new release.

**For AI assistance:** Invoke the `/release` skill which provides guided automation and mandatory verification.

**CRITICAL:** Never claim "build succeeded" without running verification commands. See Section 8 for mandatory checks.

---

## Pre-Release Validation

### 1. Tests
- [ ] `pytest -v` passes with 0 failures
- [ ] Check test count hasn't decreased unexpectedly
- [ ] Review any newly skipped tests (should be rare)
- [ ] Integration tests pass (or are properly skipped if API keys absent)

### 2. Build Status
- [ ] GitHub Actions test workflow passing on dev branch
- [ ] No known build failures on any platform (Linux, macOS, Windows)
- [ ] Recent Nuitka build completed successfully (check last workflow_dispatch or tag build)
- [ ] Binary sizes reasonable (~50-70MB range)

### 3. Version & Changelog
- [ ] `CHANGELOG.md` updated with all changes from this release
  - Clear section with version number and date
  - Categorized changes (features, fixes, docs, etc.)
  - Issue numbers linked where applicable
  - Breaking changes clearly marked (if any)
- [ ] Version number incremented in `pyproject.toml`
  - **Convention:** Always bump 4th component (e.g., 0.2.1.04 → 0.2.1.05)
  - Unless explicitly bumping minor/major

### 4. Documentation Sync
- [ ] AI context files up to date (docs/ai-context/)
- [ ] Main documentation reflects new features (docs/*.md)
- [ ] INSTALL.md still accurate for current release
- [ ] README.md examples still work
- [ ] Tutorial still matches current CLI behavior

### 5. Code Quality
- [ ] No TODO/FIXME comments that should be addressed before release
- [ ] No debug print statements left in production code
- [ ] No commented-out code blocks that should be removed
- [ ] Linter passes (`llmflow lint` on example pipelines)

---

## Release Process

### 6. Branch Management
- [ ] All changes committed on dev branch
- [ ] `git push origin dev` completed
- [ ] Switch to main: `git checkout main`
- [ ] Merge dev: `git merge dev --no-edit`
- [ ] Resolve any merge conflicts
- [ ] `git push origin main`

### 7. Tagging **[CRITICAL - CHECK FOR EXISTING TAGS]**

```bash
# Get version from pyproject.toml
VERSION=$(grep 'version = ' pyproject.toml | cut -d'"' -f2)

# CHECK if tag already exists (prevents orphaned tags from failed releases)
git tag --list "v$VERSION"
git ls-remote --tags origin "v$VERSION"

# If tag exists, DELETE IT FIRST:
git tag -d "v$VERSION"
git push origin --delete "v$VERSION"

# Create new annotated tag
git tag -a "v$VERSION" -m "Release $VERSION"

# Push tag to trigger build
git push origin "v$VERSION"
```

**CHECKLIST:**
- [ ] Checked for existing tag with same version number
- [ ] Deleted old tag if it existed (locally and remotely)
- [ ] Created annotated tag: `git tag -a v$VERSION -m "Release $VERSION"`
  - Use exact version from pyproject.toml
  - Format: `v` + version number (e.g., v0.2.1.15)
- [ ] Pushed tag: `git push origin v$VERSION`
- [ ] Verified tag appears on GitHub: https://github.com/nida-institute/LLMFlow/tags

### 8. CI Build **[CRITICAL - MANDATORY VERIFICATION]**

**🚨 DO NOT SKIP THESE VERIFICATION COMMANDS 🚨**

```bash
# Wait for workflow to start (30 seconds after tag push)
sleep 30

# Check if workflow was triggered
gh run list --workflow=build-release.yml --limit 1

# Get the run ID and URL
RUN_ID=$(gh run list --workflow=build-release.yml --limit 1 --json databaseId --jq '.[0].databaseId')
echo "Build URL: https://github.com/nida-institute/LLMFlow/actions/runs/$RUN_ID"

# Monitor until complete (takes ~3-5 minutes)
gh run watch $RUN_ID

# VERIFY ALL PLATFORMS SUCCEEDED (all must show "success")
gh run view $RUN_ID --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
```

**CHECKLIST (do not proceed unless ALL are checked):**
- [ ] GitHub Actions "Build and Release Executables" workflow triggered automatically
- [ ] Verified run URL in browser shows ALL green checkmarks
- [ ] Command output shows "success" for: Create Draft Release, Build on Linux, Build on macOS, Build on Windows
- [ ] Draft release created automatically
- [ ] Binaries attached to release (visible in GitHub UI):
  - `sp-linux`
  - `sp-macos`
  - `sp-windows.exe`
- [ ] Binary sizes reasonable (~50-70MB each)

**IF ANY BUILD FAILED:**
```bash
# Get error logs
gh run view $RUN_ID --log-failed

# Delete failed release and tag
gh release delete "v$VERSION" --yes
git tag -d "v$VERSION"
git push origin --delete "v$VERSION"

# Fix the issue, then start checklist over from step 1
```

### 9. Release Notes
- [ ] Open draft release on GitHub
- [ ] Review auto-generated notes
- [ ] Edit release notes for clarity
  - Add highlights section for major features
  - Note any breaking changes prominently
  - Link to CHANGELOG for full details
  - Add migration notes if needed
- [ ] Verify binary download links work
- [ ] Publish release (convert from draft)

---

## Post-Release Validation

### 10. Installation Testing
- [ ] Download Linux binary, verify `chmod +x`, test `./sp-linux --version`
- [ ] Download macOS binary, verify Gatekeeper instructions in INSTALL.md work
- [ ] Download Windows binary, verify SmartScreen instructions work
- [ ] Test `sp init` workflow on fresh directory
- [ ] Test example pipeline runs

### 11. Documentation Updates
- [ ] Update any external documentation pointing to release downloads
- [ ] Update version references in docs (if they specify versions)
- [ ] Announce release (if there's a communication plan)

### 12. Branch Cleanup
- [ ] Switch back to dev: `git checkout dev`
- [ ] Reset CHANGELOG "Unreleased" section:
  ```markdown
  ## Unreleased
  - _No changes yet._
  ```
- [ ] Commit and push to dev

---

## Rollback Procedure

If a critical issue is discovered post-release:

1. Mark release as "pre-release" on GitHub (or delete it)
2. Remove binaries from release assets
3. Delete the tag locally: `git tag -d v0.2.1.05`
4. Delete the tag remotely: `git push origin :refs/tags/v0.2.1.05`
5. Fix the issue on dev branch
6. Follow checklist again for new release

---

## Version Numbering Convention

**Always increment the 4th component** (per user-prefs.md):
- `0.2.1.02` → `0.2.1.03` → `0.2.1.04` → `0.2.1.05`
- Never propose minor/major bump unless explicitly asked

## Quick Reference: Common Commands

```bash
# Run tests
pytest -v

# Check version in pyproject.toml
grep 'version =' pyproject.toml

# Create and push tag
git tag -a v0.2.1.05 -m "Release 0.2.1.05"
git push origin v0.2.1.05

# Quick release (assumes all checks passed)
git checkout main && \
git merge dev --no-edit && \
git push origin main && \
git tag -a v0.2.1.05 -m "Release 0.2.1.05" && \
git push origin v0.2.1.05 && \
git checkout dev
```
