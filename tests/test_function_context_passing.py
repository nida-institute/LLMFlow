import pytest
import inspect
from llmflow.utils.io import render_markdown_template
from llmflow.runner import run_function_step

class TestFunctionContextPassing:
    """Test that functions receive context parameter when needed"""

    def test_render_markdown_template_signature(self):
        """Check that render_markdown_template accepts context parameter"""
        sig = inspect.signature(render_markdown_template)
        params = list(sig.parameters.keys())

        print(f"\nrender_markdown_template signature: {sig}")
        print(f"Parameters: {params}")

        assert "template_path" in params
        assert "variables" in params
        assert "context" in params, "render_markdown_template must have a 'context' parameter!"

    def test_function_step_passes_context(self):
        """Test that run_function_step passes context when function accepts it"""
        import tempfile
        from pathlib import Path

        template_content = "Result: {{value}}"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(template_content)
            template_path = f.name

        try:
            context = {
                "items": ["a", "b", "c"]
            }

            rule = {
                "name": "test",
                "type": "function",
                "function": "llmflow.utils.io.render_markdown_template",
                "inputs": {
                    "template_path": template_path,
                    "variables": {
                        "value": "${items[-1]}"
                    }
                },
                "outputs": "rendered_result"  # Add this!
            }

            # Add debug output
            print(f"\nRunning function step with rule: {rule}")
            print(f"Context: {context}")

            # run_function_step doesn't return anything - it stores in context
            run_function_step(rule, context)

            # Check the result in context
            assert "rendered_result" in context
            result = context["rendered_result"]

            print(f"Result from context: {result}")

            # If context was passed correctly, ${items[-1]} should resolve to "c"
            assert "Result: c" in result, f"Expected 'Result: c' but got '{result}'"

        finally:
            Path(template_path).unlink()