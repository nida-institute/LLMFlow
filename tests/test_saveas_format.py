"""`saveas` serialisation: where the format comes from, and what each value writes.

The format is a property of the file being written, so it is read from the `saveas` config and
never from the step. A step type's own `format:` key means something else entirely — `usj` for
`type: scripture`, `records` for `type: duckdb`, `csv` for `type: load_directory` — and none of
those name a serialiser.
"""
import csv
import io
import json
import unicodedata

import pytest
import yaml

from llmflow.utils.file_io import save_content_to_file
from llmflow.utils.step_outputs import handle_step_saveas

USJ = {"type": "USJ", "version": "3.1", "content": [{"type": "book", "code": "PHM"}]}
RECORDS = [{"ref": "PHM 1:1", "text": "Παῦλος"}, {"ref": "PHM 1:2", "text": "καὶ"}]


# ---------------------------------------------------------------------------
# The format comes from the saveas config
# ---------------------------------------------------------------------------


def test_the_dict_form_honours_its_own_format(tmp_path):
    """`saveas: {path: ..., format: json}` serialises as JSON even where the path does not say so."""
    step = {"output": "doc", "saveas": {"path": str(tmp_path / "out.dat"), "format": "json"}}
    written = handle_step_saveas(step, {"doc": USJ})
    assert json.loads(open(written[0], encoding="utf-8").read()) == USJ


def test_a_step_level_format_never_reaches_the_serialiser(tmp_path):
    """A step's own `format:` is that step type's vocabulary and is not a serialisation name."""
    step = {"output": "doc", "format": "usj", "saveas": str(tmp_path / "out.json")}
    written = handle_step_saveas(step, {"doc": USJ})
    assert json.loads(open(written[0], encoding="utf-8").read()) == USJ


@pytest.mark.parametrize("step_format", ["usj", "milestones", "plain", "records", "df", "tsv"])
def test_no_step_format_can_corrupt_a_json_file(tmp_path, step_format):
    """Every step-type format value leaves a `.json` path holding JSON."""
    step = {"output": "doc", "format": step_format, "saveas": str(tmp_path / "out.json")}
    written = handle_step_saveas(step, {"doc": USJ})
    assert json.loads(open(written[0], encoding="utf-8").read()) == USJ


def test_the_list_form_reads_each_item(tmp_path):
    """Each entry in a list-form saveas carries its own format."""
    step = {
        "output": "doc",
        "format": "usj",
        "saveas": [
            {"path": str(tmp_path / "a.dat"), "format": "json"},
            {"path": str(tmp_path / "b.txt"), "format": "text"},
        ],
    }
    written = handle_step_saveas(step, {"doc": USJ})
    assert json.loads(open(written[0], encoding="utf-8").read()) == USJ
    assert open(written[1], encoding="utf-8").read().startswith("{'type'")


def test_the_schema_and_the_writers_accept_the_same_values():
    """The schema's enum and the writer's alias table are one vocabulary in two files."""
    import json
    from pathlib import Path

    from llmflow import file_catalog as fc
    from llmflow.utils.file_io import FORMAT_ALIASES

    schema = json.loads(
        (Path(fc.__file__).resolve().parent / "schema" / "pipeline.schema.json").read_text()
    )
    declared = set(schema["$defs"]["SaveasConfig"]["properties"]["format"]["enum"])
    assert declared == set(FORMAT_ALIASES) | {"auto"}, (
        "The saveas format vocabulary differs between the schema and file_io.FORMAT_ALIASES. "
        f"schema only: {sorted(declared - set(FORMAT_ALIASES) - {'auto'})}; "
        f"code only: {sorted(set(FORMAT_ALIASES) | {'auto'} - declared)}."
    )


def test_saveas_reads_no_step_level_key():
    """The saveas handler consults the step only for `saveas`, `output` and `name`."""
    import inspect

    from llmflow.utils import step_outputs

    body = inspect.getsource(step_outputs.handle_step_saveas)
    assert 'step.get("format"' not in body and "step.get('format'" not in body


# ---------------------------------------------------------------------------
# One vocabulary, two notations
# ---------------------------------------------------------------------------

PAIRS = [
    ("json", "application/json", USJ),
    ("yaml", "application/yaml", USJ),
    ("text", "text/plain", "plain words"),
    ("markdown", "text/markdown", "# Heading"),
    ("csv", "text/csv", RECORDS),
    ("tsv", "text/tab-separated-values", RECORDS),
]


@pytest.mark.parametrize("informal,mime,content", PAIRS)
def test_a_mime_type_writes_what_its_informal_name_writes(tmp_path, informal, mime, content):
    a = save_content_to_file(content, str(tmp_path / f"a-{informal}.out"), informal)
    b = save_content_to_file(content, str(tmp_path / f"b-{informal}.out"), mime)
    assert open(a, encoding="utf-8").read() == open(b, encoding="utf-8").read()


