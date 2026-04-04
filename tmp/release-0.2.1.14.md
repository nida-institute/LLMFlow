# Release 0.2.1.14 - Tracking Issue

## Status
- ✅ Code committed to dev branch (commit da11f90)
- ✅ Pushed to origin/dev
- ⏳ CI re-running after fetch mock fix
- ⏳ Waiting to merge PR #90 to main
- ⏳ Tag release after merge

## What's in this release

### Type Safety & CI
- Pyright type checking in CI pipeline
- Zero type errors (1888 tests passing)
- Type stubs for all dependencies

### Content Lifecycle System
- Complete content stage transition system
- Sentinel-based permission management
- Git integration for transitions
- Full test coverage

### GUI Improvements
- Fixed file selection bug (Issue #110)
- Architecture documentation
- Comprehensive test suite

### Documentation
- AI context improvements
- "READ THIS FIRST" guidelines
- Prevent code duplication

## Next Steps

**When CI completes on PR #90:**
1. Merge PR #90 to main:
   ```bash
   gh pr merge 90 --merge --delete-branch=false
   ```

2. Switch to main and pull:
   ```bash
   git checkout main && git pull
   ```

3. Tag the release:
   ```bash
   git tag -a v0.2.1.14 -m "Release 0.2.1.14

Type safety, content lifecycle, GUI fixes"
   git push origin v0.2.1.14
   ```

4. Create GitHub release:
   ```bash
   gh release create v0.2.1.14 \
     --title "v0.2.1.14 - Type Safety & Content Lifecycle" \
     --notes-file tmp/release-notes-0.2.1.14.md
   ```

## CI Check
```bash
gh pr view 90 --json statusCheckRollup
```

Current CI runs: https://github.com/nida-institute/LLMFlow/actions/runs/23981765011
