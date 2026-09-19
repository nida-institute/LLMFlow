# Project Tracking Convention

Three places under `project/`, one job each. Getting a file into the wrong one is how a project
ends up with three half-answers to the same question and no way to tell which is current.

```
project/
  plans/                    design-<topic>.md, plan-<topic>.md   accumulates, then is deleted
  audits/                   audit-<subject>.md                    rolling, rewritten in place
  TODO.md                                                         rolling, the active queue
```

**This file is the authority.** Each directory also carries a `README.md` stating its convention
locally; those belong to the project and may be edited, so where one disagrees with this document,
this document is what holds.

---

## `plans/` — one document per piece of work

Named `design-<topic>.md` for what is being built and why, `plan-<topic>.md` for the steps when the
shape is already settled. **No dates in the filename**; the name is stable and dates go on entries
inside.

### Every document declares its status

```
**Status:** proposed (2026-09-18)
```

`proposed` means thinking aloud. **It is never authorization to build.** A document becomes `ruled`
when a person says so, and only then does implementation start.

This is the convention most often skipped under time pressure, and skipping it is how a proposal
becomes a decision nobody made. It matters most when an AI assistant wrote the document: the
assistant that drafts the plan also reads it back next session, and cannot tell its own proposal
from a human's ruling unless the document says which it is.

### These documents are temporary

**After about eight days a working document is either implemented or obsolete, and either way it
goes.**

Accumulated design documents confuse people and AI assistants differently, and both failures are
real. A person reads the newest and misses that an older one still governs. An assistant reads all
of them, cannot distinguish a proposal from a ruling or a live document from a dead one, and hands
the mixture back as though it were settled. Forty design documents are not a richer record than
four; they are an unreadable one.

Do not sift. Where a document still holds something valuable, neither a person nor a model can
reliably tell it from the rest.

### Commit it, then delete it

**Both halves, in that order.** "Git keeps every deleted file" is true only of a file git ever had;
a document written, used and deleted without a commit leaves nothing at all.

The lifecycle is: write it, commit it, work from it, **move what still has value to a permanent
home**, then delete the document in a commit of its own. `git log --diff-filter=D` finds what went
and `git show <commit>:<path>` brings it back.

**Deleting is not automatic.** List what is past eight days and ask; never delete unasked.

### Before deleting, move what still has value

A working document is deleted because it has served its purpose — **not because everything in it
stopped being true.** Version history is a place to recover something from, not a place anyone
looks. So before a document goes, each thing in it that still holds gets a permanent home:

- **Rulings → `CHANGELOG.md`.** It is the only document whose update is a side effect of the very
  work that would otherwise invalidate it. A ruling recorded there stays true; a ruling recorded
  only in a plan rots along with the plan. **A project without a changelog must establish one before
  applying the eight-day rule** — deleting a document is otherwise destroying the only copy of the
  decision.
- **Anything still true about how the project works → `docs/ai-context/`.** The map, the overview,
  the rules, or a topic document beside them. That is where the next session looks; a plan in a
  directory of plans is not, and a fact that lives only there is a fact that will be re-derived,
  wrongly, by somebody who never saw it.
- **Anything that belongs to a shipped file → that file.** A rule about how the tooling behaves
  belongs in the tooling's own documentation, not in a plan describing the change that introduced
  it.

**Then check that those documents still agree with each other.** This is the half that gets skipped.
Adding a fact in one place while a contradicting sentence stands in another is worse than not
recording it at all: a reader cannot tell which is current, and an assistant reads both and presents
the mixture as settled. When a document is retired, the documents it fed must be read together
afterwards, not one at a time.

**A document with nothing left to move is finished, and that is the normal case.** Most of what a
working document contains is the working — options weighed, evidence gathered, wrong turns
corrected. That is exactly what should not be carried forward.

---

## `audits/` — one rolling record per subject

Named `audit-<subject>.md`. **A project names its own unit** — a service, a package, a build target,
a generated artifact. Use the same name here and in `plans/`, so a reader who found one can guess
the other.

**No dates in filenames.** A record is rewritten in place and is therefore current by construction;
git history is the record of when. A dated filename produces a new file per run, and a growing set
is one nobody re-reads — each reader reads a different subset and they disagree without discovering
that they disagree. Dates belong on the individual findings inside.

A record carries the date of the audit and the data it was taken from, what passed and what failed
with locations specific enough to check, and a proposed fix where there is one. It does **not**
carry a verdict: an audit records what was found, and deciding what to do about it is someone else's
act.

When re-running an audit, rewrite the figures. A finding that still holds keeps its original date; a
fixed one is deleted, because git holds it. Appending a new section per run is a dated filename by
another name.

---

## Accumulating and rolling

The distinction that decides which rule applies:

- **Accumulating** — one more file per piece of work. `plans/` only. A growing set is one nobody
  re-reads, which is why the eight-day rule exists there and nowhere else.
- **Rolling** — overwritten in place, current by construction. `audits/`, `TODO.md`, handoffs,
  generated indexes. **Age is a reason to update these, not to delete them.** Prune stale entries
  instead.

Applying the eight-day rule to a rolling file deletes the current state of something. Applying the
rolling habit to `plans/` produces the pile it exists to prevent.
