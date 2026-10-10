"""`format: analysis` — a passage and its analyses as compact text for a model to read.

Derived from the USJ form, so it carries nothing that form does not and drops nothing it does,
except glosses in languages other than English. Two parts per sentence: the tree in bracketed
treebank notation, each word written `form/n`, then the words' rows of one table. A family with
no column of its own travels after the table as compact JSON rather than being lost.

The USJ form stays the lossless form saved to disk; this one is what a prompt is handed. The
reason is cost: the same passage is a fraction of the tokens.
"""

import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

from llmflow.utils.scripture import CONTAINER_KEY

#: Container blocks this form lays out itself; any other travels as JSON.
_LAID_OUT = {"versification", "morphology", "senses", "glosses", "frequency", "syntax",
             "outside_passage"}

#: The gloss keys that are English. Another language's gloss is left out: the prompt reads English.
_ENGLISH_GLOSSES = ("gloss", "english")

COLUMNS = ("n", "ref", "id", "form", "lemma", "morph", "sense", "gloss", "freq", "note")


def _words(content: Iterable[Any]) -> List[Dict[str, str]]:
    """Every word in source order, with the chapter:verse it falls in."""
    words: List[Dict[str, str]] = []
    state = {"chapter": "", "verse": ""}

    def walk(nodes: Iterable[Any]) -> None:
        for node in nodes or []:
            if not isinstance(node, Mapping):
                continue
            if node.get("type") == "chapter":
                state["chapter"] = str(node.get("number") or "")
            elif node.get("type") == "verse":
                state["verse"] = str(node.get("number") or "")
            elif node.get("marker") == "w":
                form = "".join(c for c in node.get("content") or [] if isinstance(c, str))
                words.append({
                    "id": str(node.get("srcloc") or ""),
                    "form": form,
                    "lemma": str(node.get("lemma") or ""),
                    "ref": f"{state['chapter']}:{state['verse']}",
                })
                continue
            walk(node.get("content") or [])

    walk(content)
    return words


def _gloss(entry: Any) -> str:
    if not isinstance(entry, Mapping):
        return ""
    seen: List[str] = []
    for key in _ENGLISH_GLOSSES:
        value = str(entry.get(key) or "").strip()
        if value and value not in seen:
            seen.append(value)
    return " / ".join(seen)


def _morph(entry: Any) -> str:
    """The values in order; a value of two characters or fewer keeps its name (`lang=A`), since a
    bare code says nothing."""
    if not isinstance(entry, Mapping):
        return ""
    return " ".join(
        str(value) if len(str(value)) > 2 else f"{key}={value}"
        for key, value in entry.items()
        if value not in (None, "")
    )


def _sense(entry: Any) -> str:
    """The sense, labelled. A bare number is read as whatever number the prompt is asking for."""
    if not isinstance(entry, Mapping):
        return ""
    if entry.get("ln"):
        return f"LN {entry['ln']}"
    if entry.get("domain"):
        return f"domain {entry['domain']}"
    return ""


def _frequency(entry: Any, present: bool) -> str:
    if not present:
        return ""
    if entry is None:
        return "not in table"
    return (
        f"{entry.get('count')}× in {entry.get('corpus')} · "
        f"{entry.get('in_least_frequent_percent')}%"
    )


def _tree(node: Mapping[str, Any], number: Mapping[str, int], form: Mapping[str, str]) -> str:
    label = str(node.get("class") or "")
    if node.get("role"):
        label += f":{node['role']}"
    attributes = [
        f"{key}={value}" for key, value in node.items()
        if key not in ("class", "role", "children", "token")
    ]
    parts = [label, *attributes]
    if node.get("token"):
        token = str(node["token"])
        parts.append(f"{form.get(token, '?')}/{number.get(token, token)}")
    parts.extend(_tree(child, number, form) for child in node.get("children") or [])
    return "(" + " ".join(part for part in parts if part) + ")"


def _tokens(node: Mapping[str, Any]) -> List[str]:
    found = [str(node["token"])] if node.get("token") else []
    for child in node.get("children") or []:
        found.extend(_tokens(child))
    return found


def usj_to_analysis(usj: Mapping[str, Any]) -> str:
    """The compact text form of a USJ document carrying a `scripture_pipelines` container."""
    container: Mapping[str, Any] = usj.get(CONTAINER_KEY) or {}
    words = _words(usj.get("content") or [])
    number = {word["id"]: n for n, word in enumerate(words, start=1)}
    form = {word["id"]: word["form"] for word in words}

    morphology = container.get("morphology") or {}
    senses = container.get("senses") or {}
    glosses = container.get("glosses") or {}
    frequency: Optional[Mapping[str, Any]] = container.get("frequency")
    outside = container.get("outside_passage") or {}

    def row(word: Mapping[str, str]) -> str:
        identifier = word["id"]
        cells = [
            str(number[identifier]),
            word["ref"],
            identifier,
            word["form"],
            word["lemma"],
            _morph(morphology.get(identifier)),
            _sense(senses.get(identifier)),
            _gloss(glosses.get(identifier)),
            _frequency(
                (frequency or {}).get(identifier),
                frequency is not None and identifier in (frequency or {}),
            ),
            "outside" if outside.get(identifier) else "",
        ]
        return "\t".join(cells)

    lines = ["# Words are rows of one table; a tree names a word as form/n, n its row."]
    if container.get("versification"):
        lines.append(f"# Verse numbers are in the {container['versification']} scheme.")
    if frequency is not None:
        lines.append(
            "# freq: how often the lemma occurs in the corpus, and the least-frequent percent of "
            "lemmas it falls in. Empty means no frequency was given for that word; no other "
            "column is a count."
        )
    if outside:
        lines.append("# outside: a word of a sentence the passage meets, outside the passage.")
    lines.append("\t".join(COLUMNS))

    by_id = {word["id"]: word for word in words}
    placed: set = set()
    for index, sentence in enumerate(container.get("syntax") or [], start=1):
        lines.append(f"## sentence {index}")
        lines.append(_tree(sentence, number, form))
        for token in sorted(set(_tokens(sentence)), key=lambda t: number.get(t, 0)):
            if token in by_id and token not in placed:
                lines.append(row(by_id[token]))
                placed.add(token)

    rest = [word for word in words if word["id"] not in placed]
    if rest:
        if placed:
            lines.append("## words in no sentence tree")
        lines.extend(row(word) for word in rest)

    for name, value in container.items():
        if name in _LAID_OUT or value in (None, {}, []):
            continue
        lines.append(f"## {name}")
        lines.append(json.dumps(value, ensure_ascii=False, separators=(",", ":")))

    return "\n".join(lines) + "\n"
