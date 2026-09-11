# Adapting `audit-levinsohn-method.md` to the document lifecycle

**From:** an AI session in `nida-institute/LLMFlow` (Scripture Pipelines), 2026-09-09.
**Status: drafted by the AI, pending the Captain's review.** Nothing here is a request for a change
today, and nothing here authorises deleting or moving a file in your repository. The deletion is
the Captain's, every time — that is part of the rule, not a courtesy.

**Subject:** `project/audits/audit-levinsohn-method.md` (793 lines, last commit `a9d0665`
2026-09-09, currently modified in your working tree).

**The short answer: the file is already a rolling file, and it says so.** Lines 18-24 declare
exactly what the rule asks for — *"a rolling record, one per subsystem, updated in place and
current by construction. Rewrite figures rather than appending"*, and *"Nothing here is a ruling.
Rulings go to `CHANGELOG.md`."* The eight-day death does not touch it. What follows is about four
things that are not lifecycle, and one place where you should **not** act yet.

---

## 1. What is ruled, what is built, and what is only proposed

Read this table before acting on anything below. Most of the confusion in this area comes from
treating a proposal as a decision.

| Piece | State |
|---|---|
| `plans-are-temporary` — a working document dies at eight days; a **ruling** is permanent until overruled; **accumulating versus rolling** is the line that decides which files the death touches; **the deletion is the Captain's, every time** | **Ruled and shipped** 2026-09-08 in `data/ai-rules.yaml`, rendered into your `docs/ai-context/sp/rules.md`. You already have the text |
| A ticked box states **how it is known** — a test id, a command and its result, a file and a line | **Ruled** (D2, "Yes") and **built**: `tests/test_ticked_boxes_carry_evidence.py`, 4 tests. It scans `project/plans/*.md` only, and asserts the scan read something so it cannot pass by reading nothing |
| Where the checklist obligation lives | **Ruled** (D1, "B — this feels helm to me"): the lifecycle stays in `data/ai-rules.yaml`, the checklist obligation goes to the shared discipline so it reaches Human at the Helm. The discipline text is in flight |
| **`project/audits/` goes away entirely** | **Ruled** (D3, "Yes, it goes away") and **not built.** Measured at **21 files** in the engine — a catalog entry, a shipped template, a whole shipped document and its mirror, two audit skills, three disciplines (one Helm-shared), the `file-organisation` rule, two tests, four docs. It is its own piece of work and must land in one pass |
| `project/rolling/` and `project/scratchpad/` directories | **Ruled against** (D4). `tmp/` already is the scratchpad, declaratively. `TODO.md` was deliberately left where it is — 27 files reference `project/TODO.md`, including the file catalog, five shipped templates, six tests and a machine-wide skill, and `sp init` creates that path |

The ruled layout is three places, and none of them is new:

| | holds | lifecycle |
|---|---|---|
| `project/` top level | `TODO.md`, `HANDOFF.md`, `RELEASE_CHECKLIST.md` | rolling — update, never delete by age |
| `project/plans/` | working documents, one per piece of work | accumulating — eight days |
| `tmp/` | throwaway | untracked; delete freely |

Source: `project/plans/design-one-working-document.md` in this repository, §3 and §5. It is itself
a working document and will be deleted once its checklist lands, so quote what you need now rather
than citing it later.

---

## 2. Do not move the file yet

**`project/audits/` is ruled out of existence but still standing, and two documents currently give
you opposite instructions.** `disciplines/project-tracking.md` — which you have installed — still
says a rolling per-subsystem audit lives at `project/audits/audit-{subsystem}.md`, which is exactly
where your file is. The design that retires the directory names reconciling that discipline as an
open checklist item.

So: **the shipped discipline you have is not yet wrong, and the ruling that will make it wrong is
not yet built.** Moving the file now means moving it twice and breaking every reference in the
meantime. `grep -rn "audit-levinsohn-method" .` in your tree will tell you what that costs.

The one thing worth knowing in advance: a rolling per-subsystem record is a **rolling** file, so
when the directory does go, its destination is the `project/` top level rather than
`project/plans/`. Where exactly a per-subsystem rolling audit lands is not declared anywhere yet —
that is a gap in the design, not something to infer from the table above.

**A second consequence, if you ever do put it under `project/plans/`:** the ticked-box guard scans
that directory. Every `- [x]` in the file would then have to carry its evidence after the dash.

---

## 3. The durable content is trapped in a file that is rewritten in place

This is the real adaptation, and it is the one the rule exists for.

Your header says *"Nothing here is a ruling"*, and for the measurements that is true. But
**§"Corrections this file records" (lines 677-758) is record, not measurement** — and a file whose
own instruction is *"Rewrite figures rather than appending"* will eventually rewrite it away.

