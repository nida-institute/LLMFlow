---
name: release
description: |
  **WORKFLOW SKILL** — Execute LLMFlow release process with mandatory build verification.
  USE FOR: cutting new releases; tagging versions; verifying Nuitka builds actually succeeded on all platforms.
  CRITICAL: NEVER claim "build succeeded" without running verification commands. Check GitHub Actions logs directly.
  DO NOT USE FOR: hotfixes without full verification; skipping build checks; assuming success.
  INVOKES: gh CLI for workflow verification, git for tagging, file editing for version bumps.
  REFERENCES: project/RELEASE_CHECKLIST.md for full checklist.
applyTo:
  - "pyproject.toml"
  - "CHANGELOG.md"
  - ".github/workflows/build-release.yml"
---

# LLMFlow Release Skill

## Purpose

Execute LLMFlow releases with **mandatory verification** that Nuitka builds actually succeeded on all three platforms (Linux, macOS, Windows).

**CRITICAL LESSON LEARNED:** Multiple releases failed for a week because builds were never verified. AI claimed success without checking. This skill prevents that.

---

## Pre-Release Validation

### 1. Tests
```bash
pytest -v
```
- [ ] All tests pass (0 failures)
- [ ] Test count hasn't decreased unexpectedly
- [ ] Review any newly skipped tests

### 2. **CRITICAL: Build Status Verification**

**MANDATORY COMMANDS - RUN THESE BEFORE CLAIMING SUCCESS:**

```bash
# Check last 5 build-release workflow runs
gh run list --workflow=build-release.yml --limit 5

# For the most recent run, get detailed status
gh run view <RUN_ID> --json conclusion,status,jobs

# Check individual job conclusions
gh run view <RUN_ID> --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'

# If any failed, get the error logs
gh run view <RUN_ID> --log-failed
```

**VERIFICATION CHECKLIST:**
- [ ] All 3 platform builds show ✓ (not X)
- [ ] Run status is "completed" with conclusion "success" (not "failure")
- [ ] Artifacts exist: sp-linux, sp-macos, sp-windows.exe
- [ ] Binary sizes reasonable (~50-70MB range)

**🚨 NEVER say "build succeeded" without running these commands and seeing ✓ for all platforms.**

### 3. Version & Changelog
- [ ] `CHANGELOG.md` updated with release section
  - Version number and date
  - Categorized changes (features, fixes, docs)
  - Issue numbers linked where applicable
- [ ] Version incremented in `pyproject.toml`
  - **Convention:** Always bump 4th component (0.2.1.14 → 0.2.1.15)
  - Unless explicitly asked to bump minor/major

### 4. Documentation Sync
- [ ] AI context files current (docs/ai-context/)
- [ ] README examples still work
- [ ] INSTALL.md accurate

---

## Release Process

### 5. Tag Creation and Push

```bash
# Get current version from pyproject.toml
VERSION=$(grep 'version = ' pyproject.toml | cut -d'"' -f2)
echo "Releasing v$VERSION"

# Check if tag already exists (CRITICAL - prevents orphaned tags)
git tag --list "v$VERSION"
git ls-remote --tags origin "v$VERSION"

# If tag exists from failed build, DELETE IT FIRST:
git tag -d "v$VERSION"
git push origin --delete "v$VERSION"

# Create new annotated tag on current commit
git tag -a "v$VERSION" -m "Release $VERSION"

# Push tag to trigger build
git push origin "v$VERSION"
```

### 6. **CRITICAL: Wait and Verify Build**

```bash
# Wait 30 seconds for workflow to start
sleep 30

# Check if workflow was triggered
gh run list --workflow=build-release.yml --limit 1

# Get the run ID
RUN_ID=$(gh run list --workflow=build-release.yml --limit 1 --json databaseId --jq '.[0].databaseId')
echo "Monitoring run: $RUN_ID"
echo "URL: https://github.com/nida-institute/LLMFlow/actions/runs/$RUN_ID"

# Monitor until complete (builds take ~3-5 minutes)
gh run watch $RUN_ID

# VERIFY ALL PLATFORMS SUCCEEDED
gh run view $RUN_ID --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
```

**EXPECTED OUTPUT (all must show "success"):**
```
Create Draft Release: success
Build on Linux: success
Build on macOS: success
Build on Windows: success
```

