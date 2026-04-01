# Issue: `sp` Command Not Available After `hatch shell` in Development

## Problem Statement

When developers clone the LLMFlow repository and run `hatch shell` to enter the development environment, the `sp` command is not available, even though they're in the correct virtual environment.

**Current behavior:**
```bash
git clone https://github.com/nida-institute/LLMFlow
cd LLMFlow
hatch shell
sp --help  # Error: sp: command not found
```

**Why this happens:**
- `hatch shell` activates the virtual environment
- But it doesn't install the package itself in editable mode
- The `sp` command is defined in `[project.scripts]` but only available after package installation

**Impact:**
- Confusing for new contributors
- Extra manual step required: `pip install -e .`
- Breaks the flow when switching between projects
- Not documented anywhere in contributor docs

## Expected Behavior

After running `hatch shell`, the `sp` command should be immediately available for development work.

```bash
git clone https://github.com/nida-institute/LLMFlow
cd LLMFlow
hatch shell
sp --help  # Should work immediately
sp run --pipeline pipelines/hello.yaml  # Should work
```

## Proposed Solution

Add `post-install-commands` to the `[tool.hatch.envs.default]` section in `pyproject.toml`:

```toml
[tool.hatch.envs.default]
dependencies = [
  "pytest",
  "pytest-asyncio",
  "pytest-mock"
]
post-install-commands = [
  "pip install -e ."
]
```

**How this works:**
1. When hatch creates/updates the environment, it runs `post-install-commands`
2. `pip install -e .` installs llmflow in editable/development mode
3. This makes the `sp` command available via the `[project.scripts]` entry point
4. Developers can immediately use `sp` commands

**Benefits:**
- Zero extra steps for contributors
- Consistent with developer expectations (enter shell → tools work)
- Editable mode means code changes are immediately reflected
- Aligns with standard Python development workflow

## Alternative Solutions Considered

### Alternative 1: Document the manual step
**Pros:** No code changes
**Cons:** Friction for every contributor, easy to forget, not discoverable

### Alternative 2: Use `hatch run sp` instead of `hatch shell`
**Pros:** Works without entering shell
**Cons:** Doesn't solve the interactive development case, verbose for iterative work

### Alternative 3: Add to CONTRIBUTING.md or README
**Pros:** Educates developers
**Cons:** Still requires manual step, contributes to "documentation debt"

## Implementation Checklist

- [ ] Add `post-install-commands` to `pyproject.toml`
- [ ] Test on clean clone: `rm -rf .venv && hatch shell && sp --help`
- [ ] Update CONTRIBUTING.md to document the automatic editable install
- [ ] Verify works on Linux, macOS, Windows
- [ ] Confirm doesn't interfere with regular package installation via pip

## Testing Plan

**Test 1: Fresh clone**
```bash
git clone https://github.com/nida-institute/LLMFlow test-repo
cd test-repo
hatch shell
sp --version  # Should print version
sp run --help  # Should show help
```

**Test 2: Code changes take effect**
```bash
hatch shell
# Edit src/llmflow/cli.py to add a test print
sp --version  # Should reflect changes without reinstall
```

**Test 3: Doesn't break normal installation**
```bash
pip install llmflow  # Should still work for end users
sp --version  # Should work
```

## Related Issues

- Part of improving contributor onboarding experience
- Complements #93 (global conventions installation)

## Notes for Reviewers

**What makes this safe:**
- `post-install-commands` runs ONLY in the development environment (not for end users)
- Editable installs are the standard Python development pattern
- Hatch officially supports this pattern: https://hatch.pypa.io/latest/config/environment/overview/#post-install-commands

**Potential concerns:**
- If someone already has `pip install -e .` from before, it's idempotent (safe to run again)
- Doesn't change how end users install the package via `pip install llmflow`

---

**Submitted by:** Developer Experience Audit
**Date:** April 1, 2026
**Priority:** Medium (affects contributors, not end users)
**Effort:** Small (~15 minutes to implement and test)
