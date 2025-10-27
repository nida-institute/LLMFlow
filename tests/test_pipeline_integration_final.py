import tempfile
from pathlib import Path

from llmflow.runner import run_function_step


class TestPipelineIntegrationFinal:
    """Test the complete pipeline flow with append_to and template rendering"""

    def test_complete_pipeline_flow(self):
        """Test the full flow: append_to -> list resolution -> template rendering"""
        context = {}

        # Step 1: Generate content and append to list (simulating bodies step)
        step1 = {
            "name": "generate_body",
            "type": "function",
            "function": "tests.test_pipeline_integration_final.generate_body_content",
            "outputs": "body_content",
            "append_to": "bodies_list",
        }

        def generate_body_content():
            return "This is the body content for the scene"

        import sys

        sys.modules[__name__].generate_body_content = generate_body_content

        # Run step 1
        run_function_step(step1, context)

        # Verify list was created
        assert "bodies_list" in context
        assert len(context["bodies_list"]) == 1
        assert context["bodies_list"][0] == "This is the body content for the scene"

        # Step 2: Render template using the list
        template_content = """### Scene Output
Body Content: {{body_value}}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(template_content)
            template_path = f.name

        try:
            step2 = {
                "name": "render_scene",
                "type": "function",
                "function": "llmflow.utils.io.render_markdown_template",
                "inputs": {
                    "template_path": template_path,
                    "variables": {
                        "body_value": "${bodies_list[-1]}"  # This should resolve!
                    },
                },
                "outputs": "rendered_scene",
            }

            # Run step 2
            run_function_step(step2, context)

            # Check the result
            assert "rendered_scene" in context
            result = context["rendered_scene"]

            print(f"\nFinal rendered output:\n{result}")

            # This is the key test - the list reference should be resolved
            assert "This is the body content for the scene" in result
            assert "${bodies_list[-1]}" not in result  # Should NOT appear literally

        finally:
            Path(template_path).unlink()
