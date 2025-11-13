import pytest
from unittest.mock import patch

from llmflow.runner import run_for_each_step, run_pipeline


class TestCriticalForEachContext:
    def test_nested_context_isolation(self):
        """Ensure for-each iterations don't contaminate each other"""
        context = {"items": ["A", "B", "C"], "global_value": "unchanged"}

        rule = {
            "name": "test_isolation",
            "type": "for-each",
            "input": "${items}",
            "item_var": "item",
            "steps": [
                {
                    "name": "mutate_context",
                    "type": "function",
                    "function": "tests.test_critical_foreach_context.mutate_context",
                    "inputs": {"item": "${item}"},
                    "outputs": "result",
                    "append_to": "results",
                }
            ],
        }

        run_for_each_step(rule, context, {"variables": {}})

        # Critical: global context not mutated
        assert context["global_value"] == "unchanged"

        # Critical: all results collected
        assert len(context["results"]) == 3

        # Critical: no contamination between iterations
        assert context["results"] == ["A-processed", "B-processed", "C-processed"]

    def test_deepcopy_prevents_list_sharing(self):
        """Regression test: deepcopy prevents the shallow copy bug where lists were shared"""
        context = {"shared_list": ["initial"]}

        rule = {
            "name": "test_deepcopy",
            "type": "for-each",
            "input": ["item1", "item2", "item3"],
            "item_var": "item",
            "steps": [
                {
                    "name": "append_to_list",
                    "type": "function",
                    "function": "tests.test_critical_foreach_context.append_to_shared_list",
                    "inputs": {"item": "${item}", "shared_list": "${shared_list}"},
                    "outputs": "result",
                }
            ],
        }

        run_for_each_step(rule, context, {})

        # Critical: The shared_list in parent context should NOT be modified by iterations
        # Each iteration gets a deepcopy, so modifications stay isolated
        assert context["shared_list"] == ["initial"], "Parent context list should not be mutated"

    def test_for_each_parent_context_isolation(self, tmp_path, temp_prompt_file):
        """Test that for-each iterations don't mutate parent context variables"""
        pipeline_content = """
name: test-pipeline
variables:
  shared_list: [initial]
  items: [1, 2, 3]
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
"""
        pipeline_file = tmp_path / "foreach-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked"):
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # Parent context shared_list should remain unchanged
                assert context["shared_list"] == ["initial"]

    def test_nested_for_each_parent_list_isolation(self, tmp_path, temp_prompt_file):
        """Test that nested for-each loops don't mutate parent lists"""
        pipeline_content = """
name: test-pipeline
variables:
  parent_list: [original]
  outer: [1, 2]
  inner: [a, b]
steps:
  - name: outer-loop
    type: for-each
    input: "${outer}"
    item_var: o
    steps:
      - name: inner-loop
        type: for-each
        input: "${inner}"
        item_var: i
        steps:
          - name: process
            type: llm
            model: gpt-4o
            prompt:
              file: test.gpt
            outputs:
              - result
"""
        pipeline_file = tmp_path / "nested-foreach-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # Verify parent_list wasn't mutated
                assert context["parent_list"] == ["original"]
                # All iterations should complete
                assert mock_llm.call_count == 4

    def test_for_each_dict_modification_isolation(self, tmp_path, temp_prompt_file):
        """Test that for-each iterations don't mutate parent dict variables"""
        pipeline_content = """
name: test-pipeline
variables:
  shared_dict:
    key: original_value
  items: [1, 2, 3]
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
"""
        pipeline_file = tmp_path / "foreach-dict-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked"):
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # Parent dict should remain unchanged
                assert context["shared_dict"]["key"] == "original_value"

    def test_for_each_with_function_mutating_context(self, tmp_path):
        """Test that function steps in for-each don't mutate parent context"""
        helper_file = tmp_path / "mutation_helpers.py"
        helper_file.write_text("""
def try_mutate_list(item, shared_list):
    # This should work on a copy, not the original
    shared_list.append(item)
    return f"processed_{item}"
""")

        import sys
        sys.path.insert(0, str(tmp_path))

        try:
            pipeline_content = """
name: test-pipeline
variables:
  shared_list: [initial]
  items: [1, 2, 3]
steps:
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: mutate-attempt
        type: function
        function: mutation_helpers.try_mutate_list
        inputs:
          item: "${item}"
          shared_list: "${shared_list}"
        outputs:
          - result
        append_to: results
"""
            pipeline_file = tmp_path / "function-mutation-isolation.yaml"
            pipeline_file.write_text(pipeline_content)

            context = run_pipeline(str(pipeline_file), skip_lint=True)

            # Parent shared_list should NOT be mutated by function calls
            assert context["shared_list"] == ["initial"], \
                "Function in for-each should not mutate parent context list"
            assert "results" in context
            assert len(context["results"]) == 3
        finally:
            sys.path.remove(str(tmp_path))

    def test_for_each_append_to_does_propagate(self, tmp_path, temp_prompt_file):
        """Test that append_to DOES propagate to parent (expected behavior)"""
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
      - name: process
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - result
        append_to: collected
