"""
Advanced edge cases for parallel execution that stress-test the dependency analyzer.

These tests explore complex scenarios that could reveal limitations in our static analysis.
"""

import time
from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.interpreter import Cy


class TestParallelAdvancedEdgeCases:
    """Test advanced edge cases for parallel execution."""

    @pytest.fixture
    async def cy_parallel(self):
        """Create a Cy interpreter with parallel execution enabled."""
        return await Cy.create_async(enable_parallel=True, parallel_threshold=2)

    @pytest.mark.asyncio
    async def test_dynamic_field_access_dependencies(self, cy_parallel):
        """Test dependencies when field names are computed at runtime.

        This is challenging because static analysis can't determine which fields
        are being accessed until runtime.
        """
        tools = {
            "get_field_name": Mock(side_effect=lambda prefix: f"{prefix}_field"),
            "compute_value1": AsyncMock(return_value="value1"),
            "compute_value2": AsyncMock(return_value="value2"),
            "compute_value3": AsyncMock(return_value="value3"),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Dynamic field names - static analyzer can't predict these
        key1 = get_field_name("first")    # Returns "first_field"
        key2 = get_field_name("second")   # Returns "second_field"
        key3 = get_field_name("first")    # Returns "first_field" (same as key1!)

        # Initialize object
        obj = {}

        # These operations have complex dependencies:
        obj[key1] = compute_value1()      # obj["first_field"] = "value1"
        obj[key2] = compute_value2()      # obj["second_field"] = "value2" (should be parallel with above)
        obj[key3] = compute_value3()      # obj["first_field"] = "value3" (overwrites first!)

        # Verify the final state
        output = obj[key1] + "," + obj[key2]
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        # Final result: key1 and key3 both point to "first_field", so obj["first_field"] = "value3"
        assert result == '"value3,value2"'

        # Critical test: Since key1 and key3 both resolve to "first_field",
        # there should be a dependency between obj[key1] and obj[key3]
        # But our static analyzer can't detect this, so it might incorrectly parallelize them
        print(
            f"Execution time: {duration:.3f}s - this reveals if dynamic conflicts are detected"
        )

    @pytest.mark.asyncio
    async def test_computed_index_conflicts(self, cy_parallel):
        """Test array access with computed indices that might conflict."""
        tools = {
            "get_index": Mock(
                side_effect=lambda base: base % 3
            ),  # Maps 0,3,6->0, 1,4,7->1, etc.
            "process_item": AsyncMock(side_effect=lambda item: f"processed_{item}"),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Computed indices that might conflict
        idx1 = get_index(0)   # Returns 0
        idx2 = get_index(1)   # Returns 1
        idx3 = get_index(3)   # Returns 0 (same as idx1!)

        # Initialize array
        arr = ["", "", ""]

        # These have a hidden conflict that static analysis can't detect
        arr[idx1] = process_item("first")   # arr[0] = "processed_first"
        arr[idx2] = process_item("second")  # arr[1] = "processed_second" (parallel with above)
        arr[idx3] = process_item("third")   # arr[0] = "processed_third" (overwrites first!)

        output = arr[0] + "," + arr[1] + "," + arr[2]
        return output
        """

        result = await cy_parallel.run_async(cy_code)

        # arr[0] gets overwritten: first by "processed_first", then by "processed_third"
        assert result == '"processed_third,processed_second,"'

    @pytest.mark.asyncio
    async def test_conditional_field_access_patterns(self, cy_parallel):
        """Test field access patterns that depend on conditional logic."""
        tools = {
            "check_condition": Mock(return_value=True),
            "get_data_a": AsyncMock(return_value="data_a"),
            "get_data_b": AsyncMock(return_value="data_b"),
            "process_data": AsyncMock(side_effect=lambda x: f"processed_{x}"),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Conditional logic affects which fields are accessed
        use_a = check_condition()

        # Object initialization
        result = {"a": "", "b": ""}

        if (use_a) {
            # These operations are within a control flow block
            # Our analyzer should treat control flow as a barrier
            result["a"] = get_data_a()
            result["b"] = get_data_b()
        } else {
            result["a"] = "default_a"
            result["b"] = "default_b"
        }

        # This runs after the conditional block
        final_a = process_data(result["a"])
        final_b = process_data(result["b"])

        output = final_a + "," + final_b
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == '"processed_data_a,processed_data_b"'

    @pytest.mark.asyncio
    async def test_chained_dynamic_access(self, cy_parallel):
        """Test chained dynamic access that creates complex dependency patterns."""
        tools = {
            "get_config": AsyncMock(return_value={"db": {"table": "users"}}),
            "get_table_name": Mock(side_effect=lambda config: config["db"]["table"]),
            "query_table": AsyncMock(side_effect=lambda table: f"data_from_{table}"),
            "process_results": AsyncMock(side_effect=lambda data: f"processed_{data}"),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Chain of dynamic access that creates implicit dependencies
        config = get_config()
        table_name = get_table_name(config)

        # These operations have implicit dependencies through the table_name
        raw_data = query_table(table_name)
        processed = process_results(raw_data)

        output = processed
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == '"processed_data_from_users"'

    @pytest.mark.asyncio
    async def test_complex_nested_mutation(self, cy_parallel):
        """Test complex nested object mutations with potential conflicts."""
        tools = {
            "get_user_id": Mock(return_value="user123"),
            "get_theme": AsyncMock(return_value="dark"),
            "get_language": AsyncMock(return_value="en"),
            "log_action": AsyncMock(return_value="logged"),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Complex nested structure
        config = {
            "users": {},
            "logs": []
        }

        user_id = get_user_id()

        # Initialize nested structure
        config["users"][user_id] = {"settings": {}}

        # These nested mutations might have subtle conflicts
        config["users"][user_id]["settings"]["theme"] = get_theme()
        config["users"][user_id]["settings"]["language"] = get_language()

        # This accesses a different part of the structure
        config["logs"] = [log_action()]

        # Access the final state
        theme = config["users"][user_id]["settings"]["theme"]
        lang = config["users"][user_id]["settings"]["language"]
        log = config["logs"][0]

        output = theme + "," + lang + "," + log
        return output
        """

        result = await cy_parallel.run_async(cy_code)
        assert result == '"dark,en,logged"'

    @pytest.mark.asyncio
    async def test_function_composition_with_side_effects(self, cy_parallel):
        """Test function composition where intermediate results affect dependencies."""
        call_tracker = {"calls": []}

        def track_call(name):
            def wrapper(*args):
                call_tracker["calls"].append(name)
                return f"{name}_result"

            return wrapper

        tools = {
            "step1": AsyncMock(side_effect=track_call("step1")),
            "step2": AsyncMock(side_effect=track_call("step2")),
            "step3": AsyncMock(side_effect=track_call("step3")),
            "combine": Mock(side_effect=lambda a, b: f"{a}+{b}"),
        }
        cy_parallel.tools = tools

        cy_code = """
        # Function composition that could be parallelized
        path1_step1 = step1()
        path1_step2 = step2()
        path1_result = combine(path1_step1, path1_step2)

        # Independent path
        path2_result = step3()

        # Final combination
        final = combine(path1_result, path2_result)
        output = final
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(cy_code)
        duration = time.time() - start

        assert result == '"step1_result+step2_result+step3_result"'

        # Check if step1, step2, and step3 were called in parallel
        # (we can't easily verify the exact timing, but we can verify the result is correct)
        assert len(call_tracker["calls"]) == 3
        assert "step1" in call_tracker["calls"]
        assert "step2" in call_tracker["calls"]
        assert "step3" in call_tracker["calls"]

        print(f"Function composition execution time: {duration:.3f}s")
        print(f"Call order: {call_tracker['calls']}")
