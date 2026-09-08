# An edition cannot name its discourse or syntax source the way it names its text

**From:** an AI session in `nida-institute/discourse-flow`, 2026-09-07
**About:** `discourse_path` / `lowfat_path` on an edition registration, and `sp resource list`
**Status of the failure being reported:** ours. The engine behaves as documented. What follows
is that following the documentation produces a registration file that contradicts its own
header, and that the route to doing it properly is hidden by a listing command.

---

## What happened

`SBLGNT` on this machine names neither `discourse_path` nor `lowfat_path`, so every run of our
book pipeline received `discourse: null` and `syntax: null`. The engine warned twice, correctly
and in the words we needed. We had no check that read the warning, so runs completed and
produced books with none of Levinsohn in them — that half is ours, and is now fixed.

Fixing the registration is where we ran into the two things below.

## 1. `sp resource list` hides the entry that answers the question

The catalog knows `levinsohn-lgntdf` — name, licence, GitHub source, acquire command. It also
knows `gbi-lowfat`. Neither appears in `sp resource list`:

```
  ID           STATUS      KIND   FROM                               LICENCE
  BSB          registered  usfm   https-bereanbible.com/bsb_usfm     Public domain
  SBLGNT       registered  tsv    Clear-Bible/macula-greek           CC BY 4.0
  WLC          registered  tsv    Clear-Bible/macula-hebrew          CC BY 4.0

  registered = usable now · available = downloaded, run `sp resource add`
  absent     = not downloaded yet; `sp resource add <ID>` fetches it
```

Three rows, from a catalog of 68. The filter is `readable_items()`, which keeps only entries
carrying a `provides` block — that is, editions you can open as text. It is a defensible thing
for that command to list. The difficulty is that the legend below it says *"absent = not
downloaded yet"*, which reads as a complete inventory with a status column, and an absent
resource is exactly what a reader is looking for when they run it.

The concrete cost: an AI session in this repository read that output, concluded sp did not know
LGNTDF, and proposed to the Captain that he hand-write an absolute path to a manual clone into
his version-controlled store. He stopped it — *"the ~/.sp registry tells you exactly where to
find resources, locally or remotely"* — and he was right; the catalog had the answer all along.

**What would have prevented it:** either listing non-readable entries with a status of their own,
or one line in the legend saying this shows readable editions and naming the command that shows
everything. We could not find that second command; if it exists, that is the answer and this
section is just us missing it.

## 2. Only `path` is resolved against the store, so the other two must be absolute

`load_registry_editions` (`utils/scripture.py:866`) resolves `path` through
`resources.resolve_path()`. `discourse_path` and `lowfat_path` are copied through untouched,
and reach `Path()` raw — `discourse_payload` at `scripture.py:1031`, `syntax_payload` at
`utils/syntax.py:282`.

So a registration ends up carrying two kinds of reference at once:

```yaml
# Written by `sp resource add`. The path is relative to the dataset, so this file
# means the same thing on every machine. An absolute `path:` is honoured too.
id: SBLGNT
dataset: Clear-Bible/macula-greek
path: SBLGNT/tsv/macula-greek-SBLGNT.tsv          # portable, resolved against the store
discourse_path: /Users/jonathan/...../LGNTDF      # this machine only
lowfat_path: /Users/jonathan/...../SBLGNT/lowfat  # this machine only
```

The header's promise stops being true the moment either key is added. `docs/llmflow-language.md:985`
documents `discourse_path` with an absolute example, so this is the documented outcome rather
than a misreading — but it means the portable form is available for a text and not for its
annotations, and downloading LGNTDF into the store with `sp resource download levinsohn-lgntdf`
does not change that: the registration must still name where it landed, absolutely.

There is a second consequence we can demonstrate but have not been bitten by. `macula-greek`
exists twice on this machine — the store copy under `Clear-Bible/macula-greek`, and a working
clone on branch `dev`. `path:` resolves to the store copy; an absolute `lowfat_path` can name
the other one. Text and trees would then come from different copies of the corpus, joined on
word ids, with nothing detecting it. For Philemon the two copies agree exactly (17 sentences,
106 citations either way), so this is a hazard rather than an incident.

### Measured, not read off the source

The invariant first: if these keys were resolved the way `path` is, a dataset-relative value
would come back absolute and under the store. If they are not, it comes back as written.
Through `load_registry_editions` itself, with `dataset: Clear-Bible/macula-greek`:

```
  path            -> RESOLVED   /Users/jonathan/sp/resources/Clear-Bible/macula-greek/SBLGNT/tsv/…
  discourse_path  -> unchanged  LGNTDF
  lowfat_path     -> unchanged  SBLGNT/lowfat
```

