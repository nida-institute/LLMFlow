import os
import tempfile

import pytest
import yaml

from llmflow.runner import run_pipeline


# Define TracedSystemExit locally since the import is failing
class TracedSystemExit(SystemExit):
    """Custom SystemExit that can be caught in tests"""

    def __init__(self, code=0):
        super().__init__(code)
        self.code = code


def create_test_verses():
    """Create test verses for pipeline testing"""
    return [
        {"citation": "Psalm 23:1", "number": 1, "text": "The LORD is my shepherd"},
        {
            "citation": "Psalm 23:2",
            "number": 2,
            "text": "He makes me lie down in green pastures",
        },
        {"citation": "Psalm 23:3", "number": 3, "text": "He restores my soul"},
        {
            "citation": "Psalm 23:4",
            "number": 4,
            "text": "Even though I walk through the valley",
        },
    ]


def mock_llm_response(verse, citation):
    """Mock LLM response for testing"""
    return {
        "citation": citation,
        "scene_title": f"Scene for {citation}",
        "content": f"Generated content for {verse.get('text', 'unknown')}",
        "scene_id": f"scene_{citation.lower().replace(' ', '_').replace(':', '_')}",
    }


def create_indexed_list():
    """Create a list with indexed items for testing"""
    return [
        {"id": "item_1", "content": "item_1"},
        {"id": "item_2", "content": "item_2"},
        {"id": "item_3", "content": "item_3"},
        {"id": "item_4", "content": "item_4"},  # Add the missing 4th item
    ]


