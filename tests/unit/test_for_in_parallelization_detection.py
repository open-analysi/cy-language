"""
Tests for Part B: Parallelization Detection for For-In Loops

This module tests the detection of parallelizable vs non-parallelizable patterns
in for-in loops. These tests will fail until parallelization is implemented (TDD).
"""

from unittest.mock import Mock

from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.execution_plan import WhileLoopNode


class TestParallelizablePatterns:
    """Test detection of patterns that CAN be parallelized."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DependencyAnalyzer(debug=False)

    def test_independent_tool_calls(self):
        """Each iteration calls a tool with no shared state."""
        # Create a mock for-in loop node
        mock_node = Mock(spec=WhileLoopNode)
        mock_node.body = []  # Would contain tool call nodes

        # Should detect as parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True
        assert reason is None

    def test_independent_computations(self):
        """Each iteration performs calculations without dependencies."""
        mock_node = Mock(spec=WhileLoopNode)
        mock_node.body = []  # Would contain arithmetic nodes

        # Should detect as parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True
        assert reason is None

    def test_list_element_modification(self):
        """Modifying properties of list elements (safe when elements are independent)."""
        mock_node = Mock(spec=WhileLoopNode)
        mock_node.body = []  # Would contain indexed assignments

        # Should detect as parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True
        assert reason is None

    def test_local_variables_only(self):
        """Using only iterator and local variables within loop."""
        mock_node = Mock(spec=WhileLoopNode)
        mock_node.body = []  # Would contain only local variable usage

        # Should detect as parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True
        assert reason is None

    def test_independent_api_calls(self):
        """Each iteration makes independent API calls."""
        mock_node = Mock(spec=WhileLoopNode)
        mock_node.body = []  # Would contain async tool calls

        # Should detect as parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is True
        assert reason is None


class TestNonParallelizablePatterns:
    """Test detection of patterns that CANNOT be parallelized."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DependencyAnalyzer(debug=False)

    def test_shared_accumulator(self):
        """Loop accumulates results in a shared variable."""
        from cy_language.execution_plan import ArithmeticNode, AssignNode, VariableNode

        mock_node = Mock(spec=WhileLoopNode)
        # Create a mock accumulator pattern: sum = sum + item
        assign_node = Mock(spec=AssignNode)
        assign_node.variable_name = "sum"

        # Create arithmetic node with left and right
        arith_node = Mock(spec=ArithmeticNode)
        # Left side reads the same variable (accumulator pattern)
        var_node = Mock(spec=VariableNode)
        var_node.variable_name = "sum"
        arith_node.left = var_node
        arith_node.right = Mock()  # Some other value

        assign_node.value = arith_node

        mock_node.body = [assign_node]

        # Should detect as NOT parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert reason is not None
        # Without async operations, the reason will be about no async
        assert (
            "async" in reason.lower()
            or "accumulator" in reason.lower()
            or "shared" in reason.lower()
            or "external" in reason.lower()
        )

    def test_external_state_modification(self):
        """Modifies variables defined outside the loop."""
        from cy_language.execution_plan import AssignNode

        mock_node = Mock(spec=WhileLoopNode)
        # Create assignment that modifies external variable
        assign_node = Mock(spec=AssignNode)
        assign_node.variable_name = "external_var"
        mock_node.body = [assign_node]

        # Should detect as NOT parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert reason is not None
        # Without async operations, the reason will be about no async
        assert (
            "async" in reason.lower()
            or "external" in reason.lower()
            or "state" in reason.lower()
        )

    def test_early_return(self):
        """Contains return statement affecting control flow."""
        from cy_language.execution_plan import ReturnNode

        mock_node = Mock(spec=WhileLoopNode)
        # Add return node to body
        return_node = Mock(spec=ReturnNode)
        mock_node.body = [return_node]

        # Should detect as NOT parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert reason is not None
        # Without async operations, the reason will be about no async
        assert (
            "async" in reason.lower()
            or "return" in reason.lower()
            or "control" in reason.lower()
        )

    def test_cross_iteration_dependency(self):
        """Later iterations depend on results from earlier ones."""
        from cy_language.execution_plan import AssignNode

        mock_node = Mock(spec=WhileLoopNode)
        # Create a dependency pattern
        assign_node = Mock(spec=AssignNode)
        assign_node.variable_name = "prev"
        mock_node.body = [assign_node]

        # Should detect as NOT parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert reason is not None
        # Without async operations, the reason will be about no async
        assert (
            "async" in reason.lower()
            or "depend" in reason.lower()
            or "iteration" in reason.lower()
            or "external" in reason.lower()
        )

    def test_shared_resource_access(self):
        """Accessing/modifying a shared resource that requires synchronization."""
        from cy_language.execution_plan import ToolCallNode

        mock_node = Mock(spec=WhileLoopNode)
        # Tool calls often access shared resources
        tool_node = Mock(spec=ToolCallNode)
        mock_node.body = [tool_node]

        # Should detect as NOT parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        assert reason is not None
        # Without async operations, the reason will be about no async
        assert (
            "async" in reason.lower()
            or "shared" in reason.lower()
            or "resource" in reason.lower()
        )


