"""
Test that async operations inside conditionals are properly detected for parallelization.

This test demonstrates that for-in loops with async operations inside if/elif/else
branches should be parallelized when enable_parallel=True.
"""

import asyncio
import time

import pytest

from cy_language.interpreter import Cy
from cy_language.ui.tools import default_registry


class TestConditionalAsyncParallelization:
    """Test parallelization of async operations inside conditionals."""

    @pytest.mark.asyncio
    async def test_async_in_if_branch(self):
        """Test that async operations in if branches are parallelized."""

        # Simple async function that sleeps
        async def async_process(value):
            await asyncio.sleep(0.1)
            return {"processed": value}

        tools = default_registry.get_tools_dict()
        tools["async_process"] = async_process

        cy_code = """
items = [
    {"id": 1, "value": 10},
    {"id": 2, "value": 20},
    {"id": 3, "value": 30},
    {"id": 4, "value": 40},
    {"id": 5, "value": 50}
]

# Process items in-place - this pattern works with parallelization
for (item in items) {
    if (item["value"] > 0) {
        # This async call should be detected for parallelization
        result = async_process(item["value"])
        item["processed"] = result
    }
}

output = items
return output
"""

        # Test with parallel execution
        cy_parallel = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        # Analyze parallelization
        analysis = cy_parallel.analyze_parallelization(cy_code)

        # This should be parallelizable!
        # Currently fails because async ops in conditionals aren't detected
        assert analysis["would_parallelize"] is True, (
            "Async operations in if branches should be parallelizable"
        )

        # Time the execution
        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration_parallel = time.time() - start

        # Should complete in ~0.1s (parallel), not 0.5s (sequential)
        assert duration_parallel < 0.3, (
            f"Parallel execution took {duration_parallel:.2f}s, expected <0.3s"
        )

    @pytest.mark.asyncio
    async def test_async_in_elif_else_branches(self):
        """Test async operations in elif and else branches."""

        async def fetch_type_a(value):
            await asyncio.sleep(0.1)
            return {"type": "A", "value": value}

        async def fetch_type_b(value):
            await asyncio.sleep(0.1)
            return {"type": "B", "value": value}

        async def fetch_default(value):
            await asyncio.sleep(0.1)
            return {"type": "default", "value": value}

        tools = default_registry.get_tools_dict()
        tools.update(
            {
                "fetch_type_a": fetch_type_a,
                "fetch_type_b": fetch_type_b,
                "fetch_default": fetch_default,
            }
        )

        cy_code = """
items = [
    {"type": "A", "id": 1},
    {"type": "B", "id": 2},
    {"type": "C", "id": 3},
    {"type": "A", "id": 4}
]
results = []

for (item in items) {
    item_type = item["type"]
    item_id = item["id"]

    if (item_type == "A") {
        result = fetch_type_a(item_id)
    } elif (item_type == "B") {
        result = fetch_type_b(item_id)
    } else {
        result = fetch_default(item_id)
    }

    results = results + [result]
}

output = results
"""

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        # Should detect async operations in all branches
        analysis = cy.analyze_parallelization(cy_code)
        assert analysis["would_parallelize"] is True, (
            "Async operations in elif/else branches should be parallelizable"
        )

    @pytest.mark.asyncio
    async def test_nested_conditionals_with_async(self):
        """Test async operations in nested conditionals."""

        async def async_fetch(value):
            await asyncio.sleep(0.1)
            return value * 2

        tools = default_registry.get_tools_dict()
        tools["async_fetch"] = async_fetch

        cy_code = """
items = [1, 2, 3, 4]
results = []

for (item in items) {
    if (item > 0) {
        if (item < 10) {
            # Nested conditional with async
            value = async_fetch(item)
            results = results + [value]
        }
    }
}

output = results
"""

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        analysis = cy.analyze_parallelization(cy_code)
        assert analysis["would_parallelize"] is True, (
            "Async operations in nested conditionals should be parallelizable"
        )

    @pytest.mark.asyncio
    async def test_mixed_sync_async_in_conditionals(self):
        """Test mix of sync and async operations in conditionals."""

        def sync_process(value):
            return value + 1

        async def async_process(value):
            await asyncio.sleep(0.1)
            return value * 2

        tools = default_registry.get_tools_dict()
        tools.update({"sync_process": sync_process, "async_process": async_process})

        cy_code = """
items = [1, 2, 3, 4, 5]
results = []

for (item in items) {
    if (item % 2 == 0) {
        # Sync operation
        value = sync_process(item)
    } else {
        # Async operation
        value = async_process(item)
    }
    results = results + [value]
}

output = results
"""

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        analysis = cy.analyze_parallelization(cy_code)
        # Should still be parallelizable because there are async operations
        assert analysis["would_parallelize"] is True, (
            "Loops with any async operations should be parallelizable"
        )

    @pytest.mark.asyncio
    async def test_real_world_pattern(self):
        """Test real-world pattern similar to VirusTotal IOC analysis."""

        async def analyze_domain(domain):
            await asyncio.sleep(0.1)
            return {"threat_level": "high", "domain": domain}

        async def analyze_ip(ip):
            await asyncio.sleep(0.1)
            return {"threat_level": "medium", "ip": ip}

        tools = default_registry.get_tools_dict()
        tools.update({"analyze_domain": analyze_domain, "analyze_ip": analyze_ip})

        cy_code = """
iocs = [
    {"type": "domain", "value": "evil.com"},
    {"type": "ip", "value": "192.168.1.1"},
    {"type": "domain", "value": "bad.org"},
    {"type": "ip", "value": "10.0.0.1"}
]

for (ioc in iocs) {
    ioc_type = ioc["type"]
    ioc_value = ioc["value"]

    if (ioc_type == "domain") {
        analysis = analyze_domain(ioc_value)
    } elif (ioc_type == "ip") {
        analysis = analyze_ip(ioc_value)
    } else {
        analysis = {"threat_level": "unknown"}
    }

    ioc["analysis"] = analysis
}

output = iocs
return output
"""

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        # Should be parallelizable
        would_parallelize = cy.would_parallelize(cy_code)
        assert would_parallelize is True, (
            "Real-world IOC analysis pattern should be parallelizable"
        )

        # Execution should be fast
        start = time.time()
        await cy.run_async(cy_code)
        duration = time.time() - start

        # With 4 IOCs at 0.1s each, parallel should be ~0.1s, sequential ~0.4s
        assert duration < 0.25, (
            f"Parallel execution took {duration:.2f}s, expected <0.25s"
        )
