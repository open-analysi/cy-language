"""
Unit tests for MCPManager class.

These tests use mocked HTTP responses and do not require external dependencies.
All tests should run fast and be suitable for continuous integration.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cy_language.mcp_manager import MCPManager


class TestMCPManagerInitialization:
    """Test MCPManager initialization scenarios."""

    def test_init_with_valid_servers(self):
        """Test initialization with valid server configurations."""
        servers = {
            "demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"},
            "virustotal": {"base_url": "http://localhost:8000", "mcp_id": "virustotal"},
        }

        manager = MCPManager(servers)

        assert manager.servers == servers
        assert manager.tools_cache == {}
        assert manager._initialized is False

    def test_init_with_none_servers(self):
        """Test initialization with None server configuration."""
        manager = MCPManager(None)

        assert manager.servers == {}
        assert manager.tools_cache == {}
        assert manager._initialized is False

    def test_init_with_empty_servers(self):
        """Test initialization with empty server configuration."""
        manager = MCPManager({})

        assert manager.servers == {}
        assert manager.tools_cache == {}
        assert manager._initialized is False


class TestMCPManagerToolDiscovery:
    """Test tool discovery with mocked HTTP responses."""

    @pytest.fixture
    def demo_servers(self):
        """Sample server configuration for testing."""
        return {"demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}}

    @pytest.fixture
    def demo_tools_response(self):
        """Sample tools response for testing."""
        return {
            "tools": [
                {"name": "add", "description": "Add two numbers"},
                {"name": "multiply", "description": "Multiply two numbers"},
                {"name": "text_length", "description": "Get length of text"},
            ]
        }

    @pytest.mark.asyncio
    async def test_initialize_success(self, demo_servers, demo_tools_response):
        """Test successful tool discovery and caching."""
        manager = MCPManager(demo_servers)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = demo_tools_response

            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            await manager.initialize()

            assert manager._initialized is True
            assert "mcp::demo::add" in manager.tools_cache
            assert "mcp::demo::multiply" in manager.tools_cache
            assert "mcp::demo::text_length" in manager.tools_cache

    @pytest.mark.asyncio
    async def test_initialize_http_error(self, demo_servers):
        """Test handling of HTTP errors during discovery."""
        manager = MCPManager(demo_servers)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 500")

            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Should not raise exception, but log warning
            await manager.initialize()

            # Manager should be marked as initialized even if servers failed
            assert manager._initialized is True
            # Tools cache should remain empty on error
            assert manager.tools_cache == {}


class TestMCPManagerToolExecution:
    """Test tool execution with mocked HTTP responses."""

    @pytest.fixture
    def initialized_manager(self):
        """MCPManager with sample tools cached."""
        manager = MCPManager(
            {"demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}}
        )

        # Manually populate cache for testing
        manager.tools_cache = {
            "mcp::demo::add": {
                "server": "demo",
                "base_url": "http://localhost:8000",
                "mcp_id": "demo",
                "tool_name": "add",
                "description": "Add two numbers",
                "schema": {},
            }
        }
        manager._initialized = True

        return manager

    @pytest.mark.asyncio
    async def test_call_mcp_tool_success(self, initialized_manager):
        """Test successful MCP tool execution."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"result": 8.0}

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await initialized_manager.call_mcp_tool(
                "mcp::demo::add", {"a": 5, "b": 3}
            )

            assert result == 8.0

    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self, initialized_manager):
        """Test calling a tool that doesn't exist."""
        with pytest.raises(
            KeyError, match="MCP tool 'mcp::demo::nonexistent' not found"
        ):
            await initialized_manager.call_mcp_tool("mcp::demo::nonexistent", {})

    @pytest.mark.asyncio
    async def test_call_mcp_tool_http_error(self, initialized_manager):
        """Test handling of HTTP errors during tool execution."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 500")

            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Should raise appropriate exception
            with pytest.raises(Exception):
                await initialized_manager.call_mcp_tool(
                    "mcp::demo::add", {"a": 5, "b": 3}
                )


class TestMCPManagerToolListing:
    """Test tool listing functionality."""

    @pytest.mark.asyncio
    async def test_get_available_tools_empty(self):
        """Test getting available tools when cache is empty."""
        manager = MCPManager()
        tools = await manager.get_available_tools()
        assert tools == []

    @pytest.mark.asyncio
    async def test_get_available_tools_populated(self):
        """Test getting available tools when cache is populated."""
        manager = MCPManager()
        manager.tools_cache = {
            "mcp::demo::add": {},
            "mcp::demo::multiply": {},
            "mcp::virustotal::domain_reputation": {},
        }

        tools = await manager.get_available_tools()
        expected_tools = [
            "mcp::demo::add",
            "mcp::demo::multiply",
            "mcp::virustotal::domain_reputation",
        ]

        assert sorted(tools) == sorted(expected_tools)
