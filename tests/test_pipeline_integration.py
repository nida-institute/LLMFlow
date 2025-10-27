from pathlib import Path

from llmflow.runner import run_function_step


class TestPipelineIntegration:
    """Test the actual pipeline flow that's failing"""

    def test_function_step_with_template_rendering(self):
        """Test that run_function_step properly passes context to render_markdown_template"""
        # Simulate the pipeline context with lists
        context = {
            "bodies_list": ["body1", "body2", "final body content"],
            "hearts_list": ["heart1", "heart2", "final heart content"],
            "connecting_list": ["conn1", "conn2", "final connecting content"],
            "naming_list": ["name1", "name2", "final naming content"],
        }

        # Create a test template
        import tempfile

        template_content = """### Step 1: Bodies
{{step1}}

### Step 2: Hearts
{{step2}}

### Step 3: Connecting
{{step3}}

### Step 4: Naming
{{step4}}"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(template_content)
            template_path = f.name

        try:
            # Simulate the function step configuration
            rule = {
                "name": "assemble_leadersguide_scene_markdown",
                "type": "function",
                "function": "llmflow.utils.io.render_markdown_template",
                "inputs": {
                    "template_path": template_path,
                    "variables": {
                        "step1": "${bodies_list[-1]}",
                        "step2": "${hearts_list[-1]}",
                        "step3": "${connecting_list[-1]}",
                        "step4": "${naming_list[-1]}",
                    },
                },
                "outputs": "scene_markdown",
            }

            # Run the function step
            run_function_step(rule, context)
            result = context.get("scene_markdown")

            # Check that the template was rendered with resolved values
            assert "final body content" in result
            assert "final heart content" in result
            assert "final connecting content" in result
            assert "final naming content" in result

            # Should NOT contain unresolved variables
            assert "${bodies_list[-1]}" not in result

        finally:
            Path(template_path).unlink()
