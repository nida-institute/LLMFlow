# BaseX collections: naming, and how a corpus is loaded

**Status:** proposal, awaiting the Captain on §8. Nothing is built.
**Issues:** #38 (collection naming), #52 (`--from-git` loading), #49 (`type: basex` step),
and **`nida-institute/awesome-biblical-data#5`, which blocks the rest** — see §8 item 0.

**Ruled by the Captain during design:**

1. **Names come from the catalog**, `data/resources.json`, not from a scheme the engine constructs.
2. **Only declared subtrees are loaded** — not a repository root, filtered.
3. **Naming is decided where the subtree is declared**, and the relationship between a meaningful
   name and a directory structure **needs human judgment**: the catalog maintainer holds that role.
4. **One identifier per repository, with a set of resources within it** — §4.1.
5. **The registry carries a SHA and a load date** — §5.1, where both fields already exist.

Those rulings retire the argument the two issues were stuck on. #38 proposed a semantic taxonomy
(`macula/gnt-lowfat`), #52 a provenance name (`github/Clear-Bible/macula-greek/lowfat`), and each
called itself canonical. Neither is needed: a catalog entry already carries a chosen name *and* its
provenance, so the engine reads rather than derives.

**Superseded during this design, recorded so it is not re-derived:** a scheme building database
names as `github.Clear-Bible.macula-greek`, with the repository as the database and the repo's own
directories as resource paths. It works, and §3 shows why it is still the wrong answer.

---

## 1. The problem is real and already advanced

The Captain's BaseX store holds **90 databases**, with the same corpus repeatedly under names that
say neither what it is nor where it came from:

```
SBLGNT-lowfat                          27 res   /Clear/macula-greek/SBLGNT/lowfat/
macula-sblgnt-lowfat                   28 res   /Clear/macula-greek/SBLGNT/lowfat/   ← same path
sblgntlowfat                            1 res   …/lowfat/sblgntlowfat.xml
sblgnt-lowfat-biblicalhumanities-2013  29 res   /biblicalhumanities/…                ← other repo
```

`trees-groves-skeleton` exists as `-raw`, `-massaged`, `-prepared` and plain, beside `trees-oshb`
and `trees-oshb-good`. This session added two more before dropping them.

## 2. What BaseX does, measured

**A database name may not contain `/`.** `CHECK github/Clear-Bible/test-name` creates a database
called plain `test-name` — the path is stripped and only the last segment survives, silently.

**`CREATE DB` preserves nested directories as resource paths, and `collection()` addresses them.**
Loading a directory holding `lowfat/one.xml` and `nodes/two.xml`:

```
collection('pathtest/lowfat') -> 1
collection('pathtest/nodes')  -> 1
collection('pathtest')        -> 2
```

So a subtree needs no encoding into a name; a path inside a database is already a path. This is
what a declared subtree loads into.

## 3. Why a directory layout cannot supply the names

A repository *does* get one identifier — §4.1 rules exactly that. What it cannot supply is the
**name a collection is addressed by**, because that is not derivable from its layout.

The superseded scheme took the repository as the database and its directories as the path, giving
`collection('macula-greek/SBLGNT/lowfat')` — the three things the Captain asked a title to tell
him, with nothing invented. It reads well for that corpus because `macula-greek`'s own layout is
`<edition>/<representation>`.

It fails on the catalog as it actually is:

```
repositories claimed by more than one id:
  Clear-Bible/macula-greek       <-  macula-greek-nt, gbi-lowfat
  biblicalhumanities/Nestle1904  <-  nestle1904, morphgnt-nestle1904
  morphgnt/sblgnt                <-  sblgnt, morphgnt-sblgnt
  ubsicap/ubs-open-license       <-  ubs-sdbh, ubs-sdgnt, ubs-thematic-lexicons,
                                     ubs-parallel-passages, ubs-hottp,
                                     ubs-marble-wlc-index, ubs-bible-routes
```

**Seven ids for one repository.** The repository is the unit of *acquisition*; the corpus inside it
is the unit of *naming*. And no derivation rule could have produced those seven names — a person
decided them, knowing what the corpora are. That is the Captain's ruling stated as evidence: the
mapping from directory structure to meaningful name is editorial, and the catalog maintainer holds
it.

So both rulings hold together: **one identifier per repository** (§4.1), because that is what gets
cloned, and **the names come from the catalog** (§4), because a layout cannot state them.

