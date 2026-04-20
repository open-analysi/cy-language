"""Tests to improve coverage for parallelization features."""

import asyncio

import pytest

from cy_language.interpreter import Cy
from cy_language.ui.tools import default_registry


class TestParallelizationCoverageGaps:
    """Tests targeting specific coverage gaps in parallelization."""

    @pytest.mark.asyncio
    async def test_debug_mode_coverage(self):
        """Test with debug=True to cover debug print paths."""

        async def mock_task(value):
            await asyncio.sleep(0.01)
            return value * 2

        tools = default_registry.get_tools_dict()
        tools["async_task"] = mock_task

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )
        cy.debug = True  # Enable debug to cover debug paths

        code = """
items = [{"id": 1}, {"id": 2}, {"id": 3}]

for (item in items) {
    if (item["id"] > 0) {
        item["result"] = async_task(item["id"])
    }
}

output = items
return output
"""

        # Run with debug enabled - this covers lines 684-686, 721-723, 740-746
        result = await cy.run_async(code)

        # Verify it still works correctly
        import ast

        result_list = ast.literal_eval(result)
        assert len(result_list) == 3
        assert all("result" in item for item in result_list)
        assert result_list[0]["result"] == 2  # 1 * 2
        assert result_list[1]["result"] == 4  # 2 * 2
        assert result_list[2]["result"] == 6  # 3 * 2

    @pytest.mark.asyncio
    async def test_below_threshold_parallelization(self):
        """Test loops with items below the parallel threshold."""

        async def mock_fetch(id):
            await asyncio.sleep(0.01)
            return {"id": id, "data": "result"}

        tools = default_registry.get_tools_dict()
        tools["fetch_data"] = mock_fetch

        cy = await Cy.create_async(
            tools=tools,
            enable_parallel=True,
            parallel_threshold=5,  # High threshold
        )

        code = """
# Only 2 items - below threshold of 5
items = [{"id": 1}, {"id": 2}]

for (item in items) {
    item["result"] = fetch_data(item["id"])
}

output = items
return output
"""

        # Should run sequentially since below threshold
        # This covers the threshold check paths
        result = await cy.run_async(code)

        import ast

        result_list = ast.literal_eval(result)
        assert len(result_list) == 2
        assert all("result" in item for item in result_list)

    @pytest.mark.asyncio
    async def test_edge_case_empty_loop(self):
        """Test parallelization with empty collection."""

        cy = await Cy.create_async(enable_parallel=True, parallel_threshold=2)

        code = """
items = []
results = []

# Empty loop - nothing to parallelize
for (item in items) {
    results = results + [item]
}

output = results
"""

        # Check that empty loops are handled in analysis
        analysis = cy.analyze_parallelization(code)
        # Analysis should complete even with empty collections
        assert "would_parallelize" in analysis

    @pytest.mark.asyncio
    async def test_single_item_loop(self):
        """Test parallelization with single item (edge case)."""

        async def async_op(val):
            await asyncio.sleep(0.01)
            return val.upper()

        tools = default_registry.get_tools_dict()
        tools["async_op"] = async_op

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        code = """
items = ["hello"]  # Single item

for (item in items) {
    item = async_op(item)
}

output = items
return output
"""

        # With one item, should not parallelize
        result = await cy.run_async(code)
        # Note: Direct mutation of loop var doesn't persist,
        # so original value is returned
        assert "['hello']" in result or '["hello"]' in result

    @pytest.mark.asyncio
    async def test_pattern_matching_async_indicators(self):
        """Test async pattern matching for various tool names."""

        # Create tools with various async indicator patterns
        async def fetch_user(id):
            await asyncio.sleep(0.01)
            return {"id": id}

        async def post_data(data):
            await asyncio.sleep(0.01)
            return {"posted": data}

        async def download_file(name):
            await asyncio.sleep(0.01)
            return {"file": name}

        async def upload_resource(data):
            await asyncio.sleep(0.01)
            return {"uploaded": data}

        async def request_api(endpoint):
            await asyncio.sleep(0.01)
            return {"endpoint": endpoint}

        tools = default_registry.get_tools_dict()
        tools.update(
            {
                "fetch_user": fetch_user,
                "post_data": post_data,
                "download_file": download_file,
                "upload_resource": upload_resource,
                "request_api": request_api,
            }
        )

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        # Test each pattern
        patterns = [
            ("fetch_user", "fetch"),
            ("post_data", "post_"),
            ("download_file", "download"),
            ("upload_resource", "upload"),
            ("request_api", "request"),
        ]

        for tool_name, pattern in patterns:
            code = f"""
items = [1, 2, 3]

for (item in items) {{
    result = {tool_name}(item)
}}

output = "done"
"""

            # Check that it's detected as parallelizable
            analysis = cy.analyze_parallelization(code)
            assert analysis["would_parallelize"], (
                f"Tool '{tool_name}' with pattern '{pattern}' should be parallelizable"
            )

    @pytest.mark.asyncio
    async def test_complex_accumulator_patterns(self):
        """Test various accumulator patterns for edge cases."""

        async def process(val):
            await asyncio.sleep(0.01)
            return val * 2

        tools = default_registry.get_tools_dict()
        tools["process"] = process

        cy = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )

        # Test that list concatenation with async is parallelizable
        code = """
items = [1, 2, 3, 4, 5]
results = []

for (item in items) {
    if (item % 2 == 0) {
        # Only process and accumulate even numbers
        processed = process(item)
        results = results + [processed]
    }
}

output = results
"""

        # This SHOULD be parallelizable - list concatenation is safe
        analysis = cy.analyze_parallelization(code)
        assert analysis["would_parallelize"], (
            "Loop with list concatenation and async should be parallelizable"
        )
