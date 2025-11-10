"""Model Context Protocol (MCP) client using official SDK."""

import asyncio
from typing import Dict, List, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from llmflow.modules.logger import Logger
import httpx
import json

logger = Logger()


class MCPClient:
    """Client for Model Context Protocol servers using official SDK."""

    def __init__(self, server_url: str, tools: Optional[List[str]] = None):
        self.server_url = server_url
        self.requested_tools = tools or []
        self._session: Optional[ClientSession] = None
        self._tool_definitions: Optional[List[Dict[str, Any]]] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._is_initialized = False
        self._message_id = 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self._async_init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._async_close()

    def _get_next_id(self) -> int:
        """Get next message ID."""
        self._message_id += 1
        return self._message_id

    async def _send_jsonrpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send JSON-RPC request to HTTP MCP server."""
        if not self._http_client:
            raise RuntimeError("HTTP client not initialized")

        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params or {}
        }

        logger.debug(f"🔧 Sending JSON-RPC: {method}")

        response = await self._http_client.post(
            self.server_url,
            json=request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        response.raise_for_status()

        result = response.json()
        logger.debug(f"✅ Received response: {result.get('result', {}).keys() if 'result' in result else 'error'}")

        if "error" in result:
            raise RuntimeError(f"JSON-RPC error: {result['error']}")

        return result.get("result", {})

    async def _async_init_session(self):
        """Initialize MCP session asynchronously via HTTP POST."""
        if self._is_initialized:
            return

        try:
            logger.debug(f"🔧 Connecting to MCP server (HTTP): {self.server_url}")

            # Create HTTP client for JSON-RPC
            self._http_client = httpx.AsyncClient(timeout=30.0)

            # Send initialize request
            logger.debug("🔧 Sending initialize request...")
            init_result = await self._send_jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "llmflow",
                    "version": "1.0.0"
                }
            })

            logger.debug(f"✅ MCP session initialized: {init_result}")

            # Send initialized notification (no response expected)
            await self._http_client.post(
                self.server_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                },
                headers={
                    "Content-Type": "application/json",
                }
            )

            self._is_initialized = True
            logger.info(f"✅ Connected to MCP server: {self.server_url}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP server: {e}")
            import traceback
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            raise RuntimeError(f"MCP connection failed: {e}")

    async def _async_get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Fetch tool definitions asynchronously."""
        if not self._is_initialized:
            await self._async_init_session()

        if self._tool_definitions is not None:
            return self._tool_definitions

        try:
            logger.debug(f"🔧 Fetching MCP tool definitions")

            # List available tools via JSON-RPC
            result = await self._send_jsonrpc("tools/list")
            all_tools = result.get("tools", [])

            logger.debug(f"📋 Server returned {len(all_tools)} tools")

            # Convert MCP tool format to OpenAI format
            openai_tools = []
            for tool in all_tools:
                if self.requested_tools and tool["name"] not in self.requested_tools:
                    continue

                openai_tools.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "inputSchema": tool.get("inputSchema", {})
                })

            self._tool_definitions = openai_tools
            tool_names = [t['name'] for t in openai_tools]
            logger.debug(f"✅ Loaded {len(openai_tools)} MCP tool(s): {tool_names}")
            return openai_tools

        except Exception as e:
            logger.error(f"❌ Failed to fetch MCP tool definitions: {e}")
            raise RuntimeError(f"MCP server communication failed: {e}")

    async def _async_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute tool call asynchronously."""
        if not self._is_initialized:
            await self._async_init_session()

        try:
            logger.debug(f"🔧 Calling MCP tool: {tool_name} with args: {arguments}")

            result = await self._send_jsonrpc("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })

            # Extract text from result
            content = result.get("content", [])
            if not content:
                logger.warning(f"⚠️  MCP tool {tool_name} returned empty content")
                return ""

            # Combine all text content
            texts = []
            for item in content:
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))

            text = "\n".join(texts)
            preview = text[:100] + "..." if len(text) > 100 else text
            logger.debug(f"✅ MCP tool result: {preview}")
            return text

        except Exception as e:
            logger.error(f"❌ MCP tool call failed for {tool_name}: {e}")
            raise RuntimeError(f"MCP tool execution failed: {e}")

    async def _async_close(self):
        """Close session asynchronously."""
        if not self._is_initialized:
            return

        try:
            if self._http_client:
                await self._http_client.aclose()
        except Exception as e:
            logger.warning(f"⚠️  Error during MCP close: {e}")
        finally:
            self._is_initialized = False
            logger.debug("🔌 MCP client connection closed")

    # Synchronous wrappers for backward compatibility
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Fetch tool definitions (sync wrapper)."""
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError(
                "get_tool_definitions() called from async context. "
                "Use 'await client._async_get_tool_definitions()' instead or use the client as async context manager."
            )
        except RuntimeError:
            return asyncio.run(self._async_get_tool_definitions())

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute tool call (sync wrapper)."""
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError(
                "call_tool() called from async context. "
                "Use 'await client._async_call_tool()' instead or use the client as async context manager."
            )
        except RuntimeError:
            return asyncio.run(self._async_call_tool(tool_name, arguments))

    def close(self):
        """Close the MCP session (sync wrapper)."""
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError(
                "close() called from async context. "
                "Use 'await client._async_close()' instead or use the client as async context manager."
            )
        except RuntimeError:
            asyncio.run(self._async_close())


def init_mcp_client(
    step_config: Dict[str, Any],
    pipeline_config: Dict[str, Any]
) -> Optional[MCPClient]:
    """
    Initialize MCP client from step and pipeline configuration.

    Returns None if MCP is not enabled for this step.
    Note: The returned client still needs async initialization.
    """
    if not step_config.get("mcp", {}).get("enabled"):
        return None

    mcp_config = step_config.get("mcp", {})
    server_name = mcp_config.get("server", "bible")
    requested_tools = mcp_config.get("tools", [])

    # Get server config from pipeline-level mcp_servers
    servers = pipeline_config.get("mcp_servers", {})
    server_config = servers.get(server_name)

    if not server_config:
        raise ValueError(
            f"MCP server '{server_name}' not defined in pipeline mcp_servers section. "
            f"Available servers: {list(servers.keys())}"
        )

    server_url = server_config["url"]
    logger.info(f"🔌 Initializing MCP client for server: {server_name}")

    # Return client without initializing (will init on first use)
    client = MCPClient(server_url, requested_tools)
    return client