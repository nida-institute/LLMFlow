class TestCriticalTemplateFlow:
    def test_template_receives_all_processed_data(self):
        """Ensure templates get complete data from pipeline"""
        import tempfile

        from llmflow.utils.io import render_markdown_template

        # Create test template
        template = """# Leader's Guide
{{intro}}

## Scenes
{{scenes_markdown}}

## Summary
Total scenes: {{scene_count}}
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(template)
            template_path = f.name

        # Simulate pipeline context at template step
        context = {
            "intro": "Introduction text",
            "scenes_markdown": "## Scene 1\nContent\n\n## Scene 2\nContent",
            "scene_count": 2,
        }

        result = render_markdown_template(template_path, context)

        # Critical assertions
        assert "Introduction text" in result
        assert "## Scene 1" in result
        assert "## Scene 2" in result
        assert "Total scenes: 2" in result
