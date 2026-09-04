"""A book is named two ways, and both must work (#218 follow-up).

SBL-style display names and Paratext-style USFM codes are both what people write, and a
reference is not more or less valid for being written one way. Until now the prescribed parser
took only names and the internal one took only codes, so `Mark 1:1-8` and `MRK 1:1-8` each
failed in one half of the engine — and the internal one silently turned `Mark` into book `MARK`,
a code nothing resolves, so the run returned "no text found" for a passage that exists.

One declaration, `data/book-names.json`, read by both.
"""
import json
import re

import pytest

from llmflow import books
from llmflow.utils.data import parse_bible_reference
from llmflow.utils.scripture import parse_passage_ref


# --- the declaration -----------------------------------------------------------------


def test_every_book_has_a_code_a_number_and_a_name():
    for code, entry in books.table().items():
        assert len(code) == 3, f"{code} is not a USFM code"
        assert entry["number"], code
        assert entry["name"], code
        assert entry["aliases"], f"{code} has no aliases, not even its own name"


def test_the_declaration_is_the_only_copy():
    """`data.py` used to hold 264 alias keys inside a function, unreachable to anything else."""
    path = books.table_path()
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8"))


def test_no_alias_points_at_two_books():
    seen: dict = {}
    for code, entry in books.table().items():
        for alias in entry["aliases"]:
            key = books.normalise(alias)
            assert key not in seen or seen[key] == code, (
                f"{alias!r} maps to both {seen.get(key)} and {code}"
            )
            seen[key] = code


# --- resolving ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "written,code",
    [
        ("Mark", "MRK"), ("mark", "MRK"), ("MARK", "MRK"), ("MRK", "MRK"), ("mrk", "MRK"),
        ("Mk", "MRK"), ("1 John", "1JN"), ("1john", "1JN"), ("1JN", "1JN"), ("1 jn", "1JN"),
        ("Song of Songs", "SNG"), ("SNG", "SNG"), ("Psalms", "PSA"), ("Psalm", "PSA"),
        ("PSA", "PSA"), ("Philippians", "PHP"), ("PHP", "PHP"), ("Philemon", "PHM"),
    ],
)
def test_both_naming_styles_resolve_case_insensitively(written, code):
    assert books.resolve(written) == code


def test_something_that_is_not_a_book_resolves_to_nothing():
    assert books.resolve("Notabook") is None
    assert books.resolve("") is None


def test_an_ambiguous_abbreviation_is_refused_rather_than_guessed():
    """`Ph` is Philippians or Philemon. Choosing one silently is the failure to avoid."""
    with pytest.raises(books.AmbiguousBook) as raised:
        books.resolve("Ph")
    assert "Philippians" in str(raised.value) and "Philemon" in str(raised.value)


# --- the two parsers agree ------------------------------------------------------------


@pytest.mark.parametrize("written", ["Mark 1:1-8", "MRK 1:1-8", "mark 1:1-8", "mrk 1:1-8"])
def test_the_read_path_accepts_both_styles(written):
    reference = parse_passage_ref(written)
    assert (reference.book, reference.start_chapter, reference.start_verse) == ("MRK", 1, 1)
    assert reference.end_verse == 8


@pytest.mark.parametrize("written", ["Mark 3:14", "MRK 3:14"])
def test_the_public_parser_accepts_both_styles(written):
    assert parse_bible_reference(written)["book_code"] == "MRK"


def test_a_multi_word_name_still_parses_in_the_read_path():
    reference = parse_passage_ref("1 John 1:1")
    assert reference.book == "1JN"


def test_the_two_parsers_agree_on_every_book():
    """One declaration means one answer; a book either resolves in both or in neither."""
    for code, entry in books.table().items():
        written = f"{entry['name']} 1:1"
        try:
            public = parse_bible_reference(written)["book_code"]
        except ValueError:
            continue  # a book the public parser's own patterns cannot express
        assert parse_passage_ref(written).book == public, written


# --- through the API a consumer actually uses -----------------------------------------


def test_the_new_arguments_are_reachable_from_a_pipeline(tmp_path):
    """The third edge named by rule 1 in `docs/ai-context/project/rules.md`: a direct call
    satisfies the runner and the object model by construction, so it cannot see an argument
    the API does not expose. Only running a pipeline can.

    `Psalm 3` is 8 verses in `eng` and 9 in `org`, where the superscription is verse 1 — so the
    number proves the argument arrived, not merely that the step ran.
    """
    from llmflow import load_pipeline

    pipeline = tmp_path / "p.yaml"
    pipeline.write_text(
        "name: passage\n"
        "steps:\n"
        "  - name: parse\n"
        "    type: function\n"
        "    function: llmflow.utils.data.parse_bible_reference\n"
        "    inputs:\n"
        '      passage: "Psalm 3"\n'
        "      versification: org\n"
        "    output: parsed\n",
        encoding="utf-8",
    )

    result = load_pipeline(str(pipeline)).run()
    parsed = result["parsed"] if isinstance(result, dict) else result.context["parsed"]
    assert parsed["end_verse"] == 9
    assert parsed["requested_versification"] == "org"