## 4. The shape

A catalog entry declares its loadable subtrees, and each declares the name it loads under:

```json
{
  "id": "macula-greek-nt",
  "github": "https://github.com/Clear-Bible/macula-greek",
  "provides": [
    { "id": "SBLGNT", "kind": "tsv", "path": "SBLGNT/tsv/macula-greek-SBLGNT.tsv" },
    { "id": "SBLGNT/lowfat", "kind": "xml", "path": "SBLGNT/lowfat" }
  ]
}
```

A pipeline names what it wants; the engine resolves it and the BaseX database name is never typed:

```yaml
- type: basex
  database: macula-greek-nt/SBLGNT/lowfat
```

Because nobody types the derived name, **verbosity there costs nothing** — it can carry every
distinguishing component. And because the visible name is declared, a collision between two
sources is resolved by the person who knows which is which, rather than by the engine mangling
strings.

**This changes the `type: basex` step's contract**: `database:` becomes a catalog id rather than a
literal BaseX database name, which is passed straight through today. A pipeline naming a raw
database must either keep working or be told to register it — see §7.

### 4.1 One identifier per repository — ruled, and what must survive the merge

**Ruled: one identifier per repository, with a set of resources within it.** The repository is the
unit of *acquisition* — cloned once — while a corpus is the unit of identity, licence and naming.
Today `sp resource download macula-greek-nt` and `sp resource download gbi-lowfat` would fetch the
same repository twice.

The four multiply-claimed repositories are the argument for it. **But they also carry the thing
that must not be merged away:**

```
Clear-Bible/macula-greek         CC BY 4.0             vs  Open
biblicalhumanities/Nestle1904    Public Domain         vs  CC BY 4.0
morphgnt/sblgnt                  Custom (sblgnt.com)   vs  CC BY-SA 3.0
ubsicap/ubs-open-license         Open                  vs  CC BY-SA 4.0
```

**Licences differ inside every one of them**, and not by accident: the SBLGNT *text* carries its
publisher's licence while morphgnt's *annotations* carry another. That is a legal distinction
somebody recorded deliberately, and a repository is not the unit of licensing.

The merge is safe anyway, because the code already anticipated it —
`merged.setdefault("license", entry.get("license"))` at `resources.py:146` lets a `provides` entry
declare its own licence and fall back to the entry's:

```json
{ "id": "macula-greek",
  "github": "https://github.com/Clear-Bible/macula-greek",
  "license": "CC BY 4.0",
  "provides": [
    { "id": "SBLGNT",        "kind": "tsv", "path": "SBLGNT/tsv/macula-greek-SBLGNT.tsv" },
    { "id": "SBLGNT/lowfat", "kind": "xml", "path": "SBLGNT/lowfat", "license": "Open" }
  ] }
```

**Two cautions.**

`provides[].id` is a **global flat namespace**: `resources.py:151` is
`out[str(item["id"])] = merged`, so a second entry providing the same id overwrites the first
silently *at read time*. It is caught at authorship, though — `validate_resources.py:83` reports
*"provides id 'X' appears N times; it must be unique"* — which is the right place for the guard.
Merging repositories therefore needs their children to be distinct, and the validator will say so.

**Renaming a top-level id breaks every reference to it** — `gbi-lowfat`, `morphgnt-sblgnt`, the
seven `ubs-*`. An alias field or a deprecation window, rather than a silent rename.

### 4.2 A worked example: the Tyndale Bible Dictionary

Looked at directly, because the abstract rule hid where the boundary really falls.

The catalog entry `tyndale-open-bible-dic` describes a zip from the publisher. What is registered
on this machine is something else — a **git repository** carrying the data plus the tooling that
built it:

```
git@github.com:Clear-Bible/TyndaleBibleDictionary.git

Tyndale/Articles/   A.xml … Z.xml        ← the dictionary itself
Tyndale/Maps/       Maps.xml
Tyndale/Pictures/   Pictures.xml
Logos/              TYNBIBDCT-Content.xml  ← same content, Logos export format
plaintext/          A.tsv … Z.tsv          ← derived TSV
xslt/  src/  pyproject.toml  poetry.lock   ← tooling, not data
```

So: acquisition id `github.com/Clear-Bible/TyndaleBibleDictionary`, derived; subtrees
`Tyndale/Articles`, `Logos`, `plaintext`, from the repository's own paths, with three tooling
directories to leave out.

