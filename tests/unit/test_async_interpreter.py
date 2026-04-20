"""
Integration tests for async Cy interpreter functionality.

These tests focus on full async interpreter integration including
script execution, MCP tool calls, and end-to-end async workflows.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cy_language.interpreter import Cy


class TestAsyncInterpreterIntegration:
    """Test full async interpreter integration."""

    @pytest.mark.asyncio
    async def test_cy_run_async_method_basic(self):
        """Test basic async run method works without event loop conflicts."""
        interpreter = await Cy.create_async()

        script = 'output = "Hello from async"\nreturn output'
        result = await interpreter.run_async(script, {})

        assert "Hello from async" in result

    @pytest.mark.asyncio
    async def test_cy_run_async_with_variables(self):
        """Test async run with input variables."""
        variables = {"name": "AsyncTest"}
        interpreter = await Cy.create_async(variables=variables)

        script = 'output = "Hello ${name}"\nreturn output'
        result = await interpreter.run_async(script, {})

        assert "Hello AsyncTest" in result

    @pytest.mark.asyncio
    async def test_no_event_loop_conflicts_full_workflow(self):
        """Test that MCP operations work in existing event loop context."""
        # Mock the MCP HTTP calls
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
            # Mock both discovery and execution HTTP calls
            async_client = mock_client.return_value.__aenter__.return_value
            async_client.get = AsyncMock(return_value=discovery_response)
            async_client.post = AsyncMock(return_value=execution_response)

            # This test runs in pytest's async context
            # Previously would fail with asyncio.run() conflicts
            interpreter = await Cy.create_async(
                mcp_servers={"demo": {"base_url": "http://test", "mcp_id": "demo"}}
            )

            script = """
            result = mcp::demo::add(a=5, b=3)
            output = {"sum": result}
            return output
            """
            result = await interpreter.run_async(script, {})

            assert "42" in result
            assert "sum" in result

    @pytest.mark.asyncio
    async def test_simple_mcp_tool_call_async(self):
        """Test a simple MCP tool call works in async context (converted from existing test)."""
        # Mock MCP responses
        discovery_response = Mock()
        discovery_response.json.return_value = {
            "tools": [
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "schema": {"type": "function"},
                }
            ]
        }
        discovery_response.raise_for_status.return_value = None

        execution_response = Mock()
        execution_response.json.return_value = {"result": 42}
        execution_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            async_client = mock_client.return_value.__aenter__.return_value
            async_client.get = AsyncMock(return_value=discovery_response)
            async_client.post = AsyncMock(return_value=execution_response)

            interpreter = await Cy.create_async(
                mcp_servers={
                    "demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}
                }
            )

            script = """
            result = mcp::demo::add(a=15, b=27)
            output = {"sum": result}
            return output
            """
            result = await interpreter.run_async(script, "{}")

            assert '"sum": 42' in result  # 15 + 27 = 42 (mocked)

    @pytest.mark.asyncio
    async def test_async_interpreter_with_native_tools(self):
        """Test async interpreter with native tools mixed with MCP tools."""
        # Native tools
        tools = {"multiply": lambda a, b: a * b}

        # Mock MCP responses
        discovery_response = Mock()
        discovery_response.json.return_value = {
            "tools": [{"name": "add", "description": "Add", "schema": {}}]
        }
        discovery_response.raise_for_status.return_value = None

        execution_response = Mock()
        execution_response.json.return_value = {"result": 8}
        execution_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            async_client = mock_client.return_value.__aenter__.return_value
            async_client.get = AsyncMock(return_value=discovery_response)
            async_client.post = AsyncMock(return_value=execution_response)

            interpreter = await Cy.create_async(
                tools=tools,
                mcp_servers={"demo": {"base_url": "http://test", "mcp_id": "demo"}},
            )

            script = """
            native_result = multiply(a=3, b=4)
            mcp_result = mcp::demo::add(a=5, b=3)
            output = {"native": native_result, "mcp": mcp_result}
            return output
            """
            result = await interpreter.run_async(script, {})

            assert '"native": 12' in result
            assert '"mcp": 8' in result

    @pytest.mark.asyncio
    async def test_async_interpreter_error_handling(self):
        """Test async interpreter error handling."""
        interpreter = await Cy.create_async()

        # Test invalid Cy script
        script = "$invalid syntax here"

        with pytest.raises(Exception):  # Should raise some form of Cy error
            await interpreter.run_async(script, {})

    @pytest.mark.asyncio
    async def test_async_interpreter_with_input_data(self):
        """Test async interpreter with input data."""
        interpreter = await Cy.create_async()

        script = """
        name = input.name
        age = input.age
        output = "User ${name} is ${age} years old"
        return output
        """

        input_data = {"name": "Alice", "age": 30}
        result = await interpreter.run_async(script, input_data)

        assert "User Alice is 30 years old" in result

    def test_streamlit_async_compatibility(self):
        """Test that Streamlit UI can handle async Cy operations."""
        # This runs in sync context (like Streamlit)
        # Should use asyncio.run() safely since no existing loop

        async def async_operation():
            interpreter = await Cy.create_async()
            return await interpreter.run_async(
                'output = "test from streamlit"\nreturn output', {}
            )

        # This should work in Streamlit context (no existing loop)
        result = asyncio.run(async_operation())
        assert "test from streamlit" in result

    @pytest.mark.asyncio
    async def test_tool_registry_async_compatibility(self):
        """Test tool registry works in async context."""
        # This test verifies that tool registry integration doesn't break async flow
        from cy_language.ui.tools import default_registry

        # Get tools and add a test function
        tools = default_registry.get_tools_dict()
        tools["add"] = lambda *args: sum(args)  # Add helper for testing

        interpreter = await Cy.create_async(tools=tools)

        script = """
        result = add(5, 10, 2)
        output = {"sum": result}
        return output
        """
        result = await interpreter.run_async(script, {})

        assert '"sum": 17' in result

    @pytest.mark.asyncio
    async def test_concurrent_async_interpreters(self):
        """Test multiple async interpreters can run concurrently."""

        async def run_interpreter(name, delay):
            await asyncio.sleep(delay)  # Simulate different timing
            interpreter = await Cy.create_async()
            script = f'output = "Result from {name}"\nreturn output'
            return await interpreter.run_async(script, {})

        # Run multiple interpreters concurrently
        tasks = [
            run_interpreter("interp1", 0.1),
            run_interpreter("interp2", 0.05),
            run_interpreter("interp3", 0.02),
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert "Result from interp1" in results[0]
        assert "Result from interp2" in results[1]
        assert "Result from interp3" in results[2]

    @pytest.mark.asyncio
    async def test_async_interpreter_complex_script(self):
        """Test async interpreter with complex Cy script including control flow."""
        interpreter = await Cy.create_async()

        script = """
        count = 0
        total = 0
        while (count < 3) {
            total = total + (count * 2)
            count = count + 1
        }
        output = {"final_total": total, "iterations": count}
        return output
        """

        result = await interpreter.run_async(script, {})

        assert '"final_total": 6' in result  # (0*2) + (1*2) + (2*2) = 6
        assert '"iterations": 3' in result
