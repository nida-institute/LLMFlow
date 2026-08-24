---
name: release
description: |
  **WORKFLOW SKILL** — Execute Scripture Pipelines release process with mandatory build verification.
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

# Scripture Pipelines Release Skill

## Purpose

Execute Scripture Pipelines releases with **mandatory verification** that Nuitka builds actually succeeded on all three platforms (Linux, macOS, Windows).

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

**🚨 IMMEDIATELY after tag push: Show the user the build URL 🚨**

```bash
# Wait 30 seconds for workflow to start
sleep 30

# Get the run ID and URL
RUN_ID=$(gh run list --workflow=build-release.yml --limit 1 --json databaseId --jq '.[0].databaseId')

# DISPLAY THIS URL TO USER IMMEDIATELY (do not wait for build completion)
echo "Build URL: https://github.com/nida-institute/LLMFlow/actions/runs/$RUN_ID"
```

**At this point, tell the user:**
```
Tag v$VERSION pushed. Build triggered:
https://github.com/nida-institute/LLMFlow/actions/runs/$RUN_ID

Monitoring build progress (takes ~3-5 minutes)...
```

**Then continue monitoring:**

```bash
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

### 8. PyPI Publication (Optional)

**🚨 CRITICAL: Verify PyPI registration status BEFORE claiming "ready to publish" 🚨**

```bash
# Check if project exists on PyPI
curl -s https://pypi.org/pypi/llmflow/json | jq -r '.info.version' 2>/dev/null || echo "NOT REGISTERED"
```

**If output is "NOT REGISTERED":**
- This is a FIRST-TIME publication
- Requires PyPI account with 2FA enabled
- Requires API token with CREATE project permissions
- Package name must be available (not claimed by another project)
- See `/memories/repo/pypi-status.md` for full first-time setup

**If output shows a version number:**
- Project already exists on PyPI
- This will be an UPDATE to existing project
- Requires API token with upload permissions for llmflow specifically

**Build packages:**
```bash
# Clean previous builds
rm -rf dist/

# Build wheel and tarball
hatch build
```

**Verify package contents:**
```bash
# Check what's in the wheel
unzip -l dist/llmflow-$VERSION-py3-none-any.whl

# Verify critical includes:
# - llmflow/ package
# - prompts/ data
# - templates/ data
# - gui/static/ frontend assets
```

**Publish (ONLY if verified registered or have first-time credentials):**
```bash
hatch publish
```

**NEVER claim "ready to publish to PyPI" based solely on successful `hatch build`.**
- Building creates local packages (works anywhere)
- Publishing uploads to PyPI (requires registration + credentials)
- These are separate steps with separate requirements

---

## Post-Release Validation

### 9. Download and Test Binaries

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

### 4. **Critical Distinction: Two Separate Build Systems**

**THE PROBLEM:** AI confuses PR test status with Nuitka build status and claims "build succeeded" when only tests passed.

**Two completely separate workflows:**

| Workflow | Triggers On | What It Does | How to Verify |
|----------|------------|--------------|---------------|
| **Tests** (`tests.yml`) | Push to any branch | Runs pytest, checks code quality | `gh pr view <PR#> --json statusCheckRollup` |
| **Nuitka Builds** (`build-release.yml`) | Push to version tag | Builds executables for Mac/Linux/Windows | `gh run list --workflow=build-release.yml` |

**What tests passing means:**
- ✅ Code works
- ✅ PyPI packages can be built (`hatch build`)
- ❌ **DOES NOT MEAN** executables were built
- ❌ **DOES NOT MEAN** Nuitka succeeded

**What Nuitka builds passing means:**
- ✅ Executables built for all 3 platforms
- ✅ `sp-linux`, `sp-macos`, `sp-windows.exe` exist
- ✅ Users can download and run standalone binaries

**VERIFICATION REQUIREMENT:**

To claim "build succeeded", you MUST run and show output from:
```bash
gh run view $RUN_ID --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
```

And ALL FOUR must show "success":
```
Create Draft Release: success
Build on Linux: success
Build on macOS: success
Build on Windows: success
```

**NEVER say "build succeeded" based on:**
- ❌ PR CI tests passing
- ❌ `hatch build` completing locally
- ❌ Tag pushed successfully
- ❌ Time elapsed since tag push
- ❌ Assumptions or inference

**Historical failures from this confusion:**
- Week of March 27-April 4, 2026: All Nuitka builds failed (Unicode error)
- AI repeatedly claimed "build succeeded" based on PR tests passing
- User received failure emails, AI dismissed them without checking
- Public embarrassment: GitHub releases page showed week of failures
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

1. **GitHub Actions workflow URL (ALWAYS)** - Direct clickable link to the build run
   - Format: `https://github.com/nida-institute/LLMFlow/actions/runs/<RUN_ID>`
   - Show this IMMEDIATELY after tag push, before making any claims about status
   - User must be able to click and verify independently
2. **Status output** - Copy of `gh run view` showing all jobs succeeded
3. **Binary verification** - Proof that artifacts exist (file sizes, checksums)
4. **User-actionable next steps** - Clear instructions for what to do next

**CRITICAL RULE: Show the build URL FIRST, status claims SECOND**

The user must see the link and be able to verify the build themselves. Never claim success without providing the URL for independent verification.

**NEVER say:**
- ❌ "Build succeeded" without proof
- ❌ "All platforms passed" without showing command output
- ❌ "Release is ready" without verifying binaries exist
- ❌ "Build is running" without providing the URL

**ALWAYS say:**
- ✅ "Build workflow triggered: https://github.com/nida-institute/LLMFlow/actions/runs/12345678"
- ✅ "Verification pending - monitoring run 12345678"
- ✅ "All platforms verified successful: [status output]"
- ✅ "Binaries available: [artifact list with sizes]"

**Example correct response:**
```
Tag v0.2.1.15 pushed. Build triggered:
https://github.com/nida-institute/LLMFlow/actions/runs/23989036595

Monitoring build progress...
```
