import os
import tempfile

import pytest
import yaml

from llmflow.runner import run_pipeline


class TestCriticalPipelineFlow:
    @pytest.mark.skip(reason="Pipeline runner does not support 'save' step type yet")
    def test_full_pipeline_produces_all_scenes(self):
        """Regression test: Ensure ALL scenes appear in final output"""
        # Since run_pipeline doesn't return context, we need to save outputs to file
        pipeline = {
            "name": "test-pipeline",
            "steps": [
                {
                    "name": "create_scenes",
                    "type": "function",
                    "function": "tests.test_critical_pipeline_flow.create_test_scenes",
                    "outputs": "scenes",
                },
                {
                    "name": "process_each_scene",
                    "type": "for-each",
                    "input": "${scenes}",
                    "item_var": "scene",
                    "steps": [
                        {
                            "name": "format_scene",
                            "type": "function",
                            "function": "tests.test_critical_pipeline_flow.format_scene",
                            "inputs": {"scene": "${scene}"},
                            "outputs": "formatted",
                            "append_to": "formatted_scenes",
                        }
                    ],
                },
                {
                    "name": "concatenate_scenes",
                    "type": "function",
                    "function": "llmflow.utils.data.flatten_json_to_markdown",
                    "inputs": {"data": "${formatted_scenes}"},
                    "outputs": "final_output",
                },
                {
                    "name": "save_output",
                    "type": "save",
                    "input": "${final_output}",
                    "filename": "test_output.md",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_file = os.path.join(tmpdir, "test_pipeline.yaml")
            with open(pipeline_file, "w") as f:
                yaml.dump(pipeline, f)

            # Run pipeline with output directory
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                run_pipeline(pipeline_file)

                # Check output file
                output_file = os.path.join("outputs", "test_output.md")
                assert os.path.exists(output_file), "Output file not created"

                with open(output_file, "r") as f:
                    content = f.read()

                # Critical assertions
                assert "Scene 1" in content
                assert "Scene 2" in content
                assert "Scene 3" in content

                # Ensure no duplicates
                assert content.count("Scene 1") == 1
                assert content.count("Scene 2") == 1
                assert content.count("Scene 3") == 1
            finally:
                os.chdir(old_cwd)


def create_test_scenes():
    return [
        {"id": 1, "title": "Scene 1", "content": "First scene"},
        {"id": 2, "title": "Scene 2", "content": "Second scene"},
        {"id": 3, "title": "Scene 3", "content": "Third scene"},
    ]


def format_scene(scene):
    return f"## {scene['title']}\n{scene['content']}\n"
