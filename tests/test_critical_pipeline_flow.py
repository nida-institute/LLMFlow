import os
import tempfile
import yaml

import pytest
from llmflow.runner import run_pipeline


class TestCriticalPipelineFlow:
    def test_full_pipeline_produces_all_scenes(self):
        """
        Test that a complete pipeline with for-each, function, and save steps
        produces the expected output files
        """
        from pathlib import Path

        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            pipeline_config = {
                "name": "test_pipeline",  # Add required name field
                "variables": {
                    "scenes": ["scene1", "scene2", "scene3"],
                    "output_dir": str(output_dir),
                },
                "steps": [
                    {
                        "name": "process_scenes",
                        "type": "for-each",
                        "input": "${scenes}",
                        "item_var": "scene",
                        "steps": [
                            {
                                "name": "generate_content",
                                "type": "function",
                                "function": "tests.test_critical_pipeline_flow.generate_scene_content",
                                "inputs": {"scene_name": "${scene}"},
                                "outputs": "content",
                            },
                            {
                                "name": "save_scene",
                                "type": "save",
                                "content": "${content}",
                                "path": "${output_dir}/${scene}.txt",
                            },
                        ],
                    }
                ],
            }

            # Write the pipeline config to a temporary YAML file
            pipeline_file = output_dir / "pipeline.yaml"
            with open(pipeline_file, "w") as f:
                yaml.dump(pipeline_config, f)

            # Run the pipeline from file
            context = run_pipeline(str(pipeline_file), skip_lint=True)

            # Verify all scene files were created
            assert (output_dir / "scene1.txt").exists(), "scene1.txt should exist"
            assert (output_dir / "scene2.txt").exists(), "scene2.txt should exist"
            assert (output_dir / "scene3.txt").exists(), "scene3.txt should exist"

            # Verify content
            content1 = (output_dir / "scene1.txt").read_text()
            assert "Content for scene1" in content1


def generate_scene_content(scene_name):
    """Helper function for test"""
    return f"Content for {scene_name}"