**IF ANY SHOW "failure":**
```bash
# Get the error logs
gh run view $RUN_ID --log-failed

# Delete the failed release artifacts
gh release delete "v$VERSION" --yes

# Delete the tag
git tag -d "v$VERSION"
git push origin --delete "v$VERSION"

# Fix the issue, then start over
```

### 7. Release Notes

Once builds verified successful:

```bash
# Open the draft release
gh release view "v$VERSION" --web

# Or edit from CLI
gh release edit "v$VERSION" --draft=false --notes "$(cat tmp/release-notes-$VERSION.md)"
```

- [ ] Review auto-generated notes
- [ ] Add highlights for major features
- [ ] Note breaking changes prominently
- [ ] Publish release (remove draft status)

---

## Post-Release Validation

### 8. Download and Test Binaries

```bash
# Download all three platform binaries
gh release download "v$VERSION" --pattern "sp-*"

# Test each one
chmod +x sp-linux sp-macos
./sp-linux --version
./sp-macos --version
# Windows requires actual Windows machine or VM
```

- [ ] All binaries execute without error
- [ ] Version numbers match release
- [ ] Basic commands work (`sp init`, `sp --help`)

---

## Rollback Procedure

If critical issue discovered post-release:

```bash
# Delete the release
gh release delete "v$VERSION" --yes

# Delete the tag
git tag -d "v$VERSION"
git push origin --delete "v$VERSION"

# Fix issue, increment version again, restart process
```

---

## Version Numbering Convention

**Always increment the 4th component** (per user-prefs.md):
- `0.2.1.14` → `0.2.1.15` → `0.2.1.16`
- Never propose minor/major bump unless explicitly asked

---

## Common Failure Modes and Prevention

### 1. **Unicode in Build Scripts (Windows)**
- **Symptom:** Windows builds fail with `UnicodeEncodeError`
- **Cause:** Windows CMD uses cp1252 encoding, can't handle emoji/Unicode
- **Prevention:** Use ASCII-only characters in all build scripts
- **Fix:** Replace emoji with [TAGS] like [BUILD], [OK], [ERROR]

### 2. **Tag Already Exists**
- **Symptom:** `git tag` creates local tag but doesn't trigger workflow
- **Cause:** Tag already exists on remote from previous failed attempt
- **Prevention:** Always check `git ls-remote --tags origin "v$VERSION"` first
- **Fix:** Delete old tag locally and remotely before creating new one

### 3. **Build Succeeds Locally but Fails in CI**
- **Symptom:** Local builds work, GitHub Actions fail
- **Cause:** Environment differences (Node versions, npm cache, etc.)
- **Prevention:** Test with `act` (GitHub Actions local runner) before tagging
- **Fix:** Check workflow logs, update CI configuration

### 4. **Claiming Success Without Verification**
- **Symptom:** AI says "build succeeded" but user gets failure emails
- **Cause:** AI didn't actually check `gh run list` output
- **Prevention:** Make verification commands MANDATORY in this skill
- **Fix:** Always require proof (workflow URL + status output) before claiming success

---

## Quick Reference Commands

```bash
# Check last 5 builds
gh run list --workflow=build-release.yml --limit 5

# Verify specific run succeeded
gh run view <RUN_ID> --json conclusion --jq '.conclusion'

# Delete failed tag
git tag -d v0.2.1.15 && git push origin --delete v0.2.1.15

# Create and verify new tag
git tag -a v0.2.1.15 -m "Release 0.2.1.15" && \
git push origin v0.2.1.15 && \
sleep 30 && \
gh run list --workflow=build-release.yml --limit 1
```

---

## Mandatory Outputs When Using This Skill

When executing a release, the AI **MUST** provide:

1. **GitHub Actions workflow URL** - Direct link to the build run
2. **Status output** - Copy of `gh run view` showing all jobs succeeded
3. **Binary verification** - Proof that artifacts exist (file sizes, checksums)
4. **User-actionable next steps** - Clear instructions for what to do next

**NEVER say:**
- ❌ "Build succeeded" without proof
- ❌ "All platforms passed" without showing command output
- ❌ "Release is ready" without verifying binaries exist

**ALWAYS say:**
- ✅ "Build workflow triggered: [URL]"
- ✅ "Verification pending - monitoring run [ID]"
- ✅ "All platforms verified successful: [status output]"
- ✅ "Binaries available: [artifact list with sizes]"
