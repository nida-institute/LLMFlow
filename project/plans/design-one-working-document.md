# One working document per piece of work

**Status:** proposed (2026-09-08)
**Issue:** none. Related: #229 (false completion reports), #232 (defect log).

**This document is the first instance of the format it proposes** — one file covering the audit,
the diagnosis, the design and the checklist, rather than four that can contradict each other.

**Ruled by the Captain during design:**

1. *"anything more than a few weeks old — plans, decisions, audits — is probably obsolete"*, then
   the argument that settles it: *"if it's still valuable, neither I nor an LLM can distinguish
   the valuable content from anything else"*, and the window: *"after a work week, it is usually
   either implemented or obsolete"* — set at **eight days**.
2. *"rulings are permanent until overruled"*, and they live in the **CHANGELOG**; *"decision lists
   should also be deleted"*.
3. **Accumulating versus rolling** is the line that decides which files the deletion touches.
4. *"hard distinctions between audits, plans, design, and rulings have proven hard to maintain"* —
   the work is one continuous act.
5. Checklists with verified completion: *"often, I have to ask an LLM to make a detailed checklist
   so it doesn't do 3/4 of the work and stop, claiming to have finished it."*

---

## 1. The problem, measured

Counted 2026-09-08 by last-commit date. Re-derive with `git log -1 --format=%ad --date=short`
per file.

| repository | plans | audits | over 8 days | over 60 days |
|---|---|---|---|---|
| Scripture Pipelines | 49 | 2 | ~37 | 1 |
| discourse-flow | 42 | 34 | 62 | 21 |
| ears-to-hear | 13 | 1 | 14 | **14 — all of them** |

Among this engine's 51 there are roughly **forty distinct `Status:` wordings**, almost no two alike:
*"Implemented — historical record"*, *"Proposed, 2026-08-25. All four questions in §7 are
answered"*, *"Decisions implemented — historical record, and the decision log is still binding"*,
*"D1–D7 ruled… D1 has a blocking technical conflict"*.

Nobody could write those consistently because the field was carrying four independent questions at
once — approved? built? questions open? still binding? — and because **the document types do not
match the work**. An audit diagnoses, a design answers, a plan sequences, and the implementation
proves it; that is one continuous act, so a file that starts as an audit becomes a design and then
a plan, and its status line ends up describing whichever phase it is in.

The consequence is drift: no session reads 76 documents, so each reads a different subset, and the
subsets disagree.

## 2. What is already built

The lifecycle half shipped on 2026-09-08 as rule `plans-are-temporary` in `data/ai-rules.yaml`,
rendered into every project's `docs/ai-context/sp/rules.md`:

- A working document has a death; a **ruling** does not — a ruling is permanent until overruled
  and lives in the CHANGELOG, or in the rules file when it binds future work.
- After **eight days** a working document is either implemented or obsolete, and either way the
  file goes, **unread**. Do not sift.
- **Accumulating, not rolling.** A file updated in place is current by construction; its age is a
  reason to update it, not to delete it. Prune its stale entries instead.
- **The deletion is the Captain's, every time.**

Why the CHANGELOG is the durable home, and this was checked rather than assumed: it is the only
place whose update is a *side effect of the very work* that would otherwise invalidate it. On the
day the rule was written, a 190-line design document had seven distinct rulings in it and all
seven were already present in the CHANGELOG entry for the same change. Deleting that plan unread
would have lost nothing.

## 3. What this document proposes, and none of it is built

### 3.1 One type, not four

`project/plans/` holds **working documents**. There is no separate document kind for an audit or a
design: a piece of work produces one file, which grows through its phases and is deleted when the
work lands.

```
Status: proposed (2026-09-08)     thinking aloud — findings, diagnosis, a design. NOT authorization.
Status: ruled (2026-09-08)        decided, in flight. The checklist below is the work.
```

Two values, because the only distinction that has to survive is the one `design-authority` needs:
whether this is a thing someone decided, or a thing someone is thinking about.

**`project/audits/` stops being a separate kind.** The rolling per-subsystem audits that
`disciplines/project-tracking.md` describes keep working — they are rolling files and exempt —
but a *dated, per-run* audit record is a working document like any other.

### 3.2 A checklist, and a box carries its evidence

The last phase of a working document is a checklist, and **a ticked box states how it is known**:

```markdown
## Checklist
- [x] lint rejects the old key — tests/test_resource_key_migration.py::test_a_pipeline_using_it_does_not_lint
- [x] consumer pipelines migrated — 5 keys across 2 repos, all 7 lint clean (2026-09-08)
- [x] docs updated — docs/llmflow-language.md, architecture.md §3.1, both templates re-synced
- [ ] CHANGELOG entry
```

Not *done* — **how you know**: a test id, a command and its result, a file and a line. That turns
a completion claim from an assertion into something a reader checks in one step, which is what
#229 says is missing — *"a report of completion is a factual claim, and making it without having
verified it is a false statement, not optimism."*

