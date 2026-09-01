# Design — the layer between Helm and the engine

**Status:** proposed — not authorization to build. Four decisions remain marked `=>` and are the
Captain's; answer inline after each. (D3 is ruled; see below.) #226

Origin: *"we also have repositories like macula-greek and macula-hebrew that predate scripture
pipelines and have their own build and test systems, but create content, and would benefit from
some of the info in sp's ai environment in addition to helm. Not sure what to do with those."*

And, settling who may write where: *"Biblica bought Clear, it's the same team, and I am the only
remaining member of that team."* The Captain works for Biblica and is seconded to Nida — so the
three org names on these repositories (`Clear-Bible`, `Biblica`, `nida-institute`) are one
team's history, not three parties to negotiate with. The `Clear/` repositories are his to
permit, and he has permitted them.

---

## 1. The layer that exists but has no name

```
Helm      how to work with an AI at all          any repo, any language
[this]    how to work with biblical text         any repo that touches scripture
sp        this engine's syntax and API           repos that run pipelines
```

The middle layer is real today — it is simply trapped inside the third. From `sp/rules.md`:

| rule | what it says | true in a Macula repo? |
|---|---|---|
| 12 | verses are milestones, not containers; never divide by verse count | yes |
| 31 | never italicise a script with no italic tradition | yes |
| 32 | `lxml`, not `xml.etree` — the work is XPath- and XSLT-shaped | yes |
| 35 | scripture reference data is JSON; PyYAML reads `1:1` as `61` | yes |
| 25, 26 | the data is the Captain's domain; teaching him is the work | yes |

None mentions pipelines. Each is knowledge a session in `macula-hebrew` would otherwise
rediscover the hard way — 35 by silently corrupting a reference, 31 by shipping mangled Hebrew.

Two documents are mostly domain as well: `passage-references.md` (versification, book naming,
what a reference means) and about half of `scripture-representations.md`.

**The boundary is already enforced one level up.** `test_portable_disciplines` fails when a
*shared* discipline carries engine vocabulary, which is why `workflow.md` and `sp-workflow.md`
are two files. The same argument applies here: a domain layer that says "pipeline" cannot be
taken by a repository that has none.

## 2. Where it lives

**`nida-institute/awesome-biblical-data`.** Ruled: *"it does live in awesome-biblical-data."*

It already holds the shared, public, domain-level artifact — a catalog of resources — and we
have taken over its maintenance. Conventions for *working with* those resources belong beside
the catalog of them. It is also already vendored into sp, so the plumbing for sp to read it
exists and was built this week for `resources.json`.

**=> D1. What is the directory called?** `conventions/` is available but was just retired in
`~/.sp` for being the stale twin of `disciplines/`, and reusing the word invites the confusion
we removed. Candidates: `practice/`, `working-with-the-data/`, `disciplines/` (matching Helm's
noun, at the cost of two things called disciplines). *Recommendation: `practice/` — it is not a
word either of the other layers uses.*

=>

## 3. How a repository gets it

Three shapes, and they are not exclusive:

- **Its own installer**, as Helm has: a `manifest.yaml` declaring what lands where, run by an
  `/install` skill. Consistent with Helm, and works for a repository that wants nothing else.
- **Vendored by sp**, as `resources.json` is: `sp init` installs the layer alongside its own.
- **Read in place** by a repo that clones the catalog anyway.

*Recommendation: the first and second.* A Macula repo takes it on its own; an sp project gets it
without a second install step.

**=> D2. Which shapes?**

=>

## 4. The renumbering problem — the real landmine

`data/ai-rules.yaml` is the single source for `sp/rules.md`, and **the rules are cited by
position** across repositories. The file says so itself, repeatedly: *"Appended rather than
inserted beside `one-design`, because rules are cited by position across this repository, and
inserting mid-list would falsify every one of those citations."*

Removing rules 12, 31, 32 and 35 renumbers everything after them. Every `rule 29` in a commit
message, a plan, a discipline or another repository would then point somewhere else.

Options:

- **Tombstones.** The number survives with a line saying where the rule went. Citations keep
  working; the file grows entries that are not rules.
- **Stop citing by number.** Each rule already has an id (`design-is-declarative`,
  `verses-are-milestones`); cite those and renumber freely. Correct long-term, and it does not
  fix the citations already written.
- **Leave them in place and duplicate.** Rejected on sight: it is the two-encodings defect this
  whole week was spent removing.

*Recommendation: tombstones now, ids in new citations from here on.*

**=> D3. How?**

=> Cite by id. *"citing by id is going to be important long term. we should bite the bullet in
the next release we are starting now."* Ruled also: the number disappears from the rendering
entirely, and two guard tests hold the convention.

**This is a prerequisite, not part of this work** — the numbers must stop being the identity
before any rule can move. Scoped separately in `plan-cite-rules-by-id.md`, which ships first.
Once it lands, D1, D2, D4 and D5 below are all that remain.

## 5. What moves

*Proposed, for your ruling — this is the list I would act on:*

| moves | stays in sp |
|---|---|
| 12 verses are milestones | 2 pipeline schema, 3 logger/telemetry, 4 prompt contracts |
| 25, 26 the data is the Captain's | 23 data moves through the pipeline context |
| 31 never italicise a non-italic script | 24 express logic in the pipeline language |
| 32 `lxml`, not ElementTree | 29 design is declarative *(general, but sp's own premise)* |
| 35 reference data is JSON | 33 output vs intermediate directories |
| `passage-references.md` | `scripture-representations.md` — **split**: formats and costs are sp's, the milestone rule and the discourse `outcome` reading are domain |

**=> D4. Is that the right cut?** In particular 29 (`design-is-declarative`) is general enough to
move and central enough to sp that moving it would gut the engine's stated premise.

=>

## 6. Not in scope

- **Rewriting Macula repositories to use sp.** They have their own build and test systems that
  predate it, and the point of a middle layer is precisely that they need not adopt the engine.
- **Helm.** Nothing moves out of it; this layer sits below it and is taken in addition.
- **The `Clear/` repositories' contents.** Installing a conventions directory is not licence to
  edit the data.

**=> D5. Which repositories get it first?** `Clear/macula-greek` and `Clear/macula-hebrew` are
the named cases. The nida-institute content repos — `semdom-greek-lexicon`, `hebrew-phrasing`,
`pericopes`, `levinsohn-samuel-hebrew`, `macula-lxx-greek` — are the same shape.

=>
