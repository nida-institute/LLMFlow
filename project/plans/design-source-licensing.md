# Design — what a source permits, and who may act on it (#201)

**Status:** Proposed, 2026-08-24. Four rulings recorded from the Captain (§3); six questions
open in §8. **Nothing built.** The model is not authorization to implement — it needs the
answers in §8 first, and §8 Q5 is a question about data only the Captain can answer.
**Issue:** #201 (related — datasets record no version and the catalog is never validated; this
is the same registry gap seen from the licensing side). A dedicated issue is proposed in §9.
**Author:** AI, from the Captain's rulings in conversation and from measurements of
`~/.sp/editions/`, `data/file-catalog.yaml` and `nida-institute/awesome-biblical-data`. Every
number below was measured on 2026-08-24 and can be re-measured.

---

## 1. What I understand the goal to be

Scripture Pipelines reads texts, lexicons and annotation sets whose terms of use differ
enormously — from public domain to a custom licence with downstream conditions to an
unpublished Paratext project belonging to a translation team. The engine currently records
**where** a source is and **nothing about what may be done with it**.

The goal is that the tooling knows the difference, that it fails safely when it does not, and
that the four ways permission arises are all expressible — including the one where the
copyright holder is the client the work is being done for.

## 2. What exists today

`~/.sp/editions/` holds three records — `BSB.yaml`, `SBLGNT.yaml`, `WLC.yaml`. A record looks
like this:

```yaml
id: BSB
name: Berean Standard Bible
language: English
canon: OT+NT
kind: usfm
base_dir: /Users/jonathan/github/usfm-bible
project: examples.bsb
notes: >-
  Depends on a local patch until usfm-bible/examples.bsb#7 merges …
```

**None of the three records a licence.** Nothing in `data/file-catalog.yaml` does either — it
governs files `sp init` writes, not sources it reads. So the engine cannot distinguish BSB,
which is public domain, from SBLGNT, whose own catalogue description says *"imposes conditions
on downstream works — read the license carefully."*

Meanwhile the facts exist. `nida-institute/awesome-biblical-data/resources.json` holds **65
resources**, each with `id`, `name`, `category`, `description`, `formats`, `license`, `github`,
`url`, `acquire` and `notes` — **30 distinct licence values**, and every resource has one.

Measured coverage against what this engine registers:

| registered edition | in the catalogue? | licence recorded there |
|---|---|---|
| BSB | yes, `bsb` | `Public domain (text); repository has no license file` |
| SBLGNT | yes, `sblgnt` | `Custom — see http://sblgnt.com/license/` |
| WLC | **no direct match** | closest are `bibleaquifer-wlc` ("See repo") and `ubs-marble-wlc-index` (CC BY-SA 4.0) |