**The case for it is not theoretical.** On 2026-09-08 this assistant reported a thread complete;
hours later, looking at `discourse-flow` for an unrelated reason, it found a pipeline broken by the
very defect that thread had addressed — inside the scope it had called done. The test suite caught
that day's other lapses. It could not catch this one, because it was in another repository. **A
checklist is the only guard over the parts no suite covers**: documentation, consumer repositories,
replies owed to other projects.

### 3.3 A guard, and an honest account of its limits

A test over working documents asserting that no `- [x]` line lacks evidence after the dash.

It is a pattern over our own declared format, so it is not the anti-pattern
`check-the-source-not-the-rendering` names — we define the format rather than re-deriving it from
prose someone else wrote. But it is **approximate in a way worth stating**: it can check that
something evidence-shaped is present, never that the evidence is true. A determined box-ticker
defeats it in one line.

It is still worth having. It converts an omission from invisible to loud, and the failure mode is
not usually deceit — it is finishing three quarters and losing track.

## 4. What it costs

| | |
|---|---|
| collapsing the types | a convention change. Existing `audits/` files drain under the eight-day rule rather than being migrated |
| the checklist | nothing structural; it is a section in a document that already exists |
| the guard | one test file |
| `project/scratchpad/` | two file moves here — `REVIEW.md` and `tmp-context.md`, referenced by nothing |

Deliberately **not** proposed: moving `TODO.md` and `HANDOFF.md` into a `project/rolling/`
directory. Measured at **27 files** referencing `project/TODO.md`, including `data/file-catalog.yaml`,
five shipped templates, six tests and a machine-wide skill — and `sp init` creates that path, so
moving it breaks the scaffold every consumer inherits. The benefit would be that a directory name
carries the meaning instead of a rule carrying it; `declared-not-inferred` means a reader must
consult the declaration either way.

## 5. Decisions for the Captain

Answer inline after each `=>`.

### D1. Where does the checklist rule live?

#229 argues that false completion reports belong in the **Helm layer** rather than `sp/rules.md`,
because they are about AI collaboration generally and not about pipelines. The same argument
applies here. Against it: the rest of the document lifecycle is already in `data/ai-rules.yaml`, and
splitting one convention across two homes is what this whole design is trying to stop.

- **A** — all of it in `data/ai-rules.yaml`, beside `plans-are-temporary`.
- **B** — the lifecycle in `data/ai-rules.yaml`, the checklist obligation in the shared discipline,
  where it reaches Human at the Helm too. Costs a `helm-sync.yaml` update and a twin commit.

=> **B. "this feels helm to me."** The checklist obligation is about how AI collaboration fails,
not about pipelines, which is the same argument #229 makes for its three failure modes. It goes
into the shared discipline and reaches Human at the Helm; the lifecycle rule stays in
`data/ai-rules.yaml` because *that* is about this project's document layout.

### D2. Do you want the guard, knowing it can only check that evidence is present?

=> **Yes.**

### D3. Does `project/audits/` go away entirely, or stay for rolling per-subsystem audits?

`disciplines/project-tracking.md` describes both a rolling per-subsystem audit and a per-artifact
record *"retained as record"*. The second directly contradicts the eight-day rule, and the two
documents currently give a reader opposite instructions.

=> **Yes, it goes away.**

**Measured after the ruling, because the question understated it: 21 files.** `project/audits/`
is a shipped scaffold, not a local directory. Removing it touches a catalog entry, a shipped
template, a whole shipped document (`sp/audits-pattern.md` and its mirror), two audit skills,
three disciplines — one of them **Helm-shared**, so a twin commit — the `file-organisation` rule
which names the directory, two tests, and four docs. A separate `docs/audits/` also exists and is
a different thing.

That makes it its own piece of work rather than a clause of this one. It also has to be done in
one pass per `one-design`: a half-removed scaffold leaves two conventions live at once, which is
the defect this whole design is against.

### D4. `project/scratchpad/` — add it now, or leave it?

=> **Not needed. `tmp/` already is it**, declaratively: `tmp/.gitignore` ignores everything with
`*` plus named negations, and its comment records the incident that made it so — `9b09195`
committed two commit-message drafts because the rule lived in `CLAUDE.md` where no tool read it.

So the layout is three places and none of them is new:

| | holds | lifecycle |
|---|---|---|
| `project/` top level | `TODO.md`, `HANDOFF.md`, `RELEASE_CHECKLIST.md` | rolling — update, never delete by age |
| `project/plans/` | working documents, one per piece of work | accumulating — eight days |
| `tmp/` | throwaway | untracked; delete freely |

The two strays resolve without a new directory: `REVIEW.md` is a working document fourteen days
old, so the eight-day rule already covers it, and `tmp-context.md` is scratch that belongs in
`tmp/`.

## 6. Checklist

- [ ] D1–D4 answered
- [ ] rule text drafted and approved — `data/ai-rules.yaml` is the Captain's file
- [ ] guard written, with a test that the scan finds something (so it cannot pass by reading nothing)
- [ ] `disciplines/project-tracking.md` reconciled with the eight-day rule, per D3
- [ ] this document deleted, its rulings in the CHANGELOG
