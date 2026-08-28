# Design — what a project gets when it asks about "Mark 3:14"

**Status: draft frame, 2026-08-27. Not authorization to build, and the answers are not here.**
Seven decisions are marked `=>` and are the Captain's. This document states the cases and the
evidence; it deliberately stops short of choosing.

Tracked as **#218**.

Origin: *"remind me how projects get a data structure describing passage references like 'Mark
3:14'"* — followed, in the same breath, by the observation that undoes the easy answer: *"you
might say that depends on the versification."* Then, having reached for `eng` as a default:
*"actually, stop. we normally know the source, right? and we can use its versification?"* — and
immediately: *"hmmm, not always."*

That sequence is the whole design problem. Both instincts are sound and neither is complete.

---

## 1. The prescribed route today

`llmflow.utils.data.parse_bible_reference()`. Four things make it the prescribed one rather than
merely an available one, and any redesign has to keep all four working:

- exported from `src/llmflow/__init__.py` — the public API surface
- registered in `src/llmflow/catalog.py:52`, so a `type: function` step can reach it
- the example the schema gives for `type: function` (`schema/pipeline.schema.json:214`)
- named in `CLAUDE.md` as the thing not to reimplement

```python
from llmflow import parse_bible_reference
parse_bible_reference("Mark 3:14")
# {'book_code': 'MRK', 'chapter': 3, 'start_verse': 14, 'end_verse': 14, 'end_chapter': 3,
#  'is_whole_chapter': False, 'filename_prefix': '41003014-41003014',
#  'display_name': 'Mark-3-14', 'canonical_reference': 'Mark 3:14', 'testament': 'NT', ...}
```

Two other parsers exist and are **not** prescribed. They should stay unadvertised whatever this
design concludes, or we have three answers to one question:

=> delete any cruft, parsers that are not needed. the response metadata should state which versification was used to produce it.   By default, use "eng," since people who don't specify a versification are probably thinking of "eng" versification.

| | scope | accepts | rejects |
|---|---|---|---|
| `utils.scripture.parse_passage_ref` | internal to `type: scripture` | USFM codes, ranges | — but silently maps `"Mark"` → book `MARK`, which no reader resolves |
| `utils.versification.parse_reference` | internal to the mapper | a single verse, with a part letter | ranges, whole chapters |

Note the asymmetry, since it is a live bug either way: the prescribed parser **rejects** `MRK
3:14` (`ValueError: Unrecognized Bible book 'mrk'`) while the internal one requires it. Each
accepts what the other refuses.

## 2. Two questions wearing one word

This is the distinction the design turns on, and the reason "default to `eng`" and "use the
source's scheme" are answers to *different* questions:

- **The scheme the request is written in.** A human typed `Psalm 23`, meaning it in whatever
  numbering they think in. This is where *"the vast majority of our users expect `eng` unless
  they have thought about the problem"* is true — it is a fact about **people**.
- **The scheme the text is numbered in.** A property of the edition, discoverable from it.

`type: scripture` already separates them, and correctly: `versification:` is the request side,
`edition_scheme()` is the source side, and the mapper runs between. **`parse_bible_reference`
sits outside both and knows neither exists.** It is a string parser called with no context.

=> the passage metadata we return could provide passage_reference metadata for what it returns, which would help transparency and debugging.  I assume the additional token cost would be modest.

## 3. What is actually broken today, measured

Only one field in the returned structure is scheme-dependent: `end_verse` when
`is_whole_chapter`. Everything else — book code, the numbers as typed, testament, language — is
scheme-free and sound.

That one field is computed from a table hardcoded inside the function covering **book 19 and
nothing else**. Every other book falls through to a sentinel:

| input | `end_verse` | `canonical_reference` |
|---|---|---|
| `Psalm 23` | 6 | `Psalms 23:1-6` |
| `Mark 3` | **999** | `Mark 3:1-999` |
| `3 John 1` | **999** | `3 John 1:1-999` |

Three consequences, in the order they would bite:

1. **Psalms is the worst possible book to hardcode unlabelled.** `org` and `eng` disagree on the
   verse count in **62 of 150** psalms — Psalm 3 is 9 verses or 8, depending on whether the
   superscription is verse 1. The table gives one number and names no scheme.
2. **No scheme field on the result.** A consumer cannot tell what numbering it is holding, while
   `canonical_reference` presents itself as canonical.
