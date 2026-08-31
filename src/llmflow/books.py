"""Which book a reference names (#218 follow-up).

SBL-style display names and Paratext-style USFM codes are both what people write, and a
reference is not more or less valid for being written one way. `Mark 1:1-8` and `MRK 1:1-8` name
the same passage, so both resolve here, case-insensitively and ignoring spaces and dots.

This module sits below both parsers deliberately. The table used to be 264 alias keys declared
*inside* `parse_bible_reference`, which meant the read path could not reach it: `parse_passage_ref`
matched a three-to-five character pattern instead and turned `Mark` into book `MARK`, a code
nothing resolves, so a run reported "no text found" for a passage that exists.

It imports nothing from the engine beyond paths and the logger, so anything may import it.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

TABLE_FILENAME = "book-names.json"

#: Spaces, dots and case carry no meaning in a book name: `1 John`, `1John` and `1JN` are one
#: book written three ways. Normalising them away is what lets one table serve both styles.
_INSIGNIFICANT = re.compile(r"[\s.]+")


class AmbiguousBook(ValueError):
    """Raised for an abbreviation that names more than one book.

    Refusing is the point. `Ph` is Philippians or Philemon, and a parser that picks one silently
    sends the whole pipeline to the wrong text.
    """


def table_path() -> Path:
    """The declaration, whether running from a wheel or a dev checkout."""
    import importlib.resources

    try:
        ref = importlib.resources.files("llmflow").joinpath(f"data/{TABLE_FILENAME}")
        path = Path(str(ref))
        if path.exists():
            return path
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent.parent / "data" / TABLE_FILENAME


@lru_cache(maxsize=1)
def _document() -> dict:
    return json.loads(table_path().read_text(encoding="utf-8"))


def table() -> dict:
    """`{USFM code: {number, name, aliases}}`."""
    return _document()["books"]


def normalise(token: str) -> str:
    return _INSIGNIFICANT.sub("", str(token or "")).lower()


@lru_cache(maxsize=1)
def _index() -> dict:
    """Every accepted spelling, normalised, to its USFM code."""
    out: dict = {}
    for code, entry in table().items():
        out[normalise(code)] = code
        for alias in entry.get("aliases", ()):
            out[normalise(alias)] = code
    # Deuterocanonical codes the shipped versification schemes use. They have no display name
    # here — inventing one would be guessing — so they resolve only to themselves, which is all
    # the mapper needs to read every scheme.
    for code in _document().get("other_codes", ()):
        out.setdefault(normalise(code), code)
    return out


@lru_cache(maxsize=1)
def _ambiguous() -> dict:
    return {normalise(k): v for k, v in _document().get("ambiguous", {}).items()}


def resolve(written: str) -> Optional[str]:
    """The USFM code *written* names, or None.

    Raises `AmbiguousBook` for an abbreviation that names several, which is not the same as
    naming none: the caller can tell "I do not know that book" from "say which one you mean".
    """
    key = normalise(written)
    if not key:
        return None
    candidates = _ambiguous().get(key)
    if candidates:
        raise AmbiguousBook(
            f"{written!r} could be {', '.join(candidates)}. Write the book out, or use its "
            f"USFM code."
        )
    return _index().get(key)


def entry(code: str) -> Optional[dict]:
    """Everything declared about one book, or None."""
    return table().get(str(code).upper())


def name(code: str) -> Optional[str]:
    """The canonical display name for a USFM code."""
    found = entry(code)
    return found["name"] if found else None


def number(code: str) -> Optional[str]:
    """The two-digit book number, as filenames and sort keys use it."""
    found = entry(code)
    return found["number"] if found else None


def testament(code: str) -> Optional[str]:
    """`OT` or `NT`, declared rather than inferred from the number.

    This was `int(number) >= 40`, a threshold nothing stated and nothing could correct. A
    deuterocanonical book breaks it outright, and a canon that numbers differently breaks it
    silently — which is the failure mode a declaration removes.
    """
    found = entry(code)
    return found.get("testament") if found else None


def original_language(code: str) -> Optional[str]:
    """The language the book was written in, as declared.

    Declared, and therefore correctable: Ezra and Daniel have Aramaic portions and are declared
    Hebrew here, which is the simplification the previous derivation hid.
    """
    found = entry(code)
    return found.get("original_language") if found else None
