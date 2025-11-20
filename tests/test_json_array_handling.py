"""Test that JSON arrays from LLM responses are preserved correctly."""

import json
from llmflow.modules.json_parser import parse_llm_json_response


def test_parse_json_array_with_markdown_fences():
    """Test parsing JSON array wrapped in markdown code fences."""

    response = '''Here is the data:
```json
{
  "lemma": "ὁ",
  "total_refs": 3,
  "references": [
    {"id": 1, "reference": "Mt 8:20", "corpus": "NT"},
    {"id": 2, "reference": "Rom 5:12", "corpus": "NT"},
    {"id": 3, "reference": "Gen 2:7", "corpus": "LXX"}
  ]
}
```'''

    result = parse_llm_json_response(response)

    assert isinstance(result, dict)
    assert result["lemma"] == "ὁ"
    assert result["total_refs"] == 3
    assert len(result["references"]) == 3
    assert result["references"][0]["id"] == 1
    assert result["references"][2]["id"] == 3


def test_parse_json_array_without_fences():
    """Test parsing raw JSON array without markdown."""

    response = '''{
  "lemma": "ὁ",
  "total_refs": 3,
  "references": [
    {"id": 1, "reference": "Mt 8:20"},
    {"id": 2, "reference": "Rom 5:12"},
    {"id": 3, "reference": "Gen 2:7"}
  ]
}'''

    result = parse_llm_json_response(response)

    assert isinstance(result, dict)
    assert len(result["references"]) == 3


def test_save_json_array_to_file(tmpdir):
    """Test that JSON array is saved correctly to file."""

    data = {
        "lemma": "ὁ",
        "total_refs": 3,
        "references": [
            {"id": 1, "reference": "Mt 8:20"},
            {"id": 2, "reference": "Rom 5:12"},
            {"id": 3, "reference": "Gen 2:7"}
        ]
    }

    output_file = tmpdir.join("test.refs.json")

    # Save using json.dump (what the runner should do)
    with open(str(output_file), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Read back and verify
    with open(str(output_file)) as f:
        loaded = json.load(f)

    assert len(loaded["references"]) == 3
    assert loaded["references"][0]["id"] == 1
    assert loaded["references"][2]["id"] == 3


def test_context_variable_preserves_array():
    """Test that storing JSON in context preserves array structure."""

    context = {}

    # Simulate what runner does
    json_data = {
        "lemma": "ὁ",
        "references": [
            {"id": 1}, {"id": 2}, {"id": 3}
        ]
    }

    # Store in context
    context["reference_analysis"] = json_data

    # Retrieve from context
    retrieved = context["reference_analysis"]

    assert len(retrieved["references"]) == 3
    assert isinstance(retrieved["references"], list)