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
from pathlib import Path
from typing import Any, Mapping, Optional

from llmflow import paths as _paths
from llmflow.modules.logger import Logger

logger = Logger()

#: The scheme every other scheme maps to and from: the original-language versification.
HUB_SCHEME = "org"

MAPPINGS_DIRNAME = "versification"

#: `GEN 1:1`, `ESG 1:1a`, `PSA 51:1-19`. Book codes are alphanumeric (`S3Y`, `PS2`, `1CO`), a
#: verse may carry a segment letter, and a range is always within one chapter — verified across
#: every shipped mapping.
REFERENCE = re.compile(
    r"^(?P<book>[A-Z0-9]{3})\s+(?P<chapter>\d+):(?P<verse>\d+)(?P<segment>[a-z]?)"
    r"(?:-(?P<end_verse>\d+)(?P<end_segment>[a-z]?))?$"
)


class UnmappableReference(ValueError):
    """Raised when a reference cannot be placed in the target scheme."""


@dataclass(frozen=True)
class Scheme:
    name: str
    max_verses: Mapping[str, list] = field(default_factory=dict)
    excluded_verses: frozenset = frozenset()
    #: One entry per verse, this scheme -> hub, with every range already expanded.
    to_hub: Mapping[str, str] = field(default_factory=dict)

    @property
    def from_hub(self) -> dict:
        """Hub -> every verse of this scheme that maps to it, in the file's own order.

        Many-valued, and not an inversion of `to_hub`: `DAN 4:4` is reached from both
        `DAG 4:1` and `DAG 4:7`, which are not adjacent, so neither a single answer nor a
        span would be true to the data.
        """
        reverse: dict = {}
        for own, hub in self.to_hub.items():
            reverse.setdefault(hub, []).append(own)
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


def parse_reference(reference: str) -> tuple[str, int, int, str]:
    """Split a single-verse reference into book, chapter, verse and segment letter."""
    match = REFERENCE.match(str(reference).strip())
    if not match or match.group("end_verse"):
        raise UnmappableReference(
            f"{reference!r} is not a reference to a single verse "
            f"(expected e.g. 'PSA 51:1' or 'ESG 1:1a')."
        )
    return (
        match.group("book"),
        int(match.group("chapter")),
        int(match.group("verse")),
        match.group("segment") or "",
    )


def format_reference(book: str, chapter: int, verse: int, segment: str = "") -> str:
    return f"{book} {chapter}:{verse}{segment}"


def _expand(entry: str) -> list[str]:
    """One mapping key or value as the list of single-verse references it names."""
    match = REFERENCE.match(entry.strip())
    if not match:
        raise UnmappableReference(f"{entry!r} in a mapping file is not a reference.")
    book, chapter = match.group("book"), int(match.group("chapter"))
    first, last = int(match.group("verse")), int(match.group("end_verse") or match.group("verse"))
    if match.group("end_verse"):
        return [format_reference(book, chapter, verse) for verse in range(first, last + 1)]
    return [format_reference(book, chapter, first, match.group("segment") or "")]


def _pairs(mapped_verses: Mapping[str, str], scheme_name: str) -> dict:
    """`{"PSA 51:1-19": "PSA 51:3-21"}` as nineteen single-verse pairs.

    An entry whose two sides cover different numbers of verses is skipped, and all such entries
    in one scheme are reported together. Skipping rather than guessing keeps a reference from
    landing where the data does not put it; one bad entry does not make a scheme unusable.
    """
    pairs, skipped = {}, []
    for own_entry, hub_entry in (mapped_verses or {}).items():
        try:
            own, hub = _expand(own_entry), _expand(hub_entry)
        except UnmappableReference as error:
            skipped.append(f"{own_entry!r} -> {hub_entry!r} ({error})")
            continue
        if len(own) != len(hub):
            skipped.append(
                f"{own_entry!r} ({len(own)} verses) -> {hub_entry!r} ({len(hub)} verses)"
            )
            continue
        pairs.update(zip(own, hub))

    if skipped:
        logger.warning(
            f"Versification scheme {scheme_name!r}: {len(skipped)} mapping "
            f"{'entry' if len(skipped) == 1 else 'entries'} skipped because the two sides cover "
            f"different numbers of verses. References in these ranges are left unmapped:\n  "
            + "\n  ".join(skipped)
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


def map_candidates(
    reference: str,
    from_scheme: str,
    to_scheme: str,
    mappings_dir: Optional[Path] = None,
) -> list:
    """Every verse of *to_scheme* that *reference* corresponds to, in the mapping's own order.

    Usually one. More than one where the target scheme divides what the source joins, and those
    are not always adjacent, so a caller wanting a single answer must choose deliberately.
    """
    if from_scheme == to_scheme:
        parse_reference(reference)  # Reject a malformed reference even when nothing moves.
        return [str(reference).strip()]

    source = load_scheme(from_scheme, mappings_dir)
    book, chapter, verse, segment = parse_reference(reference)
    own = format_reference(book, chapter, verse, segment)

    if own in source.excluded_verses:
        raise UnmappableReference(f"{own} does not exist in versification scheme {from_scheme!r}.")
    if not source.contains(book, chapter, verse):
        raise UnmappableReference(
            f"{own} is outside versification scheme {from_scheme!r}: "
            f"{book} {chapter} has {_extent(source, book, chapter)}."
        )

    in_hub = own if from_scheme == HUB_SCHEME else source.to_hub.get(own, own)
    if to_scheme == HUB_SCHEME:
        return [in_hub]

    target = load_scheme(to_scheme, mappings_dir)
    return list(target.from_hub.get(in_hub) or [in_hub])


def map_reference(
    reference: str,
    from_scheme: str,
    to_scheme: str,
    mappings_dir: Optional[Path] = None,
) -> str:
    """*reference*, read in *from_scheme*, expressed as the one verse of *to_scheme* it names.

    A verse the source scheme does not list is already aligned with the hub and passes through
    unchanged. A verse outside the source scheme, and a verse the target scheme reaches from
    more than one place, both raise rather than returning something that looks like an answer.
    """
    candidates = map_candidates(reference, from_scheme, to_scheme, mappings_dir)
    if len(candidates) > 1:
        raise UnmappableReference(
            f"{reference} in {from_scheme!r} corresponds to {len(candidates)} verses in "
            f"{to_scheme!r}: {', '.join(candidates)}. Use `map_candidates` and choose, or name "
            f"a passage range."
        )
    return candidates[0]


def _extent(scheme: Scheme, book: str, chapter: int) -> str:
    chapters = scheme.max_verses.get(book) or []
    if not 1 <= chapter <= len(chapters):
        return f"no chapter {chapter} ({len(chapters)} chapters in {book})"
    return f"{chapters[chapter - 1]} verses"
