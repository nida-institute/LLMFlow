# Design — provisioning scripture editions, #217

**Status: proposal, 2026-08-29. Not authorization to build.** Four decisions are marked `=>` and
are the Captain's. Answer inline after each `=>`.

Reported by a downstream consumer on v0.2.1.24: a machine that had completed setup, had the
versification store, and had never had an edition registered. The pipeline linted clean, started
running, and failed deep in execution with `EditionNotRegistered` — whose remedy text names
`sp registry`, a command with no subcommand that can do it.

---

## 1. What is actually missing

Not a downloader. **`sp download-data` already exists** and already knows the sources:

```
macula-greek     Clear-Bible/macula-greek            CC BY 4.0     ~150MB
macula-hebrew    Clear-Bible/macula-hebrew           CC BY 4.0     ~400MB
berean-usx       Freely-Given-org/OpenEnglishBible   CC BY-SA 4.0  ~15MB
acai             BibleAquifer/ACAI                   CC BY-SA 4.0  ~50MB
```

It unpacks them into `~/.sp/data/<name>/`. What does not exist is the step from *"the data is on
this machine"* to *"the engine knows an edition called `WLC` and where its text is"*. That step is
done today by hand-authoring a YAML file with an absolute path in it:

```yaml
id: WLC
kind: tsv
path: /Users/jonathan/github/Clear/macula-hebrew/WLC/tsv/macula-hebrew.tsv
```

Three defects follow, and they are separable:

1. **Nothing knows which editions exist.** There is no catalog, so every project re-derives that
   WLC is Macula Hebrew's `WLC/tsv/macula-hebrew.tsv` and that it is Old Testament only.
2. **The path is absolute and per-machine.** A file that is correct here is wrong on every other
   machine, which is why setting a colleague up meant hand-editing three files.
3. **Nothing checks.** `sp doctor` reports on versification, skills, conventions and project
   files, and says nothing about editions — correct, missing or broken.

## 2. The shape proposed

**One declaration, `data/editions-catalog.json`**, carrying syntax and semantics together, in the
form rule `design-is-declarative` asks for. Per edition: what it is, which dataset carries it,
where inside that dataset, and — the part that matters most — **which versification scheme it is
numbered in**, so #203 stops falling back to the guess table for a text we shipped the answer for.

```json
{
  "WLC": {
    "name": "Westminster Leningrad Codex",
    "language": "Hebrew", "canon": "OT", "kind": "tsv",
    "dataset": "macula-hebrew",
    "path": "WLC/tsv/macula-hebrew.tsv",
    "versification_scheme": "org",
    "license": "CC BY 4.0",
    "attribution": "Clear Bible, Inc."
  }
}
```

=> We already maintain this in /Users/jonathan/github/nida-institute/awesome-biblical-data, a public repo, as a JSON file. If we need to improve the format there, we should, but that's where we should maintain this list, at least for freely licensed resources.  Issue: what about resources that are not freely licensed?

### What `resources.json` has, and what it does not

Read on 2026-08-29: **65 entries**, each with `id`, `name`, `category`, `description`, `formats`,
`license`, `github`, `url`, `acquire` (shell commands) and `notes`. The nine relevant here are
`sblgnt`, `bibleaquifer-sblgnt`, `macula-hebrew`, `bibleaquifer-wlc`, `macula-greek-nt`,
`morphgnt-sblgnt`, `acai`, `ubs-marble-wlc-index`, `bsb`.

That file answers **"what exists, and how do I get it"**. It does not answer **"how does this
engine read it"** — which file inside the clone carries the text, which backend reads that shape
(`tsv`, `tei`, `usfm`), which versification scheme the numbering is in, which canon it covers.
Those four facts are exactly what #217 is missing, and they are what a human hand-typed into the
three files in `~/.sp/editions/`.

