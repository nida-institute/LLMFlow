# GitHub Authority Policy

These rules apply to every AI session on this machine, in every project.

## Identity

The goal is an audit trail in which AI actions are distinguishable from yours. There are three levels, and only the first is available to everyone.

**Free, and needs no account of any kind: the git author.** A git author is a name and an email string in the commit object, not a login — nothing validates it. Give AI commits a distinct one and `git log` tells you at a glance which changes were the AI's:

```bash
git config user.name  "Claude (AI agent)"
git config user.email "you+agent@example.com"
```

Set it per repository where the AI works, or pass `-c user.name=… -c user.email=…` on the commit. This works on any machine, on any plan, with no permissions and nothing to provision.

**Optional, and free: a second account on the hosting service**, so AI-initiated issues and pull requests appear under the agent rather than under you. Where your tooling supports it, point its credential configuration at that account — in Claude Code, `env.GH_CONFIG_DIR`.

**Never required: a paid seat, an organisation role, or an additional account for your AI tool.** Many people cannot create these — managed plans, personal plans, employer policy. If that is you, the git author above, plus the co-author trailer on commits, is a sufficient trail. Say so plainly rather than treating this policy as unmet.

**Record which identity is the AI's, not the tooling's.** Put the details somewhere that belongs to you alone — an untracked file, or a directory outside the repository — so that no install or update step overwrites it and nothing ships it to anyone else.

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

## When an action is interrupted, verify before reporting

A destructive or hard-to-reverse action that fails, is cancelled, or is interrupted has not
necessarily done nothing. Check the actual state — `gh pr view`, `git log`, the API — and report
what you find. Never report "nothing was changed" from the fact that the command did not finish.

This is the second half of the rule above. The first half says what may not be attempted; this
says what is owed once something was attempted and the outcome is unknown. An unverified
"nothing happened" is the more damaging of the two failures, because it closes the question.

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
