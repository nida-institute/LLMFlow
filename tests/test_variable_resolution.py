"""Comprehensive tests for variable resolution (resolve and get_from_context)."""
import pytest
from llmflow.runner import resolve, get_from_context


class MockRow:
    """Mock Row object to test database-style access patterns."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        return getattr(self, key)


class TestGetFromContext:
    """Test get_from_context function for dot notation and indexing."""

    # ===== Basic Access =====

    def test_simple_string_access(self):
        """Access a simple string value."""
        ctx = {"name": "John"}
        assert get_from_context("name", ctx) == "John"

    def test_simple_int_access(self):
        """Access a simple integer value."""
        ctx = {"age": 42}
        assert get_from_context("age", ctx) == 42

    def test_simple_bool_access(self):
        """Access a boolean value."""
        ctx = {"active": True}
        assert get_from_context("active", ctx) is True

    def test_simple_none_access(self):
        """Access None value returns None."""
        ctx = {"value": None}
        assert get_from_context("value", ctx) is None

    def test_missing_key(self):
        """Missing key returns None."""
        ctx = {"name": "John"}
        assert get_from_context("missing", ctx) is None

    def test_empty_context(self):
        """Empty context returns None."""
        assert get_from_context("anything", {}) is None

    # ===== Dot Notation =====

    def test_dot_notation_nested_dict(self):
        """Access nested dict with dot notation."""
        ctx = {"user": {"name": "Jane", "age": 30}}
        assert get_from_context("user.name", ctx) == "Jane"
        assert get_from_context("user.age", ctx) == 30

    def test_dot_notation_three_levels(self):
        """Access three levels deep."""
        ctx = {"data": {"user": {"profile": {"city": "NYC"}}}}
        assert get_from_context("data.user.profile.city", ctx) == "NYC"

    def test_dot_notation_missing_intermediate(self):
        """Missing intermediate key returns None."""
        ctx = {"user": {"name": "John"}}
        assert get_from_context("user.profile.city", ctx) is None

    def test_dot_notation_none_intermediate(self):
        """None intermediate value returns None."""
        ctx = {"user": None}
        assert get_from_context("user.name", ctx) is None

    # ===== List Indexing =====

    def test_list_index_first(self):
        """Access first element of list."""
        ctx = {"items": ["a", "b", "c"]}
        assert get_from_context("items[0]", ctx) == "a"

    def test_list_index_last(self):
        """Access last element of list."""
        ctx = {"items": ["a", "b", "c"]}
        assert get_from_context("items[2]", ctx) == "c"

    def test_list_index_out_of_bounds(self):
        """Out of bounds index returns None."""
        ctx = {"items": ["a", "b"]}
        assert get_from_context("items[5]", ctx) is None

    def test_list_index_empty_list(self):
        """Indexing empty list returns None."""
        ctx = {"items": []}
        assert get_from_context("items[0]", ctx) is None

    def test_list_index_negative_supported(self):
        """Negative indices ARE supported."""
        ctx = {"items": ["a", "b", "c"]}
        # Implementation actually supports negative indices
        result = get_from_context("items[-1]", ctx)
        assert result == "c"  # Gets last element

    # ===== Dict Key Access =====

    def test_dict_key_string_access(self):
        """Access dict with string key in brackets."""
        ctx = {"data": {"key": "value"}}
        assert get_from_context("data[key]", ctx) == "value"

    def test_dict_key_quoted_access(self):
        """Access dict with quoted key."""
        ctx = {"data": {"key": "value"}}
        assert get_from_context("data['key']", ctx) == "value"
        assert get_from_context('data["key"]', ctx) == "value"

    def test_dict_key_with_spaces(self):
        """Access dict key with spaces (quoted)."""
        ctx = {"data": {"my key": "value"}}
        assert get_from_context("data['my key']", ctx) == "value"

    def test_dict_key_missing(self):
        """Missing dict key returns None."""
        ctx = {"data": {"key": "value"}}
        assert get_from_context("data[missing]", ctx) is None

    # ===== Combined Access =====

    def test_combined_dot_and_list(self):
        """Combine dot notation and list indexing."""
        ctx = {"user": {"addresses": ["123 Main", "456 Oak"]}}
        assert get_from_context("user.addresses[0]", ctx) == "123 Main"
        assert get_from_context("user.addresses[1]", ctx) == "456 Oak"

    def test_combined_list_and_dot(self):
        """List of dicts with dot access."""
        ctx = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        assert get_from_context("users[0].name", ctx) == "Alice"
        assert get_from_context("users[1].name", ctx) == "Bob"

    def test_complex_nested_access(self):
        """Complex nested structure."""
        ctx = {
            "data": {
                "records": [
                    {"user": {"name": "John", "tags": ["admin", "user"]}},
                    {"user": {"name": "Jane", "tags": ["user"]}}
                ]
            }
        }
        assert get_from_context("data.records[0].user.name", ctx) == "John"
        assert get_from_context("data.records[0].user.tags[0]", ctx) == "admin"
        assert get_from_context("data.records[1].user.tags[0]", ctx) == "user"

    # ===== Row Objects =====

    def test_row_attribute_access(self):
        """Access Row object attributes."""
        row = MockRow(name="Alice", age=25)
        ctx = {"row": row}
        assert get_from_context("row.name", ctx) == "Alice"
        assert get_from_context("row.age", ctx) == 25

    def test_row_getitem_access(self):
        """Access Row object via __getitem__."""
        row = MockRow(name="Bob", city="NYC")
        ctx = {"row": row}
        assert get_from_context("row[name]", ctx) == "Bob"
        assert get_from_context("row['city']", ctx) == "NYC"

    def test_row_missing_attribute(self):
        """Missing Row attribute returns None."""
        row = MockRow(name="Charlie")
        ctx = {"row": row}
        assert get_from_context("row.missing", ctx) is None

    def test_list_of_rows(self):
        """Access list of Row objects."""
        rows = [MockRow(id=1, name="A"), MockRow(id=2, name="B")]
        ctx = {"rows": rows}
        assert get_from_context("rows[0].name", ctx) == "A"
        assert get_from_context("rows[1].id", ctx) == 2

    # ===== Edge Cases =====

    def test_numeric_string_key(self):
        """Dict key that looks like a number."""
        ctx = {"data": {"123": "value"}}
        # Implementation tries int first, so this might not work as expected
        # This is a known limitation
        result = get_from_context("data[123]", ctx)
        # Since data is a dict and 123 is parsed as int, this fails
        assert result is None

    def test_empty_brackets(self):
        """Empty brackets return None."""
        ctx = {"data": [1, 2, 3]}
        # Invalid syntax - implementation regex won't match
        result = get_from_context("data[]", ctx)
        assert result is None

    def test_special_characters_in_key(self):
        """Keys with underscores and numbers."""
        ctx = {"my_var_123": "value"}
        assert get_from_context("my_var_123", ctx) == "value"

    def test_nested_none_value(self):
        """Nested structure with None value."""
        ctx = {"data": {"value": None}}
        assert get_from_context("data.value", ctx) is None


class TestResolve:
    """Test resolve function for variable substitution."""

    # ===== String Literal Returns =====

    def test_no_variables(self):
        """String without variables returns unchanged."""
        assert resolve("Hello World", {}) == "Hello World"

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert resolve("", {}) == ""

    def test_non_string_passthrough(self):
        """Non-string primitives pass through."""
        assert resolve(42, {}) == 42
        assert resolve(True, {}) is True
        assert resolve(None, {}) is None

    # ===== Dollar Syntax ${...} =====

    def test_dollar_exact_match_string(self):
        """Exact ${var} match returns native string."""
        ctx = {"name": "Alice"}
        assert resolve("${name}", ctx) == "Alice"

    def test_dollar_exact_match_int(self):
        """Exact ${var} match returns native int."""
        ctx = {"count": 42}
        result = resolve("${count}", ctx)
        assert result == 42
        assert isinstance(result, int)

    def test_dollar_exact_match_list(self):
        """Exact ${var} match returns native list."""
        ctx = {"items": [1, 2, 3]}
        result = resolve("${items}", ctx)
        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_dollar_exact_match_dict(self):
        """Exact ${var} match returns native dict."""
        ctx = {"data": {"key": "value"}}
        result = resolve("${data}", ctx)
        assert result == {"key": "value"}
        assert isinstance(result, dict)

    def test_dollar_in_string(self):
        """${var} in string performs string substitution."""
        ctx = {"name": "Bob"}
        assert resolve("Hello ${name}!", ctx) == "Hello Bob!"

    def test_dollar_multiple_in_string(self):
        """Multiple ${var} in one string."""
        ctx = {"first": "John", "last": "Doe"}
        assert resolve("${first} ${last}", ctx) == "John Doe"

    def test_dollar_missing_var(self):
        """Missing variable leaves placeholder unchanged."""
        ctx = {"name": "Alice"}
        assert resolve("${missing}", ctx) == "${missing}"

    def test_dollar_dot_notation(self):
        """${var.field} with dot notation."""
        ctx = {"user": {"name": "Charlie"}}
        assert resolve("${user.name}", ctx) == "Charlie"

    def test_dollar_list_index(self):
        """${var[0]} with list indexing."""
        ctx = {"items": ["first", "second"]}
        assert resolve("${items[0]}", ctx) == "first"

    # ===== Curly Syntax {...} =====

    def test_curly_exact_match_string(self):
        """Exact {var} match returns native string."""
        ctx = {"name": "Dave"}
        assert resolve("{name}", ctx) == "Dave"

    def test_curly_exact_match_list(self):
        """Exact {var} match returns native list."""
        ctx = {"nums": [10, 20]}
        result = resolve("{nums}", ctx)
        assert result == [10, 20]
        assert isinstance(result, list)

    def test_curly_in_string(self):
        """{var} in string performs string substitution."""
        ctx = {"city": "NYC"}
        assert resolve("Welcome to {city}", ctx) == "Welcome to NYC"

    def test_curly_multiple(self):
        """Multiple {var} in one string."""
        ctx = {"x": 1, "y": 2}
        assert resolve("{x} + {y}", ctx) == "1 + 2"

    def test_curly_dot_notation(self):
        """{var.field} with dot notation."""
        ctx = {"data": {"status": "ok"}}
        assert resolve("{data.status}", ctx) == "ok"

    # ===== Mixed Syntax =====

    def test_mixed_dollar_and_curly(self):
        """Mix ${var} and {var} in same string."""
        ctx = {"a": "alpha", "b": "beta"}
        assert resolve("${a} and {b}", ctx) == "alpha and beta"

    def test_dollar_and_curly_exact_match(self):
        """Only one syntax should match for exact replacement."""
        ctx = {"x": 42}
        # Exact match tries ${...} first
        assert resolve("${x}", ctx) == 42

    # ===== Nested Structures =====

    def test_resolve_dict(self):
        """Resolve variables in dict values."""
        ctx = {"name": "Eve", "age": 30}
        input_dict = {"greeting": "Hello ${name}", "info": "Age: ${age}"}
        result = resolve(input_dict, ctx)
        assert result == {"greeting": "Hello Eve", "info": "Age: 30"}

    def test_resolve_list(self):
        """Resolve variables in list items."""
        ctx = {"prefix": "Item"}
        input_list = ["${prefix} 1", "${prefix} 2"]
        result = resolve(input_list, ctx)
        assert result == ["Item 1", "Item 2"]

    def test_resolve_nested_dict(self):
        """Resolve variables in nested dict."""
        ctx = {"user": "Frank", "role": "admin"}
        input_dict = {
            "outer": {
                "name": "${user}",
                "permissions": "${role}"
            }
        }
        result = resolve(input_dict, ctx)
        assert result["outer"]["name"] == "Frank"
        assert result["outer"]["permissions"] == "admin"

    def test_resolve_list_of_dicts(self):
        """Resolve variables in list of dicts."""
        ctx = {"status": "active"}
        input_list = [
            {"id": 1, "state": "${status}"},
            {"id": 2, "state": "${status}"}
        ]
        result = resolve(input_list, ctx)
        assert result[0]["state"] == "active"
        assert result[1]["state"] == "active"

    def test_resolve_dict_with_exact_match_values(self):
        """Dict values with exact matches return native types."""
        ctx = {"items": [1, 2, 3], "count": 5}
        input_dict = {"list": "${items}", "num": "${count}"}
        result = resolve(input_dict, ctx)
        assert result["list"] == [1, 2, 3]
        assert isinstance(result["list"], list)
        assert result["num"] == 5
        assert isinstance(result["num"], int)

    # ===== Recursive Resolution =====

    def test_recursive_resolution_one_level(self):
        """Variable points to another variable."""
        ctx = {"indirect": "${direct}", "direct": "value"}
        assert resolve("${indirect}", ctx) == "value"

    def test_recursive_resolution_two_levels(self):
        """Two levels of indirection."""
        ctx = {
            "level1": "${level2}",
            "level2": "${level3}",
            "level3": "final"
        }
        assert resolve("${level1}", ctx) == "final"

    def test_recursive_resolution_max_depth(self):
        """Max depth prevents infinite recursion."""
        # Create circular reference
        ctx = {"a": "${b}", "b": "${c}", "c": "${d}", "d": "${e}", "e": "${f}", "f": "${a}"}
        # Should stop at max_depth (default 5) and return the templated string
        result = resolve("${a}", ctx)
        # After 5 iterations, should still be a template string
        assert "${" in result

    def test_recursive_with_curly_syntax(self):
        """Recursive resolution works with {curly} syntax."""
        ctx = {"var1": "{var2}", "var2": "result"}
        assert resolve("{var1}", ctx) == "result"

    # ===== None Handling =====

    def test_none_value_in_context(self):
        """None value in context returns placeholder (not resolved)."""
        ctx = {"value": None}
        # get_from_context returns None, so resolve condition 'resolved is not None' fails
        # and the placeholder is left unchanged
        assert resolve("${value}", ctx) == "${value}"

    def test_none_value_in_string(self):
        """None value in string leaves placeholder unchanged."""
        ctx = {"value": None}
        result = resolve("Value is ${value}", ctx)
        # Since get_from_context returns None, the condition fails and placeholder stays
        assert result == "Value is ${value}"

    def test_resolve_none_directly(self):
        """Resolving None returns None."""
        assert resolve(None, {}) is None

    # ===== Complex Scenarios =====

    def test_complex_nested_resolution(self):
        """Complex nested dict and list resolution."""
        ctx = {
            "user": {"name": "George", "id": 123},
            "items": ["a", "b", "c"]
        }
        input_data = {
            "profile": {
                "username": "${user.name}",
                "userId": "${user.id}",
                "tags": ["${items[0]}", "${items[1]}"]
            }
        }
        result = resolve(input_data, ctx)
        assert result["profile"]["username"] == "George"
        assert result["profile"]["userId"] == 123
        assert result["profile"]["tags"] == ["a", "b"]

    def test_row_objects_in_context(self):
        """Resolve with Row objects in context."""
        row = MockRow(name="Helen", score=95)
        ctx = {"record": row}
        assert resolve("${record.name}", ctx) == "Helen"
        assert resolve("Score: ${record.score}", ctx) == "Score: 95"

    def test_deeply_nested_structure(self):
        """Very deep nesting (4+ levels)."""
        ctx = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep"
                        }
                    }
                }
            }
        }
        assert resolve("${level1.level2.level3.level4.value}", ctx) == "deep"

    def test_list_in_list_access(self):
        """Nested list access."""
        ctx = {"matrix": [[1, 2], [3, 4]]}
        assert resolve("${matrix[0][0]}", ctx) == "${matrix[0][0]}"  # Single bracket level only
        # Need to do it in two steps
        assert resolve("${matrix[0]}", ctx) == [1, 2]

    # ===== Edge Cases =====

    def test_empty_context(self):
        """Empty context leaves variables unchanged."""
        assert resolve("${anything}", {}) == "${anything}"

    def test_malformed_template(self):
        """Malformed template syntax."""
        ctx = {"var": "value"}
        # Missing closing brace
        assert resolve("${var", ctx) == "${var"
        # Missing opening brace
        assert resolve("var}", ctx) == "var}"

    def test_escaped_braces_not_supported(self):
        """Literal braces (no escape mechanism in implementation)."""
        # Implementation has no escape mechanism
        assert resolve("$${var}", {}) == "$${var}"

    def test_whitespace_in_template(self):
        """Whitespace around variable name."""
        ctx = {"var": "value"}
        # Implementation doesn't strip whitespace in the pattern
        result = resolve("${ var }", ctx)
        # This will try to look up " var " which won't match "var"
        assert result == "${ var }"

    def test_special_characters_ignored(self):
        """Special characters in non-template parts."""
        ctx = {"var": "test"}
        assert resolve("@#$%^&*() ${var}", ctx) == "@#$%^&*() test"

    def test_boolean_in_string(self):
        """Boolean values in string substitution."""
        ctx = {"flag": True, "off": False}
        assert resolve("Flag is ${flag}", ctx) == "Flag is True"
        assert resolve("Off is ${off}", ctx) == "Off is False"

    def test_float_values(self):
        """Float values in resolution."""
        ctx = {"pi": 3.14159}
        assert resolve("${pi}", ctx) == 3.14159
        assert resolve("Pi is ${pi}", ctx) == "Pi is 3.14159"


class TestStarWildcardResolution:
    """Tests for ${list[*].field} wildcard extraction.

    Semantics: when [*] is encountered, the *remaining path* after [*] is
    applied to each element via recursive get_from_context(), and the results
    are collected into a flat list at that depth.  This means:

        get_from_context("items[*].a.b[0].c", ctx)
        # equivalent to: [get_from_context("a.b[0].c", item) for item in ctx["items"]]

    Used in production pipelines:
      - storyflow-psalms.yaml:           ${scene_list[*].Title}
      - storyflow-gospels.yaml:          ${scene_list[*].Title}
      - storyflow-gospels-combined.yaml: ${scene_list[*].Title}
    """

    def test_star_extracts_field_from_list(self):
        """get_from_context('list[*].field') returns a list of field values."""
        ctx = {"scene_list": [
            {"Title": "Arrival"},
            {"Title": "Conflict"},
            {"Title": "Resolution"},
        ]}
        result = get_from_context("scene_list[*].Title", ctx)
        assert result == ["Arrival", "Conflict", "Resolution"]

    def test_star_via_resolve_returns_list(self):
        """resolve('${list[*].field}') returns native list."""
        ctx = {"scene_list": [{"Title": "Scene A"}, {"Title": "Scene B"}]}
        result = resolve("${scene_list[*].Title}", ctx)
        assert result == ["Scene A", "Scene B"]

    def test_star_empty_list(self):
        """[*] on an empty list returns []."""
        ctx = {"items": []}
        result = get_from_context("items[*].name", ctx)
        assert result == []

    def test_star_missing_field_none_filled(self):
        """[*] on items missing the target field None-fills that slot."""
        ctx = {"items": [{"name": "a"}, {"other": "b"}, {"name": "c"}]}
        result = get_from_context("items[*].name", ctx)
        assert result == ["a", None, "c"]

    def test_star_deep_path_with_index(self):
        """[*] with multiple remaining segments including a numeric index.

        Pattern: list[*].nested[0].field
        Equivalent Python: [item["nested"][0]["field"] for item in list]

        This covers the real-world case:
            pericope_results[*].segments[0].boundary_signals
        """
        ctx = {
            "pericope_results": [
                {"segments": [{"boundary_signals": "high", "score": 0.9}, {"boundary_signals": "low"}]},
                {"segments": [{"boundary_signals": "medium", "score": 0.5}]},
                {"segments": [{"boundary_signals": "none", "score": 0.1}]},
            ]
        }
        result = get_from_context("pericope_results[*].segments[0].boundary_signals", ctx)
        assert result == ["high", "medium", "none"]

    def test_star_deep_path_missing_index(self):
        """[*] deep path where one item's nested index is out of bounds → None for that slot."""
        ctx = {
            "items": [
                {"parts": [{"val": "a"}, {"val": "b"}]},
                {"parts": []},          # no index 0
                {"parts": [{"val": "c"}]},
            ]
        }
        result = get_from_context("items[*].parts[0].val", ctx)
        assert result == ["a", None, "c"]