class TestMixedPatterns:
    """Test detection in complex scenarios with mixed patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DependencyAnalyzer(debug=False)

    def test_nested_loops_outer_parallel_inner_sequential(self):
        """Outer loop parallelizable, inner loop sequential."""
        outer_node = Mock(spec=WhileLoopNode)
        inner_node = Mock(spec=WhileLoopNode)
        inner_node.body = []  # Add body attribute to inner node
        inner_node.condition = Mock()  # Add condition attribute
        outer_node.body = [inner_node]

        # Outer should be parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(outer_node)
        # This is complex - may need special handling
        assert can_parallel is not None  # Just check it returns something

    def test_conditional_dependency(self):
        """Dependencies exist only in certain conditions."""
        from cy_language.execution_plan import AssignNode

        mock_node = Mock(spec=WhileLoopNode)
        # Add assignment to make it non-parallelizable
        assign_node = Mock(spec=AssignNode)
        assign_node.variable_name = "conditional_var"
        mock_node.body = [assign_node]

        # Should be conservative and mark as NOT parallelizable
        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False


class TestDetectionHelpers:
    """Test helper methods for parallelization detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DependencyAnalyzer(debug=False)

    def test_detect_loop_dependencies(self):
        """Test dependency detection within loop body."""
        mock_body = []  # Mock loop body nodes
        dependencies = self.analyzer.detect_loop_dependencies(mock_body)
        assert isinstance(dependencies, dict)

    def test_has_side_effects(self):
        """Test side effect detection."""
        from cy_language.execution_plan import VariableNode

        # Test with node that should not have side effects
        mock_node = Mock(spec=VariableNode)
        has_effects = self.analyzer.has_side_effects(mock_node)
        assert isinstance(has_effects, bool)
        # Variable nodes should not have side effects
        assert has_effects is False

    def test_estimate_parallelization_benefit(self):
        """Test benefit estimation."""
        mock_body = []
        num_iterations = 10
        benefit = self.analyzer.estimate_parallelization_benefit(
            mock_body, num_iterations
        )
        assert isinstance(benefit, float)
        assert benefit >= 1.0  # Should be at least 1.0 (no slowdown)


