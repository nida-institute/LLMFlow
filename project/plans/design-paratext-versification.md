# Paratext versification: a project's own numbering

**Status:** implemented.
**Issue:** #222.

**Ruled by the Captain during design:**

1. **The scheme is identified by the project.** Not a synthetic name — a project name is declared,
   by the people who own the project, and the overlay belongs to exactly one project.
2. **The container reports the project identifier**, meaning *"the versification the project
   specified for this project"* — **whether standard or custom**. One meaning for the field, not a
   scheme name sometimes and a project name others.

---

## 1. The defect

`_paratext_scheme` (`scripture.py:330`) reads `Settings.xml`, finds a versification *number*, and
resolves it to a packaged scheme name. Where the project also carries a `custom.vrs`, it warns and
**returns the numbered scheme anyway** (`scripture.py:350`):

> *"…and also carries a custom.vrs, which this engine does not read. References its overlay changes
> will be wrong."*

So references into such a project land on the wrong verses. The warning is honest, and it is all
the engine does.

## 2. What a `custom.vrs` contains

Measured across every `custom.vrs` on this machine — **66 files** — and cross-checked against a
declaration of the format rather than a reading of the files. `json2vrs.py` in the Copenhagen
specification writes `.vrs` from the JSON scheme, and it emits **four** constructs, one per
scheme field:

```
GEN 1:31 2:25 3:24 … 50:26 END   maxVerses       — every chapter of a book, on one line
-MAT 17:21                       excludedVerses  — a verse the project deliberately lacks
*PSA 3:1,-,a,b                   partialVerses   — a verse published in segments
REV 13:1 = REV 12:18             mappedVerses    — left side the project's, right side org
NEH 7:68-73 = NEH 7:67-72        …and either side may be a range
```

313 chapter-length lines stating 3,515 chapters (39 terminated by the literal `END`), 990
mappings, 280 excluded verses, 58 partial-verse declarations. The file count re-derives with:

```bash
find "$HOME/My Paratext 9 Projects" -maxdepth 2 \( -name custom.vrs -o -name Custom.vrs \) | wc -l
```

Five lexical facts the parser must carry:

- **A mapping's left side may carry a segment letter** — `PSA 3:1a = PSA 3:2`, 200 lines, letters
  `a` through `t` and no `j`. `as_single_verse` and `format_reference` already model a segment.
- **`=` is not reliably surrounded by spaces** — one file omits them.
- **A book code may contain a digit or mixed case** — `S3Y`, `PS2`, `1Sa`. A `.vrs` names books by
  code and never by name, so the code is what it means: `PSS` is Psalms of Solomon, though as a
  *name* it is ambiguous with Psalms and the name resolver refuses it.
- **11 of the 66 files open with a UTF-8 byte order mark**, before the first book code.
- **`END` terminates a chapter-length line** and is not a chapter.

Comments are `#` to end of line, and lines may be indented.

**Chapter lengths cannot be held as a list per book.** Of the 313 chapter-length lines, 103 do not
begin at chapter 1 and 27 name chapters that do not run consecutively — `NUM 6:26 25:18` states
two chapters of thirty-six. A list could not say which chapters went unmentioned, so the overlay
holds them per chapter and folds each onto the base's already-resolved lengths.

Each construct already has a field in the scheme format — `maxVerses`, `excludedVerses`,
`partialVerses`, `mappedVerses` — and the base is `basedOn`. `spaNVIv3`'s own header says *"custom
modifications to eng.vrs"*. Nothing new needs designing; the overlay is a derived scheme, which
`load_scheme` already folds (`versification.py:381`, derived wins over base).

**`partialVerses` needs no interpretation in order to be parsed.** `UNREAD_FIELDS`
(`versification.py:329`) already declares that this engine does not read it and warns when a
scheme carries one, so the overlay parses the construct, the field is populated, and the engine's
existing position applies unchanged.

`_pairs` (`versification.py:276`) already expands `"PSA 51:1-19": "PSA 51:3-21"` into nineteen
single-verse pairs and skips uneven entries with a collected report, so range mappings need no
special handling.

## 3. No generated file

**A derived `spaNVIv3.json` beside `custom.vrs` would be a second source.** The repository already
holds that position about templates — *"the second copy becomes a second source, which is the whole
defect the template form exists to remove"* (`test_template_layout.py:106`). `custom.vrs` is the
declaration; deriving in memory keeps one.

Not generating a file removes three problems that only existed because of it:

- **No search path.** `_read` (`versification.py:361`) looks in one directory. A generated file in
  a cache directory could not find its base there. Loading only the *base* by name leaves `_read`
  untouched.
- **No staleness.** Nothing to invalidate when `custom.vrs` changes.
- **No collision.** The project name is never a registry key, so a project called `eng` shadows
  nothing. This is what the Captain's ruling settles: the name is a **label, not a lookup key.**

It also removes a fourth. `maxVerses` folds per *book*, not per chapter (`versification.py:347`), so
a file-based override of `PSA 47:10` would have to restate all 150 chapters. Folding onto a `Scheme`
object whose `max_verses` is already resolved makes it one assignment.

