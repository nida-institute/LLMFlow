"""Test cases for MCP client."""

import pytest
import asyncio
from llmflow.modules.mcp import MCPClient, init_mcp_client

# CRITICAL: Must include /mcp in the URL
MCP_SERVER_URL = "https://bible-resource-server-preview.labs.biblica.com/mcp"


class TestMCPClient:
    """Test suite for MCP client functionality."""

    @pytest.mark.asyncio
    async def test_connection_to_biblica_server(self):
        """Test actual connection to Biblica MCP server."""
        # DO NOT use hardcoded URL - use the constant
        async with MCPClient(MCP_SERVER_URL) as client:
            tools = await client._async_get_tool_definitions()

            assert tools is not None
            assert len(tools) > 0
            assert any(t['name'] == 'get_passage_text' for t in tools)

            print(f"✅ Connected successfully, found {len(tools)} tools")

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing available tools."""
        async with MCPClient(MCP_SERVER_URL) as client:
            tools = await client._async_get_tool_definitions()

            # Should have multiple tools
            assert len(tools) >= 10, f"Expected at least 10 tools, got {len(tools)}"

            # Check expected tools
            tool_names = [t['name'] for t in tools]
            expected_tools = [
                'get_textual_edition_abbreviations',
                'get_passage_text',
                'get_word_info',
                'get_word_sense',
            ]

            for expected in expected_tools:
                assert expected in tool_names, f"Missing expected tool: {expected}"

            # Tools should have required fields
            for tool in tools:
                assert 'name' in tool
                assert 'description' in tool
                assert 'inputSchema' in tool

            print(f"✅ Found {len(tools)} tools: {', '.join(tool_names[:5])}...")

    @pytest.mark.asyncio
    async def test_tool_filtering(self):
        """Test filtering tools by requested list."""
        requested_tools = ['get_passage_text', 'get_word_info']

        async with MCPClient(MCP_SERVER_URL, requested_tools) as client:
            tools = await client._async_get_tool_definitions()

            # Should only have requested tools
            assert len(tools) == 2, f"Expected 2 filtered tools, got {len(tools)}"
            tool_names = [t['name'] for t in tools]
            assert 'get_passage_text' in tool_names
            assert 'get_word_info' in tool_names

            print(f"✅ Successfully filtered to 2 tools: {tool_names}")

    @pytest.mark.asyncio
    async def test_get_textual_editions(self):
        """Test calling get_textual_edition_abbreviations."""
        async with MCPClient(MCP_SERVER_URL, ['get_textual_edition_abbreviations']) as client:
            result = await client._async_call_tool('get_textual_edition_abbreviations', {})

            # Should return list of editions
            assert result is not None
            assert len(result) > 0

            # Should contain expected editions
            assert 'SBLGNT' in result or 'BSB' in result, f"Expected SBLGNT or BSB in: {result}"

            print(f"✅ Available editions: {result}")

    @pytest.mark.asyncio
    async def test_get_passage_text(self):
        """Test fetching Bible passage text."""
        async with MCPClient(MCP_SERVER_URL, ['get_passage_text']) as client:
            result = await client._async_call_tool('get_passage_text', {
                'usfm_references': ['JHN 3:16'],
                'textual_editions': ['SBLGNT']
            })

            # Should return Greek text
            assert result is not None
            assert len(result) > 0
            # John 3:16 should contain these Greek words
            greek_words = ['θεὸς', 'κόσμον', 'ἠγάπησεν', 'υἱὸν']
            found = any(word in result for word in greek_words)
            assert found, f"Expected Greek text, got: {result[:100]}"

            print(f"✅ Passage text (first 150 chars): {result[:150]}...")

    @pytest.mark.asyncio
    async def test_get_word_info(self):
        """Test word alignment lookup."""
        async with MCPClient(MCP_SERVER_URL, ['get_word_info']) as client:
            result = await client._async_call_tool('get_word_info', {
                'usfm_reference': 'JHN 3:16',
                'word': 'world',
                'textual_edition': 'BSB'
            })

            assert result is not None
            assert len(result) > 0

            print(f"✅ Word info (first 200 chars): {result[:200]}...")

    @pytest.mark.asyncio
    async def test_caching_of_tool_definitions(self):
        """Test that tool definitions are cached."""
        async with MCPClient(MCP_SERVER_URL) as client:
            # First call
            tools1 = await client._async_get_tool_definitions()

            # Second call should use cache
            tools2 = await client._async_get_tool_definitions()

            assert tools1 == tools2
            assert client._tool_definitions is not None

            print(f"✅ Tool definitions cached successfully ({len(tools1)} tools)")


class TestInitMCPClient:
    """Test suite for init_mcp_client helper function."""

    def test_mcp_disabled(self):
        """Test that None is returned when MCP is disabled."""
        step_config = {'mcp': {'enabled': False}}
        pipeline_config = {}

        client = init_mcp_client(step_config, pipeline_config)
        assert client is None

    def test_mcp_not_configured(self):
        """Test that None is returned when MCP not in config."""
        step_config = {}
        pipeline_config = {}

        client = init_mcp_client(step_config, pipeline_config)
        assert client is None

    def test_missing_server_definition(self):
        """Test error when server not defined in pipeline config."""
        step_config = {
            'mcp': {
                'enabled': True,
                'server': 'nonexistent'
            }
        }
        pipeline_config = {
            'mcp_servers': {
                'bible': {
                    'url': MCP_SERVER_URL
                }
            }
        }

        with pytest.raises(ValueError) as exc_info:
            init_mcp_client(step_config, pipeline_config)

        assert 'nonexistent' in str(exc_info.value)
        assert 'not defined' in str(exc_info.value)


class TestMCPIntegration:
    """Integration tests for full MCP workflow."""

    @pytest.mark.asyncio
    async def test_full_bible_lookup_workflow(self):
        """Test complete workflow: list editions → fetch passage → verify content."""
        async with MCPClient(MCP_SERVER_URL) as client:
            # Step 1: Get available editions
            editions_result = await client._async_call_tool('get_textual_edition_abbreviations', {})
            assert 'SBLGNT' in editions_result, f"Expected SBLGNT in editions: {editions_result}"
            print(f"   Step 1: Found editions: {editions_result}")

            # Step 2: Fetch passage in SBLGNT
            passage_result = await client._async_call_tool('get_passage_text', {
                'usfm_references': ['JHN 3:16'],
                'textual_editions': ['SBLGNT']
            })

            # Step 3: Verify Greek text contains expected words
            greek_words = ['θεὸς', 'κόσμον', 'ἠγάπησεν']
            found = any(word in passage_result for word in greek_words)
            assert found, f"Expected Greek words in passage: {passage_result[:200]}"

            print(f"✅ Full workflow successful")
            print(f"   Passage (first 150 chars): {passage_result[:150]}...")

    @pytest.mark.asyncio
    async def test_multiple_references(self):
        """Test fetching multiple Bible references in one call."""
        async with MCPClient(MCP_SERVER_URL, ['get_passage_text']) as client:
            result = await client._async_call_tool('get_passage_text', {
                'usfm_references': ['JHN 3:16', 'ROM 8:28', 'PSA 23:1'],
                'textual_editions': ['BSB']
            })

            assert len(result) > 100, f"Expected substantial text, got {len(result)} chars"
            print(f"✅ Retrieved {len(result)} characters for 3 references")


# Standalone sync test script
if __name__ == '__main__':
    """Run tests manually using asyncio."""
    import sys

    async def run_tests():
        print("=" * 70)
        print("MCP CLIENT TEST SUITE")
        print(f"Server: {MCP_SERVER_URL}")
        print("=" * 70)

        # Test 1: Basic connection
        print("\n📝 Test 1: Basic Connection")
        try:
            async with MCPClient(MCP_SERVER_URL) as client:
                print("✅ Connection successful")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test 2: List tools
        print("\n📝 Test 2: List Tools")
        try:
            async with MCPClient(MCP_SERVER_URL) as client:
                tools = await client._async_get_tool_definitions()
                print(f"✅ Found {len(tools)} tools:")
                for i, tool in enumerate(tools[:10], 1):
                    print(f"   {i:2d}. {tool['name']}")
                if len(tools) > 10:
                    print(f"   ... and {len(tools) - 10} more")
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test 3: Get editions
        print("\n📝 Test 3: Get Textual Editions")
        try:
            async with MCPClient(MCP_SERVER_URL) as client:
                result = await client._async_call_tool('get_textual_edition_abbreviations', {})
                print(f"✅ Available editions:")
                print(f"   {result}")
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test 4: Fetch passage
        print("\n📝 Test 4: Fetch Passage Text (John 3:16 in Greek)")
        try:
            async with MCPClient(MCP_SERVER_URL) as client:
                result = await client._async_call_tool('get_passage_text', {
                    'usfm_references': ['JHN 3:16'],
                    'textual_editions': ['SBLGNT']
                })
                print(f"✅ Greek text retrieved ({len(result)} chars):")
                print(f"   {result[:200]}...")
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test 5: Word alignment
        print("\n📝 Test 5: Word Alignment (John 3:16 'world')")
        try:
            async with MCPClient(MCP_SERVER_URL) as client:
                result = await client._async_call_tool('get_word_info', {
                    'usfm_reference': 'JHN 3:16',
                    'word': 'world',
                    'textual_edition': 'BSB'
                })
                print(f"✅ Word info retrieved ({len(result)} chars):")
                print(f"   {result[:300]}...")
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        return True

    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)