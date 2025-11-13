import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from llmflow.runner import run_pipeline


@pytest.fixture
def temp_prompt_file(tmp_path):
    """Create a temporary prompt file"""
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_file = prompt_dir / "test.gpt"
    prompt_file.write_text("Test prompt")
    return str(prompt_dir)


def test_run_pipeline_exits_on_after_exit(tmp_path, temp_prompt_file):
    """Test that pipeline exits when a step has 'after: exit'"""
    pipeline_content = """
name: test-pipeline
steps:
  - name: step1
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result1
  - name: step2
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
    after: exit
  - name: step3
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result3
"""
    pipeline_file = tmp_path / "test-pipeline.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response"):
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            assert "result1" in context
            assert "result2" in context
            assert "result3" not in context


def test_run_pipeline_continues_on_after_continue(tmp_path, temp_prompt_file):
    """Test that pipeline continues to next step when 'after: continue'"""
    pipeline_content = """
name: test-pipeline
steps:
  - name: step1
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result1
    after: continue
  - name: step2
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
"""
    pipeline_file = tmp_path / "continue-pipeline.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response"):
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            assert "result1" in context
            assert "result2" in context


def test_run_pipeline_for_each_with_after_exit(tmp_path, temp_prompt_file):
    """Test that for-each exits entire loop when nested step has 'after: exit'"""
    pipeline_content = """
name: test-pipeline
variables:
  items:
    - value: 1
    - value: 2
    - value: 3
steps:
  - name: process-items
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: nested-step
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result
        after: exit
"""
    pipeline_file = tmp_path / "foreach-exit-pipeline.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Should only process first item due to 'after: exit'
            assert mock_llm.call_count == 1


def test_run_pipeline_for_each_with_after_continue(tmp_path, temp_prompt_file):
    """Test that for-each skips remaining steps in current iteration with 'after: continue'"""
    pipeline_content = """
name: test-pipeline
variables:
  items:
    - value: 1
    - value: 2
    - value: 3
steps:
  - name: process-items
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: nested-step1
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result1
        after: continue
      - name: nested-step2
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result2
"""
    pipeline_file = tmp_path / "foreach-continue-pipeline.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Should process nested-step1 for all 3 items, but skip nested-step2
            assert mock_llm.call_count == 3


def test_run_pipeline_if_with_after_exit(tmp_path, temp_prompt_file):
    """Test that pipeline exits when nested step in if block has 'after: exit'"""
    pipeline_content = """
name: test-pipeline
variables:
  condition: true
steps:
  - name: conditional
    type: if
    condition: "${condition}"
    steps:
      - name: nested-step1
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result1
        after: exit
      - name: nested-step2
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result2
  - name: after-if
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result3
"""
    pipeline_file = tmp_path / "if-exit-pipeline.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response"):
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Should run nested-step1, then exit entire pipeline
            assert "result1" in context
            assert "result2" not in context
            assert "result3" not in context


def test_run_pipeline_if_with_after_continue(tmp_path, temp_prompt_file):
    """Test that if block breaks to next step when nested step has 'after: continue'"""
    pipeline_content = """
name: test-pipeline
variables:
  condition: true
steps:
  - name: conditional
    type: if
    condition: "${condition}"
    steps:
      - name: nested-step1
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result1
        after: continue
      - name: nested-step2
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result2
  - name: after-if
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result3
"""
    pipeline_file = tmp_path / "if-continue-pipeline.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response"):
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Should run nested-step1, skip nested-step2, then run after-if
            assert "result1" in context
            assert "result2" not in context
            assert "result3" in context


def test_run_pipeline_no_after_runs_all_steps(tmp_path, temp_prompt_file):
    """Test that pipeline runs all steps when no 'after' directive is present"""
    pipeline_content = """
name: test-pipeline
steps:
  - name: step1
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result1
  - name: step2
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
  - name: step3
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result3
"""
    pipeline_file = tmp_path / "no-after-pipeline.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response"):
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            assert "result1" in context
            assert "result2" in context
            assert "result3" in context


