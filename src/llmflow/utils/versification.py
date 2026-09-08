"""Mapping a reference between versification schemes.

A reference is not a location until a scheme is named: `PSA 51:1` in English is `PSA 51:3` in
the original, and Malachi has four chapters in one and three in the other. See §3.-1 of
`project/plans/plan-scripture-step.md`.

Scheme files are the Copenhagen Alliance mappings, read from `$SP_HOME/versification/` rather
than bundled. Each file's `mappedVerses` maps that scheme to the hub, so any two schemes are
two lookups.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, NoReturn, Optional

from llmflow import paths as _paths
from llmflow.modules.logger import Logger

logger = Logger()

#: The scheme every other scheme maps to and from: the original-language versification.
HUB_SCHEME = "org"

MAPPINGS_DIRNAME = "versification"

class UnmappableReference(ValueError):
    """Raised when a reference cannot be placed in the target scheme."""


@dataclass(frozen=True)
class Scheme:
    name: str
    max_verses: Mapping[str, list] = field(default_factory=dict)
    excluded_verses: frozenset = frozenset()
    #: One entry per verse, this scheme -> every hub verse it names, with ranges already expanded.
    #:
    #: Many-valued in both directions, because both occur in the shipped data. `PSA 89:0-1 =>
    #: PSA 90:0` joins two verses into one, so both keys hold the same single target;
    #: `PSA 141:0 => PSA 142:0-1` divides one into two, so one key holds both. Holding a single
    #: string could express the first but not the second, and `_pairs` refused both.
    to_hub: Mapping[str, list] = field(default_factory=dict)

    @property
    def from_hub(self) -> dict:
        """Hub -> every verse of this scheme that maps to it, in the file's own order.

        Many-valued, and not an inversion of `to_hub`: `DAN 4:4` is reached from both
        `DAG 4:1` and `DAG 4:7`, which are not adjacent, so neither a single answer nor a
        span would be true to the data.
        """
        reverse: dict = {}
        for own, hub_verses in self.to_hub.items():
            for hub in hub_verses:
                if own not in reverse.setdefault(hub, []):
                    reverse[hub].append(own)
        return reverse

    def contains(self, book: str, chapter: int, verse: int) -> bool:
        """Whether the scheme's own `maxVerses` covers this reference."""
        chapters = self.max_verses.get(book)
        if not chapters:
            # A book the scheme does not describe is not evidence that the verse is wrong.
            return True
        if not 1 <= chapter <= len(chapters):
            return False
        # Verse 0 is a superscription, which `maxVerses` does not count.
        return 0 <= verse <= int(chapters[chapter - 1])


def default_mappings_dir() -> Path:
    return _paths.sp_home() / MAPPINGS_DIRNAME


def packaged_mappings_dir() -> Path:
    """The schemes bundled in the wheel, reachable without a store or a resource.

    `parse_bible_reference` has no resource and must still resolve an extent, so it reads these
    rather than `$SP_HOME`: a custom versification is resource-scoped, so a caller with no
    resource only ever needs the shipped standard schemes.
    """
    import llmflow

    return Path(llmflow.__file__).resolve().parent / "templates" / "sp" / MAPPINGS_DIRNAME


def packaged_scheme_names() -> tuple:
    """Every scheme name the package ships, from the directory rather than a second list."""
    return tuple(sorted(p.stem for p in packaged_mappings_dir().glob("*.json")))


@lru_cache(maxsize=None)
def packaged_scheme(name: str) -> Scheme:
    """A shipped scheme, read once per process — the parser consults one on every call."""
    return load_scheme(name, packaged_mappings_dir())


@dataclass(frozen=True)
class PassageRef:
    """A parsed reference. ``None`` chapter means the whole book; ``None`` verse, the whole
    chapter."""

    book: str
    start_chapter: Optional[int]
    start_verse: Optional[int]
    end_chapter: Optional[int]
    end_verse: Optional[int]
    start_part: str = ""
    end_part: str = ""

    def covers(self, chapter: int, verse: int) -> bool:
        if self.start_chapter is None:
            return True
        if chapter < self.start_chapter or chapter > (self.end_chapter or self.start_chapter):
            return False
        if self.start_verse is None:
            return True
        if chapter == self.start_chapter and verse < self.start_verse:
            return False
        end_c = self.end_chapter or self.start_chapter
        end_v = self.end_verse
        if end_v is not None and chapter == end_c and verse > end_v:
            return False
        return True


