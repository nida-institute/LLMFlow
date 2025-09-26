import pytest
import tempfile
import shutil
from pathlib import Path
import yaml

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

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

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return "This is a mock LLM response"