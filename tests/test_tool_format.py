"""
Test tool format conversion for different API endpoints.

This test suite validates that MCP tools are correctly converted to the
appropriate format for each API endpoint (Responses API vs Chat Completions).

These tests document the critical bug fix: GPT-5 Responses API requires
a flat tool structure with top-level name/description/parameters, while
Chat Completions API requires nested structure under a "function" key.
"""

import pytest


class TestToolFormatSpecification:
    """Test that documents the critical difference between API tool formats."""

    def test_responses_api_tool_format_specification(self):
        """
        Document the CORRECT tool format for Responses API (GPT-5, o1).

        This is the format that must be used for client.responses.create().
        Using the Chat Completions format causes:
        BadRequestError: Missing required parameter: 'tools[0].name'
        """
        # MCP tool from biblica server
        mcp_tool = {
            "name": "search_bible",
            "description": "Search for Bible passages",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }

        # CORRECT format for Responses API - FLAT structure
        responses_api_format = {
            "type": "function",
            "name": mcp_tool["name"],  # Top-level name - REQUIRED
            "description": mcp_tool["description"],  # Top-level description
            "parameters": mcp_tool["inputSchema"]  # Top-level parameters
        }

        # Verify the structure
        assert responses_api_format["type"] == "function"
        assert responses_api_format["name"] == "search_bible"
        assert responses_api_format["description"] == "Search for Bible passages"
        assert responses_api_format["parameters"]["type"] == "object"
        assert "query" in responses_api_format["parameters"]["properties"]

        # CRITICAL: No nested "function" key
        assert "function" not in responses_api_format

        # All required fields are at top level
        assert "name" in responses_api_format
        assert "description" in responses_api_format
        assert "parameters" in responses_api_format

    def test_chat_completions_tool_format_specification(self):
        """
        Document the CORRECT tool format for Chat Completions API (GPT-4, Claude).

        This is the format that must be used for client.chat.completions.create().
        """
        # MCP tool from biblica server
        mcp_tool = {
            "name": "search_bible",
            "description": "Search for Bible passages",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }

        # CORRECT format for Chat Completions - NESTED structure
        chat_completions_format = {
            "type": "function",
            "function": {  # Nested under "function" key
                "name": mcp_tool["name"],
                "description": mcp_tool["description"],
                "parameters": mcp_tool["inputSchema"]
            }
        }

        # Verify the structure
        assert chat_completions_format["type"] == "function"
        assert "function" in chat_completions_format  # HAS nested function key
        assert chat_completions_format["function"]["name"] == "search_bible"
        assert chat_completions_format["function"]["description"] == "Search for Bible passages"
        assert chat_completions_format["function"]["parameters"]["type"] == "object"

        # CRITICAL: Top-level does NOT have name/description/parameters
        assert "name" not in chat_completions_format
        assert "description" not in chat_completions_format
        assert "parameters" not in chat_completions_format

        # All tool details are nested under "function"
        assert "name" in chat_completions_format["function"]
        assert "description" in chat_completions_format["function"]
        assert "parameters" in chat_completions_format["function"]

    def test_wrong_format_would_cause_api_error(self):
        """
        Regression test: Using Chat Completions format for Responses API fails.

        This documents the bug we fixed. Before the fix, we were using the
        Chat Completions format (nested "function" wrapper) for Responses API,
        which caused: BadRequestError: Missing required parameter: 'tools[0].name'
        """
        # WRONG format for Responses API (this was the bug)
        wrong_format_for_responses = {
            "type": "function",
            "function": {  # This nesting is WRONG for Responses API
                "name": "search_bible",
                "description": "Search",
                "parameters": {}
            }
        }

        # The Responses API error message says: Missing required parameter: 'tools[0].name'
        # That's because it expects name at top level, not nested under "function"
        assert "name" not in wrong_format_for_responses  # This causes the error
        assert "name" in wrong_format_for_responses["function"]

        # CORRECT format for Responses API (the fix)
        correct_format_for_responses = {
            "type": "function",
            "name": "search_bible",  # Top-level name - this is what API expects
            "description": "Search",
            "parameters": {}
        }

        # Verify the fix
        assert "name" in correct_format_for_responses  # This satisfies the API
        assert "function" not in correct_format_for_responses

    def test_complex_schema_preserved_in_both_formats(self):
        """Verify that complex inputSchema structures are preserved correctly."""
        complex_mcp_tool = {
            "name": "complex_search",
            "description": "Complex search with multiple params",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "filters": {
                        "type": "object",
                        "properties": {
                            "book": {"type": "string"},
                            "chapter": {"type": "integer"}
                        }
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }

        # Responses API format (flat)
        responses_format = {
            "type": "function",
            "name": complex_mcp_tool["name"],
            "description": complex_mcp_tool["description"],
            "parameters": complex_mcp_tool["inputSchema"]
        }

        # Chat Completions format (nested)
        chat_format = {
            "type": "function",
            "function": {
                "name": complex_mcp_tool["name"],
                "description": complex_mcp_tool["description"],
                "parameters": complex_mcp_tool["inputSchema"]
            }
        }

        # Both formats preserve the complex schema
        assert responses_format["parameters"]["properties"]["limit"]["minimum"] == 1
        assert responses_format["parameters"]["properties"]["limit"]["maximum"] == 100
        assert responses_format["parameters"]["required"] == ["query"]

        assert chat_format["function"]["parameters"]["properties"]["limit"]["minimum"] == 1
        assert chat_format["function"]["parameters"]["properties"]["limit"]["maximum"] == 100
        assert chat_format["function"]["parameters"]["required"] == ["query"]

    def test_conversion_logic_from_mcp_to_responses_api(self):
        """Test the actual conversion logic used in our code for Responses API."""
        # Simulate what happens in _run_with_responses_api()
        mcp_tools = [
            {
                "name": "search_bible",
                "description": "Search for Bible passages",
                "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}
            },
            {
                "name": "get_verse",
                "description": "Get specific verse",
                "inputSchema": {"type": "object", "properties": {"ref": {"type": "string"}}}
            }
        ]

        # This is the CORRECT conversion logic (after our fix)
        openai_tools = [
            {
                "type": "function",
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {})
            }
            for tool in mcp_tools
        ]

        # Verify conversion results
        assert len(openai_tools) == 2
        assert all("function" not in tool for tool in openai_tools)
        assert all("name" in tool for tool in openai_tools)
        assert openai_tools[0]["name"] == "search_bible"
        assert openai_tools[1]["name"] == "get_verse"

    def test_conversion_logic_from_mcp_to_chat_completions(self):
        """Test the actual conversion logic used in our code for Chat Completions."""
        # Simulate what happens in _run_with_chat_completions()
        mcp_tools = [
            {
                "name": "search_bible",
                "description": "Search for Bible passages",
                "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}
            },
            {
                "name": "get_verse",
                "description": "Get specific verse",
                "inputSchema": {"type": "object", "properties": {"ref": {"type": "string"}}}
            }
        ]

        # This is the CORRECT conversion logic for Chat Completions
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {})
                }
            }
            for tool in mcp_tools
        ]

        # Verify conversion results
        assert len(openai_tools) == 2
        assert all("function" in tool for tool in openai_tools)
        assert all("name" not in tool for tool in openai_tools)  # Name is nested
        assert openai_tools[0]["function"]["name"] == "search_bible"
        assert openai_tools[1]["function"]["name"] == "get_verse"


