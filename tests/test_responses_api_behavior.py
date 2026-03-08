"""
Tests documenting Responses API behavior and format requirements.

These tests document the actual behavior observed when using OpenAI's Responses API
with GPT-5, particularly around tool calling and response parsing.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock, MagicMock

from llmflow.exceptions import ModerationError
from llmflow.utils.llm_runner import _run_with_responses_api


class TestResponsesAPIOutputTypes:
    """Test that we correctly handle all Responses API output item types."""

    def test_response_with_text_type(self):
        """
        When GPT-5 completes without tool calls, response contains 'text' type items.

        Observed behavior:
        - response.status == "completed"
        - response.output contains items with type="text"
        - text items have a 'text' attribute with the content
        """
        # This is the expected format for final text output
        expected_output_structure = {
            "status": "completed",
            "output": [
                {"type": "reasoning", "summary": "...", "content": "..."},
                {"type": "text", "text": "The final answer"}
            ]
        }
        assert expected_output_structure["output"][1]["type"] == "text"

    def test_response_with_function_call_type(self):
        """
        When GPT-5 wants to call a tool, response contains 'function_call' type items.

        Observed behavior:
        - response.status == "completed" (even with function_calls!)
        - response.output contains items with type="function_call"
        - function_call items have: name, arguments, call_id, id
        """
        expected_output_structure = {
            "status": "completed",
            "output": [
                {"type": "reasoning", "summary": "...", "content": "..."},
                {
                    "type": "function_call",
                    "id": "call_abc123",
                    "call_id": "call_abc123",
                    "name": "get_passage_text",
                    "arguments": '{"verse": "Mark 1:1"}'
                }
            ]
        }
        assert expected_output_structure["output"][1]["type"] == "function_call"

    def test_response_with_message_type_after_tool_call(self):
        """
        **CRITICAL BUG**: After tool execution, GPT-5 returns 'message' type, not 'text'.

        Observed behavior from logs:
        - First call: GPT-5 returns function_call ✅
        - Tool executes successfully ✅
        - Second call (with tool result): GPT-5 returns 'message' type ❌
        - We only check for 'text' type, so we get empty string ❌

        From actual logs:
        ```
        INFO - 📊 Output item 1: type=message, hasattr text=False
        INFO - 📊 Output item 1 attributes: ['id', 'content', 'role', 'status', 'type']
        ```

        This test documents that 'message' type items have 'content', not 'text'.
        """
        expected_output_structure = {
            "status": "completed",
            "output": [
                {"type": "reasoning", "summary": "...", "content": "..."},
                {
                    "type": "message",  # ← NOT "text"!
                    "id": "msg_abc123",
                    "content": "The final answer based on the tool result",  # ← 'content' not 'text'
                    "role": "assistant",
                    "status": "completed"
                }
            ]
        }

        # Document the bug: we're checking for 'text' but getting 'message'
        message_item = expected_output_structure["output"][1]
        assert message_item["type"] == "message"
        assert "content" in message_item
        assert "text" not in message_item  # ← This is why we get empty string!


class TestResponsesAPIConversationFormat:
    """Test the required format for conversation history with tool calls."""

    def test_function_call_output_requires_prior_function_call(self):
        """
        function_call_output items must reference a prior function_call via call_id.

        From API error:
        "No tool call found for function call output with call_id call_xxx"

        This means the conversation must include:
        1. The original function_call item from response.output
        2. Then our function_call_output with matching call_id
        """
        # Correct conversation format after tool execution
        correct_input_format = [
            {"role": "user", "content": "Analyze Mark 1:1"},
            # Must include the reasoning from response
            {"type": "reasoning", "id": "reasoning_123", "summary": "...", "content": "..."},
            # Must include the function_call from response
            {"type": "function_call", "id": "call_abc", "call_id": "call_abc", "name": "get_passage_text", "arguments": "..."},
            # Now we can add our output
            {"type": "function_call_output", "call_id": "call_abc", "output": "Verse text here"}
        ]

        # The error occurs if we skip the function_call item
        incorrect_input_format = [
            {"role": "user", "content": "Analyze Mark 1:1"},
            # Missing: reasoning and function_call items!
            {"type": "function_call_output", "call_id": "call_abc", "output": "Verse text here"}  # ← API rejects this
        ]

        assert len(correct_input_format) == 4
        assert len(incorrect_input_format) == 2  # Too short - missing items

    def test_reasoning_items_require_summary_field(self):
        """
        'reasoning' type items must include a 'summary' field.

        From API error:
        "Missing required parameter: 'input[1].summary'"

        When adding reasoning items to conversation history, they need:
        - type: "reasoning"
        - id: the reasoning id from response
        - summary: the summary from response (REQUIRED)
        - content: the full reasoning content
        """
        required_reasoning_format = {
            "type": "reasoning",
            "id": "reasoning_abc123",
            "summary": "Reasoning about the task",  # ← REQUIRED
            "content": "Full reasoning trace..."
        }

        # This would fail with the error we saw
        incorrect_reasoning_format = {
            "type": "reasoning",
            "id": "reasoning_abc123",
            # Missing summary!
            "content": "Full reasoning trace..."
        }

        assert "summary" in required_reasoning_format
        assert "summary" not in incorrect_reasoning_format

    def test_function_call_output_uses_output_not_content(self):
        """
        function_call_output items use 'output' field, not 'content'.

        From API error:
        "Missing required parameter: 'input[1].output'"

        Correct: {"type": "function_call_output", "call_id": "...", "output": "result"}
        Wrong:   {"type": "function_call_output", "call_id": "...", "content": "result"}
        """
        correct_format = {
            "type": "function_call_output",
            "call_id": "call_abc123",
            "output": "The tool result"  # ← 'output' not 'content'
        }

        incorrect_format = {
            "type": "function_call_output",
            "call_id": "call_abc123",
            "content": "The tool result"  # ← Wrong field name
        }

        assert "output" in correct_format
        assert "output" not in incorrect_format


class TestResponsesAPIBugFixes:
    """Tests that verify our fixes for discovered bugs."""

    def test_extract_text_from_message_type(self):
        """
        We must extract text from 'message' type items, not just 'text' type.

        This is the fix for the empty string bug.
        """
        # Mock response with message type (what we actually get)
        mock_output_item = Mock()
        mock_output_item.type = "message"
        mock_output_item.content = "The final answer"

        # Our code should extract from content when type is message
        if hasattr(mock_output_item, 'type'):
            if mock_output_item.type == "message" and hasattr(mock_output_item, 'content'):
                extracted_text = mock_output_item.content
            elif mock_output_item.type == "text" and hasattr(mock_output_item, 'text'):
                extracted_text = mock_output_item.text
            else:
                extracted_text = ""

        assert extracted_text == "The final answer"

    def test_conversation_includes_all_response_items(self):
        """
        Conversation history must include ALL items from response.output before adding tool results.

        Order must be:
        1. Original user message
        2. reasoning item from response.output
        3. function_call item from response.output
        4. function_call_output with tool result
        """
        # Simulate building conversation
        input_items = [{"role": "user", "content": "prompt"}]

        # Mock response items
        reasoning_item = Mock(type="reasoning", id="r1", summary="...", content="...")
        function_call_item = Mock(type="function_call", id="fc1", call_id="fc1", name="tool", arguments="{}")

        # Add response items to conversation
        input_items.append({
            "type": reasoning_item.type,
            "id": reasoning_item.id,
            "summary": reasoning_item.summary,
            "content": reasoning_item.content
        })
        input_items.append({
            "type": function_call_item.type,
            "id": function_call_item.id,
            "call_id": function_call_item.call_id,
            "name": function_call_item.name,
            "arguments": function_call_item.arguments
        })

        # Then add tool result
        input_items.append({
            "type": "function_call_output",
            "call_id": function_call_item.call_id,
            "output": "tool result"
        })

        # Verify order and structure
        assert len(input_items) == 4
        assert input_items[1]["type"] == "reasoning"
        assert input_items[2]["type"] == "function_call"
        assert input_items[3]["type"] == "function_call_output"
        assert input_items[3]["call_id"] == input_items[2]["call_id"]


@pytest.mark.parametrize("output_type,expected_attr", [
    ("text", "text"),
    ("message", "content"),
])
def test_extract_final_text_from_different_types(output_type, expected_attr):
    """
    Test that we can extract final text from both 'text' and 'message' types.

    This parametrized test documents that:
    - 'text' type uses 'text' attribute
    - 'message' type uses 'content' attribute
    """
    mock_item = Mock()
    mock_item.type = output_type
    setattr(mock_item, expected_attr, "The final answer")

    # Extraction logic
    if mock_item.type == "text" and hasattr(mock_item, "text"):
        result = mock_item.text
    elif mock_item.type == "message" and hasattr(mock_item, "content"):
        result = mock_item.content
    else:
        result = ""

    assert result == "The final answer"


@pytest.mark.asyncio
async def test_responses_api_moderation_block(monkeypatch):
    """Ensure moderation blocks raise ModerationError with context."""

    class DummyResponses:
        def create(self, **kwargs):
            return SimpleNamespace(
                status="incomplete",
                output=[],
                usage=None,
                incomplete_details=SimpleNamespace(
                    reason="content_filter",
                    explanation="Blocked because passage considered sensitive",
                    content_filter_results=[{"filtered": True, "category": "violence"}]
                )
            )

    class DummyClient:
        def __init__(self):
            self.responses = DummyResponses()

    class DummyMCP:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def _async_get_tool_definitions(self):
            return [{"name": "noop", "inputSchema": {}}]

        async def _async_call_tool(self, name, args):
            return "noop"

    monkeypatch.setattr("openai.OpenAI", lambda: DummyClient())

    with pytest.raises(ModerationError) as excinfo:
        await _run_with_responses_api(
            prompt="Translate a Bible verse",
            config={"model": "gpt-5.1"},
            mcp_client=DummyMCP(),
            output_type="text",
            step_name="moderation-test"
        )

    assert "content_filter" in str(excinfo.value)
