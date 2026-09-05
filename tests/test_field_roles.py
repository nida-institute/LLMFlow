"""A role map declares which fields are evidence and which are content, and what supports what.

Two role words, `evidence` and `content`, list-valued because one field can honestly be both. Two
checks the engine can compute without knowing whose data it is: the order rule, and structural
validity. Everything is reported; a pipeline says what is fatal.

The order rule is the whole point. A model generates properties in schema order, so a field meant
to force the model to attend to its input has to *precede* the claim it supports — and that is a
fact about the schema, visible without a run. `discourse-flow` found the failure it catches by
generating seven artifacts and scanning them; `ears-to-hear` measured an ordering defect in one of
their own schemas the same way.

Out of scope by ruling: severity, occupancy reporting, `empty_expected`, audience. Each needs a
judgment about somebody else's data, and the engine has none.
"""

import json

import pytest

from llmflow.field_roles import (
    RoleMap,
    check_order,
    load_role_map,
    validate_structure,
)

SCHEMA = {
    "type": "object",
    "properties": {
        # Deliberately in this order: `verse` and `greek_quoted` precede what they support,
        # `rhetorical_features` follows the array it draws on, and `is_boundary` follows both.
        "verse": {"type": "string"},
        "greek_quoted": {"type": "string"},
        "levinsohn_signals_to_cite": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "signal": {"type": "string"},
                    "verdict": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
        },
        "rhetorical_features": {"type": "array", "items": {"type": "string"}},
        "is_boundary": {"type": "boolean"},
    },
}

GOOD_MAP = """
schema: schemas/pericope-analysis.json

fields:
  verse:                               [evidence]
  greek_quoted:                        [evidence]
  levinsohn_signals_to_cite[].signal:  [evidence]
  rhetorical_features:                 [content]
  is_boundary:                         [content]

supports:
  levinsohn_signals_to_cite[].verdict: ["levinsohn_signals_to_cite[].signal"]
  rhetorical_features:                 [levinsohn_signals_to_cite]
  is_boundary:                         [verse, greek_quoted]
"""


