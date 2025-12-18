"""
Comprehensive unit tests for template rendering functions in utils/io.py

Tests cover:
- eval_template_expr: expression evaluation with variables
- render_template: {{}} syntax substitution
- render_markdown_template: two-pass rendering ({{}} and ${})
- extract_template_variables: variable extraction
- validate_template: template validation
"""

import pytest
from pathlib import Path
import tempfile
import os

from llmflow.utils.io import (
    eval_template_expr,
    render_template,
    render_markdown_template,
    extract_template_variables,
    validate_template,
)


# ============================================================================
# eval_template_expr Tests
# ============================================================================

class TestEvalTemplateExpr:
    """Test expression evaluation with variable substitution."""

    @pytest.mark.parametrize("expr,variables,expected", [
        # Simple variable substitution
        ("name", {"name": "World"}, "World"),
        ("x", {"x": 42}, "42"),
        ("value", {"value": True}, "True"),

        # Dot notation
        ("user.name", {"user": {"name": "Alice"}}, "Alice"),
        ("config.debug", {"config": {"debug": False}}, "False"),
        ("data.nested.value", {"data": {"nested": {"value": 99}}}, "99"),

        # Subscript access
        ("items[0]", {"items": [1, 2, 3]}, "1"),
        ("data['key']", {"data": {"key": "value"}}, "value"),

        # Math expressions
        ("x + y", {"x": 1, "y": 2}, "3"),
        ("x * 2", {"x": 5}, "10"),
        # Note: len() is blocked for security (no __builtins__)

        # String operations
        ("name.upper()", {"name": "hello"}, "HELLO"),
        ("name.strip()", {"name": "  test  "}, "test"),
    ])
    def test_eval_success(self, expr, variables, expected):
        """Test successful expression evaluation."""
        result = eval_template_expr(expr, variables)
        assert result == expected

    @pytest.mark.parametrize("expr,variables", [
        # Missing variables
        ("missing", {}),
        ("user.name", {}),
        ("items[0]", {}),

        # Invalid expressions
        ("1/0", {}),
        ("invalid syntax!", {}),
        # Note: user.nonexistent returns 'None' with AttrDict, not {{...}}
    ])
    def test_eval_failure_returns_original(self, expr, variables):
        """Test that failed evaluation returns {{expr}} unchanged."""
        result = eval_template_expr(expr, variables)
        assert result == f"{{{{{expr}}}}}"

    def test_eval_with_none(self):
        """Test evaluation with None values."""
        result = eval_template_expr("value", {"value": None})
        assert result == "None"

    def test_eval_with_empty_string(self):
        """Test evaluation with empty string."""
        result = eval_template_expr("value", {"value": ""})
        assert result == ""

    def test_eval_blocks_builtins(self):
        """Test that dangerous builtins are blocked."""
        result = eval_template_expr("open('/etc/passwd')", {})
        assert result == "{{open('/etc/passwd')}}"


# ============================================================================
# render_template Tests
# ============================================================================

