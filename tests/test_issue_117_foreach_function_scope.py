"""
Regression test for GitHub issue #117:
Template variables referencing function step outputs within the same for-each
iteration are stored as literal strings instead of being resolved.

Pattern that fails:
  Step 1: function step → outputs: item_enriched (a dict)
  Step 2: function step tries ${item_enriched.field} → gets literal string
"""
import pytest


def test_function_step_output_accessible_in_same_iteration():
    """
    Within a for-each loop, a function step's output should be accessible
    via dot-notation in subsequent steps of the same iteration.
    """
    from llmflow.runner import run_for_each_step
    from llmflow.utils.data import create_json_dictionary

    context = {
        "items": [
            {"id": 1, "name": "Item One"},
            {"id": 2, "name": "Item Two"},
        ]
    }

    step = {
        "name": "process_items",
        "type": "for-each",
        "in": "${items}",
        "for": "item",
        "steps": [
            # Step 1: create enriched dict
            {
                "name": "enrich_item",
                "type": "function",
                "function": "llmflow.utils.data.create_json_dictionary",
                "inputs": {
                    "enriched_field": "Enriched value for ${item.name}",
                },
                "outputs": "item_enriched",
            },
            # Step 2: try to use step 1's output via dot-notation
            {
                "name": "package_item",
                "type": "function",
                "function": "llmflow.utils.data.create_json_dictionary",
                "inputs": {
                    "id": "${item.id}",
                    "name": "${item.name}",
                    "enriched_field": "${item_enriched.enriched_field}",
                },
                "outputs": "packaged_item",
                "append_to": "results",
            },
        ],
    }

    run_for_each_step(step, context, {})

    assert "results" in context, "results accumulator should exist"
    assert len(context["results"]) == 2

    for i, result in enumerate(context["results"]):
        item_name = ["Item One", "Item Two"][i]
        item_id = i + 1

        assert result["id"] == item_id, f"id should be {item_id}, got {result['id']!r}"
        assert result["name"] == item_name, f"name should be {item_name!r}, got {result['name']!r}"

        # This is the critical assertion — must NOT be a literal template string
        assert result["enriched_field"] != "${item_enriched.enriched_field}", (
            f"enriched_field was stored as a literal template string, not resolved! "
            f"Got: {result['enriched_field']!r}"
        )
        expected_enriched = f"Enriched value for {item_name}"
        assert result["enriched_field"] == expected_enriched, (
            f"enriched_field should be {expected_enriched!r}, got {result['enriched_field']!r}"
        )
