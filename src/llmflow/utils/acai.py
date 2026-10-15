"""Read ACAI and answer which entities a passage names (#272).

ACAI states, for each person, place, group, deity and thing the Bible names, the verses that name
it. The answer for a passage states each entity once and indexes the verses that name it, so an
entity named in ten verses is described once rather than ten times.

`references` are the verses an entity is *named* in. A pronoun referring to it is word-level data
this reader does not serve.

Nothing about verses is implemented here: comparison is `verse_ranges.select`, and mapping the
request into ACAI's scheme is the same mapping the parallel-passages reader makes.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from llmflow import books
from llmflow.modules.logger import Logger
from llmflow.utils.verse_ranges import select

logger = Logger()

#: The declaration's file name among the engine's shipped data.
DECLARATION_FILENAME = "acai.json"

#: The suffix on an `alternate_sources.aquifer` entry naming a Tyndale Bible Dictionary article.
TYNDALE = "TyndaleBibleDictionary"


def declaration() -> Dict[str, Any]:
    """`data/acai.json`: the dataset id, the resources served, the scheme, the categories."""
    from llmflow.utils.scripture import _data_path

    return json.loads(_data_path(DECLARATION_FILENAME).read_text(encoding="utf-8"))


def _verse(bcv: str) -> Optional[str]:
    """A BCV8 reference, `41001004`, as a USFM verse, `MRK 1:4`; None for a book not known."""
    code = _book_codes().get(bcv[:2])
    if code is None:
        return None
    return f"{code} {int(bcv[2:5])}:{int(bcv[5:8])}"


@lru_cache(maxsize=1)
def _book_codes() -> Dict[str, str]:
    return {entry["number"]: code for code, entry in books.table().items() if entry.get("number")}


def _dictionary(entity: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Every Tyndale article the entity names, as `{id, title}`, in ACAI's order."""
    articles = []
    for source in (entity.get("alternate_sources") or {}).get("aquifer") or []:
        identifier, _, rest = str(source).partition("|")
        title, _, collection = rest.rpartition("|")
        if collection == TYNDALE:
            articles.append({"id": identifier, "title": title})
    return articles


def _describe(entity: Mapping[str, Any]) -> Dict[str, Any]:
    """An entity as the payload states it, leaving out any field ACAI leaves empty."""
    english = (entity.get("localizations") or {}).get("eng") or {}
    descriptions = english.get("descriptions") or []
    fields = {
        "type": entity.get("type"),
        "label": english.get("preferred_label"),
        "description": descriptions[0].get("description") if descriptions else None,
        "lemmas": entity.get("lemmas"),
        "dictionary": _dictionary(entity),
    }
    return {key: value for key, value in fields.items() if value}


@lru_cache(maxsize=2)
def load(root: str) -> Dict[str, Any]:
    """The primary entities under *root*, described, plus one row per verse that names one.

    A reference that is not a verse in ACAI's own scheme is dropped, and named in one warning
    here rather than on every lookup.
    """
    from llmflow.utils.verse_ranges import Range

    scheme = declaration()["versification"]
    entities: Dict[str, Dict[str, Any]] = {}
    rows: List[Dict[str, Any]] = []
    dropped: Dict[str, List[str]] = {}
    for category in declaration()["categories"]:
        for path in sorted((Path(root) / category / "json").glob("*.json")):
            entity = json.loads(path.read_text(encoding="utf-8"))
            identifier = entity.get("id")
            if not identifier or identifier != entity.get("primary_id"):
                continue
            entities[identifier] = _describe(entity)
            key = set(entity.get("key_references") or [])
            for bcv in entity.get("references") or []:
                verse = _verse(str(bcv))
                if verse is None:
                    continue
                try:
                    Range.parse(verse, scheme=scheme)
                except ValueError:
                    dropped.setdefault(verse, []).append(identifier)
                    continue
                rows.append(
                    {"reference": verse, "bcv": str(bcv), "id": identifier, "key": bcv in key}
                )
    if dropped:
        described = "; ".join(
            f"{verse} ({', '.join(sorted(names))})" for verse, names in sorted(dropped.items())
        )
        logger.warning(
            f"ACAI at {root} names verses that are not verses in its own scheme, {scheme!r}, so "
            f"those references are left out: {described}."
        )
    return {"entities": entities, "rows": rows}


def entities_for_passage(index: Mapping[str, Any], passage: str, versification: str) -> Dict[str, Any]:
    """`{entities, verses}` for *passage*, written in *versification*; both empty where it names
    nothing.

    Verses are in canonical order, and the entities named in one verse in id order.
    """
    from llmflow.utils.parallel_passages import _probe

    scheme = declaration()["versification"]
    hits = select(index["rows"], _probe(passage, versification), "overlaps", ref="reference", scheme=scheme)
    hits = sorted(hits, key=lambda row: (row["bcv"], row["id"]))

    verses: Dict[str, List[Dict[str, Any]]] = {}
    for row in hits:
        named = verses.setdefault(row["reference"], [])
        if all(item["id"] != row["id"] for item in named):
            named.append({"id": row["id"], "key": row["key"]})
    found = {row["id"] for row in hits}
    return {
        "entities": {identifier: index["entities"][identifier] for identifier in sorted(found)},
        "verses": verses,
    }


def acai_payload(passage: str, root: Any, versification: str) -> Dict[str, Any]:
    """The entities *passage* names, from the ACAI release at *root*."""
    return entities_for_passage(load(str(root)), passage, versification)
