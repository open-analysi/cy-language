"""
TDD tests for 6 parallelization detection/execution bugs.

Issue #1: Dead elif branch in _async_depends_on_loop_state (unreachable)
Issue #2: Heuristic tool name matching gives false positives in _has_async_operations_in_loop
Issue #3: _has_shared_resources substring matching gives false positives
Issue #4: Shallow copy in _execute_for_in_iteration_simple
Issue #5: is_independent_iteration always returns True (dead code)
Issue #6: estimate_parallelization_benefit uses os.cpu_count() for async model
"""

from unittest.mock import Mock

import pytest

from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.execution_plan import (
    ArithmeticNode,
    AssignNode,
    ListNode,
    LiteralNode,
    ToolCallNode,
    VariableNode,
    WhileLoopNode,
)


# ────────────────────────────────────────────────────────────
# Issue #1: Dead elif — unreachable branch in _async_depends_on_loop_state
# ────────────────────────────────────────────────────────────
class TestIssue1DeadElifBranch:
    """The elif isinstance(value, ArithmeticNode) at ~L957 is unreachable because
    the preceding if already catches all ArithmeticNode instances.  The dead
    branch is confusing and should be removed.  We verify:
    1. The dead code is gone (inspect the source)
    2. Concat accumulators are still correctly detected (regression test)
    """

    def setup_method(self):
        async def mock_process(x):
            return x

        self.tools = {"process": mock_process}
        self.analyzer = DependencyAnalyzer(tools=self.tools, debug=False)

    def test_no_unreachable_elif_arithmetic_branch(self):
        """The _async_depends_on_loop_state method should NOT have two
        consecutive branches both checking isinstance(..., ArithmeticNode).
        The elif is unreachable dead code since the if already catches all."""
        import inspect

        source = inspect.getsource(self.analyzer._async_depends_on_loop_state)
        lines = source.split("\n")

        # Find all lines that check isinstance(..., ArithmeticNode)
        arithmetic_checks = []
        for i, line in enumerate(lines):
            if "isinstance" in line and "ArithmeticNode" in line:
                stripped = line.strip()
                is_elif = stripped.startswith("elif") or (
                    i > 0 and lines[i - 1].strip().startswith("elif")
                )
                arithmetic_checks.append((i, stripped, is_elif))

        # There should be at most one isinstance ArithmeticNode check
        # per if/elif chain. If there are two where the second is an elif,
        # that elif is unreachable.
        elif_checks = [c for c in arithmetic_checks if c[2]]
        assert len(elif_checks) == 0, (
            f"Found unreachable elif branch(es) checking ArithmeticNode: "
            f"{[c[1] for c in elif_checks]}"
        )

    def test_concat_accumulator_blocks_parallel_when_async_uses_it(self):
        """Regression: accumulator via `results = results + [item]` followed
        by an async call that reads `results` must still be detected."""
        mock_node = Mock(spec=WhileLoopNode)

        # results = results + [item]   (concatenation accumulator)
        assign = Mock(spec=AssignNode)
        assign.variable_name = "results"
        arith = Mock(spec=ArithmeticNode)
        arith.operator = "+"
        var_results = Mock(spec=VariableNode)
        var_results.variable_name = "results"
        arith.left = var_results
        list_item = Mock(spec=ListNode)
        list_item.elements = [Mock(spec=VariableNode, variable_name="item")]
        arith.right = list_item
        assign.value = arith
        assign.expression = arith

        # x = process(results)   (async call reading the accumulator)
        async_assign = Mock(spec=AssignNode)
        async_assign.variable_name = "x"
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "process"
        tool_call.original_name = "process"
        results_arg = Mock(spec=VariableNode)
        results_arg.variable_name = "results"
        tool_call.arguments = [results_arg]
        tool_call.named_arguments = {}
        async_assign.value = tool_call
        async_assign.expression = tool_call

        mock_node.body = [assign, async_assign]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False, (
            "Concatenation accumulator read by async must block parallelization"
        )


