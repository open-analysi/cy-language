"""
Test specifically designed to reveal how our dependency analyzer handles dynamic dependencies.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from cy_language.interpreter import Cy


class TestDynamicDependencyDetection:
    """Test how well our system detects dynamic dependencies."""

    @pytest.fixture
    async def cy_parallel(self):
        """Create a Cy interpreter with parallel execution enabled."""
        return await Cy.create_async(enable_parallel=True, parallel_threshold=2)

    @pytest.fixture
    async def cy_sequential(self):
        """Create a sequential interpreter for comparison."""
        return await Cy.create_async(enable_parallel=False)

    @pytest.mark.asyncio
    async def test_static_vs_dynamic_field_conflicts(self, cy_parallel, cy_sequential):
        """Compare how static vs dynamic field access affects parallelization."""

        # Test 1: Static field access (should parallelize)
        async def slow_op_static(x):
            await asyncio.sleep(0.1)
            return f"result_{x}"

        tools_static = {
            "slow_op": AsyncMock(side_effect=slow_op_static),
        }

        static_code = """
        obj = {}
        # Static field names - analyzer can see these are different
        obj["field1"] = slow_op(1)
        obj["field2"] = slow_op(2)
        output = obj["field1"] + "," + obj["field2"]
        return output
        """

        cy_parallel.tools = tools_static
        start = time.time()
        result_static = await cy_parallel.run_async(static_code)
        static_duration = time.time() - start

        # Test 2: Dynamic field access (might not parallelize)
        async def slow_op_dynamic(x):
            await asyncio.sleep(0.1)
            return f"result_{x}"

        tools_dynamic = {
            "slow_op": AsyncMock(side_effect=slow_op_dynamic),
            "get_key": Mock(side_effect=lambda x: f"field{x}"),
        }

        dynamic_code = """
        obj = {}
        # Dynamic field names - analyzer can't predict conflicts
        key1 = get_key(1)
        key2 = get_key(2)
        obj[key1] = slow_op(1)
        obj[key2] = slow_op(2)
        output = obj[key1] + "," + obj[key2]
        return output
        """

        cy_parallel.tools = tools_dynamic
        start = time.time()
        result_dynamic = await cy_parallel.run_async(dynamic_code)
        dynamic_duration = time.time() - start

        print(f"Static field access duration: {static_duration:.3f}s")
        print(f"Dynamic field access duration: {dynamic_duration:.3f}s")

        # Both should produce the same result
        assert result_static == '"result_1,result_2"'
        assert result_dynamic == '"result_1,result_2"'

        # The key insight: if dynamic is significantly slower,
        # it means our analyzer is being conservative about unknown dependencies
        if dynamic_duration > static_duration * 1.5:
            print(
                "✓ Our analyzer is conservatively treating dynamic access as potentially dependent"
            )
        else:
            print("! Our analyzer might be missing dynamic dependency analysis")

    @pytest.mark.asyncio
    async def test_actual_dynamic_conflict_detection(self, cy_parallel):
        """Test a case where dynamic access actually creates a real conflict."""

        async def slow_op_conflict(x):
            await asyncio.sleep(0.1)
            return f"result_{x}"

        tools = {
            "slow_op": AsyncMock(side_effect=slow_op_conflict),
            "get_key": Mock(
                side_effect=lambda x: "same_key"
            ),  # Both return the same key!
        }
        cy_parallel.tools = tools

        code = """
        obj = {}
        # Both keys will resolve to "same_key" - this is a real conflict!
        key1 = get_key(1)
        key2 = get_key(2)
        obj[key1] = slow_op(1)  # obj["same_key"] = "result_1"
        obj[key2] = slow_op(2)  # obj["same_key"] = "result_2" (overwrites!)
        output = obj[key1]
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(code)
        duration = time.time() - start

        print(f"Dynamic conflict test duration: {duration:.3f}s")

        # The final value should be "result_2" (last write wins)
        assert result == '"result_2"'

        # If this takes ~0.2s (sequential), our system detected the dependency
        # If this takes ~0.1s (parallel), our system missed the conflict
        if duration > 0.15:
            print(
                "✓ System correctly detected the dynamic conflict (sequential execution)"
            )
        else:
            print("! System may have missed the dynamic conflict (parallel execution)")

        return duration

    @pytest.mark.asyncio
    async def test_variable_dependency_chains(self, cy_parallel):
        """Test complex variable dependency chains."""

        async def slow_op_chains(x):
            await asyncio.sleep(0.1)
            return x * 2

        tools = {
            "slow_op": AsyncMock(side_effect=slow_op_chains),
        }
        cy_parallel.tools = tools

        code = """
        # Complex dependency chain
        a = slow_op(1)      # Independent
        b = slow_op(2)      # Independent (should run parallel with a)
        c = slow_op(a)      # Depends on a
        d = slow_op(b)      # Depends on b (could run parallel with c)
        result = c + d      # Depends on both c and d
        output = result
        return output
        """

        start = time.time()
        result = await cy_parallel.run_async(code)
        duration = time.time() - start

        print(f"Variable dependency chain duration: {duration:.3f}s")
        assert result == "12"  # (1*2)*2 + (2*2)*2 = 4 + 8 = 12

        # Expected: a=2, b=4, c=4, d=8, result=12
        # Optimal parallel execution: ~0.2s (two sequential groups of 0.1s each)
        # Sequential execution: ~0.4s (four operations)

        if duration < 0.25:
            print("✓ Excellent parallelization of variable dependency chain")
        elif duration < 0.35:
            print("~ Good parallelization with some conservative dependencies")
        else:
            print("! May be too conservative about variable dependencies")

    @pytest.mark.asyncio
    async def test_parallel_execution_correctness_under_stress(self, cy_parallel):
        """Stress test to ensure parallel execution doesn't break correctness."""

        # Create a scenario with many potentially parallel operations
        tools = {}
        for i in range(20):
            tools[f"op_{i}"] = AsyncMock(return_value=i)

        # Generate code with 20 independent operations
        operations = [f"var_{i} = op_{i}()" for i in range(20)]
        sum_expr = " + ".join([f"var_{i}" for i in range(20)])
        code = "\n".join(operations) + f"\noutput = {sum_expr}\nreturn output"

        cy_parallel.tools = tools

        start = time.time()
        result = await cy_parallel.run_async(code)
        duration = time.time() - start

        expected_sum = sum(range(20))  # 0+1+2+...+19 = 190
        assert result == str(expected_sum)

        print(f"20 independent operations duration: {duration:.3f}s")
        print(f"Expected sum: {expected_sum}, Got: {result}")

        # With perfect parallelization, this should be very fast
        # With sequential execution, this would be much slower
        if duration < 0.05:
            print("✓ Excellent parallelization of independent operations")
        else:
            print(f"~ Parallelization took {duration:.3f}s for {20} operations")
