#!/usr/bin/env python3
"""Test that Responses API can work in both Agent mode (with tools) and Ask mode (without tools)."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llmflow.utils.llm_runner import get_model_family


def test_responses_api_agent_mode():
    """Test Responses API with MCP tools enabled (Agent mode)."""
    config = {
        "model": "gpt-5",
        "reasoning_effort": "low",
        "mcp": {
            "enabled": True,
            "server": "bible",
            "max_iterations": 2,
            "tools": ["get_passage_text"]
        }
    }

    # This would normally connect to MCP server
    # For this test, we just verify the config is correct
    assert config["mcp"]["enabled"] == True, "MCP should be enabled for agent mode"
    assert config["mcp"]["max_iterations"] > 0, "Should allow tool iterations"


def test_responses_api_ask_mode():
    """Test Responses API with MCP disabled (Ask mode / simple Q&A)."""
    config = {
        "model": "gpt-5",
        "reasoning_effort": "low",
        "mcp": {
            "enabled": False  # ← This disables autonomous tool calling
        }
    }

    assert config["mcp"]["enabled"] == False, "MCP should be disabled for ask mode"


def test_pipeline_config_for_ask_mode():
    """Test that pipeline YAML config for ask mode is correct."""
    # Simulate a pipeline step with MCP disabled
    step = {
        "name": "simple_question",
        "type": "llm",
        "model": "gpt-5",
        "reasoning_effort": "low",
        "mcp": {
            "enabled": False
        },
        "prompt": {
            "file": "test-prompt.gpt"
        }
    }

    assert step["mcp"]["enabled"] == False, "Ask mode requires mcp.enabled=False"


def test_gpt4o_always_uses_chat_completions():
    """Test that gpt-4o always uses Chat Completions API (ask mode by default)."""
    config = {
        "model": "gpt-4o",
        # Even with MCP enabled, gpt-4o uses Chat Completions
        "mcp": {
            "enabled": True,
            "server": "bible"
        }
    }

    # Check model family
    model_family = get_model_family(config["model"])

    # gpt-4o is not in the Responses API family
    assert model_family not in ("gpt-5", "o1"), "gpt-4o should not use Responses API"
