"""Check every pair in `data/alignment-pairs.json` against the alignment corpus.

An audit script rather than a test: it reads the real corpus, which a fresh clone does not
have, so it cannot run in the suite. `tests/test_alignment_declaration.py` covers what can be
checked without the corpus.

What it answers: for each declared pair, do the three files exist, does the alignment file
declare the pair it is claimed for, and do the identifiers in its records join the source and
target token files. A pair whose identifiers do not join returns nothing rather than failing,
so nothing but this check distinguishes "no alignment here" from "the identifiers never
matched".

    hatch run python scripts/check_alignment_pairs.py
    hatch run python scripts/check_alignment_pairs.py --pair SBLGNT BSB

Exit status is 1 when any declared pair is unusable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from llmflow.steps.alignment import PATH_KEYS, declared_pairs, resolve_pair
from llmflow.utils.alignment import read_tsv, validate_pair

#: Below this, treat the join as broken rather than incomplete. A pair that joins at all
#: joins at 99% or better; the observed failures join at 0%.
JOIN_THRESHOLD = 99.0


def identifiers_used(document: dict, side: str) -> set:
    return {i for record in document.get("records", ()) for i in record.get(side, ())}


def check(row: dict) -> tuple[str, list[str]]:
    """One line of report for *row*, and the reasons it is unusable."""
    name = f"{row['source']}->{row['target']}"
    reasons: list[str] = []

    try:
        resolved = resolve_pair(row["source"], row["target"])
    except ValueError as error:
        return f"{name:24} UNRESOLVED", [f"{name}: {error}"]

    absent = [key for key in PATH_KEYS if not Path(resolved[key]).is_file()]
    if absent:
        return f"{name:24} MISSING FILES", [f"{name}: no file at {[resolved[k] for k in absent]}"]

    document = json.loads(Path(resolved["alignment_file"]).read_text(encoding="utf-8"))
    try:
        validate_pair(document, row["source"], row["target"])
        declared = "ok"
    except ValueError as error:
        declared = "NO"
        reasons.append(f"{name}: {error}")

    percentages = []
    for side, key in (("source", "source_file"), ("target", "target_file")):
        used = identifiers_used(document, side)
        available = {line["id"] for line in read_tsv(resolved[key])}
        joined = len(used & available)
        share = 100.0 * joined / len(used) if used else 0.0
        percentages.append(share)
        if share < JOIN_THRESHOLD:
            reasons.append(
                f"{name}: {joined:,} of {len(used):,} {side} identifiers join "
                f"{Path(resolved[key]).name} ({share:.2f}%)"
            )

    records = len(document.get("records", ()))
    flag = "" if all(p == 100.0 for p in percentages) else "   <-- not 100%"
    line = (
        f"{name:24} {declared:3} {records:>9,} records   "
        f"source {percentages[0]:6.2f}%   target {percentages[1]:6.2f}%{flag}"
    )
    return line, reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pair", nargs=2, metavar=("SOURCE", "TARGET"), help="check one pair")
    arguments = parser.parse_args(argv)

    declaration = declared_pairs()
    rows = declaration["pairs"]
    if arguments.pair:
        wanted = tuple(arguments.pair)
        rows = [r for r in rows if (r["source"], r["target"]) == wanted]
        if not rows:
            print(f"{wanted[0]}->{wanted[1]} is not declared", file=sys.stderr)
            return 1

    print(f"dataset: {declaration['dataset']}\n")
    unusable: list[str] = []
    for row in rows:
        line, reasons = check(row)
        print(line)
        unusable.extend(reasons)

    print(f"\n{len(rows)} pairs checked, {len(unusable)} unusable")
    for reason in unusable:
        print(f"  ! {reason}")
    return 1 if unusable else 0


if __name__ == "__main__":
    raise SystemExit(main())
