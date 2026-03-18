def pytest_configure(config):
    config.addinivalue_line("markers", "critical: mark test as critical")

import pytest
from llmflow.runner import run_pipeline, run_for_each_step

@pytest.fixture
def temp_prompt_file(tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("This is a temporary prompt file.")
    return prompt_file

def append_to_shared_list(item, shared_list):
    shared_list.append(item)
    return f"processed_{item}"

class TestCriticalForEachContext:
    def test_deepcopy_prevents_list_sharing(self):
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
        assert context["shared_list"] == ["initial"]

    def test_for_each_with_function_mutating_context(self, tmp_path):
        helper_file = tmp_path / "mutation_helpers.py"
        helper_file.write_text("""
def try_mutate_list(item, shared_list):
    shared_list.append(item)
    return f"processed_{item}"
""")
        import sys
        sys.path.insert(0, str(tmp_path))
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
        assert context["shared_list"] == ["initial"]