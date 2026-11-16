"""A text answer from a step with MCP tools reaches the pipeline as one without tools does.

In semdom-greek-lexicon's SemLex pipeline, a quote-checking step with Bible lookups returned its
entry wrapped in ```` ```markdown ````, and the fence stayed in the entry: the whole-answer fence
was taken off only on the path without tools (#276). And a step that was still asking for verses
when its rounds ran out failed in the JSON parser, as "expected string or bytes-like object, got
'NoneType'", instead of saying what to change.

Driven through `_run_llm_with_mcp_tools_async`, as the other MCP tests are: `sp run` cannot reach
this path without a live MCP server.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from llmflow.utils.llm_runner import _run_llm_with_mcp_tools_async

TOOL = {"name": "get_passage_text", "description": "Verse text", "inputSchema": {"type": "object", "properties": {}}}


def _mcp():
    inner = Mock()
    inner._async_call_tool = AsyncMock(return_value="Ἐν ἀρχῇ ἦν ὁ λόγος")
    inner.list_tools = AsyncMock(return_value=[TOOL])
    inner._async_get_tool_definitions = AsyncMock(return_value=[TOOL])
    mcp = Mock()
    mcp.__aenter__ = AsyncMock(return_value=inner)
    mcp.__aexit__ = AsyncMock(return_value=None)
    return mcp


def _reply(content=None, tool_call=False):
    message = Mock()
    message.content = content
    if tool_call:
        call = Mock()
        call.id, call.type = "call_1", "function"
        call.function.name, call.function.arguments = "get_passage_text", "{}"
        message.tool_calls = [call]
    else:
        message.tool_calls = None
    response = Mock()
    response.choices = [Mock(message=message)]
    response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    return response


def _run(replies, max_iterations=2, output_type="text"):
    with patch("openai.AsyncOpenAI") as client_class:
        client_class.return_value.chat.completions.create = AsyncMock(side_effect=replies)
        return asyncio.run(_run_llm_with_mcp_tools_async(
            prompt="Check the quotes.",
            config={"model": "gpt-4o", "mcp": {"max_iterations": max_iterations}},
            mcp_client=_mcp(),
            output_type=output_type,
            step_name="verify-quotes",
        ))


ENTRY = "# λέγω\n\n## I. To say\n\n- **John 1:1**: ὁ λόγος ✓"


def test_a_fence_around_the_whole_answer_is_taken_off():
    result = _run([_reply(tool_call=True), _reply("```markdown\n" + ENTRY + "\n```")])
    assert result["content"] == ENTRY


def test_an_answer_with_a_fenced_block_inside_is_kept_whole():
    text = ENTRY + "\n\n```\nI → II\n```\n\nAfter the diagram."
    assert _run([_reply(tool_call=True), _reply(text)])["content"] == text


def test_rounds_running_out_names_the_setting_to_raise():
    with pytest.raises(RuntimeError, match=r"verify-quotes.*after 2 round\(s\).*mcp\.max_iterations"):
        _run([_reply(tool_call=True), _reply(tool_call=True)], max_iterations=2, output_type="json")
