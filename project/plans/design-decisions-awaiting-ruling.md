# Decisions awaiting the Captain's ruling

**Status:** open — twelve decisions, none answered. Written 2026-09-02 to collect them in one
place. #169 #217 #201 #212 #228 #230

**Answer inline after each `=>`.**

Every decision below blocks work that is otherwise ready to start. Each one is written to be read
cold: what the thing is, why a choice is needed, what changes depending on the answer, and a `=>`
slot for your ruling.

**Nothing here is decided.** Where I have a recommendation it is labelled as one.

**This file is a ruling sheet, not where the decisions live.** A decision belongs in the design
document or plan it governs, and that is where each answer gets written once it is given — the
last table in this file names the destination for every one. When all nine have been written back,
this file has done its job and goes; leaving it in place would create a second copy of nine
decisions, drifting from the documents that actually govern them.

---

## Before the decisions: two documents that approved opposite things

This needs explaining before decisions 5, 6 and 7 make sense, because it is the reason three of
them exist.

Issue #169 is about teaching the engine to compare verse references — to answer "is Mark 9:50
before Mark 10:1?" and "does Mark 1:7 fall inside Mark 1:1-10?" The engine cannot do either
today.

That work was designed twice, on the same day, in two documents you approved:

| document | what it says it governs |
|---|---|
| `project/plans/design-verse-range-operations.md` | the data model — what a verse range *is* and how comparisons behave |
| `project/plans/plan-verse-range-set-ops.md` | the implementation — function names, signatures, which files change |

The split was deliberate and sensible: one document for *what*, one for *how*. But they were
written far enough apart in detail that they now contradict each other in three places, and both
carry your approval, so an implementer has no way to tell which to follow.

**Contradiction 1 — comparing references from two different books.**

- The data-model document records your ruling: comparing across books answers "no". `overlaps`
  returns false, `intersect` returns nothing. **It does not fail.**
- The implementation document says the opposite: comparing across books **raises an error**.

**Contradiction 2 — whether the functions accept lists.**

- The data-model document records your ruling that a function takes either one reference or many,
  because — your words — *"iterating sets in caller code is the problem being solved."* So
  `overlaps("Mark 1:1-10", scenes)` works whether `scenes` is one reference or fifty.
- The implementation document's function signatures take exactly two references. A caller with
  fifty scenes writes the loop themselves.

This is the consequential one. The whole reason the discourse-flow project wants these functions
is that they are currently writing those loops by hand, in ten different places. A two-reference
signature leaves that problem exactly where it is.

**Contradiction 3 — how many functions there are.**

- The data-model document records your ruling that there are six operations, including one that
  tests whether two ranges sit next to each other and one that counts verses.
- The implementation document's own notes agree there are six — but its function list, further up
  the same file, still shows four. The document is stale against itself.

**What I recommend:** reconcile the two into one document before any code is written. This is not
a redesign — your rulings already settle most of it. It is deciding, in three places, which of two
approved sentences survives, and deleting the other. Decisions 5, 6 and 7 below are those three
places plus one related question.

**Why this matters beyond #169:** the reason two documents could disagree for two weeks without
anyone noticing is that nothing compares them. That is the same shape as the defects found this
week in the prompt renderer and the reference parser — two things that agree until they quietly
do not.

---

## 1. When a rule is shortened to point at its test, what happens where the test does not exist?

**What this is about.** The engine's rules file (`docs/ai-context/sp/rules.md`) is 3,828 words and
is read at the start of every AI session. Issue #230 found that reading rules is a weak way to
enforce them — they decay over a long session — while a test enforces one permanently. Six rules
already have tests.

The proposal in #230 is to shorten every rule that has a test down to one sentence plus the name
of the test, on the grounds that the test is the real enforcement and the paragraph is a second
copy of it. That cuts the reading burden, which is the thing you asked to fix.

**Why a choice is needed.** Five of those rules files are also shipped to Human at the Helm and
installed into other people's projects. A shortened rule reads:

> **Docstrings say what the code does, not why.** Enforced by
> `tests/test_docstrings_say_what_not_why.py`.

In this repository that is genuinely better — it is shorter and it says where the truth lives. In
a project that has no such test, the pointer names a file that is not there. The rule becomes
*less* enforced than the paragraph it replaced, and a reader who goes looking finds nothing.

This matters next week specifically: you are about to mentor programmers on Paratext Copilot,
which is TypeScript. They will read the shared files, not this repository's.