def test_nested_for_each_with_after_exit(tmp_path, temp_prompt_file):
    """Test that nested for-each propagates exit signal correctly"""
    pipeline_content = """
name: test-pipeline
variables:
  outer_items:
    - id: 1
    - id: 2
  inner_items:
    - value: a
    - value: b
steps:
  - name: outer-loop
    type: for-each
    input: "${outer_items}"
    item_var: outer
    steps:
      - name: inner-loop
        type: for-each
        input: "${inner_items}"
        item_var: inner
        steps:
          - name: nested-step
            type: llm
            model: gpt-4o
            prompt:
              file: test.gpt
            outputs:
              - result
            after: exit
"""
    pipeline_file = tmp_path / "nested-foreach-exit.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Should only process first inner item of first outer item
            assert mock_llm.call_count == 1


def test_for_each_with_exit_after_loop(tmp_path, temp_prompt_file):
    """Test that exit in for-each prevents subsequent pipeline steps"""
    pipeline_content = """
name: test-pipeline
variables:
  items:
    - value: 1
steps:
  - name: process-items
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: nested-step
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result1
        append_to: all_results
        after: exit
  - name: after-loop
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
"""
    pipeline_file = tmp_path / "foreach-then-exit.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response"):
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Should run nested-step and append to parent context, but not after-loop
            assert "all_results" in context
            assert len(context["all_results"]) == 1
            assert "result2" not in context


def test_function_step_with_after_exit(tmp_path):
    """Test that function steps respect 'after: exit'"""
    # Create a simple helper function that accepts keyword args
    helper_file = tmp_path / "helpers.py"
    helper_file.write_text("""
def get_basename(path):
    import os
    return os.path.basename(path)
""")

    import sys
    sys.path.insert(0, str(tmp_path))

    try:
        pipeline_content = """
name: test-pipeline
steps:
  - name: func1
    type: function
    function: helpers.get_basename
    inputs:
      path: "/path/to/file.txt"
    outputs:
      - result1
    after: exit
  - name: func2
    type: function
    function: helpers.get_basename
    inputs:
      path: "/other/path.txt"
    outputs:
      - result2
"""
        pipeline_file = tmp_path / "function-exit.yaml"
        pipeline_file.write_text(pipeline_content)

        context = run_pipeline(str(pipeline_file), skip_lint=True)

        assert "result1" in context
        assert context["result1"] == "file.txt"
        assert "result2" not in context
    finally:
        sys.path.remove(str(tmp_path))


def test_mixed_steps_with_after_directives(tmp_path, temp_prompt_file):
    """Test complex pipeline with mixed step types and after directives"""
    pipeline_content = """
name: test-pipeline
variables:
  items:
    - value: 1
    - value: 2
steps:
  - name: step1
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result1
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: nested-step
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - loop_result
        after: continue
      - name: should-not-run
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - unreachable
  - name: step2
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
"""
    pipeline_file = tmp_path / "mixed-steps.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # step1 + (nested-step * 2) + step2 = 4 calls
            assert mock_llm.call_count == 4
            assert "result1" in context
            assert "result2" in context
            assert "unreachable" not in context


def test_if_false_condition_skips_steps(tmp_path, temp_prompt_file):
    """Test that if block with false condition skips all nested steps"""
    pipeline_content = """
name: test-pipeline
variables:
  condition: false
steps:
  - name: conditional
    type: if
    condition: "${condition}"
    steps:
      - name: nested-step
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result1
        after: exit
  - name: after-if
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
"""
    pipeline_file = tmp_path / "if-false.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Should skip nested-step, but run after-if
            assert mock_llm.call_count == 1
            assert "result1" not in context
            assert "result2" in context


def test_multiple_after_exit_in_sequence(tmp_path, temp_prompt_file):
    """Test that first 'after: exit' stops entire pipeline"""
    pipeline_content = """
name: test-pipeline
steps:
  - name: step1
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result1
    after: exit
  - name: step2
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
    after: exit
  - name: step3
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result3
"""
    pipeline_file = tmp_path / "multiple-exits.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Should only run step1
            assert mock_llm.call_count == 1
            assert "result1" in context
            assert "result2" not in context
            assert "result3" not in context


def test_for_each_exit_propagates_to_parent(tmp_path, temp_prompt_file):
    """Test that exit in nested for-each propagates to parent pipeline"""
    pipeline_content = """
name: test-pipeline
variables:
  items: [1, 2]
steps:
  - name: step1
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result1
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: nested
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - loop_result
        after: exit
  - name: step2
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
"""
    pipeline_file = tmp_path / "foreach-exit-parent.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # step1 + first iteration only = 2 calls
            assert mock_llm.call_count == 2
            assert "result1" in context
            assert "result2" not in context


