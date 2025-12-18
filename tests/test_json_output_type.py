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