def write(tmp_path, text, name="pericope-analysis.roles.yaml"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# --- reading the declaration -------------------------------------------------------------


def test_a_role_map_loads(tmp_path):
    roles = load_role_map(write(tmp_path, GOOD_MAP))

    assert isinstance(roles, RoleMap)
    assert roles.schema == "schemas/pericope-analysis.json"
    assert roles.fields["verse"] == ("evidence",)
    assert roles.fields["levinsohn_signals_to_cite[].signal"] == ("evidence",)


def test_a_field_can_hold_both_roles(tmp_path):
    """`opening_word_id` is copied from the input *and* is what identifiers are minted from.

    A scalar would force one of those to be suppressed, which makes the declaration less true
    rather than simpler.
    """
    roles = load_role_map(write(tmp_path, """
schema: s.json
fields:
  opening_word_id: [evidence, content]
"""))

    assert roles.fields["opening_word_id"] == ("evidence", "content")


def test_a_path_used_as_a_value_must_be_quoted_and_the_error_says_so(tmp_path):
    """`a[].v: [a[].s]` opens a nested flow sequence and fails.

    `discourse-flow` copied an unquoted example from the design document and four of their five
    maps failed with `ParserError: while parsing a flow sequence`, which says nothing about what
    to do. The reader has to.
    """
    path = write(tmp_path, """
schema: s.json
supports:
  a[].v: [a[].s]
""")

    with pytest.raises(ValueError, match="quote paths used as values"):
        load_role_map(path)


def test_block_style_is_equally_valid(tmp_path):
    roles = load_role_map(write(tmp_path, """
schema: s.json
supports:
  levinsohn_signals_to_cite[].verdict:
    - levinsohn_signals_to_cite[].signal
"""))

    assert roles.supports["levinsohn_signals_to_cite[].verdict"] == (
        "levinsohn_signals_to_cite[].signal",
    )


# --- structural validity -----------------------------------------------------------------


def test_a_valid_map_reports_nothing(tmp_path):
    roles = load_role_map(write(tmp_path, GOOD_MAP))

    assert validate_structure(roles, SCHEMA) == []


def test_a_path_absent_from_the_schema_is_reported(tmp_path):
    roles = load_role_map(write(tmp_path, """
schema: s.json
fields:
  no_such_field: [evidence]
"""))
    findings = validate_structure(roles, SCHEMA)

    assert any("no_such_field" in f for f in findings)


def test_a_path_reaching_into_an_array_resolves(tmp_path):
    """`a[].b` reaches `properties.a.items.properties.b`, which is the whole point of the syntax."""
    roles = load_role_map(write(tmp_path, """
schema: s.json
fields:
  levinsohn_signals_to_cite[].reason: [content]
"""))

    assert validate_structure(roles, SCHEMA) == []


def test_a_path_declared_twice_is_reported(tmp_path):
    """YAML would silently keep the last of two identical keys, so the file is read as text."""
    roles = load_role_map(write(tmp_path, """
schema: s.json
fields:
  verse: [evidence]
  verse: [content]
"""))
    findings = validate_structure(roles, SCHEMA)

    assert any("declared twice" in f and "verse" in f for f in findings)


def test_a_scalar_role_is_reported(tmp_path):
    roles = load_role_map(write(tmp_path, """
schema: s.json
fields:
  verse: evidence
"""))
    findings = validate_structure(roles, SCHEMA)

    assert any("list" in f for f in findings)


def test_a_role_word_the_engine_does_not_define_is_carried_without_complaint(tmp_path):
    """`sp` defines two words and does not reject a third.

    `handoff` is a fact a project knows about its own pipeline and nobody downstream could. The
    engine's checks do not touch it, so refusing it would be legislating a vocabulary rather than
    providing one.
    """
    roles = load_role_map(write(tmp_path, """
schema: s.json
fields:
  verse: [evidence, handoff]
"""))

    assert validate_structure(roles, SCHEMA) == []
    assert "handoff" in roles.fields["verse"]


# --- the order rule ----------------------------------------------------------------------


def test_supporting_before_supported_reports_nothing(tmp_path):
    roles = load_role_map(write(tmp_path, GOOD_MAP))

    assert check_order(roles, SCHEMA) == []


def test_supporting_after_supported_is_reported(tmp_path):
    """`verse` follows `is_boundary` in no schema here — so invert one that does.

    `greek_quoted` precedes `levinsohn_signals_to_cite`, so declaring the array as support for
    `greek_quoted` puts the evidence after the claim.
    """
    roles = load_role_map(write(tmp_path, """
schema: s.json
supports:
  greek_quoted: [levinsohn_signals_to_cite]
"""))
    findings = check_order(roles, SCHEMA)

    assert findings, "evidence generated after the claim it supports cannot force anything"
    assert any("greek_quoted" in f and "levinsohn_signals_to_cite" in f for f in findings)


def test_the_order_rule_holds_inside_an_array_item(tmp_path):
    """`signal` precedes `verdict` within the item, which is what makes the anchor work.

    Without this the check degrades to "some evidence exists somewhere", which is the defect it
    exists to catch — and it is the level `discourse-flow`'s 55.2% measurement turns on.
    """
    roles = load_role_map(write(tmp_path, """
schema: s.json
supports:
  levinsohn_signals_to_cite[].verdict: ["levinsohn_signals_to_cite[].signal"]
"""))

    assert check_order(roles, SCHEMA) == []


def test_an_inverted_order_inside_an_array_item_is_reported(tmp_path):
    """`verdict` precedes `reason`, so declaring `reason` as support for `verdict` inverts it."""
    roles = load_role_map(write(tmp_path, """
schema: s.json
supports:
  levinsohn_signals_to_cite[].verdict: ["levinsohn_signals_to_cite[].reason"]
"""))
    findings = check_order(roles, SCHEMA)

    assert findings
    assert any("[].verdict" in f for f in findings)


def test_paths_at_different_levels_compare_at_their_outermost_difference(tmp_path):
    """`is_boundary` supported by a path inside the array: the array must precede it.

    Comparison is at the first segment where the two paths diverge — the array's own position at
    the top level — because that is the point at which the model generates one before the other.
    """
    roles = load_role_map(write(tmp_path, """
schema: s.json
supports:
  is_boundary: ["levinsohn_signals_to_cite[].signal"]
"""))

    assert check_order(roles, SCHEMA) == []


def test_a_supporting_path_absent_from_the_schema_is_reported_by_the_order_check(tmp_path):
    """An unresolvable path has no position, so the order rule cannot be evaluated for it."""
    roles = load_role_map(write(tmp_path, """
schema: s.json
supports:
  is_boundary: [nowhere]
"""))
    findings = check_order(roles, SCHEMA)

    assert any("nowhere" in f for f in findings)


def test_nothing_raises_on_a_finding(tmp_path):
    """Reported, never judged: the pipeline decides what is fatal.

    `discourse-flow`, reconciling two of their own rules: *"`sp` computes the verdict and exposes
    it; the pipeline says `fatal` or `report`."*
    """
    roles = load_role_map(write(tmp_path, """
schema: s.json
fields:
  no_such_field: [evidence]
supports:
  greek_quoted: [levinsohn_signals_to_cite]
"""))

    assert validate_structure(roles, SCHEMA)
    assert check_order(roles, SCHEMA)


def test_a_supports_path_need_not_be_declared_in_fields(tmp_path):
    """Deliberate, and it is what answers `discourse-flow`'s `adjudication` need.

    What the engine needs to know about `[].verdict` is what it is ordered against, not what to
    call it. So a `supports` path must exist in the *schema*, not in `fields`.
    """
    roles = load_role_map(write(tmp_path, GOOD_MAP))

    assert "levinsohn_signals_to_cite[].verdict" not in roles.fields
    assert validate_structure(roles, SCHEMA) == []
    assert check_order(roles, SCHEMA) == []


def test_the_schema_is_read_in_property_order(tmp_path):
    """The rule rests on generation following schema order, so `json.load` must preserve it.

    `discourse-flow` measured the premise rather than taking it: 166 of 166 responses matched
    their schema's property order exactly, 0 deviating. Re-derive with their command in
    `design-declaring-field-roles.md` §4.
    """
    text = json.dumps(SCHEMA)
    assert list(json.loads(text)["properties"]) == [
        "verse",
        "greek_quoted",
        "levinsohn_signals_to_cite",
        "rhetorical_features",
        "is_boundary",
    ]