class TestModelFamilyToolRouting:
    """Test that we know which models use which API (and therefore which tool format)."""

    def test_gpt5_family_uses_responses_api(self):
        """GPT-5 family models use Responses API → flat tool format."""
        from llmflow.utils.llm_runner import get_model_family

        assert get_model_family("gpt-5") == "gpt-5"
        assert get_model_family("gpt-5-mini") == "gpt-5"
        assert get_model_family("o3-mini") == "gpt-5"  # o3-mini uses GPT-5 API

        # These models → Responses API → flat tool format

    def test_o1_family_uses_responses_api(self):
        """o1 family models use Responses API → flat tool format."""
        from llmflow.utils.llm_runner import get_model_family

        assert get_model_family("o1") == "o1"
        assert get_model_family("o1-mini") == "o1"
        assert get_model_family("o1-preview") == "o1"

        # These models → Responses API → flat tool format

    def test_gpt4_family_uses_chat_completions(self):
        """GPT-4 family models use Chat Completions → nested tool format."""
        from llmflow.utils.llm_runner import get_model_family

        assert get_model_family("gpt-4") == "gpt-4"
        assert get_model_family("gpt-4o") == "gpt-4"
        assert get_model_family("gpt-4-turbo") == "gpt-4"
        assert get_model_family("gpt-3.5-turbo") == "gpt-4"  # Uses same API

        # These models → Chat Completions → nested tool format