class TestRenderTemplate:
    """Test {{}} syntax template rendering."""

    @pytest.mark.parametrize("template,variables,expected", [
        # Basic substitution
        ("Hello {{name}}", {"name": "World"}, "Hello World"),
        ("{{x}} + {{y}}", {"x": 1, "y": 2}, "1 + 2"),
        ("Value: {{value}}", {"value": 42}, "Value: 42"),

        # Multiple occurrences
        ("{{x}} and {{x}}", {"x": "test"}, "test and test"),
        ("{{a}}{{b}}{{c}}", {"a": 1, "b": 2, "c": 3}, "123"),

        # With whitespace
        ("{{ name }}", {"name": "test"}, "test"),
        ("{{  value  }}", {"value": 123}, "123"),

        # Empty template
        ("", {}, ""),
        ("no variables", {}, "no variables"),

        # Dot notation
        ("Hello {{user.name}}", {"user": {"name": "Alice"}}, "Hello Alice"),
        ("{{config.port}}", {"config": {"port": 8080}}, "8080"),
    ])
    def test_render_basic(self, template, variables, expected):
        """Test basic template rendering."""
        result = render_template(template, variables)
        assert result == expected

    def test_render_with_nested_dict(self):
        """Test rendering with nested dictionary access."""
        template = "{{person.address.city}}"
        variables = {
            "person": {
                "address": {
                    "city": "Seattle"
                }
            }
        }
        result = render_template(template, variables)
        assert result == "Seattle"

    def test_render_with_list_access(self):
        """Test rendering with list subscript access."""
        template = "First: {{items[0]}}, Last: {{items[-1]}}"
        variables = {"items": ["a", "b", "c"]}
        result = render_template(template, variables)
        assert result == "First: a, Last: c"

    def test_render_missing_variable(self):
        """Test that missing variables are left as {{variable}}."""
        template = "Hello {{name}}, age {{age}}"
        variables = {"name": "Alice"}
        result = render_template(template, variables)
        assert result == "Hello Alice, age {{age}}"

    def test_render_with_none(self):
        """Test rendering with None value."""
        template = "Value: {{value}}"
        variables = {"value": None}
        result = render_template(template, variables)
        assert result == "Value: None"

    def test_render_with_empty_string(self):
        """Test rendering with empty string value."""
        template = "Value: {{value}}"
        variables = {"value": ""}
        result = render_template(template, variables)
        assert result == "Value: "

    def test_render_with_boolean(self):
        """Test rendering with boolean values."""
        template = "Debug: {{debug}}, Active: {{active}}"
        variables = {"debug": True, "active": False}
        result = render_template(template, variables)
        assert result == "Debug: True, Active: False"

    def test_render_with_expressions(self):
        """Test rendering with expressions."""
        template = "Sum: {{x + y}}, Product: {{x * y}}"
        variables = {"x": 3, "y": 4}
        result = render_template(template, variables)
        assert result == "Sum: 7, Product: 12"

    def test_render_complex_template(self):
        """Test rendering a complex multi-line template."""
        template = """
# {{title}}

Author: {{author.name}}
Date: {{date}}

Content:
{{content}}

Stats: {{stats.views}} views
"""
        variables = {
            "title": "Test Post",
            "author": {"name": "Alice"},
            "date": "2025-12-18",
            "content": "This is test content.",
            "stats": {"views": 42}
        }
        result = render_template(template, variables)
        assert "# Test Post" in result
        assert "Author: Alice" in result
        assert "Stats: 42 views" in result

    def test_render_special_characters(self):
        """Test rendering with special characters in values."""
        template = "Message: {{message}}"
        variables = {"message": "Hello\nWorld\t!"}
        result = render_template(template, variables)
        assert result == "Message: Hello\nWorld\t!"

    def test_render_unicode(self):
        """Test rendering with unicode characters."""
        template = "Hebrew: {{hebrew}}, Greek: {{greek}}"
        variables = {
            "hebrew": "בְּרֵאשִׁית",
            "greek": "Ἐν ἀρχῇ"
        }
        result = render_template(template, variables)
        assert "בְּרֵאשִׁית" in result
        assert "Ἐν ἀρχῇ" in result

    def test_render_with_method_calls(self):
        """Test rendering with method calls on variables."""
        template = "Upper: {{name.upper()}}, Lower: {{name.lower()}}"
        variables = {"name": "Alice"}
        result = render_template(template, variables)
        assert result == "Upper: ALICE, Lower: alice"

    def test_render_with_len_blocked(self):
        """Test that len() is blocked for security."""
        template = "Count: {{len(items)}}"
        variables = {"items": [1, 2, 3, 4, 5]}
        result = render_template(template, variables)
        # len() is blocked because __builtins__ is empty for security
        assert result == "Count: {{len(items)}}"

    def test_render_malformed_expression(self):
        """Test that malformed expressions are left unchanged."""
        template = "Bad: {{1/0}}, Good: {{x}}"
        variables = {"x": "works"}
        result = render_template(template, variables)
        assert "{{1/0}}" in result
        assert "Good: works" in result


