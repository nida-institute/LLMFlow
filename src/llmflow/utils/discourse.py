"""Levinsohn discourse features: reconcile a citation's word index with the Greek it quotes.

The rules, the reasoning and the measurements: §5 step 9 of
`project/plans/plan-scripture-step.md`.
"""

from __future__ import annotations

import enum
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from llmflow.modules.logger import Logger

logger = Logger()

#: Characters that may sit at the edge of a quoted word without being part of it.
EDGE_PUNCTUATION = " ,.;:·—–-()[]{}⟦⟧«»‹›\"'’‘“”·;"

#: A truncated match — a quote running past the verse end — must cover at least this many words
#: before it counts. One word would let any verse ending in a common word verify a long quote.
MIN_TRUNCATED_MATCH = 2

#: OSIS book codes as LGNTDF writes them, to USFM as the engine uses them.
OSIS_TO_USFM = {
    "Matt": "MAT", "Mark": "MRK", "Luke": "LUK", "John": "JHN", "Acts": "ACT",
    "Rom": "ROM", "1Cor": "1CO", "2Cor": "2CO", "Gal": "GAL", "Eph": "EPH",
    "Phil": "PHP", "Col": "COL", "1Thess": "1TH", "2Thess": "2TH", "1Tim": "1TI",
    "2Tim": "2TI", "Titus": "TIT", "Phlm": "PHM", "Heb": "HEB", "Jas": "JAS",
    "1Pet": "1PE", "2Pet": "2PE", "1John": "1JN", "2John": "2JN", "3John": "3JN",
    "Jude": "JUD", "Rev": "REV",
}

#: `Mark.1.14!3`, or a range whose opening is the citation.
OSIS_REF = re.compile(r"^(?P<book>[0-9A-Za-z]+)\.(?P<chapter>\d+)\.(?P<verse>\d+)!(?P<index>\d+)")


#: A citation quoting the Greek it points at, so its index can be checked.
FEATURE_KIND = "feature"

#: One of Levinsohn's own annotations. Its text is English commentary, so there is no quote to
#: check an index against; it is anchored, never verified.
NOTE_KIND = "note"

#: The `type` a header declares for the annotations file.
ANNOTATIONS_TYPE = "annotations"


class Outcome(enum.Enum):
    """What reconciling an index with its quote established."""

    VERIFIED = "verified"
    DISAGREES = "disagrees"
    RESCUED = "rescued"
    AMBIGUOUS = "ambiguous"
    NOT_FOUND = "not_found"
    UNVERIFIABLE = "unverifiable"
    OUT_OF_RANGE = "out_of_range"
    #: A note placed at a usable index, with nothing to verify it against.
    ANCHORED = "anchored"


@dataclass(frozen=True)
class Citation:
    """One `<reference>`: what it says, where it points, and whether it can be verified."""

    feature: str
    kind: str
    book: str
    chapter: int
    verse: int
    index: int
    text: str
    level: Optional[int] = None


@dataclass(frozen=True)
class Resolution:
    outcome: Outcome
    word_id: Optional[str]
    index: int
    resolved_index: Optional[int] = None
    candidates: int = 0
    quote_found_at: Optional[int] = None


def normalize_greek(text: Optional[str]) -> str:
    """Fold a Greek word to a form safe to compare: no diacritics, lowercase, no edge marks."""
    decomposed = unicodedata.normalize("NFD", text or "")
    without_marks = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_marks.lower().strip(EDGE_PUNCTUATION)


def osis_to_usfm(book: str) -> str:
    """The USFM code for an OSIS book code."""
    try:
        return OSIS_TO_USFM[book]
    except KeyError:
        raise ValueError(
            f"{book!r} is not an OSIS book code this corpus uses. Known: "
            f"{', '.join(sorted(OSIS_TO_USFM))}."
        ) from None


def parse_osis_ref(osis_ref: str) -> tuple[str, int, int, int]:
    """`Mark.1.14!3` as (USFM book, chapter, verse, 1-based word index).

    A range reference keeps its opening: only that end is the citation.
    """
    match = OSIS_REF.match((osis_ref or "").strip())
    if not match:
        raise ValueError(
            f"{osis_ref!r} is not a Levinsohn reference (expected e.g. 'Mark.1.14!3')."
        )
    return (
        osis_to_usfm(match.group("book")),
        int(match.group("chapter")),
        int(match.group("verse")),
        int(match.group("index")),
    )


def _phrase(quote: Optional[str]) -> list[str]:
    return [w for w in (normalize_greek(part) for part in (quote or "").split()) if w]


def _matches_at(words: Sequence[str], phrase: Sequence[str], start: int) -> bool:
    """Whether *phrase* matches at *start*, allowing it to run past the verse end."""
    room = len(words) - start
    if room <= 0:
        return False
    usable = min(len(phrase), room)
    if usable < len(phrase) and usable < MIN_TRUNCATED_MATCH:
        return False
    return list(words[start : start + usable]) == list(phrase[:usable])


