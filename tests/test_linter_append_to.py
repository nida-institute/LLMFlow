from pathlib import Path
import tempfile
import yaml
import pytest

def test_linter_passes_with_outputs_and_append_to():
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
                        "file": str(tmpdir / "prompts" / "test.md"),
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