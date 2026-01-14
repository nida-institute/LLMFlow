import pytest
from llmflow.modules.json_parser import parse_llm_json_response


def test_parse_json_string_wrapped_in_quotes():
    """Test the actual bug - JSON returned as a quoted string."""
    # This is what was saved to the file
    text = '"[{\\"Scene number\\": \\"Scene 1\\"}, {\\"Scene number\\": \\"Scene 2\\"}]"'
    result = parse_llm_json_response(text)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["Scene number"] == "Scene 1"


def test_parse_empty_structures():
    """Test empty JSON structures."""
    assert parse_llm_json_response("{}") == {}
    assert parse_llm_json_response("[]") == []
    assert parse_llm_json_response("```json\n{}\n```") == {}


def test_parse_json_with_all_value_types():
    """Test JSON with booleans, null, numbers."""
    text = """{
        "string": "value",
        "int": 42,
        "float": 3.14,
        "negative": -10,
        "bool_true": true,
        "bool_false": false,
        "null_value": null,
        "array": [1, 2, 3],
        "nested": {"key": "value"}
    }"""
    result = parse_llm_json_response(text)
    assert result["int"] == 42
    assert result["float"] == 3.14
    assert result["bool_true"] is True
    assert result["null_value"] is None


def test_parse_deeply_nested_arrays():
    """Test deeply nested array structures."""
    text = """{
        "scenes": [
            {
                "translations": {
                    "SBLGNT": "text",
                    "versions": [
                        {"name": "BSB", "text": "English"}
                    ]
                }
            }
        ]
    }"""
    result = parse_llm_json_response(text)
    assert result["scenes"][0]["translations"]["versions"][0]["name"] == "BSB"


def test_parse_json_with_unicode():
    """Test JSON with Greek/Hebrew text."""
    text = '{"greek": "Καὶ ἐγένετο", "hebrew": "בְּרֵאשִׁית"}'
    result = parse_llm_json_response(text)
    assert result["greek"] == "Καὶ ἐγένετο"
    assert result["hebrew"] == "בְּרֵאשִׁית"


def test_parse_invalid_json_raises_error():
    """Invalid JSON raises ValueError to trigger retry logic."""
    with pytest.raises(ValueError, match="JSON parse failed"):
        parse_llm_json_response('{"incomplete":')

    with pytest.raises(ValueError, match="JSON parse failed"):
        parse_llm_json_response('{"unterminated": "string')

    with pytest.raises(ValueError, match="JSON parse failed"):
        parse_llm_json_response("not json at all")


def test_parse_json_with_markdown_fence_variants():
    """Test various markdown fence formats."""
    # With language identifier
    assert parse_llm_json_response('```json\n{"key": "value"}\n```') == {"key": "value"}

    # Without language identifier
    assert parse_llm_json_response('```\n{"key": "value"}\n```') == {"key": "value"}

    # With extra whitespace
    assert parse_llm_json_response('```json  \n  {"key": "value"}  \n```') == {"key": "value"}


def test_parse_json_with_surrounding_prose():
    """Test JSON embedded in explanatory text."""
    text = """Here is the JSON response:
```json
{"result": "success", "count": 3}
```
That's the output from the API."""
    result = parse_llm_json_response(text)
    assert result == {"result": "success", "count": 3}


def test_parse_json_with_escaped_characters():
    """Test JSON with escaped characters in strings."""
    text = r'{"message": "Line 1\nLine 2\tTabbed", "path": "C:\\Users\\file.txt"}'
    result = parse_llm_json_response(text)
    assert "Line 1\nLine 2" in result["message"]
    assert result["path"] == "C:\\Users\\file.txt"


def test_parse_json_array_of_primitives():
    """Test arrays containing only primitives."""
    assert parse_llm_json_response('[1, 2, 3]') == [1, 2, 3]
    assert parse_llm_json_response('["a", "b", "c"]') == ["a", "b", "c"]
    assert parse_llm_json_response('[true, false, null]') == [True, False, None]