def _positions(words: Sequence[str], phrase: Sequence[str]) -> list[int]:
    if not phrase:
        return []
    return [i for i in range(len(words)) if _matches_at(words, phrase, i)]


def resolve_citation(
    rows: Sequence[Mapping[str, Any]],
    word_index: int,
    quote: Optional[str],
) -> Resolution:
    """Reconcile one citation's index with its quote against one verse's rows.

    *word_index* is Levinsohn's 1-based index; *rows* are the verse's words in document order,
    each carrying `xml:id` and `text`.

    A usable index is never moved. Only an impossible one is rescued, and only when the quote
    appears exactly once.
    """
    words = [normalize_greek(row.get("text")) for row in rows]
    phrase = _phrase(quote)
    position = word_index - 1
    in_range = 0 <= position < len(words)

    def identifier(at: int) -> Optional[str]:
        value = rows[at].get("xml:id")
        return str(value) if value else None

    if not phrase:
        if in_range:
            return Resolution(Outcome.UNVERIFIABLE, identifier(position), word_index, word_index)
        return Resolution(Outcome.OUT_OF_RANGE, None, word_index)

    if in_range and _matches_at(words, phrase, position):
        return Resolution(Outcome.VERIFIED, identifier(position), word_index, word_index)

    found = _positions(words, phrase)

    if in_range:
        return Resolution(
            Outcome.DISAGREES,
            identifier(position),
            word_index,
            word_index,
            candidates=len(found),
            quote_found_at=(found[0] + 1) if len(found) == 1 else None,
        )
    if len(found) == 1:
        return Resolution(Outcome.RESCUED, identifier(found[0]), word_index, found[0] + 1)
    if len(found) > 1:
        return Resolution(Outcome.AMBIGUOUS, None, word_index, candidates=len(found))
    return Resolution(Outcome.NOT_FOUND, None, word_index)


def load_citations(lgntdf_dir: Any) -> dict:
    """Every citation in a directory of LGNTDF feature files, keyed by `"BOOK c:v"`.

    A file is read only when its root is a `feature` element with a header name, which skips
    `levinsohn.xml` — it only `xi:include`s the others — and any editor lock file left behind.
    """
    from lxml import etree  # type: ignore[attr-defined]

    directory = Path(lgntdf_dir)
    if not directory.is_dir():
        return {}

    found: dict = {}
    for path in sorted(directory.glob("*.xml")):
        if not path.is_file():
            continue
        try:
            root = etree.parse(str(path)).getroot()
        except (OSError, etree.XMLSyntaxError) as error:
            logger.warning(f"Discourse: {path.name} could not be read and was skipped: {error}")
            continue

        name = root.findtext("header/name")
        if etree.QName(root).localname != "feature" or not name:
            continue
        declared = root.find("header/type")
        kind = (
            NOTE_KIND
            if declared is not None and declared.get("name") == ANNOTATIONS_TYPE
            else FEATURE_KIND
        )

        for element in root.findall("references/reference"):
            try:
                book, chapter, verse, index = parse_osis_ref(element.get("osisRef") or "")
            except ValueError as error:
                logger.warning(f"Discourse: {path.name}: {error}")
                continue
            level = element.get("level")
            found.setdefault(f"{book} {chapter}:{verse}", []).append(
                Citation(
                    feature=name,
                    kind=kind,
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    index=index,
                    text=(element.text or "").strip(),
                    level=int(level) if level is not None and level.isdigit() else None,
                )
            )
    return found


def resolve_verse(
    citations: Sequence[Citation],
    rows: Sequence[Mapping[str, Any]],
) -> list:
    """One verse's citations as payload items, each carrying the word id and the outcome.

    A feature is reconciled against its quote. A note has no quote, so it is anchored at its
    index when that index exists and reported without one when it does not.
    """
    items = []
    for citation in citations:
        if citation.kind == NOTE_KIND:
            position = citation.index - 1
            usable = 0 <= position < len(rows)
            identifier = str(rows[position].get("xml:id")) if usable else None
            outcome = Outcome.ANCHORED if usable else Outcome.OUT_OF_RANGE
            resolution = Resolution(outcome, identifier, citation.index)
        else:
            resolution = resolve_citation(rows, citation.index, citation.text)

        item = {
            "id": resolution.word_id,
            "kind": citation.kind,
            "feature": citation.feature,
            "outcome": resolution.outcome.value,
            "index": citation.index,
        }
        if citation.level is not None:
            item["level"] = citation.level
        if citation.kind == NOTE_KIND:
            item["text"] = citation.text
        if resolution.resolved_index is not None and resolution.resolved_index != citation.index:
            item["resolved_index"] = resolution.resolved_index
        if resolution.quote_found_at is not None:
            item["quote_found_at"] = resolution.quote_found_at
        if resolution.candidates:
            item["candidates"] = resolution.candidates
        items.append(item)
    return items
