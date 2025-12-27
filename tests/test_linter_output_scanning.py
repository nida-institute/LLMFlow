"""
CRITICAL REGRESSION TEST: Linter must NEVER validate output files.

This test file prevents a recurring bug where the linter incorrectly validates
output files from previous pipeline runs instead of only validating the pipeline
configuration itself.

HISTORY:
- This regression has occurred TWICE
- The linter should ONLY validate:
  * Pipeline YAML structure
  * Step keywords
  * Variable references
  * Template files and variables
  * Prompt files

- The linter should NEVER validate:
  * Output files from previous runs
  * Content in outputs/ directories

If these tests fail, the linter has regressed to incorrectly scanning outputs.
"""
import pytest
from pathlib import Path
from llmflow.utils.linter import lint_pipeline_full


def test_linter_ignores_broken_output_files_in_workspace(tmp_path):
    """
    CRITICAL: Linter must NOT fail when output files from previous runs contain errors.

    This is the main regression test. If this fails, someone re-introduced
    output file scanning to the linter.
    """
    # Create workspace structure
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    pipelines_dir = project_dir / "pipelines"
    pipelines_dir.mkdir()

    prompts_dir = project_dir / "prompts"
    prompts_dir.mkdir()

    # Create outputs directory with BADLY BROKEN files from "previous runs"
    outputs_dir = project_dir / "outputs"
    leaders_guide_dir = outputs_dir / "leaders_guide"
    leaders_guide_dir.mkdir(parents=True)

    joshfrost_dir = outputs_dir / "joshfrost"
    joshfrost_dir.mkdir(parents=True)

    exegetical_dir = outputs_dir / "exegetical"
    exegetical_dir.mkdir(parents=True)

    # Create files with every type of error the old linter used to catch:
    # 1. Unexpanded template placeholders
    bad_file_1 = leaders_guide_dir / "19021001-19021999_leaders_guide.md"
    bad_file_1.write_text("""
# Leader's Guide

{{ scene.Citation }}
{{ scene.Title }}
{{ unexpanded.variable }}
{{ another.broken.placeholder }}
    """)

    # 2. Empty sections around horizontal rules
    bad_file_2 = leaders_guide_dir / "42002021-42002040_leaders_guide.md"
    bad_file_2.write_text("""
# Section 1

---

---

Empty sections everywhere!

---

---
    """)

    # 3. Both problems combined
    bad_file_3 = joshfrost_dir / "01022001-01022019_joshfrost.md"
    bad_file_3.write_text("""
{{ broken.placeholder }}

---

---

{{ more.broken.stuff }}
    """)

    # Create a valid prompt file
    prompt_file = prompts_dir / "test.gpt"
    prompt_file.write_text("---\nsystem: You are helpful.\nuser: Hello {{ name }}\n---\n")

    # Create a valid pipeline
    pipeline_file = pipelines_dir / "test.yaml"
    pipeline_file.write_text(f"""
name: "Test Pipeline"
variables:
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

    # Run linter - MUST pass despite broken output files
    result = lint_pipeline_full(str(pipeline_file))

    # If this assertion fails, the linter is incorrectly scanning output files
    assert result.valid, (
        f"REGRESSION DETECTED: Linter failed due to output files from previous runs.\n"
        f"The linter should ONLY validate pipeline configuration, not output files.\n"
        f"Errors reported: {result.errors}\n"
        f"This is the bug that has regressed twice - DO NOT scan outputs!"
    )


def test_linter_ignores_output_files_in_parent_directories(tmp_path):
    """
    CRITICAL: Linter must not scan output directories in parent/ancestor paths.

    Even if someone re-adds output scanning, it must not check parent directories.
    """
    # Create workspace with nested structure
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create broken outputs at workspace level
    workspace_outputs = workspace / "outputs" / "leaders_guide"
    workspace_outputs.mkdir(parents=True)

    bad_workspace_file = workspace_outputs / "broken.md"
    bad_workspace_file.write_text("{{ completely.broken }}\n\n---\n\n---\n")

    # Create project subdirectory
    project_dir = workspace / "subproject" / "nested"
    project_dir.mkdir(parents=True)

    pipelines_dir = project_dir / "pipelines"
    pipelines_dir.mkdir()

    prompts_dir = project_dir / "prompts"
    prompts_dir.mkdir()

    # Create broken outputs at project level too
    project_outputs = project_dir / "outputs" / "leaders_guide"
    project_outputs.mkdir(parents=True)

    bad_project_file = project_outputs / "also_broken.md"
    bad_project_file.write_text("{{ still.broken }}\n\n---\n\n---\n")

    # Create valid pipeline
    prompt_file = prompts_dir / "test.gpt"
    prompt_file.write_text("---\nsystem: Test\nuser: Hi {{ x }}\n---\n")

    pipeline_file = pipelines_dir / "test.yaml"
    pipeline_file.write_text(f"""
name: "Test Pipeline"
variables:
  prompts_dir: "{prompts_dir}"
steps:
  - name: "step1"
    type: "llm"
    prompt:
      file: "test.gpt"
      inputs:
        x: "hello"
    outputs: result
""")

    # Run linter - must pass
    result = lint_pipeline_full(str(pipeline_file))

    assert result.valid, (
        f"REGRESSION: Linter scanned output files in workspace or project directories.\n"
        f"Errors: {result.errors}\n"
        f"The linter must NEVER scan output files."
    )


def test_linter_only_validates_pipeline_configuration(tmp_path):
    """
    Positive test: Verify linter validates what it SHOULD validate.

    This ensures we didn't break valid linter functionality when removing
    output file scanning.
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    pipelines_dir = project_dir / "pipelines"
    pipelines_dir.mkdir()

    prompts_dir = project_dir / "prompts"
    prompts_dir.mkdir()

    # Create valid prompt
    prompt_file = prompts_dir / "valid.gpt"
    prompt_file.write_text("---\nsystem: Assistant\nuser: Hello {{ name }}\n---\n")

    # Create valid pipeline
    pipeline_file = pipelines_dir / "valid.yaml"
    pipeline_file.write_text(f"""
name: "Valid Pipeline"
variables:
  prompts_dir: "{prompts_dir}"
steps:
  - name: "step1"
    type: "llm"
    prompt:
      file: "valid.gpt"
      inputs:
        name: "user"
    outputs: greeting
""")

    # This should pass
    result = lint_pipeline_full(str(pipeline_file))
    assert result.valid, f"Valid pipeline should pass linting: {result.errors}"


def test_linter_still_validates_pipeline_structure(tmp_path):
    """
    Positive test: Verify linter still catches basic pipeline structure errors.

    This ensures we didn't break basic linter functionality when removing
    output file scanning.
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    pipelines_dir = project_dir / "pipelines"
    pipelines_dir.mkdir()

    # Create invalid pipeline (missing required 'name' field)
    pipeline_file = pipelines_dir / "broken.yaml"
    pipeline_file.write_text("""
steps:
  - name: "step1"
    type: "llm"
    outputs: result
""")

    # This should fail due to missing pipeline name
    result = lint_pipeline_full(str(pipeline_file))
    assert not result.valid, "Pipeline with missing 'name' field should fail linting"
