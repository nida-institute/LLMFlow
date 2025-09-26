import tempfile
from pathlib import Path
from llmflow.utils.io import render_markdown_template

def test_template_dot_and_subscript_not_expanded():
    """Test that dot notation and subscript expressions are not expanded in templates"""
    # Prepare a template that uses dot notation and subscript
    template_content = """
# Scene: {{scene.Title}}
Last body: {{bodies_list[-1]}}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(template_content)
        template_path = f.name

    try:
        variables = {
            "scene": {"Title": "Psalm 23"},
            "bodies_list": ["body1", "body2", "body3"]
        }
        # This should expand to "Psalm 23" and "body3"
        result = render_markdown_template(template_path, variables)
        print("Rendered output:\n", result)

        # The test should fail if the output still contains the template expressions
        assert "{{scene.Title}}" not in result, "Dot notation was not expanded"
        assert "{{bodies_list[-1]}}" not in result, "Subscript was not expanded"
        # And should contain the correct values
        assert "Psalm 23" in result
        assert "body3" in result

    finally:
        Path(template_path).unlink()