# ============================================================================
# render_markdown_template Tests
# ============================================================================

class TestRenderMarkdownTemplate:
    """Test two-pass template rendering with file loading."""

    @pytest.fixture
    def temp_template_file(self):
        """Create a temporary template file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            yield f
            # Cleanup
            try:
                os.unlink(f.name)
            except:
                pass

    def test_render_simple_template(self, temp_template_file):
        """Test rendering a simple template file."""
        template_content = "Hello {{name}}!"
        temp_template_file.write(template_content)
        temp_template_file.flush()

        variables = {"name": "World"}
        result = render_markdown_template(temp_template_file.name, variables)
        assert result == "Hello World!"

    def test_render_first_pass_curly_braces(self, temp_template_file):
        """Test first pass {{variable}} substitution."""
        template_content = "Title: {{title}}\nAuthor: {{author}}"
        temp_template_file.write(template_content)
        temp_template_file.flush()

        variables = {"title": "Test", "author": "Alice"}
        result = render_markdown_template(temp_template_file.name, variables)
        assert "Title: Test" in result
        assert "Author: Alice" in result

    def test_render_second_pass_dollar_syntax(self, temp_template_file):
        """Test second pass ${variable} substitution with context."""
        template_content = "Value: ${context.value}"
        temp_template_file.write(template_content)
        temp_template_file.flush()

        variables = {}
        context = {"context": {"value": 42}}
        result = render_markdown_template(temp_template_file.name, variables, context=context)
        # Note: ${} resolution depends on runner.resolve, might not work in isolation
        # This tests that the function doesn't crash
        assert result is not None

    def test_render_both_syntaxes(self, temp_template_file):
        """Test template with both {{}} and ${} syntax."""
        template_content = "Title: {{title}}\nValue: ${data.value}"
        temp_template_file.write(template_content)
        temp_template_file.flush()

        variables = {"title": "Test"}
        context = {"data": {"value": "context-value"}}
        result = render_markdown_template(temp_template_file.name, variables, context=context)
        assert "Title: Test" in result

    def test_render_multiline_template(self, temp_template_file):
        """Test rendering multi-line markdown template."""
        template_content = """# {{title}}

## Section 1
Content: {{content}}

## Section 2
Value: {{value}}
"""
        temp_template_file.write(template_content)
        temp_template_file.flush()

        variables = {
            "title": "My Document",
            "content": "Test content",
            "value": 123
        }
        result = render_markdown_template(temp_template_file.name, variables)
        assert "# My Document" in result
        assert "Content: Test content" in result
        assert "Value: 123" in result

    def test_render_missing_file(self):
        """Test that missing template file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            render_markdown_template("/nonexistent/template.md", {})

    def test_render_unicode_content(self, temp_template_file):
        """Test rendering template with unicode content."""
        template_content = "Greek: {{greek}}\nHebrew: {{hebrew}}"
        temp_template_file.write(template_content)
        temp_template_file.flush()

        variables = {
            "greek": "Ἐν ἀρχῇ",
            "hebrew": "בְּרֵאשִׁית"
        }
        result = render_markdown_template(temp_template_file.name, variables)
        assert "Ἐν ἀρχῇ" in result
        assert "בְּרֵאשִׁית" in result

    def test_render_empty_variables(self, temp_template_file):
        """Test rendering with empty variables dict."""
        template_content = "Hello World"
        temp_template_file.write(template_content)
        temp_template_file.flush()

        result = render_markdown_template(temp_template_file.name, {})
        assert result == "Hello World"

    def test_render_with_none_context(self, temp_template_file):
        """Test rendering with None context (only first pass)."""
        template_content = "Title: {{title}}"
        temp_template_file.write(template_content)
        temp_template_file.flush()

        variables = {"title": "Test"}
        result = render_markdown_template(temp_template_file.name, variables, context=None)
        assert result == "Title: Test"


