"""The properties `utils/file_io.dump_yaml` guarantees, and that it is the only serialiser.

Each test names one property of the written document: it round-trips, non-Latin scripts are
written as themselves, key order is the order given, collections are block style, nested
mappings indent by two, and scalars PyYAML would retype survive quoted.

The last test refuses a second `yaml.dump`/`yaml.safe_dump` anywhere in `src/`, because a
second call site is a second set of defaults.

Conventions: `design-is-declarative`, `reference-data-is-json`.
"""
from pathlib import Path

import pytest
import yaml

from llmflow.utils.file_io import dump_yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src" / "llmflow"

#: Where the one permitted call to PyYAML's dumper lives.
SERIALISER = SRC / "utils" / "file_io.py"


def test_output_round_trips():
    data = {"resource": "SBLGNT", "families": ["ids", "senses"], "count": 3}
    assert yaml.safe_load(dump_yaml(data)) == data


def test_greek_and_hebrew_are_written_as_themselves():
    """`allow_unicode=True`. Escaped source text is unreadable to the reviewer who must check it."""
    data = {"greek": "Παῦλος δέσμιος", "hebrew": "וַיְהִ֗י"}
    written = dump_yaml(data)

    assert "Παῦλος δέσμιος" in written
    assert "וַיְהִ֗י" in written
    assert "\\u" not in written
    assert yaml.safe_load(written) == data


def test_key_order_is_the_order_given():
    """`sort_keys=False`. A registration reads in the order its author wrote it."""
    data = {"zebra": 1, "alpha": 2, "middle": 3}
    lines = [line.split(":")[0] for line in dump_yaml(data).splitlines() if line.strip()]

    assert lines == ["zebra", "alpha", "middle"]


def test_collections_are_block_style_not_flow():
    written = dump_yaml({"families": ["ids", "senses"], "nested": {"a": 1}})

    assert "[" not in written and "{" not in written
    assert "- ids" in written


def test_nested_mappings_indent_by_two():
    written = dump_yaml({"outer": {"inner": "value"}})

    assert "\n  inner: value" in written


def test_a_scripture_reference_survives_the_round_trip():
    """PyYAML reads a bare `1:1` as the integer 61. The dumper must quote it on the way out.

    Rule `reference-data-is-json` keeps such data out of YAML entirely; this asserts that where
    it does pass through, the writer does not create the trap it warns about.
    """
    data = {"opening": "1:1", "closing": "1:3"}
    written = dump_yaml(data)

    assert yaml.safe_load(written) == data
    assert yaml.safe_load(written)["opening"] == "1:1"


def test_a_no_valued_string_survives_the_round_trip():
    """`NO` resolves to False unquoted — a language code, a column value, an answer."""
    data = {"answer": "NO", "code": "NO"}

    assert yaml.safe_load(dump_yaml(data)) == data


def test_the_dumper_is_the_safe_one():
    """`yaml.dump` emits `!!python/` tags for objects `safe_load` then refuses to read back."""
    with pytest.raises(yaml.YAMLError):
        dump_yaml({"when": object()})


def test_src_has_exactly_one_yaml_serialiser():
    """A second `yaml.dump`/`yaml.safe_dump` in `src/` is a second set of defaults.

    That is how the four writers this file replaced came to disagree about key order and about
    which dumper to use. Reuse `dump_yaml` rather than adding a call here.
    """
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "yaml.dump(" in line or "yaml.safe_dump(" in line:
                if path == SERIALISER:
                    continue
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{number}: {line.strip()}")

    assert not offenders, (
        "YAML is serialised outside `utils/file_io.dump_yaml`:\n  " + "\n  ".join(offenders)
    )
