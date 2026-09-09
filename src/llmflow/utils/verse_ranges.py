"""Comparing verse ranges — #169.

The issue reports duplicated overlap logic across four plugins. The duplication is worse and lower
down: five reference parsers between them, three incompatible return types, and none returning the
book, so one plugin compares `Mark 1:1-5` against `John 1:1-5` as overlapping. That defect is
structural — the parsed type has nowhere to put a book — which is why this module's deliverable is a
type built once at the boundary rather than a library of predicates over strings.

**No third parser is added here.** `parse_passage_ref` already gives the syntax as a `PassageRef`;
a scheme turns that into concrete verses. Only the comparison layer was missing.

Books are distinct documents, so no range spans books and ordinals are **book-local**: `max_verses`
for one book is all that is needed, canon order never arises, and the schemes disagreeing on book
inventory does not matter. Chapter-boundary adjacency becomes `a.end + 1 == b.start`.

`overlaps` means *shares at least one verse*, containment and equality included — the colloquial
sense, which is what the plugins and any pipeline author intend. The strictly-partial case that
interval algebra reserves the word for is a configuration handled here and given no name, so no
word means two things.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from llmflow.modules.logger import Logger
from llmflow.utils.context import _MISSING, get_from_context
from llmflow.utils.versification import PassageRef, packaged_scheme, parse_passage_ref

logger = Logger()

__all__ = [
    # `PassageRef` is re-exported so a caller holding one from the scripture step can see where
    # the syntax half of a `Range` comes from without a second import path.
    "PassageRef",
    "Range",
    "contains",
    "equals",
    "overlaps",
    "select",
    "touches",
    "verse_count",
]


@dataclass(frozen=True)
class Range:
    """A span of verses inside one book, in one versification scheme.

    ``start`` and ``end`` are **book-local ordinals** — the verse's position counted from the first
    verse of the book. They are an internal representation: scheme-relative, so a stored ordinal
    silently names a different verse under another scheme. Never expose or persist one.
    """

    book: str
    start: int
    end: int
    scheme: str
    text: str

    @classmethod
    def parse(cls, reference: str, *, scheme: str) -> "Range":
        """Build a range, or refuse.

        A reference is not a location until a scheme is named, so ``scheme`` is required and has no
        default. Whatever this returns is comparable: the book exists in the scheme, the chapters
        and verses exist in the book, and the end does not precede the start. Downstream functions
        are then total, with no guard converting an unreadable reference into "overlaps nothing".
        """
        ref = parse_passage_ref(reference)
        chapters = _chapters(ref.book, scheme, reference)

        start = _ordinal(ref.book, ref.start_chapter or 1, ref.start_verse or 1, chapters, reference)

        end_chapter = ref.end_chapter or ref.start_chapter or len(chapters)
        end_verse = ref.end_verse
        if end_verse is None:
            # A whole chapter, or a whole book: the scheme states where it ends.
            end_verse = int(chapters[end_chapter - 1])
        end = _ordinal(ref.book, end_chapter, end_verse, chapters, reference)

        if end < start:
            raise ValueError(f"{reference!r}: the range ends before it starts")

        return cls(book=ref.book, start=start, end=end, scheme=scheme, text=reference)


def overlaps(a: Range, b: Range) -> bool:
    """Do these share at least one verse? Containment and equality count."""
    return _same_book(a, b) and a.start <= b.end and a.end >= b.start


def contains(a: Range, b: Range) -> bool:
    """Does `a` cover every verse of `b`? A range contains itself."""
    return _same_book(a, b) and a.start <= b.start and a.end >= b.end


def touches(a: Range, b: Range) -> bool:
    """Are these adjacent — **no gap and no shared verse**?

    Said explicitly because GIS vocabulary uses the word for shared boundaries, so a reader may
    expect partially overlapping ranges to qualify. They do not; that is `overlaps`.
    """
    return _same_book(a, b) and (a.end + 1 == b.start or b.end + 1 == a.start)


def equals(a: Range, b: Range) -> bool:
    return _same_book(a, b) and a.start == b.start and a.end == b.end


def verse_count(a: Range) -> int:
    return a.end - a.start + 1


#: The relations `select` accepts by name. A string keeps a pipeline serialisable and lintable, and
#: is the only thing YAML can express; accepting a callable as well would widen this later without
#: breaking a caller, and nothing has asked.
RELATIONS: Mapping[str, Callable[[Range, Range], bool]] = {
    "overlaps": overlaps,
    "contains": contains,
    "touches": touches,
    "equals": equals,
}


def select(
    collection: Iterable[Any],
    probe: Any,
    relation: str,
    *,
    ref: str,
    scheme: str,
) -> list:
    """Every member of `collection` standing in `relation` to `probe`.

    This is the filter the pipeline language lacks. Python has a comprehension and does not need it;
    YAML has neither, which is why four plugins wrote the loop by hand and one of them takes the
    first match and reports nothing when a passage spans two units. A list makes that visible, and
    taking the first becomes something the caller writes.

    `ref` is the path to a member's reference — `declared-not-inferred`, so it is required rather
    than guessed, and it is resolved the way every other path in the engine is, so `meta.range` and
    `items[0].ref` work.

    Returns a list always, empty where nothing matched: the lookup ran and found nothing, which is
    not the same as never having asked.
    """
    if relation not in RELATIONS:
        known = ", ".join(sorted(RELATIONS))
        raise ValueError(f"Unknown relation {relation!r}. Known relations: {known}")

    holds = RELATIONS[relation]
    target = probe if isinstance(probe, Range) else Range.parse(probe, scheme=scheme)

    found, books_seen = [], set()
    for member in collection:
        reference = get_from_context(ref, dict(member)) if isinstance(member, Mapping) else None
        if reference is _MISSING or reference is None:
            logger.warning(f"select: no {ref!r} on a member; skipped: {member!r}")
            continue

        try:
            candidate = Range.parse(reference, scheme=scheme)
        except ValueError as unreadable:
            logger.warning(f"select: skipping a member whose reference will not parse: {unreadable}")
            continue

        books_seen.add(candidate.book)
        if holds(target, candidate):
            found.append(member)

    if books_seen and target.book not in books_seen:
        # Books are distinct documents, so this returns nothing and is not wrong — but an empty
        # result would otherwise read as "no unit matched" when the pipeline compared the wrong
        # book. Saying so is the difference between a finding and a silence.
        logger.warning(
            f"select: {target.book} was compared against members in "
            f"{', '.join(sorted(books_seen))}; books are distinct documents, so nothing can match"
        )

    return found


def _same_book(a: Range, b: Range) -> bool:
    return a.book == b.book


def _chapters(book: str, scheme: str, reference: str) -> list:
    chapters = packaged_scheme(scheme).max_verses.get(book)
    if not chapters:
        raise ValueError(
            f"{reference!r}: versification scheme {scheme!r} does not carry book {book}"
        )
    return chapters


def _ordinal(book: str, chapter: int, verse: int, chapters: list, reference: str) -> int:
    """The verse's position counted from the first verse of its book."""
    if chapter < 1 or chapter > len(chapters):
        raise ValueError(
            f"{reference!r}: {book} has {len(chapters)} chapters, so there is no chapter {chapter}"
        )
    in_chapter = int(chapters[chapter - 1])
    if verse < 1 or verse > in_chapter:
        raise ValueError(
            f"{reference!r}: {book} {chapter} has {in_chapter} verses, so there is no verse {verse}"
        )
    return sum(int(n) for n in chapters[: chapter - 1]) + verse
