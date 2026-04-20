"""
Edge case and stress tests for parallel execution.

Tests unusual scenarios, error conditions, and performance limits.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.errors import CyError
from cy_language.interpreter import Cy


class TestParallelEdgeCases:
    """Test edge cases and stress scenarios for parallel execution."""

    @pytest.fixture
    async def cy_parallel(self):
        """Create a Cy interpreter with parallel execution enabled."""
        interpreter = await Cy.create_async(enable_parallel=True, parallel_threshold=2)
        interpreter.show_enhanced_errors = False
        return interpreter

    @pytest.mark.asyncio
    async def test_empty_program(self, cy_parallel):
        """Test that empty program works without errors."""
        cy_code = """
        # Empty program with just a comment
        output = "default"
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == '"default"'

    @pytest.mark.asyncio
    async def test_single_operation(self, cy_parallel):
        """Test single async operation (no parallelization possible)."""
        tools = {"single_op": AsyncMock(return_value=42)}
        cy_parallel.tools = tools

        cy_code = """
        result = single_op()
        output = result
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert result == "42"
        # Should complete quickly (no parallel overhead for single op)
        assert duration < 0.5

    @pytest.mark.asyncio
    async def test_deeply_nested_dependencies(self, cy_parallel):
        """Test complex nested data structure dependencies."""
        tools = {
            "get_dict": AsyncMock(return_value={"key": {"nested": 10}}),
            "get_list": AsyncMock(return_value=[1, 2, 3]),
            "process": AsyncMock(side_effect=lambda x: x * 2),
        }
        cy_parallel.tools = tools

        cy_code = """
        data = get_dict()
        items = get_list()

        # Access nested structure
        nested_val = data["key"]["nested"]
        first_item = items[0]

        # These depend on the nested accesses
        result1 = process(nested_val)
        result2 = process(first_item)

        output = result1 + result2
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == "22"  # (10*2) + (1*2) = 22

    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self, cy_parallel):
        """Test handling of code that would create circular dependencies."""
        tools = {"identity": Mock(side_effect=lambda x: x)}
        cy_parallel.tools = tools

        # This code has implicit circular-like pattern but should work
        cy_code = """
        a = 1
        b = identity(a)
        a = b + 1  # Reassign a
        c = identity(a)
        output = c
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == "2"

    @pytest.mark.asyncio
    async def test_large_number_of_operations(self, cy_parallel):
        """Test parallel execution with 100+ independent operations."""

        # Create 100 mock async operations
        async def async_op(value):
            await asyncio.sleep(0.01)  # Very short delay
            return value

        def make_async_op(value):
            async def op():
                return await async_op(value)

            return op

        tools = {}
        for i in range(100):
            tools[f"op_{i}"] = AsyncMock(side_effect=make_async_op(i))

        cy_parallel.tools = tools

        # Generate code with 100 independent operations
        ops = [f"var_{i} = op_{i}()" for i in range(100)]
        sum_expr = " + ".join([f"var_{i}" for i in range(100)])
        cy_code = "\n".join(ops) + f"\noutput = {sum_expr}\nreturn output"

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        # Sum of 0 to 99 = 4950
        assert result == "4950"

        # Should complete much faster than sequential (100 * 0.01 = 1 second)
        assert duration < 0.5, f"Large parallel execution took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_exception_in_parallel_group(self, cy_parallel):
        """Test that exception in one parallel operation cancels others properly."""
        call_tracker = {"op1": False, "op2": False, "op3": False}

        async def track_and_sleep(name, delay):
            call_tracker[name] = True
            await asyncio.sleep(delay)
            return f"{name}_done"

        async def track_and_fail(name):
            call_tracker[name] = True
            await asyncio.sleep(0.1)
            raise RuntimeError(f"{name} failed")

        async def op1():
            return await track_and_sleep("op1", 0.5)

        async def op2():
            return await track_and_fail("op2")

        async def op3():
            return await track_and_sleep("op3", 0.5)

        tools = {
            "op1": AsyncMock(side_effect=op1),
            "op2": AsyncMock(side_effect=op2),
            "op3": AsyncMock(side_effect=op3),
        }
        cy_parallel.tools = tools

        cy_code = """
        a = op1()  # Will be cancelled
        b = op2()  # Will fail
        c = op3()  # Will be cancelled
        output = a + b + c
        return output
        """

        with pytest.raises(CyError) as exc_info:
            await cy_parallel.run_async(cy_code)

        assert "op2 failed" in str(exc_info.value)
        # All ops should have been started
        assert all(call_tracker.values())

    @pytest.mark.asyncio
    async def test_timeout_handling(self, cy_parallel):
        """Test operations with different timeouts."""

        async def timeout_op(delay):
            await asyncio.sleep(delay)
            return "completed"

        async def quick():
            return await timeout_op(0.1)

        async def slow():
            return await timeout_op(2.0)

        tools = {
            "quick": AsyncMock(side_effect=quick),
            "slow": AsyncMock(side_effect=slow),
        }
        cy_parallel.tools = tools

        cy_code = """
        a = quick()
        b = slow()
        output = a + b
        return output
        """

        # This should complete but take the time of the slowest operation
        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert result == '"completedcompleted"'
        assert 1.9 < duration < 2.5

    @pytest.mark.asyncio
    async def test_mixed_data_types_in_parallel(self, cy_parallel):
        """Test parallel operations with different data types."""
        tools = {
            "get_string": AsyncMock(return_value="hello"),
            "get_number": AsyncMock(return_value=42),
            "get_list": AsyncMock(return_value=[1, 2, 3]),
            "get_dict": AsyncMock(return_value={"key": "value"}),
            "get_bool": AsyncMock(return_value=True),
        }
        cy_parallel.tools = tools

        cy_code = """
        str_val = get_string()
        num_val = get_number()
        list_val = get_list()
        dict_val = get_dict()
        bool_val = get_bool()

        # Combine results
        output = {
            "string": str_val,
            "number": num_val,
            "list": list_val,
            "dict": dict_val,
            "bool": bool_val
        }
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert isinstance(result, str)  # Output is stringified
        assert "hello" in result
        assert "42" in result

    @pytest.mark.asyncio
    async def test_parallel_with_external_variables(self):
        """Test parallel execution with external variable injection."""

        async def process(x):
            await asyncio.sleep(0.1)
            return x * 2

        tools = {"process": AsyncMock(side_effect=process)}

        external_vars = {"multiplier": 3, "base_value": 10}

        cy = await Cy.create_async(
            tools=tools, variables=external_vars, enable_parallel=True
        )

        cy_code = """
        a = process(base_value)
        b = process(multiplier)
        c = process(5)

        output = a + b + c
        return output
        """

        result = await cy.run_async(cy_code)
        # a = 10*2 = 20, b = 3*2 = 6, c = 5*2 = 10
        assert result == "36"

    @pytest.mark.asyncio
    async def test_parallel_with_conditionals(self, cy_parallel):
        """Test that conditionals block parallelization appropriately."""
        tools = {
            "check": AsyncMock(return_value=True),
            "op1": AsyncMock(return_value=1),
            "op2": AsyncMock(return_value=2),
            "op3": AsyncMock(return_value=3),
        }
        cy_parallel.tools = tools

        cy_code = """
        condition = check()

        if (condition) {
            a = op1()
            b = op2()
        } else {
            a = op3()
            b = 0
        }

        output = a + b
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == "3"  # 1 + 2

    @pytest.mark.asyncio
    async def test_parallel_with_while_loop(self, cy_parallel):
        """Test that while loops block parallelization."""
        counter = {"value": 0}

        def increment():
            counter["value"] += 1
            return counter["value"]

        tools = {
            "increment": Mock(side_effect=increment),
            "async_op": AsyncMock(return_value=10),
        }
        cy_parallel.tools = tools

        cy_code = """
        i = 0
        result = 0

        while (i < 3) {
            i = increment()
            result = result + i
        }

        # This should run after the loop
        extra = async_op()
        output = result + extra
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == "16"  # (1+2+3) + 10

    @pytest.mark.asyncio
    async def test_parallel_with_try_catch(self, cy_parallel):
        """Test that try-catch blocks affect parallelization."""
        tools = {
            "may_fail": AsyncMock(side_effect=RuntimeError("Error")),
            "safe_op": AsyncMock(return_value=42),
            "recovery": AsyncMock(return_value=0),
        }
        cy_parallel.tools = tools

        cy_code = """
        try {
            risky = may_fail()
            safe = safe_op()  # Won't execute due to error
            result = risky + safe
        } catch (e) {
            result = recovery()
        }

        output = result
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == "0"

    @pytest.mark.asyncio
    async def test_very_deep_call_chain(self, cy_parallel):
        """Test deeply nested function calls."""
        tools = {
            "f1": Mock(side_effect=lambda x: x + 1),
            "f2": Mock(side_effect=lambda x: x * 2),
            "f3": Mock(side_effect=lambda x: x - 3),
            "f4": AsyncMock(side_effect=lambda x: x / 2),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Deep nesting of calls
        result = f4(f3(f2(f1(f1(f1(10))))))
        output = result
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        # 10 -> 11 -> 12 -> 13 -> 26 -> 23 -> 11.5
        assert float(result) == 11.5

    @pytest.mark.asyncio
    async def test_parallel_execution_memory_stress(self, cy_parallel):
        """Test parallel execution with operations that return large data."""

        async def large_data_op(size):
            await asyncio.sleep(0.1)
            return "x" * size  # Create string of given size

        async def get_large_1():
            return await large_data_op(1000)

        async def get_large_2():
            return await large_data_op(1000)

        async def get_large_3():
            return await large_data_op(1000)

        tools = {
            "get_large_1": AsyncMock(side_effect=get_large_1),
            "get_large_2": AsyncMock(side_effect=get_large_2),
            "get_large_3": AsyncMock(side_effect=get_large_3),
            "combine": Mock(side_effect=lambda *args: f"Combined {len(args)} items"),
        }
        cy_parallel.tools = tools

        cy_code = """
        data1 = get_large_1()
        data2 = get_large_2()
        data3 = get_large_3()

        output = combine(data1, data2, data3)
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert result == '"Combined 3 items"'
        # Should run in parallel
        assert duration < 0.3

    @pytest.mark.asyncio
    async def test_no_tools_available(self, cy_parallel):
        """Test parallel execution when no async tools are available."""
        # Only provide synchronous operations
        cy_parallel.tools = {"add": lambda x, y: x + y, "multiply": lambda x, y: x * y}

        cy_code = """
        a = add(1, 2)
        b = multiply(3, 4)
        c = add(a, b)
        output = c
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == "15"  # (1+2) + (3*4) = 3 + 12 = 15
