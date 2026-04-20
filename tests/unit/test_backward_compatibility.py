"""
Backward compatibility tests for parallel execution feature.

Ensures that existing code continues to work with the new parallel execution feature.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.interpreter import Cy


class TestBackwardCompatibility:
    """Test that parallel execution doesn't break existing functionality."""

    @pytest.mark.asyncio
    async def test_default_sequential_execution(self):
        """Test that default Cy() constructor uses sequential execution."""
        # Default constructor should not enable parallel execution
        cy = await Cy.create_async()  # No parallel parameters

        assert cy.enable_parallel is False
        assert cy.parallel_threshold == 2  # Default value

        # Create mock tools to test execution timing
        import time

        async def delay_op(value, delay=0.5):
            await asyncio.sleep(delay)
            return value

        async def op1():
            return await delay_op(1)

        async def op2():
            return await delay_op(2)

        async def op3():
            return await delay_op(3)

        cy.tools = {
            "op1": AsyncMock(side_effect=op1),
            "op2": AsyncMock(side_effect=op2),
            "op3": AsyncMock(side_effect=op3),
        }

        cy_code = """        a = op1()
        b = op2()
        c = op3()
        output = a + b + c
        return output
        """

        start = time.time()
        result = await cy.run_async(cy_code)
        duration = time.time() - start

        # Should execute sequentially (3 * 0.5 = 1.5 seconds)
        assert duration > 1.4  # Allow small timing variance
        assert result == "6"

    @pytest.mark.asyncio
    async def test_existing_tests_still_pass(self):
        """Test that existing code patterns work with parallel mode enabled."""
        # Test various existing patterns with parallel mode
        cy = await Cy.create_async(enable_parallel=True)

        # Pattern 1: Simple variable assignment
        cy.tools = {"add": lambda x, y: x + y}
        result = await cy.run_async("""        a = 5
        b = 10
        c = add(a, b)
        output = c
        return output
        """)
        assert result == "15"

        # Pattern 2: String interpolation
        result = await cy.run_async("""        name = "Alice"
        greeting = "Hello, ${name}!"
        output = greeting
        return output
        """)
        assert result == '"Hello, Alice!"'

        # Pattern 3: List operations
        cy.tools = {"process": lambda x: [i * 2 for i in x]}
        result = await cy.run_async("""        items = [1, 2, 3]
        processed = process(items)
        output = processed
        return output
        """)
        assert "[2, 4, 6]" in result

        # Pattern 4: Dictionary operations
        result = await cy.run_async("""        data = {"key": "value", "number": 42}
        value = data["key"]
        output = value
        return output
        """)
        assert result == '"value"'

        # Pattern 5: Arithmetic operations
        result = await cy.run_async("""        x = 10
        y = 5
        sum_result = x + y
        output = sum_result
        return output
        """)
        assert result == "15"

        # Pattern 6: Nested function calls
        cy.tools = {"double": lambda x: x * 2, "add_ten": lambda x: x + 10}
        result = await cy.run_async("""        value = 5
        doubled = double(value)
        final = add_ten(doubled)
        output = final
        return output
        """)
        assert result == "20"

        # Pattern 7: Complex expressions
        result = await cy.run_async("""        a = 2
        b = 3
        c = 4
        complex_result = (a + b) * c
        output = complex_result
        return output
        """)
        assert result == "20"

    @pytest.mark.asyncio
    async def test_deterministic_results(self):
        """Test that same program produces same results in sequential and parallel modes."""
        # Create a complex program with potential parallelization
        tools = {
            "process_a": Mock(return_value=10),
            "process_b": Mock(return_value=20),
            "process_c": Mock(return_value=30),
            "combine": Mock(side_effect=lambda x, y, z: x + y + z),
            "transform": Mock(side_effect=lambda x: x * 2),
        }

        cy_code = """        # Some operations that could be parallelized
        a = process_a()
        b = process_b()
        c = process_c()

        # Dependent operations
        intermediate = combine(a, b, c)
        final = transform(intermediate)

        output = final
        return output
        """

        # Run with sequential execution
        cy_seq = await Cy.create_async(enable_parallel=False)
        cy_seq.tools = tools
        result_seq = await cy_seq.run_async(cy_code)

        # Reset mocks
        for tool in tools.values():
            tool.reset_mock()

        # Run with parallel execution
        cy_par = await Cy.create_async(enable_parallel=True)
        cy_par.tools = tools
        result_par = await cy_par.run_async(cy_code)

        # Results must be identical
        assert result_seq == result_par
        assert result_seq == "120"  # (10+20+30) * 2

    @pytest.mark.asyncio
    async def test_external_variables_compatibility(self):
        """Test that external variable injection works with parallel mode."""
        external_vars = {"config_value": 42, "multiplier": 3}

        tools = {"process": Mock(side_effect=lambda x, m: x * m)}

        # Test with sequential
        cy_seq = await Cy.create_async(
            variables=external_vars, tools=tools, enable_parallel=False
        )

        result_seq = await cy_seq.run_async("""        result = process(config_value, multiplier)
        output = result
        return output
        """)

        # Test with parallel
        cy_par = await Cy.create_async(
            variables=external_vars, tools=tools, enable_parallel=True
        )

        result_par = await cy_par.run_async("""        result = process(config_value, multiplier)
        output = result
        return output
        """)

        assert result_seq == result_par
        assert result_seq == "126"  # 42 * 3

    @pytest.mark.asyncio
    async def test_mcp_compatibility(self):
        """Test that MCP integration works with parallel execution."""
        # Mock MCP manager
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(return_value="mcp_result")
        # Add tools_cache for tool resolution
        mock_mcp_manager.tools_cache = {
            "mcp::test::tool": {"name": "tool", "description": "Test tool"}
        }

        # Test without parallel
        cy_seq = await Cy.create_async(enable_parallel=False)
        cy_seq.mcp_manager = mock_mcp_manager

        result_seq = await cy_seq.run_async("""        data = mcp::test::tool()
        output = data
        return output
        """)

        # Reset mock
        mock_mcp_manager.call_mcp_tool.reset_mock()

        # Test with parallel
        cy_par = await Cy.create_async(enable_parallel=True)
        cy_par.mcp_manager = mock_mcp_manager

        result_par = await cy_par.run_async("""        data = mcp::test::tool()
        output = data
        return output
        """)

        assert result_seq == result_par
        assert "mcp_result" in result_seq

    @pytest.mark.asyncio
    async def test_interpolation_modes_compatibility(self):
        """Test that all interpolation modes work with parallel execution."""
        data = [1, 2, 3]

        for mode in ["markdown", "csv", "xml"]:
            # Sequential
            cy_seq = await Cy.create_async(
                interpolation_mode=mode, enable_parallel=False
            )
            cy_seq.tools = {"get_list": Mock(return_value=data)}

            result_seq = await cy_seq.run_async("""            items = get_list()
            output = "Items: ${items}"
            return output
            """)

            # Parallel
            cy_par = await Cy.create_async(
                interpolation_mode=mode, enable_parallel=True
            )
            cy_par.tools = {"get_list": Mock(return_value=data)}

            result_par = await cy_par.run_async("""            items = get_list()
            output = "Items: ${items}"
            return output
            """)

            assert result_seq == result_par

            # Verify mode-specific formatting
            if mode == "markdown":
                assert "- 1" in result_seq or "• 1" in result_seq
            elif mode == "csv":
                assert "1,2,3" in result_seq or "1, 2, 3" in result_seq
            elif mode == "xml":
                assert "<item>" in result_seq

    @pytest.mark.asyncio
    async def test_error_handling_compatibility(self):
        """Test that error handling remains consistent."""
        tools = {"fail": Mock(side_effect=RuntimeError("Test error"))}

        # Sequential error handling
        cy_seq = await Cy.create_async(enable_parallel=False)
        cy_seq.tools = tools

        with pytest.raises(Exception) as exc_seq:
            await cy_seq.run_async("""            result = fail()
            output = result
            return output
            """)

        # Parallel error handling
        cy_par = await Cy.create_async(enable_parallel=True)
        cy_par.tools = tools

        with pytest.raises(Exception) as exc_par:
            await cy_par.run_async("""            result = fail()
            output = result
            return output
            """)

        # Both should raise similar errors
        assert "Test error" in str(exc_seq.value)
        assert "Test error" in str(exc_par.value)

    def test_sync_run_method_compatibility(self):
        """Test that synchronous run() method still works."""
        interpreter = Cy()  # Sync constructor
        interpreter.show_enhanced_errors = False
        cy = interpreter
        cy.tools = {"add": lambda x, y: x + y}

        # This should work without async
        result = cy.run("""        a = 10
        b = 20
        total = add(a, b)
        output = total
        return output
        """)

        assert result == "30"

    @pytest.mark.asyncio
    async def test_input_data_compatibility(self):
        """Test that input data injection works with parallel mode."""
        tools = {"process": Mock(side_effect=lambda x: x * 2)}

        input_data = {"value": 15}

        # Sequential with input
        cy_seq = await Cy.create_async(enable_parallel=False)
        cy_seq.tools = tools

        result_seq = await cy_seq.run_async(
            """        data = input["value"]
        result = process(data)
        output = result
        return output
        """,
            input_data=input_data,
        )

        # Parallel with input
        cy_par = await Cy.create_async(enable_parallel=True)
        cy_par.tools = tools

        result_par = await cy_par.run_async(
            """        data = input["value"]
        result = process(data)
        output = result
        return output
        """,
            input_data=input_data,
        )

        assert result_seq == result_par
        assert result_seq == "30"  # 15 * 2

    @pytest.mark.asyncio
    async def test_no_side_effects_from_parallel_config(self):
        """Test that parallel configuration doesn't affect unrelated features."""
        # Test that parser, compiler, etc. work the same
        cy_seq = await Cy.create_async(enable_parallel=False)
        cy_par = await Cy.create_async(enable_parallel=True)

        # Both should have same interpolation configuration
        assert cy_seq.interpolation_mode == cy_par.interpolation_mode
        assert cy_seq.item_tag == cy_par.item_tag

        # Test parsing works the same
        test_program = """
        a = 1
        b = 2
        output = a + b
        return output
        """

        ast_seq = cy_seq.parser.parse_only(test_program)
        ast_par = cy_par.parser.parse_only(test_program)

        # ASTs should be identical
        assert str(ast_seq) == str(ast_par)
