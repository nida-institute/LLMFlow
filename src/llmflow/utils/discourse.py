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

#: `Mark.1.14!3`, or a range whose opening is the citation.
#: `Mark.1.14!3`, or a span whose two ends are written in full: `Mark.1.2!9-Mark.1.2!15`.
#:
#: A feature anchors at one word and has no end. A quotation is a span, and `OT_quotes.xml` writes
#: both ends — so the closing index is captured rather than discarded, which is what dropped the
#: extent of all 691 quotations before any consumer saw them.
OSIS_REF = re.compile(
    r"^(?P<book>[0-9A-Za-z]+)\.(?P<chapter>\d+)\.(?P<verse>\d+)!(?P<index>\d+)"
    r"(?:-(?:(?P<end_book>[0-9A-Za-z]+)\.(?P<end_chapter>\d+)\.(?P<end_verse>\d+)!)?"
    r"(?P<end_index>\d+))?"
)


#: The document roots a discourse corpus uses. LGNTDF writes `feature`; HOTDF-LS writes
#: `markup` for features and `annotations` for notes. A file whose root is none of these, or
#: which declares no header name, is skipped — which is how `levinsohn.xml`, a wrapper that
#: only xi:includes the others, stays out.
CORPUS_ROOTS = ("feature", "markup", "annotations")


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
    """One `<reference>`: what it says, where it points, and whether it can be verified.

    `book`, `chapter` and `verse` are the **opening** of the reference, and `load_citations` keys
    its result on that opening. A span closing in a later verse therefore belongs to the verse it
    starts in: `Mark.4.26!5-Mark.4.27!3` is 4:26, not 4:27. A consumer grouping by verse gets a
    different answer if it keys on the closing end instead, which is worth knowing before the two
    are compared.
    """

    feature: str
    kind: str
    book: str
    chapter: int
    verse: int
    index: int
    text: str
    level: Optional[int] = None
    #: The closing end where the reference names a span, all `None` where it names one word.
    #: A span may close in a later verse — 657 of LGNTDF's do, some three verses on — so the end
    #: is a reference in its own right rather than an index into the opening verse. The four move
    #: together: either every one is set or none is.
    end_book: Optional[str] = None
    end_chapter: Optional[int] = None
    end_verse: Optional[int] = None
    end_index: Optional[int] = None

    def __post_init__(self) -> None:
        """A bare `end_index` closes in the opening verse, which is the common span.

        `load_citations` always sets all four, so this is for a citation built by hand: giving
        only the closing word index would otherwise leave the end unplaceable, and silently, by
        looking like a span that closes in no verse at all.
        """
        if self.end_index is None:
            return
        for name, opening in (
            ("end_book", self.book),
            ("end_chapter", self.chapter),
            ("end_verse", self.verse),
        ):
            if getattr(self, name) is None:
                object.__setattr__(self, name, opening)


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
    """The USFM code for a book as a discourse corpus writes it.

    `llmflow.books.resolve` accepts either spelling and returns the USFM code, so a corpus
    writing OSIS names (`Mark`, `1Sam`) and one writing USFM codes (`MRK`, `1SA`) both parse
    with no configuration. It reads `data/book-names.json`, which is the single source for
    book names (#218); the 27-entry table this function used to carry was a second copy of
    part of it, and being New Testament only it refused every Old Testament reference.
    """
    from llmflow import books

    resolved = books.resolve(book)
    if resolved is None:
        raise ValueError(
            f"{book!r} is not a book name or code this engine recognises, so a discourse "
            f"reference naming it cannot be placed."
        )
    return resolved


def parse_osis_ref(
    osis_ref: str,
) -> tuple[str, int, int, int, Optional[tuple[str, int, int, int]]]:
    """`Mark.1.14!3` as (USFM book, chapter, verse, opening index, closing reference or None).

    A span gives both ends. `Mark.1.2!9-Mark.1.2!15` is words 9 through 15 of one verse;
    `Matt.6.9!5-Matt.6.13!61` is the Lord's Prayer, opening in 6:9 and closing four verses
    later; `Acts.26.16!14-Acts.26.18!71` crosses three. So the closing end is a reference in its
    own right — book, chapter, verse, word — not merely an index into the opening verse.

    It is stated in full whether or not it falls in the opening verse, so that `None` means
    "no span" and nothing has to read a missing verse as "the same one".

    A single-word reference reports `None`: a one-word anchor and a span of one word are not the
    same claim.
    """
    match = OSIS_REF.match((osis_ref or "").strip())
    if not match:
        raise ValueError(
            f"{osis_ref!r} is not a Levinsohn reference (expected e.g. 'Mark.1.14!3')."
        )

    book = osis_to_usfm(match.group("book"))
    chapter, verse = int(match.group("chapter")), int(match.group("verse"))

    end: Optional[tuple[str, int, int, int]] = None
    if match.group("end_index"):
        # A bare `-15` means the same verse; a written-out end names its own.
        end = (
            osis_to_usfm(match.group("end_book")) if match.group("end_book") else book,
            int(match.group("end_chapter")) if match.group("end_chapter") else chapter,
            int(match.group("end_verse")) if match.group("end_verse") else verse,
            int(match.group("end_index")),
        )

    return (book, chapter, verse, int(match.group("index")), end)