#: The numeric tail of a reference: `1`, `1:1`, `1:1a`, `1:1-8`, `1:40-2:12`.
#:
#: Splitting the string here rather than matching the book with a pattern is what lets a book be
#: named either way. A pattern over the book cannot tell `MRK` from `XYZ`, and the version that
#: tried turned `Mark` into book `MARK`, which nothing resolves; a pattern loose enough to
#: accept `Song of Songs` accepts anything at all. The tail, though, has a fixed shape — so take
#: the tail, and whatever precedes it is the book, looked up rather than guessed.
_TAIL = re.compile(
    r"^(?P<c1>\d+)"
    r"(?::(?P<v1>\d+)(?P<p1>[a-z])?)?"
    r"(?:\s*-\s*(?:(?P<c2>\d+):)?(?P<v2>\d+)(?P<p2>[a-z])?)?$"
)

#: A USFM book code: three characters, upper case, starting with a letter or digit. Accepted
#: even when `llmflow.books` does not name it — a canon may carry books this engine has never
#: heard of, and a versification scheme or a project's own text may use them.
_CODE = re.compile(r"^[A-Z1-9][A-Z0-9]{2}$")


def parse_passage_ref(passage: str) -> PassageRef:
    """Parse ``"MRK 1:1-8"`` and friends.

    Deliberately strict: an unrecognised string raises rather than being coerced into
    something plausible, because a silently wrong range yields analysis of the wrong text.
    """
    text = " ".join((passage or "").split())
    written, tail = _split_tail(text)
    code = _book_code(written)

    if code is None or (tail is None and " " in text and not _CODE.match(written)):
        _refuse(passage, text)

    if tail is None:
        return PassageRef(code, None, None, None, None, "", "")

    g = tail.groupdict()
    c1 = int(g["c1"])
    v1 = int(g["v1"]) if g.get("v1") else None
    c2 = int(g["c2"]) if g.get("c2") else c1
    v2 = int(g["v2"]) if g.get("v2") else v1
    p1 = g.get("p1") or ""
    p2 = g.get("p2") or ""
    return PassageRef(code, c1, v1, c2, v2, p1, p2 or p1)


def _split_tail(text: str):
    """`("Mark", <1:40-2:12>)`. The tail is the last token when it has the numeric shape.

    Taking the *last* token is what makes `1 John 1:1` work: its book begins with a digit, so
    scanning forwards for the first number finds the book, not the reference.
    """
    if " " in text:
        written, _, last = text.rpartition(" ")
        match = _TAIL.match(last)
        if match:
            return written, match
    return text, None


def _book_code(written: str):
    """The USFM code *written* names, whether it was written as a name or as a code."""
    from llmflow import books as _books

    resolved = _books.resolve(written)
    if resolved:
        return resolved
    # A code this engine does not name is still a code: a canon may carry books it has never
    # heard of, and a scheme or a project's own text may use them.
    return written if _CODE.match(written) else None


def _refuse(passage: str, text: str) -> NoReturn:

    if "-" in text:
        after = text.rsplit("-", 1)[1].strip()
        second, _ = _split_tail(after)
        if _book_code(second):
            raise ValueError(
                f"{passage!r} spans two books. A passage reference names one book; fetch each "
                f"separately."
            )
    raise ValueError(
        f"{passage!r} is not a passage reference. Expected forms: 'MRK', 'Mark 1', "
        f"'Mark 1:1', 'MRK 1:1-8', 'Mark 1:40-2:12' — a book name or its USFM code."
    )



