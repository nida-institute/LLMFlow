import pytest
import tempfile
import yaml
from pathlib import Path

@pytest.fixture
def full_list():
    return ["item1", "item2", "item3"]

@pytest.fixture
def first_item():
    return "item1"

@pytest.fixture
def last_item():
    return "item3"

@pytest.fixture
def second_item():
    return "item2"

@pytest.fixture
def current_scene():
    return {"citation": "Psalm 23:1", "text": "The LORD is my shepherd", "id": "psalm_23_1"}

@pytest.fixture
def joshfrost_list():
    return ["joshfrost_item1", "joshfrost_item2"]

@pytest.fixture
def bodies_list():
    return ["body1", "body2"]

@pytest.fixture
def last_joshfrost():
    return "last_joshfrost_item"

@pytest.fixture
def last_bodies():
    return "last_body_item"

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_context():
    """Provide a sample context for testing"""
    return {
        "passage": "Psalm 23",
        "passage_info": {
            "filename_prefix": "19023001-19023176",
            "book": "Psalms",
            "chapter": 23
        },
        "scene_list": [
            {"Scene number": 1, "Citation": "v1-3"},
            {"Scene number": 2, "Citation": "v4-6"}
        ],
        "outputs_dir": "outputs"
    }

@pytest.fixture
def sample_pipeline_config():
    """Provide a sample pipeline configuration"""
    return {
        "pipeline": {
            "name": "test_pipeline",
            "variables": {
                "prompts_dir": "prompts",
                "output_dir": "outputs"
            },
            "llm_config": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "steps": []
        }
    }

# Helper functions for mocking
def mock_function(input):
    """Mock function for testing"""
    return f"processed_{input}"

def transform_function(item, prefix):
    """Mock transform function for testing"""
    return f"{prefix}_{item}"

def create_test_verses():
    """Create test verses for pipeline testing"""
    return [
        {"citation": "Psalm 23:1", "number": 1, "text": "The LORD is my shepherd"},
        {"citation": "Psalm 23:2", "number": 2, "text": "He makes me lie down in green pastures"},
        {"citation": "Psalm 23:3", "number": 3, "text": "He restores my soul"},
        {"citation": "Psalm 23:4", "number": 4, "text": "Even though I walk through the valley"}
    ]

def mock_llm_response(verse, citation):
    """Mock LLM response for testing"""
    return {
        "citation": citation,
        "scene_title": f"Scene for {citation}",
        "content": f"Generated content for {verse.get('text', 'unknown')}"
    }

# MISSING FUNCTIONS FOR test_data_flow.py:
def create_test_list(prefix):
    """Create test list for data flow testing"""
    return [f"{prefix}-1", f"{prefix}-2", f"{prefix}-3"]

def transform_item(item):
    """Transform item for testing"""
    return f"{item.upper()}!"

def combine_items(items, separator):
    """Combine items with separator"""
    return separator.join(items)

def create_summary(original, transformed, combined):
    """Create summary of transformation"""
    return f"Original: {len(original)} items\nTransformed: {len(transformed)} items\nCombined length: {len(combined)}"