**What this shows about deriving names from a URL.** The download URL is

```
tyndaleopenresources.com/wp-content/themes/tyndale-openresources/files/TyndaleOpenBibleDictionary.zip
```

which yields one name — `TyndaleOpenBibleDictionary` — and **no way to reach `Tyndale/Articles`
versus `Logos` versus `plaintext`**, because a zip's internal structure is not in its URL and
cannot be. One fetch, one string; three corpora inside it.

So the boundary is sharper than "git versus download": **the URL derives the acquisition id in
both cases, and the subtree names come from the layout plus a person in both cases.** Git is not
special because it is git — it is special because the layout can be seen before fetching.

The filename stem is worth keeping, though: `TyndaleOpenBibleDictionary` and
`tyndale_open-studynotes` are both meaningful, and discarding `wp-content/themes/…/files/` loses
nothing. For a download, **host plus filename stem**, intermediate path dropped. The two would be
stylistically inconsistent — CamelCase against snake-kebab, as their publishers named them — but
accurate and derived.

**One thing the example turned up that no rule catches.** This corpus has two ids in two stores for
the same content from different sources: `tyndale-open-bible-dic` in the catalog (the publisher's
zip) and `TyndaleBibleDictionary` in the registry (Clear-Bible's repo, hand-registered). Neither is
wrong, nothing relates them, and a no-rename test would not notice.

## 5. Sources that are not git repositories

Most of the catalog is not a git clone:

```
github only:  37        url only:  17        both:  14        neither:  2
```

**17 entries have no repository at all** — a URL and nothing else — and for those, `acquire` is
prose written for a person:

```
codex-sinaiticus   "Download from https://codexsinaiticus.org/…/transcription_download.aspx"
catss              "See user agreement and request access from http://ccat.sas.upenn.edu/…"
westcott-hort      "Download from http://scrolltag.com/westcott_and_hort.html"
```

All of them declare `provides: 0`. So acquisition is manual, and the local layout is undeclared.

This is the strongest evidence for the ruling. **No derivation scheme could name these at all**:
#52's `github/<org>/<repo>` has no inputs, and its `local/<dirname>` fallback would name a corpus
after whatever an archive happened to unpack to. Only a declaration can name them, and only a
person can write it — the layout of a downloaded archive is not knowable until somebody unpacks it
and looks.

**Two consequences for the shape in §4.**

`provides[].path` is relative to a **local root**, and what that root is depends on how the
resource was acquired: a clone's root is the repository, an archive's is wherever it unpacked.
The catalog needs to say which, or a path means two things.

**An archive's top-level directory is often versioned** — `corpus-1.2.3/` — so a `provides[].path`
written against one release breaks on the next, silently finding nothing. Either the loader strips
a single top-level directory, or the catalog declares the root separately from the subtree, or
every path carries a version that goes stale. This does not arise for clones, which is why it is
easy to miss.

### 5.1 Which version — ruled, and already built

**Ruled by the Captain: the registry carries a SHA and a load date.** It is not new work; it is a
field nobody fills.

`~/.sp/datasets/*.yaml` is the machine-specific record, written by `sp resource add`:

```yaml
downloaded: '2026-03-27T11:45:28.285354'
path: /Users/jonathan/github/Clear/macula-hebrew
version: unknown
```

`downloaded:` is the load date and is written automatically (`registry.py:126`). `version:` is a
caller-supplied parameter (`registry.py:124`) that **nothing computes**, so **22 of the store's 24
datasets say `unknown`.** And `sp doctor` already reports the gap — *"Resources: all N present, M
of unknown version"* (`doctor.py:469`). The engine has been saying this all along.

**This is also the right store, and it settles a tension.** `registrations/*.yaml` opens with
*"The path is relative to the dataset, so this file means the same thing on every machine"* — it is
deliberately portable, so that a registration can be shared. A SHA and a load date are facts about
*this* machine's copy, and they belong in `datasets/`, which already holds an absolute path.

**One distinction to keep, or the field cannot be trusted.** An **observed** version — what I have
— and a **pinned** version — what this must be — are different claims. `version:` in `datasets/`
is observed. If reproducibility later wants a pin ("this analysis was produced against `4a1c9f2`"),
that is a second field in the portable store under a different name. Recording one and reading it
as the other is how a record comes to lie.

#### The case that makes this concrete

The store holds `sblgnt-lowfat-biblicalhumanities-2013`, 29 resources from
`biblicalhumanities/greek-new-testament/syntax-trees/sblgnt-lowfat`. Those trees were donated to
Clear, which merged into Biblica; the upstream repository now declares itself obsolete and points
at the maintained version, which is the same maintainer's.

**The local checkout is at a commit from 2020-05-15**, so it predates that notice and its README
says nothing about it. Nothing on this machine can tell that the corpus was superseded, and the
registry would say `version: unknown`.

So the only surviving hint that the database is old is the **`2013` somebody typed into its name** —
a year hand-written into an identifier because the field for it was empty. That is the whole
argument for this section, in one artifact.

**Supersession itself is not ours to record**, and that was already ruled before this design:

> *"State is deliberately absent. Which books have been reviewed, what is superseded, what is
> usable — that changes whenever a maintainer works, and a copy here would eventually tell a
> consumer that a reviewed file is unreviewed, authoritatively and wrongly. Where a resource
> declares its own state, its entry points at the manifest and the reader goes there."*
> — `resources.py`, module docstring

So no `superseded_by` field. What the engine *can* do is record the SHA and let `sp doctor` say
this copy is from 2020 — which it half does already, reporting *"N of unknown version"*.
The catalog, incidentally, never listed these trees; `gbi-lowfat` points at the maintained line.

## 6. How a corpus is loaded — the part that is wrong today

`load_db.py:66` is the whole loader:

```python
subprocess.run(["basex", "-c", f"CREATE DB {db_name} {source}"], ...)
```

**No options are set.** Defaults, from `SHOW OPTIONS`:

| option | default | consequence |
|---|---|---|
| `INTPARSE` | `false` | the JAXP parser, which **fails** on Luke — element depth 101 against a limit of 100 |
| `XINCLUDE` | `false` | xincludes silently unresolved |
| `DIACRITICS` | `false` | the full-text index folds accents and pointing away |
| `CASESENS` | `false` | case folded |
| `TOKENINDEX` | `false` | no token index |
| `FTINDEX` | `false` | no full-text index |
| `UPDINDEX` | `false` | indexes go stale on later adds |
| `TEXTINDEX`, `ATTRINDEX` | `true` | already on |
| `STRIPWS` | `false` | already right — Macula's `after` carries the whitespace |

**`INTPARSE` is a correctness bug, not tuning.** Loading `macula-greek/SBLGNT/lowfat` with the
default parser fails on Luke; this session hit it directly.

**`DIACRITICS` is the one that would corrupt scholarship quietly.** With it off, a full-text search
cannot distinguish **τίς** (interrogative *who?*) from **τις** (indefinite *someone*) — they differ
only by accent — nor pointed Hebrew from unpointed. The index answers, and answers wrongly.

Proposed:

```
SET INTPARSE   true
SET XINCLUDE   true
SET DIACRITICS true
SET CASESENS   true
SET TOKENINDEX true
SET FTINDEX    true
SET UPDINDEX   true
```

**A separate defect in the same eight lines:** `f"CREATE DB {db_name} {source}"` interpolates
unquoted, so **any path containing a space fails.** The Captain's Paratext projects live under
`Paratext 9 Projects/`, so no Paratext corpus can load through this driver today.

**Loading is `CREATE` then `ADD`.** A second declared subtree of the same entry must add to the
database, not recreate it. Today the driver only does `CREATE`, with `--force` to drop first, so a
second load destroys the first.

## 7. Where the rule has to live — not in this repository

**The catalog is not maintained here.** `resources.json` is *"maintained in
`nida-institute/awesome-biblical-data` and vendored here so nothing needs a network"*
(`resources.py` docstring). The vendored copy is currently identical to upstream, so the vendoring
is clean — but it means every naming decision in this document is executed in **another repository,
by an LLM**, because that is how the Captain maintains it.

So the discipline belongs in that repository's AI context. Otherwise the alternative is validation
tooling here, checking work that a maintainer should simply have been told how to do.

`resources.json` is also the **single source for every other format** — `README.md` is generated
from it by `scripts/generate_readme.py`, run by a pre-commit hook. So a field added to the JSON is
the one edit; the markdown follows.

**There is already a validator, and it is stricter than the documentation.**
`scripts/validate_resources.py` enforces `KNOWN_FIELDS` (rejecting anything outside it as a typo),
required fields, a slug pattern for ids, relative `provides[].path`, and uniqueness of both
top-level and `provides` ids. The `CLAUDE.md` schema table documents ten fields; the validator knows
twelve, including `provides` and `download`. So the *authoring* guard exists and the *instructions*
lag it.

### 7.1 Two constraints this design must satisfy or change

**`provides` currently requires scripture-text fields.**
`PROVIDES_REQUIRED = ("id", "name", "kind", "path", "versification", "canon", "language")`. Despite
`resources.py`'s general framing — *"which file inside the download, which backend reads that
shape"* — a `provides` entry cannot today describe `Tyndale/Articles`, which is a dictionary, or
`SBLGNT/lowfat`, which is a treebank: neither has a versification or a canon. So §4's shape needs
those three fields to become conditional on `kind`, or non-scripture subtrees need their own block.
**This is the one place the design meets a hard stop in existing code.**

**Top-level ids must be lower-case slugs.** `ID_PATTERN = ^[a-z0-9][a-z0-9-]*$`, enforced at
`validate_resources.py:57`. So a URL-derived id cannot be `github.com/Clear-Bible/macula-greek` —
no dots, no slashes. It would have to be mangled to `github-com-clear-bible-macula-greek`, which is
ugly and no longer reversible. That is an argument for the no-rename guarantee over derivation:
permanence without disfiguring the id, and it covers all 70 entries rather than the 51 with a
repository.

### 7.2 What the catalog's AI context needs to say

- **`provides` is how a resource is opened** — which file or subtree, which backend reads that
  shape, and, for a scripture text, how it is numbered. Absent from the schema table today.
- **`download` is a direct file URL**, distinct from `url`, which is a landing page for a human.
  Absent from the schema table today.
- **One entry per repository**, corpora as `provides` entries (§4.1) — and a `provides` entry may
  carry its own `license`, because licences differ *within* four of the shipped repositories.
- **An existing `id` is never renamed** — added, or deprecated with an alias.
- **State stays out**: no `superseded_by`, no review status. Point at the resource's own manifest.

**Not written by this session.** That file is the Captain's, in another repository, and this
document only records what it would have to contain.

## 8. Decisions for the Captain

0. **`provides` cannot describe a non-scripture subtree today** — §7.1. `versification`, `canon`
   and `language` are required of every entry, so a treebank or a dictionary cannot be declared.
   **Raised upstream as `nida-institute/awesome-biblical-data#5`**, where the schema and its
   validator live; deliberately not designed there or here. It blocks everything else in this
   document, so nothing below it can be built first.
1. **The catalog is 4% covered for this purpose** — 3 of 70 entries have `provides`, 3 subtree
   entries in total. Extending it is the maintainer's editorial work, not the engine's. Is that a
   task to schedule, or filled in as corpora are needed?
2. **`gbi-lowfat`, and the other three multiply-claimed repositories.** Is lowfat a `provides` entry
   of `macula-greek-nt`, or is `gbi-lowfat` right to stay separate because the treebank has its own
   provenance and licensing? The answer sets the pattern for the other three, including the seven
   ids over `ubs-open-license`.
3. **Version — ruled: a SHA and a load date in the registry.** Both fields already exist and are
   in the right store; see §5.1. What remains is what fills `version:` for a resource that is not
   a git checkout.
4. **`LANG`** — BaseX defaults to `English`, driving tokenisation and stemming. Greek and Hebrew
   corpora are neither. *Recommended: declare per subtree; a Greek corpus stemmed as English is
   worse than unstemmed.*
5. **`FTINDEX` by default, or declared?** It is the expensive one, and a treebank queried by
   `xml:id` never needs it while a lexicon does. *Recommended: declared per subtree, default off.*
6. **A raw BaseX name in `database:`** — keep working, or refuse and require registration? §4.
7. **The local root for a non-git source**, and whether the loader strips an archive's versioned
   top-level directory — §5. *Recommended: the catalog declares the root, and the loader strips a
   single top-level directory when the archive has exactly one*, since that is the near-universal
   shape and a declared root covers the rest.

## 9. Not in scope

Incremental reload, progress reporting on large repositories, and non-XML file types — all raised
in #52 under "what needs to be figured out", none blocked by the naming ruling.
