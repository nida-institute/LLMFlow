import json
import shutil
import tempfile
from pathlib import Path

import pytest

from llmflow.runner import run_pipeline, handle_step_outputs


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_saveas_json_from_dict(temp_output_dir):
    """Test saving a Python dict as JSON (normal case)"""
    pipeline_yaml = f"""
name: test-dict-pipeline
steps:
  - name: create-dict
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value:
        name: "test"
        count: 42
    outputs:
      - data
    saveas: "{temp_output_dir}/dict.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "dict.json"
    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    assert data == {"name": "test", "count": 42}


def test_saveas_json_string_from_xslt(temp_output_dir):
    """Test saving already-serialized JSON string (XSLT case)"""
    pipeline_yaml = f"""
name: test-xslt-pipeline
steps:
  - name: create-json-string
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: '{{"segments": [{{"text": "hello"}}], "lemma": "test"}}'
    outputs:
      - json_string
    saveas: "{temp_output_dir}/xslt.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "xslt.json"
    assert output_file.exists()

    content = output_file.read_text()

    assert '\\"segments\\"' not in content, "JSON should not be double-encoded"

    data = json.loads(content)
    assert data["lemma"] == "test"
    assert len(data["segments"]) == 1


def test_saveas_json_double_encoded_string(temp_output_dir):
    """Test unwrapping double-encoded JSON (regression test)"""
    inner_json = '{"key": "value"}'
    double_encoded = json.dumps(inner_json)

    pipeline_yaml = f"""
name: test-double-encoded-pipeline
steps:
  - name: create-double-encoded
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: {double_encoded}
    outputs:
      - data
    saveas: "{temp_output_dir}/double.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "double.json"
    content = output_file.read_text()

    # FIX: Expect indented JSON, not compact
    expected = '''{
  "key": "value"
}'''
    assert content.strip() == expected, "Should unwrap double-encoded JSON with proper indentation"

    # Also verify it's valid JSON
    data = json.loads(content)
    assert data == {"key": "value"}


def test_saveas_json_with_unicode(temp_output_dir):
    """Test JSON string with unicode characters"""
    json_string = '{"lemma": "ὁ", "text": "ἀγάπη"}'

    pipeline_yaml = f"""
name: test-unicode-pipeline
steps:
  - name: create-unicode-json
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: '{json_string}'
    outputs:
      - data
    saveas: "{temp_output_dir}/unicode.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "unicode.json"
    content = output_file.read_text(encoding="utf-8")

    assert "ὁ" in content
    assert "ἀγάπη" in content
    assert "\\u" not in content


def test_saveas_json_list_from_function(temp_output_dir):
    """Test saving a Python list as JSON"""
    pipeline_yaml = f"""
name: test-list-pipeline
steps:
  - name: create-list
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value:
        - first: 1
        - second: 2
    outputs:
      - items
    saveas: "{temp_output_dir}/list.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "list.json"
    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 2


def test_saveas_json_nested_structures(temp_output_dir):
    """Test complex nested JSON structures"""
    complex_json = json.dumps({
        "segments": [
            {"id": 1, "text": "test", "meta": {"pos": "noun"}},
            {"id": 2, "text": "data", "meta": {"pos": "verb"}},
        ],
        "etymology": {"root": "test-root", "language": "Greek"},
    })

    pipeline_yaml = f"""
name: test-complex-pipeline
steps:
  - name: create-complex
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: {complex_json}
    outputs:
      - data
    saveas: "{temp_output_dir}/complex.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "complex.json"
    with open(output_file) as f:
        data = json.load(f)

    assert len(data["segments"]) == 2
    assert data["etymology"]["language"] == "Greek"


