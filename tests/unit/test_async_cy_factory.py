"""
Unit tests for async Cy interpreter factory methods.

These tests focus on verifying that the async factory methods work correctly
and that the Cy interpreter can be created and used in async contexts.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cy_language.interpreter import Cy


class TestAsyncCyFactory:
    """Test async factory methods for Cy interpreter."""

    @pytest.mark.asyncio
    async def test_cy_create_async_factory_basic(self):
        """Test basic async factory method without MCP servers."""
        # Test creating interpreter without MCP servers
        interpreter = await Cy.create_async()

        assert interpreter is not None
        assert interpreter.mcp_manager is None
        # Now includes default native tools (len, etc.)
        assert "len" in interpreter.tools

    @pytest.mark.asyncio
    async def test_cy_create_async_factory_with_mcp(self):
        """Test async factory method with MCP servers."""
        # Mock the MCP manager initialization
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [{"name": "add", "description": "Add two numbers", "schema": {}}]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            mcp_config = {"demo": {"base_url": "http://test", "mcp_id": "demo"}}
            interpreter = await Cy.create_async(mcp_servers=mcp_config)

            assert interpreter is not None
            assert interpreter.mcp_manager is not None
            assert interpreter.mcp_manager._initialized is True
            assert "mcp::demo::add" in interpreter.mcp_manager.tools_cache

    @pytest.mark.asyncio
    async def test_cy_create_async_with_tools_and_variables(self):
        """Test async factory with custom tools and variables."""
        tools = {"test_tool": lambda x: x * 2}
        variables = {"test_var": "test_value"}

        interpreter = await Cy.create_async(
            tools=tools, variables=variables, interpolation_mode="csv"
        )

        assert interpreter is not None
        # Tools now include native tools + user tools
        assert "test_tool" in interpreter.tools
        assert "len" in interpreter.tools  # Native tool
        assert interpreter.external_variables == variables
        assert interpreter.interpolation_mode == "csv"

    @pytest.mark.asyncio
    async def test_cy_create_async_no_event_loop_conflicts(self):
        """Test that create_async works in existing event loop context."""
        # This test itself runs in an async event loop (pytest-asyncio)
        # So this verifies no asyncio.run() conflicts occur

        mock_response = Mock()
        mock_response.json.return_value = {"tools": []}
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # This should not raise "asyncio.run() cannot be called from a running event loop"
            mcp_config = {"demo": {"base_url": "http://test", "mcp_id": "demo"}}
            interpreter = await Cy.create_async(mcp_servers=mcp_config)

            assert interpreter is not None
            assert interpreter.mcp_manager._initialized is True

    @pytest.mark.asyncio
    async def test_cy_create_async_error_handling(self):
        """Test that create_async handles MCP initialization errors gracefully."""
        with patch("httpx.AsyncClient") as mock_client:
            # Simulate HTTP error during MCP initialization
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Network error")
            )

            mcp_config = {"demo": {"base_url": "http://test", "mcp_id": "demo"}}

            # Should not raise exception, just log warnings
            interpreter = await Cy.create_async(mcp_servers=mcp_config)

            assert interpreter is not None
            assert interpreter.mcp_manager is not None
            assert (
                interpreter.mcp_manager._initialized is True
            )  # Still marked as initialized
            assert len(interpreter.mcp_manager.tools_cache) == 0  # But no tools cached

    @pytest.mark.asyncio
    async def test_cy_create_async_multiple_mcp_servers(self):
        """Test async factory with multiple MCP servers."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [{"name": "test_tool", "description": "Test tool", "schema": {}}]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            mcp_config = {
                "server1": {"base_url": "http://server1", "mcp_id": "server1"},
                "server2": {"base_url": "http://server2", "mcp_id": "server2"},
            }

            interpreter = await Cy.create_async(mcp_servers=mcp_config)

            assert interpreter is not None
            assert interpreter.mcp_manager is not None
            assert "mcp::server1::test_tool" in interpreter.mcp_manager.tools_cache
            assert "mcp::server2::test_tool" in interpreter.mcp_manager.tools_cache

    @pytest.mark.asyncio
    async def test_cy_create_async_preserves_parameters(self):
        """Test that create_async preserves all initialization parameters."""
        tools = {"custom": lambda: "result"}
        variables = {"var1": 123, "var2": "test"}

        interpreter = await Cy.create_async(
            tools=tools,
            variables=variables,
            interpolation_mode="xml",
            item_tag="element",
        )

        # Tools now include native tools + user tools
        assert "custom" in interpreter.tools
        assert "len" in interpreter.tools  # Native tool
        assert interpreter.external_variables == variables
        assert interpreter.interpolation_mode == "xml"
        assert interpreter.item_tag == "element"
