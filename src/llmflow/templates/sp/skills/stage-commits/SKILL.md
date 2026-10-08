---
name: stage-commits
description: |
  Stage the outstanding changes — the agent runs `git add` itself — and print the exact
  commit command for the human to run.
  USE FOR: the end of a session, when work is finished and uncommitted; any time a human
  asks what the commit command is.
  DO NOT USE FOR: deciding whether the work is ready — that is commit-ready. This skill
  does not commit, push or merge.
---

# Stage Commits

## What this is for

Rule `commit-authority`: **the commit, the push and the merge are the human's.** An agent runs
the gates, writes the commit message to a file, and hands over the exact command.

This skill is that handover. **The agent stages: it runs `git add` itself**, then prints the
commit command. "Staging" never means handing the human a `git add` to run — that leaves the
reviewed set and the committed set to two people, and is the one part of this the agent owns. It
never runs `git commit`. It never pushes. It never merges. Those are not limitations to work around — they
are the whole point, because a commit carries an author and a push carries an identity, and
neither is the agent's to spend.

**`commit-ready` is the gate; this is the mechanism.** That skill decides whether a commit may
happen and what the message must contain. This one re-checks none of it. If the gates have not
been run, say so and point at `/commit-ready` — do not re-implement its checklist here.

---

## Step 1 — see what is outstanding

```sh
git status --short --branch
```

Use `--branch`, not bare `--short`: a clean tree prints nothing at all under `--short`, so a
successful run and a failed command look identical. The `##` header always prints.

Where a tracked directory produces overwhelming noise — a vendored dependency tree, a build
output — narrow the view rather than scrolling past it:

```sh
git status --short --branch -- . ':(exclude)path/to/noisy/dir'
```

**Read the whole list before grouping.** A path you do not recognise is the important one.

---

## Step 2 — bring the handoff and the changelog up to date, before anything is grouped

**Both are updated first, as files of the commit — never reported after it.** A commit that
leaves the handoff describing an older tree, or lands a behaviour change with no changelog entry,
has made both records false the moment it exists, and nothing afterwards corrects them. Checking
them after staging is too late to matter: the fresh file would have to be fitted into a set
already reviewed.

**This skill still writes neither.** `/handoff` owns the handoff and `/commit-ready` owns the
changelog's rules. This step runs them before grouping, so what they write is one of the files the
human sees grouped — rule `one-design`: one owner each, called at the one point their output can
still reach the commit.

### The changelog

If the outstanding changes alter behaviour — source, schema, the CLI, a shipped template, prompt
or document — and the project's changelog does not yet carry an entry for them, write the entry
now, to `/commit-ready`'s rules. A change that is not behaviour — a record, a test that only
pins existing behaviour — needs none; say which it is rather than skipping the check silently.

### The handoff

Where the project keeps a handoff, check whether it is stale, and if any signal fires, run
`/handoff` before grouping.

#### How to tell it is stale

**The primary signal is the commit, not the date.** A handoff names the commit it was written
against — "level with `origin/dev` at `3dbb55b`", or similar. If `HEAD` is not that commit, the
handoff is describing a tree that no longer exists:

```sh
git rev-parse HEAD
grep -m1 -E "[0-9a-f]{7,40}" project/HANDOFF.md
```

Both sides of that comparison are declared — one by the file, one by git — so neither is an
inference about the other. Rule `declared-not-inferred`.

**Why the date is not enough on its own, and why this check leads with the sha.** The first
version of this check had only date signals, and it was run on the day it shipped against a
handoff whose own text read *"Nothing from this session is committed"* while two commits already
existed. Every signal missed: dates compare at **whole-day granularity**, and a handoff written
and superseded within the **same day** is the ordinary case, not an edge one. Do not simplify the
sha comparison away as duplicating the dates — it is the one that works.

Then the weaker signals, which still matter for a handoff that names no commit at all:

```sh
git diff --cached --name-only
git log -1 --format=%cs
grep -m1 -E "^# HANDOFF" project/HANDOFF.md
```

- **The handoff is not among the files about to be staged, but other files are.** The commit is
  about to make its in-flight section false, and nothing afterwards will correct it.
- **The date it declares is older than today.**
- **The date it declares is older than the last commit's date**, so it has not been touched since
  the previous commit and is describing a tree two commits back.

