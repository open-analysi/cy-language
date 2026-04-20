"""Tests for parallelization analysis with actual async tools.

Uses simple async sleep functions to verify that parallelization
detection correctly identifies async operations.
"""

import asyncio

import pytest

from cy_language.interpreter import Cy
from cy_language.ui.tools import default_registry


class TestParallelizationWithAsyncTools:
    """Test parallelization detection with real async operations."""

    @pytest.fixture
    def async_tools(self):
        """Create simple async tools for testing."""
        tools = default_registry.get_tools_dict()

        async def async_fetch(item):
            """Simple async operation that simulates fetching data."""
            await asyncio.sleep(0.001)  # Tiny sleep to make it async
            return f"fetched_{item}"

        async def async_process(value):
            """Simple async operation that simulates processing."""
            await asyncio.sleep(0.001)
            return f"processed_{value}"

        async def async_save(data):
            """Simple async operation that simulates saving."""
            await asyncio.sleep(0.001)
            return f"saved_{data}"

        def sync_compute(x, y=0):
            """Simple sync operation for comparison."""
            return x + y

        tools["async_fetch"] = async_fetch
        tools["async_process"] = async_process
        tools["async_save"] = async_save
        tools["sync_compute"] = sync_compute

        return tools

    @pytest.mark.asyncio
    async def test_detect_parallelizable_async_loop(self, async_tools):
        """Test that independent async operations are detected as parallelizable."""
        cy = await Cy.create_async(
            tools=async_tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
        items = [1, 2, 3, 4, 5]
        results = []
        for (item in items) {
            data = async_fetch(item)
            results = results + [data]
        }
        output = results
        """

        result = cy.analyze_parallelization(code)

        # Should detect 1 loop
        assert result["total_loops"] == 1

        # Should be parallelizable (async operation that doesn't depend on accumulator)
        assert len(result["parallelizable_loops"]) == 1
        assert len(result["non_parallelizable_loops"]) == 0
        assert result["would_parallelize"] is True

    @pytest.mark.asyncio
    async def test_detect_non_parallelizable_accumulator(self, async_tools):
        """Test that async ops depending on accumulators are not parallelizable."""
        cy = await Cy.create_async(tools=async_tools, enable_parallel=True)

        code = """
        items = [1, 2, 3]
        total = 0
        for (item in items) {
            total = total + item
            result = async_process(total)
        }
        output = total
        """

        result = cy.analyze_parallelization(code)

        # Should detect as non-parallelizable
        assert len(result["parallelizable_loops"]) == 0
        assert len(result["non_parallelizable_loops"]) == 1

        # Check reason mentions dependency
        reason = result["non_parallelizable_loops"][0]["reason"]
        assert "depend" in reason.lower() or "state" in reason.lower()

    @pytest.mark.asyncio
    async def test_sync_operations_not_parallelizable(self, async_tools):
        """Test that loops with only sync operations are not parallelizable."""
        cy = await Cy.create_async(tools=async_tools, enable_parallel=True)

        code = """
        numbers = [1, 2, 3, 4, 5]
        results = []
        for (n in numbers) {
            result = sync_compute(n, 10)
            results = results + [result]
        }
        output = results
        """

        result = cy.analyze_parallelization(code)

        # Should not be parallelizable (no async operations)
        assert len(result["parallelizable_loops"]) == 0
        assert len(result["non_parallelizable_loops"]) == 1

        # Check reason mentions no async
        reason = result["non_parallelizable_loops"][0]["reason"]
        assert "async" in reason.lower()

    @pytest.mark.asyncio
    async def test_chained_async_operations(self, async_tools):
        """Test that chained async operations within iterations are parallelizable."""
        cy = await Cy.create_async(tools=async_tools, enable_parallel=True)

        code = """
        items = ["a", "b", "c"]
        results = []
        for (item in items) {
            fetched = async_fetch(item)
            processed = async_process(fetched)
            saved = async_save(processed)
            results = results + [saved]
        }
        output = results
        """

        result = cy.analyze_parallelization(code)

        # Should be parallelizable (each iteration's chain is independent)
        assert len(result["parallelizable_loops"]) == 1
        assert result["would_parallelize"] is True

    @pytest.mark.asyncio
    async def test_mixed_loops_detection(self, async_tools):
        """Test detection with mix of parallelizable and non-parallelizable loops."""
        cy = await Cy.create_async(tools=async_tools, enable_parallel=True)

        code = """
        # Loop 1: Parallelizable - independent async
        items1 = [1, 2, 3]
        for (item in items1) {
            data = async_fetch(item)
        }

        # Loop 2: Not parallelizable - no async
        items2 = [4, 5, 6]
        total = 0
        for (item in items2) {
            total = total + item
        }

        # Loop 3: Not parallelizable - async depends on accumulator
        items3 = [7, 8, 9]
        total = 0
        for (item in items3) {
            total = total + item
            saved = async_save(total)
        }

        output = total
        """

        result = cy.analyze_parallelization(code)

        assert result["total_loops"] == 3
        assert len(result["parallelizable_loops"]) == 1
        assert len(result["non_parallelizable_loops"]) == 2

    @pytest.mark.asyncio
    async def test_actual_execution_speedup(self, async_tools):
        """Test that parallelizable loops actually run faster when executed."""
        # Create two interpreters - one with parallelization, one without
        cy_parallel = await Cy.create_async(
            tools=async_tools, enable_parallel=True, parallel_threshold=2
        )

        cy_sequential = await Cy.create_async(tools=async_tools, enable_parallel=False)

        code = """
        items = [1, 2, 3, 4, 5]
        results = []
        for (item in items) {
            data = async_fetch(item)
            results = results + [data]
        }
        output = results
        """

        # First verify it would be parallelized
        analysis = cy_parallel.analyze_parallelization(code)
        assert analysis["would_parallelize"] is True

        # Note: Actual execution timing test would go here
        # but requires the executor to actually implement parallelization

    @pytest.mark.asyncio
    async def test_async_reading_accumulator_not_parallelizable(self, async_tools):
        """Test that async operations reading accumulators are NOT parallelizable.

        This is a critical test case: even though we have async operations,
        if they depend on values that change during the loop (accumulators),
        they MUST run sequentially to get correct results.
        """
        cy = await Cy.create_async(
            tools=async_tools, enable_parallel=True, parallel_threshold=2
        )

        # Test 1: Async function uses running total
        code1 = """
        items = [10, 20, 30]
        running_total = 0
        results = []
        for (item in items) {
            running_total = running_total + item
            # This async operation READS the accumulator!
            processed = async_process(running_total)
            results = results + [processed]
        }
        output = results
        """

        result1 = cy.analyze_parallelization(code1)

        # Should NOT be parallelizable
        assert len(result1["parallelizable_loops"]) == 0
        assert len(result1["non_parallelizable_loops"]) == 1
        assert result1["would_parallelize"] is False

        # Check reason mentions dependency
        reason = result1["non_parallelizable_loops"][0]["reason"]
        assert "depend" in reason.lower() or "state" in reason.lower()

        # Test 2: Async function uses previous result
        code2 = """
        items = ["a", "b", "c"]
        previous = "start"
        results = []
        for (item in items) {
            # Async operation depends on previous iteration's value
            combined = async_process(previous)
            previous = item
            results = results + [combined]
        }
        output = results
        """

        result2 = cy.analyze_parallelization(code2)

        # Should NOT be parallelizable
        assert len(result2["parallelizable_loops"]) == 0
        assert len(result2["non_parallelizable_loops"]) == 1

        # Test 3: Multiple async operations where one reads accumulator
        code3 = """
        items = [1, 2, 3]
        count = 0
        for (item in items) {
            # Independent async
            data = async_fetch(item)

            # Update accumulator
            count = count + 1

            # Async that DEPENDS on accumulator - makes whole loop sequential!
            saved = async_save(count)
        }
        output = count
        """

        result3 = cy.analyze_parallelization(code3)

        # Should NOT be parallelizable because async_save reads count
        assert len(result3["parallelizable_loops"]) == 0
        assert len(result3["non_parallelizable_loops"]) == 1
        assert result3["would_parallelize"] is False

    @pytest.mark.asyncio
    async def test_report_shows_correct_status(self, async_tools):
        """Test that reports correctly show parallelization status."""
        cy_enabled = await Cy.create_async(
            tools=async_tools, enable_parallel=True, parallel_threshold=3
        )

        cy_disabled = await Cy.create_async(tools=async_tools, enable_parallel=False)

        code = """
        for (item in [1, 2, 3, 4]) {
            data = async_fetch(item)
        }
        """

        # With parallelization enabled
        result_enabled = cy_enabled.analyze_parallelization(code)
        assert "ENABLED" in result_enabled["report"]
        assert "Threshold: 3" in result_enabled["report"]

        # With parallelization disabled
        result_disabled = cy_disabled.analyze_parallelization(code)
        assert "DISABLED" in result_disabled["report"]
        assert "enable_parallel=True" in result_disabled["report"]