def test_nested_if_with_exit(tmp_path, temp_prompt_file):
    """Test that exit in nested if blocks propagates correctly"""
    pipeline_content = """
name: test-pipeline
variables:
  cond1: true
  cond2: true
steps:
  - name: outer-if
    type: if
    condition: "${cond1}"
    steps:
      - name: inner-if
        type: if
        condition: "${cond2}"
        steps:
          - name: nested-step
            type: llm
            model: gpt-4o
            prompt:
              file: test.gpt
            outputs:
              - result1
            after: exit
      - name: after-inner
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result2
  - name: after-outer
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result3
"""
    pipeline_file = tmp_path / "nested-if-exit.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked response") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Only nested-step should run
            assert mock_llm.call_count == 1
            assert "result1" in context
            assert "result2" not in context
            assert "result3" not in context


def test_for_each_with_append_to_and_continue(tmp_path, temp_prompt_file):
    """Test that continue in for-each still appends results to parent context"""
    pipeline_content = """
name: test-pipeline
variables:
  items: [1, 2, 3]
steps:
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: step1
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result
        append_to: collected
        after: continue
      - name: step2
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - unreachable
"""
    pipeline_file = tmp_path / "foreach-append-continue.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test prompt"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # step1 runs 3 times, step2 never runs due to continue
            assert mock_llm.call_count == 3
            assert "collected" in context
            assert len(context["collected"]) == 3
            assert "unreachable" not in context


def test_save_step_with_exit(tmp_path):
    """Test that save steps respect 'after: exit'"""
    output_dir = tmp_path / "outputs"
    pipeline_content = f"""
name: test-pipeline
variables:
  output_dir: {str(output_dir)}
steps:
  - name: save1
    type: save
    path: ${{output_dir}}/file1.txt
    content: "Content 1"
    after: exit
  - name: save2
    type: save
    path: ${{output_dir}}/file2.txt
    content: "Content 2"
"""
    pipeline_file = tmp_path / "save-exit.yaml"
    pipeline_file.write_text(pipeline_content)

    context = run_pipeline(str(pipeline_file), skip_lint=True)

    assert (output_dir / "file1.txt").exists()
    assert not (output_dir / "file2.txt").exists()


def test_save_step_with_continue_in_loop(tmp_path):
    """Test that save steps respect 'after: continue' in loops"""
    output_dir = tmp_path / "outputs"
    pipeline_content = f"""
name: test-pipeline
variables:
  items: [1, 2, 3]
  output_dir: {str(output_dir)}
steps:
  - name: loop
    type: for-each
    input: "${{items}}"
    item_var: item
    steps:
      - name: save1
        type: save
        path: ${{output_dir}}/file_${{item}}.txt
        content: "Content ${{item}}"
        after: continue
      - name: save2
        type: save
        path: ${{output_dir}}/extra_${{item}}.txt
        content: "Extra"
"""
    pipeline_file = tmp_path / "save-continue-loop.yaml"
    pipeline_file.write_text(pipeline_content)

    context = run_pipeline(str(pipeline_file), skip_lint=True)

    # First saves should exist
    assert (output_dir / "file_1.txt").exists()
    assert (output_dir / "file_2.txt").exists()
    assert (output_dir / "file_3.txt").exists()

    # Second saves should not exist due to continue
    assert not (output_dir / "extra_1.txt").exists()
    assert not (output_dir / "extra_2.txt").exists()
    assert not (output_dir / "extra_3.txt").exists()


def test_for_each_with_nested_save_and_llm(tmp_path, temp_prompt_file):
    """Test for-each with both save and llm steps"""
    output_dir = tmp_path / "outputs"
    pipeline_content = f"""
name: test-pipeline
variables:
  items: [1, 2, 3]
  output_dir: {str(output_dir)}
steps:
  - name: loop
    type: for-each
    input: "${{items}}"
    item_var: item
    steps:
      - name: process
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result
        append_to: results
      - name: save
        type: save
        path: ${{output_dir}}/item_${{item}}.txt
        content: "Processed ${{item}}"
"""
    pipeline_file = tmp_path / "foreach-save-llm.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="processed") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Process"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            assert mock_llm.call_count == 3
            assert "results" in context
            assert len(context["results"]) == 3

            # Check all files were created
            assert (output_dir / "item_1.txt").exists()
            assert (output_dir / "item_2.txt").exists()
            assert (output_dir / "item_3.txt").exists()