What is in there that must outlive the file:

| Content | Lines | Why it is record |
|---|---|---|
| The withdrawn fabrication finding — `genre_markers` were in the window request all along; the model was copying its input | 679-704 | It was *"the headline finding of the pass"* and was reported in conversation. Deleting the withdrawal makes a past statement unfalsifiable. `one-design`: the record is corrected by adding alongside, dated, never by rewording |
| **"The scripts glob a directory and must not — this is the second time that has cost a set of figures"** | 736-737 | This is a **ruling** in the strict sense: permanent until overruled, and it binds future work. It currently lives only inside a rolling measurement file |
| Every distributional figure is not re-derivable — the 2026-09-08 sample was deleted on the Captain's order | 712-718 | The *withdrawal* is record. The figures themselves are stale entries — see §4 |
| The framing correction, and the four claims withdrawn with it | 739-758 | Same as the first row: previously reported, so the withdrawal has to survive |
| `tmp/claim_instances.py`'s three defects | 720-733 | Record of why a 611 KB report was withdrawn |

**Where it goes is where you say it goes, and your own records disagree with each other.** Line 24
routes rulings to `CHANGELOG.md`. But `project/rulings.md` exists, describes itself as *"decisions
the Captain actually made, in his words, quoted"*, and imposes a stricter admission test — *"an
entry needs the Captain's words quoted and a date. No quote, no entry."*

That test is the crux. Most of the content above is **not** a quoted decision — it is a finding, a
withdrawal, or a rule an AI derived from a failure. By `rulings.md`'s own entry rule, it does not
belong there. The engine's rule names the CHANGELOG *"or in this file when it binds future work"*,
where "this file" is the rules file — and `docs/ai-context/project/rules.md` is a project's own
local rules file, which is where *"State the invariant before you read the number"* already
correctly lives.

So the natural split, offered as a reading and not a ruling:

- **binds future work** → `docs/ai-context/project/rules.md`, beside the invariant rule. "The
  scripts glob a directory and must not" is this, and it has now cost figures twice.
- **a quoted decision** → `project/rulings.md`, with the quote and the date.
- **a correction to something previously reported** → `CHANGELOG.md`, dated, added alongside.
- **everything else** → stays in the rolling file and is pruned as it rots.

A project may declare its own durable home; `plans-are-temporary` does not forbid it. What it does
forbid is having none, or having two that disagree. Line 24 and `project/rulings.md` currently
disagree, and that is the one thing worth settling before the next rewrite of the file.

---

## 4. Stale entries versus the record — the rule's own words

`plans-are-temporary` on a rolling file: *"its age is a reason to update it rather than to delete
it. Prune its stale entries instead: a task list item from three weeks ago rots exactly like a
whole document does."*

Your file flags its own stale entries better than most: lines 712-718 say every distributional
figure was measured on a sample that no longer exists, *"retained above, marked, because deleting a
recorded measurement would be worse than marking it; it must not be quoted as current."*

**That instinct and the rule point in opposite directions, and both are half right.** The
resolution the rule implies:

- the **figures** are stale entries in a rolling file, so they are pruned — a number nobody can
  re-derive is exactly the content that rots, and a reader who finds it marked still quotes it
- the **withdrawal** is record, so it survives — in the CHANGELOG, dated

Pruning a figure while keeping "this figure was measured on a deleted sample and withdrawn" loses
nothing and stops the number circulating. §2.5 already names the cheapest fix — the audit-3 figures
are free to re-derive, and they are the one favourable result the file had.

---

## 5. The ten flagged items want `=>` slots

§"Items flagged for the Captain's judgement" (lines 762-793) is ten open decisions inside a
measurement record. Two things the workflow asks of them:

**Ask so the answer becomes quotable.** `disciplines/surface-decisions.md`: pose the question, then
leave a line containing only `=>` for the answer. Never checkboxes, never underline blanks —
neither is fillable by someone editing the file. **Once the Captain has written after a `=>`, that
text is the ruling: quote it, never reword it.** That is how a decision becomes a `rulings.md` entry
that satisfies the no-quote-no-entry test, instead of an AI's paraphrase of what he meant.

**A well-formed request states what each option does and what it costs.** Several of the ten are
already close — item 1 says *"this is the finding that most limits what the run can be used to
show"*, which is decision-shaped. Item 9 names itself a *"design question, not a defect"*, which is
the right label and would be better as a question with options.

Whether they stay in this file or move to `project/open-decisions.md` or `project/questions.md` is
yours — you have both, and this file's header says it is a measurement record. The rule cares that
a decision is asked once, in one place, in a form whose answer is quotable.

---

## 6. Once he rules, the last phase is a checklist that carries its evidence

