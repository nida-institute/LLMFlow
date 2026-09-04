"""Guardrail: a payload says which kind of nothing it means.

Three states, and the third is the ambiguous one:

- an empty collection — the question was asked and the answer is nothing
- `null` — it was not asked, or does not apply
- an absent key — neither, so it is legitimate only where another declaration explains the
  absence, such as the `include:` request list

The scripture container got the first right already: a requested family with no data yields an
empty map, which `test_scripture_families.py` covers. It got the third wrong in two places — a
family the edition could not supply was omitted, leaving a log warning as the only explanation,
and a log line does not travel with the data. A consumer could not tell "this edition has no
Levinsohn source" from "discourse was never requested".

Convention: rule `say-which-kind-of-nothing`. The pattern to copy is
`llmflow.utils.discourse.Outcome`, which names three different kinds of nothing rather than
returning an empty value for all of them.
"""
from __future__ import annotations

from llmflow.utils.scripture import CONTAINER_KEY, rows_to_usj

GREEK_ROWS = [
    {
        "book": "PHM",
        "chapter": 1,
        "verse": 1,
        "text": "Παῦλος",
        "xml:id": "n57001001001",
    }
]


def _container(include, **kwargs) -> dict:
    return rows_to_usj(GREEK_ROWS, "PHM", include=include, **kwargs)[CONTAINER_KEY]


def test_a_requested_family_the_edition_cannot_supply_is_null_not_absent():
    """`discourse` requested, but the edition names no discourse source."""
    container = _container(["ids", "discourse"], discourse=None)

    assert "discourse" in container, (
        "a requested family was omitted, so a reader cannot tell an edition with no discourse "
        "source from a passage where discourse was never asked for"
    )
    assert container["discourse"] is None


def test_a_requested_family_with_data_carries_it():
    container = _container(["ids", "discourse"], discourse=[{"id": "n57001001001"}])

    assert container["discourse"] == [{"id": "n57001001001"}]


def test_an_unrequested_family_stays_absent():
    """Absence is legitimate here: the `include:` list declares why the key is not there."""
    container = _container(["ids"])

    assert "discourse" not in container


def test_an_undeclared_versification_is_null_not_absent():
    """The edition does not say which versification its references are in.

    That was a log warning and an absent key. The warning does not reach whoever reads the
    payload later, so the payload has to say it.
    """
    container = _container(["ids"], versification=None)

    assert "versification" in container
    assert container["versification"] is None


def test_a_declared_versification_is_carried():
    container = _container(["ids"], versification="eng")

    assert container["versification"] == "eng"