def as_single_verse(reference: str) -> tuple:
    """*reference* as (book, chapter, verse, part), refusing anything that is not one verse.

    The mapper works verse by verse, so a range or a whole chapter has no single answer to give.
    Parsing is the lean parser's; this only narrows what it returns.
    """
    try:
        ref = parse_passage_ref(reference)
    except ValueError as error:
        raise UnmappableReference(f"{reference!r} is not a reference to a single verse: {error}")
    if ref.start_chapter is None or ref.start_verse is None:
        raise UnmappableReference(
            f"{reference!r} is not a reference to a single verse "
            f"(expected e.g. 'PSA 51:1' or 'ESG 1:1a')."
        )
    if (ref.end_chapter, ref.end_verse, ref.end_part) != (
        ref.start_chapter,
        ref.start_verse,
        ref.start_part,
    ):
        raise UnmappableReference(
            f"{reference!r} is a range, not a reference to a single verse."
        )
    return ref.book, ref.start_chapter, ref.start_verse, ref.start_part


def format_reference(book: str, chapter: int, verse: int, segment: str = "") -> str:
    return f"{book} {chapter}:{verse}{segment}"


def _expand(entry: str) -> list[str]:
    """One mapping key or value as the list of single-verse references it names.

    A mapping entry is one verse or a run of them within a chapter; every shipped scheme is
    written that way, and a range crossing a chapter has no single run to expand.
    """
    try:
        ref = parse_passage_ref(entry.strip())
    except ValueError as error:
        raise UnmappableReference(f"{entry!r} in a mapping file is not a reference: {error}")
    if ref.start_chapter is None or ref.start_verse is None:
        raise UnmappableReference(
            f"{entry!r} in a mapping file names no verse; a mapping is verse to verse."
        )
    if ref.end_chapter != ref.start_chapter:
        raise UnmappableReference(
            f"{entry!r} in a mapping file crosses a chapter boundary, which a mapping entry "
            f"cannot express."
        )
    if ref.end_verse is not None and ref.end_verse != ref.start_verse:
        return [
            format_reference(ref.book, ref.start_chapter, verse)
            for verse in range(ref.start_verse, ref.end_verse + 1)
        ]
    return [format_reference(ref.book, ref.start_chapter, ref.start_verse, ref.start_part)]


def _pairs(mapped_verses, scheme_name: str) -> dict:
    """`{"PSA 51:1-19": "PSA 51:3-21"}` as nineteen single-verse pairs, each verse to a list.

    Takes a mapping, or an iterable of `(own, hub)` pairs where one left-hand side may be
    stated more than once — which is how a `custom.vrs` writes a merge and a mapping cannot.

    Three shapes are meaningful, and the third used to be refused with the second:

    - **verse for verse**, equal runs: paired in order.
    - **a run joining into one verse** — `PSA 89:0-1 => PSA 90:0` — every verse of the run names
      that one. Common: `DAG 13:1-63 => SUS 1:63` folds a whole chapter of Greek Daniel into one
      verse of Susanna.
    - **one verse dividing into a run** — `PSA 141:0 => PSA 142:0-1` — that verse names both.

    Anything else is skipped and reported. Five verses to six does not say which verse gained, and
    a range written backwards names none, so both would be guesses — which is what the skip is for.
    A reference the scheme cannot place must not silently pass through as itself.
    """
    pairs: dict = {}
    skipped = []
    entries = (
        mapped_verses.items()
        if isinstance(mapped_verses, Mapping)
        else list(mapped_verses or ())
    )
    for own_entry, hub_entry in entries:
        try:
            own, hub = _expand(own_entry), _expand(hub_entry)
        except UnmappableReference as error:
            skipped.append(f"{own_entry!r} -> {hub_entry!r} ({error})")
            continue

        if len(own) == len(hub):
            joined = zip(own, [[one] for one in hub])
        elif len(hub) == 1 and own:
            joined = zip(own, [list(hub) for _ in own])
        elif len(own) == 1 and hub:
            joined = zip(own, [list(hub)])
        else:
            skipped.append(
                f"{own_entry!r} ({len(own)} verses) -> {hub_entry!r} ({len(hub)} verses)"
            )
            continue

        for verse, targets in joined:
            for target in targets:
                if target not in pairs.setdefault(verse, []):
                    pairs[verse].append(target)

    if skipped:
        logger.warning(
            f"Versification scheme {scheme_name!r}: {len(skipped)} mapping "
            f"{'entry' if len(skipped) == 1 else 'entries'} skipped because the two sides cover "
            f"numbers of verses that name no join. References in these ranges are left "
            f"unmapped:\n  " + "\n  ".join(skipped)
        )
    return pairs