@pytest.mark.parametrize("alias", ["application/yaml", "text/yaml", "application/x-yaml"])
def test_every_yaml_spelling_is_accepted(tmp_path, alias):
    written = save_content_to_file(USJ, str(tmp_path / "out.out"), alias)
    assert yaml.safe_load(open(written, encoding="utf-8").read()) == USJ


def test_usj_writes_json(tmp_path):
    """USJ has no registered mime type and is JSON on disk."""
    written = save_content_to_file(USJ, str(tmp_path / "out.out"), "usj")
    assert json.loads(open(written, encoding="utf-8").read()) == USJ


# ---------------------------------------------------------------------------
# The new writers
# ---------------------------------------------------------------------------


def test_records_write_as_tsv_with_a_header(tmp_path):
    written = save_content_to_file(RECORDS, str(tmp_path / "out.tsv"), "tsv")
    rows = list(csv.reader(io.StringIO(open(written, encoding="utf-8").read()), delimiter="\t"))
    assert rows[0] == ["ref", "text"]
    assert rows[1] == ["PHM 1:1", "Παῦλος"]


def test_a_tab_inside_a_value_survives_the_round_trip(tmp_path):
    """A delimiter inside a value is quoted, not written raw."""
    rows = [{"ref": "PHM 1:1", "text": "before\tafter"}]
    written = save_content_to_file(rows, str(tmp_path / "out.tsv"), "tsv")
    parsed = list(csv.DictReader(io.StringIO(open(written, encoding="utf-8").read()), delimiter="\t"))
    assert parsed[0]["text"] == "before\tafter"


def test_records_disagreeing_on_keys_are_refused(tmp_path):
    rows = [{"ref": "PHM 1:1"}, {"ref": "PHM 1:2", "text": "καὶ"}]
    with pytest.raises(ValueError, match="keys"):
        save_content_to_file(rows, str(tmp_path / "out.csv"), "csv")


def test_an_lxml_element_writes_as_xml(tmp_path):
    from lxml.etree import fromstring

    element = fromstring("<verse><w>Παῦλος</w></verse>")
    written = save_content_to_file(element, str(tmp_path / "out.xml"), "xml")
    assert "<w>Παῦλος</w>" in open(written, encoding="utf-8").read()


def test_an_xml_string_is_checked_for_well_formedness(tmp_path):
    with pytest.raises(ValueError, match="well-formed"):
        save_content_to_file("<verse><w>oops</verse>", str(tmp_path / "out.xml"), "xml")


def test_a_dict_is_not_guessable_as_xml(tmp_path):
    """There is no defined mapping from a mapping to XML."""
    with pytest.raises(ValueError, match="xml"):
        save_content_to_file(USJ, str(tmp_path / "out.xml"), "xml")


def test_an_xpath_result_set_writes_as_a_fragment(tmp_path):
    """A list of siblings is written as xml, not as `str(list)`."""
    results = ['<entry key="alpha">Alpha</entry>', '<entry key="beta">Beta</entry>']
    written = save_content_to_file(results, str(tmp_path / "out.xml"), "xml")
    text = open(written, encoding="utf-8").read()
    assert text == '<entry key="alpha">Alpha</entry>\n<entry key="beta">Beta</entry>'
    assert "['" not in text


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


def test_an_unknown_format_names_the_accepted_values(tmp_path):
    with pytest.raises(ValueError) as caught:
        save_content_to_file(USJ, str(tmp_path / "out.out"), "parquet")
    message = str(caught.value)
    assert "parquet" in message and "json" in message and "tsv" in message


def test_a_mapping_is_never_stringified_by_accident(tmp_path):
    """An unrecognised extension cannot fall back to `str()` on a mapping."""
    with pytest.raises(ValueError):
        save_content_to_file(USJ, str(tmp_path / "out.dat"))


def test_text_still_falls_back_to_plain_text(tmp_path):
    """A string with an unrecognised extension is written as text, as before."""
    written = save_content_to_file("just words", str(tmp_path / "notes.dat"))
    assert open(written, encoding="utf-8").read() == "just words"


# ---------------------------------------------------------------------------
# Every write is NFC
# ---------------------------------------------------------------------------


def test_a_written_file_is_nfc(tmp_path):
    decomposed = unicodedata.normalize("NFD", "λόγος")
    written = save_content_to_file(decomposed, str(tmp_path / "out.txt"), "text")
    text = open(written, encoding="utf-8").read()
    assert text == unicodedata.normalize("NFC", text)
    assert text == unicodedata.normalize("NFC", decomposed)


def test_json_content_is_normalised_too(tmp_path):
    doc = {"text": unicodedata.normalize("NFD", "λόγος")}
    written = save_content_to_file(doc, str(tmp_path / "out.json"), "json")
    text = open(written, encoding="utf-8").read()
    assert text == unicodedata.normalize("NFC", text)


def test_the_greek_question_mark_becomes_a_semicolon(tmp_path):
    """U+037E has a singleton canonical decomposition, so NFC always writes U+003B."""
    written = save_content_to_file("τί;", str(tmp_path / "out.txt"), "text")
    text = open(written, encoding="utf-8").read()
    assert ";" not in text
    assert text.endswith(";")
