# Plan — release 0.2.1.26: enforce the rules, fetch the resources, compare the references

**Status:** approved in conversation 2026-09-01 — scope ruled, not yet started. #230 #217 #201
#212 #227 #228 #226 #153 #169

Scope for the next release, ruled by the Captain on 2026-09-01. The release contained one
substantive change and no engine capability at all, so the scope was open.

**The Captain's framing:** *"we need to choose scope for the next release. I want to at LEAST
address the latest issue on ai context, making it actionable with sufficient guards. and I would
also like to start adding more sp engine support for specific awesome bible resources, starting
with the ones that discourse flow, discourse flow hebrew, and ears to hear are already using.
after that, semlex greek and lexicon support is a high priority."*

**Version: 0.2.1.26**, ruled 2026-09-01. #153 (versioning policy) stays open and is not settled
by this choice.

**Decisions are not recorded here.** Nine remain open and they are collected for ruling in
`design-decisions-awaiting-ruling.md`, which also names the document each answer gets written back
into. This plan states scope; it does not hold decisions.

**A note on names.** An earlier draft of this plan labelled the work "Track A", "B3", "D7" and so
on, and then used those labels as though they were shared vocabulary — so following the plan meant
learning an invented private language for the project's own work. Rewritten 2026-09-02 at the
Captain's direction to name everything by its issue number and in plain words. *"terminology
capture drift drift drift."*

---

## 1. What the release already contains

Since `v0.2.1.25` (2026-08-29), four commits, three sharing one subject line:

| | |
|---|---|
| #225 | rules cited by id, not by position — renderer, nine citations, two new tests |
| the handoff skill | the boundary between `HANDOFF.md` and the task list, shipped by `sp init`, resynced to Human at the Helm |
| plan documents | #226's design, #227's rulings, #225's plan — record, not shipped behaviour |

Two entries under *Unreleased*. Nothing in the runner, linter, scripture step or plugins.

---

## 2. Making the rules enforceable instead of instructional — #230

#230 measured the AI context at ~27,000 words read at the start of every session, and concluded
that reading is a weak way to enforce a rule: it sits at the top of the context while the work
happens hundreds of turns later. It catalogued all 35 rules — 6 already have tests, 13 could
easily have one, 12 can never be checked and must genuinely be held in attention.

**Ruled: all four pieces below.**

### 2.1 Write tests for six rules that have none

| rule | what the test checks |
|---|---|
| use lxml for XML | no `import xml.etree` under `src/llmflow/plugins/`. **`plugins/xml_entry_to_base_json.py:1` breaks this today** — fix it with the test, not before; it is #230's motivating evidence |
| work on the dev branch | the branch is not `main` before a commit |
| output is a draft | the phrases "production ready", "approved", "suitable for use" appear nowhere |
| reference data is JSON | no YAML file holds verse-shaped keys, which PyYAML silently reads as base-60 integers |
| every AI step names its source text | no `type: llm` step asks about a passage without the text among its inputs |
| prompt bodies use flat names | no dotted name in a prompt body, since nothing can ever substitute one — see §6.1 |

A seventh, added 2026-09-01: **the reference parser must not silently narrow** — anchor its
patterns and test for trailing content. See §6.2.

The other seven checkable rules stay in #230 with no date. Whether six is the whole batch is
decision 2 on the ruling sheet.

### 2.2 Shorten every rule that has a test

A rule with a test is stated twice — as a paragraph and as the test — and the paragraph is the
copy that goes stale. Shortening each to a sentence naming its test is where the 3,828-word rules
file actually shrinks.

**Blocked on decision 1**, because five of these files ship to other projects where the test does
not exist and the pointer would name nothing.

### 2.3 Separate the rules no test can check

Twelve rules require attention and can never be verified. Burying them among twenty-three that a
test could catch spends the model's attention on the wrong ones. A short, separate list — and the
only list the Captain would still need to hold himself.

**The highest-value piece for the mentoring in §2.4**, because it is the half that ports to any
language.

### 2.4 Make the shared methodology files fit for non-Python projects

Added 2026-09-01, after: *"I will soon start mentoring programmers who work on paratext copilot
and the biblical terms extension, so the helm ai context will be particularly important starting
next week."*

Paratext Copilot is TypeScript — `package.json`, `tsconfig.json`, npm. Mentees read the shared
Human at the Helm files, not this repository's. Measured across the eleven shared files: `tsc` ×3
and `npm` ×2, but also `ruff` ×2, `pytest` ×2, `hatch` ×1, `python` ×1. The existing portability
test checks for product and CLI vocabulary, not build-tool assumptions, so nothing catches this.

Audit the eleven files, and check for it from then on. **Where that check lives is decision 4.**