#: Specification fields this module does not yet interpret. A scheme carrying one is read
#: without it, which is not the same as the field being absent — so loading says so.
UNREAD_FIELDS = ("mergedVerses", "partialVerses")


def _warn_about_unread_fields(scheme_name: str, document: Mapping[str, Any]) -> None:
    present = [
        f"{field} ({len(document[field])})"
        for field in UNREAD_FIELDS
        if document.get(field)
    ]
    if present:
        logger.warning(
            f"Versification scheme {scheme_name!r} declares {' and '.join(present)}, which this "
            f"engine does not yet interpret. References those entries govern are mapped as "
            f"though the field were absent."
        )


def load_scheme(name: str, mappings_dir: Optional[Path] = None) -> Scheme:
    """Read a scheme, folding in whatever it declares `basedOn`.

    A base supplies the verses the derived scheme does not mention, so a mapping listing one
    verse inherits the rest rather than mapping everything else to itself.
    """
    directory = Path(mappings_dir) if mappings_dir else default_mappings_dir()

    inherited: dict = {}
    max_verses: dict = {}
    excluded: set = set()
    seen: list[str] = []
    current: Optional[str] = name

    # Walk the basedOn chain to its root, then fold back down so the derived scheme wins.
    chain = []
    while current:
        if current in seen:
            raise UnmappableReference(
                f"Versification scheme {current!r} is in a `basedOn` cycle: "
                f"{' -> '.join(seen + [current])}."
            )
        seen.append(current)
        document = _read(current, directory, wanted_by=seen[-2] if len(seen) > 1 else None)
        chain.append((current, document))
        current = document.get("basedOn")

    for scheme_name, document in reversed(chain):
        max_verses.update(document.get("maxVerses") or {})
        excluded.update(document.get("excludedVerses") or [])
        inherited.update(_pairs(document.get("mappedVerses") or {}, scheme_name))
        _warn_about_unread_fields(scheme_name, document)

    return Scheme(
        name=name,
        max_verses=max_verses,
        excluded_verses=frozenset(excluded),
        to_hub=inherited,
    )