**Eight of the 65 carry terms only a human can resolve:** `sblgnt`, `bibleaquifer-sblgnt`,
`cntr-transcriptions`, `codex-sinaiticus`, `catss` ("Restricted"), `levinsohn-lgntdf` ("freely
distributable, not for sale"), `trismegistos`, `copenhagen-versification`. One of those eight
is a text this engine uses today.

**Absent from the catalogue entirely:** HOTDF-LS (recorded elsewhere as *"not public, from SIL
International"*), and the NIV CBT rationale notes. Both are real sources in real projects.

## 3. The Captain's rulings — verbatim, 2026-08-24

On where a project-specific confidentiality constraint belongs:

> "definitely lives in the project, not sp global. we have this same problem in other spaces -
> I have legal access to various copyrighted texts that we may use to compute diffs or cross
> reference, but which must not be pirated in our output."

On individual permission:

> "a few people in our organization are also known to have permission to use these copyrighted
> texts"

On the catalogue:

> "everything in awesome bible resources has a known license. we should put these licenses in
> the registry"

On work done for the copyright holder:

> "I often work on projects for the people who own the copyright to a given work, e.g.
> processing a paratext project for the translation team, whatever license they are using. we
> need to make that possible."

## 4. Four ways permission arises

| status | permission comes from | example | in `resources.json`? |
|---|---|---|---|
| **open** | a public licence | BSB, Macula | yes |
| **needs reading** | a custom licence a human must read | SBLGNT, CATSS, Levinsohn LGNTDF | yes, and flagged |
| **individual grant** | someone granted access to *particular people* | HOTDF-LS, NIV CBT notes | no, and cannot be |
| **owner-supplied** | the copyright holder is the client, and the work is for them | a translation team's Paratext project | no, and never will be |

The first two are facts about a *source*. The third is a fact about *people*. The fourth is a
fact about an *engagement* — and the same text may be handled differently in two of them.

That is why one licence field cannot carry all four.

## 5. Three principles the model has to encode

**Reading is not publishing.** The right to open a source is not the right to reproduce its
wording. Computing over it — diffs, alignment, cross-references, counts — is usually permitted
where reading is, and what leaves is the result, not the text. For the NIV CBT case the
*attribution itself* is the leak, not the wording: notes must read as derived from general
commentary, never naming the internal source.

**Licence and availability are two axes, not one.** The Captain, 2026-08-24: *"'freely
licensed' does not imply 'already published and available', I can commit to a free license
before I make something public."* So a source may be freely licensed and unpublished, or
published under terms that forbid redistribution, and the two facts move independently:

| | published | not yet public |
|---|---|---|
| **permissive licence** | quote freely, attribute | **the licence is settled, the material is not yours to circulate** |
| **restrictive licence** | read the terms | most restricted case |

The bottom-right cell is the one a single `licence:` field gets wrong, and it is not
hypothetical: the Hebrew pipeline is recorded as *"waiting on HOTDF-LS going public before full
release"*, and the translation notes are *"going to be freely licensed, I believe"* — stated as
belief rather than settled, and in any case not yet published.

**The more restrictive of the two governs until publication.** A permissive licence agreed in
advance does not authorise circulating drafts.

### The worked example, and why it needs both layers

The Captain, 2026-08-24, of the Hebrew discourse data: *"[a colleague] has granted us the right
to use this data, and it will be freely licensed, but it is not yet published."*

Three separate facts, and no single field holds them:

| fact | axis | where it lives |
|---|---|---|
| a free licence is intended | licence | the source's record, marked as intended rather than in force |
| it is not yet published | availability | `availability: unpublished` on the record |
| the right to use it was granted to us | entitlement | **not in any repository** |

The third is the one that cannot be committed. Recording *who* granted access, and to whom,
means naming people in a shared artifact — which rule `no-stakeholder-speculation` forbids and
which the Captain ruled against directly on 2026-08-24 when asked whether to name the
collaborator in the issue: **"don't name him."**

So the committed record says only that access is individual and unpublished. Who granted it,
and whether *this* operator holds it, is recorded in `~/.sp/user-context/` — per-machine, never
shipped, uncatalogued by D6, and authored only by the machine's owner.

This is the layering doing its job under a real constraint rather than a hypothetical one: the
tooling learns "restricted, unpublished, do not circulate" and learns nothing about any person.

**A permissive output licence raises the stakes on a restricted input.** Once the translation
notes *are* published under a free licence they will be copied and republished by people with
no relationship to the internal source. An accidental *"the NIV chose X"* then travels
everywhere and cannot be recalled, and every downstream copy carries the attribution the
agreement forbids. That is why the constraint has to hold at generation time, while the artifact
is still singular and correctable.

The general form: **input terms and output terms are independent.** A restricted input can feed
a freely licensed output, and a permissive input can feed an output that belongs to a client. A
design carrying one licence per source cannot express either.

**Presence on disk is not permission.** A file resolving under `base_dir` says nothing about
whether this operator is entitled to it. Entitlement is held by people, not by filesystems or
repositories.

**A committed record cannot assert entitlement.** `may_compute: true` in a repository reads as
a statement about whoever holds the repository. Where access is individual, the record must say
that access is individual and who administers it — never that the reader has it.

## 6. Where each fact lives

| fact | home | why |
|---|---|---|
| what a public source's licence says | `resources.json`, referenced by id | one upstream, no retyping |
| that a source's terms need human reading | derived from the licence value | the AI must not infer terms |
| that access is individual, and who to ask | the source's record | a fact about the source, safe to commit |
| whether **this operator** holds that access | `~/.sp/user-context/` | per-machine, never shipped, uncatalogued by D6 — the same place `github-authority.md` puts identity |
| an engagement's terms and owner | the **project** repo doing that work | the Captain's ruling in §3; it is a fact about the engagement |

## 7. The shape of a declaration

For a catalogued source, the edition record references rather than copies — and carries
availability separately, because §5 shows the two axes move independently:

```yaml
id: SBLGNT
resource_id: sblgnt        # resolves to resources.json; the licence has one home
availability: public       # public | embargoed | unpublished | private
```

`availability` cannot come from `resources.json`: a catalogue of published resources has no way
to say "licence agreed, not yet released". It is a fact about the copy in hand, so it belongs on
the record that names that copy.

For an owner-supplied source, the project declares what no catalogue can know:

```yaml
source:
  kind: owner-supplied
  owner: <the translation team or organisation>
  purpose: <what the engagement is>
  output_belongs_to: <usually the owner>
  may_leave_this_project: false
```

`output_belongs_to` is the field the other three cases do not need. For a public text the
question is *may we quote it*; here the text may be freely processed and **the result is still
theirs**. Producing output is fine; publishing it, reusing it as an example, or carrying it
into another engagement is not.

**The failure this prevents is cross-contamination:** one team's text appearing in another
team's output, in a shipped example, in a public artifact, or in a cached intermediate a later
pipeline reads. An AI will do this cheerfully, because it looks like reuse.

**There is a mechanism available rather than a policy.** `data/file-catalog.yaml` already
derives the generated `.gitignore` from each entry's `committed` field. Outputs derived from an
owner-supplied source defaulting to `committed: false` means client material cannot reach a
public repository through the ordinary act of running a pipeline and committing.

**The default is fail-closed.** An undeclared source is restricted, not open. The registry's job
for the third and fourth cases is not to supply terms but to *require a declaration*.

## 8. Open questions

**Answer inline after each `=>`.**

### Q1. Does an undeclared source fail, or warn?

An edition with neither a `resource_id` nor a `source:` block is either an error from `sp lint`
or a warning. Failing is the difference between a model that protects and one that documents;
warning is kinder to existing projects, of which there are three editions and an unknown number
of consumer repos.

=>

### Q2. Where do owner-supplied declarations live?

§6 assumes the project repo, following the ruling in §3. The alternative is `~/.sp/editions/`
with everything else — which keeps one registry but puts client terms on a machine rather than
in the work they belong to, and makes them invisible to anyone else on the engagement.

=>

### Q3. Vendor `resources.json`, or reference the clone?

`data/models.json` is the precedent: vendored pricing data, refreshed by `sp models --update`,
with a staleness nudge at `cli.py:838`. Vendoring works on machines with no clone of
awesome-biblical-data, which is every machine sp ships to. Referencing is simpler and always
current, and breaks offline.

=>

### Q4. Does awesome-biblical-data become upstream for sp?

If licences resolve by `resource_id`, then adding a source to sp means adding it *there* first.
That couples two repositories that are currently independent, and makes one a dependency of the
other's correctness. It is the single-source discipline applied across a repo boundary — the
same trade as `data/helm-sync.yaml`, which has needed rulings to manage.

=>

### Q5. Which WLC is registered? *(data — the Captain's domain, rule 25)*

`WLC.yaml` names a `base_dir` but no catalogue entry clearly matches it. Either the text needs
adding to awesome-biblical-data, or the registry needs a different id. The AI will not guess
which Hebrew text this is or what terms it carries.

=>

### Q6. Do outputs from an owner-supplied source default to uncommitted?

§7 proposes it, using the `committed` field the catalog already derives `.gitignore` from. The
cost is that a team who *does* want their outputs committed must say so explicitly.

=>

## 9. Proposed, not filed

A dedicated issue for this design, referencing #201 as the registry gap it shares. Rule 22: the
title and body go to the Captain before `gh issue create` runs.

## 10. What this does not change

- **`resources.json`'s schema.** This design reads it; it does not propose editing
  awesome-biblical-data beyond Q4 and Q5.
- **`~/.sp/user-context/`.** Uncatalogued by D6 and authored only by the machine's owner. This
  design names it as the home for operator entitlement and proposes no AI writes there.
- **Existing pipelines.** Nothing here changes how a pipeline reads a text; it changes what the
  registry records about one.
- **The `licence` values themselves.** They are read from the catalogue, never inferred. Eight
  of them say "read this page", and that instruction is for a human.
