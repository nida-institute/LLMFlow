"""Test prompt input resolution with variable substitution"""

import tempfile
from pathlib import Path
import pytest
from llmflow.runner import render_prompt


def test_prompt_inputs_basic_resolution():
    """Test that prompt inputs are resolved and added to context"""

    # Create a simple prompt file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpt', delete=False) as f:
        f.write("Hello {{name}}, you are {{age}} years old.")
        prompt_file = f.name

    try:
        # Context with the actual data
        context = {
            "user_data": {"name": "Alice", "age": 30}
        }

        # Prompt config with inputs referencing context
        prompt_config = {
            "file": prompt_file,
            "inputs": {
                "name": "${user_data.name}",
                "age": "${user_data.age}"
            }
        }

        result = render_prompt(prompt_config, context)

        # Should have substituted the values
        assert "Hello Alice" in result
        assert "30 years old" in result
        assert "${" not in result  # No unresolved variables
        assert "{{" not in result  # All double braces replaced

    finally:
        Path(prompt_file).unlink()


def test_prompt_inputs_list_indexing():
    """Test that prompt inputs can use list indexing like ${entries[0]}"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpt', delete=False) as f:
        f.write("Entry: {{entry}}")
        prompt_file = f.name

    try:
        context = {
            "entries": ["<xml>First Entry</xml>", "<xml>Second Entry</xml>"]
        }

        prompt_config = {
            "file": prompt_file,
            "inputs": {
                "entry": "${entries[0]}"
            }
        }

        result = render_prompt(prompt_config, context)

        assert "Entry: <xml>First Entry</xml>" in result
        assert "${entries[0]}" not in result  # Should be resolved
        assert "{{entry}}" not in result  # Should be replaced

    finally:
        Path(prompt_file).unlink()


def test_prompt_inputs_with_object_attributes():
    """Test that prompt inputs work with object attributes like ${row.lemma}"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpt', delete=False) as f:
        f.write("Lemma: {{lemma}}, Status: {{status}}")
        prompt_file = f.name

    try:
        # Simulate a Row object
        class Row:
            def __init__(self, data):
                self.lemma = data['lemma']
                self.status = data['status']

        context = {
            "row": Row({"lemma": "ὁ", "status": "reviewed"})
        }

        prompt_config = {
            "file": prompt_file,
            "inputs": {
                "lemma": "${row.lemma}",
                "status": "${row.status}"
            }
        }

        result = render_prompt(prompt_config, context)

        assert "Lemma: ὁ" in result
        assert "Status: reviewed" in result
        assert "${row.lemma}" not in result
        assert "{{lemma}}" not in result

    finally:
        Path(prompt_file).unlink()


def test_prompt_inputs_complex_scenario():
    """Test the exact scenario from the lexicon pipeline"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpt', delete=False) as f:
        f.write("""
Process this entry:
{{entry}}

For lemma: {{lemma}}
Status: {{status}}
""")
        prompt_file = f.name

    try:
        # Simulate Row object
        class Row:
            def __init__(self, data):
                for k, v in data.items():
                    setattr(self, k, v)

        context = {
            "entries": ["<entry>XML content here</entry>"],
            "row": Row({"lemma": "ὁ", "status": "pending"})
        }

        prompt_config = {
            "file": prompt_file,
            "inputs": {
                "entry": "${entries[0]}",
                "lemma": "${row.lemma}",
                "status": "${row.status}"
            }
        }

        result = render_prompt(prompt_config, context)

        # Verify all substitutions happened
        assert "<entry>XML content here</entry>" in result
        assert "For lemma: ὁ" in result
        assert "Status: pending" in result

        # Verify no unresolved variables
        assert "${entries[0]}" not in result
        assert "${row.lemma}" not in result
        assert "${row.status}" not in result
        assert "{{entry}}" not in result
        assert "{{lemma}}" not in result
        assert "{{status}}" not in result

    finally:
        Path(prompt_file).unlink()


def test_prompt_without_inputs():
    """Test that prompts work without inputs specified"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpt', delete=False) as f:
        f.write("Name: {{name}}")
        prompt_file = f.name

    try:
        context = {"name": "Bob"}

        # Just a string path, no inputs dict
        result = render_prompt(prompt_file, context)

        assert "Name: Bob" in result

    finally:
        Path(prompt_file).unlink()


