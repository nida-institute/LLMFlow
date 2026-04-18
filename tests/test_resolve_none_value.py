"""
Tests for resolve() correctly handling None values in context.

Bug: resolve() cannot distinguish "variable not found" from "variable found, value is None".
Both cases return the original template string, causing silent data corruption when a
pipeline step legitimately produces a None field value.
"""
import pytest
from llmflow.runner import resolve, run_for_each_step


class TestResolveNoneValue:
    def test_none_top_level_variable_returns_none(self):
        """${var} where var=None should return None, not the literal string."""
        context = {"var": None}
        result = resolve("${var}", context)
        assert result is None, (
            f"Expected None but got {result!r}. "
            "resolve() conflates 'not found' with 'value is None'."
        )

    def test_none_dot_notation_field_returns_none(self):
        """${obj.field} where obj.field=None should return None, not the literal string."""
        context = {"obj": {"field": None, "other": "present"}}
        result = resolve("${obj.field}", context)
        assert result is None, (
            f"Expected None but got {result!r} for ${'{obj.field}'} where field=None."
        )

    def test_missing_variable_still_returns_template_string(self):
        """${missing} where key does not exist should still return the template string."""
        context = {}
        result = resolve("${missing}", context)
        assert result == "${missing}", (
            f"Missing variable should return template string, got {result!r}."
        )

    def test_missing_dot_notation_still_returns_template_string(self):
        """${obj.field} where obj doesn't exist should still return the template string."""
        context = {}
        result = resolve("${obj.field}", context)
        assert result == "${obj.field}", (
            f"Missing dot-notation variable should return template string, got {result!r}."
        )

    def test_false_value_resolves_correctly(self):
        """${var} where var=False should return False, not the template string."""
        context = {"var": False}
        result = resolve("${var}", context)
        assert result is False, f"Expected False but got {result!r}."

    def test_zero_value_resolves_correctly(self):
        """${var} where var=0 should return 0, not the template string."""
        context = {"var": 0}
        result = resolve("${var}", context)
        assert result == 0, f"Expected 0 but got {result!r}."

    def test_empty_string_value_resolves_correctly(self):
        """${var} where var='' should return '', not the template string."""
        context = {"var": ""}
        result = resolve("${var}", context)
        assert result == "", f"Expected empty string but got {result!r}."

    def test_empty_list_value_resolves_correctly(self):
        """${var} where var=[] should return [], not the template string."""
        context = {"var": []}
        result = resolve("${var}", context)
        assert result == [], f"Expected [] but got {result!r}."


class TestResolveNoneInForEach:
    def test_none_field_from_function_step_not_stored_as_literal_string(self):
        """
        When a function step produces a dict with a None field, the next step
        should receive None (not the literal template string) for that field.
        """
        from llmflow.utils.data import create_json_dictionary

        context = {
            "items": [{"id": 1, "name": "Test"}],
        }

        step = {
            "name": "process_items",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [
                # Step 1: produces a dict with a None field
                {
                    "name": "build_data",
                    "type": "function",
                    "function": "tests.test_resolve_none_value.make_dict_with_none",
                    "inputs": {"name": "${item.name}"},
                    "outputs": "built",
                },
                # Step 2: reads the None field via dot-notation
                {
                    "name": "package",
                    "type": "function",
                    "function": "llmflow.utils.data.create_json_dictionary",
                    "inputs": {
                        "id": "${item.id}",
                        "optional_field": "${built.optional_field}",
                    },
                    "outputs": "packaged",
                    "append_to": "results",
                },
            ],
        }

        run_for_each_step(step, context, {})

        assert len(context["results"]) == 1
        result = context["results"][0]
        assert result["id"] == 1

        # The critical assertion: None field should be None, not the literal string
        assert result["optional_field"] is None, (
            f"optional_field should be None but got {result['optional_field']!r}. "
            "resolve() is conflating 'not found' with 'value is None'."
        )


def make_dict_with_none(name):
    """Test helper: returns a dict with a None field."""
    return {"name": name, "optional_field": None}
