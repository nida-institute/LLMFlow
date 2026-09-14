"""`type: alignment` — target-language text for a span named by source word ids (LLMFlow#238).

**Step behaviour is exercised through the API**, per rule 1 in
`docs/ai-context/project/rules.md`: `load_pipeline(...)` then `.lint()` and `.run()`, which is the
surface the CLI uses. A raw `{"type": "alignment", ...}` dict handed to the handler satisfies both
the runner and the object model by construction, so it cannot see a key the schema fails to
declare. An alignment pipeline calls no model, so running one here is free.

The fixture is a **Scripture Burrito alignment document** in the shape the format defines —
`documents` naming the two texts and `roles` saying which is which — beside a source and a target
token file. It is synthetic: the real corpus lives outside the repository, so a test reading it
would pass on one machine only, which is the defect `project/TODO.md` records against
`test_discourse_loading.py`.

Each test names the ruling it protects. Every one is a *silent* failure: the step returns text
either way, and only the content says whether it is right. Rulings are in
`project/plans/design-scripture-alignments.md`.
"""
import json
from pathlib import Path

import pytest

from llmflow import load_pipeline
from llmflow.utils.alignment import validate_pair


def _s(verse, word):
    return f"n99001{verse:03d}{word:03d}"


def _t(verse, tok):
    return f"99001{verse:03d}{tok:03d}"


#: Four verses, each built for one case.
#:
#:   v1  unaligned tokens *between* and *after* the aligned ones  (R10, trailing)
#:   v2  a plain verse, so a span can cross a boundary            (R6)
#:   v3  one record grouping non-adjacent source words, whose
#:       target tokens are also non-adjacent                      (R14, R15, both sides)
#:   v4  unaligned tokens *before* the first aligned one          (R10, leading)
SOURCE_TSV = (
    "id\ttext\n"
    f"{_s(1,1)}\talpha\n"
    f"{_s(1,2)}\tbeta\n"
    f"{_s(1,3)}\tgamma\n"
    f"{_s(2,1)}\tdelta\n"
    f"{_s(2,2)}\tepsilon\n"
    f"{_s(3,1)}\tzeta\n"
    f"{_s(3,2)}\teta\n"
    f"{_s(3,3)}\ttheta\n"
    f"{_s(4,1)}\tiota\n"
    f"{_s(4,2)}\tkappa\n"          # in the source, in no record at all
)

TARGET_TSV = (
    # `skip_space_after` suppresses the space *after* its own token, so it sits on the word
    # before a mark rather than on the mark: "A" + "," + " " + "B" gives "A, B".
    "id\ttext\tskip_space_after\n"
    f"{_t(1,1)}\tA\ttrue\n"
    f"{_t(1,2)}\t,\t\n"
    f"{_t(1,3)}\tB\t\n"
    f"{_t(1,4)}\tC\ttrue\n"
    f"{_t(1,5)}\t.\t\n"
    f"{_t(2,1)}\tD\t\n"
    f"{_t(2,2)}\tE\t\n"
    f"{_t(3,1)}\tZ\t\n"
    f"{_t(3,2)}\tH\t\n"
    f"{_t(3,3)}\tTH\t\n"
    f"{_t(4,1)}\tIn\t\n"
    f"{_t(4,2)}\tHim\t\n"
    f"{_t(4,3)}\tI\t\n"
)

ALIGNMENT = {
    "documents": [
        {"docid": "SRC", "scheme": "BCVWP"},
        {"docid": "TGT", "scheme": "BCVW"},
    ],
    "meta": {"conformsTo": "0.3", "creator": "test"},
    "roles": ["source", "target"],
    "type": "translation",
    "records": [
        {"source": [_s(1, 1)], "target": [_t(1, 1)], "meta": {"id": "r1"}},
        {"source": [_s(1, 2)], "target": [_t(1, 3)], "meta": {"id": "r2"}},
        {"source": [_s(1, 3)], "target": [_t(1, 4)], "meta": {"id": "r3"}},
        {"source": [_s(2, 1)], "target": [_t(2, 1)], "meta": {"id": "r4"}},
        {"source": [_s(2, 2)], "target": [_t(2, 2)], "meta": {"id": "r5"}},
        # zeta and theta are one unit; eta between them is its own. Discontinuous on both sides.
        {"source": [_s(3, 1), _s(3, 3)], "target": [_t(3, 1), _t(3, 3)], "meta": {"id": "r6"}},
        {"source": [_s(3, 2)], "target": [_t(3, 2)], "meta": {"id": "r7"}},
        {"source": [_s(4, 1)], "target": [_t(4, 3)], "meta": {"id": "r8"}},
    ],
}


