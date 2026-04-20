"""
Unit tests for parallel execution functionality.

Tests that async operations execute in parallel when safe to do so.
"""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.errors import CyError
from cy_language.interpreter import Cy


class TestParallelExecution:
    """Test parallel execution of Cy programs."""

    @pytest.fixture
    async def cy_parallel(self):
        """Create a Cy interpreter with parallel execution enabled."""
        interpreter = await Cy.create_async(enable_parallel=True, parallel_threshold=2)
        interpreter.show_enhanced_errors = False
        return interpreter

    @pytest.fixture
    async def cy_sequential(self):
        """Create a Cy interpreter with sequential execution (default)."""
        interpreter = await Cy.create_async(enable_parallel=False)
        interpreter.show_enhanced_errors = False
        return interpreter

    # Mock async functions for testing

    async def slow_async_func(self, value, delay=1.0):
        """Mock async function with configurable delay."""
        await asyncio.sleep(delay)
        return value

    async def async_func_that_fails(self):
        """Mock async function that raises an error."""
        await asyncio.sleep(0.1)
        raise RuntimeError("Intentional test error")

    def create_mock_tools(self) -> dict[str, Any]:
        """Create mock tools for testing."""

        async def use_value(x):
            await asyncio.sleep(1.0)
            return x * 2

        return {
            "slow_async_func": AsyncMock(side_effect=self.slow_async_func),
            "async_func_that_fails": AsyncMock(side_effect=self.async_func_that_fails),
            "use_value": AsyncMock(side_effect=use_value),
            "merge": AsyncMock(side_effect=lambda *args: sum(args)),
            "process": AsyncMock(side_effect=lambda x: x + 1),
        }

    # Correctness Tests

    @pytest.mark.asyncio
    async def test_parallel_independent_async_calls(self, cy_parallel):
        """Test that independent async calls run in parallel."""
        tools = self.create_mock_tools()
        cy_parallel.tools = tools

        cy_code = """
        a = slow_async_func(1)  # 1 second
        b = slow_async_func(2)  # 1 second
        c = slow_async_func(3)  # 1 second
        output = a + b + c
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        # Correctness: should get sum of values
        assert result == "6"

        # Performance: should run in parallel (~1 second, not 3)
        assert duration < 1.5, (
            f"Expected parallel execution (~1s), but took {duration:.2f}s"
        )

    @pytest.mark.asyncio
    async def test_parallel_with_dependencies(self, cy_parallel):
        """Test mixed parallel and sequential execution with dependencies."""
        tools = self.create_mock_tools()
        cy_parallel.tools = tools

        cy_code = """
        a = slow_async_func(1)  # 1 second
        b = slow_async_func(2)  # 1 second (parallel with a)
        c = use_value(a)        # depends on a
        d = slow_async_func(4)  # 1 second (parallel with c)
        output = b + c + d
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        # Correctness
        assert result == "8"  # b(2) + c(1*2=2) + d(4) = 8

        # Performance: should take ~2 seconds
        # First group: a and b in parallel (1s)
        # Second group: c and d in parallel (1s)
        assert 1.8 < duration < 2.5, f"Expected ~2s execution, but took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_mixed_sync_async_operations(self, cy_parallel):
        """Test that sync operations don't break parallel execution."""
        # Create mixed sync/async tools
        tools = {
            "async_op": AsyncMock(side_effect=self.slow_async_func),
            "sync_op": Mock(return_value=42),  # Synchronous
            "process": Mock(side_effect=lambda x: x * 2),  # Synchronous
        }
        cy_parallel.tools = tools

        cy_code = """
        a = async_op(1, 0.5)  # 0.5 second async
        b = sync_op()          # instant sync
        c = async_op(3, 0.5)  # 0.5 second async (parallel with a)
        d = process(b)         # instant sync
        output = a + c + d
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        # Correctness
        assert result == "88"  # a(1) + c(3) + d(42*2=84) = 88

        # Performance: async ops should run in parallel
        assert duration < 0.8, (
            f"Expected parallel async execution (~0.5s), but took {duration:.2f}s"
        )

    @pytest.mark.asyncio
    async def test_error_propagation_in_parallel(self, cy_parallel):
        """Test that errors are properly propagated in parallel execution."""
        tools = self.create_mock_tools()
        cy_parallel.tools = tools

        cy_code = """
        a = slow_async_func(1, 0.2)
        b = async_func_that_fails()  # Raises error
        c = slow_async_func(3, 0.2)
        output = a + b + c
        return output
        """

        with pytest.raises(CyError) as exc_info:
            await cy_parallel.run_async(cy_code)

        # Verify error is properly caught and reported
        assert "Intentional test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_partial_results_on_error(self, cy_parallel):
        """Test that partial results are handled correctly on error."""
        tools = self.create_mock_tools()
        cy_parallel.tools = tools

        cy_code = """
        a = slow_async_func(1, 0.1)
        b = slow_async_func(2, 0.1)
        c = async_func_that_fails()  # This will fail
        safe_result = a + b  # This should complete
        output = safe_result + c  # This won't execute
        return output
        """

        with pytest.raises(CyError):
            await cy_parallel.run_async(cy_code)

        # The tools should have been called before the error
        tools["slow_async_func"].assert_called()

    # Performance Tests

    @pytest.mark.asyncio
    async def test_performance_improvement_multiple_apis(self):
        """Test performance improvement with multiple independent API calls."""

        # Mock API calls with delays
        async def fetch_api(name, delay):
            await asyncio.sleep(delay)
            return f"{name}_data"

        async def fetch_user():
            return await fetch_api("user", 0.5)

        async def fetch_products():
            return await fetch_api("products", 0.5)

        async def fetch_inventory():
            return await fetch_api("inventory", 0.5)

        async def fetch_orders():
            return await fetch_api("orders", 0.5)

        tools = {
            "fetch_user_api": AsyncMock(side_effect=fetch_user),
            "fetch_products_api": AsyncMock(side_effect=fetch_products),
            "fetch_inventory": AsyncMock(side_effect=fetch_inventory),
            "fetch_orders": AsyncMock(side_effect=fetch_orders),
            "merge": Mock(side_effect=lambda *args: "|".join(args)),
        }

        cy_code = """
        user = fetch_user_api()        # 500ms
        products = fetch_products_api() # 500ms
        inventory = fetch_inventory()   # 500ms
        orders = fetch_orders()         # 500ms
        output = merge(user, products, inventory, orders)
        return output
        """

        # Sequential execution
        cy_seq = await Cy.create_async(enable_parallel=False)
        cy_seq.tools = tools
        start = time.time()
        result_seq = await cy_seq.run_async(cy_code)
        duration_seq = time.time() - start

        # Reset mocks
        for tool in tools.values():
            if hasattr(tool, "reset_mock"):
                tool.reset_mock()

        # Parallel execution
        cy_par = await Cy.create_async(enable_parallel=True)
        cy_par.tools = tools
        start = time.time()
        result_par = await cy_par.run_async(cy_code)
        duration_par = time.time() - start

        # Same results
        assert result_seq == result_par
        assert "user_data" in result_par
        assert "products_data" in result_par

        # Performance comparison
        assert duration_seq > 1.8, (
            f"Sequential should take ~2s, took {duration_seq:.2f}s"
        )
        assert duration_par < 0.7, (
            f"Parallel should take ~0.5s, took {duration_par:.2f}s"
        )

        # Calculate speedup
        speedup = duration_seq / duration_par
        assert speedup > 2.5, f"Expected >2.5x speedup, got {speedup:.2f}x"

    @pytest.mark.asyncio
    async def test_no_performance_regression_sequential_code(self):
        """Test that sequential code doesn't have significant overhead."""

        async def step1_func():
            await asyncio.sleep(0.1)
            return "step1_result"

        async def step2_func(x):
            await asyncio.sleep(0.1)
            return f"step2_{x}"

        async def step3_func(x):
            await asyncio.sleep(0.1)
            return f"step3_{x}"

        tools = {
            "step1": AsyncMock(side_effect=step1_func),
            "step2": AsyncMock(side_effect=step2_func),
            "step3": AsyncMock(side_effect=step3_func),
        }

        # Code with dependencies (can't be parallelized)
        cy_code = """
        a = step1()
        b = step2(a)  # Depends on a
        c = step3(b)  # Depends on b
        output = c
        return output
        """

        # Sequential execution
        cy_seq = await Cy.create_async(enable_parallel=False)
        cy_seq.tools = tools
        start = time.time()
        await cy_seq.run_async(cy_code)
        duration_seq = time.time() - start

        # Reset mocks
        for tool in tools.values():
            tool.reset_mock()

        # Parallel mode (but code can't actually parallelize)
        cy_par = await Cy.create_async(enable_parallel=True)
        cy_par.tools = tools
        start = time.time()
        await cy_par.run_async(cy_code)
        duration_par = time.time() - start

        # Overhead should be minimal (< 10%)
        overhead = (duration_par - duration_seq) / duration_seq
        assert overhead < 0.1, f"Parallel mode overhead too high: {overhead:.2%}"

    @pytest.mark.asyncio
    async def test_threshold_configuration(self):
        """Test that parallel_threshold configuration works correctly."""

        async def async_func():
            await asyncio.sleep(0.5)
            return 1

        tools = {"async_func": AsyncMock(side_effect=async_func)}

        cy_code = """
        a = async_func()
        b = async_func()
        output = a + b
        return output
        """

        # With threshold=3, shouldn't parallelize (only 2 ops)
        cy_high_threshold = await Cy.create_async(
            enable_parallel=True, parallel_threshold=3
        )
        cy_high_threshold.tools = tools

        start = time.time()
        await cy_high_threshold.run_async(cy_code)
        duration = time.time() - start

        # Should run sequentially
        assert duration > 0.9, f"Expected sequential (~1s), took {duration:.2f}s"

        # Reset mocks
        tools["async_func"].reset_mock()

        # With threshold=2, should parallelize
        cy_low_threshold = await Cy.create_async(
            enable_parallel=True, parallel_threshold=2
        )
        cy_low_threshold.tools = tools

        start = time.time()
        await cy_low_threshold.run_async(cy_code)
        duration = time.time() - start

        # Should run in parallel
        assert duration < 0.7, f"Expected parallel (~0.5s), took {duration:.2f}s"

    # Helper method tests

    def assert_parallel_execution(
        self, duration, expected_parallel_time, tolerance=0.3
    ):
        """Assert that execution happened in parallel."""
        assert duration < expected_parallel_time + tolerance, (
            f"Expected parallel execution in ~{expected_parallel_time}s, but took {duration}s"
        )

    def assert_sequential_execution(
        self, duration, expected_sequential_time, tolerance=0.3
    ):
        """Assert that execution happened sequentially."""
        assert abs(duration - expected_sequential_time) < tolerance, (
            f"Expected sequential execution in ~{expected_sequential_time}s, but took {duration}s"
        )

    @pytest.mark.asyncio
    async def test_parallel_execution_with_different_delays(self, cy_parallel):
        """Test parallel execution with operations of different durations."""

        async def fast_op():
            await asyncio.sleep(0.2)
            return 1

        async def medium_op():
            await asyncio.sleep(0.5)
            return 2

        async def slow_op():
            await asyncio.sleep(1.0)
            return 3

        tools = {
            "fast_op": AsyncMock(side_effect=fast_op),
            "medium_op": AsyncMock(side_effect=medium_op),
            "slow_op": AsyncMock(side_effect=slow_op),
        }
        cy_parallel.tools = tools

        cy_code = """
        a = fast_op()    # 0.2s
        b = medium_op()  # 0.5s
        c = slow_op()    # 1.0s
        output = a + b + c
        return output
        """

        start = time.time()
        await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        # Should complete in time of slowest operation
        self.assert_parallel_execution(duration, 1.0)

    @pytest.mark.asyncio
    async def test_correct_results_with_parallel_execution(self, cy_parallel):
        """Ensure parallel execution produces correct results."""

        # Mock tools that return specific values
        async def get_value(x):
            await asyncio.sleep(0.1)
            return x

        tools = {
            "get_value": AsyncMock(side_effect=get_value),
            "multiply": Mock(side_effect=lambda x, y: x * y),
            "add": Mock(side_effect=lambda x, y: x + y),
        }
        cy_parallel.tools = tools

        cy_code = """
        a = get_value(5)
        b = get_value(10)
        c = get_value(15)

        product = multiply(a, b)
        sum_val = add(b, c)

        output = add(product, sum_val)
        return output
        """

        result = await cy_parallel.run_async(cy_code)

        # a=5, b=10, c=15
        # product = 5*10 = 50
        # sum_val = 10+15 = 25
        # output = 50+25 = 75
        assert result == "75"
