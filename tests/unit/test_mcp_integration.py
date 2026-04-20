"""
Integration tests for MCP support in full Cy programs.

These tests verify that MCP tools work correctly in complete Cy programs
with mocked MCP manager. No external dependencies required.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.interpreter import Cy


class TestMCPIntegrationBasic:
    """Test basic MCP tool integration in Cy programs."""

    @pytest.fixture
    def mock_mcp_manager(self):
        """Create a mocked MCP manager for testing."""
        manager = Mock()
        manager.call_mcp_tool = AsyncMock(side_effect=self._mock_tool_responses)
        manager.initialize = AsyncMock()
        manager.get_available_tools = AsyncMock(
            return_value=[
                "mcp::demo::add",
                "mcp::demo::multiply",
                "mcp::demo::text_length",
            ]
        )

        # Add tools_cache for tool resolution
        manager.tools_cache = {
            "mcp::demo::add": {"name": "add", "parameters": ["a", "b"]},
            "mcp::demo::multiply": {"name": "multiply", "parameters": ["a", "b"]},
            "mcp::demo::text_length": {"name": "text_length", "parameters": ["text"]},
        }

        # Mock parameter name mapping for proper argument handling
        def get_parameter_names(tool_name):
            if tool_name == "mcp::demo::add" or tool_name == "mcp::demo::multiply":
                return ["a", "b"]
            if tool_name == "mcp::demo::text_length":
                return ["text"]
            return None

        manager.get_tool_parameter_names = get_parameter_names
        return manager

    def _mock_tool_responses(self, tool_name, kwargs):
        """Mock responses for different MCP tools."""
        if tool_name == "mcp::demo::add":
            return kwargs.get("a", 0) + kwargs.get("b", 0)
        if tool_name == "mcp::demo::multiply":
            return kwargs.get("a", 1) * kwargs.get("b", 1)
        if tool_name == "mcp::demo::text_length":
            return len(kwargs.get("text", ""))
        raise Exception(f"Unknown tool: {tool_name}")

    @pytest.mark.asyncio
    async def test_simple_mcp_tool_call(self, mock_mcp_manager):
        """Test a simple MCP tool call in a Cy program."""
        cy = await Cy.create_async(
            mcp_servers={
                "demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}
            }
        )
        cy.mcp_manager = mock_mcp_manager  # Inject mock

        program = """
        result = mcp::demo::add(a=5, b=3)
        output = "Result: ${result}"
        return output
        """

        output = await cy.run_async(program)
        assert output == '"Result: 8"'

    @pytest.mark.asyncio
    async def test_multiple_mcp_tool_calls(self, mock_mcp_manager):
        """Test multiple MCP tool calls in one program."""
        cy = await Cy.create_async()
        cy.mcp_manager = mock_mcp_manager

        program = """
        total = mcp::demo::add(a=10, b=20)
        product = mcp::demo::multiply(a=4, b=5)
        output = "Sum: ${total}, Product: ${product}"
        return output
        """

        output = await cy.run_async(program)
        assert output == '"Sum: 30, Product: 20"'

    @pytest.mark.asyncio
    async def test_mcp_tool_in_string_interpolation(self, mock_mcp_manager):
        """Test MCP tool result in string interpolation."""
        cy = await Cy.create_async()
        cy.mcp_manager = mock_mcp_manager

        program = """
        text = "Hello World"
        output = "Text length is: ${mcp::demo::text_length(text=text)}"
        return output
        """

        output = await cy.run_async(program)

        # MCP tools now work correctly in string interpolation!
        # The mock returns len(text) = 11 for "Hello World"
        assert output == '"Text length is: 11"'


class TestMCPWithNativeTools:
    """Test mixing MCP tools with native Cy tools."""

    @pytest.fixture
    def mock_mcp_manager(self):
        """Mocked MCP manager."""
        manager = Mock()
        manager.call_mcp_tool = AsyncMock(return_value=42)
        manager.initialize = AsyncMock()
        # Add tools_cache for tool resolution
        manager.tools_cache = {
            "mcp::demo::special_calc": {
                "name": "special_calc",
                "parameters": ["value"],
            },
            "mcp::demo::process": {"name": "process", "parameters": ["data"]},
            "mcp::demo::get_number": {"name": "get_number", "parameters": []},
        }
        return manager

    @pytest.fixture
    def native_tools(self):
        """Sample native tools."""

        def native_add(a, b):
            return a + b

        return {"native_add": native_add}

    @pytest.mark.asyncio
    async def test_native_and_mcp_tools_together(self, mock_mcp_manager, native_tools):
        """Test using both native and MCP tools in the same program."""
        cy = await Cy.create_async(tools=native_tools)
        cy.mcp_manager = mock_mcp_manager

        program = """
        native_result = native_add(5, 10)
        mcp_result = mcp::demo::special_calc(value=100)
        output = "Native: ${native_result}, MCP: ${mcp_result}"
        return output
        """

        output = await cy.run_async(program)
        assert output == '"Native: 15, MCP: 42"'

    @pytest.mark.asyncio
    async def test_mcp_tool_result_to_native_tool(self, mock_mcp_manager, native_tools):
        """Test passing MCP tool result to native tool."""
        mock_mcp_manager.call_mcp_tool = AsyncMock(return_value=25)

        cy = await Cy.create_async(tools=native_tools)
        cy.mcp_manager = mock_mcp_manager

        program = """
        mcp_value = mcp::demo::get_number()
        final_result = native_add(mcp_value, 5)
        output = "Final: ${final_result}"
        return output
        """

        output = await cy.run_async(program)
        assert output == '"Final: 30"'


class TestMCPInControlFlow:
    """Test MCP tools in control flow structures."""

    @pytest.fixture
    def mock_mcp_manager(self):
        """Mocked MCP manager for control flow tests."""
        manager = Mock()

        def mock_response(tool_name, kwargs):
            if tool_name == "mcp::demo::random_number":
                # Return different values to test control flow
                return kwargs.get("seed", 5)
            if tool_name == "mcp::demo::is_even":
                return kwargs.get("number", 0) % 2 == 0
            return 0

        manager.call_mcp_tool = AsyncMock(side_effect=mock_response)
        manager.initialize = AsyncMock()
        # Add tools_cache for tool resolution
        manager.tools_cache = {
            "mcp::demo::random_number": {
                "name": "random_number",
                "parameters": ["seed"],
            },
            "mcp::demo::is_even": {"name": "is_even", "parameters": ["number"]},
            "mcp::demo::should_continue": {
                "name": "should_continue",
                "parameters": ["iteration"],
            },
        }
        return manager

    @pytest.mark.asyncio
    async def test_mcp_tool_in_if_condition(self, mock_mcp_manager):
        """Test MCP tool in if statement condition."""
        cy = await Cy.create_async()
        cy.mcp_manager = mock_mcp_manager

        program = """
        number = 6
        if (mcp::demo::is_even(number=number)) {
            output = "Number is even"
        } else {
            output = "Number is odd"
        }
        return output
        """

        output = await cy.run_async(program)
        assert output == '"Number is even"'

    @pytest.mark.asyncio
    async def test_mcp_tool_in_while_loop(self, mock_mcp_manager):
        """Test MCP tool in while loop."""
        call_count = 0

        def counting_mock(tool_name, kwargs):
            nonlocal call_count
            call_count += 1
            return call_count <= 3  # Stop after 3 iterations

        mock_mcp_manager.call_mcp_tool = AsyncMock(side_effect=counting_mock)

        cy = await Cy.create_async()
        cy.mcp_manager = mock_mcp_manager

        program = """
        counter = 0
        while (mcp::demo::should_continue(iteration=counter)) {
            counter = counter + 1
        }
        output = "Stopped at: ${counter}"
        return output
        """

        output = await cy.run_async(program)
        assert output == '"Stopped at: 3"'


class TestMCPErrorHandling:
    """Test error handling in MCP tool integration."""

    @pytest.mark.asyncio
    async def test_nonexistent_mcp_tool(self):
        """Test calling a non-existent MCP tool."""
        cy = await Cy.create_async()

        program = """
        $result = mcp::demo::nonexistent_tool(param="test")
        $output = "Result: $result"
        """

        # Should raise appropriate error for missing tool
        with pytest.raises(Exception):  # Specific error type depends on implementation
            await cy.run_async(program)

    @pytest.mark.asyncio
    async def test_mcp_tool_execution_error(self):
        """Test handling of MCP tool execution errors."""
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(
            side_effect=Exception("Tool execution failed")
        )
        mock_mcp_manager.initialize = AsyncMock()
        # Add tools_cache for tool resolution
        mock_mcp_manager.tools_cache = {
            "mcp::demo::failing_tool": {"name": "failing_tool", "parameters": []}
        }

        cy = await Cy.create_async()
        cy.mcp_manager = mock_mcp_manager

        program = """
        result = mcp::demo::failing_tool()
        output = "Result: ${result}"
        return output
        """

        # Should propagate tool execution error
        with pytest.raises(Exception, match="Tool execution failed"):
            await cy.run_async(program)

    @pytest.mark.asyncio
    async def test_mcp_tool_invalid_arguments(self):
        """Test MCP tool with invalid argument types."""
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(
            side_effect=Exception("Invalid arguments")
        )
        mock_mcp_manager.initialize = AsyncMock()
        # Add tools_cache for tool resolution
        mock_mcp_manager.tools_cache = {
            "mcp::demo::add": {"name": "add", "parameters": ["a", "b"]}
        }

        cy = await Cy.create_async()
        cy.mcp_manager = mock_mcp_manager

        program = """
        result = mcp::demo::add(a="not_a_number", b=5)
        output = "Result: ${result}"
        return output
        """

        with pytest.raises(Exception, match="Invalid arguments"):
            await cy.run_async(program)


class TestMCPFormatting:
    """Test MCP tool results in different output formats."""

    @pytest.fixture
    def mock_mcp_manager_with_complex_data(self):
        """Mocked MCP manager returning complex data structures."""
        manager = Mock()

        def mock_response(tool_name, kwargs):
            if tool_name == "mcp::demo::get_user_data":
                return {"name": "John Doe", "age": 30, "email": "john@example.com"}
            if tool_name == "mcp::demo::get_numbers":
                return [1, 2, 3, 4, 5]
            return "simple_result"

        manager.call_mcp_tool = AsyncMock(side_effect=mock_response)
        manager.initialize = AsyncMock()
        # Add tools_cache for tool resolution
        manager.tools_cache = {
            "mcp::demo::get_user_data": {"name": "get_user_data", "parameters": []},
            "mcp::demo::get_numbers": {"name": "get_numbers", "parameters": []},
        }
        return manager

    @pytest.mark.asyncio
    async def test_mcp_tool_result_markdown_formatting(
        self, mock_mcp_manager_with_complex_data
    ):
        """Test MCP tool result with markdown formatting."""
        cy = await Cy.create_async(interpolation_mode="markdown")
        cy.mcp_manager = mock_mcp_manager_with_complex_data

        program = """
        user = mcp::demo::get_user_data()
        output = "User: ${user|markdown}"
        return output
        """

        output = await cy.run_async(program)
        # After implementation, should format dict as markdown
        assert "**name**: John Doe" in output

    @pytest.mark.asyncio
    async def test_mcp_tool_result_csv_formatting(
        self, mock_mcp_manager_with_complex_data
    ):
        """Test MCP tool result with CSV formatting."""
        cy = await Cy.create_async()
        cy.mcp_manager = mock_mcp_manager_with_complex_data

        program = """
        numbers = mcp::demo::get_numbers()
        output = "Numbers: ${numbers|csv}"
        return output
        """

        output = await cy.run_async(program)
        # After implementation, should format list as CSV
        assert "1,2,3,4,5" in output
