# GitHub Issue & Commit Workflow

## AI GitHub Authority — Hard Boundaries

These rules apply in every AI session in this repository. The machine-level version lives in `~/.sp/user-context/github-authority.md` and applies to all registered pipeline projects.

**AI may do without asking:**
- Read issues, PRs, code, and project boards
- Create issues
- Comment on issues or PRs
- Create branches and push commits
- **Create pull requests** for human review (completed, tested work only — not drafts or works-in-progress)

**Never without an explicit per-action instruction from the user:**
- Merge or apply a pull request
- Approve a pull request
- Assign an issue or task to any person
- Add or remove collaborators
- Close an issue not created in the current conversation turn
- Push to a protected branch (main, dev)

"It seemed like the next logical step" is not authorisation. Ask.

All AI GitHub actions should use a designated machine user account, not the repository owner's personal account, so AI actions are clearly distinguishable in the audit log.

---

## Issue Process

### Issues as Design Forum

Issues serve three roles in this project:

1. **Backlog management** — tracking features and bugs
2. **Upstream bug reporting** — documenting problems in dependencies or data sources
3. **Live design forum** — capturing the full trajectory of design decisions

For complex features, design conversations belong in issue threads, not in documents that drift out of sync. The entire history from initial proposal through implementation is preserved in the issue.

**Example pattern** (from discourse-flow nested pericope work):
- Issue #3: The "what" — rhetorical case, proposed schema, triggering conditions
- Issue #5: The "how" — pipeline design, prompt contracts, checkpoint implications

### Issue References in Commits

**Subject line format:**
```
feat: description (#93, #94)
```

**Commit body format:**
```
- Key change 1
- Key change 2
- Key change 3

Issues: #93, #94
Version: X.X.X.XX
```

**Auto-closing issues:**

Use `Closes #XX` or `Fixes #XX` in the commit body to trigger GitHub's automatic issue closure:

```
Enforce prompt contracts at runtime (Issue #96)

Implements runtime validation to prevent undeclared variables in
prompt bodies. Variables used in {{brackets}} must be declared in
the prompt header's 'requires' or 'optional' lists.

Key changes:
- src/llmflow/runner.py: Enhanced render_prompt() with contract enforcement
- tests/test_prompt_contract_enforcement.py: 7 comprehensive test cases

Test coverage: 1770 passed, 12 skipped (7 new tests)

Closes #96
Version: 0.2.1.14
```

When this commit is pushed to GitHub, Issue #96 will automatically close.

## Version Numbering

**CRITICAL:** Always increment the 4th component:
- `0.2.1.13` → `0.2.1.14`
- `0.2.1.14` → `0.2.1.15`

**Never propose minor/major bumps** unless explicitly requested by the user.

Each issue gets one version increment. The 4th component is the atomic unit of change tracking.

## CHANGELOG Updates

Every version in `CHANGELOG.md` documents completed issues:

```markdown
## 0.2.1.14 — 2026-04-02

### New Features

- **Runtime prompt contract enforcement** — Variables used in {{brackets}}
  must be declared in prompt header's 'requires' or 'optional' lists.
  Prevents undeclared variable expansion from context. (Issue #96)

### Test Coverage

- Added `tests/test_prompt_contract_enforcement.py` with 7 comprehensive tests
- Full test suite: **1770 tests passing** (7 new tests added)
```

Issues are referenced with `(Issue #XX)` notation for traceability.

## Using GitHub CLI

**Do NOT assume:**
- GitKraken is configured (MCP tools may not be available)
- Heredoc syntax works (it always corrupts in run_in_terminal)
- Permission to write to `/tmp`, `~/tmp`, or arbitrary directories

**DO use:**
- GitHub CLI (`gh`) for all GitHub operations
- `./tmp/` directory (workspace-relative) for temporary files
- Standard file writes instead of heredocs

**Example - closing an issue:**
```bash
gh issue close 96 --comment "Fixed in v0.2.1.14 - runtime prompt contract enforcement implemented"
```

**Example - viewing issue details:**
```bash
gh issue view 96
```

**Example - temporary file pattern:**
```bash
# Write to workspace-relative tmp/
cat > ./tmp/comment.txt << 'EOF'
Fixed in v0.2.1.14. Runtime prompt contract enforcement now validates that
all variables used in {{brackets}} are declared in the prompt header.
EOF

gh issue comment 96 --body-file ./tmp/comment.txt
```

## Workflow Summary

1. **Create issue** for feature/bug (or it already exists)
2. **Design discussion** in issue thread (for complex work)
3. **Implement** with test-first approach
4. **Commit** with issue reference and `Closes #XX`
5. **Update CHANGELOG** with issue reference `(Issue #XX)`
6. **Push** to trigger auto-close
7. **Verify** issue closed automatically

If auto-close doesn't work, use `gh issue close XX` manually.