"""
        pipeline_file = tmp_path / "foreach-append-propagates.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # append_to should work and propagate to parent
                assert "collected" in context
                assert len(context["collected"]) == 3
                assert mock_llm.call_count == 3

    def test_for_each_variable_shadowing_isolation(self, tmp_path, temp_prompt_file):
        """Test that item_var shadowing doesn't leak between iterations"""
        pipeline_content = """
name: test-pipeline
variables:
  item: parent_item_value
  items: [1, 2, 3]
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
  - name: after-loop
    type: llm
    model: gpt-4o
    prompt:
      file: test.gpt
    outputs:
      - final
"""
        pipeline_file = tmp_path / "foreach-variable-shadowing.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
            with patch("llmflow.runner.Path.read_text", return_value="Test ${item}"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # After loop completes, original 'item' should be restored
                assert context["item"] == "parent_item_value"
                assert mock_llm.call_count == 4  # 3 iterations + 1 after-loop

    def test_for_each_multiple_lists_no_cross_contamination(self, tmp_path, temp_prompt_file):
        """Test that multiple list variables don't cross-contaminate"""
        pipeline_content = """
name: test-pipeline
variables:
  list_a: [a1, a2]
  list_b: [b1, b2]
  items: [1, 2]
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
"""
        pipeline_file = tmp_path / "foreach-multi-list-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked"):
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # Both lists should remain unchanged
                assert context["list_a"] == ["a1", "a2"]
                assert context["list_b"] == ["b1", "b2"]

    def test_for_each_with_nested_objects_isolation(self, tmp_path, temp_prompt_file):
        """Test that nested objects in context are properly isolated"""
        pipeline_content = """
name: test-pipeline
variables:
  config:
    nested:
      deep_list: [original]
  items: [1, 2, 3]
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
"""
        pipeline_file = tmp_path / "foreach-nested-object-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked"):
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # Deep nested values should remain unchanged
                assert context["config"]["nested"]["deep_list"] == ["original"]

    def test_for_each_outputs_without_append_to_dont_mutate_parent(self, tmp_path, temp_prompt_file):
        """Test that regular outputs in for-each don't accumulate in parent"""
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
      - name: process
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - iteration_result
"""
        pipeline_file = tmp_path / "foreach-outputs-no-append.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # iteration_result should only contain last iteration's value
                # OR not be in parent context at all (depending on implementation)
                assert mock_llm.call_count == 3
                if "iteration_result" in context:
                    # If present, should be single value, not list
                    assert not isinstance(context["iteration_result"], list) or \
                           len(context["iteration_result"]) == 1

    def test_for_each_with_if_context_isolation(self, tmp_path, temp_prompt_file):
        """Test context isolation with for-each containing if blocks"""
        pipeline_content = """
name: test-pipeline
variables:
  shared_state: unchanged
  items: [1, 2, 3]
steps:
  - name: loop
    type: for-each
    input: "${items}"
    item_var: item
    steps:
      - name: check
        type: if
        condition: "${item} > 1"
        steps:
          - name: process
            type: llm
            model: gpt-4o
            prompt:
              file: test.gpt
            outputs:
              - result
            append_to: results
