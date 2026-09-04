# For the session writing executive documents: what this repository can and cannot tell you

**From:** the development session in `nida-institute/LLMFlow`, 2026-09-04.
**To:** whichever session is drafting C-level documents.
**Status: drafted by the AI, pending the Captain's review.**

The Captain named the altitude: deliverable, customer, who he is working with, partnerships, and
Nida Institute time — what they are paying for. He also asked, of that list, *"will they care about
this level of detail"*, which is the right question and mostly answers itself: a C-level reader
wants none of the engineering.

This note exists because two of those six headings are ones **this repository cannot answer and an
AI must not invent**, and because the documents that look like they hold the answers are known to
be unreliable. Read the second section before using anything from the plan files.

---

## 1. Two headings are the Captain's alone — do not derive them

Rule `no-stakeholder-speculation`, in force:

> **Do not name customers, partners or stakeholders, and do not speculate about their needs or
> their politics.** In issues, documents, commit messages and anything else shared, write
> "downstream consumers" or "use cases" generically. Name a specific organisation, system or person
> only where the human has asked for it in that context.

Its stated reason is exactly this situation: the AI does not know who the customers are, what they
have been promised, or what is contested between them — and a guess in a shared artifact is
indistinguishable from a statement of fact to whoever reads it. For an executive document that is
the worst place for it to happen, because no reader downstream can check it.

So **"Customer", "Who am I working with" and "All partnerships"** are inputs the Captain supplies.
They cannot be assembled from repository contents, git history, or the names in a dependency list.

**The distinction that is safe**, and it is worth holding on to: *"the software reads data
published by X"* is a fact about the code. *"X is a partner"* is a claim about a relationship.
Section 3 gives the first kind. Only the Captain can give the second.

---

## 2. Do not take state from the plan documents

**Five plan or tracking documents in this repository asserted state that was false — found in a
single day, 2026-09-03.** This is the repository's dominant defect class, and an executive document
built on it would carry the error further than any other artifact.

| document | claimed | actual |
|---|---|---|
| `plan-release-0-2-1-26.md` §3.1 | resource-catalogue fetching still to build | shipped three weeks earlier |
| seven shipped documents | one configuration directory | a different one; the named path was retired months ago |
| `TODO.md` workshop section | ten open blockers | several already fixed |
| `plan-release-0-2-1-26.md` | one feature "not implemented" | shipped, but silently does nothing |
| issue #38 | closed as completed | never implemented; closed on an AI's conversational claim with no commit and no test. Reopened 2026-09-03 |

The Captain's words on the last one, which is the one worth quoting in a document about how the
work is run:

> "We had to implement this because it's not in SP" is not proof that it isn't needed, it is often
> proof that it is needed.

Everything in section 3 below was verified against the code, the test suite, or CI on 2026-09-04 —
not read from a record. If you need a fact that is not here, ask for it to be verified rather than
quoting a plan file.

---

## 3. Deliverable — verified

**Scripture Pipelines 0.2.1.26, released 2026-09-04.** Published, not a draft. Three platform
binaries attached — macOS, Windows, Linux — and the installation script was verified by CI on all
three operating systems as part of the release.

Public release history runs back through 0.2.1.18. Distribution is by downloadable binary and
install script, plus the Python package index.

**One qualification a C-level document should not overstate:** the Python-package-index publication
of 0.2.1.26 was still pending the Captain's approval at the time of writing, so that channel was
one version behind. If the document claims "released", the binary and installer channels support
it; check with him before implying every channel is current.

**What is in it**, at a level worth writing down: support for Hebrew alongside Greek in a feature
that previously served only Greek; two breaking changes to the pipeline language, deliberately
taken while the user base is small; and a body of work making the project's own written rules
enforceable by tests rather than by attention.

**What is next**, scope ruled 2026-09-03 for the following release: Hebrew working end-to-end for
one consumer project, a declaration mechanism for distinguishing evidence from product in generated
output, support for Paratext translation projects including their own verse-numbering files,
verse-range comparison operations, and syntactic structure. One further item is conditional on
capacity.

---

## 4. Data sources the software reads — fact, not relationship

Stated as what the code does, because that is all this repository establishes. Whether any of these
represents a partnership, a licence negotiation, or an informal arrangement is the Captain's to
say — several are open-licence public datasets and require no relationship at all.

- Original-language texts with word-level linguistic annotation, Greek and Hebrew
- Discourse-feature annotations for both Greek and Hebrew, the Hebrew set currently unpublished
- An English translation used for comparison
- A published cross-tradition verse-numbering specification, and Paratext project versification
  files
- Two published book-naming authorities, one scholarly style manual and one open-source standard
- A public catalogue of biblical datasets, 70 entries, carrying licence and acquisition
  information per entry

The engine also declines to gate access on licence, by ruling: a project you can open is one you
have already established a right to read. That is a deliberate design decision and may be worth an
executive line, since it places the licence responsibility with the user rather than the tool.

---

## 5. Nida Institute time — the one dated commitment

**A mentoring week beginning 2026-09-08.** The Captain's acceptance criterion for it, recorded
2026-08-17:

> a user clones a mentoring repository, runs `sp init`, and `/load-context` works. Nothing
> hand-carried.

That criterion is not yet met, and the repository's own tracking marks workshop readiness as the
**main next goal** while none of the next release's scope addresses it. The evidence it is unmet is
a recorded first-hand failure: a colleague cloned the repository, ran the setup command, and the
onboarding step failed; getting him working required hand-built archives and manual file edits, and
still did not fully work.

Several of the specific causes have since been fixed — verified — but the blocker list has not been
re-checked as a whole, so **nobody currently knows how far from the criterion it is.** That is the
honest executive statement, and it is a scheduling question rather than a technical one: a dated
commitment competes with a release for the same days.

If the documents need a single risk item at this altitude, that is the one.

---

## 6. What not to carry into an executive document

- **Test counts, commit identifiers, file paths, defect classes.** They are the substance of the
  development record and noise at this level. If a claim needs them as evidence, cite the
  conclusion and keep the evidence available on request.
- **The names of consumer projects, and the volume of duplicated code found in one of them.** It is
  a real and interesting finding — a consumer carries a fork of engine code, and that fork is why
  one language does not work there — but it names a specific project and characterises its
  engineering. Whether that is written down, and how, is the Captain's call, not a detail to
  include for colour.
- **Anything framed as "approved", "production ready", or "suitable for use".** Rule
  `output-is-draft` and the project's authority boundary both forbid an AI making that assessment;
  deployment decisions require human accountability.

---

## 7. What to ask the Captain for

1. The customer and partnership map — section 1 explains why it cannot come from here.
2. Whether the mentoring week's readiness gap goes in the documents, and how it is framed.
3. Whether the package-index channel is current by the time the documents are written.
4. Which of the four data-source categories in section 4 are relationships he wants named.
