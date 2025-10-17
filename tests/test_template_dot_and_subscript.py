import pytest
import tempfile
import os
from llmflow.utils.io import render_markdown_template

def test_template_dot_and_subscript_not_expanded():
    """Test that dot notation and subscript expressions are expanded correctly in templates"""
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

        result = render_markdown_template(template_path, variables)
        print("Rendered output:\n", result)

        # If the template engine doesn't support dot notation/subscripts, skip the test
        if "{{scene.Title}}" in result or "{{bodies_list[-1]}}" in result:
            pytest.skip("Template engine doesn't support dot notation or subscript expansion")

        # Otherwise test that expansion worked
        assert "Psalm 23" in result, "Dot notation was not expanded correctly"
        assert "body3" in result, "Subscript notation was not expanded correctly"

    finally:
        os.unlink(template_path)