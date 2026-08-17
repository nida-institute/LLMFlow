"""Named scripture editions: a reference range in, running text out (LLMFlow#200).

Three consumer repos each built this, and each converged on a dict or list keyed by verse —
the shape ``docs/ai-context/rules.md`` forbids, because chopping running text at verse
boundaries destroys the sentence and clause structure the analysis depends on.

That was not carelessness. While every project loads raw assets itself, every project
inherits the asset's shape: ``discourse-flow`` reads a verse-per-line BSB file and returns
``{"Mark 1:1": "..."}`` because that is what the file is. This module exists so the engine
is the layer that turns an asset into running text with verse milestones, and the convention
stops being advisory.

**Joining is data, not logic.** The Macula TSVs carry a ``text`` column and an ``after``
column; the running text is their concatenation, in order. ``after`` holds the space, the
maqqef, the sof pasuq, the Greek comma. So there is no whitespace to infer and no
per-language branching — one code path serves Hebrew and Greek, and the awkward cases
(``עַל־פְּנֵי`` joined, ``הָאָֽרֶץ׃`` attached) come out right because the source says so.

Sources are the Captain's choice and must not be substituted by an assistant. Editions
resolve through the registry rather than through paths written into code — partly so a
pipeline is not pinned to one machine, as ``ears-to-hear`` and ``discourse-flow`` currently
are, and partly so the source stays configuration the Captain controls.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

#: Verse-milestone form. Inherited from the ears-to-hear convention; declared once so it can
#: be changed by decision rather than by search-and-replace. Whether it is canonical for the
#: engine is an open question in project/plans/design-scripture-editions.md.
MILESTONE_TEMPLATE = "⌊{chapter}:{verse}⌋"

#: Representations offered. Deliberately absent: any per-verse container. A caller who needs
#: verse records can derive them; the engine must not make that the easy path.
FORMATS = ("plain", "milestones")


class EditionNotRegistered(KeyError):
    """Raised when an edition has no registry entry, listing what is available."""

    def __str__(self) -> str:  # KeyError repr would quote the message
        return self.args[0] if self.args else ""


@dataclass(frozen=True)
class PassageRef:
    """A parsed reference. ``None`` chapter means the whole book; ``None`` verse, the whole
    chapter."""

    book: str
    start_chapter: Optional[int]
    start_verse: Optional[int]
    end_chapter: Optional[int]
    end_verse: Optional[int]

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


_BOOK = r"(?P<book>[A-Z1-9][A-Za-z0-9]{1,4})"
_PATTERNS = (
    # MRK 1:40-2:12
    re.compile(rf"^{_BOOK}\s+(?P<c1>\d+):(?P<v1>\d+)\s*-\s*(?P<c2>\d+):(?P<v2>\d+)$"),
    # MRK 1:1-8
    re.compile(rf"^{_BOOK}\s+(?P<c1>\d+):(?P<v1>\d+)\s*-\s*(?P<v2>\d+)$"),
    # MRK 1:1
    re.compile(rf"^{_BOOK}\s+(?P<c1>\d+):(?P<v1>\d+)$"),
    # MRK 1
    re.compile(rf"^{_BOOK}\s+(?P<c1>\d+)$"),
    # PHM
    re.compile(rf"^{_BOOK}$"),
)


def parse_passage_ref(passage: str) -> PassageRef:
    """Parse ``"MRK 1:1-8"`` and friends.

    Deliberately strict: an unrecognised string raises rather than being coerced into
    something plausible, because a silently wrong range yields analysis of the wrong text.
    """
    text = (passage or "").strip()
    for pattern in _PATTERNS:
        m = pattern.match(text)
        if not m:
            continue
        g = m.groupdict()
        c1 = int(g["c1"]) if g.get("c1") else None
        v1 = int(g["v1"]) if g.get("v1") else None
        c2 = int(g["c2"]) if g.get("c2") else c1
        v2 = int(g["v2"]) if g.get("v2") else v1
        return PassageRef(g["book"].upper(), c1, v1, c2, v2)
    raise ValueError(
        f"{passage!r} is not a passage reference. Expected forms: 'MRK', 'MRK 1', "
        f"'MRK 1:1', 'MRK 1:1-8', 'MRK 1:40-2:12'."
    )


def _split_ref(ref: str) -> tuple[str, Optional[int], Optional[int]]:
    """``"GEN 1:1!3"`` -> ``("GEN", 1, 1)``. The ``!n`` word index is discarded."""
    head = (ref or "").split("!", 1)[0].strip()
    if " " not in head:
        return head.upper(), None, None
    book, _, cv = head.partition(" ")
    if ":" not in cv:
        return book.upper(), (int(cv) if cv.isdigit() else None), None
    c, _, v = cv.partition(":")
    try:
        return book.upper(), int(c), int(v)
    except ValueError:
        return book.upper(), None, None


def filter_rows(rows: Iterable[Mapping[str, Any]], ref: PassageRef) -> list[dict]:
    """Keep the rows inside *ref*, in source order."""
    kept = []
    for row in rows:
        book, chapter, verse = _split_ref(row.get("ref", ""))
        if book != ref.book:
            continue
        if chapter is None:
            continue
        if ref.covers(chapter, verse if verse is not None else 1):
            kept.append(dict(row))
    return kept


def rows_to_text(rows: Sequence[Mapping[str, Any]], fmt: str = "milestones") -> str:
    """Concatenate ``text + after`` into running text.

    ``after`` is taken verbatim. A missing ``after`` contributes nothing — **not** a space:
    inserting one would break the joined forms (``עַל־פְּנֵי``) that are the whole reason
    this column exists.

    With ``fmt="milestones"`` a ``⌊chapter:verse⌋`` marker precedes each verse. A separating
    space is inserted before the marker when the preceding text does not already end in
    whitespace, so the last word of a verse does not fuse onto the next marker.
    """
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r}; expected one of {', '.join(FORMATS)}")

    parts: list[str] = []
    current: Optional[tuple[int, int]] = None
    for row in rows:
        _, chapter, verse = _split_ref(row.get("ref", ""))
        if fmt == "milestones" and chapter is not None and verse is not None:
            if (chapter, verse) != current:
                current = (chapter, verse)
                if parts and not parts[-1][-1:].isspace():
                    parts.append(" ")
                parts.append(MILESTONE_TEMPLATE.format(chapter=chapter, verse=verse))
                parts.append(" ")
        parts.append(str(row.get("text") or ""))
        parts.append(str(row.get("after") or ""))
    return "".join(parts).strip()


def resolve_edition(
    edition: str,
    registry_editions: Optional[Mapping[str, Any]] = None,
) -> Any:
    """Return the definition for a named edition.

    A definition is either a path string — a Macula-style TSV — or a mapping carrying a
    ``kind`` (``"tsv"`` or ``"usfm"``) plus what that backend needs. Two backends exist
    because the Captain's chosen sources are not one shape: WLC and SBLGNT come from Macula
    TSVs, BSB from per-book USFM.

    *registry_editions* is passed in rather than read here, so this stays pure and testable.
    The error names what is available: a bare KeyError sends the reader to the source instead
    of to their configuration.
    """
    available = dict(registry_editions or {})
    if edition in available:
        return available[edition]
    known = ", ".join(sorted(available)) or "(none registered)"
    raise EditionNotRegistered(
        f"Scripture edition {edition!r} is not registered.\n"
        f"  Registered editions: {known}\n"
        f"  Register one with `sp registry` so the path is not written into a pipeline."
    )


def usj_to_text(usj: Mapping[str, Any], fmt: str = "milestones") -> str:
    """Flatten a USJ document into running text.

    The USFM backend's counterpart to ``rows_to_text``. USJ nests strings inside ``para``
    elements with ``verse`` markers interleaved, so a verse boundary is a marker in a stream
    rather than a column on a row — but the output contract is identical: running text, verse
    positions marked, never a per-verse container.

    Chapter number is tracked from ``chapter`` elements, because a ``verse`` element carries
    only its own number.
    """
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r}; expected one of {', '.join(FORMATS)}")

    parts: list[str] = []
    chapter = {"n": None}  # boxed so the closure can assign

    def walk(node: Any) -> None:
        if isinstance(node, str):
            text = node.strip()
            if not text:
                return
            if parts and not parts[-1][-1:].isspace():
                parts.append(" ")
            parts.append(text)
            return
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, Mapping):
            return
        kind = node.get("type")
        if kind == "chapter":
            chapter["n"] = node.get("number")
            return
        if kind == "verse":
            if fmt == "milestones":
                if parts and not parts[-1][-1:].isspace():
                    parts.append(" ")
                parts.append(
                    MILESTONE_TEMPLATE.format(
                        chapter=chapter["n"] or "?", verse=node.get("number", "?")
                    )
                )
                parts.append(" ")
            return
        walk(node.get("content"))

    walk(usj.get("content"))
    return "".join(parts).strip()


def read_rows(tsv_path: str | Path) -> list[dict]:
    """Read a Macula-style TSV. Only ``ref``, ``text`` and ``after`` are required here."""
    path = Path(tsv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Scripture data file not found: {path}")
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def passage_text(
    edition: str,
    passage: str,
    fmt: str = "milestones",
    registry_editions: Optional[Mapping[str, str]] = None,
) -> str:
    """Running text for *passage* in *edition* — the whole job in one call."""
    path = resolve_edition(edition, registry_editions)
    ref = parse_passage_ref(passage)
    rows = filter_rows(read_rows(path), ref)
    if not rows:
        raise ValueError(
            f"No text found for {passage!r} in edition {edition!r}. "
            f"Check the book code and that the edition covers it "
            f"(WLC is Old Testament only; SBLGNT is New Testament only)."
        )
    return rows_to_text(rows, fmt=fmt)
