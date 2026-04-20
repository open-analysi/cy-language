"""Integration tests for unified calling patterns across all function types."""

import os
from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.executor import ExecutionContext
from cy_language.ui.tools import default_registry


class TestNativeFunctionBothPatterns:
    """Test native functions with both positional and named arguments."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use actual native functions from the registry
        tools = default_registry.get_tools_dict()
        self.context = ExecutionContext(tools=tools)

    @pytest.mark.asyncio
    async def test_len_positional_and_named_identical_results(self):
        """Test len() function with both calling patterns produces identical results."""
        test_list = [1, 2, 3]

        # Test positional call - len_function takes 'arg' parameter
        result1 = await self.context.call_tool("len", [test_list], {})

        # Test named call - use correct parameter name 'arg'
        result2 = await self.context.call_tool("len", [], {"arg": test_list})

        # Results should be identical
        assert result1 == result2
        assert result1 == 3

    @pytest.mark.asyncio
    async def test_debug_print_both_patterns(self):
        """Test log() with both calling patterns (renamed from debug_print)."""
        message = "Test debug message"

        # Test positional call - log function takes 'message' parameter
        result1 = await self.context.call_tool("log", [message], {})

        # Test named call
        result2 = await self.context.call_tool("log", [], {"message": message})

        # Both should return the message string (log returns what it logged)
        assert result1 == message
        assert result2 == message
        assert result1 == result2


class TestMCPFunctionBothPatterns:
    """Test MCP functions with both positional and named arguments."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock MCP manager with proper parameter name support
        self.mock_mcp_manager = Mock()
        self.mock_mcp_manager.call_mcp_tool = AsyncMock(return_value=8)

        # Mock the get_tool_parameter_names method for dynamic argument handling
        def get_parameter_names(tool_name):
            if tool_name == "mcp::demo::add":
                return ["a", "b"]
            return None

        self.mock_mcp_manager.get_tool_parameter_names = get_parameter_names

        self.context = ExecutionContext(mcp_manager=self.mock_mcp_manager)

    @pytest.mark.asyncio
    async def test_mcp_add_positional_converted_to_named(self):
        """Test MCP add function converts positional args to named."""
        # Test positional call to MCP function
        result = await self.context.call_tool("mcp::demo::add", [5, 3], {})

        # Should call MCP manager with named arguments
        self.mock_mcp_manager.call_mcp_tool.assert_called_with(
            "mcp::demo::add", {"a": 5, "b": 3}
        )
        assert result == 8

    @pytest.mark.asyncio
    async def test_mcp_add_named_unchanged(self):
        """Test MCP add function with named arguments stays unchanged."""
        # Test named call to MCP function
        result = await self.context.call_tool("mcp::demo::add", [], {"a": 5, "b": 3})

        # Should call MCP manager with same named arguments
        self.mock_mcp_manager.call_mcp_tool.assert_called_with(
            "mcp::demo::add", {"a": 5, "b": 3}
        )
        assert result == 8


class TestLLMFunctionBothPatterns:
    """Test LLM functions with both positional and named arguments."""

    def setup_method(self):
        """Set up test fixtures."""
        from cy_language.llm_functions import llm_registry

        # Use actual LLM functions from the registry - combine default and LLM tools
        tools = default_registry.get_tools_dict()
        tools.update(llm_registry.get_tools_dict())
        self.context = ExecutionContext(tools=tools)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    )
    async def test_llm_run_both_patterns(self):
        """Test llm_run with both positional and named arguments."""
        prompt = "Tell me a story"

        # Test positional call (this will actually call the LLM - might be slow)
        result1 = await self.context.call_tool("llm_run", [prompt], {})

        # Test named call
        result2 = await self.context.call_tool("llm_run", [], {"prompt": prompt})

        # Both should produce string results (actual LLM responses may vary)
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        # Note: We can't assert they're identical since LLM responses may vary

    @pytest.mark.asyncio
    async def test_llm_function_argument_normalization(self):
        """Test LLM function argument normalization without actual LLM calls."""

        # Create a simple mock LLM function for testing
        async def mock_llm_eval(prompt: str, results: str, goals: str) -> bool:
            return len(prompt) > 0 and len(results) > 0 and len(goals) > 0

        # Add mock to tools temporarily
        self.context.tools["llm_evaluate_results"] = mock_llm_eval

        # Test positional call
        result1 = await self.context.call_tool(
            "llm_evaluate_results", ["task", "result", "goals"], {}
        )

        # Test named call
        result2 = await self.context.call_tool(
            "llm_evaluate_results",
            [],
            {"prompt": "task", "results": "result", "goals": "goals"},
        )

        # Both should produce the same result
        assert result1 == result2 is True


