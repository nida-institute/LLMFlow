from llmflow.runner import resolve
from llmflow.utils.io import render_markdown_template


class TestTemplateRenderingDebug:
    """Debug the template rendering issue"""

    def test_manual_resolution_works(self):
        """Test that manually resolving before template rendering works"""
        import tempfile
        from pathlib import Path

        # Use template syntax {{}} not pipeline syntax ${}
        template_content = "Body: {{body_value}}"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(template_content)
            template_path = f.name

        try:
            # Original approach - passing unresolved variable
            variables = {"body_value": "${bodies_list[-1]}"}
            result1 = render_markdown_template(template_path, variables)
            print(f"Without resolution: {result1}")

            # Manual resolution approach
            context = {"bodies_list": ["body1", "body2", "final body"]}
            resolved_value = resolve("${bodies_list[-1]}", context)
            variables2 = {"body_value": resolved_value}
            result2 = render_markdown_template(template_path, variables2)
            print(f"With resolution: {result2}")

            assert "final body" in result2

        finally:
            Path(template_path).unlink()
