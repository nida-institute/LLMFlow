"""`sp lint` runs the role-map checks, so an inert forcing device is caught before a run.

A role map sits beside its schema — `X.json` and `X.roles.yaml` — and the order rule is a fact
about property order, visible without calling a model. That is the whole argument for declaring
roles rather than inferring them: `discourse-flow` found the failure this catches by generating
seven artifacts and scanning them, and the cause was ordering.

Findings are **warnings**, not errors. The engine reports; the pipeline decides what is fatal.
`discourse-flow`, reconciling two of their own rules: *"`sp` computes the verdict and exposes it;
the pipeline says `fatal` or `report`."*

A schema with no role map beside it is the common case and says nothing at all — silence, not a
warning, because most schemas have no anchors to declare.
"""

import json

from llmflow.utils.linter import validate_structured_output_schemas

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verse", "signals", "is_boundary"],
    "properties": {
        "verse": {"type": "string"},
        "signals": {"type": "array", "items": {"type": "string"}},
        "is_boundary": {"type": "boolean"},
    },
}


def a_step(schema_file):
    return {
        "name": "analyse",
        "type": "llm",
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "s", "strict": True, "schema_file": str(schema_file)},
        },
    }


def write_schema(tmp_path, name="analysis.json"):
    path = tmp_path / name
    path.write_text(json.dumps(SCHEMA), encoding="utf-8")
    return path


def test_a_schema_without_a_role_map_says_nothing(tmp_path):
    """The common case. Most schemas declare no roles, and that is not a finding."""
    schema = write_schema(tmp_path)
    warnings: list = []

    validate_structured_output_schemas([a_step(schema)], {}, warnings)

    assert not [w for w in warnings if "role" in w.lower()]


def test_a_sound_role_map_says_nothing(tmp_path):
    schema = write_schema(tmp_path)
    (tmp_path / "analysis.roles.yaml").write_text(
        "schema: analysis.json\n"
        "fields:\n"
        "  verse: [evidence]\n"
        "  is_boundary: [content]\n"
        "supports:\n"
        "  is_boundary: [verse]\n",
        encoding="utf-8",
    )
    warnings: list = []

    validate_structured_output_schemas([a_step(schema)], {}, warnings)

    assert not [w for w in warnings if "role map" in w.lower()]


def test_evidence_after_its_claim_is_reported(tmp_path):
    """`verse` precedes `is_boundary`, so declaring `verse` as supported *by* it inverts the rule."""
    schema = write_schema(tmp_path)
    (tmp_path / "analysis.roles.yaml").write_text(
        "schema: analysis.json\nsupports:\n  verse: [is_boundary]\n", encoding="utf-8"
    )
    warnings: list = []

    validate_structured_output_schemas([a_step(schema)], {}, warnings)

    reported = [w for w in warnings if "is_boundary" in w and "verse" in w]
    assert reported, f"expected an ordering finding, got {warnings}"
    assert "analyse" in reported[0], "a finding names the step it came from"


def test_a_path_absent_from_the_schema_is_reported(tmp_path):
    schema = write_schema(tmp_path)
    (tmp_path / "analysis.roles.yaml").write_text(
        "schema: analysis.json\nfields:\n  no_such_field: [evidence]\n", encoding="utf-8"
    )
    warnings: list = []

    validate_structured_output_schemas([a_step(schema)], {}, warnings)

    assert [w for w in warnings if "no_such_field" in w]


def test_an_unparseable_role_map_is_reported_with_what_to_do(tmp_path):
    """The YAML error is about flow sequences; the finding has to name the fix."""
    schema = write_schema(tmp_path)
    (tmp_path / "analysis.roles.yaml").write_text(
        "schema: analysis.json\nsupports:\n  a[].v: [a[].s]\n", encoding="utf-8"
    )
    warnings: list = []

    validate_structured_output_schemas([a_step(schema)], {}, warnings)

    assert [w for w in warnings if "quote paths used as values" in w]


def test_findings_are_warnings_and_never_errors(tmp_path):
    """Severity is the pipeline's. A role-map finding must not stop a run on the engine's word."""
    schema = write_schema(tmp_path)
    (tmp_path / "analysis.roles.yaml").write_text(
        "schema: analysis.json\nsupports:\n  verse: [is_boundary]\n", encoding="utf-8"
    )
    warnings: list = []

    errors = validate_structured_output_schemas([a_step(schema)], {}, warnings)

    assert not [e for e in (errors or []) if "role map" in e.lower() or "verse" in e]
    assert warnings
