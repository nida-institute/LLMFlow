"""The Semantic Dictionary of the Greek New Testament, read for `include: [senses]` (#272).

A Louw-Nida code names a meaning, and SDGNT files each meaning under a headword. One code can be
filed under several headwords, each with its own definition, so a word's entries are found by its
lemma and the code together. Where the lemma does not match, a code filed under exactly one
headword is still that meaning; a code filed under several cannot be chosen between.

Both sides write some codes with a `{N:001}`-style suffix, and on different codes, so the suffix
is not part of the code on either side.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Any, Optional

from lxml import etree  # type: ignore[attr-defined]

#: The suffix some codes carry, which names nothing the join needs.
SUFFIX = re.compile(r"\{N:\d+\}")

#: The language whose definitions and glosses an entry carries.
LANGUAGE = "en"


def codes(value: Any) -> list:
    """The Louw-Nida codes *value* names, space-separated, each without its suffix."""
    return SUFFIX.sub("", str(value or "")).split()


def _nfc(text: Any) -> str:
    return unicodedata.normalize("NFC", str(text or ""))


def _text(node: Optional[Any]) -> str:
    return (node.text or "").strip() if node is not None else ""


def _record(lemma: str, code: str, meaning: Any) -> dict:
    """One meaning as an entry, leaving out any field the dictionary leaves empty."""
    sense = meaning.find(f"LEXSenses/LEXSense[@LanguageCode='{LANGUAGE}']")
    fields = {
        "code": code,
        "lemma": lemma,
        "domain": _text(meaning.find("LEXDomains/LEXDomain")),
        "subdomain": _text(meaning.find("LEXSubDomains/LEXSubDomain")),
        "definition": _text(sense.find("DefinitionShort")) if sense is not None else "",
        "glosses": [_text(gloss) for gloss in sense.iter("Gloss") if _text(gloss)]
        if sense is not None
        else [],
        "biblical_term": meaning.get("IsBiblicalTerm") or "",
    }
    return {key: value for key, value in fields.items() if value}


@lru_cache(maxsize=4)
def load(path: str) -> tuple:
    """`(by lemma and code, by code then lemma)` for the dictionary at *path*."""
    by_pair: dict = {}
    by_code: dict = {}
    for entry in etree.parse(path).iter("Lexicon_Entry"):
        lemma = _nfc(entry.get("Lemma"))
        for meaning in entry.iter("LEXMeaning"):
            found = codes(meaning.get("EntryCode"))
            if not found:
                continue
            record = _record(lemma, found[0], meaning)
            by_pair.setdefault((lemma, found[0]), record)
            by_code.setdefault(found[0], {}).setdefault(lemma, record)
    return by_pair, by_code


def entries(lemma: Any, ln: Any, dictionary: tuple) -> tuple:
    """`(entries, unresolved)` for a word's *lemma* and its `ln` column.

    One entry per code, in the order `ln` names them. `unresolved` lists `(code, headwords)` for
    each code with no entry: the headwords it is filed under, none when it is absent.
    """
    by_pair, by_code = dictionary
    word = _nfc(lemma)
    found: list = []
    unresolved: list = []
    for code in codes(ln):
        record = by_pair.get((word, code))
        if record is None:
            headwords = by_code.get(code, {})
            if len(headwords) == 1:
                record = next(iter(headwords.values()))
            else:
                unresolved.append((code, sorted(headwords)))
                continue
        found.append(dict(record))
    return found, unresolved
