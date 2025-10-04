import pytest
from llmflow.runner import run_pipeline
import tempfile
import yaml
import os

def test_data_flows_through_pipeline():
    """Verify data moves correctly through pipeline stages"""

    # Create a pipeline that tests data flow
    pipeline = {
        "name": "test-data-flow",
        "variables": {
            "initial_value": "start"
        },
        "steps": [
            # Step 1: Create initial data
            {
                "name": "create_list",
                "type": "function",
                "function": "tests.test_data_flow.create_test_list",
                "inputs": {"prefix": "${initial_value}"},
                "outputs": "items"
            },
            # Step 2: Transform each item
            {
                "name": "transform_items",
                "type": "for-each",
                "input": "${items}",
                "item_var": "item",
                "steps": [{
                    "name": "transform",
                    "type": "function",
                    "function": "tests.test_data_flow.transform_item",
                    "inputs": {"item": "${item}"},
                    "outputs": "transformed",
                    "append_to": "transformed_items"
                }]
            },
            # Step 3: Use transformed data
            {
                "name": "combine_results",
                "type": "function",
                "function": "tests.test_data_flow.combine_items",
                "inputs": {
                    "items": "${transformed_items}",
                    "separator": " | "
                },
                "outputs": "combined"
            },
            # Step 4: Reference earlier data
            {
                "name": "create_summary",
                "type": "function",
                "function": "tests.test_data_flow.create_summary",
                "inputs": {
                    "original": "${items}",
                    "transformed": "${transformed_items}",
                    "combined": "${combined}"
                },
                "outputs": "summary"
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(pipeline, f)
        pipeline_path = f.name

    # Run pipeline
    context = run_pipeline(pipeline_path)

    # Verify data flowed correctly through each stage

    # Step 1 output
    assert "items" in context
    assert context["items"] == ["start-1", "start-2", "start-3"]

    # Step 2 output (for-each with append)
    assert "transformed_items" in context
    assert len(context["transformed_items"]) == 3
    assert context["transformed_items"] == ["START-1!", "START-2!", "START-3!"]

    # Step 3 output
    assert "combined" in context
    assert context["combined"] == "START-1! | START-2! | START-3!"

    # Step 4 output (verifies access to all previous data)
    assert "summary" in context
    summary = context["summary"]
    assert "Original: 3 items" in summary
    assert "Transformed: 3 items" in summary
    assert "Combined length: 29" in summary

    # Verify initial variables are still accessible
    assert context.get("initial_value") == "start"

def create_test_list(prefix):
    """Create test data"""
    return [f"{prefix}-1", f"{prefix}-2", f"{prefix}-3"]

def transform_item(item):
    """Transform individual item"""
    return f"{item.upper()}!"

def combine_items(items, separator):
    """Combine items with separator"""
    return separator.join(items)

def create_summary(original, transformed, combined):
    """Create summary using data from multiple steps"""
    return (
        f"Original: {len(original)} items\n"
        f"Transformed: {len(transformed)} items\n"
        f"Combined length: {len(combined)}"
    )

def test_data_flow_with_nested_references():
    """Test complex data references including nested objects"""

    pipeline = {
        "name": "test-nested-data-flow",
        "steps": [
            {
                "name": "create_nested_data",
                "type": "function",
                "function": "tests.test_data_flow.create_nested_structure",
                "outputs": "data"
            },
            {
                "name": "access_nested",
                "type": "function",
                "function": "tests.test_data_flow.access_nested_data",
                "inputs": {
                    "user_name": "${data.user.name}",
                    "user_age": "${data.user.age}",
                    "first_item": "${data.items[0]}",
                    "last_item": "${data.items[-1]}"
                },
                "outputs": "extracted"
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(pipeline, f)
        pipeline_path = f.name

    context = run_pipeline(pipeline_path)

    # Verify nested data access worked
    assert context["extracted"]["user_name"] == "John"
    assert context["extracted"]["user_age"] == 30
    assert context["extracted"]["first_item"] == "apple"
    assert context["extracted"]["last_item"] == "cherry"

def create_nested_structure():
    """Create nested test structure"""
    return {
        "user": {"name": "John", "age": 30},
        "items": ["apple", "banana", "cherry"]
    }

def access_nested_data(user_name, user_age, first_item, last_item):
    """Verify nested data was accessed correctly"""
    return {
        "user_name": user_name,
        "user_age": user_age,
        "first_item": first_item,
        "last_item": last_item
    }

@pytest.mark.skip(reason="Pipeline runner does not support 'save' step type yet")
def test_data_flow_through_save_files():
    """Test data flow by checking saved outputs"""
    # Create a pipeline that saves intermediate results
    pipeline = {
        "name": "test-data-flow",
        "variables": {
            "initial_value": "start"
        },
        "steps": [
            {
                "name": "create_list",
                "type": "function",
                "function": "tests.test_data_flow.create_test_list",
                "inputs": {"prefix": "${initial_value}"},
                "outputs": "items"
            },
            {
                "name": "transform_items",
                "type": "for-each",
                "input": "${items}",
                "item_var": "item",
                "steps": [{
                    "name": "transform",
                    "type": "function",
                    "function": "tests.test_data_flow.transform_item",
                    "inputs": {"item": "${item}"},
                    "outputs": "transformed",
                    "append_to": "transformed_items"
                }]
            },
            {
                "name": "save_results",
                "type": "save",
                "input": "${transformed_items}",
                "filename": "transformed.json",
                "format": "json"
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_file = os.path.join(tmpdir, "pipeline.yaml")
        with open(pipeline_file, 'w') as f:
            yaml.dump(pipeline, f)

        # Run pipeline
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            from llmflow.runner import run_pipeline
            run_pipeline(pipeline_file)

            # Check output
            output_file = os.path.join("outputs", "transformed.json")
            assert os.path.exists(output_file)

            import json
            with open(output_file, 'r') as f:
                data = json.load(f)

            assert data == ["START-1!", "START-2!", "START-3!"]
        finally:
            os.chdir(old_cwd)