def _phrase(quote: Optional[str]) -> list[str]:
    return [w for w in (normalize_greek(part) for part in (quote or "").split()) if w]


def _word_index(row: Mapping[str, Any]) -> Optional[str]:
    """The `!N` of a row's `ref`, or None when it carries none."""
    ref = str(row.get("ref") or "")
    _, marker, index = ref.partition("!")
    return index.strip() if marker and index.strip().isdigit() else None


def _word_identifier(row: Mapping[str, Any], index: str) -> Optional[str]:
    """A row's `xml:id` addressed at the word rather than the morpheme.

    Macula ids are `BBCCCVVVWWWP` in Hebrew and `BBCCCVVVWWW` in Greek — the same shape, with a
    trailing **word part** where a word is written in several pieces. The format is declared in
    *MACULA Hebrew Treebank for OSHB* §2.1: `WWW` is the word index within the verse and `P` the
    word part. Greek carries no `P`, having no such words.

    So the part is dropped when doing so leaves the id ending in this row's own word index, and
    kept otherwise. That reads the declared format rather than guessing from length: a Hebrew
    `…0041` becomes `…004`, and a Greek `…003` is already the word.
    """
    value = row.get("xml:id")
    if not value:
        return None
    identifier = str(value)
    if identifier.endswith(index.zfill(3)):
        return identifier
    if len(identifier) > 1 and identifier[:-1].endswith(index.zfill(3)):
        return identifier[:-1]
    return identifier


def _words(rows: Sequence[Mapping[str, Any]]) -> tuple[list[str], list[Optional[str]]]:
    """One text and one word-level id per *word*, in document order.

    Macula Hebrew splits a word into morphemes, so a row is not a word: Ruth 1:1 is 33 rows over
    19 words. A citation's index counts words, so the comparison has to as well. Where `ref`
    carries no `!N` — any edition that is not Macula — each row stands as its own word, which is
    what the previous behaviour did everywhere.
    """
    texts: list[str] = []
    identifiers: list[Optional[str]] = []
    current: Optional[str] = None

    for row in rows:
        index = _word_index(row)
        text = normalize_greek(row.get("text"))
        if index is not None and index == current:
            texts[-1] += text
            continue
        texts.append(text)
        identifiers.append(_word_identifier(row, index) if index else _word_identifier(row, ""))
        current = index

    return texts, identifiers


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
    words, identifiers = _words(rows)
    phrase = _phrase(quote)
    position = word_index - 1
    in_range = 0 <= position < len(words)

    def identifier(at: int) -> Optional[str]:
        return identifiers[at]

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
    # `rglob`: HOTDF-LS keeps its files in subdirectories, LGNTDF in one flat directory.
    for path in sorted(directory.rglob("*.xml")):
        if not path.is_file():
            continue
        try:
            root = etree.parse(str(path)).getroot()
        except (OSError, etree.XMLSyntaxError) as error:
            logger.warning(f"Discourse: {path.name} could not be read and was skipped: {error}")
            continue

        name = root.findtext("header/name")
        if etree.QName(root).localname not in CORPUS_ROOTS or not name:
            continue
        declared = root.find("header/type")
        kind = (
            NOTE_KIND
            if declared is not None and declared.get("name") == ANNOTATIONS_TYPE
            else FEATURE_KIND
        )

        for element in root.findall("references/reference"):
            try:
                book, chapter, verse, index, end = parse_osis_ref(element.get("osisRef") or "")
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
                    end_book=end[0] if end else None,
                    end_chapter=end[1] if end else None,
                    end_verse=end[2] if end else None,
                    end_index=end[3] if end else None,
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
    # Words, not rows: a note is anchored by index like a feature, so it counts the same units.
    # See `_words` — Macula Hebrew gives a word several rows, and this path had its own indexing.
    _, identifiers = _words(rows)

    items = []
    for citation in citations:
        if citation.kind == NOTE_KIND:
            position = citation.index - 1
            usable = 0 <= position < len(identifiers)
            identifier = identifiers[position] if usable else None
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
        # A span states its closing end. The reference is always reported; the closing *id* only
        # where this verse holds that word, because these rows are one verse's. A span closing
        # in a later verse — 657 of LGNTDF's do — is reported without an id rather than dropped,
        # which is the extent this change exists to keep, and rather than given an id from the
        # wrong verse's rows, which would be worse than saying nothing.
        if citation.end_index is not None:
            item["end_index"] = citation.end_index
            item["end_verse"] = citation.end_verse
            if citation.end_chapter != citation.chapter:
                item["end_chapter"] = citation.end_chapter
            in_this_verse = (
                citation.end_verse == citation.verse
                and citation.end_chapter == citation.chapter
                and citation.end_book == citation.book
            )
            closing = citation.end_index - 1
            if in_this_verse and 0 <= closing < len(identifiers):
                item["id_end"] = identifiers[closing]
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