**Options.**

1. **Shorten only in this repository**; shipped copies keep the full paragraph. Two versions of
   each rule to maintain, which is the duplication the change was meant to remove.
2. **Shorten everywhere, and state the rule so it stands alone** — one sentence that is complete
   in itself, with the test named as a footnote rather than as the substance. Works in both
   places; requires each sentence to be written carefully.
3. **Shorten everywhere and let the pointer dangle** where the test is absent. Cheapest, and it
   ships a broken reference to your mentees.
4. Something else.

**My recommendation: option 2.** It is the only one that removes the duplication without shipping
a dead pointer, and the constraint it imposes — every rule must be complete in one sentence — is
a good discipline in its own right.

=>

---

## 2. Are six new tests the whole of the rules-enforcement work this release, or a first batch?

**What this is about.** Issue #230 catalogued all 35 rules and found 13 that no test checks but
easily could. The release plan schedules six of them:

| rule | what the test would check |
|---|---|
| use lxml for XML | no `import xml.etree` in the plugins directory. **A file breaks this today.** |
| work on the dev branch | the branch is not `main` before a commit |
| output is a draft | the words "production ready", "approved", "suitable for use" appear nowhere |
| reference data is JSON, not YAML | no YAML file holds verse-shaped keys, which PyYAML silently reads as numbers |
| every AI step names its source text | no step asks a model about a passage without the text in front of it |
| prompt bodies use flat names | no dotted name in a prompt body, since nothing can ever fill it |

The other seven have no date.

**Why a choice is needed.** Six is a guess at what fits. If you want the whole thirteen this
release, that is a larger but still bounded piece of work and it finishes the job. If six is
right, the remaining seven need to be either scheduled later or explicitly parked, or they will
sit unowned.

**Options.** Six as listed / all thirteen / a different subset you name.

**My recommendation: six as listed**, with the other seven staying in #230. The one I would move
up if you want a seventh is "every AI step names its source text" — it is already in the six, and
it is the rule that stops a model answering from memory instead of from the passage, which is the
failure that matters most in this domain.

=>

---

## 3. How is a licence recorded when one download holds many works under different licences?

**What this is about.** Issue #217 asks the engine to fetch freely-licensed source texts instead
of you placing them by hand. The catalogue in `awesome-biblical-data/resources.json` already
describes 70 resources, including how to acquire each one and what licence it carries. Issue #212
asks the registry to record not just where a text is but what may be done with it. One catalogue
answers both.

**Why a choice is needed.** The catalogue records one licence per resource, and for most that is
true — Abbott-Smith is public domain, papyri.info is CC BY 3.0. But the Perseus Digital Library's
entry reads `"Various CC"`: it is one download containing many works, each under its own terms.
BDAG is the opposite problem in a useful way — it is marked `Commercial`, print and Logos only,
so the engine must refuse to fetch it at all.

If the code assumes one licence per resource, Perseus will be recorded under a licence that is not
quite anyone's, and a downstream question of "may we publish an extract from this?" gets a
confident wrong answer.

**Options.**

1. **One licence per resource, and Perseus-style entries are flagged rather than resolved** — the
   registry records "varies, check per work" and refuses to answer the question automatically.
2. **Licence per work**, which means the catalogue grows a level of structure it does not have,
   and someone has to fill it in for Perseus.
3. **Fetch only resources with a single clear licence** for now; leave the varied ones to manual
   placement.
4. Something else.

**My recommendation: option 1.** It is honest about what is known, it does not invent data, and
refusing to answer is the right behaviour for a licensing question. Option 2 is the correct
long-term shape but it is work in someone else's repository.

=>

---

## 4. Where does the check for Python-specific wording in shared files live?

**What this is about.** Eleven files are shared between this repository and Human at the Helm —
five methodology documents, the drift-patterns catalogue, and five skills. This repository is
upstream; a script copies changes across and a test fails when the two sides differ unexpectedly.

An existing test already checks that shared files carry no engine vocabulary — no product name, no
CLI name. But it does not check for build-tool assumptions, and those have got in: across the
shared files there are two mentions of `pytest`, two of `ruff`, one of `hatch`, one of `python` —
alongside three of `tsc` and two of `npm`. A TypeScript reader meets Python tooling in week one.

**Why a choice is needed.** A test in this repository governs what is *sent*. Human at the Helm
also has its own material that this repository never sees and cannot check.