@pytest.fixture
def store(tmp_path, monkeypatch) -> Path:
    """A throwaway `$SP_HOME` with one registered alignment pair over synthetic files."""
    home = tmp_path / "sp"
    resources = home / "resources"
    resources.mkdir(parents=True)

    alignment = tmp_path / "SRC-TGT-manual.json"
    alignment.write_text(json.dumps(ALIGNMENT), encoding="utf-8")
    source = tmp_path / "src.tsv"
    source.write_text(SOURCE_TSV, encoding="utf-8")
    target = tmp_path / "tgt.tsv"
    target.write_text(TARGET_TSV, encoding="utf-8")

    (resources / "SRC-TGT.yaml").write_text(
        "id: SRC-TGT\n"
        "kind: alignment\n"
        "source: SRC\n"
        "target: TGT\n"
        f"alignment_file: {alignment}\n"
        f"source_file: {source}\n"
        f"target_file: {target}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SP_HOME", str(home))
    return home


def pipeline_file(tmp_path: Path, steps: str, name: str = "alignment-test") -> Path:
    path = tmp_path / "pipeline.yaml"
    path.write_text(f"name: {name}\nsteps:\n{steps}", encoding="utf-8")
    return path


def step_yaml(spans, extra: str = "") -> str:
    rendered = ", ".join(f"{{from: {a}, to: {b}}}" for a, b in spans)
    return (
        "  - name: english\n"
        "    type: alignment\n"
        "    source: SRC\n"
        "    target: TGT\n"
        f"    spans: [{rendered}]\n"
        f"{extra}"
        "    output: english\n"
    )


def run(path: Path) -> dict:
    """Lint then run, failing with the linter's own message rather than a bare exception."""
    pipeline = load_pipeline(path)
    result = pipeline.lint()
    assert result.valid, f"pipeline did not lint: {getattr(result, 'errors', result)}"
    return pipeline.run(log_file=str(path.parent / "llmflow.log"))


def one(tmp_path, spans, extra: str = ""):
    return run(pipeline_file(tmp_path, step_yaml(spans, extra)))["english"][0]


# --- the object model exposes what the schema declares ------------------------------------

def test_the_api_exposes_every_alignment_key(tmp_path, store):
    """If a key is missing here it is missing from the schema, since Step is generated."""
    path = pipeline_file(
        tmp_path,
        step_yaml([(_s(1, 1), _s(1, 2))], "    returns: [text]\n    order: [target]\n"),
    )
    step = load_pipeline(path).steps[0]
    assert step.source == "SRC"
    assert step.target == "TGT"
    assert step.returns == ["text"]
    assert step.order == ["target"]
    assert step.spans == [{"from": _s(1, 1), "to": _s(1, 2)}]


# --- R10: the unaligned tokens inside a span are kept, at both ends ------------------------

def test_an_unaligned_token_between_aligned_ones_is_kept(tmp_path, store):
    """Without this the text reads 'AB' — the comma vanishes."""
    assert one(tmp_path, [(_s(1, 1), _s(1, 2))])["text"] == "A, B"


def test_an_unaligned_token_after_the_last_aligned_one_is_kept(tmp_path, store):
    """The `wordTherefore` case: verse-final punctuation sits past the last aligned token."""
    assert one(tmp_path, [(_s(1, 1), _s(1, 3))])["text"] == "A, B C."


def test_an_unaligned_token_before_the_first_aligned_one_is_kept(tmp_path, store):
    """The Ephesians 1:11 case: 'In Him' aligns to nothing and starts the sentence."""
    assert one(tmp_path, [(_s(4, 1), _s(4, 1))])["text"] == "In Him I"


def test_a_span_does_not_reach_into_a_neighbour(tmp_path, store):
    """R10 stops where a token belonging to a different source unit begins."""
    assert one(tmp_path, [(_s(1, 2), _s(1, 2))])["text"] == "B"


# --- R6: a span crosses verses, because a clause does --------------------------------------

def test_a_span_crossing_a_verse_boundary_joins_the_verses_in_order(tmp_path, store):
    assert one(tmp_path, [(_s(1, 3), _s(2, 1))])["text"] == "C. D"


# --- R12: the span says whether its tokens are contiguous ----------------------------------

def test_a_span_whose_tokens_are_contiguous_says_so(tmp_path, store):
    assert one(tmp_path, [(_s(1, 1), _s(1, 3))])["contiguous"] is True


def test_a_span_whose_tokens_are_not_contiguous_says_so(tmp_path, store):
    """zeta+theta are one unit with eta's H sitting inside their range."""
    assert one(tmp_path, [(_s(3, 1), _s(3, 1))])["contiguous"] is False