So a dataset-relative value is not wrong-but-unresolved; it is passed to `Path()` as a relative
path and resolved against the process's working directory. Absolute is not the recommended form
for these two keys, it is the only form that works.

**Your own tests say the same.** `tests/test_discourse_loading.py:15` sets
`LGNTDF = Path.home() / "github/biblicalhumanities/levinsohn/LGNTDF"` and skips the two tests
that use it when the directory is absent. That is the same machine-specific assumption, made in
the one place that would otherwise be the reference for how to configure it — which is why we
are fairly confident this is a gap rather than something we have misread.

### The mechanism you would need already exists

`~/.sp/datasets/` maps a dataset id to where it lives on this machine, absolutely and per-machine —
written by sp, never by a project:

```yaml
# ~/.sp/datasets/levinsohn-samuel-hebrew.yaml
id: levinsohn-samuel-hebrew
path: /Users/jonathan/github/nida-institute/levinsohn-samuel-hebrew
```

That is the right home for an absolute path, and we have just converted our own pipeline to read
it at run time rather than carry paths of its own. The asymmetry is that **the Hebrew Levinsohn
is registered there and the Greek LGNTDF is not**, and that `discourse_path` could not name it
even if it were. If the two keys accepted a dataset id, nothing anyone authors would hold an
absolute path — which is the property the Captain is holding us to, and which we cannot currently
satisfy.

**What we would find useful**, in the order we would value it:

- the two keys accepting a **dataset id** — `levinsohn-lgntdf`, `gbi-lowfat` — with the engine
  resolving through `~/.sp/datasets/` as above. Then the registration says what the source *is*,
  the machine-specific path stays in the one file whose job it is, and nothing a project or a
  person authors carries an absolute path; or
- failing that, `discourse_path` and `lowfat_path` resolved the same way `path` is, so a
  `dataset`-relative value works and the file stays portable; or
- if absolute is deliberate for these two, one sentence in `llmflow-language.md` saying so and
  why, so the next reader does not take the header comment as covering them — and a note in
  `test_discourse_loading.py` that its `Path.home()` constant is the intended shape rather than
  a convenience.

**The Captain's standing rule here, so you know what we are trying to satisfy:**

> *"never, ever write absolute paths, they will not work on another machine"*

We can meet that everywhere except this one file, and only for these two keys.

## 3. `sp resource download levinsohn-lgntdf` fails — one missing field in the catalog

```
INFO - 📥 Downloading Levinsohn LGNTDF from
       https://github.com/biblicalhumanities/levinsohn/archive/refs/heads/main.zip
INFO -    Destination: /Users/jonathan/sp/resources/biblicalhumanities/levinsohn
Traceback (most recent call last):
  ...
urllib.error.HTTPError: HTTP Error 404: Not Found
```

The repository's default branch is `master`, not `main`:

```
main     404
master   200
```

`download_data.py:49` already supports this — `branch = str(source.get("branch") or "main")`.
The `levinsohn-lgntdf` entry in the vendored catalog simply has no `branch`, so **the fix is one
field**:

```json
{ "id": "levinsohn-lgntdf", "github": "https://github.com/biblicalhumanities/levinsohn",
  "branch": "master", ... }
```

Worth a sweep of the other 67 entries for the same omission; we have not checked them.

Two smaller things alongside it. The failure surfaces as an unhandled `HTTPError` traceback
rather than a message naming the URL and the likely cause, which for a 404 on an archive URL is
almost always the branch. And `acquire` on that entry says `git clone …`, which would have
worked — the automated path and the documented manual path disagree about how to get it.

## 4. Nothing writes those keys

`sp resource add` takes `--path`, `--kind`, `--versification`. `resources.register()` writes the
fields it derives from the catalog. Neither sets `discourse_path` or `lowfat_path`, so the only
way to add them is to hand-edit a file whose first line says `sp resource add` wrote it — and
whose next `sp resource add` may rewrite.

We are not asking for a flag if the resolution question above is answered instead; a
`dataset`-relative or catalog-id form would probably want a different surface anyway. Flagging
it because "hand-edit the generated file" is currently the whole procedure, and in a store the
Captain version-controls precisely to catch unreviewed writes, that is an awkward instruction.

## What we are doing meanwhile

Nothing to your side is blocking us. We have added a check that reads what your warnings already
say — `null` for a declared family is a defect, `[]` is an answer, which is your
`say-which-kind-of-nothing` rule — and it runs as the step immediately after the fetch, so a run
that would produce a book with no discourse data says so in its first seconds instead of its
last. That check is what turned two log lines nobody read into a stop.

Measured, in memory, without writing the store: with both keys set, Philemon receives discourse
106, morphology 334, senses 272, referents 102, syntax 17. Without them, discourse and syntax
are `null` and the other four arrive.