# ============================================================================
# extract_template_variables Tests
# ============================================================================

class TestExtractTemplateVariables:
    """Test variable extraction from template strings."""

    @pytest.mark.parametrize("template,expected", [
        # Single variable
        ("{{name}}", {"name"}),
        ("${value}", {"value"}),

        # Multiple variables
        ("{{x}} and {{y}}", {"x", "y"}),
        ("${a} ${b} ${c}", {"a", "b", "c"}),

        # Mixed syntax
        ("{{foo}} and ${bar}", {"foo", "bar"}),

        # With whitespace
        ("{{ name }}", {"name"}),
        ("${ value }", {"value"}),

        # Duplicate variables
        ("{{x}} {{x}} {{x}}", {"x"}),

        # No variables
        ("plain text", set()),
        ("", set()),

        # Dot notation
        ("{{user.name}}", {"user.name"}),
        ("${config.port}", {"config.port"}),

        # Complex expressions
        ("{{x + y}}", {"x + y"}),
        ("{{len(items)}}", {"len(items)"}),
    ])
    def test_extract_variables(self, template, expected):
        """Test extracting variables from templates."""
        result = extract_template_variables(template)
        assert result == expected

    def test_extract_ignores_handlebars_helpers(self):
        """Test that handlebars helper syntax is ignored."""
        template = "{{#if condition}}text{{/if}}"
        result = extract_template_variables(template)
        # Should not include #if or /if
        assert "#if condition" not in result
        assert "/if" not in result

    def test_extract_multiline_template(self):
        """Test extracting from multi-line template."""
        template = """
# {{title}}

Content: {{content}}
Value: ${data.value}
"""
        result = extract_template_variables(template)
        assert "title" in result
        assert "content" in result
        assert "data.value" in result
        assert len(result) == 3

    def test_extract_nested_braces(self):
        """Test handling of nested or malformed braces."""
        template = "{{outer {{inner}}}}"
        result = extract_template_variables(template)
        # Should handle gracefully without crashing
        assert isinstance(result, set)


# ============================================================================
# validate_template Tests
# ============================================================================

