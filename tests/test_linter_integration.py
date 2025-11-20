"""Integration tests for full pipeline linting"""
from pathlib import Path
from llmflow.utils.linter import lint_pipeline_full

def test_typo_saveaas_caught_by_full_linter(tmp_path):
    """Integration test: full linter should catch 'saveaas' typo"""
    pipeline_file = tmp_path / "test-pipeline.yaml"
    pipeline_file.write_text("""
name: Test Pipeline
steps:
  - name: bad-step
    type: xslt
    saveaas:  # This is a typo!
      path: output.xml
    inputs:
      xml_string: "<root/>"
""")

    result = lint_pipeline_full(str(pipeline_file))
    assert not result.valid, "Pipeline with typo should fail validation"
    assert any("saveaas" in err for err in result.errors), "Should mention the typo"
    assert any("saveas" in err for err in result.errors), "Should suggest correction"


def test_typo_ouput_caught_by_full_linter(tmp_path):
    """Integration test: full linter should catch 'ouput' typo"""
    # Create a valid prompt file
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    prompt_file = prompts_dir / "test.gpt"
    prompt_file.write_text("""
<!--
prompt:
  requires: []
-->
---
system: Test system prompt
---
Test user prompt
""")

    pipeline_file = tmp_path / "test-pipeline.yaml"
    pipeline_file.write_text(f"""
name: Test Pipeline
variables:
  prompts_dir: {prompts_dir}
steps:
  - name: bad-step
    type: llm
    prompt:
      file: test.gpt
      inputs: {{}}
    ouput:  # This is a typo!
      - result
""")

    result = lint_pipeline_full(str(pipeline_file))
    assert not result.valid, "Pipeline with typo should fail validation"
    assert any("ouput" in err for err in result.errors), f"Should mention the typo, got: {result.errors}"
    assert any("outputs" in err for err in result.errors), "Should suggest correction"


def test_valid_pipeline_passes_full_linter(tmp_path):
    """Integration test: valid pipeline should pass"""
    pipeline_file = tmp_path / "valid-pipeline.yaml"
    pipeline_file.write_text("""
name: Valid Pipeline
steps:
  - name: good-step
    type: xslt
    saveas:  # Correct spelling!
      path: output.xml
    inputs:
      xml_string: "<root/>"
    outputs:
      - result
""")

    result = lint_pipeline_full(str(pipeline_file))
    # Should pass keyword validation (might fail on other things like missing files)
    if not result.valid:
        # Check that no errors are about unknown keywords
        assert not any("unknown keyword" in err for err in result.errors), \
            f"Should not have keyword errors, got: {result.errors}"


def test_nested_steps_typos_caught(tmp_path):
    """Integration test: typos in nested for-each steps should be caught"""
    # Create a valid prompt file
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    prompt_file = prompts_dir / "test.gpt"
    prompt_file.write_text("""
<!--
prompt:
  requires: []
-->
---
system: Test system prompt
---
Test user prompt
""")

    pipeline_file = tmp_path / "nested-pipeline.yaml"
    pipeline_file.write_text(f"""
name: Nested Pipeline
variables:
  prompts_dir: {prompts_dir}
steps:
  - name: loop
    type: for-each
    input: items
    item_var: item
    steps:
      - name: nested-step
        type: llm
        prompt:
          file: test.gpt
          inputs: {{}}
        intputs:  # Typo in nested step!
          data: "${{item}}"
""")

    result = lint_pipeline_full(str(pipeline_file))
    assert not result.valid, "Pipeline with typo in nested step should fail"
    assert any("intputs" in err for err in result.errors), f"Should catch typo in nested step, got: {result.errors}"
    assert any("inputs" in err for err in result.errors), "Should suggest correction"


def test_multiple_typos_all_reported(tmp_path):
    """Integration test: multiple typos should all be reported"""
    # Create a valid prompt file
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    prompt_file = prompts_dir / "test.gpt"
    prompt_file.write_text("""
<!--
prompt:
  requires: []
-->
---
system: Test system prompt
---
Test user prompt
""")

    pipeline_file = tmp_path / "multi-typo-pipeline.yaml"
    pipeline_file.write_text(f"""
name: Multiple Typos
variables:
  prompts_dir: {prompts_dir}
steps:
  - name: step1
    type: llm
    prompt:
      file: test.gpt
      inputs: {{}}
    saveaas:
      path: output1.xml
  - name: step2
    type: xslt
    intputs:
      data: foo
    ouput:
      - result
""")

    result = lint_pipeline_full(str(pipeline_file))
    assert not result.valid, "Pipeline with multiple typos should fail"
    assert len([e for e in result.errors if "unknown keyword" in e]) >= 3, \
        f"Should report all 3 typos (saveaas, intputs, ouput), got: {result.errors}"