3. **We ship the real data and this function does not read it.** `~/.sp/versification/*.json`
   carries `maxVerses` for every book in six schemes (`MRK`: 16 chapters, ch. 3 = 35 verses). The
   999 sentinel and the Psalms table both predate that vendoring and are now redundant.

Also unvalidated: `Mark 3:99` and `Mark 99:1` both parse without complaint. `maxVerses` would
catch both — but only once a scheme is named, which is the same problem again.

## 4. The cases — why "use the source's versification" is not sufficient

Ranked by how often they occur, not by difficulty. Each breaks a different rule.

**(a) No source in sight.** The function is called to build a filename, a cache key, a display
name. No edition is in play, and none ever will be. This is its *most common* use, and it is why
the 999 exists rather than an error.

**(b) Source known but silent.** No Paratext `Settings.xml`, not in `versification-editions.json`.
`edition_scheme()` returns `None` today, by the standing ruling that there is no global default.

**(c) Two sources, one reference.** *"You can already fetch the hebrew original together with bsb
in one step"* — WLC is `org`, BSB is `eng`. One passage string, two schemes; it cannot be in both.

**(d) Annotation data with a third numbering.** Levinsohn's indices are NA28-family against an
SBLGNT text; discourse outlines use OSIS book codes. A third scheme in the same pipeline, already
shipping.

**(e) Naming stability.** `filename_prefix` and `display_name` become filenames and cache keys.
If a scheme can move the numbers, the same passage can write two different files across runs — or
two distinct passages can collide on one name. This is a question about **stability**, and a
default answers it very differently from a refusal. Worth deciding on its own terms.

**(f) The reference is a range crossing a mapped boundary.** Where a scheme merges or splits
verses, a range's extent is not a simple endpoint lookup. The mapper already refuses ambiguity
by naming candidates; a parser that returns a plain `end_verse` has nowhere to put a refusal.

---

## 5. Decisions

**=> D1. Does `parse_bible_reference` resolve extent at all?** The case for removing it: extent is
only ever *needed* when something is about to read a text, and at that moment the edition is in
hand. The case against: case (a) is the common one, and callers building filenames want a
complete structure without an edition. Removing it is a breaking change to a published API.

=>  we need it.

**=> D2. If it keeps extent, where does the number come from?** `maxVerses` from a named scheme,
replacing the inline Psalms table — and then D3 decides what happens with no scheme.

=> Yes, maxVerses

**=> D3. With no scheme named, what does `end_verse` do?** Candidates: refuse (raise); return
`None` and mark the field unresolved; fall back to `eng` as the stated request-side default. Note
that 999 is none of these — it reads like an answer and is not one.

=> With no named schema, use "eng".

**=> D4. Does the returned structure carry the scheme it used?** Type safety was already ruled
worth a few bytes in the resource design. The same argument applies to a reference that has been
resolved against a numbering.

=> Absolutely.

**=> D5. Is `eng` the request-side default, and is it global or per-project?** *"The vast majority
of our users expect that unless they have thought about the problem"* — but the standing ruling on
the source side is that there is no global default, and a project working in Hebrew Psalms would
be silently wrong every time. A per-project setting is a third option.

=> It's the global default.  But we could also provide a way to declare a different default in a pipeline file if we added a "header declaration" section to our language for configuration.  Create an issue for that, that's a big change and it's not required for the immediate goal.

**=> D6. Do the two parsers converge?** The prescribed one rejects `MRK`, the internal one
requires it and mis-accepts `Mark`. Both bugs are real today regardless of the rest of this
design, and could be fixed independently — `parse_bible_reference` already knows the USFM code
for every display name it accepts.

=> As few implementations as needed to cover the functionality. Each one needs to be fully tested and supported, and adds to the confusion, so each one needs to really justify itself.

**=> D7. Are filenames and keys allowed to depend on a scheme at all?** If not, `filename_prefix`
and `display_name` must be computed from the reference *as written*, and only reading is
scheme-resolved. This may be the cleanest cut available: it makes case (a) scheme-free by
construction and confines the whole problem to the read path.

=>  File names and keys can be constructed using any variable. Why special case this?

---

## 6. Not in scope

- **Changing `type: scripture`'s resolution order.** Declared → Paratext `Settings.xml` → known
  editions → `None` is settled and works. This document is about the *parser*, which sits outside it.