**Options.**

1. **Here only.** Simple, one test, and it covers everything this repository ships. Helm's own
   files stay unchecked.
2. **Both sides**, each with its own test. Complete, and it is a second test to keep in step.
3. **Here, plus widen the existing shared-file test** rather than adding a new one, so there is
   one check on portability rather than two.

**My recommendation: option 3.** There is already a test asking "is this file fit to ship to
another project?" — build-tool assumptions are the same question, and a second test beside it
would be two encodings of one idea.

=>

---

## 5. Comparing references from two different books: answer "no", or fail?

This is contradiction 1 from the top of this document.

**Concrete example.** A caller asks whether `Mark 1:1-10` overlaps `John 3:16`.

- **Answer "no".** `overlaps` returns false. The caller carries on. Your recorded ruling.
- **Fail.** The call raises an error, and the caller must check the books match before asking.
  What the implementation document says.

**What each costs.** Answering "no" is the truthful answer to the literal question, and it makes
the function safe to call across a mixed list. Failing catches a caller who has muddled two books
and would otherwise get a quiet false — which, in a pipeline that sorts pericopes, could hide a
real mistake.

**My recommendation: answer "no", as you already ruled.** The functions are meant to be called
across lists, and a list spanning two books is a normal thing to hold, not an error.

=>

---

## 6. Do the comparison functions take two references, or accept lists?

This is contradiction 2, and the one that decides whether the feature is worth building.

**Concrete example.** A caller has one window and fifty pericopes and wants to know whether the
window touches any of them.

Accepting lists:

```
verse_range_overlaps(window, pericopes)      -> True
```

Two references only:

```
any(verse_range_overlaps(window, p) for p in pericopes)
```

**What each costs.** Two references is simpler to write and to test. Accepting lists is what you
ruled, and the reason you gave was that the loop in caller code is the problem being solved — a
loop that currently exists ten times in one consumer project, in seven files, with four different
behaviours between them.

**My recommendation: accept lists, as you already ruled.** With the two-reference signature the
consumer keeps writing the loops, and the ten functions this work exists to delete stay where they
are.

=>

---

## 7. What should happen to a reference with extra text after it?

**What this is about.** `parse_bible_reference` is the engine's most-used reference parser. It
tries four patterns in order and only the last is anchored to the end of the string, so an earlier
pattern can match the *beginning* of a reference and silently discard the rest. Measured:

```
'1JN 2:5b-6'             ->  1 John 2:5      (the "-6" is gone: two verses became one)
'PHM 1:19b-20'           ->  Philemon 1:19   (same)
'MRK 1:14 and then some' ->  Mark 1:14
'MRK 1:14;16'            ->  Mark 1:14
'MRK 1:14+MRK 2:1'       ->  Mark 1:14
```

Note the first two carefully. `1JN 2:5-6` parses correctly and gives verses 5 to 6. Adding the
sub-verse letter `b` does not merely lose the letter — **it drops the end of the range**, so the
result is one verse instead of two, and nothing in the returned value says anything was lost.

`1JN 2:5b-6` and `PHM 1:19b-20` are both real references in the discourse-flow corpus, and this
parser runs in four of their pipelines.

**Why a choice is needed.** This is a contract question, not just a bug: something has to happen
when the input is not a clean reference. The reporting project offered three possibilities and
said any of them is safe for them.

**Options.**

1. **Reject it.** `1JN 2:5b-6` raises an error naming what it could not parse. Loud, and it is
   what the engine's own stated philosophy calls for — the overview says the engine "prefers a
   loud error to a plausible result."
2. **Parse the range and drop only the letter, visibly** — return verses 5 to 6, with a field on
   the result recording that a sub-verse letter was discarded. Preserves the caller's range,
   admits the loss.
3. **Parse it and carry the letter**, which means sub-verse addressing becomes a thing the engine
   supports, with everything downstream needing to understand it.

**This one changes work outside this repository.** Mid-verse boundaries are real in discourse-flow
— a pericope can open at `1:19b` — and they have an open question about whether to represent those
as word identifiers instead. Your answer here decides theirs.

**My recommendation: option 2.** It fixes the actual damage (a silently narrowed range), it does
not commit the engine to sub-verse addressing, and the discarded letter is visible rather than
inferred. Option 1 is more in keeping with the engine's philosophy but would break their pipelines
on real data the day it ships.

=>

---

