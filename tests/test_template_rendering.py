import tempfile
from pathlib import Path

from llmflow.utils.io import render_markdown_template


class TestTemplateRendering:
    """Test template rendering with various variable patterns"""

    def test_render_with_list_indexing(self):
        """Test that template rendering properly resolves list indices"""
        # Create a temporary template
        template_content = """
# Test Template

Body: {{body_value}}
Heart: {{heart_value}}
Scene: {{scene_title}}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(template_content)
            template_path = f.name

        try:
            # Test data - pass the resolved values as template variables
            variables = {
                "body_value": "${bodies_list[-1]}",
                "heart_value": "${hearts_list[-1]}",
                "scene_title": "${scene.title}",
            }

            # Context with the actual data
            context = {
                "bodies_list": ["body1", "body2", "final body"],
                "hearts_list": ["heart1", "heart2", "final heart"],
                "scene": {"title": "Test Scene"},
            }

            # Render template with context
            result = render_markdown_template(
                template_path=template_path, variables=variables, context=context
            )

            # Check results
            assert "Body: final body" in result
            assert "Heart: final heart" in result
            assert "Scene: Test Scene" in result

        finally:
            Path(template_path).unlink()

    def test_render_with_empty_lists(self):
        """Test template rendering with empty lists"""
        template_content = "Result: ${items[-1]}"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(template_content)
            template_path = f.name

        try:
            variables = {"items": []}
            result = render_markdown_template(
                template_path=template_path, variables=variables
            )

            # Should handle empty list gracefully
            assert result is not None

        finally:
            Path(template_path).unlink()