class TestMixedFunctionTypesInProgram:
    """Test programs that use multiple function types with different calling patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use actual native functions plus mock MCP manager
        tools = default_registry.get_tools_dict()

        self.mock_mcp_manager = Mock()
        self.mock_mcp_manager.call_mcp_tool = AsyncMock(return_value=8)

        # Mock the get_tool_parameter_names method for dynamic argument handling
        def get_parameter_names(tool_name):
            if tool_name == "mcp::demo::add":
                return ["a", "b"]
            return None

        self.mock_mcp_manager.get_tool_parameter_names = get_parameter_names

        self.context = ExecutionContext(tools=tools, mcp_manager=self.mock_mcp_manager)

    @pytest.mark.asyncio
    async def test_mixed_calling_patterns_in_sequence(self):
        """Test sequence of different function types with mixed calling patterns."""
        # Native function with positional args
        result1 = await self.context.call_tool("len", [[1, 2, 3]], {})

        # MCP function with positional args (should convert to named)
        result2 = await self.context.call_tool("mcp::demo::add", [5, 3], {})

        # Add a simple mock LLM function to avoid actual API calls
        async def mock_llm(prompt: str) -> str:
            return f"Response to: {prompt}"

        self.context.tools["llm_run"] = mock_llm

        # LLM function with named args
        result3 = await self.context.call_tool("llm_run", [], {"prompt": "test"})

        # All should work correctly
        assert result1 == 3
        assert result2 == 8
        assert result3 == "Response to: test"

        # Verify MCP was called with converted named arguments
        self.mock_mcp_manager.call_mcp_tool.assert_called_with(
            "mcp::demo::add", {"a": 5, "b": 3}
        )


class TestArgumentErrorHandling:
    """Test error handling for invalid argument patterns."""

    def setup_method(self):
        """Set up test fixtures."""

        # Add minimal tools for testing
        def simple_func(a: int) -> int:
            return a

        def len_func(arg) -> int:
            return len(arg) if hasattr(arg, "__len__") else 0

        tools = {"test_func": simple_func, "len": len_func}

        self.context = ExecutionContext(tools=tools)

    @pytest.mark.asyncio
    async def test_invalid_positional_argument_count(self):
        """Test clear error when too many positional arguments provided."""
        # test_func only takes 1 argument, but we're passing 5
        from cy_language.errors import ToolInvocationError

        with pytest.raises(ToolInvocationError, match="Too many.*arguments"):
            await self.context.call_tool("test_func", [1, 2, 3, 4, 5], {})

    @pytest.mark.asyncio
    async def test_invalid_named_argument_names(self):
        """Test clear error when invalid parameter names used."""

        # This will fail because test_func doesn't have an 'invalid_param' parameter
        with pytest.raises(Exception):  # Could be various error types
            await self.context.call_tool("test_func", [], {"invalid_param": 123})

    @pytest.mark.asyncio
    async def test_duplicate_positional_and_named_error(self):
        """Test error when same param provided both positionally and by name."""
        from cy_language.errors import ToolInvocationError

        # len() has one param 'arg': providing both positionally and by name is a duplicate
        with pytest.raises(ToolInvocationError, match="both positionally and by name"):
            await self.context.call_tool("len", [[1, 2]], {"arg": [3, 4]})

    @pytest.mark.asyncio
    async def test_mcp_function_not_found_error(self):
        """Test error handling when MCP function doesn't exist."""
        from cy_language.errors import ToolInvocationError

        with pytest.raises(
            ToolInvocationError, match="MCP tool.*called but no MCP manager available"
        ):
            await self.context.call_tool("mcp::nonexistent::tool", [], {})


class TestBackwardCompatibility:
    """Test that existing functionality remains unchanged."""

    def setup_method(self):
        """Set up test fixtures with real function calls."""

        # Add a simple len function for testing
        def len_func(arg):
            return len(arg) if hasattr(arg, "__len__") else 0

        tools = {"len": len_func}
        self.context = ExecutionContext(tools=tools)

    @pytest.mark.asyncio
    async def test_existing_native_calls_unchanged(self):
        """Test that all existing native function calls work identically."""
        # This should work exactly as before
        result = await self.context.call_tool("len", [[1, 2, 3, 4, 5]], {})

        assert result == 5  # Length of the list

    @pytest.mark.asyncio
    async def test_existing_mcp_calls_unchanged(self):
        """Test that existing MCP calls work identically."""
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(return_value="mcp_result")

        context = ExecutionContext(mcp_manager=mock_mcp_manager)

        # Existing MCP named calls should work unchanged
        result = await context.call_tool("mcp::demo::test", [], {"param": "value"})

        assert result == "mcp_result"
        mock_mcp_manager.call_mcp_tool.assert_called_with(
            "mcp::demo::test", {"param": "value"}
        )