# --- R14, R15: a discontinuous unit survives, with its gap marked on both sides -------------

def test_a_discontinuous_record_keeps_its_gap_on_the_source_side(tmp_path, store):
    got = one(tmp_path, [(_s(3, 1), _s(3, 3))], "    returns: [text, alignments]\n")
    assert "zeta … theta" in [u["source_text"] for u in got["units"]]


def test_a_discontinuous_record_keeps_its_gap_on_the_target_side(tmp_path, store):
    """Closing it up would produce 'ZTH', which the translation does not contain."""
    got = one(tmp_path, [(_s(3, 1), _s(3, 3))], "    returns: [text, alignments]\n")
    assert "Z … TH" in [u["target_text"] for u in got["units"]]


# --- R5: target order by default, source order on request, both together --------------------

def test_target_order_is_the_default(tmp_path, store):
    got = one(tmp_path, [(_s(1, 1), _s(1, 3))])
    assert "text" in got and "text_in_source_order" not in got


def test_source_order_is_available_on_request(tmp_path, store):
    got = one(tmp_path, [(_s(3, 1), _s(3, 3))], "    order: [source]\n")
    assert "text_in_source_order" in got


def test_both_orders_cover_the_same_tokens(tmp_path, store):
    """R8 fixes membership; R5 only changes sequence.

    The gap marker is dropped before comparing: it is presentation, and the two orderings put
    the gaps in different places by construction — target order has none here, while source
    order separates zeta's two tokens because eta's sits between them in the translation.
    """
    got = one(tmp_path, [(_s(3, 1), _s(3, 3))], "    order: [target, source]\n")
    words = lambda text: sorted(w for w in text.split() if w != "…")
    assert words(got["text"]) == words(got["text_in_source_order"])


# --- R11: two kinds of nothing, told apart --------------------------------------------------

def test_a_source_word_present_but_aligning_to_nothing_gives_an_empty_collection(tmp_path, store):
    got = one(tmp_path, [(_s(4, 2), _s(4, 2))], "    returns: [text, alignments]\n")
    assert got["units"] == []


def test_a_source_id_absent_from_the_alignment_gives_null(tmp_path, store):
    got = one(tmp_path, [("n99001009001", "n99001009001")])
    assert got["text"] is None


# --- R16: the records themselves, on request -------------------------------------------------

def test_the_raw_records_are_absent_unless_asked_for(tmp_path, store):
    assert "records" not in one(tmp_path, [(_s(1, 1), _s(1, 2))])


def test_the_raw_records_are_returned_when_asked_for(tmp_path, store):
    got = one(tmp_path, [(_s(1, 1), _s(1, 2))], "    returns: [alignments]\n")
    assert [r["meta"]["id"] for r in got["records"]] == ["r1", "r2"]


# --- one result per span, in the order asked --------------------------------------------------

def test_one_result_per_span_in_the_order_asked(tmp_path, store):
    """alpha's span takes the comma after it: nothing else claims it, and R10 reaches over
    unaligned tokens. A segment ending mid-clause carries its punctuation for the same reason a
    verse-final one does."""
    got = run(pipeline_file(tmp_path, step_yaml([(_s(2, 1), _s(2, 2)), (_s(1, 1), _s(1, 1))])))
    assert [r["text"] for r in got["english"]] == ["D E", "A,"]


# --- R2: the pair is checked against the file's own documents ----------------------------------
# These take a document rather than a step, so they are called directly: routing a pure helper
# through a pipeline would test the pipeline instead, which `docs/ai-context/project/rules.md`
# carves out explicitly for pure helpers.

def test_the_role_says_which_document_is_the_source():
    """`roles` is positional against `documents`; the source is not the first by convention."""
    validate_pair(
        {"documents": [{"docid": "TGT"}, {"docid": "SRC"}], "roles": ["target", "source"]},
        "SRC", "TGT",
    )


def test_a_pair_matching_the_declared_documents_is_accepted():
    validate_pair(
        {"documents": [{"docid": "SRC"}, {"docid": "TGT"}], "roles": ["source", "target"]},
        "SRC", "TGT",
    )


def test_a_pair_contradicting_the_declared_documents_is_refused_loudly():
    """The Hausa case: a file named for Hebrew whose documents say Greek."""
    doc = {"documents": [{"docid": "OTHER"}, {"docid": "TGT"}], "roles": ["source", "target"]}
    with pytest.raises(ValueError, match="SRC"):
        validate_pair(doc, "SRC", "TGT")
