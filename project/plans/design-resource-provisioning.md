# Design — making trusted resources available to projects

**Status: proposed, 2026-08-27. Not authorization to build.** Nine decisions are marked `=>`
and are the Captain's.

Goal, in his words: *"make our trusted resources that are freely licensed available transparently
so each project doesn't have to figure this out individually. We can fetch from github repos, but
they should not have to. And if all they need is the pericope list from a discourse flow, we
should be able to give them a simple tree with that data instead of the whole discourse
analysis."* And: *"install the latest version on main in github the first time asked for, provide
a way to update as needed."*

---

## 1. What this costs today, measured

One afternoon, one consumer repository (`sil-translator-notes`), three separate failures — none
of them the project's fault:

| | |
|---|---|
| **Pericope outlines** | The assistant was handed `gh api` incantations naming two private repositories, on two different branches (`dev` for Greek, `main` for Hebrew), in two differently-named subdirectories (`book-discourse`, `ot-discourse`), with a media-type header required because the files exceed GitHub's 1 MB JSON limit. Every one of those five facts is ours, not theirs. |
| **Versification schemes** | Worked without anyone asking where they live — because they are vendored and installed by `sp init`. The contrast is the argument for this document. |
| **The release binary** | Shipped without its own bundled data (#216). Noticed only because a consumer tried to use it. |

A fourth, latent: of eleven pericope files on disk, the Captain ruled **only four trustworthy**.
Nothing in any file says which. A consumer cannot tell a reviewed boundary from an unreviewed one,
and there is no reason it should have to.

## 2. What already exists, and precisely what it lacks

`src/llmflow/download_data.py`, 143 lines. `sp download-data <name>` and `--list`, with a
`CATALOG` of five datasets carrying `repo`, `branch`, `license`, `description`, `approx_size`. It
downloads `github.com/{repo}/archive/refs/heads/{branch}.zip`, strips the archive prefix, and
extracts to `$LLMFLOW_DATA_DIR` or `~/.sp/data/`.

**The shape is right.** It already fetches from GitHub by name rather than by URL, and it already
records a licence per resource. What it lacks:

| gap | consequence |
|---|---|
| **No update path.** `_download_dataset` returns early if the destination exists — *"already exists… use `--dest`"* | The only way to update is to delete the directory by hand. His *"provide a way to update as needed"* does not exist |
| **No provenance.** Nothing records which commit was fetched, or when | Two runs a month apart used different data and nothing says so. For scholarship this is the serious one |
| **A human must run it.** Nothing fetches on demand | Every project's setup instructions carry a manual step, which is how the `gh api` incantations happened |
| **Public repos only.** Plain `urllib`, no authentication | The pericope outlines cannot be fetched at all |
| **The catalog is code**, not data — a `dict` literal in a `.py` | Rule 29. And #216 is the lesson about two lists that must agree: `pyproject`'s force-include and the Nuitka flags drifted, and a released binary shipped broken |
| **Three names for one place** — `~/.sp/data/`, `~/.sp/datasets/`, `$LLMFLOW_DATA_DIR` | A project cannot be told one path |
| **No integrity check** | A truncated download extracts as far as it got |

## 3. The shape proposed

**A declarative resource catalog, fetch on demand, provenance recorded, update explicit.**

### 3.1 One declaration, in data

`data/resources.yaml`, beside `file-catalog.yaml` and `ai-rules.yaml`, and read by everything that
touches a resource — the fetcher, `sp doctor`, and the AI-context renderer. No second list.

```yaml
version: 1
resources:
  - id: macula-greek
    repo: Clear-Bible/macula-greek
    ref: main                      # a branch, tag or commit
    licence: CC BY 4.0
    visibility: public
    approx_size: 150MB
    purpose: Greek New Testament — syntax trees, morphology, senses
    provides:                      # what a pipeline may name, so a project needs no paths
      - id: sblgnt-tsv
        path: SBLGNT/tsv/macula-greek-SBLGNT.tsv
      - id: sblgnt-tei
        path: SBLGNT/tei

  - id: discourse-outlines-greek
    repo: nida-institute/discourse-flow
    ref: dev
    licence: proprietary
    visibility: private            # needs the human's credential; never fetched silently
    subdirectory: output/book-discourse
    trusted: [MRK, PHM, 1JN]       # the Captain's ruling, in the data rather than in prose
```

**`trusted:` is in the wrong repository and is a stopgap.** A field in our catalog listing which
of another project's files are usable is a second source of truth about their data — the defect
§2 objects to and #216 is the cautionary tale for. The first time they review a fifth book and we
do not notice, a consumer is told a reviewed file is unreviewed: wrong, and authoritative.

**Ruled 2026-08-27: the producer publishes a catalog with a status and a date per item, and the
user decides what they are willing to use.** Not a boolean, and not our judgement. Asked for in
the drafted issue against `discourse-flow`, with an ordered scale so a threshold is expressible:

```
generated  <  draft  <  reviewed  <  approved        superseded, withdrawn
```

`reviewed` and `approved` are distinct on purpose — examining something and declaring it fit for
someone else's use are different acts, and the second is a human judgement. That distinction is
the same one behind this project's rule against an assistant calling output approved.

So the engine's side is a *threshold*, not a list:

```yaml
  - id: discourse-outlines-greek
    repo: nida-institute/discourse-flow
    ref: dev
    subdirectory: output/book-discourse
    status_catalog: output/catalog.json   # theirs; read, never written here
    minimum_status: reviewed              # the default this engine will use
```

and a project may lower or raise it deliberately:

```yaml
- name: load_pericopes
  type: scripture           # illustrative — the key belongs wherever resources are named
  minimum_status: draft     # "I know these are unreviewed and I want them anyway"
```

Three properties worth stating, because each removes a failure seen today:

- **An item below the threshold is refused by name, with its status and date.** Not filtered out
  silently: *"LUK is `generated` as of 2026-06-12; this pipeline requires `reviewed` or better"*
  tells a user what to do, where an empty result does not.
- **A missing status reads as `generated`**, the lowest. Absence must not mean "fine".
- **The date is load-bearing.** A book approved before a boundary algorithm changed is not
  approved for current output. Macula was re-normalised on 2026-08-25; the same will happen there.

Until their catalog exists, ours carries a dated stopgap that says what it is:

```yaml
    trusted: [MRK, PHM, 1JN]       # STOPGAP, ruled 2026-08-27. Retire when the producer
                                   # publishes a status catalog — discourse-flow issue.
```

=> 

### 3.1a A well-known file, used if present — because we control few of these

**Ruled 2026-08-27.** The status catalog above can only be *required* of repositories the Captain
controls. `Clear-Bible/macula-greek`, `biblicalhumanities/levinsohn` and `BibleAquifer/ACAI` are
other people's, and will never publish a file in our shape. So the convention is **declarative and
optional: a known filename at the resource root, used when it is there and absent without
complaint when it is not.**

`.sp-resource.yaml`, at the root of the resource:

```yaml
# Published by the resource, describing itself. Read by sp; never written by sp.
version: 1
id: discourse-outlines-greek
licence: proprietary
attribution: "Nida Institute — discourse-flow"
provides:
  - id: pericopes
    path: output/catalog.json      # or a directory
    kind: json
status_catalog: output/catalog.json
```

**The separation this creates is the point, and it is worth stating as a rule:**

> **Facts about a resource come from the resource. Policy about using it comes from us.**

| | declared by | example |
|---|---|---|
| what it provides, its licence, attribution, review status | **the resource**, in `.sp-resource.yaml` | `status: approved, as_of: 2026-06-11` |
| whether to fetch automatically, what minimum status to accept, where to cache | **`data/resources.yaml`** | `minimum_status: reviewed` |

So for a repository the Captain controls, our catalog entry shrinks to almost nothing — `repo`,
`ref`, and our own policy — because the resource describes itself. For Macula and Levinsohn our
entry carries everything, as it must, and is honestly marked as *our* description of someone
else's data rather than theirs.

**Three consequences.**

- **Precedence must be stated, not inferred.** The resource wins on facts about itself; a
  disagreement between the two is reported rather than silently resolved, because a resource that
  has started declaring its own licence and a stale entry of ours claiming another is exactly the
  case where guessing is worst.
- **Absence is normal, not a warning.** Most resources will never have the file. `sp resources`
  can show which do — *"self-describing"* against *"described by sp"* — which is useful
  information rather than a defect to nag about.
- **It is a small spec, so it should stay small.** Every field is one more thing another project
  must implement to be a good citizen. The four above earn their place; a fifth needs an argument.

*Naming: the provenance record this engine writes in its own cache (§3.3) must not use the same
filename, or a fetched resource's own declaration would be overwritten by our note about it.
`.sp-resource.yaml` is the publisher's; `.sp-fetch.yaml` is ours.*

=> 

### 3.2 Fetch on demand, but never silently

A pipeline naming a resource that is absent triggers a fetch. Two constraints on that:

- **Size and consent.** Macula Hebrew is ~400 MB. Fetching that because a pipeline mentioned it,
  with no prompt, on a metered connection, is not acceptable. So: fetch automatically below a
  size threshold; above it, fail with the exact command to run.
- **Private resources are never fetched automatically.** They need a credential that is the
  human's, and a failure there is an access question, not a retry.

### 3.3 Provenance, which is the part that matters for scholarship

Every fetch records what it got, in `~/.sp/resources/<id>/.sp-fetch.yaml`:

```yaml
id: macula-greek
repo: Clear-Bible/macula-greek
ref: main
commit: 3839852b1c...          # what `main` actually was at fetch time
fetched: 2026-08-27T14:22:00Z
bytes: 157286400
```

Two things follow. **`sp doctor` can report the version of every resource**, so "what data was
this run against" has an answer. And **a run's audit trail can record it**, which is the
difference between a reproducible analysis and one that merely looks reproducible. Macula was
re-normalised on 2026-08-25 — output generated before and after that differs, and today nothing
in either run would say so.

### 3.4 Seeing what you have, what exists, and whether to upgrade

**Ruled 2026-08-27: this is a first-class requirement, not a by-product of the update command.**
A user must be able to answer three questions without reading a design document or a repository.

```
$ sp resources
  RESOURCE                    STATUS      VERSION            SIZE
  versification               installed   vendored, 0.2.1.24  169 KB
  macula-greek                installed   3839852 (2 days)    150 MB   ← update available
  macula-hebrew               available   —                   ~400 MB
  discourse-outlines-greek    available   —                   —        needs access
  acai                        installed   a41c9f2 (31 days)   50 MB
```

Three states, and the distinction matters: **installed** (present, with the commit it came
from), **available** (catalogued, not fetched), and **needs access** (catalogued, private, and
this machine has no credential for it). The last is a state today's `download_data.py` cannot
express at all, and it is the one that cost an afternoon.

*"Update available"* requires asking GitHub what the ref resolves to now, which is a network
call — so it is shown when the command is given a flag, or when the answer is already cached,
and never as a side effect of a pipeline run. A status view that silently reaches the network
each time is a status view people stop running.

### 3.5 Update as an explicit act

`sp resources update [id]` re-resolves the ref, compares the commit, and reports. Never
automatic: a resource changing under a project mid-analysis is the failure this design exists to
prevent, and *"fetch the latest"* is exactly how it would happen.

## 4. Decisions

**4.1 One directory name.** Three are in play. Proposal: `~/.sp/resources/<id>/`, with
`~/.sp/datasets/` and `~/.sp/data/` migrated and `$LLMFLOW_DATA_DIR` kept as an override for a
machine that must put bulk data elsewhere.

=>

**4.2 Automatic fetch, and the threshold.** Proposal: fetch without asking below 50 MB; above it,
fail with the command. That makes versification-sized things invisible and Macula-sized things
deliberate.

=>

**4.3 Private resources.** Proposal: use `gh` when it is on `PATH` and authenticated, since that
is how the human already authenticates, and otherwise fail naming the resource and the access
needed. Alternatives: a token in the environment, or refusing private resources entirely and
requiring a local clone registered by path.

=>

**4.4 Pinning.** Proposal: the catalog's `ref` is the default and a project may pin a resource to
a commit in its own configuration; a pinned resource that does not match errors rather than
re-fetching. The question is whether pinning belongs in the pipeline, in a project-level file, or
nowhere yet.

=>

**4.5 Does a resource version enter the audit trail?** Proposal: yes, and it is the strongest
argument in this document. The cost is that every run writes a few more lines, and that a
resource with no provenance file — a hand-registered local clone — has to be recorded as
`unknown` rather than omitted.

=>

**4.6 What about a slim projection, like the pericope list?** A consumer needing only boundaries
should not fetch a 2 MB analysis for 14 KB of data (0.7%). Two ways: the producing repository
publishes the projection — asked for in a drafted issue against `discourse-flow` — or the engine
derives it on fetch. Proposal: ask the producer, because a projection derived here would be a
second implementation of their boundary semantics, and the first time those changed we would be
silently wrong. But it makes us wait for them.

=>

## 5. What this does not cover

- **Licensing and attribution obligations** — `#212`. This design records a `licence` field and
  nothing more. What a project must do when it ships output derived from a CC BY-SA source is
  that issue's question, and it should be settled before any resource with a share-alike licence
  is fetched automatically.
- **Bundling.** Deliberately unchanged: the versification schemes stay vendored because they are
  169 KB and every project needs them. The rule proposed is that vendoring is for what is small
  and universally needed, and fetching for everything else — not that vendoring is wrong.
- **Resources that are not on GitHub.** Every one today is. A resource behind a login or on a
  filesystem stays a registered path, as editions are now.

- **Loading XML resources into BaseX.** Noted by the Captain, 2026-08-27, and deliberately out of
  scope for this release: a future one should be able to load an XML resource into a standard
  BaseX database location **when asked to**, not as a side effect of fetching it.

  Recorded here because it constrains this design rather than merely following it. The catalog
  entry is the natural place to say that a resource is XML and which database name it belongs in,
  so `provides:` should be able to carry that without a second declaration — which is an argument
  for getting `data/resources.yaml` right now even though nothing reads that field yet. It also
  sharpens 4.4: a BaseX database built from a resource is a *derived artefact*, so the provenance
  record has to say which commit it was built from, or a stale database is indistinguishable from
  a current one. `type: basex` already exists and takes a `database:` name, so the consuming half
  is built.

## 6. Order of work, if approved

1. `data/resources.yaml` and a loader, with the existing five datasets migrated into it and
   `CATALOG` deleted rather than left as a second source.
2. Provenance on fetch, and `sp doctor` reporting resource versions. This is small and useful
   immediately, independently of anything else.
3. `sp resources` — the status view of §3.4. It needs only the catalog and the provenance
   files, so it follows directly from 1 and 2 and answers the question users actually ask.
4. `sp resources update`.
5. Fetch on demand, with the threshold from 4.2.
6. Private resources, per 4.3.
7. The audit-trail entry, per 4.5.

Steps 1 to 3 are worth doing even if the rest is deferred: they turn a hardcoded list into data
and answer "what was this run against", which nothing does today.