**A second copy already exists and should go.** `download_data.CATALOG` in `src/llmflow/download_data.py`
lists four resources — `macula-greek`, `macula-hebrew`, `berean-usx`, `acai` — with repo, branch,
licence and size. That is a smaller, drifting copy of `resources.json`, and its `berean-usx` entry
is the one pointing at a 404 (#201). Whatever shape this takes, sp should read the public catalog
rather than keep its own list.

**=> D5. Where do the four engine-facing facts live?** (a) An optional block added to entries in
`resources.json`, so one declaration serves both — but it couples a general-purpose public catalog
to this engine's backend names. (b) A binding file in sp, keyed by `resources.json` id, holding
only the read facts — two files, but each owns what it knows. *Recommendation: (a), with the block
named for what it describes rather than for sp, so another consumer can use it.*

=>

### "Optional block" was vague. Here is what it means concretely

**Is it rendered into the Markdown?** As things stand, **no** — and by omission rather than by
design. `scripts/generate_readme.py` reads exactly `name`, `description`, `license`, `formats`,
and `github`/`url`/`acquire` (or a hand-written `get_it` override). `build_sections` touches
nothing else, so any key added to an entry sits in `resources.json`, is ignored by the generator,
and leaves `README.md` byte-identical.

That is a property of the current script, not a decision, so it is worth making one.

**=> D5a. Should any of it reach the README?** (a) Nothing — the block is machine-facing, and a
column of `tsv` / `org` is noise for the human reading a curated list. (b) One marker per row —
"readable by Scripture Pipelines", or a format-neutral phrasing — because *"can a tool read this
directly, or must I write a parser"* is a real question a reader of this catalog has. (c) The
whole block. *Recommendation: (b), one marker, phrased for any tool rather than for sp.*

=>

### The harder half: shape versus state

The four facts I proposed — which file inside the clone, which backend shape, which versification
scheme, which canon — share a property. They are **facts about how the resource is built**, and
they change only when the resource is restructured. A central catalog can hold them safely,
because a stale entry means a resource moved a file, which is loud and rare.

There is a second kind of fact, and it must not go in the same place. **State** — which books have
been reviewed, when, what is usable, what is superseded — changes whenever the maintainer works.
That is the exact case worked through with `discourse-flow` on 2026-08-27, and both sides reached
the same conclusion in the same words. Their side:

> *"a list in our repository naming which of your files are usable is a second source of truth
> about your data, and the first time you review a fifth book and we do not notice, we will tell
> consumers a reviewed file is unreviewed — authoritatively, and wrongly."*

with the agreed shape being an ordered scale — `generated < draft < reviewed < approved`, with
`superseded` and `withdrawn` off-scale — held **in the resource's own repository**, and with
`approved` reserved to a human because a session there is barred from declaring its own output
fit for use.

**So the rule this design should adopt:** `resources.json` carries **shape, never state**. Where a
resource has state worth knowing, its entry carries a *pointer* — the path, inside the resource,
to the manifest that declares it — and the engine reads that manifest at use time and never copies
it. One source of truth per fact, and a maintainer who reviews a fifth book does not need a
release from us for consumers to see it.

That also answers what the block is *for*. It is not a description of the resource; it is the
binding that lets a tool open it. Shape belongs to whoever packaged the resource; state belongs to
whoever maintains it; opinion belongs to neither and stays out.

**One thing I could not verify.** The 2026-08-27 exchange describes the usable-book list as being
held in our resource catalog "as a stopgap". I searched `data/`, `utils/scripture.py` and
`utils/discourse.py` and found no such list, so it appears to have been agreed rather than built.
Worth confirming before this design assumes either way.

**Non-free resources — your own question, and I think your Paratext note in §4 answers it.**
A public catalog can only list what is publicly available, so a non-free resource is never a
catalog entry. It reaches the engine the other way: the user registers it from a local path or a
Paratext project, having already established their own right to read it. That makes two entry
points, not two systems — the catalog fills in the facts when it knows them, and the user supplies
them when it does not.

**Then three thin things, none of them clever:**

| | |
|---|---|
| `sp editions list` | every known edition, and for each: registered, available (dataset present, not registered), or absent (dataset not downloaded) |
| `sp editions add <ID>` | writes `~/.sp/editions/<ID>.yaml` from the catalog, resolving the path against the store's data directory rather than a human typing one |
| `sp doctor` | grows an editions group: how many registered, which registered ones now point at a path that does not exist |

**And the portability fix:** a registered edition records `dataset:` and a dataset-relative
`path:`, resolved when it is read. No absolute path is written into the store at all, so the file
is the same on every machine. An entry carrying an absolute `path:` keeps working unchanged —
that is how every existing registration is written, and they are the Captain's.

## 3. Decisions

**=> D1. Does `sp editions add` download the dataset if it is missing?** Macula Hebrew is ~400MB.
The alternative is that `add` registers what is present and, when the dataset is absent, prints the
exact `sp download-data macula-hebrew` command and stops. *Recommendation: register-only by
default, `--download` to fetch.* A large network fetch is the kind of act this project asks a human
to authorize; the same reasoning as never running `sp run` unasked.

=> That complicates the interface.  With good Internet connectivity, downloading 400MB is pretty fast and free for most users.  In places where they pay by the byte, though, this is a real concern. Still, it will have to be downloaded sometime before use.  Explain how you think a two step approach simplifies the user's life or makes the user happier.

### It does not, and the recommendation was wrong

Asked directly, the honest answer is that a two-step flow makes no user happier. The argument
against it is the issue this document exists for.

`sp editions add WLC` is a request to make WLC usable. Downloading the text is not a surprise
consequence of that request, it is the request. A mode that registers an edition and leaves the
data absent produces precisely the failure #217 reports: a command reports success, and the
pipeline fails later, deep in execution, having linted clean. Building that state deliberately,
after filing an issue about arriving in it accidentally, is not a defensible design.

The metered-connection concern is real but it is a minority, and it is served better by a flag
than by a second command: everyone else pays nothing for `--no-download`, whereas a register-only
default charges every user an extra step to protect a few. The flag also covers the offline and
scripted-setup cases, which a second command does not.

**So: `sp editions add <ID>` downloads by default.** Before fetching it prints the dataset name,
its size and its licence, and it is skipped when the data is already present. `--no-download`
registers against a path that is not there yet and says so plainly — one line stating the edition
will not resolve until the dataset is fetched, and the command that fetches it.

The size figure comes from the catalog rather than a HEAD request, so the announcement costs no
network round-trip and works offline.

**=> D2. Do registered editions become dataset-relative?** `dataset: macula-hebrew` plus
`path: WLC/tsv/macula-hebrew.tsv`, resolved at read time against `~/.sp/data/`. *Recommendation:
yes — it is the literal complaint in #217, and it is what makes an edition file portable between
machines.* Absolute paths continue to be honoured, so nothing already registered changes.

=>  Yes.  I do need to be able to use the absolute paths on my machine - I am the maintainer for quite a few of these resources - so that must continue to work.  A few of our users may also be maintainers of resources we or they use.  But that's a minority of users.

**=> D3. What happens to BSB?** It is the one edition of this project's three with no working
catalog source: it is registered here from a local clone of `usfm-bible/examples.bsb` that carries
an unmerged patch, and the catalog's `berean-usx` entry points at a 404 (#201). Options: (a) fix
the source as part of this work, (b) ship the catalog with WLC and SBLGNT and leave BSB
hand-registered, naming the reason in the catalog so it is not mistaken for an oversight.
*Recommendation: (b), and let #201 close the gap on its own terms.*

=>  I agree.

**=> D4. Does `sp init` register editions automatically when their dataset is already present?**
Or is registration always an explicit act? *Recommendation: no auto-registration; `sp doctor`
reports what is available and unregistered, and the user runs one command.* Registering an edition
decides which text a pipeline reads, and that is not a setup detail.

=>   Discuss.  When does this case arise, and why?

### When it arises — and it is narrower than it looks

The case is: a dataset is present in `~/.sp/data/`, and no edition file names it. It arises in
four ways, and only the first is common.

1. **The user ran `sp download-data macula-hebrew` directly**, because that is the command the
   documentation and the error messages point at today. The data lands; nothing registers it.
2. **A second project on a machine that already has the data** — though note editions live in
   `~/.sp/editions/`, which is machine-wide, so if the first project registered WLC the second
   already sees it. This case only survives if nothing ever registered it.
3. **`~/.sp` was rebuilt** — restored, relocated via `$SP_HOME`, or cleared — while `~/.sp/data/`
   survived or was copied across.
4. **The data was placed by hand**, which is how several of these arrive for a maintainer.

So after the first registration on a machine, the case stops arising for every later project. It
is a first-run condition, not a recurring one.

**That is the argument against auto-registration.** Registering an edition decides which text a
pipeline reads. Doing it silently, from a project-scoped command, writes machine-wide state that
every other project on the machine then inherits — and the user who typed `sp init` in one
repository did not ask for that. With `add` downloading by default (D1), the remedy is a single
command, so nothing is saved by guessing.

**Recommendation stands, with the reason now concrete:** no auto-registration. `sp doctor` reports
each known edition as registered, available (data present, not registered) or absent, and prints
the one command for the available ones. `sp init` says nothing about editions at all.

**A smaller one, for the same pass:** the `EditionNotRegistered` message says *"Register one with
`sp registry`"*, which is not true of any existing subcommand. It becomes `sp editions add <ID>`
if D1–D4 land as proposed. No decision needed unless the command should live under `sp registry`
instead.

=> Discuss naming here.  we will eventually support all kinds of resources from Awesome Bible Resources. Registry, resources, naming ... we need naming that is clear but accurate and covers the range of resources we are planning.

### Three words are in play, and they name three different things

The vocabulary is currently doing three jobs with words that overlap, which is why the error
message could name a command that cannot do the job.

| word | what it actually names today |
|---|---|
| **registry** | the store: `~/.sp/`, and the `sp registry` command that reports on projects, datasets, databases and ai-context files. A **place**, not a kind of thing |
| **data / dataset** | a corpus as it sits on disk: `macula-hebrew`, a directory of files. What `sp download-data` fetches |
| **edition** | a text the engine can read, addressed by reference: `WLC`. What a pipeline names |

The distinction that must survive any renaming is the second against the third, because it is the
one #217 tripped over: **having the data is not the same as having something the engine can read.**
`macula-hebrew` is one dataset that carries at least two readable things (the WLC text, and its
morphology); `WLC` is one of them.

**Where "edition" runs out.** It is the right word for a scripture text and the wrong one for
most of what `resources.json` holds. ACAI is entity annotation; MARBLE is a semantic-domain index;
Levinsohn's features are discourse annotation. None of those is an edition of anything, and
`sp editions add acai` would be a lie in the interface.

Three candidate shapes:

- **(a) `sp resource add <id>` / `list`** — one verb surface for everything, the kind carried in
  the catalog entry rather than the command name. Matches the public catalog's own word, extends
  to every category in it, and leaves `sp registry` meaning what it means: the store.
  Cost: `~/.sp/editions/` becomes `~/.sp/resources/`, a migration.
- **(b) `sp editions add <ID>` now, `sp resources` later** — smaller today, but it ends with two
  vocabularies for one act, which `one-design` exists to prevent.
- **(c) `sp registry add edition WLC`** — keeps the error message true without changing it, but
  overloads "registry" from a place into a verb surface, and reads as a database operation rather
  than as acquiring something.

*Recommendation: (a).* The range you have named is wider than editions, the catalog already calls
them resources, and doing it once now is cheaper than migrating a released command later.

**=> D6. Which naming?** (a) `sp resource`, (b) `sp editions` now and rename later, (c) under
`sp registry`. And if (a): does `~/.sp/editions/` move to `~/.sp/resources/` in this change, or
stay put with the new command reading it?

=>

**Ruled in conversation, 2026-08-29.** The Captain, on (a) and on the directory moving with it:
*"a rename is not a cost. Let's do it this way."*

So: `sp resource add|list`, and `~/.sp/editions/` becomes `~/.sp/resources/` in this change rather
than later. `sp registry` keeps its present meaning — the store and what it reports. The
`EditionNotRegistered` message becomes `sp resource add <ID>`, and the exception class is renamed
with it, since "edition" is no longer the word for what is missing.

Existing `~/.sp/editions/*.yaml` files are read from the new location after the move; the move
itself is a `sp doctor` repair rather than something a user does by hand, so a machine that has
the old directory is carried across without being told to move files.

## 4. Not in scope

- **Fetching editions we do not already list in `download-data`'s catalog.** A new source is a
  licensing question before it is an engineering one.
  
  => exception: if I have access to a resource in my Paratext project, that means I have already proven to Paratext that I have a right to read that resource. And of course, my own local repositories are also fair game and my responsibility for handling licensing.

  ### So there are two entry points, and only one of them consults a catalog

  That ruling moves local registration **into** scope, and it is what answers the non-free
  question in §2. Registering from a path the user already has is not a licensing decision the
  engine gets to make — Paratext has already made it, or the user owns the repository.

  - **From the catalog:** `sp resource add WLC` — identity, licence, source and the read facts all
    come from the declaration; the user types an id.
  - **From a local path:** the user names the path and the facts the catalog would have supplied.
    A Paratext project supplies most of them itself — `Settings.xml` carries the versification and
    the books present — so that form should ask for as little as possible.

  The engine gates neither on licence. It records what it was told, and the catalog's `license`
  field travels into the registration so a later reader can see the terms without going back to
  the catalog.
  
- **#201**, the stale `berean-usx` URL and the absent dataset-version checking. Related, filed,
  and separable.
  
- **Changing how an edition is read.** `resolve_edition` and the backends are unaffected except
  for resolving a dataset-relative path.

## 5. What it costs

Small, and mostly declaration. The catalog is one JSON file; `sp editions` is a subcommand with
three verbs over `load_registry_editions` and `download_data.CATALOG`, both of which exist; the
doctor group follows the pattern of the versification group it sits beside. The test surface is
the catalog's agreement with `download_data.CATALOG`, path resolution with and without a dataset,
and a doctor report on a registered edition whose path has gone away.