def test_saveas_txt_extension_no_json_processing(temp_output_dir):
    """Test that .txt extension doesn't trigger JSON processing"""
    json_string = '{"key": "value"}'

    pipeline_yaml = f"""
name: test-txt-pipeline
steps:
  - name: save-as-txt
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: '{json_string}'
    outputs:
      - data
    saveas: "{temp_output_dir}/data.txt"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "data.txt"
    content = output_file.read_text()

    assert content == json_string


def test_saveas_json_with_subdirectory(temp_output_dir):
    """Test saving JSON to a subdirectory that doesn't exist yet"""
    pipeline_yaml = f"""
name: test-subdirectory-pipeline
steps:
  - name: create-with-subdir
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value:
        nested: true
    outputs:
      - data
    saveas: "{temp_output_dir}/subdir/nested.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "subdir" / "nested.json"
    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    assert data["nested"] is True


def test_saveas_markdown_extension(temp_output_dir):
    """Test saving markdown content"""
    markdown_content = "# Test Heading\n\nParagraph text."

    # Use YAML block scalar with |- to strip trailing newline
    pipeline_yaml = f"""
name: test-markdown-pipeline
steps:
  - name: save-markdown
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: |-
        # Test Heading

        Paragraph text.
    outputs:
      - content
    saveas: "{temp_output_dir}/output.md"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "output.md"
    content = output_file.read_text()

    assert content == markdown_content


def test_saveas_json_format_validation(temp_output_dir):
    """Test that JSON files are properly formatted with double quotes"""
    pipeline_yaml = f"""
name: test-json-format-pipeline
steps:
  - name: create-data
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value:
        key: "value"
        number: 123
    outputs:
      - data
    saveas: "{temp_output_dir}/formatted.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "formatted.json"
    content = output_file.read_text()

    # Should use double quotes, not single quotes
    assert '"key"' in content
    assert "'key'" not in content

    # Should be valid JSON
    data = json.loads(content)
    assert data["key"] == "value"
    assert data["number"] == 123


def test_saveas_preserves_newlines(temp_output_dir):
    """Test that multiline text preserves newlines"""
    text_with_newlines = "Line 1\nLine 2\nLine 3"

    pipeline_yaml = f"""
name: test-newlines-pipeline
steps:
  - name: save-multiline
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: |
        Line 1
        Line 2
        Line 3
    outputs:
      - text
    saveas: "{temp_output_dir}/multiline.txt"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "multiline.txt"
    content = output_file.read_text()

    assert content.count('\n') >= 2  # At least 2 newlines


def test_saveas_empty_string(temp_output_dir):
    """Test saving an empty string"""
    pipeline_yaml = f"""
name: test-empty-pipeline
steps:
  - name: save-empty
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: ""
    outputs:
      - text
    saveas: "{temp_output_dir}/empty.txt"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "empty.txt"
    assert output_file.exists()
    assert output_file.read_text() == ""


def test_saveas_boolean_values_in_json(temp_output_dir):
    """Test that Python booleans are properly converted to JSON"""
    pipeline_yaml = f"""
name: test-boolean-pipeline
steps:
  - name: save-booleans
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value:
        active: true
        disabled: false
        nothing: null
    outputs:
      - flags
    saveas: "{temp_output_dir}/booleans.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "booleans.json"
    content = output_file.read_text()

    # JSON uses lowercase true/false, not Python's True/False
    assert "true" in content
    assert "false" in content
    assert "null" in content
    assert "True" not in content
    assert "False" not in content
    assert "None" not in content


def test_saveas_number_types_in_json(temp_output_dir):
    """Test various number types in JSON"""
    pipeline_yaml = f"""
name: test-numbers-pipeline
steps:
  - name: save-numbers
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value:
        integer: 42
        float_val: 3.14159
        negative: -100
        zero: 0
    outputs:
      - numbers
    saveas: "{temp_output_dir}/numbers.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "numbers.json"
    with open(output_file) as f:
        data = json.load(f)

    assert data["integer"] == 42
    assert data["float_val"] == 3.14159
    assert data["negative"] == -100
    assert data["zero"] == 0


def test_saveas_empty_json_array(temp_output_dir):
    """Test saving an empty JSON array"""
    pipeline_yaml = f"""
name: test-empty-array-pipeline
steps:
  - name: save-empty-array
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: []
    outputs:
      - items
    saveas: "{temp_output_dir}/empty_array.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "empty_array.json"
    with open(output_file) as f:
        data = json.load(f)

    assert data == []
    assert isinstance(data, list)