def _read(name: str, directory: Path, wanted_by: Optional[str] = None) -> dict:
    path = directory / f"{name}.json"
    if not path.is_file():
        available = ", ".join(sorted(p.stem for p in directory.glob("*.json"))) or "(none)"
        wanted = f" (declared as the base of {wanted_by!r})" if wanted_by else ""
        raise UnmappableReference(
            f"Versification scheme {name!r}{wanted} has no mapping file in {directory}.\n"
            f"  Available: {available}"
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise UnmappableReference(f"Versification scheme {name!r} at {path} is not valid JSON: {error}")


_CHAPTER_LENGTH = re.compile(r"^(\d+):(\d+)$")

#: Ends a chapter-length line in a `.vrs` file. A terminator, not a chapter.
_LINE_END = "END"


@dataclass(frozen=True)
class CustomOverlay:
    """What a Paratext `custom.vrs` states, as its four constructs.

    Chapter lengths are held per chapter rather than as a list per book: a line names any
    chapters in any order, and most name neither chapter 1 nor a consecutive run, so a list
    could not say which chapters went unmentioned.

    Mappings are ordered pairs rather than a mapping, because one left-hand side may be stated
    twice — two lines naming two hub verses for one project verse, which is a merge.
    """

    chapter_lengths: Mapping[str, Mapping[int, int]] = field(default_factory=dict)
    excluded_verses: frozenset = frozenset()
    partial_verses: Mapping[str, tuple] = field(default_factory=dict)
    mapped_verses: tuple = ()

    def states_nothing(self) -> bool:
        """Whether the file declared no numbering — comments and blank lines only.

        A project whose overlay states nothing is numbered by its base after all, so it is not
        a numbering of its own and has no need of the project's name.
        """
        return not (
            self.chapter_lengths
            or self.excluded_verses
            or self.partial_verses
            or self.mapped_verses
        )


def _vrs_book(token: str) -> Optional[str]:
    """The USFM code a `.vrs` book token names, or None when it is not code-shaped.

    A `.vrs` names books by code and never by name, so this does not consult the name
    resolver: `PSS` is the code for Psalms of Solomon, while as a *name* it is ambiguous with
    Psalms and would raise. Case is normalised because real files write `1Sa`.
    """
    code = (token or "").upper()
    return code if _CODE.match(code) else None


def _overlay_verse(reference: str, source: Path, number: int) -> str:
    """One reference from a `.vrs` line, in the form the rest of this module writes."""
    try:
        book, chapter, verse, segment = as_single_verse(reference)
    except (ValueError, UnmappableReference) as error:
        raise UnmappableReference(f"{source}:{number}: {error}")
    return format_reference(book, chapter, verse, segment)


def read_custom_vrs(path) -> CustomOverlay:
    """Read a Paratext `custom.vrs`.

    Four constructs, which are the four the Copenhagen specification's `json2vrs.py` writes:

        GEN 1:31 2:25 3:24 ... 50:26 END    chapter lengths, any chapters, optional terminator
        -MAT 17:21                          a verse the project does not have
        *PSA 3:1,-,a,b                      a verse published in segments
        REV 13:1 = REV 12:18                a mapping, left side the project's, right side hub

    Comments run from `#` to end of line, lines may be indented, and a leading byte order mark
    is discarded. A line matching none of the four is refused with its number rather than
    skipped, because a construct read as nothing is a project's numbering silently ignored.
    """
    source = Path(path)
    if not source.is_file():
        raise UnmappableReference(f"No custom versification file at {source}.")

    chapter_lengths: dict = {}
    excluded: list = []
    partial: dict = {}
    mapped: list = []

    text = source.read_text(encoding="utf-8-sig", errors="replace")
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue

        if line.startswith("*"):
            reference, _, segments = line[1:].partition(",")
            partial[_overlay_verse(reference, source, number)] = tuple(
                part.strip() for part in segments.split(",") if part.strip()
            )
            continue

        if line.startswith("-"):
            excluded.append(_overlay_verse(line[1:], source, number))
            continue

        if "=" in line:
            own, _, hub = line.partition("=")
            mapped.append((own.strip(), hub.strip()))
            continue

        book, *tokens = line.split()
        code = _vrs_book(book)
        if code is None or not tokens:
            raise UnmappableReference(
                f"{source}:{number}: {line!r} is not a versification line. Expected a book with "
                f"`chapter:verses` pairs, `-BOOK C:V`, `*BOOK C:V,a,b`, or `A = B`."
            )
        chapters = chapter_lengths.setdefault(code, {})
        for token in tokens:
            if token == _LINE_END:
                continue
            stated = _CHAPTER_LENGTH.match(token)
            if not stated:
                raise UnmappableReference(
                    f"{source}:{number}: {token!r} is not a `chapter:verses` pair in a chapter "
                    f"length line for {code}."
                )
            chapters[int(stated.group(1))] = int(stated.group(2))

    return CustomOverlay(
        chapter_lengths=chapter_lengths,
        excluded_verses=frozenset(excluded),
        partial_verses=partial,
        mapped_verses=tuple(mapped),
    )


def fold_custom(base: Scheme, overlay: CustomOverlay, name: str) -> Scheme:
    """*base* with *overlay* applied, labelled *name*.

    The overlay wins where it speaks, which is what `load_scheme` already does for a `basedOn`
    chain: a chapter length and a verse's mapping are replaced, excluded verses are added to.
    Assigning onto the base's resolved chapter list is what makes a sparse override cheap — a
    line naming two chapters of thirty-six costs two assignments, not a restatement of the book.

    A chapter the base neither covers nor immediately follows is refused: the chapters in
    between would have to be given lengths nothing states.
    """
    max_verses = {book: list(chapters) for book, chapters in base.max_verses.items()}

    for book, stated in overlay.chapter_lengths.items():
        chapters = max_verses.setdefault(book, [])
        for chapter in sorted(stated):
            # Shipped scheme files write verse counts as strings, and `contains` coerces. The
            # folded scheme keeps that encoding so one book's chapters are not half of each.
            length = str(stated[chapter])
            if chapter <= len(chapters):
                chapters[chapter - 1] = length
            elif chapter == len(chapters) + 1:
                chapters.append(length)
            else:
                raise UnmappableReference(
                    f"Versification overlay {name!r} states {book} {chapter}:{stated[chapter]}, "
                    f"but {base.name!r} describes {len(chapters)} chapters of {book}. Chapters "
                    f"{len(chapters) + 1}-{chapter - 1} would have to be invented."
                )

    to_hub = {verse: list(targets) for verse, targets in base.to_hub.items()}
    to_hub.update(_pairs(overlay.mapped_verses, name))

    _warn_about_unread_fields(name, {"partialVerses": overlay.partial_verses})

    return Scheme(
        name=name,
        max_verses=max_verses,
        excluded_verses=frozenset(base.excluded_verses | overlay.excluded_verses),
        to_hub=to_hub,
    )


def scheme_name(scheme) -> str:
    """The name of a scheme given either as a name or as a `Scheme`.

    A scheme folded from a project's `custom.vrs` has no file to be named by, so it travels as
    an object. Everything that reports or compares a scheme goes through here, so a message
    never shows a dataclass where a reader expects a name.
    """
    return scheme.name if isinstance(scheme, Scheme) else str(scheme)


def _as_scheme(scheme, mappings_dir: Optional[Path] = None) -> Scheme:
    """A scheme given as a name or as a `Scheme`, as a `Scheme`."""
    return scheme if isinstance(scheme, Scheme) else load_scheme(str(scheme), mappings_dir)


def map_candidates(
    reference: str,
    from_scheme,
    to_scheme,
    mappings_dir: Optional[Path] = None,
) -> list:
    """Every verse of *to_scheme* that *reference* corresponds to, in the mapping's own order.

    Usually one. More than one where the target scheme divides what the source joins, and those
    are not always adjacent, so a caller wanting a single answer must choose deliberately.

    Either scheme may be a name or a `Scheme`. A project's own numbering has no file to be named
    by, so it arrives as an object.
    """
    from_name, to_name = scheme_name(from_scheme), scheme_name(to_scheme)

    if from_name == to_name:
        as_single_verse(reference)  # Reject a malformed reference even when nothing moves.
        return [str(reference).strip()]

    source = _as_scheme(from_scheme, mappings_dir)
    book, chapter, verse, segment = as_single_verse(reference)
    own = format_reference(book, chapter, verse, segment)

    if own in source.excluded_verses:
        raise UnmappableReference(f"{own} does not exist in versification scheme {from_name!r}.")
    if not source.contains(book, chapter, verse):
        raise UnmappableReference(
            f"{own} is outside versification scheme {from_name!r}: "
            f"{book} {chapter} has {_extent(source, book, chapter)}."
        )

    # A verse may name several hub verses where the schemes divide it differently, and each of
    # those may be reached from several verses of the target. Order follows the mapping file's.
    in_hub = [own] if from_name == HUB_SCHEME else list(source.to_hub.get(own) or [own])
    if to_name == HUB_SCHEME:
        return in_hub

    target = _as_scheme(to_scheme, mappings_dir)
    found: list = []
    for hub in in_hub:
        for candidate in target.from_hub.get(hub) or [hub]:
            if candidate not in found:
                found.append(candidate)
    return found


def map_reference(
    reference: str,
    from_scheme,
    to_scheme,
    mappings_dir: Optional[Path] = None,
) -> str:
    """*reference*, read in *from_scheme*, expressed as the one verse of *to_scheme* it names.

    A verse the source scheme does not list is already aligned with the hub and passes through
    unchanged. A verse outside the source scheme, and a verse the target scheme reaches from
    more than one place, both raise rather than returning something that looks like an answer.

    Either scheme may be a name or a `Scheme`.
    """
    candidates = map_candidates(reference, from_scheme, to_scheme, mappings_dir)
    if len(candidates) > 1:
        raise UnmappableReference(
            f"{reference} in {scheme_name(from_scheme)!r} corresponds to {len(candidates)} "
            f"verses in {scheme_name(to_scheme)!r}: {', '.join(candidates)}. Use "
            f"`map_candidates` and choose, or name a passage range."
        )
    return candidates[0]


def _extent(scheme: Scheme, book: str, chapter: int) -> str:
    chapters = scheme.max_verses.get(book) or []
    if not 1 <= chapter <= len(chapters):
        return f"no chapter {chapter} ({len(chapters)} chapters in {book})"
    return f"{chapters[chapter - 1]} verses"
