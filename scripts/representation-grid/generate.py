"""Fill the format x include grid for the representation workbench.

Calls the same two functions `steps/scripture.py` calls, so every cell is what a
`type: scripture` step would return. Reads registered datasets; calls no model.

    hatch run python tmp/representation-grid/generate.py
"""

from __future__ import annotations

import json
from pathlib import Path

from llmflow.utils.scripture import load_registry_resources, resource_text

HERE = Path(__file__).parent
CELLS = HERE / "cells"

PASSAGES = [
    ("SBLGNT", "PHM 1:1-7"),
    ("WLC", "RUT 1:1"),
    ("SBLGNT", "MRK 1:1-8"),
]

FORMATS = ["plain", "milestones", "usj"]

ALL_FAMILIES = ["ids", "morphology", "senses", "glosses", "referents", "discourse", "syntax"]

COMBINATIONS = [
    [],
    ["ids"],
    ["senses"],
    ["ids", "senses"],
    ["discourse"],
    ["ids", "discourse"],
    ["ids", "syntax"],
    ALL_FAMILIES,
]

USJ_TOP_LEVEL = {"type", "version", "content"}


def slug(text: str) -> str:
    return text.replace(" ", "-").replace(":", "_").replace(",", "")


def combo_slug(combo: list[str]) -> str:
    if not combo:
        return "none"
    if combo == ALL_FAMILIES:
        return "all"
    return "+".join(combo)


def walk(node, words: list, containers: list) -> None:
    """Collect `w` char nodes and any non-standard container keys, at any depth."""
    if isinstance(node, dict):
        if node.get("marker") == "w":
            words.append(node)
        for key, value in node.items():
            if key == "scripture_pipelines":
                containers.append(value)
            walk(value, words, containers)
    elif isinstance(node, list):
        for item in node:
            walk(item, words, containers)


def entry_count(payload) -> int | None:
    if payload is None:
        return None
    if isinstance(payload, (list, dict)):
        return len(payload)
    return None


def measure(result) -> dict:
    """Sizes in all three units, because the same text differs by 2.5x among them."""
    if isinstance(result, str):
        carried = result
    else:
        carried = json.dumps(result, ensure_ascii=False)
    return {
        "codepoints": len(carried),
        "utf8_bytes": len(carried.encode("utf-8")),
        "json_escaped": len(json.dumps(result, ensure_ascii=True)),
    }


def describe_usj(result: dict) -> dict:
    words: list = []
    containers: list = []
    walk(result, words, containers)
    anchored = [w for w in words if "srcloc" in w]
    families: dict = {}
    for container in containers:
        if isinstance(container, dict):
            for name, payload in container.items():
                families[name] = entry_count(payload)
    return {
        "word_nodes": len(words),
        "words_with_srcloc": len(anchored),
        "top_level_keys": sorted(k for k in result if k not in USJ_TOP_LEVEL),
        "family_entries": families,
    }


def main() -> int:
    CELLS.mkdir(parents=True, exist_ok=True)
    resources = load_registry_resources(None)
    rows = []

    for resource, passage in PASSAGES:
        for fmt in FORMATS:
            for combo in COMBINATIONS:
                row = {
                    "resource": resource,
                    "passage": passage,
                    "format": fmt,
                    "include": combo,
                }
                name = f"{resource}__{slug(passage)}__{fmt}__{combo_slug(combo)}"
                try:
                    result = resource_text(
                        resource, passage, fmt=fmt, resources=resources, include=combo
                    )
                except Exception as exc:  # a refusal is data, not a crash
                    row["outcome"] = "refused"
                    row["error_type"] = type(exc).__name__
                    row["error"] = str(exc)
                    rows.append(row)
                    continue

                row["outcome"] = "ok"
                row.update(measure(result))
                if isinstance(result, dict):
                    row.update(describe_usj(result))
                    (CELLS / f"{name}.json").write_text(
                        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                else:
                    (CELLS / f"{name}.txt").write_text(result, encoding="utf-8")
                rows.append(row)

    # The multiplier every cost claim is stated against: this passage as `plain`.
    baseline = {
        (r["resource"], r["passage"]): r["codepoints"]
        for r in rows
        if r["format"] == "plain" and r["outcome"] == "ok" and not r["include"]
    }
    for row in rows:
        base = baseline.get((row["resource"], row["passage"]))
        if base and row.get("codepoints"):
            row["x_plain"] = round(row["codepoints"] / base, 3)

    (HERE / "grid.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    header = [
        "resource",
        "passage",
        "format",
        "include",
        "outcome",
        "codepoints",
        "utf8_bytes",
        "json_escaped",
        "x_plain",
        "word_nodes",
        "words_with_srcloc",
        "family_entries",
        "error_type",
    ]
    lines = ["\t".join(header)]
    for row in rows:
        cells = []
        for key in header:
            value = row.get(key)
            if isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
            cells.append("" if value is None else str(value))
        lines.append("\t".join(cells))
    (HERE / "grid.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    ok = sum(1 for r in rows if r["outcome"] == "ok")
    print(f"{len(rows)} cells: {ok} returned, {len(rows) - ok} refused")
    print(f"  {HERE / 'grid.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
