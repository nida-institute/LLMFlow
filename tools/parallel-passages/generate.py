"""Convert the UBS Parallel Passages database to the JSON dataset described in
`project/plans/design-parallel-passages-json.md`.

    hatch run python tools/parallel-passages/generate.py <ParallelPassages.xml> data/parallel-passages.json

One object per group, in the source's order; one object per member, in the group's order. Each
member has an `addressed` block — the reference as the database writes it, in `org` — and a
`counted` block — the verses and edition its word scores index. A Hebrew member of a group that
also has Greek members is counted in Rahlfs, so its `counted` verses are mapped `org` to `lxx`.
`match` is one value per word, from the `Match` enum. The source's line-break component is
discarded.
"""

import enum
import json
import sys
from pathlib import Path

from lxml import etree

from llmflow.utils.parallel_passages import _whole_references
from llmflow.utils.versification import (
    UnmappableReference,
    format_reference,
    load_scheme,
    map_candidates,
    packaged_mappings_dir,
    packaged_scheme,
    parse_passage_ref,
)

DATABASE_SCHEME = "org"
RAHLFS_SCHEME = "lxx"


class Match(enum.Enum):
    """How strongly a word corresponds to some other member of its group."""

    NO_MATCH = "no_match"
    PARTIAL = "partial"
    FULL = "full"


class CountedIn(enum.Enum):
    """The edition a member's word scores index. Extended when an edition is added."""

    BHS = "BHS"
    RAHLFS = "Rahlfs"
    UBSGNT5 = "UBSGNT5"


MATCH_BY_DIGIT = {0: Match.NO_MATCH, 1: Match.PARTIAL, 2: Match.FULL}


def verses_of(reference: str) -> list:
    """Every verse a database reference names: comma lists split, ranges expanded."""
    out = []
    for piece in _whole_references(reference):
        ref = parse_passage_ref(piece)
        if ref.start_verse is None:
            raise ValueError(f"{reference!r} names a whole chapter or book")
        end_chapter = ref.end_chapter or ref.start_chapter
        end_verse = ref.end_verse or ref.start_verse
        extents = packaged_scheme(DATABASE_SCHEME).max_verses[ref.book]
        chapter, verse = ref.start_chapter, ref.start_verse
        while (chapter, verse) <= (end_chapter, end_verse):
            out.append(format_reference(ref.book, chapter, verse))
            if verse < int(extents[chapter - 1]):
                verse += 1
            else:
                chapter, verse = chapter + 1, 1
    return out


def counted_verses(verses: list, org, lxx) -> list | None:
    """*verses* mapped `org` to `lxx`; None where a verse has no `lxx` counterpart."""
    out = []
    for verse in verses:
        try:
            for candidate in map_candidates(verse, org, lxx):
                if candidate not in out:
                    out.append(candidate)
        except UnmappableReference:
            return None
    return out


def convert(xml_path: Path) -> dict:
    org = load_scheme(DATABASE_SCHEME, packaged_mappings_dir())
    lxx = load_scheme(RAHLFS_SCHEME, packaged_mappings_dir())
    groups = []
    for passage in etree.parse(str(xml_path)).getroot().iter("Passage"):
        rows = []
        for verse in passage.findall("Verse"):
            greek = verse.get("GRK") is not None
            digits = verse.get("GRK") if greek else verse.get("HEB")
            if digits is None:
                raise ValueError(f"{verse.text!r} states neither GRK nor HEB")
            rows.append(((verse.text or "").strip(), greek, digits))
        if not rows:
            continue

        mixed = any(greek for _, greek, _ in rows) and not all(greek for _, greek, _ in rows)
        members = []
        for reference, greek, digits in rows:
            verses = verses_of(reference)
            if greek:
                counted_in = CountedIn.UBSGNT5
            elif mixed:
                counted_in = CountedIn.RAHLFS
            else:
                counted_in = CountedIn.BHS

            if counted_in is CountedIn.RAHLFS:
                counted = {
                    "verses": counted_verses(verses, org, lxx),
                    "versification": RAHLFS_SCHEME,
                    "text": counted_in.value,
                }
            else:
                counted = {
                    "verses": verses,
                    "versification": DATABASE_SCHEME,
                    "text": counted_in.value,
                }

            members.append(
                {
                    "addressed": {
                        "reference": reference,
                        "verses": verses,
                        "versification": DATABASE_SCHEME,
                    },
                    "counted": counted,
                    "match": [MATCH_BY_DIGIT[int(d) % 3].value for d in digits],
                }
            )

        editions = sorted({member["counted"]["text"] for member in members})
        groups.append({"editions": editions, "members": members})

    return {
        "about": {
            "source": {
                "name": "UBS Parallel Passages Database",
                "license": "CC BY-SA 4.0",
                "origin": "ubsicap/ubs-open-license — parallel passages/ParallelPassages.xml",
            },
            "design": "project/plans/design-parallel-passages-json.md",
            "generator": "tools/parallel-passages/generate.py",
            "match": [value.value for value in Match],
            "counted_in": [value.value for value in CountedIn],
            "editions": "derived from the members' counted.text, never authored",
            "counted_verses_null": "a Hebrew member whose verse has no single lxx counterpart",
            "groups": len(groups),
            "members": sum(len(group["members"]) for group in groups),
        },
        "groups": groups,
    }


def write(document: dict, output: Path) -> None:
    """One group per line, so a regeneration's diff names the groups that changed."""
    lines = [
        "{",
        f' "about": {json.dumps(document["about"], ensure_ascii=False)},',
        ' "groups": [',
    ]
    groups = document["groups"]
    for index, group in enumerate(groups):
        comma = "," if index < len(groups) - 1 else ""
        lines.append("  " + json.dumps(group, ensure_ascii=False) + comma)
    lines += [" ]", "}"]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    document = convert(source)
    write(document, target)
    print(f"wrote {target}: {document['about']['groups']} groups, {document['about']['members']} members")