def test_prompt_inputs_from_yaml_string():
    """Test that prompt inputs work when coming from YAML as strings"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpt', delete=False) as f:
        f.write("Entry: {{entry}}")
        prompt_file = f.name

    try:
        context = {
            "entries": ["<xml>First Entry</xml>", "<xml>Second Entry</xml>"]
        }

        # Simulate how YAML loads the config - as strings
        prompt_config = {
            "file": prompt_file,
            "inputs": {
                "entry": "${entries[0]}"  # This is a STRING, not resolved yet
            }
        }

        result = render_prompt(prompt_config, context)

        print(f"Result: {result}")
        assert "Entry: <xml>First Entry</xml>" in result
        assert "${entries[0]}" not in result
        assert "{{entry}}" not in result

    finally:
        Path(prompt_file).unlink()


def test_xpath_plugin_returns_list():
    """Test that xpath plugin returns a list, not a string"""
    import os
    from llmflow.runner import run_pipeline
    import tempfile
    import yaml

    # Create a simple XML file
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<lexicon>
    <entry n="word1"><definition>First definition</definition></entry>
    <entry n="word2"><definition>Second definition</definition></entry>
</lexicon>
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write XML file
        xml_file = os.path.join(tmpdir, "test.xml")
        with open(xml_file, "w") as f:
            f.write(xml_content)

        # Create pipeline that uses xpath
        pipeline_content = {
            "name": "test-xpath-output",
            "variables": {
                "xml_file": xml_file
            },
            "steps": [
                {
                    "name": "find-entries",
                    "type": "xpath",
                    "inputs": {
                        "path": "${xml_file}",
                        "xpath": "//entry[@n='word1']"
                    },
                    "outputs": "entries"
                }
            ]
        }

        pipeline_file = os.path.join(tmpdir, "test.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_content, f)

        context = run_pipeline(pipeline_file, skip_lint=True)

        # Check what we got
        print(f"\n=== XPATH PLUGIN RESULT ===")
        print(f"Type of entries: {type(context['entries'])}")
        print(f"Is it a list? {isinstance(context['entries'], list)}")

        if isinstance(context['entries'], list):
            print(f"✅ SUCCESS: It's a list with {len(context['entries'])} elements")
            if context['entries']:
                print(f"First element type: {type(context['entries'][0])}")
                print(f"First element: {context['entries'][0][:100]}")
        else:
            print(f"❌ FAIL: Expected list, got {type(context['entries'])}")

        # Assert it's a list
        assert isinstance(context['entries'], list), f"Expected list, got {type(context['entries'])}"
        assert len(context['entries']) > 0, "Expected at least one entry"

        # Now test that ${entries[0]} would work
        print(f"\n=== Testing entries[0] access ===")
        first_entry = context['entries'][0]
        print(f"entries[0] = {first_entry[:100]}...")
        assert isinstance(first_entry, str), "First entry should be a string"
        assert "word1" in first_entry, "First entry should contain 'word1'"


def test_full_lexicon_pipeline_simulation(mocker):  # Add mocker parameter
    """Simulate the exact flow of the lexicon pipeline"""
    import os
    from llmflow.runner import run_pipeline
    import tempfile
    import yaml

    # Mock the LLM call so it doesn't actually run - fix the patch path
    mock_llm = mocker.patch('llmflow.runner.call_llm')
    mock_llm.return_value = "Mocked LLM response for expanded entry"

    # Create test XML lexicon
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text>
        <body>
            <entry n="ὁ">
                <form>ὁ, ἡ, τό</form>
                <sense>the definite article</sense>
            </entry>
        </body>
    </text>
</TEI>
"""

    # Create test prompt file
    prompt_content = """Process this Greek lexicon entry:

{{entry}}

Lemma: {{lemma}}
Status: {{status}}

Please expand this entry with semantic domain information."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write XML file
        xml_file = os.path.join(tmpdir, "lexicon.xml")
        with open(xml_file, "w") as f:
            f.write(xml_content)

        # Write prompt file
        os.makedirs(os.path.join(tmpdir, "prompts"))
        prompt_file = os.path.join(tmpdir, "prompts", "expand-entry.gpt")
        with open(prompt_file, "w") as f:
            f.write(prompt_content)

        # Create TSV status file
        tsv_file = os.path.join(tmpdir, "status.tsv")
        with open(tsv_file, "w") as f:
            f.write("lemma\tstatus\n")
            f.write("ὁ\tpending\n")

        pipeline_content = {
            "name": "test-lexicon-expansion",
            "variables": {
                "prompts_dir": os.path.join(tmpdir, "prompts"),
                "lexicon_file": xml_file,
                "status_file": tsv_file
            },
            "linter_config": {"enabled": False},
            "llm_config": {
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "steps": [
                {
                    "name": "load-status",
                    "type": "tsv",
                    "inputs": {
                        "path": "${status_file}"
                    },
                    "outputs": "status"
                },
                {
                    "name": "process-entries",
                    "type": "for-each",
                    "input": "${status}",
                    "item_var": "row",
                    "steps": [
                        {
                            "name": "find-entry",
                            "type": "xpath",
                            "inputs": {
                                "path": "${lexicon_file}",
                                "xpath": "//entry[@n='${row.lemma}']"
                            },
                            "outputs": "entries"
                        },
                        {
                            "name": "expand-entry",
                            "type": "llm",
                            "prompt": {
                                "file": "expand-entry.gpt",
                                "inputs": {
                                    "entry": "${entries[0]}",
                                    "lemma": "${row.lemma}",
                                    "status": "${row.status}"
                                }
                            },
                            "outputs": "expanded_entry"
                        }
                    ]
                }
            ]
        }

        pipeline_file = os.path.join(tmpdir, "test.yaml")
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_content, f)

        print(f"\n=== Running full pipeline simulation ===")
        context = run_pipeline(pipeline_file, skip_lint=True, dry_run=False)

        print(f"\n=== Context after pipeline ===")
        print(f"Keys: {list(context.keys())}")

        # Now status should be in context since it actually ran
        assert "status" in context
        assert "prompts_dir" in context
        assert "lexicon_file" in context

        # Check that status was loaded as a list
        assert isinstance(context['status'], list), "status should be a list from TSV"
        assert len(context['status']) > 0, "status should have at least one row"

        # Check the first row has the expected structure
        first_row = context['status'][0]
        print(f"First status row: {first_row}")
        print(f"First row type: {type(first_row)}")

        # The TSV plugin should give us a Row object with lemma and status attributes
        if hasattr(first_row, 'lemma'):
            assert first_row.lemma == 'ὁ'
            assert first_row.status == 'pending'
        else:
            # If it's a dict
            assert 'lemma' in first_row
            assert 'status' in first_row
            assert first_row['lemma'] == 'ὁ'
            assert first_row['status'] == 'pending'

        # Verify the LLM was called (mocked)
        assert mock_llm.called