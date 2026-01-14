"""Test to reproduce the contract validation bug where missing required inputs are not caught"""

import tempfile
from pathlib import Path
import pytest
from llmflow.utils.linter import validate_all_step_contracts, parse_prompt_header


def test_parse_prompt_header_with_requires():
    """Test that parse_prompt_header correctly extracts requires list"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpt', delete=False) as f:
        f.write("""---
prompt:
  requires:
    - passage
    - exegetical_bodies
    - exegetical_language
  format: json
---
Generate bodies questions using {{passage}}, {{exegetical_bodies}}, {{exegetical_language}}.
""")
        prompt_path = f.name

    try:
        result = parse_prompt_header(prompt_path)
        print(f"Parsed header: {result}")

        assert result is not None, "Should parse the header"
        assert "requires" in result, "Should have 'requires' key"
        assert result["requires"] == ["passage", "exegetical_bodies", "exegetical_language"]

    finally:
        Path(prompt_path).unlink()


def test_contract_validation_catches_missing_inputs():
    """Test that validation catches when required inputs are missing from pipeline step"""

    # Create a temporary prompt file with requirements
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpt', delete=False) as f:
        f.write("""---
prompt:
  requires:
    - passage
    - exegetical_bodies
    - exegetical_language
  format: json
---
Generate bodies questions.
""")
        prompt_path = f.name

    try:
        # Create a step that's MISSING required inputs
        steps = [
            {
                "name": "bodies_ast",
                "type": "llm",
                "prompt": {
                    "file": prompt_path,
                    "inputs": {
                        "passage": "${passage}",
                        "scenes_enriched_json": "${scenes_enriched_json}",
                        # MISSING: exegetical_bodies, exegetical_language
                    }
                }
            }
        ]

        errors = []
        def log_func(msg):
            print(msg)

        validation_errors, validated_count = validate_all_step_contracts(
            steps, log_func, pipeline_root=None
        )

        print(f"Validation errors: {validation_errors}")
        print(f"Validated count: {validated_count}")

        # Should have caught the missing inputs
        assert len(validation_errors) > 0, "Should have validation errors for missing inputs"
        assert any("exegetical_bodies" in err for err in validation_errors), \
            "Should report missing exegetical_bodies"
        assert any("exegetical_language" in err for err in validation_errors), \
            "Should report missing exegetical_language"

    finally:
        Path(prompt_path).unlink()


def test_contract_validation_passes_with_all_inputs():
    """Test that validation passes when all required inputs are provided"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpt', delete=False) as f:
        f.write("""---
prompt:
  requires:
    - passage
    - exegetical_bodies
    - exegetical_language
  format: json
---
Generate bodies questions.
""")
        prompt_path = f.name

    try:
        # Create a step with ALL required inputs
        steps = [
            {
                "name": "bodies_ast",
                "type": "llm",
                "prompt": {
                    "file": prompt_path,
                    "inputs": {
                        "passage": "${passage}",
                        "exegetical_bodies": "${bodies_analysis}",
                        "exegetical_language": "${language_analysis}",
                    }
                }
            }
        ]

        def log_func(msg):
            print(msg)

        validation_errors, validated_count = validate_all_step_contracts(
            steps, log_func, pipeline_root=None
        )

        print(f"Validation errors: {validation_errors}")
        print(f"Validated count: {validated_count}")

        # Should have NO errors
        assert len(validation_errors) == 0, f"Should have no validation errors, got: {validation_errors}"
        assert validated_count == 1, "Should have validated 1 step"

    finally:
        Path(prompt_path).unlink()