def test_saveas_empty_json_object(temp_output_dir):
    """Test saving an empty JSON object"""
    pipeline_yaml = f"""
name: test-empty-object-pipeline
steps:
  - name: save-empty-object
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: {{}}
    outputs:
      - obj
    saveas: "{temp_output_dir}/empty_object.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "empty_object.json"
    with open(output_file) as f:
        data = json.load(f)

    assert data == {}
    assert isinstance(data, dict)


def test_saveas_special_characters_in_path(temp_output_dir):
    """Test saving to paths with special characters"""
    pipeline_yaml = f"""
name: test-special-chars-pipeline
steps:
  - name: save-special-chars
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "test content"
    outputs:
      - text
    saveas: "{temp_output_dir}/file-with_special.chars.txt"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "file-with_special.chars.txt"
    assert output_file.exists()


def test_saveas_deeply_nested_json(temp_output_dir):
    """Test saving deeply nested JSON structures"""
    nested_data = {
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

    pipeline_yaml = f"""
name: test-deep-nesting-pipeline
steps:
  - name: save-deep-nested
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: {json.dumps(nested_data)}
    outputs:
      - data
    saveas: "{temp_output_dir}/deep_nested.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "deep_nested.json"
    with open(output_file) as f:
        data = json.load(f)

    assert data["level1"]["level2"]["level3"]["level4"]["value"] == "deep"


def test_saveas_json_with_mixed_types_array(temp_output_dir):
    """Test JSON array with mixed types"""
    pipeline_yaml = f"""
name: test-mixed-array-pipeline
steps:
  - name: save-mixed-array
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value:
        - "string"
        - 42
        - true
        - null
        - nested: "object"
    outputs:
      - mixed
    saveas: "{temp_output_dir}/mixed_array.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "mixed_array.json"
    with open(output_file) as f:
        data = json.load(f)

    assert len(data) == 5
    assert data[0] == "string"
    assert data[1] == 42
    assert data[2] is True
    assert data[3] is None
    assert data[4]["nested"] == "object"


def test_saveas_overwrite_existing_file(temp_output_dir):
    """Test that saveas overwrites existing files"""
    output_file = Path(temp_output_dir) / "overwrite.txt"
    output_file.write_text("old content")

    pipeline_yaml = f"""
name: test-overwrite-pipeline
steps:
  - name: overwrite-file
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value: "new content"
    outputs:
      - text
    saveas: "{temp_output_dir}/overwrite.txt"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    content = output_file.read_text()
    assert content == "new content"
    assert "old content" not in content


def test_saveas_json_indentation(temp_output_dir):
    """Test that JSON output is properly indented for readability"""
    pipeline_yaml = f"""
name: test-json-indent-pipeline
steps:
  - name: save-indented-json
    type: function
    function: llmflow.utils.data.identity
    inputs:
      value:
        key1: "value1"
        key2: "value2"
    outputs:
      - data
    saveas: "{temp_output_dir}/indented.json"
"""
    pipeline_file = Path(temp_output_dir) / "pipeline.yaml"
    pipeline_file.write_text(pipeline_yaml)

    run_pipeline(str(pipeline_file), skip_lint=True)

    output_file = Path(temp_output_dir) / "indented.json"
    content = output_file.read_text()

    # Check for indentation (multiple lines with spaces/tabs)
    lines = content.split('\n')
    assert len(lines) > 1, "JSON should be multi-line formatted"


class TestHandleStepOutputs:
    def test_saveas_simple(self, tmp_path):
        """Test saveas writes file correctly"""
        context = {}
        step = {
            "name": "test",
            "outputs": "content",
            "saveas": str(tmp_path / "output.txt")
        }
        result = "Hello World"

        handle_step_outputs(step, result, context, base_dir=str(tmp_path.parent))

        # Verify file was written
        output_file = tmp_path / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == "Hello World"

        # Verify context was updated
        assert context["content"] == "Hello World"