- **A global source-side default.** Already ruled against: a Byzantine text and a critical text
  are numbered differently, and guessing picks a side silently.
- **Custom user-supplied schemes.** Separate thread; the catalog already places a custom mapping
  alongside the vendored six without overwriting it.

## 7. Resolved

Ruled after §5's `=>` answers, working through the consequences one at a time. Nothing here
overrides an `=>`; it records what those answers turned out to require.

| | decision |
|---|---|
| **Whole-chapter extent** | Stops returning `999`, returns the real count. A breaking change to a returned field, accepted: there is no compatibility guarantee at this version and the CHANGELOG is the notice. |
| **Where `maxVerses` comes from** | The copy packaged at `llmflow/templates/sp/versification/`, already in the wheel and both Nuitka commands. **No `~/.sp` dependency** — a custom versification is edition-scoped (a Paratext project or a Scripture Burrito), so a parser with no edition only ever needs the six shipped schemes. |
| **A book the named scheme lacks** | Three cases, not two. Extent needed and exactly one other scheme defines the book (`ENO`, `EZA`, `JUB` in `org`; `6EZ` in `vul`) → resolve from it; one scheme is not a guess. Extent needed and two define it (`ODA`, `PSS` in both `lxx` and `org`) → raise, naming both candidates. Extent *not* needed, so nothing is looked up → parse; the metadata records that the book is not available in that versification; the log carries a warning. |
| **`filename_prefix` and `display_name`** | Keep the resolved end verse. **Decided against changing, not deferred.** |
| **How many parsers** | Two. |

### Why the name fields keep the resolved verse

The argument for making them scheme-free was that `rewind` recomputes a saveas path from context
(`rewind.py:90`) rather than reading a manifest, so a name that moves breaks replay. That is true
of the mechanism and false as a problem: the steps before a rewind target are re-executed, so
`passage_info` is regenerated by the engine doing the replay and the path comes out as it did when
the artifact was written. The only failing case is an artifact written by one version and replayed
by another — and **replaying old runs is not a supported scenario**; replay has to work for new
runs.

The Captain's other point is the more general one: these are fields on a returned dict, not a
mandated naming scheme. A pipeline that wants a stable name builds one. Constraining what the
field may contain in order to protect a naming property solves a problem the pipeline author
already owns.

Residual, and cosmetic: `19003001-19003008` asserts an extent that came from a default rather than
from the text, so a directory listing can mislead a human. That argues for documenting the field,
not for changing its format — and the metadata and log warning tell the truth where it matters.

### Why two parsers rather than one

D6 asks each implementation to justify itself. Two do, and they justify themselves *against each
other*, by a property the other must not have:

- **Public, rich, scheme-aware.** `parse_bible_reference` has no edition to consult, so it must
  carry a scheme, a default, and a `maxVerses` lookup.
- **Internal, lean, scheme-free.** `parse_passage_ref` serves the read path and the mapper, which
  already know their edition. Converging it onto the public parser would drag a versification
  default into the one place a global source-side default is forbidden — and it currently *cannot*
  make that mistake, because it has no concept of a scheme.

The third goes away rather than being kept: `versification.parse_reference` differs only in
handling a verse part letter, which is load-bearing (`map_reference` builds `ESG 1:1a`-style keys
via `format_reference` and looks them up in `excluded_verses` and `to_hub`). Give `PassageRef` a
part field and the mapper uses the lean parser.

Two bugs are fixed independently of all this: the public parser stops rejecting `MRK` when it
already knows every USFM code, and the lean one stops silently accepting `Mark` as book `MARK`.

## 8. Key files

| | |
|---|---|
| `src/llmflow/utils/data.py:109` | `parse_bible_reference`, and the Psalms table at `:403` |
| `src/llmflow/utils/scripture.py:125` | `parse_passage_ref`; `edition_scheme` resolves the source side |
| `src/llmflow/utils/versification.py:80` | `parse_reference`, `map_reference`, the ambiguity refusal |
| `~/.sp/versification/*.json` | `maxVerses` for six schemes — the data the parser does not read |
| `data/versification-editions.json` | edition → scheme, with `confirmed` flags |
| `docs/ai-context/sp/scripture-representations.md` | *"A reference is not a location until a scheme is named"* |