# ────────────────────────────────────────────────────────────
# Issue #2: Heuristic tool name matching false positives
# ────────────────────────────────────────────────────────────
class TestIssue2HeuristicToolNameMatching:
    """_has_async_operations_in_loop falls back to substring matching
    (e.g. "get_" ⊂ tool_name) when the tool is not in the registry.
    This produces false positives for sync tools with matching names."""

    def test_sync_tool_with_get_prefix_not_detected_as_async(self):
        """A sync tool named 'get_config' must NOT be detected as async."""

        def get_config(key):
            return {"debug": True}[key]

        tools = {"get_config": get_config}
        analyzer = DependencyAnalyzer(tools=tools, debug=False)

        mock_node = Mock(spec=WhileLoopNode)

        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "get_config"
        tool_call.original_name = "get_config"
        tool_call.arguments = [Mock(spec=LiteralNode, value="debug")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        # A loop with only sync tool calls has no async ops to parallelize
        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert "no async" in reason.lower()

    def test_sync_tool_with_fetch_in_name_not_detected_as_async(self):
        """A sync tool named 'fetch_from_cache' must NOT be detected as async."""

        def fetch_from_cache(key):
            return key

        tools = {"fetch_from_cache": fetch_from_cache}
        analyzer = DependencyAnalyzer(tools=tools, debug=False)

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "fetch_from_cache"
        tool_call.original_name = "fetch_from_cache"
        tool_call.arguments = [Mock(spec=LiteralNode, value="key")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert "no async" in reason.lower()

    def test_unknown_tool_not_in_registry_not_detected_when_assume_off(self):
        """With assume_unregistered_async=False, a tool not in the registry
        should NOT be considered async."""
        # Empty tools dict, explicit opt-out of assuming async
        analyzer = DependencyAnalyzer(
            tools={}, debug=False, assume_unregistered_async=False
        )

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "fetch_data"
        tool_call.original_name = "fetch_data"
        tool_call.arguments = []
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert "no async" in reason.lower()

    def test_actual_async_tool_is_detected(self):
        """An actual async function should still be detected."""

        async def fetch_data(url):
            return url

        tools = {"fetch_data": fetch_data}
        analyzer = DependencyAnalyzer(tools=tools, debug=False)

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "fetch_data"
        tool_call.original_name = "fetch_data"
        tool_call.arguments = [Mock(spec=LiteralNode, value="url")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True
        assert reason is None


# ────────────────────────────────────────────────────────────
# Issue #3: _has_shared_resources false positives
# ────────────────────────────────────────────────────────────
class TestIssue3SharedResourcesFalsePositives:
    """Substring matching for 'query', 'delete' etc. blocks safe
    tools like 'query_virustotal' or 'delete_from_list'."""

    def setup_method(self):
        async def query_virustotal(ip):
            return {"score": 0}

        async def delete_from_list(lst, item):
            return [x for x in lst if x != item]

        self.tools = {
            "query_virustotal": query_virustotal,
            "delete_from_list": delete_from_list,
        }
        self.analyzer = DependencyAnalyzer(tools=self.tools, debug=False)

    def test_query_virustotal_not_blocked_as_shared_resource(self):
        """query_virustotal is a safe read-only API call, not a DB query."""
        mock_node = Mock(spec=WhileLoopNode)

        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "query_virustotal"
        tool_call.original_name = "query_virustotal"
        tool_call.arguments = [Mock(spec=LiteralNode, value="1.2.3.4")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True, (
            f"query_virustotal should be parallelizable, got: {reason}"
        )

    def test_delete_from_list_not_blocked_as_shared_resource(self):
        """delete_from_list is an in-memory operation, not a DB delete."""
        mock_node = Mock(spec=WhileLoopNode)

        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "delete_from_list"
        tool_call.original_name = "delete_from_list"
        tool_call.arguments = [Mock(spec=LiteralNode, value="x")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True, (
            f"delete_from_list should be parallelizable, got: {reason}"
        )

    def test_actual_file_write_still_blocked(self):
        """A tool that genuinely writes files should still be blocked."""

        async def file_write(path, data):
            pass

        tools = {"file_write": file_write}
        analyzer = DependencyAnalyzer(tools=tools, debug=False)

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "file_write"
        tool_call.original_name = "file_write"
        tool_call.arguments = [Mock(spec=LiteralNode, value="/tmp/x")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False

    def test_actual_db_query_still_blocked(self):
        """A tool explicitly named for DB operations should still be blocked."""

        async def sql_query(stmt):
            pass

        tools = {"sql_query": sql_query}
        analyzer = DependencyAnalyzer(tools=tools, debug=False)

        mock_node = Mock(spec=WhileLoopNode)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "sql_query"
        tool_call.original_name = "sql_query"
        tool_call.arguments = [Mock(spec=LiteralNode, value="SELECT 1")]
        tool_call.named_arguments = {}

        mock_node.body = [tool_call]

        can_parallel, reason = analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False


# ────────────────────────────────────────────────────────────
# Issue #4: Shallow copy in _execute_for_in_iteration_simple
# ────────────────────────────────────────────────────────────
class TestIssue4ShallowCopyIsolation:
    """_execute_for_in_iteration_simple uses .copy() (shallow) for
    the iteration context variables.  Mutable objects (dicts, lists)
    inside the parent context could be mutated by one iteration and
    visible to another."""

    @pytest.mark.asyncio
    async def test_iteration_mutation_does_not_leak_to_parent(self):
        """If an iteration body mutates a dict from parent context via
        indexed assignment (data["key"] = "mutated"), parent must not
        see the change.  With shallow copy the iteration's 'data' IS
        the parent's dict, so mutation leaks."""
        from cy_language.execution_plan import (
            IndexedAccessNode,
            IndexedAssignNode,
        )
        from cy_language.executor import ExecutionContext, PlanExecutor

        parent_dict = {"key": "original"}
        ctx = ExecutionContext(
            tools={},
            variables={
                "data": parent_dict,
            },
        )
        executor = PlanExecutor(ctx)

        # Build AST: data["key"] = "mutated"
        target = IndexedAccessNode(
            object_node=VariableNode("data", 1, 1, "n1"),
            index_node=LiteralNode("key", 1, 1, "n2"),
            line_number=1,
            column=1,
            node_id="n3",
        )
        stmt = IndexedAssignNode(
            target=target,
            value=LiteralNode("mutated", 1, 1, "n4"),
            line_number=1,
            column=1,
            node_id="n5",
        )

        mock_node = Mock(spec=WhileLoopNode)
        mock_node.body = [stmt]

        await executor._execute_for_in_iteration_simple(mock_node, "item", "a", 0, None)

        # With deep copy, parent's dict is untouched
        assert parent_dict["key"] == "original", (
            "Iteration mutated parent's dict — shallow copy leaked!"
        )

    @pytest.mark.asyncio
    async def test_two_iterations_get_independent_mutable_copies(self):
        """Two concurrent iterations should each get their own copy of
        mutable parent variables so they can't interfere with each other."""
        from unittest.mock import patch

        from cy_language.executor import ExecutionContext, PlanExecutor

        parent_list = [1, 2, 3]
        ctx = ExecutionContext(
            tools={},
            variables={
                "items": parent_list,
            },
        )
        executor = PlanExecutor(ctx)

        # We'll intercept the iteration contexts to check identity
        captured_contexts = []
        original_init = ExecutionContext.__init__

        def capturing_init(self_inner, *args, **kwargs):
            original_init(self_inner, *args, **kwargs)
            captured_contexts.append(self_inner)

        mock_node = Mock(spec=WhileLoopNode)
        mock_node.body = []

        with patch.object(ExecutionContext, "__init__", capturing_init):
            await executor._execute_for_in_iteration_simple(
                mock_node, "item", "a", 0, None
            )
            await executor._execute_for_in_iteration_simple(
                mock_node, "item", "b", 1, None
            )

        # Should have created 2 iteration contexts
        assert len(captured_contexts) >= 2

        # Each iteration's "items" should be a different object from parent
        for ic in captured_contexts:
            if "items" in ic.variables:
                assert ic.variables["items"] is not parent_list, (
                    "Iteration context shares the same list object as parent — "
                    "shallow copy doesn't isolate mutable values"
                )


# ────────────────────────────────────────────────────────────
# Issue #5: is_independent_iteration is dead code
# ────────────────────────────────────────────────────────────
class TestIssue5RemoveDeadIsIndependentIteration:
    """is_independent_iteration always returns True, making it useless.
    After removal, calling it should raise AttributeError."""

    def test_is_independent_iteration_removed(self):
        """Method should no longer exist on DependencyAnalyzer."""
        analyzer = DependencyAnalyzer()
        assert not hasattr(analyzer, "is_independent_iteration"), (
            "is_independent_iteration should be removed — it always returns True "
            "and misleads callers into thinking iteration independence is checked"
        )


# ────────────────────────────────────────────────────────────
# Issue #6: estimate_parallelization_benefit uses cpu_count
# ────────────────────────────────────────────────────────────
class TestIssue6EstimateBenefitAsyncModel:
    """estimate_parallelization_benefit uses os.cpu_count() to cap
    parallelism, but asyncio.gather runs on one thread.  The benefit
    for async I/O should scale with the number of concurrent I/O ops,
    not with CPU cores."""

    def setup_method(self):
        self.analyzer = DependencyAnalyzer(debug=False)

    def test_single_iteration_no_benefit(self):
        """Single iteration always returns 1.0 regardless."""
        tool = Mock(spec=ToolCallNode)
        tool.tool_name = "fetch"
        assert self.analyzer.estimate_parallelization_benefit([tool], 1) == 1.0

    def test_cpu_only_loop_no_benefit(self):
        """A loop with no I/O operations has no async benefit."""
        lit = Mock(spec=LiteralNode)
        lit.value = 42
        assert self.analyzer.estimate_parallelization_benefit([lit], 10) == 1.0

    def test_io_loop_benefit_scales_with_iterations_not_cpus(self):
        """With 100 iterations of pure I/O, benefit should approach 100x,
        not be capped at cpu_count."""
        import os

        tool = Mock(spec=ToolCallNode)
        tool.tool_name = "fetch"

        benefit = self.analyzer.estimate_parallelization_benefit([tool], 100)

        cpu_count = os.cpu_count() or 4
        # The benefit should be much higher than cpu_count for async I/O
        # With 100 iterations of pure I/O, theoretical speedup is ~100x
        assert benefit > cpu_count, (
            f"Async I/O benefit ({benefit}) should not be capped at cpu_count ({cpu_count})"
        )

    def test_mixed_io_cpu_benefit_proportional_to_io_ratio(self):
        """A loop that's 50% I/O and 50% CPU should have ~50% of max benefit."""
        tool = Mock(spec=ToolCallNode)
        tool.tool_name = "fetch"
        lit = Mock(spec=LiteralNode)
        lit.value = 42

        # 1 IO + 1 CPU = 50% IO ratio, 20 iterations
        benefit_mixed = self.analyzer.estimate_parallelization_benefit([tool, lit], 20)
        # Pure IO, 20 iterations
        benefit_pure = self.analyzer.estimate_parallelization_benefit([tool], 20)

        # Mixed should be less than pure but still meaningful
        assert benefit_mixed < benefit_pure
        assert benefit_mixed > 1.0
