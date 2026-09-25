---
name: stage-commits
description: |
  Stage the outstanding changes and print the exact strings needed to commit them.
  USE FOR: the end of a session, when work is finished and uncommitted; any time a human
  asks what the commit command is.
  DO NOT USE FOR: deciding whether the work is ready — that is commit-ready. This skill
  does not commit, push or merge.
---

# Stage Commits

## What this is for

Rule `commit-authority`: **the commit, the push and the merge are the human's.** An agent runs
the gates, writes the commit message to a file, and hands over the exact command.

This skill is that handover. It stages the paths and prints the command. It never runs
`git commit`. It never pushes. It never merges. Those are not limitations to work around — they
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

## Step 2 — group the changes, and ask

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

### Before staging: is the handoff stale?

Where the project keeps a handoff, check it **here** — before staging, not after. `/handoff`
writes that file, so a check that fires later leaves the fresh handoff outside the commit.

Three signals, each read from something declared rather than inferred:

```sh
git diff --cached --name-only
git log -1 --format=%cs
grep -m1 -E "^# HANDOFF" project/HANDOFF.md
```

- **The handoff is not among the files about to be staged, but other files are.** The strongest
  signal and the cheapest: the commit is about to make the handoff's in-flight section false, and
  nothing afterwards will correct it.
- **The date it declares is older than today.**
- **The date it declares is older than the last commit's date.** That means it has not been
  touched since the previous commit, so it is describing a tree two commits back.

**Do not try to check it by reading its prose** — parsing the in-flight list and testing whether
those files are still modified produces a derived set that silently becomes empty when the
document's shape changes, and then the check passes by vacuum. Rule
`check-the-source-not-the-rendering`.

**Ask; never block.** Say which signal fired and offer `/handoff`. If the human says go, go — a
one-line fix does not need a fresh handoff, and a gate that refuses gets routed around, which is
worse than no gate. This skill does not write the handoff; it says when it is worth writing.

---

## Step 3 — write each commit message to a file

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

## Step 4 — stage, naming every path

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

## Step 5 — check what is actually staged

```sh
git diff --cached --stat
```

Compare the file count against the list you meant to stage, and account for any difference before
going further. Staging is not evidence that the index holds what you think it holds.

### Two files to look for in that list, and what to do about them

This skill is the only one holding the actual staged set, so these checks are free. **It reports
them. It does not write either file.**

**The changelog.** If the staged set changes behaviour — source, schema, CLI — and the project's
changelog is not in it, say so. A ruling or a behaviour change that lands without a changelog
entry has no durable home, and the working document that carried it is deleted on its own
schedule. Writing the entry is the gate's job: point at `/commit-ready`, do not draft it here.

**The handoff.** Whether it needs rewriting was decided in Step 2, because that is the only point
at which the answer can still reach the commit. Here, confirm only that it is in the staged set if
it was rewritten — a fresh handoff left out of the commit is the same defect as a stale one left
in.

**Why point instead of write.** Both files already have an owner — the gate owns the changelog,
the handoff skill owns the handoff. A third mechanism that also writes them is two encodings of
one fact, and they agree right up until they silently do not. Rule `one-design`.

---

## Step 6 — hand over the command

Print it for the human to run. One commit:

```sh
git commit -F tmp/commit-1.txt
```

Several commits, staged and committed in turn:

```sh
git add "path/one" "path/two"
git commit -F tmp/commit-1.txt
git add "path/three"
git commit -F tmp/commit-2.txt
```

**Say plainly that the commit is theirs to run, and stop.** Do not run it. Do not offer to run
it. If they ask for the push command, give it — and say that a push is authenticated by their
credential, so the record will name them as the pusher whoever wrote the change.

---

## Step 7 — once the commit exists, show what landed

As soon as a commit has been made, run this and read it:

```sh
git show --stat HEAD
```

**"Committed" is not evidence that the commit holds what you think it holds.** Check the file
count against the list that was meant to be staged, and account for any difference out loud. A
commit whose message describes work it does not contain is worse than no commit, because the
message reads as authoritative to everyone afterwards.

Where several commits were made, check each:

```sh
git log --stat -3
```

Run this whenever a commit has happened in reach of this skill — the human pasting the command
in the same session counts. If nothing has been committed yet, say so rather than showing the
previous commit as though it were the new one.

---

## Step 8 — delete the files this skill made

Once the commit exists and Step 7 confirms it, the message files have done their job:

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
- **Re-run `commit-ready`'s checklist.** One design, not two.
- **Edit the files it is staging.** If something needs fixing, say so and stop; a fix folded into
  a staging step is a change nobody reviewed.