def test_exit_in_first_iteration_of_loop(tmp_path, temp_prompt_file):
    """Test that exit in first iteration stops the entire loop"""
    pipeline_content = """
name: test-pipeline
variables:
  items: [1, 2, 3, 4, 5]
steps:
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: process
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result
        append_to: results
        after: exit
"""
    pipeline_file = tmp_path / "exit-first-iteration.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="processed") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Process"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Should only process first item
            assert mock_llm.call_count == 1
            assert "results" in context
            assert len(context["results"]) == 1


def test_continue_in_first_step_of_loop_iteration(tmp_path, temp_prompt_file):
    """Test continue as first step in loop iteration"""
    pipeline_content = """
name: test-pipeline
variables:
  items: [1, 2, 3]
steps:
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: skip-step
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - skipped
        after: continue
      - name: never-runs
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result
"""
    pipeline_file = tmp_path / "continue-first-step.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="skipped") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # skip-step runs 3 times, never-runs doesn't run
            assert mock_llm.call_count == 3
            assert "result" not in context


def test_nested_if_both_conditions_false(tmp_path, temp_prompt_file):
    """Test nested if where outer condition is false"""
    pipeline_content = """
name: test-pipeline
variables:
  outer_cond: false
  inner_cond: true
steps:
  - name: outer-if
    type: if
    condition: "${outer_cond}"
    steps:
      - name: inner-if
        type: if
        condition: "${inner_cond}"
        steps:
          - name: nested-step
            type: llm
            model: gpt-4o
            prompt:
              file: test.gpt
            outputs:
              - result1
  - name: after-all
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
"""
    pipeline_file = tmp_path / "nested-if-outer-false.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Only after-all should run
            assert mock_llm.call_count == 1
            assert "result1" not in context
            assert "result2" in context


def test_for_each_with_empty_list(tmp_path, temp_prompt_file):
    """Test for-each with empty list"""
    pipeline_content = """
name: test-pipeline
variables:
  items: []
steps:
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: process
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result
  - name: after-loop
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - final_result
"""
    pipeline_file = tmp_path / "foreach-empty-list.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Only after-loop should run
            assert mock_llm.call_count == 1
            assert "result" not in context
            assert "final_result" in context


def test_exit_and_continue_in_same_pipeline(tmp_path, temp_prompt_file):
    """Test pipeline with both exit and continue directives"""
    pipeline_content = """
name: test-pipeline
variables:
  items1: [1, 2, 3]
  items2: [a, b]
steps:
  - name: loop1
    type: for-each
    input: "${items1}"
    item_var: item
    steps:
      - name: step1
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - r1
        append_to: list1
        after: continue
      - name: step2
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - r2
  - name: loop2
    type: for-each
    input: "${items2}"
    item_var: item
    steps:
      - name: step3
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - r3
        after: exit
"""
    pipeline_file = tmp_path / "exit-and-continue-mixed.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # loop1: step1 runs 3 times (continue prevents step2)
            # loop2: step3 runs once then exits
            # Total: 4 calls
            assert mock_llm.call_count == 4
            assert "list1" in context
            assert len(context["list1"]) == 3
            assert "r2" not in context


def test_if_with_explicit_true_condition(tmp_path, temp_prompt_file):
    """Test if condition with explicit true value (not variable)"""
    pipeline_content = """
name: test-pipeline
steps:
  - name: conditional
    type: if
    condition: "True"
    steps:
      - name: nested-step
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result1
        after: exit
  - name: after-if
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
"""
    pipeline_file = tmp_path / "if-explicit-true.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            assert mock_llm.call_count == 1
            assert "result1" in context
            assert "result2" not in context


def test_if_with_explicit_false_condition(tmp_path, temp_prompt_file):
    """Test if condition with explicit false value"""
    pipeline_content = """
name: test-pipeline
steps:
  - name: conditional
    type: if
    condition: "False"
    steps:
      - name: nested-step
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result1
  - name: after-if
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
"""
    pipeline_file = tmp_path / "if-explicit-false.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            assert mock_llm.call_count == 1
            assert "result1" not in context
            assert "result2" in context


