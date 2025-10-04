import pytest
from llmflow.runner import run_for_each_step, run_function_step
from llmflow.utils.data import flatten_json_to_markdown
import tempfile
from pathlib import Path

class TestSceneConcatenation:
    """Test that scene lists are properly built and concatenated"""

    def test_append_to_in_for_each_creates_full_list(self):
        """Test that append_to in for-each loop collects ALL items, not just the last"""
        context = {
            "scenes": [
                {"title": "Scene 1", "content": "Content 1"},
                {"title": "Scene 2", "content": "Content 2"},
                {"title": "Scene 3", "content": "Content 3"}
            ]
        }

        rule = {
            "name": "process_scenes",
            "type": "for-each",
            "input": "${scenes}",
            "item_var": "scene",
            "steps": [
                {
                    "name": "format_scene",
                    "type": "function",
                    "function": "tests.test_scene_concatenation.format_scene_content",
                    "inputs": {"scene": "${scene}"},
                    "outputs": "formatted_scene",
                    "append_to": "scene_list"
                }
            ]
        }

        def format_scene_content(scene):
            return f"## {scene['title']}\n{scene['content']}\n"

        import sys
        sys.modules[__name__].format_scene_content = format_scene_content

        # Run the for-each
        run_for_each_step(rule, context, {"variables": {}})

        # Assert ALL scenes were appended
        assert "scene_list" in context
        assert len(context["scene_list"]) == 3, f"Expected 3 scenes, got {len(context['scene_list'])}"

        # Check each scene is present
        assert "Scene 1" in context["scene_list"][0]
        assert "Scene 2" in context["scene_list"][1]
        assert "Scene 3" in context["scene_list"][2]

        print(f"Scene list contains: {context['scene_list']}")

    def test_flatten_json_to_markdown_concatenates_all_items(self):
        """Test that flatten_json_to_markdown concatenates ALL items, not just the last"""
        # Test with a list of markdown strings
        markdown_list = [
            "## Scene 1\nContent for scene 1\n",
            "## Scene 2\nContent for scene 2\n",
            "## Scene 3\nContent for scene 3\n"
        ]

        result = flatten_json_to_markdown(markdown_list)

        # All scenes should be present
        assert "Scene 1" in result
        assert "Scene 2" in result
        assert "Scene 3" in result

        # They should be in order
        assert result.index("Scene 1") < result.index("Scene 2")
        assert result.index("Scene 2") < result.index("Scene 3")

        print(f"Concatenated result:\n{result}")

    def test_template_receives_all_scenes(self):
        """Test that the final template rendering receives all concatenated scenes"""
        # Create a simple template
        template_content = """# Leader's Guide
{{leadersguide_scenes_markdown}}
---
End of guide"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(template_content)
            template_path = f.name

        try:
            # Simulate pipeline context with concatenated scenes
            context = {
                "leadersguide_scenes_markdown": "## Scene 1\nContent 1\n\n## Scene 2\nContent 2\n\n## Scene 3\nContent 3"
            }

            # Render template
            from llmflow.utils.io import render_markdown_template
            result = render_markdown_template(template_path, context)

            # All scenes should appear in the output
            assert "Scene 1" in result
            assert "Scene 2" in result
            assert "Scene 3" in result

            # Verify they're not just the last scene repeated
            assert result.count("## Scene") == 3

            print(f"Template output:\n{result}")

        finally:
            Path(template_path).unlink()

    def test_overwrite_vs_append_bug(self):
        """Test the difference between overwriting and appending in a loop"""
        # This test demonstrates the bug where only the last item is kept

        # Simulate WRONG behavior (overwriting)
        wrong_context = {}
        for i in range(3):
            wrong_context["scene_output"] = f"Scene {i+1}"  # Overwrites each time

        assert wrong_context["scene_output"] == "Scene 3"  # Only last value remains

        # Simulate CORRECT behavior (appending)
        correct_context = {"scene_list": []}
        for i in range(3):
            correct_context["scene_list"].append(f"Scene {i+1}")  # Appends each time

        assert len(correct_context["scene_list"]) == 3  # All values preserved
        assert correct_context["scene_list"] == ["Scene 1", "Scene 2", "Scene 3"]