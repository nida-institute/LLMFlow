import pytest
from pathlib import Path

@pytest.fixture
def temp_prompt_file(tmp_path):
    """Create a temporary prompt file for testing"""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(exist_ok=True)

    prompt_file = prompts_dir / "test.gpt"
    prompt_file.write_text("Test prompt: ${item}")

    return str(prompts_dir)