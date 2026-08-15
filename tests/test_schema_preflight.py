"""Structured-output schemas are checked before the run (LLMFlow#196).

Under `strict: true` OpenAI accepts only a restricted subset of JSON Schema and rejects
anything outside it with HTTP 400 *at request time* — so a pipeline could pass every check,
fetch its passage, complete three steps, and die on the fourth after the earlier steps had
been paid for.

Hard rules are errors, per the Captain's decision (see
project/plans/design-structured-output-preflight.md). Keyword and size limits are warnings,
because OpenAI has widened the accepted subset over time and a stale rule table must not
block work that the provider would in fact accept.

The fixtures are the real schemas from pipelines/json-schema-example.yaml, which violated
the "every property required" rule in five places.
"""
import pytest

from llmflow.utils.schema_preflight import Severity, check_strict_schema


def _errors(schema):
    return [f for f in check_strict_schema(schema) if f.severity == Severity.ERROR]


def _warnings(schema):
    return [f for f in check_strict_schema(schema) if f.severity == Severity.WARNING]


def _obj(properties, required=None, extra_false=True):
    s = {"type": "object", "properties": properties,
         "required": list(properties) if required is None else required}
    if extra_false:
        s["additionalProperties"] = False
    return s


class TestEveryPropertyMustBeRequired:
    def test_missing_property_is_an_error(self):
        s = _obj({"a": {"type": "string"}, "b": {"type": "string"}}, required=["a"])
        errs = _errors(s)
        assert errs and any("b" in e.message for e in errs), errs

    def test_all_present_is_clean(self):
        assert _errors(_obj({"a": {"type": "string"}})) == []

    def test_nullable_optional_is_the_documented_workaround(self):
        s = _obj({"a": {"type": "string"}, "b": {"type": ["string", "null"]}})
        assert _errors(s) == []

    def test_the_fix_is_suggested(self):
        s = _obj({"a": {"type": "string"}, "b": {"type": "string"}}, required=["a"])
        assert any("null" in e.fix for e in _errors(s)), "should offer the nullable form"

    def test_missing_required_entirely_is_an_error(self):
        s = {"type": "object", "properties": {"a": {"type": "string"}},
             "additionalProperties": False}
        assert _errors(s)

    def test_nested_object_is_checked(self):
        s = _obj({"outer": _obj({"x": {"type": "string"}, "y": {"type": "string"}},
                                required=["x"])})
        errs = _errors(s)
        assert errs and any("y" in e.message for e in errs), errs

    def test_array_items_object_is_checked(self):
        s = _obj({"list": {"type": "array",
                           "items": _obj({"x": {"type": "string"},
                                          "y": {"type": "string"}}, required=["x"])}})
        errs = _errors(s)
        assert errs and any("y" in e.message for e in errs), errs

    def test_path_points_at_the_offending_object(self):
        s = _obj({"list": {"type": "array",
                           "items": _obj({"x": {"type": "string"},
                                          "y": {"type": "string"}}, required=["x"])}})
        assert any("items" in e.path for e in _errors(s)), [e.path for e in _errors(s)]


class TestAdditionalPropertiesFalse:
    def test_missing_is_an_error(self):
        s = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        assert any("additionalProperties" in e.message for e in _errors(s))

    def test_true_is_an_error(self):
        s = {"type": "object", "properties": {"a": {"type": "string"}},
             "required": ["a"], "additionalProperties": True}
        assert any("additionalProperties" in e.message for e in _errors(s))


class TestRootMustBeAnObject:
    @pytest.mark.parametrize("schema", [
        {"type": "array", "items": {"type": "string"}},
        {"type": "string"},
        {"anyOf": [{"type": "object", "properties": {}, "required": [],
                    "additionalProperties": False}]},
    ])
    def test_non_object_root_is_an_error(self, schema):
        assert any("root" in e.message.lower() for e in _errors(schema)), schema


class TestRefs:
    def test_resolvable_ref_is_clean(self):
        s = {
            "type": "object",
            "properties": {"a": {"$ref": "#/$defs/thing"}},
            "required": ["a"], "additionalProperties": False,
            "$defs": {"thing": _obj({"x": {"type": "string"}})},
        }
        assert _errors(s) == []

    def test_dangling_ref_is_an_error(self):
        s = _obj({"a": {"$ref": "#/$defs/missing"}})
        assert any("$ref" in e.message or "missing" in e.message for e in _errors(s))

    def test_recursive_ref_terminates(self):
        """A self-referential schema must not hang the linter."""
        s = {
            "type": "object",
            "properties": {"child": {"$ref": "#"}},
            "required": ["child"], "additionalProperties": False,
        }
        check_strict_schema(s)  # must return


class TestWarningsNotErrors:
    """OpenAI has widened the subset over time; a stale table must not block work."""

    @pytest.mark.parametrize("keyword,value", [
        ("allOf", [{"type": "object"}]),
        ("not", {"type": "string"}),
        ("if", {"type": "string"}),
        ("default", "x"),
        ("patternProperties", {"^a": {"type": "string"}}),
    ])
    def test_unsupported_keyword_warns(self, keyword, value):
        s = _obj({"a": {"type": "string"}})
        s["properties"]["a"][keyword] = value
        assert _warnings(s), f"{keyword} should warn"
        assert not any(keyword in e.message for e in _errors(s)), f"{keyword} must not error"

    def test_oneOf_suggests_anyOf(self):
        s = _obj({"a": {"oneOf": [{"type": "string"}, {"type": "integer"}]}})
        w = _warnings(s)
        assert w and any("anyOf" in x.fix or "anyOf" in x.message for x in w), w

    def test_rule_table_is_dated(self):
        """A checker encoding a moving target must say when it was last checked."""
        from llmflow.utils import schema_preflight
        assert schema_preflight.RULES_LAST_VERIFIED
        assert schema_preflight.RULES_DOC_URL.startswith("https://")


class TestTheFlagshipExample:
    """The real schemas from pipelines/json-schema-example.yaml, pre-fix."""

    def test_segment_book_schema_is_rejected(self):
        s = {
            "type": "object",
            "properties": {
                "book": {"type": "string"},
                "segmentation_rationale": {"type": "string"},
                "pericopes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "passage": {"type": "string"},
                            "start_verse": {"type": "string"},
                            "end_verse": {"type": "string"},
                            "theme": {"type": "string"},
                            "pericope_type": {"type": "string",
                                              "enum": ["narrative", "teaching"]},
                        },
                        "required": ["title", "passage", "theme"],
                        "additionalProperties": False,
                    },
                },
                "total_pericopes": {"type": "integer"},
            },
            "required": ["book", "pericopes", "total_pericopes"],
            "additionalProperties": False,
        }
        errs = _errors(s)
        reported = " ".join(e.message for e in errs)
        for missing in ("segmentation_rationale", "start_verse", "end_verse", "pericope_type"):
            assert missing in reported, f"{missing} not reported; got {reported}"

    def test_enum_is_allowed(self):
        s = _obj({"kind": {"type": "string", "enum": ["a", "b"]}})
        assert _errors(s) == []
