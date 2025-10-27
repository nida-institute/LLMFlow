import shutil
import tempfile

import pytest

from llmflow.runner import run_pipeline


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_pipeline_with_saveas(tmp_path):
    """Create a test pipeline that uses saveas"""
    pipeline_dir = tmp_path / "pipelines"
    pipeline_dir.mkdir()

    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    # Create a simple test pipeline with saveas
    pipeline_content = f"""
name: "Test Saveas Pipeline"
description: "Test pipeline to verify saveas functionality"

variables:
  test_value: "Hello, World!"
  output_path: "{output_dir}/test_output.txt"

llm_config:
  model: "gpt-4o"
  max_tokens: 1000
  temperature: 0.7

steps:
  - name: "identity_step"
    type: "function"
    function: "llmflow.utils.data.identity"
    inputs:
      value: "${{test_value}}"
    outputs:
      - result
    saveas: "${{output_path}}"
"""

    pipeline_file = pipeline_dir / "test_saveas.yaml"
    pipeline_file.write_text(pipeline_content)

    return {
        "pipeline_file": str(pipeline_file),
        "output_file": output_dir / "test_output.txt",
        "output_dir": output_dir,
    }


def test_saveas_writes_file(test_pipeline_with_saveas):
    """Test that saveas directive writes output to the specified file"""
    pipeline_file = test_pipeline_with_saveas["pipeline_file"]
    output_file = test_pipeline_with_saveas["output_file"]

    # Run the pipeline
    run_pipeline(pipeline_file)

    # Verify the file was created
    assert output_file.exists(), f"Output file was not created: {output_file}"

    # Verify the content
    content = output_file.read_text()
    assert "Hello, World!" in content, f"Expected content not found in {output_file}"


def test_saveas_with_template_substitution(tmp_path):
    """Test saveas with variable substitution in the filename"""
    pipeline_dir = tmp_path / "pipelines"
    pipeline_dir.mkdir()

    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    pipeline_content = f"""
name: "Test Saveas with Variables"
variables:
  file_prefix: "test_prefix"
  test_data: "Some test data"

llm_config:
  model: "gpt-4o"
  max_tokens: 1000
  temperature: 0.7

steps:
  - name: "save_with_variable_filename"
    type: "function"
    function: "llmflow.utils.data.identity"
    inputs:
      value: "${{test_data}}"
    outputs:
      - result
    saveas: "{output_dir}/${{file_prefix}}_output.md"
"""

    pipeline_file = pipeline_dir / "test_saveas_vars.yaml"
    pipeline_file.write_text(pipeline_content)

    # Run the pipeline
    run_pipeline(str(pipeline_file))

    # Verify the file was created with the correct name
    expected_file = output_dir / "test_prefix_output.md"
    assert expected_file.exists(), f"Output file was not created: {expected_file}"

    content = expected_file.read_text()
    assert "Some test data" in content


def test_saveas_creates_directories(tmp_path):
    """Test that saveas creates output directories if they don't exist"""
    pipeline_dir = tmp_path / "pipelines"
    pipeline_dir.mkdir()

    # Use a nested output path that doesn't exist yet
    output_file = tmp_path / "outputs" / "nested" / "deep" / "test.txt"

    pipeline_content = f"""
name: "Test Saveas Directory Creation"
variables:
  test_value: "Test content"

llm_config:
  model: "gpt-4o"
  max_tokens: 1000
  temperature: 0.7

steps:
  - name: "save_with_nested_path"
    type: "function"
    function: "llmflow.utils.data.identity"
    inputs:
      value: "${{test_value}}"
    outputs:
      - result
    saveas: "{output_file}"
"""

    pipeline_file = pipeline_dir / "test_saveas_dirs.yaml"
    pipeline_file.write_text(pipeline_content)

    # Run the pipeline
    run_pipeline(str(pipeline_file))

    # Verify the file and directories were created
    assert output_file.exists(), f"Output file was not created: {output_file}"
    assert output_file.parent.exists(), "Parent directories were not created"


def test_saveas_with_json_format(tmp_path):
    """Test saveas with JSON format"""
    pipeline_dir = tmp_path / "pipelines"
    pipeline_dir.mkdir()

    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    output_file = output_dir / "test.json"

    pipeline_content = f"""
name: "Test Saveas JSON Format"
variables:
  test_dict:
    key1: "value1"
    key2: "value2"

llm_config:
  model: "gpt-4o"
  max_tokens: 1000
  temperature: 0.7

steps:
  - name: "save_json"
    type: "function"
    function: "llmflow.utils.data.identity"
    inputs:
      value: "${{test_dict}}"
    outputs:
      - result
    saveas: "{output_file}"
    format: "json"
"""

    pipeline_file = pipeline_dir / "test_saveas_json.yaml"
    pipeline_file.write_text(pipeline_content)

    # Run the pipeline
    run_pipeline(str(pipeline_file))

    # Verify JSON file was created and is valid
    assert output_file.exists()
    import json

    with open(output_file) as f:
        data = json.load(f)
    assert data["key1"] == "value1"
    assert data["key2"] == "value2"
