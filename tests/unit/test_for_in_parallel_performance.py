"""
Performance tests for Part B: Parallel Execution

These tests demonstrate that parallel execution of for-in loops
is actually faster than sequential execution for I/O-bound operations.
"""

import asyncio
import time
from unittest.mock import Mock

import pytest

from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.execution_plan import ToolCallNode
from cy_language.executor import ExecutionContext, PlanExecutor


class TestParallelPerformance:
    """Test that parallel execution is actually faster."""

    def setup_method(self):
        """Set up test fixtures."""
        self.context = ExecutionContext()
        self.analyzer = DependencyAnalyzer()

    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_io_bound(self):
        """Test that parallel is faster for I/O-bound operations."""

        # Create mock I/O-bound tasks
        async def slow_io_task(delay=0.1):
            """Simulate slow I/O operation."""
            await asyncio.sleep(delay)
            return f"Result after {delay}s"

        num_tasks = 5
        delay_per_task = 0.1

        # Sequential execution
        start = time.time()
        sequential_results = []
        for _ in range(num_tasks):
            result = await slow_io_task(delay_per_task)
            sequential_results.append(result)
        sequential_time = time.time() - start

        # Parallel execution using our executor
        executor = PlanExecutor(self.context, enable_parallel=True)
        start = time.time()
        tasks = [slow_io_task(delay_per_task) for _ in range(num_tasks)]
        parallel_results = await executor._collect_parallel_results(tasks)
        parallel_time = time.time() - start

        # Parallel should be significantly faster
        print(f"Sequential: {sequential_time:.2f}s, Parallel: {parallel_time:.2f}s")
        assert parallel_time < sequential_time * 0.5  # At least 2x faster
        assert len(parallel_results) == num_tasks

    @pytest.mark.asyncio
    async def test_parallel_with_different_delays(self):
        """Test parallel execution with varying task durations."""

        async def task_with_delay(delay):
            """Task with specific delay."""
            await asyncio.sleep(delay)
            return f"Completed in {delay}s"

        delays = [0.1, 0.2, 0.15, 0.05, 0.25]

        # Sequential would take sum of all delays
        sequential_expected = sum(delays)

        # Parallel should take max delay
        executor = PlanExecutor(self.context, enable_parallel=True)
        start = time.time()
        tasks = [task_with_delay(d) for d in delays]
        results = await executor._collect_parallel_results(tasks, preserve_order=True)
        parallel_time = time.time() - start

        # Should be close to max delay, not sum
        assert parallel_time < sequential_expected * 0.6
        assert len(results) == len(delays)
        # Results should be in order when preserve_order=True
        for i, result in enumerate(results):
            assert f"{delays[i]}s" in result

    @pytest.mark.asyncio
    async def test_large_scale_parallel_performance(self):
        """Test performance with many tasks."""

        async def quick_task(i):
            """Quick async task."""
            await asyncio.sleep(0.01)
            return i * 2

        num_tasks = 50

        executor = PlanExecutor(self.context, enable_parallel=True)
        start = time.time()
        tasks = [quick_task(i) for i in range(num_tasks)]
        results = await executor._collect_parallel_results(tasks)
        parallel_time = time.time() - start

        # Should handle many tasks efficiently
        sequential_expected = num_tasks * 0.01
        assert parallel_time < sequential_expected * 0.3  # Much faster than sequential
        assert len(results) == num_tasks

    @pytest.mark.asyncio
    async def test_worker_pool_efficiency(self):
        """Test that worker pool is properly limited."""
        import os

        cpu_count = os.cpu_count() or 4

        executor = PlanExecutor(self.context, enable_parallel=True)

        # Test with various task counts
        for num_tasks in [1, 5, 10, 100, 1000]:
            workers = executor._configure_parallel_workers(num_tasks)
            # Should never exceed reasonable limits
            assert workers <= cpu_count * 2
            assert workers <= num_tasks
            assert workers > 0

    @pytest.mark.asyncio
    async def test_parallelization_benefit_estimation(self):
        """Test that benefit estimation is reasonable."""

        # Create loop with I/O operations
        loop_body = [
            Mock(spec=ToolCallNode),
            Mock(spec=ToolCallNode),
            Mock(),  # Non-I/O operation
        ]

        # High I/O ratio should show good benefit
        benefit = self.analyzer.estimate_parallelization_benefit(loop_body, 10)
        assert benefit > 1.0  # Should show some benefit

        # No I/O operations should show no benefit
        loop_body_cpu = [Mock(), Mock(), Mock()]
        benefit_cpu = self.analyzer.estimate_parallelization_benefit(loop_body_cpu, 10)
        assert benefit_cpu == 1.0  # No benefit for CPU-bound

    @pytest.mark.asyncio
    async def test_real_world_scenario(self):
        """Test a realistic for-in loop scenario."""

        # Simulate fetching data from multiple APIs
        async def fetch_api_data(item_id):
            """Simulate API call."""
            await asyncio.sleep(0.05)  # 50ms latency
            return {"id": item_id, "data": f"Data for {item_id}"}

        item_ids = list(range(10))

        # Sequential approach
        start = time.time()
        sequential_results = []
        for item_id in item_ids:
            result = await fetch_api_data(item_id)
            sequential_results.append(result)
        sequential_time = time.time() - start

        # Parallel approach
        executor = PlanExecutor(self.context, enable_parallel=True)
        start = time.time()
        tasks = [fetch_api_data(item_id) for item_id in item_ids]
        parallel_results = await executor._collect_parallel_results(
            tasks, preserve_order=True
        )
        parallel_time = time.time() - start

        print(
            f"Real-world scenario - Sequential: {sequential_time:.2f}s, Parallel: {parallel_time:.2f}s"
        )
        print(f"Speedup: {sequential_time / parallel_time:.1f}x")

        # Should see significant speedup
        assert parallel_time < sequential_time * 0.3  # At least 3x faster
        assert len(parallel_results) == len(item_ids)

        # Verify order preservation
        for i, result in enumerate(parallel_results):
            assert result["id"] == item_ids[i]


class TestParallelErrorHandling:
    """Test error handling in parallel execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.context = ExecutionContext()
        self.executor = PlanExecutor(self.context, enable_parallel=True)

    @pytest.mark.asyncio
    async def test_partial_failures_still_fast(self):
        """Test that partial failures don't slow down execution."""

        async def task_that_might_fail(i):
            """Task that fails for certain inputs."""
            await asyncio.sleep(0.05)
            if i % 3 == 0:
                raise ValueError(f"Task {i} failed")
            return f"Success {i}"

        start = time.time()
        tasks = [task_that_might_fail(i) for i in range(10)]
        results = await self.executor._collect_parallel_results(tasks)
        parallel_time = time.time() - start

        # Should still be fast despite failures
        assert parallel_time < 0.2  # Should complete quickly
        # Should get partial results
        assert len(results) > 0
        assert len(results) < 10  # Some failed

    @pytest.mark.asyncio
    async def test_empty_and_single_task_performance(self):
        """Test edge cases perform correctly."""
        # Empty task list
        start = time.time()
        results = await self.executor._collect_parallel_results([])
        elapsed = time.time() - start
        assert elapsed < 0.01  # Should be instant
        assert results == []

        # Single task
        async def single():
            await asyncio.sleep(0.05)
            return "single"

        start = time.time()
        results = await self.executor._collect_parallel_results([single()])
        elapsed = time.time() - start
        assert 0.04 < elapsed < 0.1  # Just the task time
        assert results == ["single"]
