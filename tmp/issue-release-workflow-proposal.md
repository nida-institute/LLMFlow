# Proposal: Adopt Standardized Release Workflow from LLMFlow

## Summary

Implement the release management workflow developed for LLMFlow, which enforces "main is always releasable" through automated PR CI validation, structured release tracking, and build-from-main discipline.

## Background

LLMFlow recently formalized its release process after experiencing:
- Builds from wrong branches (dev instead of main)
- Merges with failing tests
- Unclear release status tracking
- Manual, error-prone release steps

The solution: A documented workflow + `/publish` skill that automates and enforces best practices.

## The LLMFlow Release Workflow

### Core Principle: PR CI is Your Test Build

```
1. Work on dev branch
2. Open PR (dev → main)     ← CI RUNS HERE (Test Build)
3. Fix any test failures    ← Keep pushing to dev
4. CI goes green ✅         ← Test build passed
5. Merge PR to main         ← Only when test build succeeds
6. Checkout main
7. Tag from main            ← Final build happens here
8. Build package (hatch build, etc.)
9. Publish (PyPI, GitHub releases, etc.)
```

### Why This Matters

**Traceability** - Every release corresponds to a specific commit on main
**Reproducibility** - Anyone can checkout the tag and rebuild the exact artifact
**Quality Gate** - main represents production-ready code that passed all checks
**Trust** - Users expect releases to match the default branch

### What's Enforced

❌ **Never:**
- Build from dev/feature branches
- Merge with failing CI
- Tag before merge to main
- Skip the PR (direct merge bypasses test build)

✅ **Always:**
- Test on PR CI before merge
- Merge only when green
- Tag from main
- Build from main after tagging

## Benefits for This Project

1. **Eliminates "main is broken"** - No merges until CI passes
2. **Clear release timeline** - Tags on main show what was released when
3. **Reproducible builds** - Anyone can rebuild from a tag on main
4. **Reduced manual errors** - Automated checks catch common mistakes
5. **Better collaboration** - Clear handoff between dev work and releases

## Implementation Checklist

### Phase 1: Documentation (1-2 hours)
- [ ] Document release workflow in CONTRIBUTING.md or RELEASES.md
- [ ] Add "Build from Main" section to README
- [ ] Create release checklist template

### Phase 2: Process Changes (ongoing)
- [ ] Require PR reviews before merge
- [ ] Enforce CI passing before merge (GitHub branch protection)
- [ ] Use PR CI as test build
- [ ] Always tag from main, never dev

### Phase 3: Automation (optional, 2-4 hours)
- [ ] Create `/publish` skill (or equivalent script) to automate:
  - Version bump verification
  - CHANGELOG generation from commits
  - Issue tracking (comment + label issues mentioned in commits)
  - CI status checking
  - Release notes generation
  - tmp/ file tracking for audit trail

### Phase 4: GitHub Configuration
- [ ] Enable branch protection on `main`:
  - Require pull request reviews
  - Require status checks to pass
  - Require branches to be up to date
- [ ] Configure CI to run on all PRs
- [ ] Set up automated release notes (GitHub Releases)

## Example: LLMFlow's Current Release (v0.2.1.14)

**What we learned:**
1. CI caught test failures that passed locally (environment differences)
2. PyPI build had duplicate file warnings (fixed before release)
3. Proper tmp/ cleanup prevented committing 30+ obsolete files
4. Release tracking in tmp/release-0.2.1.14.md provided clear audit trail

**Workflow in action:**
```bash
# 1. Fixed issues on dev, committed
git add -A && git commit -m "fix: PyPI build issues"
git push origin dev

# 2. PR CI ran (test build)
gh pr view 90 --json statusCheckRollup  # Monitored status

# 3. When CI passed:
gh pr merge 90 --merge

# 4. Final build from main:
git checkout main && git pull
git tag -a v0.2.1.14 -m "Release 0.2.1.14"
hatch build  # ← Building from tagged main
```

## Resources

- **LLMFlow /publish skill**: Comprehensive release automation
- **SKILL.md**: Full workflow documentation with examples
- **LLMFlow PR #90**: Real example of this workflow in action

## Questions / Discussion

1. **Do we currently have branch protection on main?**
2. **What's our current release cadence?**
3. **Do we use GitHub Releases or just tags?**
4. **Should we implement the full automation or start with manual process?**

## Proposed Next Steps

1. Review this workflow with the team
2. Decide on Phase 1-2 implementation (documentation + process)
3. Test workflow on next release
4. Evaluate whether Phase 3 automation is needed
5. Document lessons learned

---

**Related:**
- LLMFlow repository: https://github.com/nida-institute/LLMFlow
- LLMFlow PR #90: https://github.com/nida-institute/LLMFlow/pull/90
- Release tracking: LLMFlow/tmp/release-0.2.1.14.md