def test_resolve_book_is_part_of_the_published_api():
    """Normalising a book name should not need a bespoke function in every project."""
    import llmflow

    assert "resolve_book" in llmflow.__all__
    assert llmflow.resolve_book("Mark") == "MRK"


def test_every_exported_function_is_in_the_api_catalog():
    """The module-level half of `api_catalog()` is hand-written, so it drifts silently.

    Adding a public function and forgetting the catalog leaves consumers unable to discover it
    from the machine-readable map, which is the map's whole purpose.
    """
    import llmflow
    from llmflow import api_catalog

    catalogued = {entry["name"] for entry in api_catalog()}
    exported = {
        name
        for name in llmflow.__all__
        if callable(getattr(llmflow, name)) and not name[0].isupper()
    }
    assert exported <= catalogued, f"exported but not catalogued: {sorted(exported - catalogued)}"


# --- the document a consumer reads ----------------------------------------------------

FORM_ROW = re.compile(r"^\| `([^`]+)` \| ", re.M)


def _shipped_document() -> str:
    from llmflow import file_catalog as fc

    entry = next(
        e for e in fc.entries() if e.path == "docs/ai-context/sp/passage-references.md"
    )
    content = fc.shipped_content(entry)
    assert content is not None, "passage-references.md ships no content"
    return content


def test_every_form_the_document_shows_actually_parses():
    """The document is what a consumer's assistant reads instead of guessing. A form listed
    there and refused by the parser teaches the wrong thing, authoritatively."""
    forms = [f for f in FORM_ROW.findall(_shipped_document()) if " " in f or f.isupper()]
    assert len(forms) >= 8, f"expected the forms table, found {forms}"
    for form in forms:
        if form.startswith(("requested_", "source_", "extent_", "book_in_")):
            continue  # the returned-fields table, not the forms table
        parse_passage_ref(form)


def test_the_document_says_a_range_may_not_cross_a_book():
    document = _shipped_document()
    assert "may not cross books" in document or "not cross books" in document
    assert "Mark 16:1-Luke 1:4" in document, "and shows the refused example"


# --- ranges ---------------------------------------------------------------------------


def test_a_range_may_cross_a_chapter_boundary():
    reference = parse_passage_ref("Mark 1:40-2:12")
    assert (reference.start_chapter, reference.end_chapter) == (1, 2)


def test_a_range_may_not_cross_a_book_boundary():
    """Two books is two passages; a span across them has no single text to return."""
    with pytest.raises(ValueError, match="one book"):
        parse_passage_ref("Mark 16:1-Luke 1:4")


def test_testament_is_declared_not_inferred_from_the_number():
    """It was `int(number) >= 40` — a threshold nothing stated and nothing could correct."""
    assert books.testament("GEN") == "OT"
    assert books.testament("MAL") == "OT"
    assert books.testament("MAT") == "NT"
    assert books.testament("REV") == "NT"
    for code, entry in books.table().items():
        assert entry["testament"] in ("OT", "NT"), code
        assert entry["original_language"] in ("Hebrew", "Greek"), code


def test_the_public_parser_reads_the_declaration_not_a_copy():
    """`data.py` held 271 alias lines of its own; two copies agree until they silently do not."""
    for code, entry in books.table().items():
        parsed = parse_bible_reference(f"{entry['name']} 1:1")
        assert parsed["book_code"] == code
        assert parsed["book_number"] == entry["number"]
        assert parsed["book_name"] == entry["name"]
        assert parsed["testament"] == entry["testament"]
        assert parsed["original_language"] == entry["original_language"]


def test_a_code_this_engine_does_not_name_is_still_a_code():
    """A closed list would refuse `TST` in a test fixture, `DAG` in a scheme, and any book a
    canon carries that we have never heard of. The shape is the check; the dictionary only adds
    the names."""
    assert books.resolve("XYZ") is None, "the dictionary does not name it"
    assert parse_passage_ref("XYZ 1:1").book == "XYZ", "and it parses anyway, as a code"


def test_something_shaped_like_neither_is_refused():
    with pytest.raises(ValueError, match="not a passage reference"):
        parse_passage_ref("the bit about the shepherd")
