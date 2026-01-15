"""
Test MCP tool response truncation functionality.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import json


@pytest.mark.asyncio
async def test_truncation_applies_when_response_exceeds_limit():
    """Test that responses larger than max_tool_response_size are truncated."""
    from llmflow.utils.llm_runner import _run_llm_with_mcp_tools_async

    # Create a large response (150k characters)
    large_response = "x" * 150000

    # Mock MCP client with async context manager support
    mock_mcp_inner = Mock()
    mock_mcp_inner._async_call_tool = AsyncMock(return_value=large_response)
    mock_mcp_inner.list_tools = AsyncMock(return_value=[
        {"name": "test_tool", "description": "Test", "inputSchema": {"type": "object", "properties": {}}}
    ])
    mock_mcp_inner._async_get_tool_definitions = AsyncMock(return_value=[
        {"name": "test_tool", "description": "Test", "inputSchema": {"type": "object", "properties": {}}}
    ])

    mock_mcp = Mock()
    mock_mcp.__aenter__ = AsyncMock(return_value=mock_mcp_inner)
    mock_mcp.__aexit__ = AsyncMock(return_value=None)

    # Mock OpenAI response with function call
    mock_tool_call = Mock()
    mock_tool_call.id = "call_1"
    mock_tool_call.type = "function"
    mock_tool_call.function.name = "test_tool"
    mock_tool_call.function.arguments = '{}'

    mock_message = Mock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]

    mock_choice = Mock()
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150

    # Mock final text response
    mock_final_message = Mock()
    mock_final_message.content = "Done"
    mock_final_message.tool_calls = None

    mock_final_choice = Mock()
    mock_final_choice.message = mock_final_message

    mock_final_response = Mock()
    mock_final_response.choices = [mock_final_choice]
    mock_final_response.usage = Mock()
    mock_final_response.usage.prompt_tokens = 200
    mock_final_response.usage.completion_tokens = 75
    mock_final_response.usage.total_tokens = 275

    config = {
        "model": "gpt-4",
        "mcp": {
            "max_iterations": 2,
            "max_tool_response_size": 50000  # 50k limit
        }
    }

    with patch("openai.AsyncOpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock chat completions structure
        mock_completions = Mock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[mock_response, mock_final_response])

        result = await _run_llm_with_mcp_tools_async(
            prompt="Test prompt",
            config=config,
            mcp_client=mock_mcp,
            output_type="text",
            step_name="test_step"
        )

        # Verify tool was called
        assert mock_mcp_inner._async_call_tool.called

        # Verify truncation occurred in the messages
        calls = mock_client.chat.completions.create.call_args_list
        second_call_messages = calls[1][1]["messages"]

        # Find the tool response message
        tool_message = None
        for msg in second_call_messages:
            if msg.get("role") == "tool":
                tool_message = msg
                break

        assert tool_message is not None, "Should have tool message in messages"
        assert len(tool_message["content"]) <= 50000 + 100, "Output should be truncated to ~50k chars"
        assert "[...truncated" in tool_message["content"], "Should include truncation notice"


@pytest.mark.asyncio
async def test_no_truncation_when_response_under_limit():
    """Test that small responses are not truncated."""
    from llmflow.utils.llm_runner import _run_llm_with_mcp_tools_async

    # Create a small response
    small_response = "Small response"

    # Mock MCP client with async context manager support
    mock_mcp_inner = Mock()
    mock_mcp_inner._async_call_tool = AsyncMock(return_value=small_response)
    mock_mcp_inner.list_tools = AsyncMock(return_value=[
        {"name": "test_tool", "description": "Test", "inputSchema": {"type": "object", "properties": {}}}
    ])
    mock_mcp_inner._async_get_tool_definitions = AsyncMock(return_value=[
        {"name": "test_tool", "description": "Test", "inputSchema": {"type": "object", "properties": {}}}
    ])

    mock_mcp = Mock()
    mock_mcp.__aenter__ = AsyncMock(return_value=mock_mcp_inner)
    mock_mcp.__aexit__ = AsyncMock(return_value=None)

    # Mock OpenAI response
    mock_tool_call = Mock()
    mock_tool_call.id = "call_1"
    mock_tool_call.type = "function"
    mock_tool_call.function.name = "test_tool"
    mock_tool_call.function.arguments = '{}'

    mock_message = Mock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]

    mock_choice = Mock()
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150

    mock_final_message = Mock()
    mock_final_message.content = "Done"
    mock_final_message.tool_calls = None

    mock_final_choice = Mock()
    mock_final_choice.message = mock_final_message

    mock_final_response = Mock()
    mock_final_response.choices = [mock_final_choice]
    mock_final_response.usage = Mock()
    mock_final_response.usage.prompt_tokens = 200
    mock_final_response.usage.completion_tokens = 75
    mock_final_response.usage.total_tokens = 275

    config = {
        "model": "gpt-4",
        "mcp": {
            "max_iterations": 2,
            "max_tool_response_size": 50000
        }
    }

    with patch("openai.AsyncOpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=[mock_response, mock_final_response])

        await _run_llm_with_mcp_tools_async(
            prompt="Test prompt",
            config=config,
            mcp_client=mock_mcp,
            output_type="text",
            step_name="test_step"
        )

        # Verify no truncation in the request
        calls = mock_client.chat.completions.create.call_args_list
        second_call_messages = calls[1][1]["messages"]

        tool_message = None
        for msg in second_call_messages:
            if msg.get("role") == "tool":
                tool_message = msg
                break

        assert tool_message is not None
        assert tool_message["content"] == small_response, "Small response should not be truncated"
        assert "[...truncated" not in tool_message["content"]


@pytest.mark.asyncio
async def test_default_truncation_limit():
    """Test that default limit is 100,000 characters."""
    from llmflow.utils.llm_runner import _run_llm_with_mcp_tools_async

    # Create response larger than default (150k chars)
    large_response = "y" * 150000

    # Mock MCP client with async context manager support
    mock_mcp_inner = Mock()
    mock_mcp_inner._async_call_tool = AsyncMock(return_value=large_response)
    mock_mcp_inner.list_tools = AsyncMock(return_value=[
        {"name": "test_tool", "description": "Test", "inputSchema": {"type": "object", "properties": {}}}
    ])
    mock_mcp_inner._async_get_tool_definitions = AsyncMock(return_value=[
        {"name": "test_tool", "description": "Test", "inputSchema": {"type": "object", "properties": {}}}
    ])

    mock_mcp = Mock()
    mock_mcp.__aenter__ = AsyncMock(return_value=mock_mcp_inner)
    mock_mcp.__aexit__ = AsyncMock(return_value=None)

    mock_tool_call = Mock()
    mock_tool_call.id = "call_1"
    mock_tool_call.type = "function"
    mock_tool_call.function.name = "test_tool"
    mock_tool_call.function.arguments = '{}'

    mock_message = Mock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]

    mock_choice = Mock()
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150

    mock_final_message = Mock()
    mock_final_message.content = "Done"
    mock_final_message.tool_calls = None

    mock_final_choice = Mock()
    mock_final_choice.message = mock_final_message

    mock_final_response = Mock()
    mock_final_response.choices = [mock_final_choice]
    mock_final_response.usage = Mock()
    mock_final_response.usage.prompt_tokens = 200
    mock_final_response.usage.completion_tokens = 75
    mock_final_response.usage.total_tokens = 275

    # No max_tool_response_size specified - should use default 100k
    config = {
        "model": "gpt-4",
        "mcp": {
            "max_iterations": 2
        }
    }

    with patch("openai.AsyncOpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=[mock_response, mock_final_response])

        await _run_llm_with_mcp_tools_async(
            prompt="Test prompt",
            config=config,
            mcp_client=mock_mcp,
            output_type="text",
            step_name="test_step"
        )

        calls = mock_client.chat.completions.create.call_args_list
        second_call_messages = calls[1][1]["messages"]

        tool_message = None
        for msg in second_call_messages:
            if msg.get("role") == "tool":
                tool_message = msg
                break

        assert tool_message is not None
        # Should be truncated to ~100k (default)
        assert len(tool_message["content"]) <= 100000 + 100
        assert "[...truncated" in tool_message["content"]
        assert "50,000 characters]" in tool_message["content"], "Should show 50k chars truncated"


@pytest.mark.asyncio
async def test_truncation_includes_character_count():
    """Test that truncation message includes how many chars were removed."""
    from llmflow.utils.llm_runner import _run_llm_with_mcp_tools_async

    # 75k character response
    response = "z" * 75000

    # Mock MCP client with async context manager support
    mock_mcp_inner = Mock()
    mock_mcp_inner._async_call_tool = AsyncMock(return_value=response)
    mock_mcp_inner.list_tools = AsyncMock(return_value=[
        {"name": "test_tool", "description": "Test", "inputSchema": {"type": "object", "properties": {}}}
    ])
    mock_mcp_inner._async_get_tool_definitions = AsyncMock(return_value=[
        {"name": "test_tool", "description": "Test", "inputSchema": {"type": "object", "properties": {}}}
    ])

    mock_mcp = Mock()
    mock_mcp.__aenter__ = AsyncMock(return_value=mock_mcp_inner)
    mock_mcp.__aexit__ = AsyncMock(return_value=None)

    mock_tool_call = Mock()
    mock_tool_call.id = "call_1"
    mock_tool_call.type = "function"
    mock_tool_call.function.name = "test_tool"
    mock_tool_call.function.arguments = '{}'

    mock_message = Mock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]

    mock_choice = Mock()
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150

    mock_final_message = Mock()
    mock_final_message.content = "Done"
    mock_final_message.tool_calls = None

    mock_final_choice = Mock()
    mock_final_choice.message = mock_final_message

    mock_final_response = Mock()
    mock_final_response.choices = [mock_final_choice]
    mock_final_response.usage = Mock()
    mock_final_response.usage.prompt_tokens = 200
    mock_final_response.usage.completion_tokens = 75
    mock_final_response.usage.total_tokens = 275

    config = {
        "model": "gpt-4",
        "mcp": {
            "max_iterations": 2,
            "max_tool_response_size": 30000  # Limit to 30k
        }
    }

    with patch("openai.AsyncOpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=[mock_response, mock_final_response])

        await _run_llm_with_mcp_tools_async(
            prompt="Test prompt",
            config=config,
            mcp_client=mock_mcp,
            output_type="text",
            step_name="test_step"
        )

        calls = mock_client.chat.completions.create.call_args_list
        second_call_messages = calls[1][1]["messages"]

        tool_message = None
        for msg in second_call_messages:
            if msg.get("role") == "tool":
                tool_message = msg
                break

        assert tool_message is not None
        # 75k - 30k = 45k truncated
        assert "45,000 characters]" in tool_message["content"], "Should show exact truncation amount"
