"""Target-language text for a span named by source word ids.

A pipeline can already cut a source passage by word id (`spans:` on `type: scripture`). This is
the other side of it: given the same `{from, to}` pairs, the text of the translation.

Design: `project/plans/design-scripture-alignments.md`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

#: Source ids address a word, or a morpheme of one: `n40001001001` in Greek, `o010010010011` in
#: Hebrew, whose last digit is the morpheme. A span boundary names a *word*, so both sides are
#: compared at word level and every morpheme of an edge word is taken with it.
WORD_KEY_LENGTH = 12

#: Written between two parts of one unit that are not adjacent in the text.
GAP = " … "


def word_key(source_id: str) -> str:
    return source_id[:WORD_KEY_LENGTH]


def verse_key(token_or_source_id: str) -> str:
    """`BBCCCVVV`, with any leading `n`/`o` removed so source and target keys compare."""
    digits = token_or_source_id.lstrip("no")
    return digits[:8]


def validate_pair(document: Dict[str, Any], source_docid: str, target_docid: str) -> None:
    """Refuse a pair the alignment file does not itself declare.

    `roles` is positional against `documents`, so which text is the source is stated by the file
    rather than assumed from position.
    """
    documents = document.get("documents") or []
    roles = document.get("roles") or []
    declared = {}
    for role, doc in zip(roles, documents):
        declared[role] = (doc or {}).get("docid")

    if declared.get("source") != source_docid or declared.get("target") != target_docid:
        raise ValueError(
            f"alignment file declares {declared.get('source')!r} -> {declared.get('target')!r}, "
            f"but the step asks for {source_docid!r} -> {target_docid!r}. "
            "The file's own `documents` and `roles` are authoritative; a filename is not."
        )


def read_tsv(path: Any) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(path, encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        for line in handle:
            cells = (line.rstrip("\n").split("\t") + [""] * len(header))[: len(header)]
            rows.append(dict(zip(header, cells)))
    return rows


def load_pair(definition: Dict[str, Any]) -> Dict[str, Any]:
    """Open the three files a pair needs, and check the alignment declares the pair."""
    document = json.loads(Path(definition["alignment_file"]).read_text(encoding="utf-8"))
    validate_pair(document, definition["source"], definition["target"])
    return {
        "document": document,
        "source": read_tsv(definition["source_file"]),
        "target": read_tsv(definition["target_file"]),
    }


def _owner_of_each_target_token(
    records: Sequence[Dict], target_ids: Sequence[str]
) -> tuple[Dict[str, set], Dict[str, Optional[str]]]:
    """Which source units each target token aligns to, and which unaligned token belongs where.

    An unaligned token belongs with the nearest *preceding* aligned token, or with the nearest
    following one where nothing precedes it in its verse.
    """
    aligned_to: Dict[str, set] = {}
    for record in records:
        for token in record.get("target", ()):
            aligned_to.setdefault(token, set()).update(record.get("source", ()))

    belongs_with: Dict[str, Optional[str]] = {}
    by_verse: Dict[str, List[str]] = {}
    for token in target_ids:
        by_verse.setdefault(verse_key(token), []).append(token)

    for tokens in by_verse.values():
        previous_aligned = None
        pending: List[str] = []
        for token in tokens:
            if token in aligned_to:
                for held in pending:
                    belongs_with[held] = token
                pending = []
                previous_aligned = token
            else:
                belongs_with[token] = previous_aligned
                if previous_aligned is None:
                    pending.append(token)
        for held in pending:                       # trailing unaligned with nothing after them
            belongs_with[held] = previous_aligned
    return aligned_to, belongs_with


def _join(tokens: Sequence[str], text_of: Dict[str, Dict], order_of: Dict[str, int]) -> str:
    """Assemble target text, writing `GAP` where the tokens are not a contiguous run."""
    out: List[str] = []
    previous = None
    for token in tokens:
        if previous is not None:
            if order_of[token] != order_of[previous] + 1:
                out.append(GAP)
            elif not text_of[previous].get("skip_space_after"):
                out.append(" ")
        out.append(text_of[token]["text"])
        previous = token
    return "".join(out).strip()


def _source_phrase(ids: Sequence[str], text_of: Dict[str, Dict]) -> str:
    """Join source surface forms, writing `GAP` where the unit's words are not adjacent.

    Morphemes of one word run together; a skipped word is written with `GAP` rather than
    closed up.
    """
    out: List[str] = []
    for index, source_id in enumerate(ids):
        text = text_of.get(source_id, {}).get("text", "")
        if index == 0:
            out.append(text)
            continue
        previous = ids[index - 1]
        if word_key(source_id) == word_key(previous):
            out.append(text)
        elif int(word_key(source_id)[-3:]) > int(word_key(previous)[-3:]) + 1:
            out.append(GAP + text)
        else:
            out.append(" " + text)
    return "".join(out)


def aligned_text_for_spans(
    spans: Iterable[Dict[str, str]],
    document: Dict[str, Any],
    source_rows: Sequence[Dict[str, str]],
    target_rows: Sequence[Dict[str, str]],
    *,
    order: Sequence[str] = ("target",),
    returns: Sequence[str] = ("text",),
) -> List[Dict[str, Any]]:
    """One result per span, in the order asked."""
    records = document.get("records") or []
    source_text_of = {row["id"]: row for row in source_rows}
    target_text_of = {row["id"]: row for row in target_rows}
    target_ids = [row["id"] for row in target_rows]
    order_of = {token: index for index, token in enumerate(target_ids)}
    source_ids = [row["id"] for row in source_rows]

    aligned_to, belongs_with = _owner_of_each_target_token(records, target_ids)

    #: The other direction: which target tokens each source unit aligns to. Needed for source
    #: order, which walks the source and asks what each word became.
    targets_of_source: Dict[str, set] = {}
    for record in records:
        for sid in record.get("source", ()):
            targets_of_source.setdefault(sid, set()).update(
                t for t in record.get("target", ()) if t in target_text_of
            )

    results: List[Dict[str, Any]] = []
    for span in spans:
        low, high = word_key(span["from"]), word_key(span["to"])
        held = [sid for sid in source_ids if low <= word_key(sid) <= high]

        if not held:
            # The question could not be answered: these ids are not in the source at all.
            results.append({"text": None, "contiguous": None})
            continue

        held_set = set(held)
        mine = {
            token
            for token, sources in aligned_to.items()
            if sources & held_set and token in target_text_of
        }
        mine |= {
            token
            for token, owner in belongs_with.items()
            if owner in mine and token in target_text_of
        }

        ordered = sorted(mine, key=lambda token: order_of[token])
        contiguous = all(
            order_of[b] == order_of[a] + 1 for a, b in zip(ordered, ordered[1:])
        ) if ordered else True

        result: Dict[str, Any] = {}
        if "text" in returns or not returns:
            if "target" in order:
                result["text"] = _join(ordered, target_text_of, order_of)
            if "source" in order:
                # Walk the source units in their own sequence and emit the tokens each aligns
                # to. An unaligned token follows the token it belongs to, so punctuation stays
                # beside the word it punctuates rather than collecting at the end.
                owned_by_token: Dict[str, List[str]] = {}
                for token, owner in belongs_with.items():
                    if token in mine and owner is not None:
                        owned_by_token.setdefault(owner, []).append(token)

                seen, sequence = set(), []
                for sid in held:
                    for token in sorted(targets_of_source.get(sid, ()), key=order_of.__getitem__):
                        if token not in mine or token in seen:
                            continue
                        seen.add(token)
                        sequence.append(token)
                        for extra in sorted(owned_by_token.get(token, ()), key=order_of.__getitem__):
                            if extra not in seen:
                                seen.add(extra)
                                sequence.append(extra)
                result["text_in_source_order"] = _join(sequence, target_text_of, order_of)
        result["contiguous"] = contiguous

        if "alignments" in returns:
            held_records = [r for r in records if set(r.get("source", ())) & held_set]
            result["records"] = held_records
            result["units"] = [
                {
                    "source_text": _source_phrase(
                        sorted(s for s in r.get("source", ()) if s in held_set), source_text_of
                    ),
                    "target_text": _join(
                        sorted(
                            (t for t in r.get("target", ()) if t in target_text_of),
                            key=lambda t: order_of[t],
                        ),
                        target_text_of,
                        order_of,
                    ),
                }
                for r in held_records
            ]
        results.append(result)
    return results
