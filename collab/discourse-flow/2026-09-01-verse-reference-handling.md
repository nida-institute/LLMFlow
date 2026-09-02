# Verse references: we parse them ten ways, and a sub-verse reference survives none of them

**From:** an AI session in `nida-institute/discourse-flow`, 2026-09-01.
**Status: drafted by the AI, pending the Captain's review.**

The Captain asked whether we use the reference structure the engine provides or roll our own. The
answer is both, the split is not clean, and looking at it turned up something we think you will
want to see regardless of what you decide about the rest.

## 1. Where we use yours

`llmflow.utils.data.parse_bible_reference` runs as the `parse_book_reference` step in four of our
pipelines including the main one, and `plugins/add_pericope_ids.py` calls it directly to build
canonical pericope ids. We use it for **book-level facts** — `book_code`, `book_number`,
`filename_prefix`, `canonical_reference`.

## 2. Where we roll our own

Ten functions across seven files:

```
plugins/continuity_validation.py   parse_verse
plugins/discourse_export.py        _parse_verse_ref, _parse_verse_range, _verses_in_range
plugins/milestone_content.py       _parse_verse_key
plugins/nested_pericopes.py        _parse_start_bcv
plugins/windowing.py               _parse_verse, _parse_sid_to_chapter_verse
utils/discourse_tree.py            parse_verse_ref, _cmp_verse
plugins/acai_local.py              parse_reference_range
```

They exist because what we need at verse level is not what `parse_bible_reference` returns. Two
operations account for almost all of it:

- **order** — is `MRK 9:50` before `MRK 10:1`? We sort pericopes, detect gaps and overlaps, and
  check that a window's slice tiles its range.
- **membership** — does verse `X` fall inside range `A–B`?

Your parser gives us `chapter`, `start_verse`, `end_chapter`, `end_verse`, which is the input to
both, but we could find no comparator and no range-membership helper on the public surface of
`llmflow.utils.data`. So these are not straightforwardly reimplementations of something you ship.

They do differ from yours in input shape: most of ours take a bare `"1:14"`, not a full
reference. `parse_bible_reference("1:14")` has no book to work with.

## 3. What we found while checking: they do not agree with each other

Same input, four of our implementations, four behaviours:

```
'2:5b'    continuity_validation.parse_verse   ValueError
          windowing._parse_verse              ValueError
          discourse_tree.parse_verse_ref      None            <- silent
          discourse_export._parse_verse_ref   (2, 5)          <- silently drops the 'b'

'2:5b' vs '2:5'  discourse_tree._cmp_verse    ValueError      <- ordering crashes
```

`2:5b` is not a hypothetical. Our own data carries it: 1 John 2:1-6 contains the segment
`2:5b-6`, and Philemon has `1:19b-20`. Two of these raise, one returns `None` and one truncates —
so the same reference is a hard error, an absence, or a slightly wrong verse depending on which
file reaches it first. **That is our defect, not yours**, and we are reporting it here only
because it bears on the question of where this logic should live.

## 4. The part we think is yours

`parse_bible_reference` accepts a sub-verse reference and silently returns something narrower:

```
'1JN 2:5b-6'    -> start_verse=5  end_verse=5  canonical_reference='1 John 2:5'
'PHM 1:19b-20'  -> start_verse=19 end_verse=19 canonical_reference='Philemon 1:19'
'1 John 2:5b-6' -> start_verse=5  end_verse=5  canonical_reference='1 John 2:5'
```

Two things are lost without a warning: the sub-verse letter, and **the end of the range** — `-6`
and `-20` are gone, so a two-verse span becomes a single verse. A caller that round-trips a
reference through this gets a different, narrower passage back and nothing says so.

We are not asking you to support sub-verse addressing. We are asking whether **silent** narrowing
is the intended contract. From here the options look like: reject the reference; parse it and
carry the letter; or parse the range and drop only the letter, with the loss visible in the
returned structure. Any of the three would be safe for us; the current behaviour is the one we
cannot defend against, because nothing distinguishes it from a correct parse.

Relevant to us specifically: mid-verse boundaries are real in this project — a pericope can open
at `1:19b` — and we have an open question about whether to carry them as word ids instead. Which
way you answer this changes that decision.

## 5. What we would like your view on

1. **Do verse ordering and range membership belong in the engine?** They are the two operations
   our ten functions implement. If they are yours, we delete ours and call yours. If they are
   not, we consolidate ours into one module and stop pretending it is your job.
2. **Is silent narrowing of a sub-verse reference intended?** §4.
3. **Is there a canonical form we should be storing?** We keep `"MRK 1:14"` in ids and `"1:14"`
   in fields the prompts read, and the mismatch is why some of our functions take one shape and
   some the other.

None of this blocks us. We can consolidate locally this week either way; we would rather do it
once, in the place you think it belongs.
