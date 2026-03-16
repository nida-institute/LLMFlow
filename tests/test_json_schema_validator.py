"""Tests for the json_schema_validator plugin.

Key scenario: payloads may arrive as native Python objects (fresh LLM run) OR
as raw JSON strings/bytes (loaded from disk via --rewind-to).  Both must
validate successfully.
"""

import json

import pytest

from llmflow.plugins.json_schema_validator import execute
from llmflow.plugins.loader import plugin_registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ARRAY_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "summary"],
        "properties": {
            "id": {"type": "integer"},
            "summary": {"type": "string"},
        },
    },
}

VALID_PAYLOAD = [{"id": 1, "summary": "Scene one"}, {"id": 2, "summary": "Scene two"}]


@pytest.fixture
def schema_file(tmp_path):
    path = tmp_path / "test.schema.json"
    path.write_text(json.dumps(ARRAY_SCHEMA), encoding="utf-8")
    return path


def _step_config(payload, schema_path):
    return {"inputs": {"payload": payload, "schema_path": str(schema_path)}}


# ---------------------------------------------------------------------------
# Core behaviour
# ---------------------------------------------------------------------------


class TestJsonSchemaValidator:
    def test_valid_python_object_passes(self, schema_file):
        """Fresh-run path: payload is already a Python list."""
        result = execute(_step_config(VALID_PAYLOAD, schema_file))
        assert result == VALID_PAYLOAD

    def test_valid_json_string_passes(self, schema_file):
        """Rewind path: payload is a JSON string loaded from disk."""
        payload_str = json.dumps(VALID_PAYLOAD)
        result = execute(_step_config(payload_str, schema_file))
        assert result == VALID_PAYLOAD

    def test_valid_json_bytes_passes(self, schema_file):
        """Rewind path: payload is JSON bytes (e.g. read_bytes() from Path)."""
        payload_bytes = json.dumps(VALID_PAYLOAD).encode("utf-8")
        result = execute(_step_config(payload_bytes, schema_file))
        assert result == VALID_PAYLOAD

    def test_invalid_python_object_raises(self, schema_file):
        """A Python object that fails the schema should still raise."""
        import jsonschema

        bad_payload = [{"id": "not-an-int", "summary": "oops"}]
        with pytest.raises(jsonschema.ValidationError):
            execute(_step_config(bad_payload, schema_file))

    def test_invalid_json_string_raises(self, schema_file):
        """A serialised payload that fails the schema should still raise."""
        import jsonschema

        bad_payload = json.dumps([{"id": "not-an-int", "summary": "oops"}])
        with pytest.raises(jsonschema.ValidationError):
            execute(_step_config(bad_payload, schema_file))

    def test_missing_schema_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            execute(_step_config(VALID_PAYLOAD, tmp_path / "nonexistent.schema.json"))

    def test_missing_payload_key_raises(self, schema_file):
        with pytest.raises(ValueError, match="payload"):
            execute({"inputs": {"schema_path": str(schema_file)}})

    def test_missing_schema_path_key_raises(self, schema_file):
        with pytest.raises(ValueError, match="schema_path"):
            execute({"inputs": {"payload": VALID_PAYLOAD}})

    def test_returns_parsed_payload_not_string(self, schema_file):
        """Return value should be the native object so downstream steps work."""
        payload_str = json.dumps(VALID_PAYLOAD)
        result = execute(_step_config(payload_str, schema_file))
        assert isinstance(result, list)

    def test_registered_in_plugin_registry(self):
        """Plugin must be discoverable via the standard registry."""
        assert "json_schema_validator" in plugin_registry
        assert callable(plugin_registry["json_schema_validator"])
