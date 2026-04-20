"""
Unit tests for the dependency analyzer module.

Tests dependency detection and parallel group identification.
"""

from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.execution_plan import (
    AssignNode,
    ConditionalNode,
    FieldAccessNode,
    IndexedAccessNode,
    IndexedAssignNode,
    LiteralNode,
    ToolCallNode,
    VariableNode,
    WhileLoopNode,
)


class TestDependencyAnalyzer:
    """Test the DependencyAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DependencyAnalyzer(debug=False)

    # Test Cases from TEST_PLAN.md

    def test_independent_variables(self):
        """Test that independent variable assignments can be parallelized.

        Input: a = func1(), b = func2(), c = func3()
        Expected: All three in same parallel group
        """
        nodes = [
            AssignNode(
                variable_name="a",
                expression=ToolCallNode(
                    tool_name="func1",
                    arguments=[],
                    named_arguments={},
                    line_number=1,
                    column=1,
                    node_id="n1",
                ),
                line_number=1,
                column=1,
                node_id="a1",
            ),
            AssignNode(
                variable_name="b",
                expression=ToolCallNode(
                    tool_name="func2",
                    arguments=[],
                    named_arguments={},
                    line_number=2,
                    column=1,
                    node_id="n2",
                ),
                line_number=2,
                column=1,
                node_id="a2",
            ),
            AssignNode(
                variable_name="c",
                expression=ToolCallNode(
                    tool_name="func3",
                    arguments=[],
                    named_arguments={},
                    line_number=3,
                    column=1,
                    node_id="n3",
                ),
                line_number=3,
                column=1,
                node_id="a3",
            ),
        ]

        dependencies = self.analyzer.analyze_node_dependencies(nodes)
        groups = self.analyzer.find_parallel_groups(dependencies)

        # All should be in the same group (can run in parallel)
        assert len(groups) == 1
        assert set(groups[0]) == {0, 1, 2}

    def test_read_after_write_dependency(self):
        """Test that read-after-write creates proper dependency.

        Input: a = func1(), b = use(a)
        Expected: Sequential execution (b depends on a)
        """
        nodes = [
            AssignNode(
                variable_name="a",
                expression=ToolCallNode(
                    tool_name="func1",
                    arguments=[],
                    named_arguments={},
                    line_number=1,
                    column=1,
                    node_id="n1",
                ),
                line_number=1,
                column=1,
                node_id="a1",
            ),
            AssignNode(
                variable_name="b",
                expression=ToolCallNode(
                    tool_name="use",
                    arguments=[],
                    named_arguments={
                        "value": VariableNode(
                            variable_name="a", line_number=2, column=10, node_id="v1"
                        )
                    },
                    line_number=2,
                    column=1,
                    node_id="n2",
                ),
                line_number=2,
                column=1,
                node_id="a2",
            ),
        ]

        dependencies = self.analyzer.analyze_node_dependencies(nodes)

        # Node 1 should depend on Node 0
        assert 0 in dependencies[1]
        assert len(dependencies[0]) == 0  # First node has no dependencies

        groups = self.analyzer.find_parallel_groups(dependencies)

        # Should be in separate groups (sequential)
        assert len(groups) == 2
        assert groups[0] == [0]
        assert groups[1] == [1]

    def test_write_after_write_same_variable(self):
        """Test that multiple writes to same variable are sequential.

        Input: a = func1(), a = func2()
        Expected: Sequential execution (preserve order)
        """
        nodes = [
            AssignNode(
                variable_name="a",
                expression=ToolCallNode(
                    tool_name="func1",
                    arguments=[],
                    named_arguments={},
                    line_number=1,
                    column=1,
                    node_id="n1",
                ),
                line_number=1,
                column=1,
                node_id="a1",
            ),
            AssignNode(
                variable_name="a",
                expression=ToolCallNode(
                    tool_name="func2",
                    arguments=[],
                    named_arguments={},
                    line_number=2,
                    column=1,
                    node_id="n2",
                ),
                line_number=2,
                column=1,
                node_id="a2",
            ),
        ]

        dependencies = self.analyzer.analyze_node_dependencies(nodes)

        # Second write should depend on first write
        assert 0 in dependencies[1]

        groups = self.analyzer.find_parallel_groups(dependencies)

        # Should be sequential
        assert len(groups) == 2
        assert groups[0] == [0]
        assert groups[1] == [1]

    def test_write_after_read_dependency(self):
        """Test that write-after-read creates proper dependency.

        Input: b = use(a), a = func1()
        Expected: Sequential execution (writer waits for reader)
        """
        nodes = [
            AssignNode(
                variable_name="b",
                expression=ToolCallNode(
                    tool_name="use",
                    arguments=[],
                    named_arguments={
                        "value": VariableNode(
                            variable_name="a", line_number=1, column=10, node_id="v1"
                        )
                    },
                    line_number=1,
                    column=1,
                    node_id="n1",
                ),
                line_number=1,
                column=1,
                node_id="a1",
            ),
            AssignNode(
                variable_name="a",
                expression=ToolCallNode(
                    tool_name="func1",
                    arguments=[],
                    named_arguments={},
                    line_number=2,
                    column=1,
                    node_id="n2",
                ),
                line_number=2,
                column=1,
                node_id="a2",
            ),
        ]

        dependencies = self.analyzer.analyze_node_dependencies(nodes)

        # Write to 'a' should depend on read of 'a'
        assert 0 in dependencies[1]

        groups = self.analyzer.find_parallel_groups(dependencies)
        assert len(groups) == 2

    def test_complex_dependency_chain(self):
        """Test complex interleaved reads and writes.

        a = func1()  # 0
        b = func2()  # 1 (parallel with 0)
        c = use(a)   # 2 (depends on 0)
        d = use(b)   # 3 (depends on 1, parallel with 2)
        e = merge(c, d)  # 4 (depends on 2 and 3)
        """
        nodes = [
            AssignNode(
                variable_name="a",
                expression=ToolCallNode(
                    tool_name="func1",
                    arguments=[],
                    named_arguments={},
                    line_number=1,
                    column=1,
                    node_id="n1",
                ),
                line_number=1,
                column=1,
                node_id="a1",
            ),
            AssignNode(
                variable_name="b",
                expression=ToolCallNode(
                    tool_name="func2",
                    arguments=[],
                    named_arguments={},
                    line_number=2,
                    column=1,
                    node_id="n2",
                ),
                line_number=2,
                column=1,
                node_id="a2",
            ),
            AssignNode(
                variable_name="c",
                expression=ToolCallNode(
                    tool_name="use",
                    arguments=[],
                    named_arguments={
                        "value": VariableNode(
                            variable_name="a", line_number=3, column=10, node_id="v1"
                        )
                    },
                    line_number=3,
                    column=1,
                    node_id="n3",
                ),
                line_number=3,
                column=1,
                node_id="a3",
            ),
            AssignNode(
                variable_name="d",
                expression=ToolCallNode(
                    tool_name="use",
                    arguments=[],
                    named_arguments={
                        "value": VariableNode(
                            variable_name="b", line_number=4, column=10, node_id="v2"
                        )
                    },
                    line_number=4,
                    column=1,
                    node_id="n4",
                ),
                line_number=4,
                column=1,
                node_id="a4",
            ),
            AssignNode(
                variable_name="e",
                expression=ToolCallNode(
                    tool_name="merge",
                    arguments=[],
                    named_arguments={
                        "left": VariableNode(
                            variable_name="c", line_number=5, column=12, node_id="v3"
                        ),
                        "right": VariableNode(
                            variable_name="d", line_number=5, column=15, node_id="v4"
                        ),
                    },
                    line_number=5,
                    column=1,
                    node_id="n5",
                ),
                line_number=5,
                column=1,
                node_id="a5",
            ),
        ]

        dependencies = self.analyzer.analyze_node_dependencies(nodes)

        # Check dependencies
        assert len(dependencies[0]) == 0  # a has no deps
        assert len(dependencies[1]) == 0  # b has no deps
        assert 0 in dependencies[2]  # c depends on a
        assert 1 in dependencies[3]  # d depends on b
        assert 2 in dependencies[4]  # e depends on c
        assert 3 in dependencies[4]  # e depends on d

        groups = self.analyzer.find_parallel_groups(dependencies)

        # Expected groups:
        # Group 0: [0, 1] - a and b can run in parallel
        # Group 1: [2, 3] - c and d can run in parallel
        # Group 2: [4]    - e runs alone
        assert len(groups) == 3
        assert set(groups[0]) == {0, 1}
        assert set(groups[1]) == {2, 3}
        assert groups[2] == [4]

    def test_field_access_dependencies(self):
        """Test that different fields can be written in parallel.

        Input: obj.field1 = func1(), obj.field2 = func2()
        Expected: Parallel execution (different fields)
        """
        # Create field access nodes for obj.field1 and obj.field2
        obj_var = VariableNode(
            variable_name="obj", line_number=1, column=1, node_id="v1"
        )

        # For field assignments, we use IndexedAssignNode with FieldAccessNode as target
        nodes = [
            IndexedAssignNode(
                target=FieldAccessNode(
                    object_node=obj_var,
                    field_name="field1",
                    line_number=1,
                    column=1,
                    node_id="f1",
                ),
                value=ToolCallNode(
                    tool_name="func1",
                    arguments=[],
                    named_arguments={},
                    line_number=1,
                    column=15,
                    node_id="n1",
                ),
                line_number=1,
                column=1,
                node_id="ia1",
            ),
            IndexedAssignNode(
                target=FieldAccessNode(
                    object_node=obj_var,
                    field_name="field2",
                    line_number=2,
                    column=1,
                    node_id="f2",
                ),
                value=ToolCallNode(
                    tool_name="func2",
                    arguments=[],
                    named_arguments={},
                    line_number=2,
                    column=15,
                    node_id="n2",
                ),
                line_number=2,
                column=1,
                node_id="ia2",
            ),
        ]

        dependencies = self.analyzer.analyze_node_dependencies(nodes)
        groups = self.analyzer.find_parallel_groups(dependencies)

        # Different fields should allow parallel execution
        assert len(groups) == 1
        assert set(groups[0]) == {0, 1}

    def test_array_index_dependencies(self):
        """Test that different array indices can be written in parallel.

        Input: arr[0] = func1(), arr[1] = func2()
        Expected: Parallel execution (different indices)
        """
        nodes = [
            IndexedAssignNode(
                target=IndexedAccessNode(
                    object_node=VariableNode(
                        variable_name="arr", line_number=1, column=1, node_id="v1"
                    ),
                    index_node=LiteralNode(
                        value=0, line_number=1, column=5, node_id="l1"
                    ),
                    line_number=1,
                    column=1,
                    node_id="idx1",
                ),
                value=ToolCallNode(
                    tool_name="func1",
                    arguments=[],
                    named_arguments={},
                    line_number=1,
                    column=10,
                    node_id="n1",
                ),
                line_number=1,
                column=1,
                node_id="ia1",
            ),
            IndexedAssignNode(
                target=IndexedAccessNode(
                    object_node=VariableNode(
                        variable_name="arr", line_number=2, column=1, node_id="v2"
                    ),
                    index_node=LiteralNode(
                        value=1, line_number=2, column=5, node_id="l2"
                    ),
                    line_number=2,
                    column=1,
                    node_id="idx2",
                ),
                value=ToolCallNode(
                    tool_name="func2",
                    arguments=[],
                    named_arguments={},
                    line_number=2,
                    column=10,
                    node_id="n2",
                ),
                line_number=2,
                column=1,
                node_id="ia2",
            ),
        ]

        dependencies = self.analyzer.analyze_node_dependencies(nodes)
        groups = self.analyzer.find_parallel_groups(dependencies)

        # Different indices should allow parallel execution
        assert len(groups) == 1
        assert set(groups[0]) == {0, 1}

    def test_control_flow_blocks_parallelization(self):
        """Test that control flow creates execution barriers.

        Control flow nodes should not be parallelized with other nodes.
        """
        nodes = [
            AssignNode(
                variable_name="a",
                expression=ToolCallNode(
                    tool_name="func1",
                    arguments=[],
                    named_arguments={},
                    line_number=1,
                    column=1,
                    node_id="n1",
                ),
                line_number=1,
                column=1,
                node_id="a1",
            ),
            ConditionalNode(
                condition=VariableNode(
                    variable_name="a", line_number=2, column=4, node_id="v1"
                ),
                if_body=[],
                elif_conditions=[],
                elif_bodies=[],
                else_body=None,
                line_number=2,
                column=1,
                node_id="c1",
            ),
            AssignNode(
                variable_name="b",
                expression=ToolCallNode(
                    tool_name="func2",
                    arguments=[],
                    named_arguments={},
                    line_number=3,
                    column=1,
                    node_id="n2",
                ),
                line_number=3,
                column=1,
                node_id="a2",
            ),
        ]

        dependencies = self.analyzer.analyze_node_dependencies(nodes)
        groups = self.analyzer.find_parallel_groups(dependencies)

        # Control flow should prevent parallelization
        assert len(groups) == 3
        assert groups[0] == [0]
        assert groups[1] == [1]
        assert groups[2] == [2]

    # Additional helper method tests

    def test_collect_reads_from_variable_node(self):
        """Test that _collect_reads correctly identifies variable reads."""
        node = VariableNode(
            variable_name="test_var", line_number=1, column=1, node_id="v1"
        )
        reads = self.analyzer._collect_reads(node)
        assert "test_var" in reads

    def test_collect_reads_from_tool_call(self):
        """Test that _collect_reads finds variables in tool arguments."""
        node = ToolCallNode(
            tool_name="process",
            arguments=[],
            named_arguments={
                "input1": VariableNode(
                    variable_name="var1", line_number=1, column=10, node_id="v1"
                ),
                "input2": VariableNode(
                    variable_name="var2", line_number=1, column=20, node_id="v2"
                ),
                "literal": LiteralNode(
                    value=42, line_number=1, column=30, node_id="l1"
                ),
            },
            line_number=1,
            column=1,
            node_id="n1",
        )
        reads = self.analyzer._collect_reads(node)
        assert "var1" in reads
        assert "var2" in reads

    def test_collect_writes_from_assign(self):
        """Test that _collect_writes identifies variable writes."""
        node = AssignNode(
            variable_name="output",
            expression=LiteralNode(
                value="test", line_number=1, column=10, node_id="l1"
            ),
            line_number=1,
            column=1,
            node_id="a1",
        )
        writes = self.analyzer._collect_writes(node)
        assert "output" in writes

    def test_is_control_flow_node(self):
        """Test control flow node identification."""
        conditional = ConditionalNode(
            condition=LiteralNode(value=True, line_number=1, column=4, node_id="l1"),
            if_body=[],
            elif_conditions=[],
            elif_bodies=[],
            else_body=None,
            line_number=1,
            column=1,
            node_id="c1",
        )
        while_loop = WhileLoopNode(
            condition=LiteralNode(value=True, line_number=2, column=7, node_id="l2"),
            body=[],
            line_number=2,
            column=1,
            node_id="w1",
        )
        regular = AssignNode(
            variable_name="a",
            expression=LiteralNode(value=1, line_number=3, column=5, node_id="l3"),
            line_number=3,
            column=1,
            node_id="a1",
        )

        assert self.analyzer._is_control_flow_node(conditional) is True
        assert self.analyzer._is_control_flow_node(while_loop) is True
        assert self.analyzer._is_control_flow_node(regular) is False

    def test_has_side_effects(self):
        """Test side effect detection for nodes."""
        tool_call = ToolCallNode(
            tool_name="api_call",
            arguments=[],
            named_arguments={},
            line_number=1,
            column=1,
            node_id="n1",
        )
        assignment = AssignNode(
            variable_name="a",
            expression=LiteralNode(value=1, line_number=2, column=5, node_id="l1"),
            line_number=2,
            column=1,
            node_id="a1",
        )

        assert self.analyzer._has_side_effects(tool_call) is True
        assert self.analyzer._has_side_effects(assignment) is False

    def test_can_parallelize_nodes(self):
        """Test the can_parallelize_nodes helper method."""
        # Create simple dependency graph
        dependencies = {
            0: set(),  # No dependencies
            1: {0},  # Depends on 0
            2: set(),  # No dependencies
            3: {1, 2},  # Depends on 1 and 2
        }

        # Nodes 0 and 2 have no mutual dependencies
        assert self.analyzer.can_parallelize_nodes(0, 2, dependencies) is True

        # Node 1 depends on 0
        assert self.analyzer.can_parallelize_nodes(0, 1, dependencies) is False

        # Node 3 depends on 1 and 2
        assert self.analyzer.can_parallelize_nodes(1, 3, dependencies) is False
        assert self.analyzer.can_parallelize_nodes(2, 3, dependencies) is False

        # Nodes 1 and 2 can run in parallel (no mutual deps)
        assert self.analyzer.can_parallelize_nodes(1, 2, dependencies) is True