## 4. The shape

```python
base    = load_scheme(numbered_scheme, mappings_dir)     # already works
overlay = read_custom_vrs(project_dir / "custom.vrs")    # new: the three constructs
scheme  = fold(base, overlay, name=project_id)           # a Scheme, labelled for the project
```

`map_candidates` resolves a name in one place — `load_scheme(from_scheme, mappings_dir)` at
`versification.py:390` — so accepting `str | Scheme` there is a couple of lines.

**A correction to an earlier framing in this design.** "Scheme objects through the API" was put to
the Captain as the *wider* of two options. It is not: it looked wide only because the scheme was
assumed to need a registered, resolvable name. Identifying it by the project removed that
assumption and most of the work with it.

## 5. What the container reports

Ruled: the **project identifier**, for every Paratext project, meaning *the versification the
project specified for this project*.

That is a change in what the field promises. It currently reports a scheme name a reader could look
up; `"spaNVIv3"` is not resolvable outside that Paratext installation. It is reported anyway
because the alternative — reporting the base `eng` — is a plain falsehood about verses that differ,
and reporting the base only when there is no `custom.vrs` would make the field mean two things.

The shipped documentation must say this, since consumers read that key.

**Corrected during implementation.** The ruling above reads "for every Paratext project… whether
standard or custom". The Captain's clarification narrows it: *"the project name means 'whatever
versification the project uses, including eng + custom.vrs on top of it'. a standard mapping means
'the standard mapping'."*

The field has one meaning — which numbering is in force — and the name it carries follows from
what is in force. A project using a standard scheme reports that scheme's name. A project using a
standard scheme with its own `custom.vrs` on top reports the project's name, that numbering having
no other. An overlay stating nothing leaves the base in force and reports the base's name; one
shipped project's `custom.vrs` is comments only. This does not make the field mean two things,
which the paragraph above was guarding against: it means one thing, and both standard scheme names
and project names are names for a numbering.

**The original wording would have shipped a defect.** Labelling a plain `eng` project with its
project id stops the equality short-circuit in `resolve_passage` from firing, so an `eng` request
is mapped `eng → org → eng` instead of left alone. Measured: 31 of 2,422 mapped `eng` verses do not
survive that round trip — 30 return several candidates so `map_reference` refuses, and `BAR 6:73`
raises "outside versification scheme 'org'". All are deuterocanonical, which is exactly the
material a project carrying a `custom.vrs` is most likely to have.

## 6. The blocker, found and cleared before Paratext

`spaNVIv3` states the same left-hand side twice:

```
REV 13:1 = REV 12:18
REV 13:1 = REV 13:1
```

An earlier draft of this document read that as a deliberate workaround for a Paratext limitation
and proposed refusing it. **The Captain corrected it: this is what a merge looks like.** In `org`,
REV 12 has 18 verses; in NIV-like numbering it has 17, and the content of org's REV 12:18 sits in
the project's REV 13:1. So one project verse names two hub verses. The neighbouring `REV 12:17`
line, shortening the chapter, is the other half of the same statement.

**The engine could not represent that at all**, and not only for Paratext. `_pairs` required a
mapping's two sides to cover equal numbers of verses and skipped the entry otherwise — dropping
seven entries across three *shipped* schemes, including `PSA 89:0-1 => PSA 90:0` and
`PSA 141:0 => PSA 142:0-1` in `rsc`. A reference inside a dropped range then passed through
unchanged: silently the wrong verse, despite an honest warning at load.

Ruled: **fix merges first, then Paratext.** Done — `to_hub` holds a list per verse, `_pairs`
recognises a run joining into one verse and one verse dividing into a run, and `map_candidates`
accumulates across both hops. `rsc` now loads with no complaint; `rso`'s five-verses-to-six and
`vul`'s backwards range stay refused, because neither says where a verse went.

So Paratext needs **no special case** for this: a merge in a `custom.vrs` is the same thing as a
merge in `rsc`, and the format already carries it.

## 7. Decisions for the Captain

None outstanding. `read_custom_vrs` goes beside the scheme loader in `utils/versification.py`,
since it produces scheme data and nothing else uses it; §5 already covers the plain project, by
the ruling that the field means *the versification the project specified* whether standard or
custom.

Remaining work, all of it ordinary: the `custom.vrs` parser for the three constructs, wiring it
into `_paratext_scheme`, `map_candidates` accepting `str | Scheme`, and the shipped documentation
for what the container's `versification` key now reports.

**All four landed.** `read_custom_vrs` and `fold_custom` in `utils/versification.py`, the wiring in
`edition_scheme`, `map_candidates` and `map_reference` taking a name or a `Scheme`, and the
documentation in `docs/llmflow-language.md` and the shipped `sp/scripture-representations.md`. The
parser covers **four** constructs rather than the three named above — see the correction in §2.

## 8. Not in scope

Writing a `custom.vrs`, or mapping *between* two projects' numbering. Both projects would have to be
registered and the hub route already covers it if they are.
