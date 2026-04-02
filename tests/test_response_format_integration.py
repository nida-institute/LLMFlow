"""Integration tests for response_format with OpenAI structured outputs.

These tests verify that LLMFlow correctly passes response_format to OpenAI's API
and receives valid JSON conforming to the schema.

Tests are SKIPPED unless OPENAI_API_KEY is set (to avoid charging during normal test runs).
"""

import os
import pytest
import json

# Skip all tests in this file unless OPENAI_API_KEY is set
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set - skipping integration tests"
)


def test_response_format_basic_json_object():
    """Test basic json_object mode (no schema)."""
    from llmflow.utils.llm_runner import call_llm

    config = {
        "model": "gpt-4o-2024-08-06",
        "max_tokens": 100,
        "temperature": 0.0,
        "response_format": {
            "type": "json_object"
        }
    }

    prompt = 'Return a JSON object with a single field "message" saying "Hello"'

    result = call_llm(prompt, config, output_type="json")

    # Should be valid JSON
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    # Should have the message field
    assert "message" in result, f"Missing 'message' field: {result}"
    assert "Hello" in result["message"] or "hello" in result["message"].lower()


def test_response_format_json_schema_simple():
    """Test json_schema mode with a simple schema."""
    from llmflow.utils.llm_runner import call_llm

    config = {
        "model": "gpt-4o-2024-08-06",
        "max_tokens": 200,
        "temperature": 0.0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "test_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "greeting": {
                            "type": "string",
                            "description": "A friendly greeting"
                        },
                        "count": {
                            "type": "integer",
                            "description": "A number between 1 and 10"
                        }
                    },
                    "required": ["greeting", "count"],
                    "additionalProperties": False
                }
            }
        }
    }

    prompt = "Return a friendly greeting and a number between 1 and 10"

    result = call_llm(prompt, config, output_type="json")

    # Verify structure matches schema
    assert isinstance(result, dict)
    assert "greeting" in result
    assert "count" in result
    assert isinstance(result["greeting"], str)
    assert isinstance(result["count"], int)
    assert 1 <= result["count"] <= 10
    # Verify no additional properties
    assert set(result.keys()) == {"greeting", "count"}


def test_response_format_json_schema_nested_array():
    """Test json_schema with nested objects and arrays."""
    from llmflow.utils.llm_runner import call_llm

    config = {
        "model": "gpt-4o-2024-08-06",
        "max_tokens": 500,
        "temperature": 0.0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "book_segmentation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "book": {"type": "string"},
                        "pericopes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "passage": {"type": "string"}
                                },
                                "required": ["title", "passage"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["book", "pericopes"],
                    "additionalProperties": False
                }
            }
        }
    }

    prompt = """Segment the book of Philemon into 2 pericopes.
For each pericope provide:
- title: A descriptive title
- passage: The verse range (e.g., "Philemon 1:1-7")
"""

    result = call_llm(prompt, config, output_type="json")

    # Verify top-level structure
    assert isinstance(result, dict)
    assert "book" in result
    assert "pericopes" in result
    assert result["book"] == "Philemon"

    # Verify array structure
    assert isinstance(result["pericopes"], list)
    assert len(result["pericopes"]) >= 1  # Should have at least 1 pericope

    # Verify each pericope has required fields
    for pericope in result["pericopes"]:
        assert isinstance(pericope, dict)
        assert "title" in pericope
        assert "passage" in pericope
        assert isinstance(pericope["title"], str)
        assert isinstance(pericope["passage"], str)
        # No additional properties
        assert set(pericope.keys()) == {"title", "passage"}


