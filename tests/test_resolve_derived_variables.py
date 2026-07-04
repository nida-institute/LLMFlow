"""
Tests for resolve() with derived/nested variables — variables whose stored
values themselves reference other variables via ${...} syntax.

These cases arise in pipeline YAML when a variable declaration builds on
another declared variable:

    variables:
      base_dir: "outputs/intermediate"
      sub_dir: "${base_dir}/build-book"            # derived, 1 level
      path_prefix: "${sub_dir}/${item.code}"       # derived, 2 levels

These tests also guard against the two-pass regex bug: the second
re.sub(r"\\{...\\}") matching bare {var} fragments left behind by the first
pass when nested tokens are not fully expanded.
"""
import pytest
from llmflow.utils.context import resolve


# ---------------------------------------------------------------------------
# Single-level derived variable
# ---------------------------------------------------------------------------

def test_resolve_single_derived_variable():
    """Variable whose value references another variable is fully resolved."""
    context = {
        "base_dir": "outputs/intermediate",
        "sub_dir": "${base_dir}/build-book",
    }
    result = resolve("${sub_dir}/file.json", context)
    assert result == "outputs/intermediate/build-book/file.json"


def test_resolve_derived_variable_embedded_in_string():
    """Derived variable in the middle of an interpolated string."""
    context = {
        "base_dir": "outputs/intermediate",
        "sub_dir": "${base_dir}/book-summaries",
    }
    result = resolve("prefix/${sub_dir}/suffix.md", context)
    assert result == "prefix/outputs/intermediate/book-summaries/suffix.md"


# ---------------------------------------------------------------------------
# Two-level derived variable chain
# ---------------------------------------------------------------------------

def test_resolve_two_tier_derived_variable():
    """Two levels of derived variable references are fully resolved.

    Mirrors the build-book.yaml pattern:
        book_output_dir: "${output_file_directory}/${book_ref.book_number}-${book_ref.book_code}"
        book_output_prefix: "${book_output_dir}/${book_ref.book_number}-${book_ref.book_code}"
    """
    context = {
        "output_file_directory": "outputs/book-summaries",
        "book_ref": {"book_number": "57", "book_code": "PHM"},
        "book_output_dir": "${output_file_directory}/${book_ref.book_number}-${book_ref.book_code}",
        "book_output_prefix": "${book_output_dir}/${book_ref.book_number}-${book_ref.book_code}",
    }
    result = resolve("${book_output_prefix}-book-summary.json", context)
    assert result == "outputs/book-summaries/57-PHM/57-PHM-book-summary.json"


def test_resolve_two_tier_intermediate_dir():
    """Two-tier chain for intermediate_build_book_dir mirrors the actual failure case."""
    context = {
        "intermediate_file_directory": "outputs/intermediate",
        "book_ref": {"book_number": "57", "book_code": "PHM"},
        "intermediate_build_book_dir": "${intermediate_file_directory}/build-book/${book_ref.book_number}-${book_ref.book_code}",
    }
    # Exact saveas pattern from build-book.yaml bodies step
    result = resolve("${intermediate_build_book_dir}/bodies/1.json", context)
    assert result == "outputs/intermediate/build-book/57-PHM/bodies/1.json"


# ---------------------------------------------------------------------------
# Regression: second-pass bare {var} regex must not corrupt ${var} tokens
# ---------------------------------------------------------------------------

def test_second_pass_does_not_leave_dollar_prefix():
    """Bare {var} regex pass must not strip braces from ${var}, leaving a bare $.

    Before the fix, ${inner_var} tokens introduced by the first pass were
    partially matched by the second re.sub(r"\\{...\\}"), which resolved the
    inner name but left the $ behind, producing $57 instead of 57.
    """
    context = {
        "outer": "${inner}",
        "inner": "resolved",
    }
    result = resolve("path/${outer}/file.txt", context)
    assert result == "path/resolved/file.txt"
    assert "$" not in result, f"Stray $ found in result: {result!r}"


def test_nested_dollar_var_in_interpolated_string():
    """${var} token that expands to a string containing ${other} is fully resolved."""
    context = {
        "dir": "outputs/${env}",
        "env": "production",
    }
    result = resolve("base/${dir}/data.json", context)
    assert result == "base/outputs/production/data.json"


# ---------------------------------------------------------------------------
# Bare {curly} syntax must still work (not broken by the fix)
# ---------------------------------------------------------------------------

def test_bare_curly_syntax_still_resolves():
    """Bare {var} syntax (without $) must still resolve from context."""
    context = {"name": "Alice"}
    result = resolve("{name} logged in", context)
    assert result == "Alice logged in"


def test_bare_curly_mixed_with_dollar_curly():
    """Mix of {var} and ${var} in one string both resolve correctly."""
    context = {"first": "foo", "second": "bar"}
    result = resolve("${first}-{second}", context)
    assert result == "foo-bar"


# ---------------------------------------------------------------------------
# Direct exact-match path with nested value
# ---------------------------------------------------------------------------

def test_exact_match_with_nested_value():
    """Exact ${var} reference whose value is itself a derived reference."""
    context = {
        "base": "outputs",
        "path": "${base}/data",
    }
    result = resolve("${path}", context)
    assert result == "outputs/data"


def test_exact_match_chain_three_levels():
    """Three-level chain fully resolves through exact-match recursive path."""
    context = {
        "root": "outputs",
        "mid": "${root}/middle",
        "leaf": "${mid}/leaf",
    }
    result = resolve("${leaf}", context)
    assert result == "outputs/middle/leaf"