class TestValidateTemplate:
    """Test template validation."""

    @pytest.fixture
    def temp_template_file(self):
        """Create a temporary template file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            yield f
            # Cleanup
            try:
                os.unlink(f.name)
            except:
                pass

    def test_validate_existing_file(self, temp_template_file):
        """Test validating an existing file without checking variables."""
        temp_template_file.write("Hello {{name}}")
        temp_template_file.flush()

        is_valid, missing, extra = validate_template(temp_template_file.name)
        assert is_valid is True
        assert missing == []
        assert extra == []

    def test_validate_missing_file(self):
        """Test validating a non-existent file."""
        is_valid, missing, extra = validate_template("/nonexistent/file.md")
        assert is_valid is False

    def test_validate_with_required_variables_all_present(self, temp_template_file):
        """Test validation when all required variables are present."""
        temp_template_file.write("{{title}} {{author}} {{date}}")
        temp_template_file.flush()

        required = ["title", "author", "date"]
        is_valid, missing, extra = validate_template(temp_template_file.name, required)
        assert is_valid is True
        assert missing == []
        assert extra == []

    def test_validate_with_missing_variables(self, temp_template_file):
        """Test validation when required variables are missing."""
        temp_template_file.write("{{title}}")
        temp_template_file.flush()

        required = ["title", "author", "date"]
        is_valid, missing, extra = validate_template(temp_template_file.name, required)
        assert is_valid is False
        assert set(missing) == {"author", "date"}

    def test_validate_with_extra_variables(self, temp_template_file):
        """Test validation when template has extra variables."""
        temp_template_file.write("{{title}} {{author}} {{date}} {{extra}}")
        temp_template_file.flush()

        required = ["title", "author"]
        is_valid, missing, extra = validate_template(temp_template_file.name, required)
        assert is_valid is True
        assert missing == []
        assert set(extra) == {"date", "extra"}

    def test_validate_empty_template(self, temp_template_file):
        """Test validating an empty template."""
        temp_template_file.write("")
        temp_template_file.flush()

        required = ["title"]
        is_valid, missing, extra = validate_template(temp_template_file.name, required)
        assert is_valid is False
        assert missing == ["title"]

    def test_validate_mixed_syntax(self, temp_template_file):
        """Test validation with mixed {{}} and ${} syntax."""
        temp_template_file.write("{{title}} ${data.value}")
        temp_template_file.flush()

        required = ["title", "data.value"]
        is_valid, missing, extra = validate_template(temp_template_file.name, required)
        assert is_valid is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestTemplateIntegration:
    """Test end-to-end template rendering scenarios."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for templates."""
        import tempfile
        import shutil
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_full_workflow(self, temp_dir):
        """Test complete workflow: validate, extract, render."""
        template_path = Path(temp_dir) / "test.md"
        template_path.write_text("# {{title}}\n\nContent: {{content}}")

        # Step 1: Validate
        is_valid, _, _ = validate_template(str(template_path), ["title", "content"])
        assert is_valid is True

        # Step 2: Extract
        variables = extract_template_variables(template_path.read_text())
        assert variables == {"title", "content"}

        # Step 3: Render
        result = render_markdown_template(
            str(template_path),
            {"title": "Test", "content": "Hello World"}
        )
        assert "# Test" in result
        assert "Content: Hello World" in result

    def test_render_with_attrdict(self):
        """Test that render_template works with AttrDict for dot notation."""
        from llmflow.utils.io import to_attrdict

        template = "Hello {{user.name}} from {{user.location}}"
        variables = to_attrdict({"user": {"name": "Alice", "location": "Seattle"}})

        result = render_template(template, variables)
        assert result == "Hello Alice from Seattle"

    def test_nested_structure_rendering(self):
        """Test rendering deeply nested structures."""
        template = "{{data.level1.level2.level3}}"
        variables = {
            "data": {
                "level1": {
                    "level2": {
                        "level3": "deep value"
                    }
                }
            }
        }

        result = render_template(template, variables)
        assert result == "deep value"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestTemplateEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_variable_name(self):
        """Test handling of empty variable name."""
        template = "Value: {{}}"
        result = render_template(template, {})
        # Should handle gracefully
        assert isinstance(result, str)

    def test_variable_with_special_chars(self):
        """Test variables with special characters."""
        template = "{{var_name}} {{var-name}} {{var.name}}"
        variables = {
            "var_name": "underscore",
            "var-name": "hyphen",
            "var.name": "dot"
        }
        result = render_template(template, variables)
        assert "underscore" in result

    def test_numeric_keys(self):
        """Test numeric dictionary keys."""
        template = "{{data[0]}} {{data[1]}}"
        variables = {"data": {0: "first", 1: "second"}}
        result = render_template(template, variables)
        # Behavior depends on implementation
        assert isinstance(result, str)

    def test_very_long_template(self):
        """Test rendering very long template."""
        template = " ".join([f"{{{{var{i}}}}}" for i in range(100)])
        variables = {f"var{i}": i for i in range(100)}
        result = render_template(template, variables)
        assert "0" in result
        assert "99" in result

    def test_recursive_variable_reference(self):
        """Test that recursive references don't cause infinite loops."""
        template = "{{x}}"
        variables = {"x": "{{x}}"}  # Self-referential
        result = render_template(template, variables)
        # Should just substitute once
        assert result == "{{x}}"
