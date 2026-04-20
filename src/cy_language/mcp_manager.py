"""
MCP Manager for handling remote Model Context Protocol server integration.

This module provides a simplified interface for discovering and executing tools
from remote MCP servers via HTTP API calls.
"""

from typing import Any, cast

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

_MISSING_HTTPX_MSG = (
    "httpx is required for MCP server support. "
    "Install it with: pip install cy-language[mcp]"
)


def _require_httpx() -> None:
    if httpx is None:
        raise ImportError(_MISSING_HTTPX_MSG)


class MCPManager:
    """
    Manager for MCP (Model Context Protocol) server integration.

    Provides HTTP client functionality combined with tool registry for
    discovering and executing tools from remote MCP servers.
    """

    def __init__(self, servers: dict[str, dict[str, str]] | None = None):
        """
        Initialize MCP manager with server configurations.

        Args:
            servers: Dict mapping server names to config dicts with 'base_url' and 'mcp_id'
                    Format: {"demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}}
        """
        self.servers = servers or {}
        self.tools_cache: dict[str, dict] = {}  # mcp::namespace::tool -> metadata
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all MCP servers."""
        if not self._initialized:
            await self._async_initialize()
            self._initialized = True

    async def _async_initialize(self) -> None:
        """Discover tools from all configured servers."""
        for server_name, config in self.servers.items():
            # Validate config is a dictionary
            if not isinstance(config, dict):
                print(
                    f"Warning: Invalid config format for server '{server_name}': expected dict, got {type(config).__name__}"
                )
                continue

            base_url = config.get("base_url")
            mcp_id = config.get("mcp_id", server_name)

            # Validate required fields
            if not base_url:
                print(f"Warning: Missing 'base_url' for MCP server '{server_name}'")
                continue

            if not mcp_id:
                print(f"Warning: Missing 'mcp_id' for MCP server '{server_name}'")
                continue

            if not base_url:
                continue

            try:
                _require_httpx()
                async with httpx.AsyncClient() as client:
                    # Discover tools from server using correct API endpoint
                    response = await client.get(
                        f"{base_url}/v1/default/mcps/{mcp_id}/tools"
                    )
                    response.raise_for_status()
                    tools_data = response.json()

                    # Cache tools with mcp::server::tool format
                    for tool in tools_data.get("tools", []):
                        tool_name = tool.get("name")
                        if tool_name:
                            namespaced_name = f"mcp::{server_name}::{tool_name}"
                            self.tools_cache[namespaced_name] = {
                                "server": server_name,
                                "base_url": base_url,
                                "mcp_id": mcp_id,
                                "tool_name": tool_name,
                                "description": tool.get("description", ""),
                                "schema": tool.get("schema", {}),
                                "metadata": tool,
                            }
            except Exception as e:
                # Log error but don't fail initialization
                print(f"Warning: Could not initialize MCP server {server_name}: {e}")

    async def call_mcp_tool(self, tool_name: str, kwargs: dict[str, Any]) -> Any:
        """Call an MCP tool."""
        return await self._async_call_tool(tool_name, kwargs)

    async def _async_call_tool(self, tool_name: str, kwargs: dict[str, Any]) -> Any:
        """Execute MCP tool call."""
        # Ensure initialization
        if not self._initialized:
            await self._async_initialize()
            self._initialized = True

        # Check if tool exists in cache
        if tool_name not in self.tools_cache:
            raise KeyError(f"MCP tool '{tool_name}' not found")

        tool_info = self.tools_cache[tool_name]
        base_url = tool_info["base_url"]
        actual_tool_name = tool_info["tool_name"]

        # Make HTTP POST request to execute tool using correct API endpoint
        _require_httpx()
        async with httpx.AsyncClient() as client:
            payload = {"tool": actual_tool_name, "arguments": kwargs}

            response = await client.post(
                f"{base_url}/v1/default/mcps/{tool_info['mcp_id']}/invoke",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()  # This will raise for non-200 status codes

            result = response.json()
            return result.get("result")

    async def get_available_tools(self) -> list[str]:
        """Get list of all available MCP tools."""
        return list(self.tools_cache.keys())

    async def get_tool_schema(self, tool_name: str) -> dict | None:
        """Get schema for a specific MCP tool.

        Args:
            tool_name: Full tool name in format mcp::server::tool

        Returns:
            Tool schema dict or None if tool not found
        """
        if not self._initialized:
            await self.initialize()

        tool_info = self.tools_cache.get(tool_name)
        if tool_info:
            return cast(dict[Any, Any], tool_info.get("schema", {}))
        return None

    async def get_tool_parameter_names(self, tool_name: str) -> list[str] | None:
        """Get parameter names for an MCP tool from its schema.

        Args:
            tool_name: Full tool name in format mcp::server::tool

        Returns:
            List of parameter names or None if tool/schema not found
        """
        if not self._initialized:
            await self.initialize()

        tool_info = self.tools_cache.get(tool_name)
        if not tool_info:
            return None

        # Extract parameter names from multiple possible locations
        # Try metadata.parameters.properties first (common format)
        metadata = tool_info.get("metadata", {})
        parameters = metadata.get("parameters", {})
        properties = parameters.get("properties", {})

        if properties:
            return list(properties.keys())

        # Fallback: try schema.inputSchema.properties
        schema = tool_info.get("schema", {})
        input_schema = schema.get("inputSchema", {})
        properties = input_schema.get("properties", {})

        if properties:
            return list(properties.keys())

        return None
