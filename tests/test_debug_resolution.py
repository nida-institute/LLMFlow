import pytest
from llmflow.runner import resolve
from llmflow.utils.io import render_markdown_template

class TestDebugResolution:
    """Debug the exact issue happening in production"""

    def test_resolve_with_pipeline_context(self):
        """Test that resolve works when variables reference context"""
        # This simulates your actual pipeline state
        variables = {
            "step1": "${bodies_list[-1]}",
            "step2": "${hearts_list[-1]}"
        }

        context = {
            "bodies_list": ["intro", "middle", "conclusion"],
            "hearts_list": ["start", "journey", "arrival"]
        }

        # Test that resolve works with context
        resolved1 = resolve(variables["step1"], context)
        resolved2 = resolve(variables["step2"], context)

        assert resolved1 == "conclusion"
        assert resolved2 == "arrival"

    def test_render_markdown_template_full_flow(self):
        """Test the exact flow that's failing in production"""
        import tempfile
        from pathlib import Path

        # Your actual template content
        template_content = """### Step 2: Context (What's the Background?)
> How does it help you picture the scene?

{{hearts_value}}

---

### Step 3: Spiritual Journey
> What struggles or growth were they experiencing?

{{connecting_value}}"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(template_content)
            template_path = f.name

        try:
            # Your actual pipeline state
            variables = {
                "hearts_value": "${hearts_list[-1]}",
                "connecting_value": "${connecting_list[-1]}"
            }

            context = {
                "hearts_list": ["heart1", "heart2", "This is the hearts content"],
                "connecting_list": ["conn1", "conn2", "This is the connecting content"]
            }

            # This is what should happen
            result = render_markdown_template(
                template_path=template_path,
                variables=variables,
                context=context
            )

            # Verify it worked
            assert "This is the hearts content" in result
            assert "This is the connecting content" in result
            assert "${hearts_list[-1]}" not in result

            print("Result:", result)

        finally:
            Path(template_path).unlink()