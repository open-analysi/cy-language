"""Tests for async dependency patterns in for-in loops.

These tests ensure that:
1. Independent async operations CAN be parallelized
2. Async operations that depend on loop-modified state CANNOT be parallelized
3. We prevent incorrect results from improper parallelization
"""

from unittest.mock import Mock

from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.execution_plan import (
    ArithmeticNode,
    AssignNode,
    ListNode,
    ToolCallNode,
    VariableNode,
    WhileLoopNode,
)


class TestAsyncDependencyPatterns:
    """Test cases for async operations with dependencies on loop state."""

    def setup_method(self):
        # Create mock async tools for testing
        async def mock_process(x):
            return x

        async def mock_fetch(x):
            return x

        async def mock_update(x):
            return x

        async def mock_get_count(x):
            return x

        self.tools = {
            "process": mock_process,
            "fetch": mock_fetch,
            "update": mock_update,
            "get_count": mock_get_count,
        }
        self.analyzer = DependencyAnalyzer(tools=self.tools, debug=False)

    def test_async_depends_on_accumulator(self):
        """Async operation that uses an accumulator CANNOT be parallelized.

        Example:
            for item in items:
                total = total + item
                result = await process(total)  # Uses current total value

        This cannot be parallelized because each async needs the
        accumulated value at that point in the iteration.
        """
        mock_node = Mock(spec=WhileLoopNode)

        # First: accumulate sum
        assign = Mock(spec=AssignNode)
        assign.variable_name = "sum"
        arith = Mock(spec=ArithmeticNode)
        arith.operator = "+"
        var_sum = Mock(spec=VariableNode)
        var_sum.variable_name = "sum"
        arith.left = var_sum
        arith.right = Mock()  # item
        assign.value = arith
        assign.expression = arith

        # Second: async call using the accumulated sum
        async_call = Mock(spec=ToolCallNode)
        async_call.tool_name = "process"
        sum_arg = Mock(spec=VariableNode)
        sum_arg.variable_name = "sum"  # Uses loop-modified variable!
        async_call.arguments = [sum_arg]
        async_call.named_arguments = {}

        mock_node.body = [assign, async_call]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False, (
            "Should NOT parallelize when async depends on accumulator"
        )
        assert "depend" in reason.lower() or "state" in reason.lower()

    def test_async_with_running_total(self):
        """Async operation that saves running totals CANNOT be parallelized.

        Example:
            for item in items:
                total = total + item
                await save_checkpoint(total)  # Must save in order!
        """
        mock_node = Mock(spec=WhileLoopNode)

        # Accumulate total
        assign = Mock(spec=AssignNode)
        assign.variable_name = "total"
        arith = Mock(spec=ArithmeticNode)
        arith.operator = "+"
        var_total = Mock(spec=VariableNode)
        var_total.variable_name = "total"
        arith.left = var_total
        arith.right = Mock()
        assign.value = arith
        assign.expression = arith

        # Save checkpoint with current total
        save = Mock(spec=ToolCallNode)
        save.tool_name = "save_state"  # Not a file operation, just async
        total_arg = Mock(spec=VariableNode)
        total_arg.variable_name = "total"  # Uses accumulated total
        save.arguments = [total_arg]
        save.named_arguments = {}

        mock_node.body = [assign, save]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False, (
            "Should NOT parallelize when async uses running total"
        )

    def test_async_uses_previous_result(self):
        """Async that depends on previous iteration's result CANNOT be parallelized.

        Example:
            for item in items:
                prev_result = result
                result = await compute(item, prev_result)
        """
        mock_node = Mock(spec=WhileLoopNode)

        # Save previous result
        assign_prev = Mock(spec=AssignNode)
        assign_prev.variable_name = "prev_result"
        var_result = Mock(spec=VariableNode)
        var_result.variable_name = "result"
        assign_prev.value = var_result
        assign_prev.expression = var_result

        # Async compute using previous result
        compute = Mock(spec=ToolCallNode)
        compute.tool_name = "compute"
        item_arg = Mock(spec=VariableNode)
        item_arg.variable_name = "item"
        prev_arg = Mock(spec=VariableNode)
        prev_arg.variable_name = "prev_result"  # Uses previous iteration!
        compute.arguments = [item_arg, prev_arg]
        compute.named_arguments = {}

        # Assign new result
        assign_result = Mock(spec=AssignNode)
        assign_result.variable_name = "result"
        assign_result.value = compute
        assign_result.expression = compute

        mock_node.body = [assign_prev, compute, assign_result]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False, (
            "Should NOT parallelize when using previous iteration result"
        )

    def test_async_only_uses_loop_variable(self):
        """Async that only uses loop variable CAN be parallelized.

        Example:
            for item in items:
                data = await fetch(item)  # Only uses 'item'
                results.append(data)
        """
        mock_node = Mock(spec=WhileLoopNode)

        # Fetch using only loop variable
        fetch = Mock(spec=ToolCallNode)
        fetch.tool_name = "fetch"
        item_var = Mock(spec=VariableNode)
        item_var.variable_name = "item"  # Only loop variable
        fetch.arguments = [item_var]
        fetch.named_arguments = {}

        # Store result (safe accumulation after async)
        assign = Mock(spec=AssignNode)
        assign.variable_name = "data"
        assign.value = fetch
        assign.expression = fetch

        mock_node.body = [fetch, assign]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True, (
            "Should parallelize when async only uses loop variable"
        )

    def test_async_with_independent_accumulator(self):
        """Async followed by accumulation CAN be parallelized.

        Example:
            for item in items:
                data = await fetch(item)  # Independent async
                total = total + data  # Accumulate after

        This CAN be parallelized because the async doesn't depend on total.
        The accumulation happens after all fetches complete.
        """
        mock_node = Mock(spec=WhileLoopNode)

        # First: independent async fetch
        fetch = Mock(spec=ToolCallNode)
        fetch.tool_name = "fetch"
        item_var = Mock(spec=VariableNode)
        item_var.variable_name = "item"
        fetch.arguments = [item_var]
        fetch.named_arguments = {}

        # Assign fetch result
        assign_data = Mock(spec=AssignNode)
        assign_data.variable_name = "data"
        assign_data.value = fetch
        assign_data.expression = fetch

        # Then: accumulate (safe because async doesn't use sum)
        assign_sum = Mock(spec=AssignNode)
        assign_sum.variable_name = "sum"
        arith = Mock(spec=ArithmeticNode)
        arith.operator = "+"
        var_sum = Mock(spec=VariableNode)
        var_sum.variable_name = "sum"
        var_data = Mock(spec=VariableNode)
        var_data.variable_name = "data"
        arith.left = var_sum
        arith.right = var_data
        assign_sum.value = arith
        assign_sum.expression = arith

        mock_node.body = [fetch, assign_data, assign_sum]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True, (
            "Should parallelize when async is independent of accumulator"
        )

    def test_chained_async_within_iteration(self):
        """Chained async operations within same iteration CAN be parallelized.

        Example:
            for item in items:
                temp = await fetch(item)
                result = await process(temp)  # Uses this iteration's temp

        This CAN be parallelized because each iteration's chain is independent.
        """
        mock_node = Mock(spec=WhileLoopNode)

        # First async: fetch
        fetch = Mock(spec=ToolCallNode)
        fetch.tool_name = "fetch"
        item_var = Mock(spec=VariableNode)
        item_var.variable_name = "item"
        fetch.arguments = [item_var]
        fetch.named_arguments = {}

        # Assign to temp
        assign_temp = Mock(spec=AssignNode)
        assign_temp.variable_name = "temp"
        assign_temp.value = fetch
        assign_temp.expression = fetch

        # Second async: process temp
        process = Mock(spec=ToolCallNode)
        process.tool_name = "process"
        temp_var = Mock(spec=VariableNode)
        temp_var.variable_name = "temp"  # Uses this iteration's temp
        process.arguments = [temp_var]
        process.named_arguments = {}

        mock_node.body = [fetch, assign_temp, process]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True, (
            "Should parallelize chained async within iterations"
        )

    def test_async_with_list_append(self):
        """Async with list append CAN be parallelized (order preserved).

        Example:
            for item in items:
                data = await fetch(item)
                results = results + [data]  # Order preserved
        """
        mock_node = Mock(spec=WhileLoopNode)

        # Async fetch
        fetch = Mock(spec=ToolCallNode)
        fetch.tool_name = "fetch"
        item_var = Mock(spec=VariableNode)
        item_var.variable_name = "item"
        fetch.arguments = [item_var]
        fetch.named_arguments = {}

        # Assign fetch result
        assign_data = Mock(spec=AssignNode)
        assign_data.variable_name = "data"
        assign_data.value = fetch
        assign_data.expression = fetch

        # Append to results list
        assign_results = Mock(spec=AssignNode)
        assign_results.variable_name = "results"
        arith = Mock(spec=ArithmeticNode)
        arith.operator = "+"
        var_results = Mock(spec=VariableNode)
        var_results.variable_name = "results"
        arith.left = var_results
        list_node = Mock(spec=ListNode)
        list_node.elements = [Mock()]  # [data]
        arith.right = list_node
        assign_results.value = arith
        assign_results.expression = arith

        mock_node.body = [fetch, assign_data, assign_results]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True, "Should parallelize with list concatenation"

    def test_async_modifies_shared_counter(self):
        """Async that modifies a shared counter based on async result.

        Example:
            for item in items:
                count = await get_count(item)
                total_count = total_count + count

        This CAN be parallelized because async doesn't depend on total_count.
        """
        mock_node = Mock(spec=WhileLoopNode)

        # Get count async (independent)
        get_count = Mock(spec=ToolCallNode)
        get_count.tool_name = "get_count"
        item_var = Mock(spec=VariableNode)
        item_var.variable_name = "item"
        get_count.arguments = [item_var]
        get_count.named_arguments = {}

        # Assign count result
        assign_count = Mock(spec=AssignNode)
        assign_count.variable_name = "count"
        assign_count.value = get_count
        assign_count.expression = get_count

        # Update total_count
        assign_total = Mock(spec=AssignNode)
        assign_total.variable_name = "total_count"
        arith = Mock(spec=ArithmeticNode)
        arith.operator = "+"
        var_total = Mock(spec=VariableNode)
        var_total.variable_name = "total_count"
        var_count = Mock(spec=VariableNode)
        var_count.variable_name = "count"
        arith.left = var_total
        arith.right = var_count
        assign_total.value = arith
        assign_total.expression = arith

        mock_node.body = [get_count, assign_count, assign_total]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True, "Should parallelize when async is independent"