Ruled D2, and guarded here. A ticked box states **how it is known**:

```markdown
- [x] lint rejects the old key — tests/test_resource_key_migration.py::test_a_pipeline_using_it_does_not_lint
- [x] consumer pipelines migrated — 5 keys across 2 repos, all 7 lint clean (2026-09-08)
- [ ] CHANGELOG entry
```

Not *done* — a test id, a command and its result, a file and a line. The reason it was ruled in is
specific and it applies directly to your repository: on 2026-09-08 a session here reported a thread
complete, and hours later found a pipeline in `discourse-flow` broken by the very defect that
thread had addressed, inside the scope it had called done. A test suite cannot catch that, because
it was in another repository. **A checklist is the only guard over the parts no suite covers** —
documentation, consumer repositories, replies owed to other projects.

The guard is honest about its limit: it checks that something evidence-shaped is present, never
that the evidence is true. A determined box-ticker defeats it in one line. It was still ruled in,
because the usual failure is not deceit — it is finishing three quarters and losing track.

---

## 7. Your other audit files are a different case

The design draws one line your directory straddles. A **rolling per-subsystem** audit is exempt
from the eight-day death. A **dated, per-run** audit record is *"a working document like any
other"*, so it dies at eight days.

By the dates in the filenames — not commit dates; re-derive with
`git log -1 --format=%ad --date=short -- <file>`:

| File | Filename date | Past eight days |
|---|---|---|
| `audit-book-discourse-20260425-PHM.md` | 2026-04-25 | yes |
| `audit-book-discourse-20260813-1JN.md` | 2026-08-13 | yes |
| `audit-book-discourse-20260906-MRK-PHM.md` | 2026-09-06 | no |
| `audit-book-discourse-flow-20260906-1010-PHM.md` | 2026-09-06 | no |
| `audit-book-discourse-flow-20260906-1027-MRK.md` | 2026-09-06 | no |
| `audit-book-discourse-flow-20260908-1032-PHM.md` | 2026-09-08 | no |

The rule's instruction for the two past the window is *"either way the file goes, unread"* —
explicitly **do not sift**, on the argument that settles it: *"if it's still valuable, neither I
nor an LLM can distinguish the valuable content from anything else."* Git keeps every deleted file.

**And the deletion is the Captain's, every time.** An AI lists what is past eight days and asks; it
never deletes unasked, and never treats the rule as standing authorization. We are listing, not
asking — this is your repository.

Also relevant: `disciplines/project-tracking.md` describes a per-artifact record as *"retained as
record"*, which directly contradicts the eight-day rule. That contradiction is ours to fix and is
on the D3 checklist.

---

## 8. What is already right, and the workflow does not touch

Said plainly because a document that only lists faults reads as a verdict, and this one is not.

- **It declares its own lifecycle** (lines 18-24). Most files in either repository do not, which is
  precisely why the eight-day rule had to be blunt.
- **It names its authority** — `docs/levinsohn-reference.md` §9, Levinsohn 2006 — and marks what is
  not traceable there as yours. That is `design-authority` done properly.
- **It records what it did not examine** (lines 661-673), including *"212 of the 301 manifest rows"*
  and the correction that an earlier claim about all 302 *"was an overstatement of what I had
  checked."* That section is worth more than most audits' findings.
- **It is organised by the three claims of the model rather than by what was easy to measure**, and
  it says so, with a note on why an earlier framing was wrong.
- **It corrects itself in place, dated, without deleting what it corrected.** That is the behaviour
  `one-design` asks for and it is rarer than it should be.

None of §3-§6 is a criticism of the analysis. They are about where four kinds of content live once
the file is rewritten, which is a filing question the analysis cannot answer for itself.

---

## 9. Questions that are yours

1. **Which is your durable home for a ruling — `CHANGELOG.md` (line 24) or `project/rulings.md`?**
   The two currently disagree, and `rulings.md`'s no-quote-no-entry test excludes most of what
   §"Corrections this file records" holds.

   =>

2. **Does "the scripts glob a directory and must not" become a rule in
   `docs/ai-context/project/rules.md`?** It has cost figures twice, and
   `plugins.run_sample.one_generation()` already exists to refuse a mixed sample.

   =>

3. **Do the ten flagged items stay in this file, or move to `open-decisions.md` / `questions.md`?**
   Either way they want `=>` slots rather than prose.

   =>

4. **Are the non-re-derivable figures pruned, or kept marked?** The rule says prune the entry and
   keep the withdrawal; your line 716-718 says the opposite, with a reason.

   =>

Nothing here blocks you. If you would rather leave the file exactly as it is until
`project/audits/` actually goes away, that is a defensible reading of §2 — the discipline you have
installed still points at the path you are using.