## 8. When asking whether a set of ranges contains another, do gaps count?

**What this is about.** Only live if decision 6 goes toward lists. If a function can be asked
"does this collection of ranges contain that range?", there are two reasonable meanings.

**Concrete example.** Does `[Mark 1:1-5, Mark 1:8-10]` contain `Mark 1:1-10`?

- **Outer bounds only:** yes. The collection spans 1:1 to 1:10, and 1:1-10 sits inside that span.
- **Every verse:** no. Verses 6 and 7 are in neither range.

**What each costs.** Outer bounds is cheaper and is usually what someone eyeballing a range wants.
Every-verse is the answer that is actually true, and it is the one that would catch a gap in
pericope coverage — which is one of the things the consumer project uses these comparisons for.

**My recommendation: every verse.** The purpose of the function in practice is finding gaps, and
outer-bounds containment cannot find them by construction.

=>

---

## 9. Is there one written form a reference should be stored in?

**What this is about.** The discourse-flow project stores `"MRK 1:14"` in identifiers and
`"1:14"` in the fields prompts read, and says that mismatch is why some of their functions take
one shape and some the other. The engine's parser accepts the first and rejects the second:

```
parse_bible_reference('MRK 1:14')  ->  parses
parse_bible_reference('1:14')      ->  ValueError: Could not parse Bible reference '1:14'
```

A bare `1:14` has no book, so the parser has nothing to work with. That is defensible in
isolation, but it means every caller holding chapter-and-verse without a book has to carry the
book separately and join them back together — which is what their seven files each do differently.

**Why a choice is needed.** If the engine names one canonical stored form, consumers can converge
on it and the comparison functions have exactly one input shape to accept. If it does not, every
project keeps its own convention and the functions must be liberal about what they take.

**Options.**

1. **Name one form** — always book, chapter and verse together — and say so in the documentation.
2. **Accept a book supplied separately**, so `1:14` parses when a book is passed alongside it.
3. **Leave it to each project**, and have the comparison functions accept both shapes.

This touches issue #218, "a passage reference has no data structure until a versification is
named", which is not otherwise part of this release. I would not settle #218 here, but decision 9
should not contradict it.

**My recommendation: option 1**, and say it plainly in the language documentation. One form is the
whole point of a canonical form; option 3 pushes the ambiguity into every caller.

=>

---

## 10, 11, 12. Three rules recovered from the deleted memory files

These three came out of the 81 memory files deleted on 2026-08-22 and committed on 2026-09-02.
The audit classified all three as **general-rule candidates, not yet ruled**, and they have never
been anywhere a session would read them. Their text below is recovered verbatim from
`e846f4d^`.

**Why they need a home now.** Two came from `paratext-copilot` and one from
`paratext-biblical-terms-extension` — the two projects the mentoring starts on. Both are
TypeScript and neither will ever run `sp init`, so `data/ai-rules.yaml` cannot reach them. The
shared Human at the Helm disciplines can, and are what a mentee reads in week one.

**The source to edit is `src/llmflow/templates/sp/disciplines/`** in this repository, not
`~/.sp/disciplines/` and not Helm's copy — those are installed copies, and the next update
overwrites anything written to them. After the edit, `tools/sync_helm.py --apply` propagates it,
which needs your word as a separate act because it writes into another repository.

**A consequence to note for all three:** the disciplines reach every project, sp or not, so an
sp project gets the rule twice if it is *also* added to `data/ai-rules.yaml`. My reading is that
the discipline is the right single home and `ai-rules.yaml` should not duplicate it — but that is
part of each ruling.

### 10. Questions are not instructions

Recovered text: *"Do not act on diagnostic questions. 'Is that clear?' 'Do we need X?' 'Does this
cover Y?' are questions — answer them, then wait."* With: *"Auto mode is not blanket authorization
for scope the user did not request."* And: if the answer reveals a gap, name it and stop; do not
fix it unless asked.

**Proposed home: `disciplines/surface-decisions.md`**, as a new section. That file already governs
*when to stop and ask*; this is its mirror — not treating a question as a go-ahead. The file's own
framing is *"one crisp ask, halt"*, and this says a question from you is not the opposite of a
halt.

**Options.** Add it there / add it to `design-authority.md` instead / a new discipline file of its
own / do not add it.

**My recommendation: `surface-decisions.md`.** The recovered file recorded that you had corrected
this behaviour explicitly, and the failure it names — answering a question about the README, then
editing and pushing it — is the same shape as offloading a decision.

