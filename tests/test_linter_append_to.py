import pytest
import tempfile
from pathlib import Path
import yaml
from llmflow.utils.linter import lint_pipeline_contracts, collect_all_steps
import io
import sys

class TestLinterAppendTo:
    """Test that linter catches append_to without outputs errors"""

    def test_linter_catches_append_to_without_outputs(self, caplog):
        """Test that linter catches append_to without outputs field"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create pipeline config
            pipeline_config = {
                "name": "test-pipeline",
                "variables": {"prompts_dir": str(tmpdir / "prompts")},
                "linter_config": {
                    "enabled": True,
                    "treat_warnings_as_errors": True
                },
                "steps": [
                    {
                        "name": "generate_content",
                        "type": "llm",
                        "prompt": {
                            "file": "test.md",
                            "inputs": {"text": "test"}
                        },
                        "append_to": "content_list"  # Missing outputs field
                    }
                ]
            }

            # Write pipeline file
            pipeline_path = tmpdir / "pipeline.yaml"
            with open(pipeline_path, 'w') as f:
                yaml.dump({"pipeline": pipeline_config}, f)

            # Create prompts directory and file
            prompts_dir = tmpdir / "prompts"
            prompts_dir.mkdir(exist_ok=True)
            prompt_file = prompts_dir / "test.md"
            prompt_file.write_text("""<!--
prompt:
  requires:
    - text
  format: markdown
-->
Test prompt {{text}}""")

            with pytest.raises(SystemExit):
                lint_pipeline_contracts(str(pipeline_path))

            # Check caplog instead of captured stdout
            log_output = caplog.text
            assert "generate_content" in log_output
            assert "append_to: content_list" in log_output

    def test_linter_passes_with_outputs_and_append_to(self):
        """Test that linter passes when both outputs and append_to are present"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            pipeline_config = {
                "name": "test-pipeline",
                "variables": {"prompts_dir": str(tmpdir / "prompts")},
                "linter_config": {
                    "enabled": True,
                    "treat_warnings_as_errors": True
                },
                "steps": [
                    {
                        "name": "generate_content",
                        "type": "llm",
                        "prompt": {
                            "file": "test.md",
                            "inputs": {"text": "test"}
                        },
                        "outputs": ["result"],
                        "append_to": "content_list"
                    }
                ]
            }

            # Write pipeline file
            pipeline_path = tmpdir / "pipeline.yaml"
            with open(pipeline_path, 'w') as f:
                yaml.dump({"pipeline": pipeline_config}, f)

            # Create prompts directory and file
            prompts_dir = tmpdir / "prompts"
            prompts_dir.mkdir(exist_ok=True)
            prompt_file = prompts_dir / "test.md"
            prompt_file.write_text("""<!--
prompt:
  requires:
    - text
  format: markdown
-->
Test prompt {{text}}""")

            # This should NOT raise SystemExit
            lint_pipeline_contracts(str(pipeline_path))

    def test_linter_catches_append_to_in_nested_for_each(self, caplog):
        """Test that linter catches append_to errors in nested for-each steps"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            pipeline_config = {
                "name": "test-pipeline",
                "variables": {"prompts_dir": str(tmpdir / "prompts")},
                "linter_config": {
                    "enabled": True,
                    "treat_warnings_as_errors": True
                },
                "steps": [
                    {
                        "name": "process_items",
                        "type": "for-each",
                        "input": "${items}",
                        "item_var": "item",
                        "steps": [
                            {
                                "name": "nested_generate",
                                "type": "llm",
                                "prompt": {
                                    "file": "test.md",
                                    "inputs": {"text": "${item}"}
                                },
                                "append_to": "nested_list"  # append_to without outputs
                            }
                        ]
                    }
                ]
            }

            # Write pipeline file
            pipeline_path = tmpdir / "pipeline.yaml"
            with open(pipeline_path, 'w') as f:
                yaml.dump({"pipeline": pipeline_config}, f)

            # Create prompts directory and file
            prompts_dir = tmpdir / "prompts"
            prompts_dir.mkdir(exist_ok=True)
            prompt_file = prompts_dir / "test.md"
            prompt_file.write_text("""<!--
prompt:
  requires:
    - text
  format: markdown
-->
Test prompt {{text}}""")

            with pytest.raises(SystemExit):
                lint_pipeline_contracts(str(pipeline_path))

            log_output = caplog.text
            assert "nested_generate" in log_output
            assert "append_to" in log_output

    def test_linter_handles_empty_outputs_list(self, caplog):
        """Test that linter catches append_to with empty outputs list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            pipeline_config = {
                "name": "test-pipeline",
                "variables": {"prompts_dir": str(tmpdir / "prompts")},
                "linter_config": {
                    "enabled": True,
                    "treat_warnings_as_errors": True
                },
                "steps": [
                    {
                        "name": "generate_content",
                        "type": "llm",
                        "prompt": {
                            "file": "test.md",
                            "inputs": {"text": "test"}
                        },
                        "outputs": [],  # Empty list
                        "append_to": "content_list"
                    }
                ]
            }

            # Write pipeline file
            pipeline_path = tmpdir / "pipeline.yaml"
            with open(pipeline_path, 'w') as f:
                yaml.dump({"pipeline": pipeline_config}, f)

            # Create prompts directory and file
            prompts_dir = tmpdir / "prompts"
            prompts_dir.mkdir(exist_ok=True)
            prompt_file = prompts_dir / "test.md"
            prompt_file.write_text("""<!--
prompt:
  requires:
    - text
  format: markdown
-->
Test prompt {{text}}""")

            with pytest.raises(SystemExit):
                lint_pipeline_contracts(str(pipeline_path))

            log_output = caplog.text
            assert "generate_content" in log_output
            assert "append_to" in log_output

    def test_linter_ignores_function_steps_with_append_to(self, caplog):
        """Test that linter checks append_to for function steps too"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            pipeline_config = {
                "name": "test-pipeline",
                "variables": {},
                "linter_config": {
                    "enabled": True,
                    "treat_warnings_as_errors": True
                },
                "steps": [
                    {
                        "name": "function_step",
                        "type": "function",
                        "function": "some.module.func",
                        "append_to": "results_list"  # append_to without outputs
                    }
                ]
            }

            # Write pipeline file
            pipeline_path = tmpdir / "pipeline.yaml"
            with open(pipeline_path, 'w') as f:
                yaml.dump({"pipeline": pipeline_config}, f)

            with pytest.raises(SystemExit):
                lint_pipeline_contracts(str(pipeline_path))

            log_output = caplog.text
            assert "function_step" in log_output
            assert "append_to" in log_output