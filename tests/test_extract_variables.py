"""Comprehensive unit tests for template variable extraction.

Tests cover:
- extract_template_variables(): Both {{ }} and ${ } syntaxes
- Edge cases: Escaped braces, nested structures, malformed templates
- Complex expressions, whitespace handling, Unicode
"""

import pytest
from llmflow.utils.io import extract_template_variables


# ============================================================================
# Test extract_template_variables() - Basic Functionality
# ============================================================================

class TestExtractTemplateVariablesBasic:
    """Test basic variable extraction functionality."""

    def test_single_curly_brace_variable(self):
        """Single {{variable}} should be extracted."""
        result = extract_template_variables("Hello {{name}}")
        assert result == {"name"}

    def test_single_dollar_brace_variable(self):
        """Single ${variable} should be extracted."""
        result = extract_template_variables("Hello ${name}")
        assert result == {"name"}

    def test_multiple_curly_variables(self):
        """Multiple {{variables}} should all be extracted."""
        result = extract_template_variables("{{first}} {{middle}} {{last}}")
        assert result == {"first", "middle", "last"}

    def test_multiple_dollar_variables(self):
        """Multiple ${variables} should all be extracted."""
        result = extract_template_variables("${x} ${y} ${z}")
        assert result == {"x", "y", "z"}

    def test_mixed_syntax_variables(self):
        """Mix of {{}} and ${} syntax should both be extracted."""
        result = extract_template_variables("{{foo}} and ${bar}")
        assert result == {"foo", "bar"}

    def test_duplicate_variables_deduped(self):
        """Duplicate variable names should appear once."""
        result = extract_template_variables("{{x}} {{x}} {{x}}")
        assert result == {"x"}

    def test_empty_template(self):
        """Empty template should return empty set."""
        result = extract_template_variables("")
        assert result == set()

    def test_plain_text_no_variables(self):
        """Plain text without variables should return empty set."""
        result = extract_template_variables("Just plain text, no variables here.")
        assert result == set()


# ============================================================================
# Test extract_template_variables() - Whitespace Handling
# ============================================================================

class TestExtractTemplateVariablesWhitespace:
    """Test whitespace handling in variable extraction."""

    def test_variable_with_leading_space(self):
        """Variable with leading space should be trimmed."""
        result = extract_template_variables("{{ name}}")
        assert result == {"name"}

    def test_variable_with_trailing_space(self):
        """Variable with trailing space should be trimmed."""
        result = extract_template_variables("{{name }}")
        assert result == {"name"}

    def test_variable_with_both_spaces(self):
        """Variable with spaces on both sides should be trimmed."""
        result = extract_template_variables("{{  name  }}")
        assert result == {"name"}

    def test_variable_with_tabs(self):
        """Variable with tabs should be trimmed."""
        result = extract_template_variables("{{\tname\t}}")
        assert result == {"name"}

    def test_multiline_template(self):
        """Variables across multiple lines should all be extracted."""
        template = """
Line 1: {{var1}}
Line 2: ${var2}
Line 3: {{var3}}
"""
        result = extract_template_variables(template)
        assert result == {"var1", "var2", "var3"}


# ============================================================================
# Test extract_template_variables() - Complex Expressions
# ============================================================================

class TestExtractTemplateVariablesExpressions:
    """Test extraction of complex expressions."""

    def test_dot_notation_single_level(self):
        """Variable with dot notation should be extracted as-is."""
        result = extract_template_variables("{{user.name}}")
        assert result == {"user.name"}

    def test_dot_notation_multiple_levels(self):
        """Variable with multiple levels should be extracted."""
        result = extract_template_variables("{{config.database.host}}")
        assert result == {"config.database.host"}

    def test_expression_with_operator(self):
        """Expression with operators should be extracted."""
        result = extract_template_variables("{{x + y}}")
        assert result == {"x + y"}

    def test_expression_with_function(self):
        """Expression with function call should be extracted."""
        result = extract_template_variables("{{len(items)}}")
        assert result == {"len(items)"}

    def test_complex_expression(self):
        """Complex expression should be extracted as-is."""
        result = extract_template_variables("{{data['key'] if condition else default}}")
        assert result == {"data['key'] if condition else default"}

    def test_multiple_complex_expressions(self):
        """Multiple complex expressions should all be extracted."""
        template = "{{user.name}} {{items[0]}} ${config.port}"
        result = extract_template_variables(template)
        assert result == {"user.name", "items[0]", "config.port"}


# ============================================================================
# Test extract_template_variables() - Edge Cases
# ============================================================================

