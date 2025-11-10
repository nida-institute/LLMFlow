"""Test end-to-end MCP integration with runner."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from llmflow.runner import run_llm_step


def test_llm_step_with_mcp_enabled():
    """Test that run_llm_step properly handles MCP-enabled steps."""

    # Mock pipeline config with MCP server
    pipeline_config = {
        "mcp_servers": {
            "bible": {
                "url": "https://bible-resource-server-preview.labs.biblica.com/mcp"
            }
        },
        "llm_config": {
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
    }

    # Mock step config with MCP enabled
    step_config = {
        "name": "test-step",
        "type": "llm",
        "prompt": "Test prompt",
        "mcp": {
            "enabled": True,
            "server": "bible"
        }
    }

    context = {"prompts_dir": "prompts"}

    # Mock the MCP client and LLM response
    with patch("llmflow.runner.init_mcp_client") as mock_init, \
         patch("llmflow.runner.run_llm_with_mcp_tools") as mock_mcp_call, \
         patch("llmflow.runner.render_prompt") as mock_render:

        # Setup mocks - use AsyncMock for the client's async methods
        mock_client = Mock()
        mock_client._async_close = AsyncMock()  # Make close method async

        mock_init.return_value = mock_client
        mock_render.return_value = "Rendered test prompt"
        mock_mcp_call.return_value = "MCP response"

        # Execute
        result = run_llm_step(step_config, context, pipeline_config)

        # Verify MCP client was initialized
        mock_init.assert_called_once_with(step_config, pipeline_config)

        # Verify MCP tool calling was used
        mock_mcp_call.assert_called_once()
        args = mock_mcp_call.call_args
        assert args[0][0] == "Rendered test prompt"  # prompt
        assert args[0][2] == mock_client  # mcp_client

        # Verify client was closed
        mock_client._async_close.assert_awaited_once()

        assert result == "MCP response"


def test_llm_step_without_mcp():
    """Test that run_llm_step falls back to regular LLM when MCP disabled."""

    pipeline_config = {
        "llm_config": {
            "model": "gpt-4o-mini"
        }
    }

    step_config = {
        "name": "test-step",
        "type": "llm",
        "prompt": "Test prompt"
        # No MCP config
    }

    context = {"prompts_dir": "prompts"}

    with patch("llmflow.runner.init_mcp_client") as mock_init, \
         patch("llmflow.runner.call_llm") as mock_llm, \
         patch("llmflow.runner.render_prompt") as mock_render:

        # MCP disabled - should return None
        mock_init.return_value = None
        mock_render.return_value = "Rendered test prompt"
        mock_llm.return_value = "Regular LLM response"

        result = run_llm_step(step_config, context, pipeline_config)

        # Verify regular LLM was called
        mock_llm.assert_called_once()

        # Verify MCP tools were NOT called
        assert result == "Regular LLM response"