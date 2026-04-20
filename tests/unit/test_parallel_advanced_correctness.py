"""
Advanced correctness tests for parallel execution.

These tests focus on subtle edge cases that could break parallel execution
correctness, including complex data sharing, aliasing, and interpolation scenarios.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.interpreter import Cy


class TestParallelAdvancedCorrectness:
    """Test advanced correctness scenarios for parallel execution."""

    @pytest.fixture
    async def cy_parallel(self):
        """Create a Cy interpreter with parallel execution enabled."""
        interpreter = await Cy.create_async(enable_parallel=True, parallel_threshold=2)
        interpreter.show_enhanced_errors = False
        return interpreter

    @pytest.mark.asyncio
    async def test_shared_object_field_mutations(self, cy_parallel):
        """Test that field mutations on the same object are handled correctly."""
        # This tests field-level dependency tracking

        async def set_field(value):
            await asyncio.sleep(0.1)
            return value

        tools = {"set_field": AsyncMock(side_effect=set_field)}
        cy_parallel.tools = tools

        cy_code = """
        shared_obj = {}

        # These operations modify different fields of the same object
        # Our dependency analyzer should detect these as potential conflicts
        shared_obj["field1"] = set_field("value1")
        shared_obj["field2"] = set_field("value2")

        # Reading the fields
        output = shared_obj["field1"] + "," + shared_obj["field2"]
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        # Should get both values correctly
        assert result == '"value1,value2"'

        # Our analyzer should handle field-level dependencies correctly
        # Different fields should be able to parallelize, but we're conservative

    @pytest.mark.asyncio
    async def test_mixed_serial_and_parallel_dependencies(self, cy_parallel):
        """Test complex mix of operations that must be serial vs parallel."""

        async def independent_fetch(resource_id):
            """Independent API fetch - can be parallelized."""
            await asyncio.sleep(0.1)
            return f"data_{resource_id}"

        async def process_data(data):
            """Processing that depends on fetched data - must be serial after fetch."""
            await asyncio.sleep(0.1)
            return f"processed_{data}"

        async def aggregate_results(result1, result2):
            """Aggregation depends on processed results - must be serial after processing."""
            await asyncio.sleep(0.1)
            return f"aggregated_{result1}_{result2}"

        tools = {
            "independent_fetch": AsyncMock(side_effect=independent_fetch),
            "process_data": AsyncMock(side_effect=process_data),
            "aggregate_results": AsyncMock(side_effect=aggregate_results),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Independent fetches - SHOULD PARALLELIZE
        raw_data1 = independent_fetch("user")
        raw_data2 = independent_fetch("profile")
        raw_data3 = independent_fetch("settings")

        # Processing depends on fetches - SHOULD PARALLELIZE within phase
        processed1 = process_data(raw_data1)  # Depends on raw_data1
        processed2 = process_data(raw_data2)  # Depends on raw_data2
        processed3 = process_data(raw_data3)  # Depends on raw_data3

        # Aggregation depends on processing - MUST BE SERIAL
        final_result = aggregate_results(processed1, processed2)

        # Independent final step - CAN PARALLELIZE with aggregation
        summary = process_data(processed3)

        output = final_result + "|" + summary
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        # Verify correctness
        assert "aggregated_processed_data_user_processed_data_profile" in result
        assert "processed_processed_data_settings" in result

        # Expected execution:
        # 3 parallel fetches (~0.1s)
        # 3 parallel processes (~0.1s)
        # aggregate + summary in parallel (~0.1s)
        # Total: ~0.3s instead of sequential 0.7s
        print(f"Mixed serial/parallel execution took: {duration:.3f}s")
        # Allow 0.5s timeout to account for system load and timing variations
        assert duration < 0.5, (
            f"Expected ~0.3s with optimal parallelization, took {duration:.3f}s"
        )

    @pytest.mark.asyncio
    async def test_complex_nested_object_parallelization(self, cy_parallel):
        """Test parallelization with complex nested object structures."""

        async def update_user_profile(user_id, field, value):
            await asyncio.sleep(0.1)
            return {"user_id": user_id, field: value}

        async def update_user_settings(user_id, setting, value):
            await asyncio.sleep(0.1)
            return {"user_id": user_id, "settings": {setting: value}}

        tools = {
            "update_user_profile": AsyncMock(side_effect=update_user_profile),
            "update_user_settings": AsyncMock(side_effect=update_user_settings),
            "merge_user_data": Mock(
                side_effect=lambda profile, settings: {
                    "user_id": profile["user_id"],
                    "profile": profile,
                    "settings": settings["settings"],
                }
            ),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Different users - should parallelize
        user1_profile = update_user_profile("user1", "name", "Alice")
        user2_profile = update_user_profile("user2", "name", "Bob")

        # Different settings for different users - should parallelize
        user1_settings = update_user_settings("user1", "theme", "dark")
        user2_settings = update_user_settings("user2", "theme", "light")

        # Merging depends on previous operations
        user1_data = merge_user_data(user1_profile, user1_settings)
        user2_data = merge_user_data(user2_profile, user2_settings)

        output = user1_data["profile"]["name"] + "," + user2_data["profile"]["name"]
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert result == '"Alice,Bob"'

        # Should achieve good parallelization (~0.2s for two groups of parallel ops)
        assert duration < 0.35, f"Expected good parallelization, took {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_function_parameter_aliasing(self, cy_parallel):
        """Test that function parameter aliasing doesn't break dependency analysis."""

        async def process_value(x):
            await asyncio.sleep(0.1)
            return x * 2

        async def modify_and_process(value, multiplier):
            await asyncio.sleep(0.1)
            return value * multiplier

        tools = {
            "process_value": AsyncMock(side_effect=process_value),
            "modify_and_process": AsyncMock(side_effect=modify_and_process),
            "combine": Mock(side_effect=lambda a, b: a + b),
        }
        cy_parallel.tools = tools

        cy_code = """
        base_value = 5

        # These use the same variable but don't interfere
        result1 = process_value(base_value)      # base_value * 2 = 10
        result2 = modify_and_process(base_value, 3)  # base_value * 3 = 15

        # This depends on both results
        final = combine(result1, result2)  # 10 + 15 = 25

        output = final
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert result == "25"

        # Should parallelize the first two operations
        assert duration < 0.25, f"Expected parallelization, took {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_interpolation_with_parallel_variables(self, cy_parallel):
        """Test string interpolation with variables computed in parallel."""

        async def get_user_name(user_id):
            await asyncio.sleep(0.1)
            return f"User_{user_id}"

        async def get_user_email(user_id):
            await asyncio.sleep(0.1)
            return f"user{user_id}@example.com"

        async def get_timestamp():
            await asyncio.sleep(0.1)
            return "2023-12-01T10:00:00Z"

        tools = {
            "get_user_name": AsyncMock(side_effect=get_user_name),
            "get_user_email": AsyncMock(side_effect=get_user_email),
            "get_timestamp": AsyncMock(side_effect=get_timestamp),
        }
        cy_parallel.tools = tools

        cy_code = """
        # These should run in parallel
        name = get_user_name(123)
        email = get_user_email(123)
        timestamp = get_timestamp()

        # Interpolation uses all parallel results
        output = "User: ${name}, Email: ${email}, Time: ${timestamp}"
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert "User: User_123" in result
        assert "Email: user123@example.com" in result
        assert "Time: 2023-12-01T10:00:00Z" in result

        # Should run all operations in parallel
        assert duration < 0.2, f"Expected parallel execution, took {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_recursive_data_structure_dependencies(self, cy_parallel):
        """Test dependencies with recursive/hierarchical data structures."""

        async def create_node(value, parent_id=None):
            await asyncio.sleep(0.1)
            node = {"id": value, "value": value}
            if parent_id:
                node["parent"] = parent_id
            return node

        async def link_nodes(parent, child):
            await asyncio.sleep(0.1)
            parent["children"] = [*parent.get("children", []), child["id"]]
            return parent

        tools = {
            "create_node": AsyncMock(side_effect=create_node),
            "link_nodes": AsyncMock(side_effect=link_nodes),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Independent node creation - should parallelize
        root = create_node(1)
        child1 = create_node(2)
        child2 = create_node(3)

        # Linking depends on node creation - should be sequential after creation
        linked_root1 = link_nodes(root, child1)
        linked_root2 = link_nodes(linked_root1, child2)

        output = linked_root2["id"]
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert result == "1"

        # Should achieve some parallelization in the first group
        # Allow 25% tolerance for timing variations
        assert duration < 0.5, f"Expected some parallelization, took {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_array_index_computation_conflicts(self, cy_parallel):
        """Test conflicts when array indices are computed dynamically."""

        async def compute_index(base, offset):
            await asyncio.sleep(0.1)
            return base + offset

        async def store_value(value):
            await asyncio.sleep(0.1)
            return f"stored_{value}"

        tools = {
            "compute_index": AsyncMock(side_effect=compute_index),
            "store_value": AsyncMock(side_effect=store_value),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Array initialization
        data = ["", "", "", "", ""]

        # Compute indices that might conflict
        idx1 = compute_index(1, 0)  # Returns 1
        idx2 = compute_index(0, 1)  # Returns 1 (same as idx1!)
        idx3 = compute_index(2, 0)  # Returns 2

        # Store values at computed indices
        val1 = store_value("first")
        val2 = store_value("second")
        val3 = store_value("third")

        # Assignment to array - potential conflicts
        data[idx1] = val1  # data[1] = "stored_first"
        data[idx2] = val2  # data[1] = "stored_second" (overwrites!)
        data[idx3] = val3  # data[2] = "stored_third"

        output = data[1] + "," + data[2]
        return output
        """

        result = await cy_parallel.run_async(cy_code)

        # Last write wins: idx1 and idx2 both write to index 1
        assert result == '"stored_second,stored_third"'

    @pytest.mark.asyncio
    async def test_conditional_dependency_branches(self, cy_parallel):
        """Test parallel execution across conditional branches."""

        async def expensive_check():
            await asyncio.sleep(0.1)
            return True

        async def process_branch_a():
            await asyncio.sleep(0.1)
            return "branch_a_result"

        async def process_branch_b():
            await asyncio.sleep(0.1)
            return "branch_b_result"

        async def process_independent():
            await asyncio.sleep(0.1)
            return "independent_result"

        tools = {
            "expensive_check": AsyncMock(side_effect=expensive_check),
            "process_branch_a": AsyncMock(side_effect=process_branch_a),
            "process_branch_b": AsyncMock(side_effect=process_branch_b),
            "process_independent": AsyncMock(side_effect=process_independent),
        }
        cy_parallel.tools = tools

        cy_code = """
        # This should run independently of the conditional
        independent = process_independent()

        # Conditional logic
        condition = expensive_check()

        if (condition) {
            branch_result = process_branch_a()
        } else {
            branch_result = process_branch_b()
        }

        output = independent + "," + branch_result
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert result == '"independent_result,branch_a_result"'

        # The independent operation should run in parallel with expensive_check
        # Total time should be less than sequential (3 * 0.1 = 0.3s)
        assert duration < 0.25, f"Expected some parallelization, took {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_mcp_tool_parallel_execution(self, cy_parallel):
        """Test parallel execution with MCP tools."""

        async def mock_mcp_call(server, tool_name, *args, **kwargs):
            await asyncio.sleep(0.1)
            return f"mcp_result_{server}_{tool_name}"

        # Mock MCP manager
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(side_effect=mock_mcp_call)
        # Add tools_cache for tool resolution
        mock_mcp_manager.tools_cache = {
            "mcp::server1::fetch_data": {"name": "fetch_data"},
            "mcp::server2::get_info": {"name": "get_info"},
            "mcp::server1::process": {"name": "process"},
        }
        cy_parallel.mcp_manager = mock_mcp_manager

        cy_code = """
        # Multiple independent MCP calls - should parallelize
        result1 = mcp::server1::fetch_data()
        result2 = mcp::server2::get_info()
        result3 = mcp::server1::process()

        output = result1 + "," + result2 + "," + result3
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert "mcp_result_mcp::server1::fetch_data" in result
        assert "mcp_result_mcp::server2::get_info" in result
        assert "mcp_result_mcp::server1::process" in result

        # Should parallelize MCP calls
        assert duration < 0.2, f"Expected parallel MCP execution, took {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_large_scale_parallel_correctness(self, cy_parallel):
        """Stress test with many parallel operations to check for race conditions."""

        # Counter to verify all operations execute
        call_counter = {"count": 0}

        async def counted_operation(value):
            await asyncio.sleep(0.05)  # Shorter delay for faster test
            call_counter["count"] += 1
            return value * 2

        def make_counted_op(index):
            async def op(v):
                return await counted_operation(index)

            return op

        tools = {}
        for i in range(10):  # Reduce to 10 to avoid recursion
            tools[f"op_{i}"] = AsyncMock(side_effect=make_counted_op(i))

        cy_parallel.tools = tools

        # Generate code with 10 independent operations - use interpolation
        operations = [f"var_{i} = op_{i}({i})" for i in range(10)]
        interpolated_vars = ",".join([f"${{var_{i}}}" for i in range(10)])
        cy_code = (
            "\n".join(operations) + f'\noutput = "{interpolated_vars}"\nreturn output'
        )

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        # Verify correctness - check that all values are present
        for i in range(10):
            expected_value = str(i * 2)
            assert expected_value in result

        # Verify all operations were called
        assert call_counter["count"] == 10

        # Should achieve significant parallelization
        assert duration < 0.3, (
            f"Expected parallel execution for 10 ops, took {duration:.3f}s"
        )
