"""Add text to a Markdown document under its headings, without a model rewriting the document.

A model asked to return a whole document with a few additions also returns it changed: in
semdom-greek-lexicon, a step asked to add definitions to an entry of 37 references, "keeping
every reference", kept 14. Here the model returns only the additions, and this puts them in place,
so everything already in the document reaches the result by construction.

    additions = {
        "intro":    "...",   # at the end of the text under the title, before the first heading below it
        "sections": [        # each under the heading whose label it names
            {"heading": "I.1", "before": "...", "after": "..."},
        ],
        "end":      "...",   # at the end of the document
    }

A heading's label is its first word, without a trailing period or bold markers: `## I. To say`
is `I`, `### I.1 Indirect speech` is `I.1`. `before` goes straight after the heading, `after` at
the end of the text under it (before the next heading of any level). Every key is optional.
"""
from __future__ import annotations

import json
import re
from typing import Any

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")


def _label(text: str) -> str:
    words = text.strip().strip("*_ ").split()
    return words[0].strip("*_").rstrip(".:") if words else ""


def _join(*parts: str) -> str:
    return "\n\n".join(p.strip("\n") for p in parts if p and p.strip())


def merge_sections(markdown: str, additions: Any) -> str:
    """*markdown* with *additions* placed under its headings.

    *additions* is a dict, or a JSON string of one, as a model step with `response_format`
    returns it. A section whose label matches no heading is not dropped: it is added at the end
    under "Not placed", with the label it named, for an editor to place.
    """
    if isinstance(additions, str):
        additions = json.loads(additions) if additions.strip() else {}
    additions = additions or {}
    wanted: dict[str, dict] = {}
    order: list[str] = []
    for section in additions.get("sections") or []:
        key = _label(str(section.get("heading", "")))
        if key not in wanted:
            order.append(key)
            wanted[key] = {"before": "", "after": ""}
        for side in ("before", "after"):
            wanted[key][side] = _join(wanted[key][side], section.get(side) or "")

    # Split into blocks: the text before the first heading below the title, then one block per
    # heading. Headings inside fenced code are text.
    blocks: list[dict] = [{"heading": None, "lines": []}]
    in_fence = False
    for line in markdown.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
        m = None if in_fence else _HEADING.match(line)
        if m and not (len(m.group(1)) == 1 and blocks[0]["heading"] is None and len(blocks) == 1):
            blocks.append({"heading": line, "label": _label(m.group(2)), "lines": []})
        else:
            blocks[-1]["lines"].append(line)

    out: list[str] = []
    placed: set[str] = set()
    for i, block in enumerate(blocks):
        body = "\n".join(block["lines"])
        if i == 0:
            out.append(_join(body, additions.get("intro") or ""))
            continue
        add = wanted.get(block["label"]) if block["label"] not in placed else None
        if add:
            placed.add(block["label"])
            out.append(_join(block["heading"], add["before"], body, add["after"]))
        else:
            out.append(_join(block["heading"], body))

    unplaced = [k for k in order if k not in placed]
    if unplaced:
        notes = [
            "## Not placed",
            "> These were written for headings the document does not have. Place or remove them.",
        ]
        for key in unplaced:
            notes.append(_join(f"**{key or '(no heading named)'}**", wanted[key]["before"], wanted[key]["after"]))
        out.append(_join(*notes))
    out.append(additions.get("end") or "")
    return _join(*out) + "\n"
