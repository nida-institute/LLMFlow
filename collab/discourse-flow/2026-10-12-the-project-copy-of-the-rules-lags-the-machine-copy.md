# The project's copy of the rules lags the machine's copy, and nothing says so

**From:** discourse-flow · **To:** Scripture Pipelines · 2026-10-12

## What happened

A session starting in discourse-flow today read three sources of rules. They disagree on two
points, and nothing it read said which one is current.

| point | `docs/ai-context/sp/rules.md` (project, generated) | `~/.sp/disciplines/` (machine) |
|---|---|---|
| inline code | `inline-code-uses-a-heredoc`: *"Write inline code as a heredoc, never as `-c` or `-e`"* | `workflow.md:30`: *"Inline code — write it to a file. No heredocs, no `-c`, no `-e`."* |
| GitHub issues | `issues-need-approval`: *"run `gh issue create` only after explicit approval"* | `github-authority.md:27`: an agent may create an issue, rule `agent-may-file-issues` |

The sp-owned block at the top of discourse-flow's `CLAUDE.md` takes the project file's side on
the first point: *"write inline code as a heredoc, never `-c`"*.

## Why: one copy was refreshed and the other was not

Both disagreements were resolved upstream in `065bf747` (2026-10-07 20:57), which replaced
`inline-code-uses-a-heredoc` and `issues-need-approval` in `data/ai-rules.yaml`. Neither old
wording appears anywhere in `src/` or `data/` today. So the engine is consistent, and the
problem is copies of different ages:

| file | last written |
|---|---|
| `~/.sp/disciplines/workflow.md` | 2026-10-07 20:52, after the ruling |
| discourse-flow `docs/ai-context/sp/rules.md` | 2026-10-07 10:24, **before** the ruling |
| discourse-flow `CLAUDE.md` (the block sp owns) | 2026-09-19 |

These are filesystem times, used here only to order the writes. The project's `sp/` files were
regenerated that morning and are still uncommitted: its `cite-paths` example now names
`readers-guide.yaml`, from `70e8a7b0`. The refresh ran between those two commits and picked up
the first and not the second.

`sp doctor` or `sp init --update` in discourse-flow will presumably clear this, and we will run
it. That is not what this note is about.

## The question for sp

**A session cannot tell that the project's generated copy is behind the engine installed on the
same machine.** The machine-wide disciplines refresh with the engine; the project's
`docs/ai-context/sp/` and its `CLAUDE.md` block wait for someone to run a command. A session
that reads both gets two rules with the same authority and opposite instructions. It has two
choices, both bad:

- follow the stricter one, which is a guess about which is current;
- ask, which spends a person's attention on a version skew a tool could have reported.

Could the engine report it? For example: `sp lint`, or whatever a session runs first, could
warn when a `generated` file in the project differs from what this installation would write.
`sp doctor` already knows that difference, since it is what it restores. The warning would
name the file and the command that fixes it, and change nothing.

Whether that belongs in `sp lint`, in a session-start check, or nowhere is yours to decide.
We are reporting the skew, not proposing a mechanism.

## Not part of this

A third disagreement is ours, and we will fix it here: discourse-flow's `AGENTS.md:172` says
the agent should *"stage nothing"*, while `github-authority.md:29` lets it stage named paths.
`AGENTS.md` is ours to change.
