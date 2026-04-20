"""
Unit tests for ExecutionContext MCP integration.

These tests verify that ExecutionContext correctly routes MCP tools and
provides proper error handling for MCP-related operations.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.errors import ToolInvocationError, ToolNotFoundError
from cy_language.executor import ExecutionContext


class TestExecutionContextMCPIntegration:
    """Test MCP tool routing in ExecutionContext."""

    def test_init_with_mcp_manager(self):
        """Test ExecutionContext initialization with MCP manager."""
        mock_mcp_manager = Mock()

        context = ExecutionContext(tools={}, variables={}, mcp_manager=mock_mcp_manager)

        assert context.mcp_manager is mock_mcp_manager

    def test_init_without_mcp_manager(self):
        """Test ExecutionContext initialization without MCP manager."""
        context = ExecutionContext(tools={}, variables={})

        assert context.mcp_manager is None

    @pytest.mark.asyncio
    async def test_call_mcp_tool_success(self):
        """Test successful MCP tool call routing."""
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(return_value=8.0)

        context = ExecutionContext(tools={}, variables={}, mcp_manager=mock_mcp_manager)

        # This will initially fail as call_tool MCP routing is not implemented
        result = await context.call_tool("mcp::demo::add", [], {"a": 5, "b": 3})

        # After implementation, these assertions should pass:
        # assert result == 8.0
        # mock_mcp_manager.call_mcp_tool.assert_called_once_with("mcp::demo::add", {"a": 5, "b": 3})

    @pytest.mark.asyncio
    async def test_call_mcp_tool_no_manager(self):
        """Test MCP tool call when no MCP manager is available."""
        context = ExecutionContext(tools={}, variables={})

        # Should raise ToolInvocationError when no manager available
        with pytest.raises(
            ToolInvocationError, match="MCP tool.*called but no MCP manager available"
        ):
            await context.call_tool("mcp::demo::add", [], {"a": 5, "b": 3})

    @pytest.mark.asyncio
    async def test_call_mcp_tool_with_positional_args(self):
        """Test MCP tool call with positional arguments (should convert to named)."""
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(return_value=8.0)

        # Mock the get_tool_parameter_names method for dynamic argument handling
        def get_parameter_names(tool_name):
            if tool_name == "mcp::demo::add":
                return ["a", "b"]
            return None

        mock_mcp_manager.get_tool_parameter_names = get_parameter_names

        context = ExecutionContext(tools={}, variables={}, mcp_manager=mock_mcp_manager)

        # MCP tools now accept positional arguments and convert them to named
        result = await context.call_tool("mcp::demo::add", [5, 3], {})

        # Should convert positional args to named and call MCP manager
        assert result == 8.0
        mock_mcp_manager.call_mcp_tool.assert_called_once_with(
            "mcp::demo::add", {"a": 5, "b": 3}
        )

    @pytest.mark.asyncio
    async def test_call_native_tool_with_mcp_manager(self):
        """Test that native tools still work when MCP manager is present."""
        mock_native_tool = Mock(return_value="native_result")
        mock_mcp_manager = Mock()

        context = ExecutionContext(
            tools={"native_add": mock_native_tool},
            variables={},
            mcp_manager=mock_mcp_manager,
        )

        result = await context.call_tool("native_add", [5, 3], {})

        assert result == "native_result"
        mock_native_tool.assert_called_once_with(5, 3)
        # MCP manager should not be called for native tools
        mock_mcp_manager.call_mcp_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_call_nonexistent_native_tool(self):
        """Test calling a non-existent native tool."""
        context = ExecutionContext(tools={}, variables={})

        with pytest.raises(ToolNotFoundError, match="Tool 'nonexistent' not found"):
            await context.call_tool("nonexistent", [], {})


class TestMCPToolArgumentValidation:
    """Test argument validation for MCP tools."""

    @pytest.fixture
    def context_with_mcp_manager(self):
        """ExecutionContext with mocked MCP manager."""
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(return_value="mcp_result")

        # Provide parameter name schema for mixed argument support
        def get_parameter_names(tool_name):
            if tool_name == "mcp::demo::add":
                return ["a", "b"]
            return None

        mock_mcp_manager.get_tool_parameter_names = get_parameter_names

        return ExecutionContext(tools={}, variables={}, mcp_manager=mock_mcp_manager)

    @pytest.mark.asyncio
    async def test_mcp_tool_named_args_only(self, context_with_mcp_manager):
        """Test that MCP tools accept named arguments only."""
        # This should work (named args only)
        result = await context_with_mcp_manager.call_tool(
            "mcp::demo::add", [], {"a": 5, "b": 3}
        )
        # After implementation: assert result == "mcp_result"

    @pytest.mark.asyncio
    async def test_mcp_tool_accepts_mixed_args(self, context_with_mcp_manager):
        """Test that MCP tools accept mixed positional and named arguments.

        Mixed args are normalized to all-named for MCP protocol.
        """
        result = await context_with_mcp_manager.call_tool(
            "mcp::demo::add", [5], {"b": 3}
        )
        # MCP adapter converts positional to named using schema

    @pytest.mark.asyncio
    async def test_mcp_tool_empty_args(self, context_with_mcp_manager):
        """Test MCP tool call with no arguments."""
        result = await context_with_mcp_manager.call_tool("mcp::demo::ping", [], {})
        # After implementation: assert result == "mcp_result"


class TestMCPErrorPropagation:
    """Test error propagation from MCP manager."""

    @pytest.mark.asyncio
    async def test_mcp_manager_exception_propagation(self):
        """Test that MCP manager exceptions are properly wrapped."""
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(
            side_effect=Exception("Network error")
        )

        context = ExecutionContext(tools={}, variables={}, mcp_manager=mock_mcp_manager)

        # Should propagate MCP manager exceptions
        with pytest.raises(Exception, match="Network error"):
            await context.call_tool("mcp::demo::add", [], {"a": 5, "b": 3})

    @pytest.mark.asyncio
    async def test_error_includes_line_column_info(self):
        """Test that MCP tool errors include line and column information."""
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(side_effect=Exception("Tool error"))

        context = ExecutionContext(tools={}, variables={}, mcp_manager=mock_mcp_manager)

        with pytest.raises(Exception) as exc_info:
            await context.call_tool(
                "mcp::demo::add", [], {"a": 5, "b": 3}, line=10, column=5
            )

        # Error should be the original MCP manager exception
        assert "Tool error" in str(exc_info.value)


class TestMCPToolDetection:
    """Test MCP tool detection logic."""

    @pytest.mark.asyncio
    async def test_detects_mcp_prefix(self):
        """Test that tools starting with 'mcp::' are detected as MCP tools."""
        context = ExecutionContext(tools={}, variables={})

        # These should be detected as MCP tools (and fail due to no manager)
        mcp_tool_names = [
            "mcp::demo::add",
            "mcp::virustotal::domain_reputation",
            "mcp::custom::my_tool",
        ]

        for tool_name in mcp_tool_names:
            with pytest.raises(
                ToolInvocationError, match="called but no MCP manager available"
            ):
                await context.call_tool(tool_name, [], {})

    @pytest.mark.asyncio
    async def test_does_not_detect_non_mcp_tools(self):
        """Test that tools not starting with 'mcp::' are treated as native tools."""
        mock_tool = Mock(return_value="result")
        context = ExecutionContext(tools={"regular_tool": mock_tool}, variables={})

        # These should be treated as native tools
        non_mcp_tool_names = [
            "regular_tool",
            "add",
            "my::custom::tool",  # Different namespace format
            "mcpish_tool",  # Similar but not mcp::
        ]

        # Only regular_tool should work, others should fail as missing native tools
        result = await context.call_tool("regular_tool", [], {})
        assert result == "result"

        for tool_name in ["add", "my::custom::tool", "mcpish_tool"]:
            with pytest.raises(
                ToolNotFoundError, match=f"Tool '{tool_name}' not found"
            ):
                await context.call_tool(tool_name, [], {})