def test_exit_in_save_step_stops_subsequent_saves(tmp_path):
    """Test that exit in save step prevents subsequent saves"""
    output_dir = tmp_path / "outputs"
    pipeline_content = f"""
name: test-pipeline
variables:
  output_dir: {str(output_dir)}
steps:
  - name: save1
    type: save
    path: ${{output_dir}}/file1.txt
    content: "First"
  - name: save2
    type: save
    path: ${{output_dir}}/file2.txt
    content: "Second"
    after: exit
  - name: save3
    type: save
    path: ${{output_dir}}/file3.txt
    content: "Third"
"""
    pipeline_file = tmp_path / "save-exit-sequence.yaml"
    pipeline_file.write_text(pipeline_content)

    context = run_pipeline(str(pipeline_file), skip_lint=True)

    assert (output_dir / "file1.txt").exists()
    assert (output_dir / "file2.txt").exists()
    assert not (output_dir / "file3.txt").exists()


def test_continue_with_multiple_outputs(tmp_path, temp_prompt_file):
    """Test that continue preserves multiple outputs in append_to"""
    pipeline_content = """
name: test-pipeline
variables:
  items: [1, 2, 3]
steps:
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: step1
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result1
          - result2
        append_to: collected
        after: continue
      - name: step2
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - unreachable
"""
    pipeline_file = tmp_path / "continue-multiple-outputs.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            assert mock_llm.call_count == 3
            assert "collected" in context
            assert len(context["collected"]) == 3


def test_exit_after_successful_search(tmp_path, temp_prompt_file):
    """Test using exit to stop after finding a match"""
    pipeline_content = """
name: test-pipeline
variables:
  candidates: [apple, banana, cherry, date]
  target: cherry
steps:
  - name: search
    type: for-each
    input: "${candidates}"
    item_var: candidate
    steps:
      - name: check
        type: if
        condition: '"${candidate}" == "${target}"'
        steps:
          - name: found
            type: llm
            model: gpt-4o
            prompt:
              file: test.gpt
            outputs:
              - match
            after: exit
      - name: keep-searching
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - searched
        append_to: searched_items
"""
    pipeline_file = tmp_path / "exit-after-match.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # keep-searching for apple, banana (2)
            # found for cherry (1)
            # Total: 3 calls
            assert mock_llm.call_count == 3
            assert "match" in context
            assert "searched_items" in context
            assert len(context["searched_items"]) == 2


def test_save_and_llm_mixed_with_exit(tmp_path, temp_prompt_file):
    """Test mixed save and llm steps with exit"""
    output_dir = tmp_path / "outputs"
    pipeline_content = f"""
name: test-pipeline
variables:
  output_dir: {str(output_dir)}
steps:
  - name: step1
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result1
  - name: save1
    type: save
    path: ${{output_dir}}/step1.txt
    content: "After step1"
  - name: step2
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - result2
    after: exit
  - name: save2
    type: save
    path: ${{output_dir}}/step2.txt
    content: "After step2"
"""
    pipeline_file = tmp_path / "mixed-save-llm-exit.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="test") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            assert mock_llm.call_count == 2
            assert (output_dir / "step1.txt").exists()
            assert not (output_dir / "step2.txt").exists()
            assert "result1" in context
            assert "result2" in context


def test_for_each_with_index_variable(tmp_path, temp_prompt_file):
    """Test for-each accessing loop index"""
    pipeline_content = """
name: test-pipeline
variables:
  items: [a, b, c]
steps:
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: process
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result
        append_to: results
        after: continue
      - name: unreachable
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - skip
"""
    pipeline_file = tmp_path / "foreach-with-index.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="processed") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Process ${item}"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            assert mock_llm.call_count == 3
            assert "results" in context
            assert len(context["results"]) == 3
            assert "skip" not in context


def test_deeply_nested_exit_propagation(tmp_path, temp_prompt_file):
    """Test exit propagates through 3 levels of nesting"""
    pipeline_content = """
name: test-pipeline
variables:
  level1: [1]
  level2: [a]
  level3: [x]
steps:
  - name: outer
    type: for-each
    input: "${level1}"
    item_var: l1
    steps:
      - name: middle
        type: for-each
        input: "${level2}"
        item_var: l2
        steps:
          - name: inner
            type: for-each
            input: "${level3}"
            item_var: l3
            steps:
              - name: deepest
                type: llm
                model: gpt-4o
                prompt:
                  file: test.gpt
                outputs:
                  - result
                after: exit
  - name: after-all
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - final
"""
    pipeline_file = tmp_path / "deeply-nested-exit.yaml"
    pipeline_file.write_text(pipeline_content)

    with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
        with patch("llmflow.runner.Path.read_text", return_value="Test"):
            context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

            # Only deepest runs once
            assert mock_llm.call_count == 1
            assert "result" in context
            assert "final" not in context