def test_parse_json_with_scientific_notation():
    """Test numbers in scientific notation."""
    text = '{"small": 1.5e-10, "large": 3.2e8}'
    result = parse_llm_json_response(text)
    assert result["small"] == 1.5e-10
    assert result["large"] == 3.2e8


def test_parse_triple_encoded_json():
    """Test edge case of triple-encoded JSON (shouldn't happen, but be defensive)."""
    # Double-encoded is handled, but triple would need recursive parsing
    text = '"\\"[{\\\\\\"id\\\\\\": 1}]\\""'
    result = parse_llm_json_response(text)
    # Should at least return something parseable or the cleaned string
    assert result is not None


def test_fence_with_multiple_newlines():
    """Test fence with excessive newlines before JSON."""
    text = "```json\n\n\n\n{\"key\": \"value\"}\n```"
    result = parse_llm_json_response(text)
    assert result == {"key": "value"}


def test_fence_with_leading_trailing_spaces():
    """Test fence markers with spaces and tabs."""
    text = "  ```json  \n  {\"key\": \"value\"}  \n  ```  "
    result = parse_llm_json_response(text)
    assert result == {"key": "value"}


def test_fence_with_trailing_content():
    """Test JSON fence followed by explanatory text."""
    text = """```json
{"result": "success"}
```
The above JSON shows the result."""
    result = parse_llm_json_response(text)
    assert result == {"result": "success"}


def test_fence_with_leading_content():
    """Test explanatory text before JSON fence."""
    text = """Here's the output:
```json
{"status": "ok"}
```"""
    result = parse_llm_json_response(text)
    assert result == {"status": "ok"}


def test_fence_uppercase_language():
    """Test fence with uppercase JSON language tag."""
    text = "```JSON\n{\"key\": \"value\"}\n```"
    result = parse_llm_json_response(text)
    assert result == {"key": "value"}


def test_fence_with_extra_language_chars():
    """Test fence with extra characters after json tag."""
    # Some LLMs might add extra chars - should still work if regex is flexible
    text = "```json \n{\"key\": \"value\"}\n```"
    result = parse_llm_json_response(text)
    assert result == {"key": "value"}


def test_json_with_backticks_in_strings():
    """Test JSON containing literal backtick characters in string values."""
    text = '{"code": "Use \\`backticks\\` for code", "command": "\\`ls -la\\`"}'
    result = parse_llm_json_response(text)
    assert result["code"] == "Use `backticks` for code"
    assert result["command"] == "`ls -la`"


def test_fenced_json_array_multiline():
    """Test fenced JSON array with proper formatting."""
    text = """```json
[
  {"id": 1, "name": "first"},
  {"id": 2, "name": "second"}
]
```"""
    result = parse_llm_json_response(text)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "first"


def test_multiple_fenced_blocks():
    """Test text with multiple fenced blocks - should extract first."""
    text = """```json
{"first": true}
```

Some text

```json
{"second": true}
```"""
    result = parse_llm_json_response(text)
    # Should get the first block
    assert result == {"first": True}


def test_fence_with_windows_line_endings():
    """Test fence with Windows-style CRLF line endings."""
    text = "```json\r\n{\"key\": \"value\"}\r\n```"
    result = parse_llm_json_response(text)
    assert result == {"key": "value"}


def test_fence_no_closing_backticks():
    """Test JSON with opening fence but missing closing fence."""
    text = "```json\n{\"key\": \"value\"}"
    result = parse_llm_json_response(text)
    # Should still parse the JSON even without closing fence
    assert result == {"key": "value"}


def test_deeply_nested_json_in_fence():
    """Test deeply nested JSON structure in fence."""
    text = """```json
{
  "level1": {
    "level2": {
      "level3": {
        "value": "deep"
      }
    }
  }
}
```"""
    result = parse_llm_json_response(text)
    assert result["level1"]["level2"]["level3"]["value"] == "deep"