def test_response_format_prevents_hallucinated_fields():
    """Test that strict mode prevents LLM from adding unexpected fields."""
    from llmflow.utils.llm_runner import call_llm

    config = {
        "model": "gpt-4o-2024-08-06",
        "max_tokens": 150,
        "temperature": 0.0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "strict_test",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    },
                    "required": ["name"],
                    "additionalProperties": False
                }
            }
        }
    }

    # Prompt tries to get LLM to add extra fields
    prompt = """Return JSON with:
- name: "Test"
- age: 25
- country: "USA"

Only include the fields specified in the schema!
"""

    result = call_llm(prompt, config, output_type="json")

    # Should ONLY have "name" field, not age or country
    assert isinstance(result, dict)
    assert "name" in result
    assert "age" not in result, "strict mode should prevent 'age' field"
    assert "country" not in result, "strict mode should prevent 'country' field"
    assert set(result.keys()) == {"name"}


def test_response_format_reliability_no_parse_errors():
    """Test that response_format eliminates JSON parse errors.

    Run the same request 10 times to verify 100% success rate.
    Without response_format, this type of complex nested JSON has 40-60% failure rate.
    """
    from llmflow.utils.llm_runner import call_llm

    config = {
        "model": "gpt-4o-2024-08-06",
        "max_tokens": 1000,
        "temperature": 0.3,  # Some randomness to vary output
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "complex_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "themes": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "characters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "role": {"type": "string"},
                                    "quotes": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["name", "role"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["themes", "characters"],
                    "additionalProperties": False
                }
            }
        }
    }

    prompt = """Analyze Mark 10:17-22 (Rich Young Ruler).
Return:
- themes: List of 2-3 theological themes
- characters: List of 2 characters with name, role, and optional quotes (with proper escaping!)
"""

    # Run 10 times to verify reliability
    success_count = 0
    for i in range(10):
        try:
            result = call_llm(prompt, config, output_type="json")

            # Verify structure
            assert isinstance(result, dict)
            assert "themes" in result
            assert "characters" in result
            assert isinstance(result["themes"], list)
            assert isinstance(result["characters"], list)

            # Verify nested structure
            for char in result["characters"]:
                assert "name" in char
                assert "role" in char
                # quotes field is optional but if present must be array
                if "quotes" in char:
                    assert isinstance(char["quotes"], list)

            success_count += 1
        except (ValueError, AssertionError, KeyError) as e:
            # Any parse error or structure error is a failure
            print(f"Attempt {i+1} failed: {e}")

    # With response_format, should have 100% success rate
    assert success_count == 10, f"Only {success_count}/10 attempts succeeded (expected 100%)"


def test_response_format_with_escaping_edge_cases():
    """Test that response_format handles strings with quotes and special chars correctly."""
    from llmflow.utils.llm_runner import call_llm

    config = {
        "model": "gpt-4o-2024-08-06",
        "max_tokens": 300,
        "temperature": 0.0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "escaping_test",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "quote_with_double_quotes": {"type": "string"},
                        "quote_with_apostrophe": {"type": "string"},
                        "quote_with_both": {"type": "string"}
                    },
                    "required": ["quote_with_double_quotes", "quote_with_apostrophe", "quote_with_both"],
                    "additionalProperties": False
                }
            }
        }
    }

    prompt = """Return three Biblical quotes:
1. A quote containing double quotes: He said "Follow me"
2. A quote with apostrophe: Jesus' disciples
3. A quote with both: Peter said "It's the Lord!"
"""

    result = call_llm(prompt, config, output_type="json")

    # Should successfully parse despite complex escaping
    assert isinstance(result, dict)
    assert "quote_with_double_quotes" in result
    assert "quote_with_apostrophe" in result
    assert "quote_with_both" in result

    # All should be strings
    assert isinstance(result["quote_with_double_quotes"], str)
    assert isinstance(result["quote_with_apostrophe"], str)
    assert isinstance(result["quote_with_both"], str)

    # Should contain the expected characters (API handles escaping internally)
    assert '"' in result["quote_with_double_quotes"] or "quote" in result["quote_with_double_quotes"].lower()
    assert "'" in result["quote_with_apostrophe"] or "apostrophe" in result["quote_with_apostrophe"].lower()