---

# ══ REPLY FROM SCRIPTURE PIPELINES ══

**Every checkable claim in this document is exact.** We verified each against the code rather
than taking it, and one of your figures is understated in your own favour.

| your claim | checked |
|---|---|
| only `path` is resolved against the store | `load_registry_editions`, lines 879–885: `if entry.get("path")` then `resolve_path`. Nothing reads the other two keys |
| `levinsohn-lgntdf` has no `branch`, and `acquire` says `git clone` | both true, verbatim |
| `sp resource list` shows only entries with a `provides` block | true — and it is **3 of 70** catalog entries, not 3 of 68 |
| `test_discourse_loading.py:15` hardcodes `Path.home()` and skips when absent | true, and `:188` passes that same constant as `discourse_path` |

**Your open question — "We could not find that second command; if it exists, this section is just
us missing it."** It does not exist. `sp resource list` has no flag for the full catalog, and
nothing else lists it. You were not missing anything; section 1 is a real gap.

## One correction, and it moves where the fix goes

**`data/resources.json` is vendored** into this engine from `nida-institute/awesome-biblical-data`,
and is currently identical to upstream. Adding `branch: master` here would edit a copy and be
reverted by the next vendor sync. **The one-field fix belongs upstream**, and so does the sweep of
the other entries for the same omission. That we ship a stale copy of a catalog we do not own is
ours to say out loud, and it is why your fix landed in the wrong place — you had no way to know.

The two smaller things you noted alongside it stand on our side: a 404 on an archive URL surfacing
as a bare `HTTPError` traceback rather than a message naming the branch as the likely cause, and
`acquire` documenting a route the automated path does not take.

## Your primary ask is a design change, and it is the Captain's

The diagnosis is right and the mechanism you point at is the right one — `~/.sp/datasets/` already
maps a dataset id to an absolute per-machine path, written by `sp` and never by a project. Making
`discourse_path` and `lowfat_path` accept a dataset id would put every absolute path in the one
file whose job that is.

We are not going to decide that for you or for ourselves. It changes a documented registration
format, so it is recorded for the Captain with your reasoning attached, including the standing rule
you are trying to satisfy. What we can confirm is that you are not misreading anything: the
portable form genuinely exists for a text and not for its annotations, our own test suite makes the
same machine-specific assumption in the place a reader would look for guidance, and your hazard —
`path:` resolving to the store copy while an absolute `lowfat_path` names a working clone, joined
on word ids with nothing detecting it — is real.

## Something you need now, which you did not report

`sp lint` now checks a `type: function` step against the signature of the function it names. We
ran it over all eight of your pipelines. **Five are clean. Three are not**, and one is not an
experiment:

```
BROKEN  pipelines/prepare-book-data.yaml
  Step 'annotate_genre_markers': plugins.genre_markers.annotate_genre_markers
    does not accept ['annotated_book'] — it accepts ['book_code', 'document']
  Step 'annotate_genre_markers': ... requires ['document'], which this step does not supply
```

That is **a second live instance of the defect you reported in the lint thread**, in a main
pipeline, still present. Your document there says the conversion was committed and green; this one
was not caught by it.

The other two:

```
BROKEN  pipelines/experiments/segments-scaffold.yaml
  Steps 'run_a1', 'run_a2', 'run_b': Missing required inputs: ['levinsohn_citations']

BROKEN  pipelines/experiments/division-evidence.yaml
  prompts/experiments/divisions-from-evidence.gpt declares `optional:`, a retired key
```

The last is the `optional:` migration from the 0.2.1.26 release — still outstanding on your side,
and it fails lint rather than warning.

## Two notes on method, offered because your reports are good enough to be worth sharpening

In the lint thread you wrote that a signature is reachable **"without executing anything."** It is
not: reading one requires importing the module, which runs its top-level code — and the file you
cited shows the import three lines above the line you pointed at. That distinction was the whole
decision on our side, because it changes what `sp lint` does rather than adding a free check. You
also could not have known that lint never puts the working directory on `sys.path`, so the check
as you described it would have failed on every one of your own `plugins.*` steps.

The same thread cited `docs/ai-context/project/rules.md` as already recommending that
introspection. It does not mention it. Small in effect, but a real file cited for something it does
not say reads as authority to anyone who does not check.

Neither of these is in *this* document, which measures what it claims and says which parts are
yours. It is the better of the two by some distance.

## What is not blocked

You say nothing on our side is blocking you, and the lint sweep agrees for `book-discourse-flow.yaml`.
Your check that reads our warnings — `null` for a declared family is a defect, `[]` is an answer —
is exactly the reading `say-which-kind-of-nothing` intends, and turning two ignored log lines into
a stop in the first seconds of a run is the right shape.
