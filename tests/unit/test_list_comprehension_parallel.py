"""
TDD tests for parallel list comprehension execution.

List comprehensions like [fetch(ip) for(ip in ips)] should be parallelized
via asyncio.gather when enable_parallel=True and the element expression
contains async operations.
"""

import asyncio
import json
import time

import pytest

from cy_language.interpreter import Cy
from cy_language.native_functions import default_registry


class TestListComprehensionParallel:
    """Integration tests for parallel list comprehension execution."""

    @pytest.mark.asyncio
    async def test_comprehension_with_async_tool_parallelizes(self):
        """A comprehension with an async tool should run concurrently."""
        concurrent_count = 0
        max_concurrent = 0

        async def async_fetch(ip):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.02)
            concurrent_count -= 1
            return f"result_{ip}"

        tools = default_registry.get_tools_dict()
        tools["async_fetch"] = async_fetch

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4"]
        results = [async_fetch(ip) for(ip in ips)]
        return results
        """

        result = json.loads(await cy.run_async(code))

        assert result == [
            "result_1.1.1.1",
            "result_2.2.2.2",
            "result_3.3.3.3",
            "result_4.4.4.4",
        ]
        assert max_concurrent > 1, (
            f"Expected concurrent execution, but max_concurrent was {max_concurrent}"
        )

    @pytest.mark.asyncio
    async def test_comprehension_with_sync_tool_stays_sequential(self):
        """A comprehension with a sync tool should not parallelize."""

        def sync_double(x):
            return x * 2

        tools = default_registry.get_tools_dict()
        tools["sync_double"] = sync_double

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
        items = [1, 2, 3, 4]
        results = [sync_double(x) for(x in items)]
        return results
        """

        result = json.loads(await cy.run_async(code))
        assert result == [2, 4, 6, 8]

    @pytest.mark.asyncio
    async def test_comprehension_parallel_disabled_stays_sequential(self):
        """With enable_parallel=False, comprehensions stay sequential."""

        async def async_fetch(ip):
            await asyncio.sleep(0.01)
            return f"result_{ip}"

        tools = default_registry.get_tools_dict()
        tools["async_fetch"] = async_fetch

        cy = await Cy.create_async(
            tools=tools, enable_parallel=False, parallel_threshold=2
        )

        code = """
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
        results = [async_fetch(ip) for(ip in ips)]
        return results
        """

        start = time.monotonic()
        result = json.loads(await cy.run_async(code))
        elapsed = time.monotonic() - start

        assert result == ["result_1.1.1.1", "result_2.2.2.2", "result_3.3.3.3"]
        # Sequential: 3 * 0.01s = ~0.03s minimum
        assert elapsed >= 0.025, "Should have run sequentially"

    @pytest.mark.asyncio
    async def test_comprehension_below_threshold_stays_sequential(self):
        """Below threshold, comprehension stays sequential."""

        async def async_fetch(ip):
            await asyncio.sleep(0.01)
            return f"result_{ip}"

        tools = default_registry.get_tools_dict()
        tools["async_fetch"] = async_fetch

        cy = await Cy.create_async(
            tools=tools,
            enable_parallel=True,
            parallel_threshold=5,  # threshold > items
        )

        code = """
        ips = ["1.1.1.1", "2.2.2.2"]
        results = [async_fetch(ip) for(ip in ips)]
        return results
        """

        result = json.loads(await cy.run_async(code))
        assert result == ["result_1.1.1.1", "result_2.2.2.2"]

    @pytest.mark.asyncio
    async def test_comprehension_with_filter_parallelizes(self):
        """Comprehension with filter should filter first, then parallelize."""
        concurrent_count = 0
        max_concurrent = 0

        async def async_fetch(ip):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.02)
            concurrent_count -= 1
            return f"result_{ip}"

        tools = default_registry.get_tools_dict()
        tools["async_fetch"] = async_fetch

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
        ips = ["1.1.1.1", "skip", "2.2.2.2", "skip", "3.3.3.3"]
        results = [async_fetch(ip) for(ip in ips) if(ip != "skip")]
        return results
        """

        result = json.loads(await cy.run_async(code))

        assert result == ["result_1.1.1.1", "result_2.2.2.2", "result_3.3.3.3"]
        assert max_concurrent > 1, (
            f"Expected concurrent execution after filtering, "
            f"but max_concurrent was {max_concurrent}"
        )

    @pytest.mark.asyncio
    async def test_filter_reduces_below_threshold_stays_sequential(self):
        """If filter reduces items below threshold, falls back to sequential."""

        async def async_fetch(ip):
            await asyncio.sleep(0.01)
            return f"result_{ip}"

        tools = default_registry.get_tools_dict()
        tools["async_fetch"] = async_fetch

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=3
        )

        code = """
        ips = ["1.1.1.1", "skip", "skip", "skip", "2.2.2.2"]
        results = [async_fetch(ip) for(ip in ips) if(ip != "skip")]
        return results
        """

        # Only 2 items pass filter, threshold is 3 -> sequential
        result = json.loads(await cy.run_async(code))
        assert result == ["result_1.1.1.1", "result_2.2.2.2"]

    @pytest.mark.asyncio
    async def test_comprehension_preserves_order(self):
        """Parallel execution must preserve iteration order."""

        async def async_fetch(ip):
            # Varying delays -- if order isn't preserved, results would be scrambled
            delay = 0.05 if ip == "1.1.1.1" else 0.01
            await asyncio.sleep(delay)
            return f"result_{ip}"

        tools = default_registry.get_tools_dict()
        tools["async_fetch"] = async_fetch

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
        results = [async_fetch(ip) for(ip in ips)]
        return results
        """

        result = json.loads(await cy.run_async(code))

        # Order must match input order, not completion order
        assert result == ["result_1.1.1.1", "result_2.2.2.2", "result_3.3.3.3"]

    @pytest.mark.asyncio
    async def test_comprehension_parallel_context_isolation(self):
        """Mutations inside one iteration must not leak to others or parent."""

        async def mutating_fetch(ip, data):
            """Tool that receives a dict -- should get independent copies."""
            data["modified"] = True
            await asyncio.sleep(0.01)
            return f"result_{ip}"

        tools = default_registry.get_tools_dict()
        tools["mutating_fetch"] = mutating_fetch

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
        ips = ["1.1.1.1", "2.2.2.2", "3.3.3.3"]
        shared = {"modified": False}
        results = [mutating_fetch(ip, shared) for(ip in ips)]
        output = shared
        return output
        """

        result = json.loads(await cy.run_async(code))

        # Parent's shared dict should not be modified by iterations
        assert result == {"modified": False}, (
            f"Parent context was mutated by parallel iteration: {result}"
        )