---

## 3. Fetching source texts and data, from the catalogue — #217, #201, #212

**Ruled 2026-09-01: the engine gains mechanism, not knowledge of particular resources.** It learns
to read the catalogue, fetch, validate versions and check licences, and to expose generic
`include:` families. Anything specific to one resource stays in `awesome-biblical-data`, which is
where #226 put that layer.

### What the three consumer projects actually use

Measured by reference count across each project's pipelines, plugins and prompts:

| resource | discourse-flow | discourse-flow-hebrew | ears-to-hear | engine support today |
|---|---|---|---|---|
| Levinsohn discourse features | 199 | 88 | 4,031 | `include: [discourse]` — built |
| Macula (Greek and Hebrew) | 55 | 17 | 707 | five `include:` families — built |
| **ACAI entity data** | 25 | 15 | **26,531** | **nothing** — reachable only through MCP tools |
| Berean Standard Bible | 22 | 20 | 14 | registered on this machine only, by absolute path |
| Lowfat syntax trees | 4 | 1 | 44 | ruled in #227; named but not implemented |
| SDBH / MARBLE / Tyndale | — | — | 11 / 45 / 59 | SDBH only, via `include: [senses]` on Hebrew |

`~/.sp/registrations/` holds three editions: BSB, SBLGNT, WLC.

### 3.1 Fetch from the catalogue — build this release

`awesome-biblical-data/resources.json` holds 70 entries, each with an id, name, category, formats,
licence, repository, acquisition commands and notes. That is already the declarative source three
open issues have each been missing:

- **#217** — no automatic provisioning for freely-licensed sources. The `acquire` field holds the
  commands.
- **#201** — datasets record no version and the catalogue is never validated.
- **#212** — the registry records where a source is, not what may be done with it. The `license`
  field answers exactly that.

One catalogue, three issues.

**Two findings from the catalogue itself:** BDAG is marked `Commercial`, print and Logos only, with
no acquisition path — so the licence field has to gate what the engine will fetch, which is #212's
whole point. And Perseus is marked `"Various CC"`: one download, many works, separate terms. A
single licence per resource cannot express that, and **decision 3 settles what the code does about
it.**

### 3.2 ACAI — design and rule this release, build next

The largest gap by a wide margin and the one all three projects lean on hardest. No family, no
step, no registry entry. Needs a design and the Captain's ruling before any code.

### 3.3 Lowfat syntax trees — #227, not this release

The design is ruled and recorded in `design-scripture-representations.md` §4.5 and §7; what
remains is implementation. #228 is recommended first and is bigger than it was filed as — §6.1.

---

## 4. Lexicons and semantic domains — designed next cycle

The Captain: *"after that, semlex greek and lexicon support is a high priority."* Explicitly after
the resource work, so it is recorded and not scheduled.

**Half of it already exists.** `include: [senses]` carries Louw-Nida domains for Greek and SDBH
for Hebrew, per word. What is missing is the lexicon as something you can look a word up in.

**The engine has no way to address anything by word rather than by passage.** Everything it does
is addressed by book, chapter and verse. But the join already exists: `include: [morphology]`
yields each word's dictionary form and Strong's number, so a lexicon lookup is "given this
dictionary form, return the entry", and it composes with what is built. That is a new kind of
addressing, not another edition, and it deserves its own design.

**Two shapes, and only one of them is lexicons:**

| | addressed by | belongs in |
|---|---|---|
| Abbott-Smith, LSJ, Dodson, Mounce, UBS Greek semantic dictionary | **dictionary form** | a lookup step |
| Perseus, papyri.info, First1KGreek, Patrologia Graeca, catenae | their own citation schemes | BaseX, queried with XPath |

**Perseus and papyri.info are not scripture.** They have no book, chapter and verse and no
versification, so the scripture step and the edition registry do not reach them. They are
comparative-usage corpora, and their home is BaseX — which §7.1 of
`design-scripture-representations.md` already reserved as undisplaced. Fetch them, load them,
query them; no new passage machinery.

§3.1 fetches all of them regardless, since acquisition is the same shape for every catalogue entry.

---

## 5. Comparing verse references — #169

**Ruled into this release 2026-09-01**, on the evidence in
`collab/discourse-flow/2026-09-01-verse-reference-handling.md`: that project carries **ten
verse-parsing functions across seven files**, because ordering and range membership have no home
in the engine. Verified — nothing on the public surface of `llmflow.utils.data` does either, so
those are not reimplementations of shipped code.

**It is designed twice, and the two documents are both approved and disagree in three places:**

