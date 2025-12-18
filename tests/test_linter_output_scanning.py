"""
Test that the linter's output scanning only checks the pipeline's local outputs directory,
not ancestor directories in the workspace.
"""
import pytest
import uuid
from pathlib import Path
from llmflow.utils.linter import lint_pipeline_full


def test_linter_does_not_scan_ancestor_outputs(tmp_path):
    """
    Test that linter only scans outputs in the pipeline's immediate context,
    not outputs directories in parent directories.

    This prevents the issue where running a pipeline from a subdirectory
    (e.g., tmp/pipelines/) would incorrectly validate output files from
    the main workspace outputs directory.
    """
    # Create workspace structure:
    # workspace/
    #   outputs/leaders_guide/UUID.md  (has errors - should NOT be checked)
    #   project/
    #     pipelines/test.yaml
    #     outputs/leaders_guide/  (empty - should be checked)

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create ancestor outputs with problematic file (UUID to avoid conflicts)
    ancestor_outputs = workspace / "outputs" / "leaders_guide"
    ancestor_outputs.mkdir(parents=True)
    unique_filename = f"{uuid.uuid4()}.md"
    bad_file = ancestor_outputs / unique_filename
    bad_file.write_text("# Test\n\n{{ unexpanded.placeholder }}\n\n---\n\n---\n\n")

    try:
        # Create project subdirectory with pipeline
        project_dir = workspace / "project"
        project_dir.mkdir()

        pipelines_dir = project_dir / "pipelines"
        pipelines_dir.mkdir()

        prompts_dir = project_dir / "prompts"
        prompts_dir.mkdir()

        # Create a prompt file with valid header
        prompt_file = prompts_dir / "test.gpt"
        prompt_file.write_text("---\nsystem: You are a test assistant.\nuser: Hello {{ name }}\n---\n")

        # Create a simple valid pipeline with absolute prompt path
        pipeline_file = pipelines_dir / "test.yaml"
        pipeline_file.write_text(f"""
name: "Test Pipeline"
variables:
  output_dir: "output"
  prompts_dir: "{prompts_dir}"
steps:
  - name: "test-step"
    type: "llm"
    prompt:
      file: "test.gpt"
      inputs:
        name: "world"
    outputs: result
""")

        # Create project's local outputs directory (empty - no errors)
        project_outputs = project_dir / "outputs" / "leaders_guide"
        project_outputs.mkdir(parents=True)

        # Run linter - should pass because it only checks project_dir/outputs,
        # not workspace/outputs
        result = lint_pipeline_full(str(pipeline_file))

        # Should be valid - the bad file in ancestor directory should be ignored
        assert result.valid, f"Expected valid, but got errors: {result.errors}"
    finally:
        # Clean up UUID file
        if bad_file.exists():
            bad_file.unlink()


def test_linter_scans_local_outputs_when_present(tmp_path):
    """
    Test that linter DOES scan outputs when they are in the correct location
    relative to the pipeline.
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    pipelines_dir = project_dir / "pipelines"
    pipelines_dir.mkdir()

    prompts_dir = project_dir / "prompts"
    prompts_dir.mkdir()

    # Create a prompt file with valid header
    prompt_file = prompts_dir / "test.gpt"
    prompt_file.write_text("---\nsystem: You are a test assistant.\nuser: Hello {{ name }}\n---\n")

    # Create pipeline with absolute prompt path
    pipeline_file = pipelines_dir / "test.yaml"
    pipeline_file.write_text(f"""
name: "Test Pipeline"
variables:
  output_dir: "output"
  prompts_dir: "{prompts_dir}"
steps:
  - name: "test-step"
    type: "llm"
    prompt:
      file: "test.gpt"
      inputs:
        name: "world"
    outputs: result
""")

    # Create local outputs with problematic file (UUID to avoid conflicts)
    local_outputs = project_dir / "outputs" / "leaders_guide"
    local_outputs.mkdir(parents=True)
    unique_filename = f"{uuid.uuid4()}.md"
    bad_file = local_outputs / unique_filename
    bad_file.write_text("# Test\n\n{{ unexpanded.placeholder }}\n\n---\n\n---\n\n")

    try:
        # Run linter - should FAIL because local outputs have errors
        result = lint_pipeline_full(str(pipeline_file))

        assert not result.valid, "Expected validation to fail due to local output errors"
        assert any("unexpanded.placeholder" in err for err in result.errors), \
            "Expected error about unexpanded placeholder"
        assert any("Empty sections" in err for err in result.errors), \
            "Expected error about empty sections"
    finally:
        # Clean up UUID file
        if bad_file.exists():
            bad_file.unlink()


def test_linter_skips_output_scanning_when_no_outputs_dir(tmp_path):
    """
    Test that linter gracefully skips output scanning when outputs directory
    doesn't exist.
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    pipelines_dir = project_dir / "pipelines"
    pipelines_dir.mkdir()

    prompts_dir = project_dir / "prompts"
    prompts_dir.mkdir()

    # Create a prompt file with valid header
    prompt_file = prompts_dir / "test.gpt"
    prompt_file.write_text("---\nsystem: You are a test assistant.\nuser: Hello {{ name }}\n---\n")

    # Create pipeline with absolute prompt path (no outputs directory)
    pipeline_file = pipelines_dir / "test.yaml"
    pipeline_file.write_text(f"""
name: "Test Pipeline"
variables:
  output_dir: "output"
  prompts_dir: "{prompts_dir}"
steps:
  - name: "test-step"
    type: "llm"
    prompt:
      file: "test.gpt"
      inputs:
        name: "world"
    outputs: result
""")

    # Run linter - should pass (no outputs to scan)
    result = lint_pipeline_full(str(pipeline_file))

    assert result.valid, f"Expected valid when no outputs directory exists, but got: {result.errors}"