**Do not try to check it by reading its prose** — parsing the in-flight list and testing whether
those files are still modified produces a derived set that silently becomes empty when the
document's shape changes, and then the check passes by vacuum. Rule
`check-the-source-not-the-rendering`.

**When a signal fires, the handoff is rewritten before grouping.** Say which signal fired and run
`/handoff`; the rewritten file is then grouped with the rest. Skipping it is the human's call,
made explicitly — never the default.

---

## Step 3 — group the changes, and ask

**Group by concern, not by directory.** One commit per concern is what the commit-message
convention assumes: a subject naming what is now true, and a body whose bolded lead phrases each
cover one piece of work.

**Then ask the human to confirm the grouping, and to confirm whose each change is.**

This is the step that cannot be skipped, and it is not deference for its own sake. A working tree
holds changes the agent did not make — another session's, another tool's, the human's own work in
progress, a file deliberately held back from a release. **Nothing in `git status` says whose a
change is.** Guessing produces a commit that sweeps somebody else's unreviewed work in under the
agent's message, which is unrecoverable once pushed.

Present the groups, name any path whose origin is unclear, and wait.

---

## Step 4 — write each commit message to a file

Write the message with the file tools, one file per commit: `tmp/commit-1.txt`,
`tmp/commit-2.txt`.

**Every file this skill creates goes in `./tmp`, and nowhere else.** Message files, any scratch
list, anything at all. `tmp/` is throwaway by convention and git-ignored in most projects, so
nothing the skill produces can reach a commit by accident — which matters here more than
elsewhere, because this skill's whole job is deciding what reaches a commit. Never write a
message file to the repository root.

**The message goes in a file, and the command reads it with `-F`. This is not a style
preference — it is what makes the command portable.** A message containing a quote, a backtick,
a `$` or a newline behaves differently in `sh`, `bash` and `zsh` when it is passed inline. Put it
in a file and quoting stops being part of the problem.

Follow the project's commit-message convention for the content. If the project has none: a
subject line `type(scope): what changed`, a blank line, then a body whose bolded lead phrases
each cover one piece of work, what was verified with the command and its result, and what was
deliberately left out.

Close issues from the body where the project's workflow says to — `Closes #N`. Note that a
closing keyword fires only when the commit reaches the repository's **default** branch, so on a
working branch the issue stays open until the merge. Do not record it as closed meanwhile.

Add whatever attribution trailer the project or the session requires.

---

## Step 5 — stage, naming every path

**The agent runs this itself.** Staging is the agent's act, done with its own shell, before the
human sees anything — not a command printed for the human to paste. The human's part starts at
Step 7, with the commit.

```sh
git add "project/TODO.md" "project/HANDOFF.md" "docs/example.md"
```

**Name every path explicitly. Never sweep.** `git add` with a sweep flag takes everything the
working tree happens to hold — including a tracked dependency directory whose files were deleted
to free disk, a vendored file that regenerates, and a change somebody is holding back on purpose.
An explicit list cannot pick those up; a sweep silently will. This is a real failure, not a
hypothetical one.

**Quote every path.** `zsh` does not word-split an unquoted variable and `bash` does, so an
unquoted path containing a space behaves differently depending on who pastes it.

**A renamed file needs both halves named**, or git records a delete plus an add and the history
does not follow it.

**Never name a path that no longer exists.** An unmatched pathspec aborts the *entire* command
and stages nothing — yet if an earlier `git mv` already staged something, a commit afterwards
still succeeds, carrying a message describing work it does not contain.

---

## Step 6 — check what is actually staged

```sh
git diff --cached
```

**Show the diff, never a summary.** `--stat` gives file names and a count of changed lines, which
answers "did I stage roughly the right files" and nothing else. What a reviewer is looking for is
what the change actually says: a line nobody meant to touch, a stray edit inside a file that does
belong in the commit, someone else's work carried along inside a shared file. A summary hides
every one of those — and hides them behind a number that reads like verification.

Compare the file list against the one you meant to stage, and account for any difference before
going further. Staging is not evidence that the index holds what you think it holds.

### Two files to confirm in that list

Both were brought up to date in Step 2; here, confirm they are in the staged set. A fresh handoff
or a new changelog entry left out of the commit is the same defect as a stale one left in.

