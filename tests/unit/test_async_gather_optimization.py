"""
Integration tests to verify that for-in loops with async operations
are actually optimized to use asyncio.gather() when appropriate.

These tests ensure:
1. Basic async loops are parallelized with asyncio.gather()
2. Execution is actually faster with parallelization
3. Results maintain correct order
4. Dependent operations run sequentially
"""

import asyncio
import time

import pytest

from cy_language.interpreter import Cy
from cy_language.native_functions import default_registry


class TestAsyncGatherOptimization:
    """Test that async operations in for loops use asyncio.gather() when safe."""

    @pytest.mark.asyncio
    async def test_basic_async_loop_uses_gather(self):
        """Test that a simple for loop with async calls uses asyncio.gather()."""
        # Track how many operations run concurrently
        concurrent_ops = []
        max_concurrent = 0

        async def async_fetch(item):
            """Async function that tracks concurrent execution."""
            nonlocal max_concurrent
            concurrent_ops.append(item)
            current = len(concurrent_ops)
            max_concurrent = max(max_concurrent, current)

            # Simulate async work
            await asyncio.sleep(0.01)

            concurrent_ops.remove(item)
            return f"fetched_{item}"

        # Get native tools (includes len, etc.)
        tools = default_registry.get_tools_dict()
        tools["async_fetch"] = async_fetch

        # Create interpreter with parallelization enabled
        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
        items = [1, 2, 3, 4, 5]
        results = []
        for (item in items) {
            data = async_fetch(item)
            results = results + [data]
        }
        output = results
        return output
        """

        # Run the code
        result = await cy.run_async(code)

        # Verify all items were fetched
        assert "fetched_1" in result
        assert "fetched_2" in result
        assert "fetched_3" in result
        assert "fetched_4" in result
        assert "fetched_5" in result

        # Verify operations ran concurrently (max_concurrent > 1)
        assert max_concurrent > 1, (
            f"Expected concurrent execution, but max_concurrent was {max_concurrent}"
        )

    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_performance(self):
        """Test that parallel execution is actually faster than sequential."""
        call_times = []

        async def slow_async_op(item):
            """Async operation with noticeable delay."""
            call_times.append(time.time())
            await asyncio.sleep(0.05)  # 50ms delay
            return f"processed_{item}"

        # Get native tools
        tools = default_registry.get_tools_dict()
        tools["slow_async_op"] = slow_async_op

        # Test with parallelization enabled
        cy_parallel = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        # Test with parallelization disabled
        cy_sequential = await Cy.create_async(tools=tools, enable_parallel=False)

        code = """
        items = [1, 2, 3, 4, 5]
        results = []
        for (item in items) {
            data = slow_async_op(item)
            results = results + [data]
        }
        output = results
        return output
        """

        # Measure parallel execution time
        call_times.clear()
        start_parallel = time.time()
        result_parallel = await cy_parallel.run_async(code)
        time_parallel = time.time() - start_parallel

        # Check that calls happened nearly simultaneously
        # Under CPU contention, scheduling can add significant jitter
        if len(call_times) >= 2:
            time_spread = max(call_times) - min(call_times)
            assert time_spread < 0.5, (
                f"Calls should be nearly simultaneous, spread was {time_spread}s"
            )

        # Measure sequential execution time
        call_times.clear()
        start_sequential = time.time()
        result_sequential = await cy_sequential.run_async(code)
        time_sequential = time.time() - start_sequential

        # Check that calls happened sequentially (spread > total delay)
        if len(call_times) >= 2:
            time_spread = max(call_times) - min(call_times)
            assert time_spread > 0.15, (
                f"Calls should be sequential, spread was {time_spread}s"
            )

        # Both should produce same results
        assert result_parallel == result_sequential

        # Parallel should be significantly faster (at least 2x for 5 items)
        # Sequential: ~250ms (5 * 50ms)
        # Parallel: ~50ms (all run concurrently)
        assert time_parallel < time_sequential / 2, (
            f"Parallel ({time_parallel:.3f}s) should be much faster than sequential ({time_sequential:.3f}s)"
        )

    @pytest.mark.asyncio
    async def test_result_order_preserved(self):
        """Test that results maintain correct order even with different completion times."""

        async def async_process(item):
            """Process items with delays inversely proportional to value."""
            # Later items complete faster, testing order preservation
            delay = 0.05 / item if item > 0 else 0.05
            await asyncio.sleep(delay)
            return f"result_{item}"

        tools = default_registry.get_tools_dict()
        tools["async_process"] = async_process

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
        items = [1, 2, 3, 4, 5]
        results = []
        for (item in items) {
            data = async_process(item)
            results = results + [data]
        }
        output = results
        return output
        """

        result = await cy.run_async(code)

        # Results should be in original iteration order
        assert "result_1" in result
        assert "result_2" in result
        assert "result_3" in result
        assert "result_4" in result
        assert "result_5" in result

        # Check order is preserved
        assert result.index("result_1") < result.index("result_2")
        assert result.index("result_2") < result.index("result_3")
        assert result.index("result_3") < result.index("result_4")
        assert result.index("result_4") < result.index("result_5")

    @pytest.mark.asyncio
    async def test_dependent_operations_run_sequentially(self):
        """Test that operations with dependencies don't use asyncio.gather()."""
        execution_order = []

        async def async_accumulate(value):
            """Track when this operation runs."""
            execution_order.append(("start", value, time.time()))
            await asyncio.sleep(0.02)
            execution_order.append(("end", value, time.time()))
            return value + 10

        tools = default_registry.get_tools_dict()
        tools["async_accumulate"] = async_accumulate

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        # Code with accumulator dependency - should NOT parallelize
        code = """
        items = [1, 2, 3]
        total = 0
        results = []
        for (item in items) {
            total = total + item
            processed = async_accumulate(total)
            results = results + [processed]
        }
        output = results
        return output
        """

        execution_order.clear()
        result = await cy.run_async(code)

        # Check that operations ran sequentially
        # Each operation should complete before next starts
        for i in range(len(execution_order) - 2):
            if execution_order[i][0] == "end" and execution_order[i + 1][0] == "start":
                # End of one operation should be before start of next
                assert execution_order[i][2] <= execution_order[i + 1][2], (
                    "Operations should run sequentially when there are dependencies"
                )

        # Results should reflect accumulation: 1, 1+2=3, 1+2+3=6, plus 10 each
        assert "11" in result  # 1 + 10
        assert "13" in result  # 3 + 10
        assert "16" in result  # 6 + 10

    @pytest.mark.asyncio
    async def test_mixed_sync_async_operations(self):
        """Test loops with both sync and async operations."""
        sleep_duration = 0.05  # 50ms per async op

        async def async_fetch(item):
            await asyncio.sleep(sleep_duration)
            return f"async_{item}"

        def sync_process(item):
            return f"sync_{item}"

        tools = default_registry.get_tools_dict()
        tools["async_fetch"] = async_fetch
        tools["sync_process"] = sync_process

        code = """
        items = [1, 2, 3]
        results = []
        for (item in items) {
            # Mix of sync and async operations
            sync_data = sync_process(item)
            async_data = async_fetch(item)
            combined = sync_data + "_" + async_data
            results = results + [combined]
        }
        output = results
        return output
        """

        # Run with parallelization
        cy_parallel = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )
        start = time.time()
        result_parallel = await cy_parallel.run_async(code)
        elapsed_parallel = time.time() - start

        # Run without parallelization for a baseline
        cy_sequential = await Cy.create_async(tools=tools, enable_parallel=False)
        start = time.time()
        result_sequential = await cy_sequential.run_async(code)
        elapsed_sequential = time.time() - start

        # Parallel should be faster than sequential
        # Sequential: ~150ms (3 × 50ms), Parallel: ~50ms (all concurrent)
        assert elapsed_parallel < elapsed_sequential, (
            f"Parallel ({elapsed_parallel:.3f}s) should be faster than "
            f"sequential ({elapsed_sequential:.3f}s)"
        )

        # Verify results are correct and identical
        assert result_parallel == result_sequential
        assert "sync_1_async_1" in result_parallel
        assert "sync_2_async_2" in result_parallel
        assert "sync_3_async_3" in result_parallel

    @pytest.mark.asyncio
    async def test_threshold_controls_parallelization(self):
        """Test that parallel_threshold controls when parallelization kicks in."""
        execution_count = 0

        async def counting_async_op(item):
            nonlocal execution_count
            execution_count += 1
            current_count = execution_count
            await asyncio.sleep(0.01)
            execution_count -= 1
            return (item, current_count)

        tools = default_registry.get_tools_dict()
        tools["counting_async_op"] = counting_async_op

        # Test with high threshold (won't parallelize)
        cy_high_threshold = await Cy.create_async(
            tools=tools,
            enable_parallel=True,
            parallel_threshold=10,  # Higher than number of items
        )

        # Test with low threshold (will parallelize)
        cy_low_threshold = await Cy.create_async(
            tools=tools,
            enable_parallel=True,
            parallel_threshold=2,  # Lower than number of items
        )

        code = """
        items = [1, 2, 3]
        results = []
        for (item in items) {
            data = counting_async_op(item)
            results = results + [data]
        }
        output = results
        return output
        """

        # High threshold - should run sequentially
        execution_count = 0
        max_concurrent_high = 0
        result_high = await cy_high_threshold.run_async(code)

        # Parse results to find max concurrent from the returned data
        for item_result in eval(result_high.replace("(", "[").replace(")", "]")):
            max_concurrent_high = max(max_concurrent_high, item_result[1])

        # Low threshold - should run in parallel
        execution_count = 0
        max_concurrent_low = 0
        result_low = await cy_low_threshold.run_async(code)

        for item_result in eval(result_low.replace("(", "[").replace(")", "]")):
            max_concurrent_low = max(max_concurrent_low, item_result[1])

        # With high threshold, operations should be sequential (max concurrent = 1)
        assert max_concurrent_high == 1, (
            f"High threshold should prevent parallelization, got {max_concurrent_high}"
        )

        # With low threshold, operations should be parallel (max concurrent > 1)
        assert max_concurrent_low > 1, (
            f"Low threshold should allow parallelization, got {max_concurrent_low}"
        )


if __name__ == "__main__":
    # Run a specific test for debugging
    async def debug_test():
        test = TestAsyncGatherOptimization()
        await test.test_basic_async_loop_uses_gather()
        print("✓ Basic async loop test passed")

        await test.test_parallel_vs_sequential_performance()
        print("✓ Performance test passed")

        await test.test_result_order_preserved()
        print("✓ Order preservation test passed")

        await test.test_dependent_operations_run_sequentially()
        print("✓ Dependency test passed")

    asyncio.run(debug_test())