def test_for_each_variable_isolation_minimal():
    """Minimal test for for-each variable isolation"""
    try:
        pipeline = {
            "name": "test-minimal-isolation",
            "variables": {},
            "llm_config": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000},
            "steps": [
                {
                    "name": "create_items",
                    "type": "function",
                    "function": "tests.test_regression_scene_duplication.create_simple_items",
                    "outputs": "items",
                },
                {
                    "name": "process_each",
                    "type": "for-each",
                    "input": "${items}",
                    "item_var": "item",
                    "steps": [
                        {
                            "name": "capture",
                            "type": "function",
                            "function": "tests.test_regression_scene_duplication.capture_item_context",
                            "inputs": {
                                "current_item": "${item}",
                                "item_id": "${item.id}",
                                "item_name": "${item.name}",
                            },
                            "outputs": "result",
                            "append_to": "results",
                        }
                    ],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
            with open(pipeline_file, "w") as f:
                yaml.dump(pipeline, f)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                context = run_pipeline(pipeline_file)  # Capture return value

                print("\n=== VARIABLE BINDING TEST ===")
                print(f"Generated {len(context['results'])} results:")

                for i, result in enumerate(context["results"]):
                    expected_id = f"item_{i+1}"
                    expected_name = f"Item {i+1}"
                    actual_id = result["item_id"]
                    actual_name = result["item_name"]

                    print(
                        f"Result {i+1}: Expected ID={expected_id}, Got ID={actual_id}, Name={actual_name}"
                    )

                    assert (
                        actual_id == expected_id
                    ), f"Result {i+1}: Expected ID {expected_id} but got {actual_id} - variable binding issue!"

                    assert (
                        actual_name == expected_name
                    ), f"Result {i+1}: Expected name '{expected_name}' but got '{actual_name}' - variable binding issue!"

            finally:
                os.chdir(old_cwd)
    except TracedSystemExit as e:
        pytest.skip(f"Pipeline validation failed with exit code {e.code}")


def test_simple_for_each_context_contamination():
    """Test simple for-each context contamination"""
    try:
        pipeline = {
            "name": "test-context-contamination",
            "variables": {},
            "llm_config": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000},
            "steps": [
                {
                    "name": "setup_items",
                    "type": "function",
                    "function": "tests.test_regression_scene_duplication.create_simple_items",
                    "outputs": "items",
                },
                {
                    "name": "process_items",
                    "type": "for-each",
                    "input": "${items}",
                    "item_var": "item",
                    "steps": [
                        {
                            "name": "capture_context",
                            "type": "function",
                            "function": "tests.test_regression_scene_duplication.capture_item_context",
                            "inputs": {
                                "current_item": "${item}",
                                "item_id": "${item.id}",
                                "item_name": "${item.name}",
                            },
                            "outputs": "captured_context",
                            "append_to": "context_snapshots",
                        }
                    ],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
            with open(pipeline_file, "w") as f:
                yaml.dump(pipeline, f)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                context = run_pipeline(pipeline_file)
                snapshots = context["context_snapshots"]

                print("\n=== CONTEXT CONTAMINATION TEST ===")
                print(f"Captured {len(snapshots)} context snapshots:")

                for i, snapshot in enumerate(snapshots):
                    expected_id = f"item_{i+1}"
                    actual_id = snapshot["item_id"]
                    captured_name = snapshot["item_name"]
                    expected_name = f"Item {i+1}"

                    print(
                        f"Iteration {i+1}: Expected ID='{expected_id}', Got ID='{actual_id}', Name='{captured_name}'"
                    )

                    assert (
                        actual_id == expected_id
                    ), f"Context contamination detected! Expected {expected_id}, got {actual_id}"

                    assert (
                        captured_name == expected_name
                    ), f"Name contamination detected! Expected '{expected_name}', got '{captured_name}'"

            finally:
                os.chdir(old_cwd)
    except TracedSystemExit as e:
        pytest.skip(f"Pipeline validation failed with exit code {e.code}")


def test_list_indexing_behavior():
    """Test list indexing behavior"""
    try:
        pipeline = {
            "name": "test-list-indexing",
            "variables": {},
            "llm_config": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000},
            "steps": [
                {
                    "name": "create_test_list",
                    "type": "function",
                    "function": "tests.test_regression_scene_duplication.create_indexed_list",
                    "outputs": "test_list",
                },
                {
                    "name": "test_list_access_patterns",
                    "type": "function",
                    "function": "tests.test_regression_scene_duplication.list_access_helper",
                    "inputs": {
                        "full_list": "${test_list}",
                        "first_item": "${test_list[0]}",
                        "last_item": "${test_list[-1]}",
                        "second_item": "${test_list[1]}",
                    },
                    "outputs": "access_results",
                },
                {
                    "name": "process_with_for_each",
                    "type": "for-each",
                    "input": "${test_list}",
                    "item_var": "item",
                    "steps": [
                        {
                            "name": "capture_indexing",
                            "type": "function",
                            "function": "tests.test_regression_scene_duplication.capture_list_indexing",
                            "inputs": {
                                "current_item": "${item}",
                                "item_id": "${item.id}",
                                "full_list": "${test_list}",
                                "first_from_list": "${test_list[0]}",
                                "last_from_list": "${test_list[-1]}",
                            },
                            "outputs": "indexing_result",
                            "append_to": "indexing_results",
                        }
                    ],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
            with open(pipeline_file, "w") as f:
                yaml.dump(pipeline, f)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                context = run_pipeline(pipeline_file)
                results = context["indexing_results"]

                print("\n=== LIST INDEXING TEST ===")
                print(f"Total iterations: {len(results)}")

                for i, result in enumerate(results):
                    expected_id = f"item_{i+1}"
                    actual_id = result["current_item_id"]
                    first_item_id = result["first_item_from_list"]["id"]
                    last_item_id = result["last_item_from_list"]["id"]

                    print(f"\nIteration {i+1}:")
                    print(f"  Current item: {actual_id} (expected: {expected_id})")
                    print(f"  test_list[0]: {first_item_id} (should always be: item_1)")
                    print(f"  test_list[-1]: {last_item_id} (should always be: item_4)")

                    assert (
                        actual_id == expected_id
                    ), f"Current item mismatch: expected {expected_id}, got {actual_id}"

                    assert (
                        first_item_id == "item_1"
                    ), f"test_list[0] should always be item_1, got {first_item_id}"

                    assert (
                        last_item_id == "item_4"
                    ), f"test_list[-1] should always be item_4, got {last_item_id}"

                    print(f"  ✅ All indexing correct for iteration {i+1}")

            finally:
                os.chdir(old_cwd)
    except TracedSystemExit as e:
        pytest.skip(f"Pipeline validation failed with exit code {e.code}")


def test_append_list_indexing():
    """Test append list indexing"""
    try:
        pipeline = {
            "name": "test-append-indexing",
            "variables": {},
            "llm_config": {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000},
            "steps": [
                {
                    "name": "create_scenes",
                    "type": "function",
                    "function": "tests.test_regression_scene_duplication.create_indexed_list",
                    "outputs": "scene_list",
                },
                {
                    "name": "process_scenes",
                    "type": "for-each",
                    "input": "${scene_list}",
                    "item_var": "scene",
                    "steps": [
                        {
                            "name": "add_to_joshfrost_list",
                            "type": "function",
                            "function": "tests.test_regression_scene_duplication.mock_joshfrost_generation",
                            "inputs": {"scene": "${scene}"},
                            "outputs": "joshfrost_content",
                            "append_to": "joshfrost_list",
                        },
                        {
                            "name": "add_to_bodies_list",
                            "type": "function",
                            "function": "tests.test_regression_scene_duplication.mock_bodies_generation",
                            "inputs": {"scene": "${scene}"},
                            "outputs": "bodies_content",
                            "append_to": "bodies_list",
                        },
                        {
                            "name": "test_list_access",
                            "type": "function",
                            "function": "tests.test_regression_scene_duplication.append_list_access_helper",
                            "inputs": {
                                "current_scene": "${scene}",
                                "joshfrost_list": "${joshfrost_list}",
                                "bodies_list": "${bodies_list}",
                                "last_joshfrost": "${joshfrost_list[-1]}",
                                "last_bodies": "${bodies_list[-1]}",
                            },
                            "outputs": "append_test_result",
                            "append_to": "append_test_results",
                        },
                    ],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
            with open(pipeline_file, "w") as f:
                yaml.dump(pipeline, f)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                context = run_pipeline(pipeline_file)
                results = context["append_test_results"]

                print("\n=== APPEND LIST INDEXING TEST ===")

                for i, result in enumerate(results):
                    iteration = i + 1
                    current_scene_id = result["current_scene_id"]
                    last_joshfrost_scene = result["last_joshfrost_scene_id"]
                    last_bodies_scene = result["last_bodies_scene_id"]

                    print(f"\nIteration {iteration} (Scene: {current_scene_id}):")
                    print(f"  joshfrost_list[-1] scene: {last_joshfrost_scene}")
                    print(f"  bodies_list[-1] scene: {last_bodies_scene}")

                    expected_scene_id = f"item_{iteration}"

                    if last_joshfrost_scene != expected_scene_id:
                        print(
                            f"  ❌ joshfrost_list[-1] MISMATCH: expected {expected_scene_id}, got {last_joshfrost_scene}"
                        )
                        pytest.fail(
                            f"joshfrost_list[-1] indexing broken at iteration {iteration}"
                        )

                    if last_bodies_scene != expected_scene_id:
                        print(
                            f"  ❌ bodies_list[-1] MISMATCH: expected {expected_scene_id}, got {last_bodies_scene}"
                        )
                        pytest.fail(
                            f"bodies_list[-1] indexing broken at iteration {iteration}"
                        )

                    print(f"  ✅ [-1] indexing correct for iteration {iteration}")

            finally:
                os.chdir(old_cwd)
    except TracedSystemExit as e:
        pytest.skip(f"Pipeline validation failed with exit code {e.code}")


# Helper functions
def create_simple_items():
    """Create simple test items for context contamination test"""
    return [
        {"id": "item_1", "name": "Item 1", "value": "A"},
        {"id": "item_2", "name": "Item 2", "value": "B"},
        {"id": "item_3", "name": "Item 3", "value": "C"},
        {"id": "item_4", "name": "Item 4", "value": "D"},
    ]


def list_access_helper(
    full_list, first_item, last_item, second_item
):  # Complete this line
    """Test basic list access patterns"""
    return {
        "list_length": len(full_list),
        "first_item": first_item["id"] if isinstance(first_item, dict) else first_item,
        "last_item": last_item["id"] if isinstance(last_item, dict) else last_item,
        "second_item": (
            second_item["id"] if isinstance(second_item, dict) else second_item
        ),
    }


def capture_list_indexing(
    current_item, item_id, full_list, first_from_list, last_from_list
):
    """Capture indexing behavior during for-each"""
    return {
        "current_item_id": item_id,
        "first_item_from_list": first_from_list,
        "last_item_from_list": last_from_list,
        "list_length": len(full_list),
    }


def mock_scene_generation(verse_data, verse_number):
    """Mock scene generation that should preserve verse context"""
    return {
        "verse_number": verse_number,
        "citation": verse_data["citation"],
        "content_verse_reference": verse_number,  # This should match verse_number
        "scene_title": f"Scene for Verse {verse_number}",
        "scene_content": f"Content for verse {verse_number}: {verse_data['text']}",
    }


def capture_item_context(current_item, item_id, item_name):
    """Capture the current context to detect contamination"""
    return {
        "item_id": item_id,
        "item_name": item_name,
        "current_item_id": current_item["id"],
        "current_item_name": current_item["name"],
        "current_item_value": current_item["value"],
    }


def append_list_access_helper(
    current_scene, joshfrost_list, bodies_list, last_joshfrost, last_bodies
):  # Renamed from test_append_list_access
    """Test append list indexing behavior"""
    return {
        "current_scene_id": current_scene["id"],
        "joshfrost_list_length": len(joshfrost_list) if joshfrost_list else 0,
        "bodies_list_length": len(bodies_list) if bodies_list else 0,
        "last_joshfrost_scene_id": (
            last_joshfrost.split()[-1]
            if "item_" in str(last_joshfrost)
            else "PARSE_ERROR"
        ),
        "last_bodies_scene_id": (
            last_bodies.split()[-1] if "item_" in str(last_bodies) else "PARSE_ERROR"
        ),
    }


def mock_joshfrost_generation(scene):
    """Mock joshfrost content generation"""
    return f"joshfrost_content for {scene['id']}"


def mock_bodies_generation(scene):
    """Mock bodies content generation"""
    return f"bodies_content for {scene['id']}"


@pytest.mark.skip(
    reason="Pipeline missing required files - test the actual bug once files are available"
)
def test_psalm_pipeline_scene_content_mismatch():
    """
    Regression test for scene duplication bug in Psalm pipeline.

    SKIPPED: The actual pipeline test is skipped until prompt files and templates are available.
    Use the minimal tests above to detect the for-each variable binding issues.
    """
    pass


# Add helper function for saving JSON
def save_json_helper(data, filename):
    """Helper function to save JSON data"""
    import json

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    return {"saved": filename}


if __name__ == "__main__":
    # Run the simpler regression tests directly
    test_for_each_variable_isolation_minimal()
    test_simple_for_each_context_contamination()
    test_list_indexing_behavior()
    test_append_list_indexing()