**The changelog.** If the staged set changes behaviour — source, schema, CLI, a shipped template
or prompt — the changelog must be among the staged files. If it is not, Step 2 was skipped: stop
and go back to it rather than staging around the gap. A ruling or a behaviour change that lands
without a changelog entry has no durable home, and the working document that carried it is
deleted on its own schedule.

**The handoff.** If Step 2 rewrote it, it must be staged with the commit it describes.

**Why this skill does not write them itself.** Both files already have an owner — `/commit-ready`
owns the changelog's rules, `/handoff` owns the handoff. Step 2 runs them; it does not repeat
them. A third mechanism that also writes them is two encodings of one fact, and they agree right
up until they silently do not. Rule `one-design`.

---

## Step 7 — hand over the command

Print it for the human to run. The index is already staged — Step 5 did that — so the command is
the commit alone:

```sh
git commit -F tmp/commit-1.txt
```

**Several commits are staged and committed in turn, and the agent does the staging each time.**
Stage the first group, hand over its commit command, and wait. Once the human has committed and
Step 8 has shown what landed, stage the next group, show its diff, and hand over its command. The
human is never handed a `git add`.

**Say plainly that the commit is theirs to run, and stop.** Do not run it. Do not offer to run
it. If they ask for the push command, give it — and say that a push is authenticated by their
credential, so the record will name them as the pusher whoever wrote the change.

---

## Step 8 — once the commit exists, show what landed

As soon as a commit has been made, run this and read it:

```sh
git show HEAD
```

**"Committed" is not evidence that the commit holds what you think it holds**, and neither is a
summary of it. Read the diff. Check the files against the list that was meant to be staged, and
account for any difference out loud. A commit whose message describes work it does not contain is
worse than no commit, because the message reads as authoritative to everyone afterwards.

Where several commits were made, show each diff without repeating the messages you already wrote:

```sh
git diff HEAD~2 HEAD
```

A large diff is not a reason to fall back to `--stat`. Show it in groups — the mechanical changes
first, where a stray edit stands out, then the substantial ones — using a pathspec:

```sh
git show HEAD -- "path/one" "path/two"
```

Run this whenever a commit has happened in reach of this skill — the human pasting the command
in the same session counts. If nothing has been committed yet, say so rather than showing the
previous commit as though it were the new one.

---

## Step 9 — delete the files this skill made

Once the commit exists and Step 8 confirms it, the message files have done their job:

```sh
rm -f tmp/commit-1.txt tmp/commit-2.txt
```

**Delete them by name, not with a wildcard sweep of `tmp/`.** That directory holds other
sessions' unbacked drafts — issue bodies, diffs, notes that exist in exactly one place — and it
is git-ignored, so a sweep is unrecoverable.

**Do not delete anything before the commit succeeds.** If the commit is refused, or the human
decides to change the message, the file is the only copy of the text.

---

## Portable shell — what is ruled out

Everything this skill emits must run in `sh`, `bash` and `zsh` alike. A construct that works in
the shell the author happened to use, and not in the one the reader has, fails at the moment the
reader can least afford it: mid-commit, with a staged index.

| do not use | use instead |
|---|---|
| `git commit -m "…"` | `git commit -F <file>` |
| `echo -e`, `echo -n` | `printf` |
| `[[ … ]]` | `[ … ]` |
| `(( … ))` | `expr`, or restructure |
| arrays, `+=` | positional parameters, or separate commands |
| process substitution | a temporary file |
| `$'…'` quoting | a literal, or `printf` |
| `&>` | `> file 2>&1` |
| `function name() {` | `name() {` |

Anything emitted as a script file starts `#!/bin/sh`, not `#!/bin/bash`.

`tests/test_stage_commits_is_portable.py` holds this by test rather than by attention — it reads
the shipped template and refuses each construct above.

---

## What this skill never does

- **Commit, push or merge.** `commit-authority`. Passing the gates is not authorization.
- **Sweep.** Every path is named.
- **Guess whose a change is.** It groups and asks.
- **Stage before the handoff and the changelog are current.** Step 2 comes first.
- **Hand the human a `git add`.** Staging is the agent's; the human's command is the commit.
- **Re-run `commit-ready`'s checklist.** One design, not two.
- **Edit the files it is staging.** If something needs fixing, say so and stop; a fix folded into
  a staging step is a change nobody reviewed.