"""
        pipeline_file = tmp_path / "foreach-if-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # shared_state should remain unchanged
                assert context["shared_state"] == "unchanged"
                # Only items 2 and 3 should be processed
                assert "results" in context
                assert len(context["results"]) == 2
                assert mock_llm.call_count == 2

    def test_for_each_parallel_loops_no_interference(self, tmp_path, temp_prompt_file):
        """Test that sequential for-each loops don't interfere with each other"""
        pipeline_content = """
name: test-pipeline
variables:
  state_a: [initial_a]
  state_b: [initial_b]
  items1: [1, 2]
  items2: [a, b]
steps:
  - name: loop1
    type: for-each
    input: "${items1}"
    item_var: item
    steps:
      - name: process1
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - r1
        append_to: results1
  - name: loop2
    type: for-each
    input: "${items2}"
    item_var: item
    steps:
      - name: process2
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - r2
        append_to: results2
"""
        pipeline_file = tmp_path / "foreach-parallel-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # Original state variables should be unchanged
                assert context["state_a"] == ["initial_a"]
                assert context["state_b"] == ["initial_b"]
                # Both loops should complete independently
                assert len(context["results1"]) == 2
                assert len(context["results2"]) == 2
                assert mock_llm.call_count == 4

    def test_for_each_with_save_and_context_isolation(self, tmp_path):
        """Test that save steps in for-each don't mutate parent context"""
        output_dir = tmp_path / "outputs"
        pipeline_content = f"""
name: test-pipeline
variables:
  metadata: {{status: initial}}
  items: [1, 2, 3]
  output_dir: {str(output_dir)}
steps:
  - name: loop
    type: for-each
    input: "${{items}}"
    item_var: item
    steps:
      - name: save
        type: save
        path: ${{output_dir}}/item_${{item}}.txt
        content: "Item ${{item}}"
"""
        pipeline_file = tmp_path / "foreach-save-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        context = run_pipeline(str(pipeline_file), skip_lint=True)

        # metadata should remain unchanged
        assert context["metadata"]["status"] == "initial"
        # All files should be created
        assert (output_dir / "item_1.txt").exists()
        assert (output_dir / "item_2.txt").exists()
        assert (output_dir / "item_3.txt").exists()

    def test_for_each_iteration_counter_doesnt_leak(self, tmp_path, temp_prompt_file):
        """Test that iteration state doesn't leak between loops"""
        pipeline_content = """
name: test-pipeline
variables:
  items1: [a, b]
  items2: [1, 2, 3]
steps:
  - name: loop1
    type: for-each
    input: "${items1}"
    item_var: letter
    steps:
      - name: process1
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - r1
        append_to: list1
  - name: loop2
    type: for-each
    input: "${items2}"
    item_var: number
    steps:
      - name: process2
        type: llm
        model: gpt-4o
        prompt:
          file: test.gpt
        outputs:
          - r2
        append_to: list2
"""
        pipeline_file = tmp_path / "foreach-counter-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # Each loop should run independently with correct counts
                assert len(context["list1"]) == 2
                assert len(context["list2"]) == 3
                assert mock_llm.call_count == 5

    def test_for_each_with_pre_existing_append_target(self, tmp_path, temp_prompt_file):
        """Test append_to behavior when target list already exists"""
        pipeline_content = """
name: test-pipeline
variables:
  results: [pre-existing]
  items: [1, 2, 3]
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
"""
        pipeline_file = tmp_path / "foreach-append-pre-existing.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="new") as mock_llm:
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # Should append to existing list, not replace it
                assert "results" in context
                # Original + 3 new items = 4 total
                assert len(context["results"]) == 4
                assert context["results"][0] == "pre-existing"
                assert mock_llm.call_count == 3

    def test_deeply_nested_for_each_context_isolation(self, tmp_path, temp_prompt_file):
        """Test context isolation in 3-level nested for-each"""
        pipeline_content = """
name: test-pipeline
variables:
  global_state: untouched
  level1: [1]
  level2: [a]
  level3: [x, y]
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
                append_to: deep_results
"""
        pipeline_file = tmp_path / "foreach-3level-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked") as mock_llm:
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # global_state should remain unchanged
                assert context["global_state"] == "untouched"
                # Should process all iterations: 1 * 1 * 2 = 2
                assert "deep_results" in context
                assert len(context["deep_results"]) == 2
                assert mock_llm.call_count == 2

    def test_for_each_with_complex_data_structures(self, tmp_path, temp_prompt_file):
        """Test that complex data structures in context are properly isolated"""
        pipeline_content = """
name: test-pipeline
variables:
  complex:
    lists: [[1, 2], [3, 4]]
    dicts: [{a: 1}, {b: 2}]
    nested:
      deep:
        deeper: [original]
  items: [1, 2]
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
"""
        pipeline_file = tmp_path / "foreach-complex-isolation.yaml"
        pipeline_file.write_text(pipeline_content)

        with patch("llmflow.runner.call_llm", return_value="mocked"):
            with patch("llmflow.runner.Path.read_text", return_value="Test"):
                context = run_pipeline(str(pipeline_file), vars={"prompts_dir": temp_prompt_file}, skip_lint=True)

                # All complex structures should remain unchanged
                assert context["complex"]["lists"] == [[1, 2], [3, 4]]
                assert context["complex"]["dicts"] == [{"a": 1}, {"b": 2}]
                assert context["complex"]["nested"]["deep"]["deeper"] == ["original"]


def mutate_context(item):
    return f"{item}-processed"


def append_to_shared_list(item, shared_list):
    """This function modifies the list - testing if deepcopy isolates it"""
    shared_list.append(item)
    return f"appended {item}"
