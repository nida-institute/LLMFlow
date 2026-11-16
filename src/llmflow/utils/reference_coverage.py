"""Which of a list of Bible references a text contains: an audit no model writes.

In semdom-greek-lexicon a model was asked to audit an entry against its 37 analysed references;
it reported 35 present, and 14 were. Whether a reference is in a text is a lookup, so it is done
here, and the report says exactly which are missing.
"""
from __future__ import annotations

import json
import re
from typing import Any

_REF = re.compile(r"^\s*(.+?)\s+(\d+):(\d+)")


def _references(references: Any) -> list[str]:
    if isinstance(references, str):
        references = json.loads(references)
    if isinstance(references, dict):
        references = references.get("references", [])
    found = []
    for item in references or []:
        ref = item.get("reference") if isinstance(item, dict) else item
        if ref and str(ref).strip() and str(ref).strip() not in found:
            found.append(str(ref).strip())
    return found


def _present(reference: str, text: str) -> bool:
    m = _REF.match(reference)
    if not m:
        return reference in text
    book, chapter, verse = m.groups()
    # "Mark 3:21" is found as "Mark 3:21", "Mark 3:21-22" or "**Mark 3:21**", not as "Mark 3:2".
    return re.search(rf"{re.escape(book)}\s+{chapter}:{verse}(?!\d)", text) is not None


def reference_coverage(references: Any, text: str, title: str = "Reference coverage") -> str:
    """A Markdown report of which *references* appear in *text*.

    *references* is a list of references ("Mark 3:21"), a list of objects each with a
    `reference`, or an object with such a list under `references`, or a JSON string of any of
    these. A reference is present when its book, chapter and verse appear together in *text*.
    The status is PASS when none is missing.
    """
    refs = _references(references)
    missing = [r for r in refs if not _present(r, text)]
    lines = [
        f"# {title}",
        "",
        f"- **References analysed:** {len(refs)}",
        f"- **In the text:** {len(refs) - len(missing)}",
        f"- **Missing:** {len(missing)}",
        f"- **Status:** {'FAIL' if missing else 'PASS'}",
    ]
    if missing:
        lines += ["", "## Missing", ""] + [f"- {r}" for r in missing]
    return "\n".join(lines) + "\n"
