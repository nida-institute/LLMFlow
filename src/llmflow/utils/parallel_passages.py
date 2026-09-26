"""Read the UBS Parallel Passages database and answer which groups a passage is in.

A group states that several passages are parallel, or that one quotes another. The reader
returns a group whole; it never intersects a group with the request (#258).

Nothing about verses is implemented here. Comparison is `verse_ranges.select`, reference
handling is `versification`, and book codes are `books`. The one thing this module does to a
reference is split a comma list — `MRK 1:32,34` names two verses and not the one between them,
and no other module has reason to know that.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from lxml import etree

from llmflow import books
from llmflow.utils.verse_ranges import Range, select

# The scheme the database's own references are written in (#258). `Range.parse` requires one
# and has no default, so a reader that did not state this would be guessing.
DATABASE_SCHEME = "org"

EDITION_ATTRIBUTES = ("HEB", "GRK")


class ParallelPassagesError(ValueError):
    """A reference in the database is not in a form this reader knows."""


def _whole_references(reference: str) -> List[str]:
    """Split a comma list into complete references, carrying the chapter forward."""
    token, _, remainder = reference.strip().partition(" ")
    if books.resolve(token) is None:
        raise ParallelPassagesError(f"Parallel passages: {reference!r} does not begin with a book this engine knows.")
    if not remainder:
        raise ParallelPassagesError(f"Parallel passages: {reference!r} names a book with no chapter or verse.")

    out: List[str] = []
    chapter: Optional[str] = None
    for part in remainder.split(","):
        part = part.strip()
        if ":" in part:
            chapter = part.partition(":")[0]
            out.append(f"{token} {part}")
        elif chapter is not None:
            out.append(f"{token} {chapter}:{part}")
        else:
            raise ParallelPassagesError(f"Parallel passages: cannot read the verses in {reference!r}.")
    return out


def load_parallel_passages(path: Any) -> Dict[str, Any]:
    """Read the database into groups, plus one row per verse span for the lookup to filter.

    `groups` is plain data, so a step may put it in the pipeline context or write it with
    `saveas` unchanged.
    """
    tree = etree.parse(str(Path(path)))
    groups: List[Dict[str, Any]] = []
    rows: List[Dict[str, Any]] = []

    for element in tree.iter("Passage"):
        verses: List[Dict[str, str]] = []
        references: List[str] = []
        for verse in element.findall("Verse"):
            reference = (verse.text or "").strip()
            indexed_by = next((name for name in EDITION_ATTRIBUTES if verse.get(name) is not None), None)
            if indexed_by is None:
                raise ParallelPassagesError(
                    f"Parallel passages: {reference!r} states no edition; "
                    f"expected one of {', '.join(EDITION_ATTRIBUTES)}."
                )
            verses.append(
                {
                    "reference": reference,
                    "scores": verse.get(indexed_by),
                    "indexed_by": indexed_by,
                }
            )
            references.extend(_whole_references(reference))
        if not verses:
            continue
        position = len(groups)
        groups.append({"verses": verses})
        rows.extend({"reference": piece, "group": position} for piece in references)

    return {"groups": groups, "rows": rows, "source": str(path)}


def _probe(passage: str, versification: str) -> Range:
    """The request as a range in the database's own scheme.

    A reference is not a location until a scheme is named, so a request written in another
    scheme is mapped before anything is compared. Comparing across schemes would be silent:
    the algebra's ordinals are scheme-relative and its comparisons do not check the scheme.
    """
    if versification == DATABASE_SCHEME:
        return Range.parse(passage, scheme=DATABASE_SCHEME)

    from llmflow.utils.data import parse_bible_reference
    from llmflow.utils.versification import (
        format_reference,
        map_reference,
        packaged_mappings_dir,
    )

    # The packaged schemes, not `~/.sp`, because the database is fixed and `Range.parse` reads
    # the packaged copy too; a reader that answered differently per machine would be worse than
    # one that cannot see a custom scheme (#258).
    mappings = packaged_mappings_dir()
    info = parse_bible_reference(passage, versification=versification)
    code = info["book_code"]
    if info.get("is_whole_book"):
        return Range.parse(code, scheme=DATABASE_SCHEME)

    chapter = info["chapter"]
    start_verse = info.get("start_verse") or 1
    end_chapter = info.get("end_chapter") or chapter
    end_verse = info.get("end_verse") or start_verse

    opening = map_reference(format_reference(code, chapter, start_verse), versification, DATABASE_SCHEME, mappings)
    closing = map_reference(format_reference(code, end_chapter, end_verse), versification, DATABASE_SCHEME, mappings)
    first = Range.parse(opening, scheme=DATABASE_SCHEME)
    last = Range.parse(closing, scheme=DATABASE_SCHEME)
    return Range(book=first.book, start=first.start, end=last.end, scheme=DATABASE_SCHEME, text=passage)


def groups_for_passage(index: Dict[str, Any], passage: str, versification: str = "eng") -> List[Dict[str, Any]]:
    """Every group the passage takes part in, whole, in the order the database states them.

    An empty list means the database was consulted and this passage is in no group.
    `versification` names the scheme `passage` is written in, not the database's.
    """
    hits = select(
        index["rows"],
        _probe(passage, versification),
        "overlaps",
        ref="reference",
        scheme=DATABASE_SCHEME,
    )
    seen: List[int] = []
    for row in hits:
        if row["group"] not in seen:
            seen.append(row["group"])
    return [index["groups"][position] for position in sorted(seen)]
