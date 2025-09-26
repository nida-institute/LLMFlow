import pytest
import tempfile
from pathlib import Path
import yaml
from llmflow.utils.linter import lint_pipeline_contracts, collect_all_steps
import io
import sys

class TestLinterAppendTo:
    """Test that linter catches append_to without outputs errors"""

    def test_linter_catches_append_to_without_outputs(self):
        """Test that linter errors when append_to is used without outputs"""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create pipeline config
            pipeline_config = {
                "name": "test-pipeline",
                "variables": {"prompts_dir": str(tmpdir / "prompts")},  # Use absolute path
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
                        "append_to": "content_list"  # append_to without outputs
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

            # Capture stdout to check the error message
            captured_output = io.StringIO()
            sys.stdout = captured_output

            try:
                # This should raise SystemExit due to the error
                with pytest.raises(SystemExit):
                    lint_pipeline_contracts(str(pipeline_path))

                # Get the output
                output = captured_output.getvalue()

                # Verify the specific error message was printed
                assert "append_to: content_list" in output
                assert "no valid 'outputs' field" in output

            finally:
                sys.stdout = sys.__stdout__

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
                        "outputs": "content",  # Has outputs
                        "append_to": "content_list"  # And append_to
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

            # This should NOT raise an error
            lint_pipeline_contracts(str(pipeline_path))  # Should complete successfully

    def test_linter_catches_append_to_in_nested_for_each(self):
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

            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            try:
                with pytest.raises(SystemExit):
                    lint_pipeline_contracts(str(pipeline_path))

                output = captured_output.getvalue()

                # Verify the nested step error
                assert "nested_generate" in output
                assert "append_to: nested_list" in output

            finally:
                sys.stdout = sys.__stdout__

    def test_linter_handles_empty_outputs_list(self):
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

            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            try:
                with pytest.raises(SystemExit):
                    lint_pipeline_contracts(str(pipeline_path))

                output = captured_output.getvalue()
                assert "no valid 'outputs' field" in output

            finally:
                sys.stdout = sys.__stdout__

    def test_linter_ignores_function_steps_with_append_to(self):
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

            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            try:
                with pytest.raises(SystemExit):
                    lint_pipeline_contracts(str(pipeline_path))

                output = captured_output.getvalue()
                # The linter should catch this for function steps too
                assert "function_step" in output
                assert "append_to: results_list" in output
                assert "no valid 'outputs' field" in output

            finally:
                sys.stdout = sys.__stdout__