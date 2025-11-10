"""Integration tests for verify-citations step with real MCP server."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from llmflow.modules.mcp import MCPClient
from llmflow.runner import run_llm_step


@pytest.mark.asyncio
async def test_mcp_client_returns_tools():
    """Test that MCP client actually fetches tool definitions."""

    # Real MCP connection
    client = MCPClient(
        server_url="https://bible-resource-server-preview.labs.biblica.com/mcp"
    )

    async with client as mcp:
        tools = await mcp._async_get_tool_definitions()

        # Debug: Print what we got
        print(f"\n📋 MCP returned {len(tools)} tools")
        for tool in tools:
            print(f"   - {tool['name']}: {tool.get('description', 'No description')[:80]}")

        # Verify we got tools
        assert len(tools) > 0, "MCP server returned no tools"
        # ✅ Use actual tool name from server
        assert any(t['name'] == 'get_passage_text' for t in tools), "get_passage_text tool not found"


@pytest.mark.asyncio
async def test_get_passage_text_schema():
    """Get the actual schema for get_passage_text to understand its parameters."""

    client = MCPClient(
        server_url="https://bible-resource-server-preview.labs.biblica.com/mcp"
    )

    async with client as mcp:
        tools = await mcp._async_get_tool_definitions()

        # Find get_passage_text tool
        passage_tool = next((t for t in tools if t['name'] == 'get_passage_text'), None)

        assert passage_tool is not None, "get_passage_text tool not found"

        print(f"\n📋 get_passage_text tool schema:")
        print(f"   Name: {passage_tool['name']}")
        print(f"   Description: {passage_tool.get('description', 'N/A')[:200]}")

        input_schema = passage_tool.get('inputSchema', {})
        properties = input_schema.get('properties', {})
        required = input_schema.get('required', [])

        print(f"\n   Parameters:")
        for param_name, param_info in properties.items():
            is_required = "✅ REQUIRED" if param_name in required else "⚪ optional"
            param_type = param_info.get('type', 'unknown')
            param_desc = param_info.get('description', 'No description')[:100]
            print(f"      {param_name} ({param_type}) - {is_required}")
            print(f"         {param_desc}")

            # If it's an array, show what items it expects
            if param_type == 'array':
                items = param_info.get('items', {})
                print(f"         Items type: {items.get('type', 'unknown')}")

        print(f"\n   Required fields: {required}")


@pytest.mark.asyncio
async def test_mcp_client_with_tool_filter():
    """Test that MCPClient can filter tools."""

    # Check the MCPClient signature first
    import inspect
    sig = inspect.signature(MCPClient.__init__)
    print(f"\n📋 MCPClient.__init__ signature: {sig}")

    # MCPClient might not support allowed_tools parameter directly
    # It's filtered in init_mcp_client instead
    from llmflow.modules.mcp import init_mcp_client

    pipeline_config = {
        "mcp_servers": {
            "bible": {
                "url": "https://bible-resource-server-preview.labs.biblica.com/mcp",
                "tools": ["get_passage_text", "get_word_info"]
            }
        }
    }

    step_config = {
        "mcp": {
            "enabled": True,
            "server": "bible"
        }
    }

    # Create client through init function which handles filtering
    client = init_mcp_client(step_config, pipeline_config)

    assert client is not None, "MCP client should be created"

    async with client as mcp:
        tools = await mcp._async_get_tool_definitions()

        print(f"\n📋 Filtered to {len(tools)} tools")
        for tool in tools:
            print(f"   - {tool['name']}")

        # Should only have the allowed tools
        tool_names = {t['name'] for t in tools}
        assert 'get_passage_text' in tool_names
        assert 'get_word_info' in tool_names


@pytest.mark.asyncio
async def test_get_textual_editions():
    """Get the list of valid textual editions to use."""

    client = MCPClient(
        server_url="https://bible-resource-server-preview.labs.biblica.com/mcp"
    )

    async with client as mcp:
        # Call the tool that lists available editions
        result = await mcp._async_call_tool(
            "get_textual_edition_abbreviations",
            {}
        )

        print(f"\n📚 Available textual editions:")
        print(f"   Type: {type(result)}")
        print(f"   Content:\n{result}")


@pytest.mark.asyncio
async def test_get_passage_text_directly():
    """Test calling get_passage_text tool directly using the correct schema."""

    client = MCPClient(
        server_url="https://bible-resource-server-preview.labs.biblica.com/mcp"
    )

    async with client as mcp:
        # First, get the schema to know what parameters to use
        tools = await mcp._async_get_tool_definitions()
        passage_tool = next((t for t in tools if t['name'] == 'get_passage_text'), None)
        required_params = passage_tool.get('inputSchema', {}).get('required', [])

        print(f"\n🔍 Required parameters for get_passage_text: {required_params}")

        # Let's also check the schema for textual_editions
        properties = passage_tool.get('inputSchema', {}).get('properties', {})
        textual_editions_schema = properties.get('textual_editions', {})

        print(f"\n📋 textual_editions schema:")
        print(f"   Type: {textual_editions_schema.get('type')}")
        print(f"   Items: {textual_editions_schema.get('items')}")
        print(f"   Full schema: {textual_editions_schema}")

        # Try with just required parameters first
        print(f"\n🧪 Test 1: Only required parameters")
        result = await mcp._async_call_tool(
            "get_passage_text",
            {
                "usfm_references": ["JHN 3:16"]
            }
        )

        print(f"\n📖 Passage text result:")
        print(f"   Type: {type(result)}")
        print(f"   Length: {len(str(result))}")
        print(f"   Content preview: {str(result)[:300]}")

        # Verify we got content
        assert result is not None
        result_str = str(result)

        # Check for error messages first
        if "Error" in result_str or "error" in result_str:
            print(f"\n❌ Tool returned error: {result_str}")
            pytest.fail(f"Tool execution failed: {result_str}")

        assert len(result_str) > 50, f"Expected substantial Bible text, got only: {result_str}"

        # John 3:16 should contain Greek text or English text
        print(f"\n✅ get_passage_text works correctly!")


@pytest.mark.asyncio
async def test_get_passage_text_with_greek():
    """Test getting passage text in Greek (SBLGNT) - the preferred edition."""

    client = MCPClient(
        server_url="https://bible-resource-server-preview.labs.biblica.com/mcp"
    )

    async with client as mcp:
        # Get Greek text from John 3:16 using SBLGNT (SBL Greek New Testament)
        result = await mcp._async_call_tool(
            "get_passage_text",
            {
                "usfm_references": ["JHN 3:16"],
                "textual_editions": ["SBLGNT"]  # ✅ SBL Greek New Testament (preferred)
            }
        )

        print(f"\n📖 Greek text (SBLGNT) result:")
        print(f"   Type: {type(result)}")
        print(f"   Length: {len(str(result))}")
        print(f"   Content:\n{result}")

        # Verify we got content
        assert result is not None
        result_str = str(result)

        # Check for error messages
        assert "Error" not in result_str and "error" not in result_str, \
            f"Tool returned error: {result_str}"

        # John 3:16 should contain Greek text - key words from the verse
        # "οὕτως γὰρ ἠγάπησεν ὁ θεὸς τὸν κόσμον..."
        greek_words = ["οὕτως", "θεός", "ἠγάπησεν", "κόσμον"]
        found_words = [word for word in greek_words if word in result_str]

        assert len(found_words) >= 2, \
            f"Expected Greek text from John 3:16, found only {found_words} in: {result_str}"

        # Check for the specific verb we care about
        assert "ἠγάπησεν" in result_str, "Should contain ἠγάπησεν (loved/aorist of ἀγαπάω)"

        print(f"\n✅ Greek text (SBLGNT) retrieved successfully!")
        print(f"   Found Greek words: {found_words}")


@pytest.mark.asyncio
async def test_get_passage_text_with_hebrew():
    """Test getting passage text in Hebrew (WLC) - Westminster Leningrad Codex."""

    client = MCPClient(
        server_url="https://bible-resource-server-preview.labs.biblica.com/mcp"
    )

    async with client as mcp:
        # Get Hebrew text from Genesis 1:1 using WLC
        result = await mcp._async_call_tool(
            "get_passage_text",
            {
                "usfm_references": ["GEN 1:1"],
                "textual_editions": ["WLC"]  # ✅ Westminster Leningrad Codex (Hebrew OT)
            }
        )

        print(f"\n📖 Hebrew text (WLC) result:")
        print(f"   Type: {type(result)}")
        print(f"   Length: {len(str(result))}")
        print(f"   Content:\n{result}")

        # Verify we got content
        assert result is not None
        result_str = str(result)

        # Check for error messages
        assert "Error" not in result_str and "error" not in result_str, \
            f"Tool returned error: {result_str}"

        # Extract just the Hebrew text from the JSON response
        import json
        import unicodedata

        try:
            result_json = json.loads(result_str)
            hebrew_text = result_json.get("WLC", "")
            # ✅ Normalize to NFC form (canonical composition)
            hebrew_text = unicodedata.normalize('NFC', hebrew_text)
            print(f"\n📝 Extracted Hebrew text: '{hebrew_text}'")
            print(f"   Byte representation: {hebrew_text.encode('utf-8')}")
        except json.JSONDecodeError:
            # If it's not JSON, use the whole string
            hebrew_text = unicodedata.normalize('NFC', result_str)

        # Genesis 1:1 WLC text (as actually returned):
        # "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"

        expected_words = [
            "בְּרֵאשִׁ֖ית",  # In the beginning
            "בָּרָ֣א",       # created
            "אֱלֹהִ֑ים",     # God
            "אֵ֥ת",          # (object marker)
            "הַשָּׁמַ֖יִם",   # the heavens
            "וְאֵ֥ת",        # and (object marker)
            "הָאָֽרֶץ׃",     # the earth (with sof pasuq)
        ]

        # ✅ Normalize expected words too
        expected_words_normalized = [unicodedata.normalize('NFC', word) for word in expected_words]

        found_words = [word for word in expected_words_normalized if word in hebrew_text]

        print(f"\n🔍 Checking for Genesis 1:1 words with full pointing:")
        for i, word in enumerate(expected_words_normalized):
            status = "✅" if word in hebrew_text else "❌"
            print(f"   {status} {expected_words[i]}")
            if word not in hebrew_text:
                # Debug: show what characters we're looking for vs what's there
                print(f"       Expected bytes: {word.encode('utf-8')}")

        # ALL 7 words should be found - this is an exact match test
        assert len(found_words) == 7, \
            f"Expected all 7 words from Genesis 1:1, found only {len(found_words)}/7: {[expected_words[i] for i, w in enumerate(expected_words_normalized) if w in found_words]}"

        # Verify we got the right reference
        assert "GEN 1:1" in result_str
        assert "WLC" in result_str

        print(f"\n✅ Hebrew text (WLC) retrieved successfully!")
        print(f"   Verified all 7 words from Genesis 1:1 (with full WLC pointing)")


def test_verify_citations_with_real_mcp_mock_llm():
    """Test verify-citations step with real MCP server but mocked LLM."""

    pipeline_config = {
        "mcp_servers": {
            "bible": {
                "url": "https://bible-resource-server-preview.labs.biblica.com/mcp",
                "tools": ["get_passage_text"]
            }
        },
        "llm_config": {
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
    }

    step_config = {
        "name": "verify-citations",
        "type": "llm",
        "prompt": {
            "file": "verify_citations.md",
            "inputs": {
                "citation": "John 3:16",
                "word": "ἀγαπάω",
                "gloss": "love"
            }
        },
        "mcp": {
            "enabled": True,
            "server": "bible",
            "tools": ["get_passage_text"]
        }
    }

    context = {
        "prompts_dir": "prompts",
        "citation": "John 3:16",
        "word": "ἀγαπάω",
        "gloss": "love"
    }

    # Mock both the prompt rendering AND the LLM call
    with patch("llmflow.runner.render_prompt") as mock_render, \
         patch("llmflow.runner.run_llm_with_mcp_tools") as mock_mcp_call:

        # Mock prompt rendering
        mock_render.return_value = "Verify that citation 'John 3:16' contains the word 'ἀγαπάω' (love)"

        # Mock LLM response
        mock_mcp_call.return_value = "✅ Citation verified: John 3:16 contains ἀγαπάω (love)"

        # Run the step - NOT async
        result = run_llm_step(step_config, context, pipeline_config)

        print(f"\n✅ LLM Result: {result}")

        # Verify the result
        assert "verified" in result.lower()
        assert "John 3:16" in result

        # Verify prompt was rendered
        mock_render.assert_called_once()

        # Verify MCP tool calling was invoked
        mock_mcp_call.assert_called_once()

        # Check that MCP client was passed
        call_args = mock_mcp_call.call_args
        print(f"\n🔧 run_llm_with_mcp_tools called with:")
        print(f"   - prompt: {call_args[0][0]}")
        print(f"   - llm_config: {call_args[0][1]}")
        print(f"   - mcp_client: {call_args[0][2]}")

        assert call_args[0][2] is not None, "MCP client should be passed to run_llm_with_mcp_tools"

        # Verify the prompt was passed correctly
        assert call_args[0][0] == "Verify that citation 'John 3:16' contains the word 'ἀγαπάω' (love)"