=>

### 11. No "junior", no status talk in team-visible text

Recovered text: *"Don't use the word 'junior' (or similar diminutives) when referring to team
members in issue comments or any public-facing text. Also avoid 'status talk' — summary phrases
like 'in progress', 'tracked separately', or process-oriented filler. Present technical facts
directly."*

**Proposed home: `disciplines/github-authority.md`**, as a new section on the language of
team-visible text. That file already governs what an AI may write on GitHub; this governs how.

**Worth knowing while you rule:** Helm's disciplines carry **no** equivalent of
`no-stakeholder-speculation` — the rule against naming customers and speculating about their
politics. That rule lives only in `data/ai-rules.yaml`, so it reaches sp projects and nothing
else. Both rules are about text other people read. Whether to state them together in one section
is a larger question than this decision, and I am not folding it in unasked.

**Options.** Add to `github-authority.md` / a new discipline on team-visible writing, carrying
both this and stakeholder speculation / do not add it.

**My recommendation: add to `github-authority.md` now**, and treat the stakeholder-speculation gap
as its own decision later. One rule with a home beats two waiting on a bigger design.

=>

### 12. Design documents must teach the tradeoffs

Recovered text, quoting you directly: *"Design documents should clearly explain engineering
tradeoffs. That's how I can learn enough to make good decisions and become better over time,
instead of accepting whatever stupid non-aligned approach some LLM does. If it's not educating me
to decide wisely, it's not worth writing at all."*

The recovered file also carried four specific applications: explain the underlying concept before
evaluating options; name the mechanism that makes an option costly; include the concrete
constraint that rules something out; and give the reasoning, not just a recommendation, so you can
override it with domain knowledge the AI does not have.

**This one has no obvious home**, which is why I flagged it as needing your call. `rules.md` has
`transfer-the-expertise`, but that is about teaching you a *dataset*, not about how a design
document is written. Nothing covers design documents.

**Options.**

1. **`disciplines/design-authority.md`** — that file establishes that decisions are yours; this
   says a document must equip you to make them. Same axis, and it is the closest existing fit.
2. **`disciplines/surface-decisions.md`** — it already contains *"If you don't give the
   information the Captain needs to decide, you haven't got a well-formed request for a
   decision"*, which is this rule applied to a single ask rather than to a document.
3. **A new discipline** of its own, since it governs a whole document class.
4. **`data/ai-rules.yaml`** as a general rule, accepting that it then misses the two TypeScript
   projects.

**My recommendation: option 2, `surface-decisions.md`.** It is not a new principle there — it is
the same principle at document scale, and the existing sentence is one line away from saying it.
Option 1 is defensible; a new file spends a whole discipline on what is a paragraph.

=>

---

## What each decision blocks, and where the answer gets written

| # | blocks | the ruling is written back into |
|---|---|---|
| 1 | shortening the rules file; the shared-file work before mentoring starts | `data/ai-rules.yaml` — the single source the rules file is generated from — and #230 |
| 2 | knowing when the rules-enforcement work is finished | #230, and the release plan |
| 3 | the resource-fetching code | `design-resource-provisioning.md` and `design-source-licensing.md`; #212 |
| 4 | the shared-file portability check | `design-helm-parity.md`, and the test it names |
| 5, 6, 8 | any code for #169 | `design-verse-range-operations.md` and `plan-verse-range-set-ops.md`, **reconciled into one** — these three rulings are what resolves the contradictions |
| 7 | the parser fix here, **and** discourse-flow's decision on mid-verse boundaries | `docs/ai-context/sp/passage-references.md`, which is the documented contract for what parses |
| 9 | the input shape the #169 functions accept | `docs/ai-context/sp/passage-references.md`; must not contradict #218 |
| 10, 11, 12 | three recovered rules reaching any session at all, including the mentees' | `src/llmflow/templates/sp/disciplines/` — the source, not the installed copies — then `tools/sync_helm.py --apply` as a separate act, because it writes to another repository |

Two files above are under `docs/ai-context/`, which an AI session may not edit without your
per-file permission in the conversation. Decisions 7 and 9 therefore need that permission as well
as the ruling, or they need someone else to make the edit.

**Time-sensitive:** decision 1, because mentoring starts next week and the shared files are what
mentees read. Decision 7, because another project is waiting on it and is currently feeding
silently narrowed references to a model.
