"""
TDD tests for assume_unregistered_async flag on DependencyAnalyzer.

When a tool is NOT in the local registry (e.g., MCP/integration tools),
the analyzer should assume it's async by default, since external tools
are almost always async HTTP calls.
"""

from unittest.mock import Mock

from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.execution_plan import (
    LiteralNode,
    ToolCallNode,
    VariableNode,
    WhileLoopNode,
)


class TestAssumeUnregisteredAsync:
    """Test the assume_unregistered_async flag behavior."""

    def test_unregistered_tool_assumed_async_by_default(self):
        """An unregistered tool should be assumed async with default settings."""
        analyzer = DependencyAnalyzer(tools={})

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "some_api_call"
        tool_call.original_name = "some_api_call"
        tool_call.arguments = [Mock(spec=LiteralNode, value="x")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True, (
            f"Unregistered tool should be assumed async by default, got: {reason}"
        )

    def test_unregistered_tool_not_async_when_flag_false(self):
        """With assume_unregistered_async=False, unregistered tools are not async."""
        analyzer = DependencyAnalyzer(tools={}, assume_unregistered_async=False)

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "some_api_call"
        tool_call.original_name = "some_api_call"
        tool_call.arguments = []
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert "no async" in reason.lower()

    def test_registered_sync_tool_not_detected_regardless_of_flag(self):
        """A registered sync tool must NOT be detected as async, even with
        assume_unregistered_async=True. The flag only affects unregistered tools."""

        def sync_tool(x):
            return x

        analyzer = DependencyAnalyzer(
            tools={"sync_tool": sync_tool},
            assume_unregistered_async=True,
        )

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "sync_tool"
        tool_call.original_name = "sync_tool"
        tool_call.arguments = [Mock(spec=LiteralNode, value="x")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert "no async" in reason.lower()

    def test_registered_async_tool_still_detected(self):
        """A registered async tool should still be detected regardless of flag."""

        async def async_tool(x):
            return x

        analyzer = DependencyAnalyzer(
            tools={"async_tool": async_tool},
            assume_unregistered_async=False,  # Even with flag off
        )

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "async_tool"
        tool_call.original_name = "async_tool"
        tool_call.arguments = [Mock(spec=LiteralNode, value="x")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True
        assert reason is None

    def test_mcp_prefixed_tool_assumed_async(self):
        """MCP tools (app::virustotal::ip_reputation) are never in the local
        registry. They should be assumed async with the default flag."""
        analyzer = DependencyAnalyzer(tools={})

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "app::virustotal::ip_reputation"
        tool_call.original_name = "ip_reputation"
        tool_call.arguments = [Mock(spec=VariableNode, variable_name="ip")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True, f"MCP tool should be assumed async, got: {reason}"


class TestHasAsyncOperationsInExpression:
    """Test the new public method for checking a single expression."""

    def test_expression_with_async_tool(self):
        """An expression containing an async tool call should be detected."""

        async def fetch(url):
            return url

        analyzer = DependencyAnalyzer(tools={"fetch": fetch})

        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "fetch"
        tool_call.original_name = "fetch"
        tool_call.arguments = [Mock(spec=LiteralNode, value="url")]
        tool_call.named_arguments = {}

        assert analyzer.has_async_operations_in_expression(tool_call) is True

    def test_expression_without_async_tool(self):
        """An expression with only sync operations should not be detected."""
        analyzer = DependencyAnalyzer(tools={}, assume_unregistered_async=False)

        lit = Mock(spec=LiteralNode)
        lit.value = 42

        assert analyzer.has_async_operations_in_expression(lit) is False

    def test_expression_with_unregistered_tool_assumed_async(self):
        """An unregistered tool in an expression should be assumed async."""
        analyzer = DependencyAnalyzer(
            tools={}
        )  # default assume_unregistered_async=True

        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "unknown_api"
        tool_call.original_name = "unknown_api"
        tool_call.arguments = []
        tool_call.named_arguments = {}

        assert analyzer.has_async_operations_in_expression(tool_call) is True
