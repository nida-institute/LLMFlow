"""The container states the scheme its verse labels are actually in — never the one requested.

Two things were wrong, and the first was a silent wrong answer.

**The container claimed the requested scheme.** `versification:` names the scheme the caller's
*reference* is written in, and the engine maps it inward to fetch the right verses. It does not
relabel the result: the verse markers come from the edition's own rows. But the container
reported the request, so asking for `shifted` against an edition numbered `org` returned
`⌊1:3⌋` under a label saying `shifted` — and shifted 1:3 is a different verse. The only thing
telling a consumer which scheme the labels are in was asserting the wrong one.

**An undeclared scheme refused a cross-scheme request.** Much of the translation world uses
English versification without meeting the issue, so a project may have no versification file
and assume it. That is supported, and warned about, and the payload keeps the guess apart from
a declaration:

    versification: null              nobody declared one
    versification_guessed: "eng"     what was used instead

so a consumer reading only `versification` gets the honest answer and cannot mistake a guess
for a fact. `versification_guessed` appears only where there was a guess to report.

Convention: rule `say-which-kind-of-nothing`.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from llmflow.utils.scripture import (
    ASSUMED_SCHEME,
    CONTAINER_KEY,
    edition_text,
    rows_to_usj,
)
from llmflow.utils.versification import HUB_SCHEME

ROWS = [{"book": "PHM", "chapter": 1, "verse": 1, "text": "Παῦλος", "xml:id": "n57001001001"}]

TSV = "ref\ttext\tafter\nTST 1:1!1\talpha\t \nTST 1:2!1\tbeta\t \nTST 1:3!1\tgamma\t \n"


@pytest.fixture
def store(tmp_path) -> dict:
    """A hub scheme, and one that shifts TST by two verses."""
    directory = tmp_path / "versification"
    directory.mkdir()
    (directory / f"{HUB_SCHEME}.json").write_text(
        json.dumps({"maxVerses": {"TST": ["5"]}, "mappedVerses": {}}), encoding="utf-8"
    )
    (directory / "shifted.json").write_text(
        json.dumps({"maxVerses": {"TST": ["5"]}, "mappedVerses": {"TST 1:1-3": "TST 1:3-5"}}),
        encoding="utf-8",
    )
    tsv = tmp_path / "hub.tsv"
    tsv.write_text(TSV, encoding="utf-8")
    return {"dir": directory, "tsv": str(tsv)}


def _editions(store: dict, **overrides) -> dict:
    definition = {"kind": "tsv", "path": store["tsv"], "versification_scheme": HUB_SCHEME}
    definition.update(overrides)
    return {"HUB": definition}


def _container(**kwargs) -> dict:
    return rows_to_usj(ROWS, "PHM", include=["ids"], **kwargs)[CONTAINER_KEY]


# --- the container tells the truth about its labels ------------------------------------


def test_a_cross_scheme_request_does_not_relabel_the_container(store):
    """The labels come from the edition, so the container must name the edition's scheme.

    `shifted TST 1:1` is hub `TST 1:3`. The text returned is the right one and its marker
    reads 1:3, which is the edition's numbering — so reporting `shifted` would tell a consumer
    to read 1:3 as shifted 1:3, two verses away.
    """
    usj = edition_text(
        "HUB", "TST 1:1", fmt="usj", editions=_editions(store), include=["ids"],
        versification="shifted", mappings_dir=store["dir"],
    )

    assert usj[CONTAINER_KEY]["versification"] == HUB_SCHEME, (
        "the container named the requested scheme while the labels are the edition's"
    )


def test_the_text_itself_is_still_fetched_through_the_request(store):
    """The inward mapping is unchanged — only the label was ever wrong."""
    text = edition_text(
        "HUB", "TST 1:1", fmt="milestones", editions=_editions(store),
        versification="shifted", mappings_dir=store["dir"],
    )

    assert "gamma" in text, "shifted 1:1 is hub 1:3, whose word is gamma"
    assert "⌊1:3⌋" in text, "the marker is the edition's numbering"


# --- a scheme nobody declared ----------------------------------------------------------


def test_the_assumed_scheme_is_english():
    assert ASSUMED_SCHEME == "eng"


def test_an_undeclared_scheme_is_null_with_the_guess_beside_it():
    container = _container(versification=None)

    assert container["versification"] is None, "a guess must not be reported as a declaration"
    assert container["versification_guessed"] == ASSUMED_SCHEME


def test_a_declared_scheme_carries_no_guess():
    """Absence is legitimate here: `versification` being set explains it."""
    container = _container(versification="org")

    assert container["versification"] == "org"
    assert "versification_guessed" not in container


def test_an_undeclared_edition_is_read_as_english_with_a_warning(store, caplog):
    """Supported, because much of the translation world works this way — but not silently."""
    editions = {"MYSTERY": {"kind": "tsv", "path": store["tsv"]}}

    with caplog.at_level("WARNING"):
        usj = edition_text(
            "MYSTERY", "TST 1:1", fmt="usj", editions=editions, include=["ids"],
            versification=ASSUMED_SCHEME, mappings_dir=store["dir"],
        )

    assert ASSUMED_SCHEME in caplog.text
    assert usj[CONTAINER_KEY]["versification"] is None
    assert usj[CONTAINER_KEY]["versification_guessed"] == ASSUMED_SCHEME
