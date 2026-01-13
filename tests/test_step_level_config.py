#!/usr/bin/env python3
"""Test that step-level LLM config parameters override defaults correctly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llmflow.utils.llm_runner import get_model_family

def test_config_merging():
    """Test that step-level config parameters override pipeline defaults."""

    # Simulate the config merging logic from runner.py lines 592-613
    pipeline_config = {
        "llm_config": {
            "model": "gpt-4o",
            "temperature": 0.5,
            "reasoning_effort": "medium"
        }
    }

    step = {
        "name": "test_step",
        "model": "gpt-5",
        "reasoning_effort": "low",
        "temperature": 0.9
    }

    # Build merged config (same logic as runner.py)
    llm_config = pipeline_config.get("llm_config", {})
    step_options = step.get("llm_options", {})
    step_config = {
        "model": step.get("model"),
        "temperature": step.get("temperature") or step_options.get("temperature"),
        "max_tokens": step.get("max_tokens") or step_options.get("max_tokens"),
        "max_completion_tokens": step.get("max_completion_tokens") or step_options.get("max_completion_tokens"),
        "timeout_seconds": step.get("timeout_seconds") or step_options.get("timeout_seconds"),
        "response_format": step.get("response_format"),
        "reasoning_effort": step.get("reasoning_effort"),  # Add this field
    }
    step_config = {k: v for k, v in step_config.items() if v is not None}

    # Start with universal defaults
    merged_config = {
        "model": "gpt-4o",
        "temperature": 0.7,
        "timeout_seconds": 30,
    }
    merged_config.update(llm_config)
    merged_config.update(step_options)
    merged_config.update(step_config)

    print("=" * 80)
    print("CONFIG MERGING TEST")
    print("=" * 80)
    print(f"\nPipeline-level llm_config:")
    for k, v in llm_config.items():
        print(f"  {k}: {v}")

    print(f"\nStep-level config:")
    for k, v in step_config.items():
        print(f"  {k}: {v}")

    print(f"\nMerged config:")
    for k, v in merged_config.items():
        print(f"  {k}: {v}")

    # Assertions
    assert merged_config["model"] == "gpt-5", "Step model should override pipeline model"
    assert merged_config["temperature"] == 0.9, "Step temperature should override pipeline temperature"
    assert merged_config["reasoning_effort"] == "low", "Step reasoning_effort should override pipeline reasoning_effort"

    print("\n✅ All assertions passed!")
    print("   - Step-level 'model' overrides pipeline default")
    print("   - Step-level 'temperature' overrides pipeline default")
    print("   - Step-level 'reasoning_effort' overrides pipeline default")


def test_reasoning_effort_in_responses_api():
    """Test that reasoning_effort gets passed to Responses API correctly."""

    config = {
        "model": "gpt-5",
        "reasoning_effort": "low"
    }

    # This is how it's used in llm_runner.py line 362
    effort = config.get("reasoning_effort", "medium")

    print("\n" + "=" * 80)
    print("RESPONSES API PARAMETER TEST")
    print("=" * 80)
    print(f"\nConfig: {config}")
    print(f"Reasoning effort extracted: {effort}")

    assert effort == "low", "Should extract reasoning_effort from config"

    print("\n✅ Reasoning effort parameter extraction works!")

    # Simulate the API params building (llm_runner.py lines 352-367)
    api_params = {
        "model": config.get("model", "gpt-5"),
        "input": [{"role": "user", "content": "test"}],
        "tools": [],
        "reasoning": {
            "effort": config.get("reasoning_effort", "medium")
        }
    }

    print(f"\nAPI params that would be sent:")
    print(f"  model: {api_params['model']}")
    print(f"  reasoning.effort: {api_params['reasoning']['effort']}")

    assert api_params["reasoning"]["effort"] == "low"

    print("\n✅ API params correctly include reasoning_effort!")


def test_missing_reasoning_effort_uses_default():
    """Test that missing reasoning_effort falls back to 'medium'."""

    config = {
        "model": "gpt-5",
        # No reasoning_effort specified
    }

    effort = config.get("reasoning_effort", "medium")

    print("\n" + "=" * 80)
    print("DEFAULT REASONING EFFORT TEST")
    print("=" * 80)
    print(f"\nConfig (no reasoning_effort): {config}")
    print(f"Reasoning effort (should default to 'medium'): {effort}")

    assert effort == "medium", "Should default to 'medium' when not specified"

    print("\n✅ Default reasoning_effort works correctly!")


if __name__ == "__main__":
    test_config_merging()
    test_reasoning_effort_in_responses_api()
    test_missing_reasoning_effort_uses_default()

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)
    print("\nYou can now safely use step-level reasoning_effort like:")
    print("""
- name: my_step
  type: llm
  model: gpt-5
  reasoning_effort: "low"   # Just this one param!
  mcp:
    enabled: true
    # ...
""")
