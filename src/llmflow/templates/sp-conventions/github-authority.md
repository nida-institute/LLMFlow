# GitHub Authority Policy

These rules apply to every AI session on this machine, in every project.

## Identity

All AI-initiated GitHub actions should use a designated machine user account so that AI actions are clearly distinguishable from human actions in the audit log.

**Recording which account is yours, not the tooling's.** Put the machine user's address and GitHub username somewhere that belongs to you alone — an untracked file, or a directory outside the repository — so that no install or update step overwrites it and nothing ships it to anyone else. Point `env.GH_CONFIG_DIR` in your Claude Code settings at that account's `gh` configuration so AI sessions authenticate as it rather than as you.

## What AI may do without asking

- Read issues, PRs, code, and project boards
- Create GitHub issues
- Comment on issues or PRs
- Create branches and push commits
- **Create pull requests** for human review (completed, tested work only)

## Hard stop — never without explicit per-action instruction

- **Merge or apply a pull request** — human review and merge only
- **Approve a pull request**
- **Assign an issue or task to any person**
- **Add or remove collaborators or team members**
- **Change org-level settings or permissions**
- **Close an issue** not created in the current conversation turn
- **Push to a protected or shared branch** (main, dev) without being asked

"It seemed like the next logical step" is not authorisation. Workflow patterns and prior context are not authorisation. Ask.

## Why this policy exists

An AI acting on a user's GitHub account can affect colleagues' work and professional reputation without their knowledge. In April 2026 an agent applied PRs and assigned tasks to team members without being asked. This policy exists to prevent recurrence.

## Recommended PAT scopes for the machine user account

| Scope | Reason |
|---|---|
| `repo` (read) | Read code, issues, PRs |
| `issues: write` | Create and comment on issues |
| `pull_requests: write` | Create PRs (not merge) |
| No `org` permissions | Cannot assign people or change team membership |
| No `merge` / admin | Cannot merge PRs or change branch protection |
