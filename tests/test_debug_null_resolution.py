import tempfile

import yaml

from llmflow.runner import run_pipeline


def test_null_value_resolution():
    """Debug how null values are resolved"""

    pipeline = {
        "name": "debug-null-resolution",
        "variables": {"test_null": None, "test_string": "hello", "test_empty": []},
        "steps": [
            {
                "name": "debug_variables",
                "type": "function",
                "function": "tests.test_debug_null_resolution.debug_variable_types",
                "inputs": {
                    "null_var": "${test_null}",
                    "string_var": "${test_string}",
                    "empty_var": "${test_empty}",
                },
                "outputs": "debug_result",
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(pipeline, f)
        pipeline_path = f.name

    context = run_pipeline(pipeline_path)

    print("Debug results:")
    for key, value in context["debug_result"].items():
        print(f"  {key}: {value}")

    # The test will show us what's actually happening
    assert context["debug_result"]["string_resolved"] is True


def debug_variable_types(null_var, string_var, empty_var):
    """Debug what types we receive"""
    return {
        "null_var_repr": repr(null_var),
        "null_var_type": str(type(null_var)),
        "string_var_repr": repr(string_var),
        "string_var_type": str(type(string_var)),
        "empty_var_repr": repr(empty_var),
        "empty_var_type": str(type(empty_var)),
        "null_is_none": null_var is None,
        "null_is_unresolved": null_var == "${test_null}",
        "string_resolved": string_var == "hello",
        "empty_resolved": empty_var == [],
    }
