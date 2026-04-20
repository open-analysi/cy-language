"""
Regression tests for control flow node ID uniqueness.

These tests prevent the regression where nested control flow structures
would get duplicate node IDs (e.g., both outer and inner while loops
having the same ID like "while_1_1").
"""

from src.cy_language.compiler import compile_cy_program
from src.cy_language.execution_plan import ConditionalNode, ReturnNode, WhileLoopNode
from src.cy_language.parser import Parser


class TestControlFlowNodeIdUniqueness:
    """Test that all control flow nodes get unique IDs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = Parser()

    def _get_all_node_ids_recursive(self, node):
        """Recursively collect all node IDs from an execution node and its children."""
        node_ids = [node.node_id]

        # Check nested nodes based on type
        if hasattr(node, "body") and node.body:
            for child in node.body:
                node_ids.extend(self._get_all_node_ids_recursive(child))

        if hasattr(node, "if_body") and node.if_body:
            for child in node.if_body:
                node_ids.extend(self._get_all_node_ids_recursive(child))

        if hasattr(node, "elif_bodies") and node.elif_bodies:
            for elif_body in node.elif_bodies:
                for child in elif_body:
                    node_ids.extend(self._get_all_node_ids_recursive(child))

        if hasattr(node, "else_body") and node.else_body:
            for child in node.else_body:
                node_ids.extend(self._get_all_node_ids_recursive(child))

        if hasattr(node, "condition"):
            node_ids.extend(self._get_all_node_ids_recursive(node.condition))

        if hasattr(node, "expression") and node.expression:
            node_ids.extend(self._get_all_node_ids_recursive(node.expression))

        # Handle other nested node types
        if hasattr(node, "left"):
            node_ids.extend(self._get_all_node_ids_recursive(node.left))
        if hasattr(node, "right"):
            node_ids.extend(self._get_all_node_ids_recursive(node.right))

        return node_ids

    def _find_node_types(self, node):
        """Recursively find control flow node types."""
        types = []
        if isinstance(node, WhileLoopNode):
            types.append("while")
        elif isinstance(node, ConditionalNode):
            types.append("conditional")
        elif isinstance(node, ReturnNode):
            types.append("return")

        for attr in ("body", "if_body", "else_body"):
            children = getattr(node, attr, None)
            if children:
                for child in children:
                    types.extend(self._find_node_types(child))
        if hasattr(node, "elif_bodies") and node.elif_bodies:
            for elif_body in node.elif_bodies:
                for child in elif_body:
                    types.extend(self._find_node_types(child))
        return types

    def test_nested_while_loops_unique_ids(self):
        """Test that nested while loops get unique node IDs."""
        program = """
total = 0
outer = 1

while (outer <= 3) {
    inner = 1
    while (inner <= 2) {
        total = total + (outer * inner)
        inner = inner + 1
    }
    outer = outer + 1
}

output = "Total: ${total}"
return output
"""

        ast_tree = self.parser.parse_only(program)
        plan = compile_cy_program(ast_tree, source_file="<test>", validate_output=False)

        # Collect all node IDs from the execution plan
        all_node_ids = []
        for node in plan.nodes:
            all_node_ids.extend(self._get_all_node_ids_recursive(node))

        # Check that all IDs are unique
        unique_ids = set(all_node_ids)
        assert len(all_node_ids) == len(unique_ids), (
            f"Found duplicate node IDs: {[id for id in all_node_ids if all_node_ids.count(id) > 1]}"
        )

        # Specifically check that we have two different while loop IDs
        while_nodes = [node for node in plan.nodes if isinstance(node, WhileLoopNode)]
        assert len(while_nodes) >= 1, "Should have at least one while loop node"

        # Find the nested while loop in the outer while loop's body
        outer_while = while_nodes[0]
        nested_while_found = False
        for stmt in outer_while.body:
            if isinstance(stmt, WhileLoopNode):
                nested_while_found = True
                assert stmt.node_id != outer_while.node_id, (
                    f"Nested while loop has same ID as outer: {stmt.node_id}"
                )
                break

        assert nested_while_found, "Should have found a nested while loop"

    def test_nested_conditionals_unique_ids(self):
        """Test that nested if statements get unique node IDs."""
        program = """
score = 85
attendance = 90

if (score > 80) {
    if (attendance > 85) {
        grade = "A"
    } else {
        grade = "B"
    }
} else {
    grade = "C"
}

output = "Grade: ${grade}"
return output
"""

        ast_tree = self.parser.parse_only(program)
        plan = compile_cy_program(ast_tree, source_file="<test>", validate_output=False)

        # Collect all node IDs from the execution plan
        all_node_ids = []
        for node in plan.nodes:
            all_node_ids.extend(self._get_all_node_ids_recursive(node))

        # Check that all IDs are unique
        unique_ids = set(all_node_ids)
        assert len(all_node_ids) == len(unique_ids), (
            f"Found duplicate node IDs: {[id for id in all_node_ids if all_node_ids.count(id) > 1]}"
        )

    def test_mixed_nested_control_flow_unique_ids(self):
        """Test that mixed nested control flow (while + if) gets unique node IDs."""
        program = """
