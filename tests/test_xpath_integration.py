"""Integration tests for XPath plugin with pipeline runner."""

import tempfile
from pathlib import Path

import pytest
import yaml

from llmflow.runner import run_pipeline


class TestXPathIntegration:
    """Test XPath plugin integration with pipeline execution."""

    @pytest.fixture
    def sample_xml(self, tmp_path):
        """Create a sample XML file for testing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <entry key="alpha">Alpha content</entry>
    <entry key="beta">Beta content</entry>
    <entry key="gamma">Gamma content</entry>
</root>
"""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content)
        return xml_file

    @pytest.fixture
    def tsv_data(self, tmp_path):
        """Create a TSV file with test data."""
        tsv_content = """key\tvalue
alpha\tFirst
beta\tSecond
gamma\tThird
"""
        tsv_file = tmp_path / "test.tsv"
        tsv_file.write_text(tsv_content)
        return tsv_file

    @pytest.fixture
    def namespaced_xml(self, tmp_path):
        """Create XML with namespaces for testing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<tei:root xmlns:tei="http://www.tei-c.org/ns/1.0">
    <tei:entry key="alpha">Alpha entry</tei:entry>
    <tei:entry key="beta">Beta entry</tei:entry>
</tei:root>
"""
        xml_file = tmp_path / "test_ns.xml"
        xml_file.write_text(xml_content)
        return xml_file

    def test_xpath_extracts_text_content(self, tmp_path, sample_xml):
        """Test XPath plugin extracts text content from XML elements."""
        pipeline_config = {
            "name": "test-xpath-text",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "extract-text",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[@key='alpha']",
                        "output_format": "text",
                    },
                    "outputs": ["content"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: Check the actual output
        assert "content" in context
        assert context["content"] == ["Alpha content"]

    def test_xpath_extracts_xml_strings(self, tmp_path, sample_xml):
        """Test XPath plugin extracts XML as strings."""
        pipeline_config = {
            "name": "test-xpath-xml",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "extract-xml",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry",
                        "output_format": "xml-string",
                    },
                    "outputs": ["entries"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: Check we got a list of XML strings
        assert "entries" in context
        assert isinstance(context["entries"], list)
        assert len(context["entries"]) == 3
        assert '<entry key="alpha">Alpha content</entry>' in context["entries"][0]

    def test_xpath_can_index_results(self, tmp_path, sample_xml):
        """Test that XPath results can be indexed with [0] syntax."""
        pipeline_config = {
            "name": "test-xpath-indexing",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "extract-xml",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[@key='alpha']",
                        "output_format": "xml-string",
                    },
                    "outputs": ["entries"],
                },
                {
                    "name": "save-first",
                    "type": "save",
                    "path": str(tmp_path / "first.xml"),
                    "content": "${entries[0]}",  # THIS IS THE CRITICAL TEST
                },
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: Check the file was created with the first entry
        output_file = tmp_path / "first.xml"
        assert output_file.exists()
        content = output_file.read_text()
        assert '<entry key="alpha">Alpha content</entry>' in content
        # Make sure it's NOT the literal string "${entries[0]}"
        assert "${entries[0]}" not in content

    def test_xpath_in_llm_prompt_inputs(self, tmp_path, sample_xml, mocker):
        """Test XPath results can be used in LLM prompt inputs with indexing."""
        mock_llm = mocker.patch('llmflow.runner.call_llm')
        mock_llm.return_value = "Mocked response"

        # Create a simple prompt file WITH PROPER YAML HEADER
        prompt_file = tmp_path / "test.gpt"
        prompt_file.write_text("""<!--
prompt:
  requires:
    - entry
-->
Process this entry: {entry}""")

        pipeline_config = {
            "name": "test-xpath-llm",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "extract-entry",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[@key='beta']",
                        "output_format": "xml-string",
                    },
                    "outputs": ["entries"],
                },
                {
                    "name": "process-entry",
                    "type": "llm",
                    "prompt": {
                        "file": str(prompt_file),
                        "inputs": {
                            "entry": "${entries[0]}",  # CRITICAL: Must expand correctly
                        }
                    },
                    "outputs": ["result"],
                },
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file), skip_lint=False)

        # ASSERT: Check that call_llm received the actual XML, not the template string
        mock_llm.assert_called_once()
        call_args = mock_llm.call_args
        prompt_sent = call_args[0][0]  # First positional argument is the prompt

        print(f"\n=== PROMPT SENT TO LLM ===\n{prompt_sent}\n===")

        # The prompt should contain the actual XML entry
        assert '<entry key="beta">Beta content</entry>' in prompt_sent, \
            f"Expected XML entry in prompt, got: {prompt_sent[:500]}"
        # It should NOT contain the unresolved template variable
        assert "${entries[0]}" not in prompt_sent, \
            f"Found unresolved variable in prompt: {prompt_sent[:500]}"
        assert "{entry}" not in prompt_sent, \
            f"Found unresolved placeholder in prompt: {prompt_sent[:500]}"

    def test_xpath_with_attribute_selector(self, tmp_path, sample_xml):
        """Test XPath with attribute-based selection."""
        pipeline_config = {
            "name": "test-xpath-attribute",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "find-by-key",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[@key='beta']",
                        "output_format": "text",
                    },
                    "outputs": ["beta_content"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT
        assert context["beta_content"] == ["Beta content"]

    def test_xpath_extracts_attribute_values(self, tmp_path, sample_xml):
        """Test XPath extracts attribute values."""
        pipeline_config = {
            "name": "test-xpath-attrs",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "get-keys",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry/@key",
                        "output_format": "text",
                    },
                    "outputs": ["keys"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT
        assert context["keys"] == ["alpha", "beta", "gamma"]

    def test_xpath_multiple_matches(self, tmp_path, sample_xml):
        """Test XPath returns multiple matching elements."""
        pipeline_config = {
            "name": "test-xpath-multiple",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "get-all-entries",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry",
                        "output_format": "text",
                    },
                    "outputs": ["all_entries"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT
        assert isinstance(context["all_entries"], list)
        assert len(context["all_entries"]) == 3
        assert "Alpha content" in context["all_entries"]
        assert "Beta content" in context["all_entries"]
        assert "Gamma content" in context["all_entries"]

    def test_xpath_with_namespaces(self, tmp_path, namespaced_xml):
        """Test XPath with XML namespaces."""
        pipeline_config = {
            "name": "test-xpath-namespaces",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "extract-namespaced",
                    "type": "xpath",
                    "inputs": {
                        "path": str(namespaced_xml),
                        "xpath": "//tei:entry",
                        "output_format": "text",
                        "namespaces": {"tei": "http://www.tei-c.org/ns/1.0"},
                    },
                    "outputs": ["entries"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: Check we got the correct namespaced entries
        assert "entries" in context
        assert context["entries"] == ["Alpha entry", "Beta entry"]

    def test_xpath_with_namespace_attributes(self, tmp_path, namespaced_xml):
        """Test XPath extracts namespaced attributes."""
        pipeline_config = {
            "name": "test-xpath-ns-attrs",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "get-ns-keys",
                    "type": "xpath",
                    "inputs": {
                        "path": str(namespaced_xml),
                        "xpath": "//tei:entry/@key",
                        "output_format": "text",
                        "namespaces": {"tei": "http://www.tei-c.org/ns/1.0"},
                    },
                    "outputs": ["keys"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: Check we got the correct attribute values
        assert context["keys"] == ["alpha", "beta"]

    def test_xpath_empty_results(self, tmp_path, sample_xml):
        """Test XPath with no matching elements."""
        pipeline_config = {
            "name": "test-xpath-empty",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "find-nothing",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//nonexistent",
                        "output_format": "text",
                    },
                    "outputs": ["nothing"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: No results should be found
        assert "nothing" in context
        assert context["nothing"] == []

    def test_xpath_with_predicate(self, tmp_path, sample_xml):
        """Test XPath with position predicate."""
        pipeline_config = {
            "name": "test-xpath-predicate",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "get-first-entry",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[1]",
                        "output_format": "text",
                    },
                    "outputs": ["first_entry"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: The first entry should be returned
        assert context["first_entry"] == ["Alpha content"]

    def test_xpath_complex_expression(self, tmp_path, sample_xml):
        """Test XPath with complex expression."""
        pipeline_config = {
            "name": "test-xpath-complex",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "complex-query",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[@key!='alpha']",
                        "output_format": "xml-string",
                    },
                    "outputs": ["non_alpha"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: We should get XML for beta and gamma entries
        assert "non_alpha" in context
        assert len(context["non_alpha"]) == 2

    def test_xpath_from_keyword_alias(self, tmp_path, sample_xml):
        """Test XPath plugin accepts 'from' as alias for 'path'."""
        pipeline_config = {
            "name": "test-xpath-from",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "use-from-keyword",
                    "type": "xpath",
                    "inputs": {
                        "from": str(sample_xml),
                        "xpath": "//entry",
                        "output_format": "text",
                    },
                    "outputs": ["entries"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: Check we got all entries
        assert "entries" in context
        assert len(context["entries"]) == 3

    def test_xpath_default_output_format(self, tmp_path, sample_xml):
        """Test XPath uses xml-string as default output format."""
        pipeline_config = {
            "name": "test-xpath-default",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "default-format",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[@key='alpha']",
                    },
                    "outputs": ["entry"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: Check the output is in xml-string format
        assert "entry" in context
        assert len(context["entry"]) == 1
        assert '<entry key="alpha">Alpha content</entry>' in context["entry"][0]

    def test_xpath_with_saveas(self, tmp_path, sample_xml):
        """Test XPath with saveas directive."""
        output_file = tmp_path / "saved.xml"

        pipeline_config = {
            "name": "test-xpath-saveas",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "save-result",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[@key='alpha']",
                        "output_format": "xml-string",
                    },
                    "outputs": ["entry"],
                    "saveas": str(output_file),
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        run_pipeline(str(pipeline_file))

        # Verify file was created
        assert output_file.exists()
        content = output_file.read_text()
        assert '<entry key="alpha">Alpha content</entry>' in content

    def test_xpath_in_for_each_loop(self, tmp_path, sample_xml, tsv_data):
        """Test XPath used in for-each loop."""
        output_file = tmp_path / "results.txt"

        pipeline_config = {
            "name": "test-xpath-loop",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "load-keys",
                    "type": "tsv",
                    "inputs": {"path": str(tsv_data)},
                    "outputs": ["rows"],
                },
                {
                    "name": "process-each",
                    "type": "for_each",
                    "items": "${rows}",
                    "steps": [
                        {
                            "name": "find-entry",
                            "type": "xpath",
                            "inputs": {
                                "path": str(sample_xml),
                                "xpath": "//entry[@key='${item.key}']",
                                "output_format": "text",
                            },
                            "outputs": ["entry_text"],
                            "append_to": "all_results",
                        }
                    ],
                },
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        context = run_pipeline(str(pipeline_file))

        # ASSERT: We should have collected results from all 3 iterations
        assert "all_results" in context
        assert len(context["all_results"]) == 3
        # Each result should be a list with one item
        assert context["all_results"][0] == ["Alpha content"]
        assert context["all_results"][1] == ["Beta content"]
        assert context["all_results"][2] == ["Gamma content"]

    def test_xpath_chained_with_other_steps(self, tmp_path, sample_xml):
        """Test XPath output used by subsequent steps."""
        output_file = tmp_path / "processed.txt"

        pipeline_config = {
            "name": "test-xpath-chain",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "extract",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[@key='alpha']",
                        "output_format": "text",
                    },
                    "outputs": ["content"],
                },
                {
                    "name": "save",
                    "type": "save",
                    "path": str(output_file),
                    "content": "${content[0]}",  # Index the list!
                },
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        run_pipeline(str(pipeline_file))

        # ASSERT: Verify file was created with correct content
        assert output_file.exists()
        content = output_file.read_text()
        assert content == "Alpha content"
        assert "${content[0]}" not in content

    def test_xpath_nested_in_conditional(self, tmp_path, sample_xml):
        """Test XPath in conditional step."""
        pipeline_config = {
            "name": "test-xpath-conditional",
            "linter_config": {"enabled": False},
            "variables": {"target_key": "beta"},
            "steps": [
                {
                    "name": "conditional-extract",
                    "type": "if",
                    "condition": "${target_key} == 'beta'",
                    "steps": [
                        {
                            "name": "extract-beta",
                            "type": "xpath",
                            "inputs": {
                                "path": str(sample_xml),
                                "xpath": "//entry[@key='${target_key}']",
                                "output_format": "text",
                            },
                            "outputs": ["result"],
                        }
                    ],
                },
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        run_pipeline(str(pipeline_file))

    def test_xpath_with_variable_substitution(self, tmp_path, sample_xml):
        """Test XPath with variable substitution in xpath expression."""
        pipeline_config = {
            "name": "test-xpath-variables",
            "linter_config": {"enabled": False},
            "variables": {"search_key": "gamma"},
            "steps": [
                {
                    "name": "variable-query",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry[@key='${search_key}']",
                        "output_format": "text",
                    },
                    "outputs": ["content"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        run_pipeline(str(pipeline_file))

    def test_xpath_multiple_outputs(self, tmp_path, sample_xml):
        """Test XPath with multiple output variables."""
        pipeline_config = {
            "name": "test-xpath-multi-out",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "extract-multiple",
                    "type": "xpath",
                    "inputs": {
                        "path": str(sample_xml),
                        "xpath": "//entry",
                        "output_format": "text",
                    },
                    "outputs": ["all_entries", "backup_entries"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        run_pipeline(str(pipeline_file))

    def test_xpath_with_nested_xml(self, tmp_path):
        """Test XPath with nested XML structure."""
        nested_xml = tmp_path / "nested.xml"
        nested_xml.write_text("""<?xml version="1.0"?>
<library>
    <book id="1">
        <title>Book One</title>
        <author>Author A</author>
        <chapters>
            <chapter num="1">Chapter 1</chapter>
            <chapter num="2">Chapter 2</chapter>
        </chapters>
    </book>
    <book id="2">
        <title>Book Two</title>
        <author>Author B</author>
        <chapters>
            <chapter num="1">Chapter 1</chapter>
        </chapters>
    </book>
</library>
""")

        pipeline_config = {
            "name": "test-xpath-nested",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "get-chapters",
                    "type": "xpath",
                    "inputs": {
                        "path": str(nested_xml),
                        "xpath": "//book[@id='1']//chapter",
                        "output_format": "text",
                    },
                    "outputs": ["chapters"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        run_pipeline(str(pipeline_file))

    def test_xpath_descendant_axis(self, tmp_path):
        """Test XPath with descendant axis."""
        xml_file = tmp_path / "tree.xml"
        xml_file.write_text("""<?xml version="1.0"?>
<root>
    <level1>
        <level2>
            <leaf>Deep content</leaf>
        </level2>
    </level1>
</root>
""")

        pipeline_config = {
            "name": "test-xpath-descendant",
            "linter_config": {"enabled": False},
            "steps": [
                {
                    "name": "find-deep",
                    "type": "xpath",
                    "inputs": {
                        "path": str(xml_file),
                        "xpath": "//root//leaf",
                        "output_format": "text",
                    },
                    "outputs": ["deep_content"],
                }
            ],
        }

        pipeline_file = tmp_path / "pipeline.yaml"
        with open(pipeline_file, "w") as f:
            yaml.dump(pipeline_config, f)

        run_pipeline(str(pipeline_file))