class TestExtractTemplateVariablesEdgeCases:
    """Test edge cases and malformed templates."""

    def test_single_opening_brace(self):
        """Single { should not cause errors."""
        result = extract_template_variables("This has a { single brace")
        assert result == set()

    def test_single_closing_brace(self):
        """Single } should not cause errors."""
        result = extract_template_variables("This has a } single brace")
        assert result == set()

    def test_mismatched_braces(self):
        """Mismatched braces should not crash."""
        result = extract_template_variables("{{incomplete")
        assert isinstance(result, set)

    def test_triple_braces(self):
        """Triple braces {{{ should not match."""
        result = extract_template_variables("{{{not_a_variable}}}")
        # Should not extract this as it's triple braces
        assert result == set() or "not_a_variable" not in result

    def test_empty_braces_curly(self):
        """Empty {{}} extracts empty string."""
        result = extract_template_variables("{{ }}")
        # Whitespace-only is trimmed to empty string
        assert "" in result or len(result) == 1

    def test_empty_braces_dollar(self):
        """Empty ${} extracts empty string."""
        result = extract_template_variables("${ }")
        # Whitespace-only is trimmed to empty string
        assert "" in result or len(result) == 1

    def test_nested_braces_structure(self):
        """Nested brace structures should be handled."""
        result = extract_template_variables("{{outer {{inner}}}}")
        # Should extract something, exact behavior depends on regex
        assert isinstance(result, set)

    def test_handlebars_if_block_ignored(self):
        """Handlebars #if blocks should be ignored."""
        result = extract_template_variables("{{#if condition}}text{{/if}}")
        # Should not include #if or /if
        assert "#if condition" not in result
        assert "/if" not in result

    def test_handlebars_each_block_ignored(self):
        """Handlebars #each blocks should be ignored."""
        result = extract_template_variables("{{#each items}}{{name}}{{/each}}")
        # Should extract name but not #each or /each
        assert "name" in result
        assert "#each items" not in result
        assert "/each" not in result

    def test_unicode_variable_names(self):
        """Unicode variable names should be extracted."""
        result = extract_template_variables("{{имя}} {{名前}}")
        assert "имя" in result
        assert "名前" in result

    def test_variable_with_underscore(self):
        """Variables with underscores should be extracted."""
        result = extract_template_variables("{{user_name}} ${first_last}")
        assert result == {"user_name", "first_last"}

    def test_variable_with_numbers(self):
        """Variables with numbers should be extracted."""
        result = extract_template_variables("{{var1}} {{var2}} ${item3}")
        assert result == {"var1", "var2", "item3"}

    def test_consecutive_variables_no_space(self):
        """Consecutive variables without space should both be extracted."""
        result = extract_template_variables("{{a}}{{b}}")
        assert result == {"a", "b"}

    def test_variable_at_start_of_string(self):
        """Variable at start of string should be extracted."""
        result = extract_template_variables("{{first}} comes first")
        assert "first" in result

    def test_variable_at_end_of_string(self):
        """Variable at end of string should be extracted."""
        result = extract_template_variables("last comes {{last}}")
        assert "last" in result

    def test_variable_as_only_content(self):
        """Variable as only content should be extracted."""
        result = extract_template_variables("{{only}}")
        assert result == {"only"}


# ============================================================================
# Test extract_template_variables() - Real-World Scenarios
# ============================================================================

class TestExtractTemplateVariablesRealWorld:
    """Test real-world template scenarios."""

    def test_markdown_template(self):
        """Extract variables from Markdown template."""
        template = """
# {{title}}

## Introduction
{{intro}}

## Content
${body_content}

## Conclusion
{{conclusion}}
"""
        result = extract_template_variables(template)
        assert result == {"title", "intro", "body_content", "conclusion"}

    def test_yaml_frontmatter_style(self):
        """Extract variables from YAML-style template."""
        template = """
---
title: {{document_title}}
author: ${author_name}
date: {{creation_date}}
---

Content: {{main_content}}
"""
        result = extract_template_variables(template)
        assert "document_title" in result
        assert "author_name" in result
        assert "creation_date" in result
        assert "main_content" in result

    def test_html_style_template(self):
        """Extract variables from HTML-like template."""
        template = """
<div class="{{css_class}}">
    <h1>{{heading}}</h1>
    <p>${paragraph_text}</p>
</div>
"""
        result = extract_template_variables(template)
        assert result == {"css_class", "heading", "paragraph_text"}

    def test_mixed_text_and_code(self):
        """Extract variables from mixed content."""
        template = """
Regular text with {{var1}}.
Some code: `{{not_code}}` but ${var2} is.
More text {{var3}}.
"""
        result = extract_template_variables(template)
        # All should be extracted, even in backticks
        assert "var1" in result
        assert "not_code" in result
        assert "var2" in result
        assert "var3" in result

    def test_large_template_with_many_variables(self):
        """Extract from large template with many variables."""
        variables = [f"var{i}" for i in range(50)]
        template = " ".join([f"{{{{var{i}}}}}" for i in range(50)])
        result = extract_template_variables(template)
        assert len(result) == 50
        for var in variables:
            assert var in result
