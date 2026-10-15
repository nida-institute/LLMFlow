"""Read the Tyndale Open Bible Dictionary and answer articles by title (#272).

Tyndale's release keys an article by a name, `PhilemonPerson`, and has no numeric id. ACAI names
an entity's articles by the Aquifer adaptation's ids and by title, so the title is what joins the
two. Tyndale marks some titles with `*`, and the request is matched without it; the article is
returned with its title as Tyndale wrote it.

An article's body is returned verbatim: the markup inside `<body>`, Tyndale's links included.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from lxml import etree  # type: ignore[attr-defined]

#: The declaration's file name among the engine's shipped data.
DECLARATION_FILENAME = "tyndale.json"

#: The item type that is an article; the rest are letter indexes, charts and pictures.
ARTICLE = "Article"


def declaration() -> Dict[str, Any]:
    """`data/tyndale.json`: the dataset id, where the articles lie, the language, the credit."""
    from llmflow.utils.scripture import _data_path

    return json.loads(_data_path(DECLARATION_FILENAME).read_text(encoding="utf-8"))


def matching_key(title: Any) -> str:
    """A title as a request and an article are matched: without Tyndale's `*`."""
    return " ".join(str(title or "").replace("*", "").split())


def _body(item: Any) -> str:
    """The markup inside an item's `<body>`, as the release writes it."""
    body = item.find("body")
    if body is None:
        return ""
    inner = (body.text or "") + "".join(
        etree.tostring(child, encoding="unicode") for child in body
    )
    return inner.strip()


@lru_cache(maxsize=2)
def load(root: str) -> Dict[str, Dict[str, str]]:
    """`{matching key: {title, name, body}}` for every article under *root*."""
    articles: Dict[str, Dict[str, str]] = {}
    for path in sorted(Path(root).glob(declaration()["articles"])):
        for item in etree.parse(str(path)).getroot().iter("item"):
            if item.get("typename") != ARTICLE:
                continue
            title = (item.findtext("title") or "").strip()
            articles.setdefault(
                matching_key(title), {"title": title, "name": item.get("name") or "", "body": _body(item)}
            )
    return articles


def titles_in(entries: Iterable[Any]) -> List[str]:
    """The titles *entries* names: each a title, or an ACAI `{id, title}` pair."""
    return [
        str(entry.get("title") or "") if isinstance(entry, dict) else str(entry)
        for entry in entries or []
    ]


def titles_from_acai(result: Any) -> List[str]:
    """Every article title the entities of a `type: acai` result name, in entity order."""
    entities = (result or {}).get("entities") or {} if isinstance(result, dict) else {}
    return [
        str(article.get("title") or "")
        for entity in entities.values()
        if isinstance(entity, dict)
        for article in entity.get("dictionary") or []
        if isinstance(article, dict)
    ]


def articles_for(titles: Iterable[str], root: Any) -> Tuple[List[Dict[str, str]], List[str]]:
    """`(articles, missing titles)`: one article per distinct title, in the order first asked."""
    index = load(str(root))
    found: List[Dict[str, str]] = []
    missing: List[str] = []
    seen: set = set()
    for title in titles:
        key = matching_key(title)
        if not key or key in seen:
            continue
        seen.add(key)
        article = index.get(key)
        if article is None:
            missing.append(title)
        else:
            found.append(dict(article))
    return found, missing
