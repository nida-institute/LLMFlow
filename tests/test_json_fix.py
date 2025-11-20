"""Test the JSON parser greedy regex fix."""

from llmflow.modules.json_parser import parse_llm_json_response


def test_full_nested_structure():
    """Test parsing full nested JSON with array."""
    response = """{
  "lemma": "ὁ",
  "total_refs": 3,
  "references": [
    {"id": 1, "reference": "Mt 8:20"},
    {"id": 2, "reference": "Rom 5:12"},
    {"id": 3, "reference": "Gen 2:7"}
  ]
}"""

    result = parse_llm_json_response(response)

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert 'lemma' in result, "Missing 'lemma' key"
    assert 'references' in result, "Missing 'references' key"
    assert len(result['references']) == 3, f"Expected 3 references, got {len(result['references'])}"


def test_json_with_surrounding_text():
    """Test parsing JSON embedded in text."""
    response = """Here is the analysis:

{
  "lemma": "ὁ",
  "total_refs": 2,
  "references": [
    {"id": 1, "reference": "Mt 8:20"},
    {"id": 2, "reference": "Rom 5:12"}
  ]
}

Done!"""

    result = parse_llm_json_response(response)

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert 'references' in result, "Missing 'references' key"
    assert len(result['references']) == 2, f"Expected 2 references, got {len(result['references'])}"


def test_single_object():
    """Test parsing single JSON object still works."""
    response = """{"id": 2, "reference": "1 Corinthians 7:7", "corpus": "NT"}"""

    result = parse_llm_json_response(response)

    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert 'id' in result, "Missing 'id' key"
    assert result['id'] == 2, f"Expected id=2, got {result['id']}"