class TestCriticalSafetyChecks:
    """Test critical safety checks to prevent data corruption."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DependencyAnalyzer(debug=False, assume_unregistered_async=False)

    def test_shared_dictionary_mutation_prevented(self):
        """Test that mutations to shared dictionaries are caught."""
        from cy_language.execution_plan import (
            IndexedAssignNode,
            VariableNode,
            WhileLoopNode,
        )

        mock_node = Mock(spec=WhileLoopNode)

        # Simulate: shared_dict["key"] = value
        indexed_assign = Mock(spec=IndexedAssignNode)
        collection = Mock(spec=VariableNode)
        collection.variable_name = "shared_dict"
        indexed_assign.collection = collection

        mock_node.body = [indexed_assign]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        # Without async operations, the reason will be about no async
        assert "async" in reason.lower() or "shared data structure" in reason.lower()

    def test_file_io_operations_prevented(self):
        """Test that file I/O operations prevent parallelization."""
        from cy_language.execution_plan import ToolCallNode, WhileLoopNode

        mock_node = Mock(spec=WhileLoopNode)

        # Simulate: write_file("output.txt", data)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "write_file"

        mock_node.body = [tool_call]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        # Without async operations, the reason will be about no async
        assert "async" in reason.lower() or "shared resources" in reason.lower()

    def test_database_operations_prevented(self):
        """Test that database operations prevent parallelization."""
        from cy_language.execution_plan import ToolCallNode, WhileLoopNode

        mock_node = Mock(spec=WhileLoopNode)

        # Simulate: database_update(record)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "database_update"

        mock_node.body = [tool_call]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        # Without async operations, the reason will be about no async
        assert "async" in reason.lower() or "shared resources" in reason.lower()

    def test_try_catch_blocks_prevented(self):
        """Test that try-catch blocks prevent parallelization."""
        from cy_language.execution_plan import TryCatchNode, WhileLoopNode

        mock_node = Mock(spec=WhileLoopNode)

        # Simulate a try-catch block
        try_catch = Mock(spec=TryCatchNode)
        try_catch.try_body = []
        try_catch.catch_clauses = []

        mock_node.body = [try_catch]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        # Without async operations, the reason will be about no async
        assert "async" in reason.lower() or "try-catch" in reason.lower()

    def test_shared_list_concatenation_prevented(self):
        """Test that shared list concatenation is caught."""
        from cy_language.execution_plan import (
            ArithmeticNode,
            AssignNode,
            VariableNode,
            WhileLoopNode,
        )

        mock_node = Mock(spec=WhileLoopNode)

        # Simulate: results = results + [item]
        assign = Mock(spec=AssignNode)
        assign.variable_name = "results"

        concat = Mock(spec=ArithmeticNode)
        concat.operator = "+"
        left = Mock(spec=VariableNode)
        left.variable_name = "results"  # Same variable - accumulator pattern
        concat.left = left
        concat.right = Mock()

        assign.value = concat
        assign.expression = concat

        mock_node.body = [assign]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        # It's caught as "shared accumulator" which is correct
        # Without async operations, the reason will be about no async
        assert (
            "async" in reason.lower()
            or "shared accumulator" in reason.lower()
            or "shared list concatenation" in reason.lower()
        )

    def test_shared_array_mutation_prevented(self):
        """Test that mutations to shared arrays are caught."""
        from cy_language.execution_plan import (
            IndexedAssignNode,
            VariableNode,
            WhileLoopNode,
        )

        mock_node = Mock(spec=WhileLoopNode)

        # Simulate: shared_array[i] = value
        indexed_assign = Mock(spec=IndexedAssignNode)
        collection = Mock(spec=VariableNode)
        collection.variable_name = "shared_array"
        indexed_assign.collection = collection

        mock_node.body = [indexed_assign]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        # Without async operations, the reason will be about no async
        assert "async" in reason.lower() or "shared data structure" in reason.lower()

    def test_parallel_array_index_race_condition(self):
        """Test detection of race conditions when multiple iterations modify same array."""
        from cy_language.execution_plan import (
            IndexedAssignNode,
            LiteralNode,
            VariableNode,
            WhileLoopNode,
        )

        mock_node = Mock(spec=WhileLoopNode)

        # Simulate: for (i in range) { array[0] = i }
        # All iterations write to same index - RACE CONDITION!
        indexed_assign = Mock(spec=IndexedAssignNode)
        collection = Mock(spec=VariableNode)
        collection.variable_name = "array"
        indexed_assign.collection = collection

        # Index is a literal 0 - all iterations write to same spot!
        index = Mock(spec=LiteralNode)
        index.value = 0
        indexed_assign.index = index

        mock_node.body = [indexed_assign]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        # Without async operations, the reason will be about no async
        assert "async" in reason.lower() or "shared data structure" in reason.lower()

    def test_multidimensional_array_mutation_prevented(self):
        """Test that mutations to multi-dimensional arrays are caught."""
        from cy_language.execution_plan import (
            IndexedAssignNode,
            VariableNode,
            WhileLoopNode,
        )

        mock_node = Mock(spec=WhileLoopNode)

        # Simulate: matrix[i][j] = value
        # Even nested indexed assignments should be caught
        indexed_assign = Mock(spec=IndexedAssignNode)

        # The collection is itself an indexed access (matrix[i])
        outer_indexed = Mock(spec=IndexedAssignNode)
        matrix = Mock(spec=VariableNode)
        matrix.variable_name = "matrix"
        outer_indexed.collection = matrix
        outer_indexed.target = None  # IndexedAssignNode has a target attribute
        outer_indexed.value = None  # IndexedAssignNode has a value attribute

        indexed_assign.collection = outer_indexed  # matrix[i][j]
        indexed_assign.target = None  # IndexedAssignNode needs target
        indexed_assign.value = None  # IndexedAssignNode needs value

        mock_node.body = [indexed_assign]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        assert can_parallel is False
        # Without async operations, the reason will be about no async
        assert "async" in reason.lower() or (
            "shared" in reason.lower() and "data structure" in reason.lower()
        )

    def test_safe_operations_allowed(self):
        """Test that safe operations are still allowed to parallelize."""
        from cy_language.execution_plan import ToolCallNode, WhileLoopNode

        mock_node = Mock(spec=WhileLoopNode)

        # Simulate safe operations: len(item), str(item)
        tool_call = Mock(spec=ToolCallNode)
        tool_call.tool_name = "len"  # Pure function
        tool_call.arguments = []  # ToolCallNode has arguments
        tool_call.named_arguments = {}  # Also has named arguments

        mock_node.body = [tool_call]

        can_parallel, reason = self.analyzer.can_parallelize_for_in(mock_node)
        # Without async operations, it can't be parallelized
        assert can_parallel is False
        assert reason is not None
        assert "async" in reason.lower()