| | `design-verse-range-operations.md` (the data model) | `plan-verse-range-set-ops.md` (the implementation) |
|---|---|---|
| references from different books | answer "no" — returns false, no error | **raises an error** |
| what the functions accept | one reference or a list, *"both"* | **two references only** |
| how many functions | six | four (stale against its own resolved note, which says six) |

Both approved 2026-08-17. An implementer has no way to tell which to follow, which is why nothing
has been built.

**The design document's own "decisions needed" list is largely stale** — five of its six items are
settled by the implementation plan or by the Captain's 2026-08-17 rulings. The real blocker is the
three rows above, which are decisions 5, 6 and 8 on the ruling sheet.

**The work, in order:** reconcile the two documents into one, then build against it —
`src/llmflow/utils/data.py` plus a new `tests/test_verse_range_ops.py`, per the implementation
plan's file list. No runner, linter or CLI change.

**Why two approved documents could disagree for two weeks unnoticed:** nothing compares them. That
is the same shape as the two defects found this week in §6 — two things that agree until they
quietly do not.

---

## 6. Carried in from the discourse-flow reports

Two documents received and answered 2026-09-01, both in `collab/discourse-flow/`.

### 6.1 A dotted name in a prompt body is never filled in

`2026-09-01-dotted-requires.md`. A name like `{{prior_closing_context.boundary_rationale}}` in a
prompt body passes the declaration check, is skipped by the required-variables check when declared
optional, is missed by the substitution loop, and is then left alone by `resolve()` — which
handles `${var}` and `{var}` but not `{{var}}`. **The placeholder text reaches the model
verbatim.** Verified end to end. Four checks, and not one of them was the one that would have
caught it.

**Not to be fixed by making the required-variables check resolve paths.** That clears the error
and leaves the placeholder unfilled, turning a loud failure into a silent one.

**#228's premise is incomplete.** It was filed on "every `optional:` in the tree is already
`optional: []`" — true in this repository, and why removing it looked like deleting a keyword. It
surveyed neither consumer projects, which carry non-empty lists, nor
`disciplines/llmflow-prompt-organization.md:40`, which documents a non-empty `optional:` as the
house pattern and is installed everywhere by `sp init`. The engine teaches what the convention
retires. Removal needs a migration and a ruling; #227 is not blocked by it.

### 6.2 The reference parser silently narrows

`2026-09-01-verse-reference-handling.md`. Reported as a sub-verse problem; it is more general.
`data.py:237-243` tries four patterns with `re.match`, and only the last is anchored to the end of
the string, so an earlier pattern matches a prefix and discards the rest:

```
'1JN 2:5b-6'             -> 1 John 2:5     end verse 5, not 6
'PHM 1:19b-20'           -> Philemon 1:19  end verse 19, not 20
'MRK 1:14 and then some' -> Mark 1:14
'MRK 1:14;16'            -> Mark 1:14
'MRK 1:14+MRK 2:1'       -> Mark 1:14
```

`1JN 2:5-6` parses correctly and gives two verses. Adding the sub-verse letter does not merely
lose the letter — **it drops the end of the range**, and nothing in the result says so. Any
trailing content behaves the same way. This is the engine's most-used reference parser, running in
four of that project's pipelines, and it is the failure `project/overview.md` names as the one to
design against: *"the engine prefers a loud error to a plausible result."* Here it does not.

The data is real: `1JN 2:5b-6` and `PHM 1:19b-20` both occur in their corpus. **What the parser
should do instead is decision 7**, and it also decides whether they represent mid-verse boundaries
as word identifiers.

**Their own inconsistency is theirs, not ours** — four of their implementations handle `2:5b` four
different ways, two raising, one returning nothing, one truncating. Recorded because it bears on
where the logic belongs, which is §5.

---

## 7. Decisions

Nine, none answered, collected in `design-decisions-awaiting-ruling.md` with a plain-language
explanation of each and the document its answer gets written back into.

Two are time-sensitive: **decision 1** blocks §2.2 and §2.4, and mentoring starts next week;
**decision 7** blocks §6.2 here and a decision in another project that is currently feeding
narrowed references to a model.

---

## 8. Out of scope, stated so it is not inferred

- **#227, Lowfat syntax trees** — ruled, implementation deferred
- **#228, removing `optional:`** — premise needs correcting first
- **Lexicons and semantic domains** — designed next cycle, not built
- **ACAI implementation** — design and ruling only
- **The seven remaining checkable rules** from #230
- **#153, versioning policy** — 0.2.1.26 is a choice, not a policy
- **#218**, which decision 9 touches but must not settle
- **The three same-subject commits on `dev`** (`2b75894`, `fcd4c67`, `ddc404d`) and `ddc404d`'s
  message, which describes #225 while carrying the design record and the skill change. Already
  pushed; the correction is the Captain's call and is not release work.
