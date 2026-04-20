"""
Unit tests for async MCP Manager functionality.

These tests focus on verifying that the MCP Manager works correctly
in async contexts without asyncio.run() conflicts.
"""

import warnings
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cy_language.mcp_manager import MCPManager


class TestAsyncMCPManager:
    """Test async functionality of MCPManager."""

    @pytest.mark.asyncio
    async def test_mcp_manager_async_initialization(self):
        """Test that MCP manager initializes properly in async context."""
        # Mock the HTTP client to avoid real network calls
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "schema": {"type": "function"},
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            manager = MCPManager(
                {"demo": {"base_url": "http://test", "mcp_id": "demo"}}
            )

            # This should work without raising event loop conflicts
            await manager.initialize()

            assert manager._initialized is True
            assert "mcp::demo::add" in manager.tools_cache

    @pytest.mark.asyncio
    async def test_no_unawaited_coroutine_warnings(self):
        """Test that all coroutines are properly awaited."""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.json.return_value = {"tools": []}
        mock_response.raise_for_status.return_value = None

        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                manager = MCPManager(
                    {"demo": {"base_url": "http://test", "mcp_id": "demo"}}
                )
                await manager.initialize()

                # Check no RuntimeWarning about unawaited coroutines
                runtime_warnings = [
                    w for w in warning_list if issubclass(w.category, RuntimeWarning)
                ]
                unawaited_warnings = [
                    w for w in runtime_warnings if "never awaited" in str(w.message)
                ]
                assert len(unawaited_warnings) == 0, (
                    f"Found unawaited coroutine warnings: {unawaited_warnings}"
                )

    @pytest.mark.asyncio
    async def test_async_tool_call(self):
        """Test that async tool calling works without event loop conflicts."""
        # Mock HTTP responses for both tool discovery and execution
        discovery_response = Mock()
        discovery_response.json.return_value = {
            "tools": [
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "schema": {"type": "function"},
                    "parameters": {
                        "properties": {"a": {"type": "number"}, "b": {"type": "number"}}
                    },
                }
            ]
        }
        discovery_response.raise_for_status.return_value = None

        execution_response = Mock()
        execution_response.json.return_value = {"result": 42}
        execution_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            # Mock both GET (discovery) and POST (execution) calls
            async_client = mock_client.return_value.__aenter__.return_value
            async_client.get = AsyncMock(return_value=discovery_response)
            async_client.post = AsyncMock(return_value=execution_response)

            manager = MCPManager(
                {"demo": {"base_url": "http://test", "mcp_id": "demo"}}
            )
            await manager.initialize()

            # Test async tool call
            result = await manager._async_call_tool(
                "mcp::demo::add", {"a": 15, "b": 27}
            )
            assert result == 42

    @pytest.mark.asyncio
    async def test_async_tool_schema_access(self):
        """Test that tool schema access works after async initialization."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "schema": {"inputSchema": {"properties": {"a": {}, "b": {}}}},
                    "parameters": {
                        "properties": {"a": {"type": "number"}, "b": {"type": "number"}}
                    },
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            manager = MCPManager(
                {"demo": {"base_url": "http://test", "mcp_id": "demo"}}
            )
            await manager.initialize()

            # Test schema access
            schema = await manager.get_tool_schema("mcp::demo::add")
            assert schema is not None
            assert "inputSchema" in schema

            # Test parameter names
            param_names = await manager.get_tool_parameter_names("mcp::demo::add")
            assert param_names == ["a", "b"]

    @pytest.mark.asyncio
    async def test_async_initialization_error_handling(self):
        """Test that async initialization handles errors gracefully."""
        with patch("httpx.AsyncClient") as mock_client:
            # Simulate HTTP error
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Network error")
            )

            manager = MCPManager(
                {"demo": {"base_url": "http://test", "mcp_id": "demo"}}
            )

            # Should not raise exception, just log warning
            await manager.initialize()

            # Manager should still be marked as initialized even if servers failed
            assert manager._initialized is True
            # But no tools should be cached
            assert len(manager.tools_cache) == 0

    @pytest.mark.asyncio
    async def test_multiple_servers_async_initialization(self):
        """Test async initialization with multiple MCP servers."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {"name": "server1_tool", "description": "Test tool", "schema": {}}
            ]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            servers_config = {
                "server1": {"base_url": "http://server1", "mcp_id": "server1"},
                "server2": {"base_url": "http://server2", "mcp_id": "server2"},
            }

            manager = MCPManager(servers_config)
            await manager.initialize()

            assert manager._initialized is True
            # Should have tools from both servers
            assert "mcp::server1::server1_tool" in manager.tools_cache
            assert (
                "mcp::server2::server1_tool" in manager.tools_cache
            )  # Same tool from both servers