counter = 1
total = 0

while (counter <= 5) {
    if (counter % 2 == 0) {
        total = total + counter
        if (total > 10) {
            return "Sum exceeded: ${sum}"
        }
    }
    counter = counter + 1
}

output = "Final sum: ${sum}"
"""

        ast_tree = self.parser.parse_only(program)
        plan = compile_cy_program(ast_tree, source_file="<test>", validate_output=False)

        # Collect all node IDs from the execution plan
        all_node_ids = []
        for node in plan.nodes:
            all_node_ids.extend(self._get_all_node_ids_recursive(node))

        # Check that all IDs are unique
        unique_ids = set(all_node_ids)
        assert len(all_node_ids) == len(unique_ids), (
            f"Found duplicate node IDs: {[id for id in all_node_ids if all_node_ids.count(id) > 1]}"
        )

        all_types = []
        for node in plan.nodes:
            all_types.extend(self._find_node_types(node))

        assert "while" in all_types, "Should have while loop node"
        assert "conditional" in all_types, "Should have conditional node"
        assert "return" in all_types, "Should have return node"

    def test_deeply_nested_while_loops_unique_ids(self):
        """Test that deeply nested while loops (3 levels) get unique node IDs."""
        program = """
total = 0
i = 1

while (i <= 2) {
    j = 1
    while (j <= 2) {
        k = 1
        while (k <= 2) {
            total = total + 1
            k = k + 1
        }
        j = j + 1
    }
    i = i + 1
}

output = "Total: ${total}"
return output
"""

        ast_tree = self.parser.parse_only(program)
        plan = compile_cy_program(ast_tree, source_file="<test>", validate_output=False)

        # Collect all node IDs from the execution plan
        all_node_ids = []
        for node in plan.nodes:
            all_node_ids.extend(self._get_all_node_ids_recursive(node))

        # Check that all IDs are unique
        unique_ids = set(all_node_ids)
        assert len(all_node_ids) == len(unique_ids), (
            f"Found duplicate node IDs: {[id for id in all_node_ids if all_node_ids.count(id) > 1]}"
        )

        # Count while loop nodes (should find 3 levels)
        while_loop_ids = []

        def collect_while_ids(node):
            if isinstance(node, WhileLoopNode):
                while_loop_ids.append(node.node_id)
                for stmt in node.body:
                    collect_while_ids(stmt)
            elif hasattr(node, "body") and node.body:
                for stmt in node.body:
                    collect_while_ids(stmt)

        for node in plan.nodes:
            collect_while_ids(node)

        # Should have 3 while loops with unique IDs
        assert len(while_loop_ids) >= 3, (
            f"Expected at least 3 while loops, found {len(while_loop_ids)}"
        )
        assert len(set(while_loop_ids)) == len(while_loop_ids), (
            f"While loop IDs not unique: {while_loop_ids}"
        )

    def test_node_id_format_consistency(self):
        """Test that all control flow nodes use the proper node_X format."""
        program = """
x = 5

if (x > 0) {
    while (x > 1) {
        x = x - 1
        if (x == 3) {
            return "Found three!"
        }
    }
}

output = "Done: ${x}"
"""

        ast_tree = self.parser.parse_only(program)
        plan = compile_cy_program(ast_tree, source_file="<test>", validate_output=False)

        # Collect all node IDs from the execution plan
        all_node_ids = []
        for node in plan.nodes:
            all_node_ids.extend(self._get_all_node_ids_recursive(node))

        # Check that all control flow nodes use node_X format (not the old line_column format)
        control_flow_ids = []

        def collect_control_flow_ids(node):
            if isinstance(node, (WhileLoopNode, ConditionalNode, ReturnNode)):
                control_flow_ids.append(node.node_id)

            # Recursively check nested nodes
            if hasattr(node, "body") and node.body:
                for child in node.body:
                    collect_control_flow_ids(child)
            if hasattr(node, "if_body") and node.if_body:
                for child in node.if_body:
                    collect_control_flow_ids(child)
            if hasattr(node, "else_body") and node.else_body:
                for child in node.else_body:
                    collect_control_flow_ids(child)

        for node in plan.nodes:
            collect_control_flow_ids(node)

        # All control flow node IDs should follow node_X format
        for node_id in control_flow_ids:
            assert node_id.startswith("node_"), (
                f"Control flow node ID should start with 'node_': {node_id}"
            )
            # Extract the number part and verify it's a valid integer
            number_part = node_id[5:]  # Remove "node_" prefix
            assert number_part.isdigit(), (
                f"Node ID should have numeric suffix: {node_id}"
            )
