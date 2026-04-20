"""
Integration tests for GraphViz visualization structure and connectivity.

These tests verify that the GraphViz visualization accurately represents
the execution plan structure and maintains proper connectivity properties.
"""

import re

from src.cy_language.compiler import compile_cy_program
from src.cy_language.parser import Parser
from src.cy_language.plan_visualization import format_plan_for_cli


class TestGraphVizStructure:
    """Test GraphViz visualization structure and connectivity."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = Parser()

    def _parse_dot_graph(self, dot_output):
        """Parse DOT output to extract nodes and connections."""
        lines = dot_output.split("\n")

        # Extract node definitions (lines with [label=...])
        node_pattern = r"^\s*(\w+)\s*\[label="
        nodes = []
        for line in lines:
            match = re.match(node_pattern, line)
            if match:
                nodes.append(match.group(1))

        # Extract connections (lines with ->)
        connection_pattern = r"^\s*(\w+)\s*->\s*(\w+)\s*\[.*\];?"
        connections = []
        for line in lines:
            match = re.match(connection_pattern, line)
            if match:
                connections.append((match.group(1), match.group(2)))

        return nodes, connections

    def _get_connected_nodes(self, connections):
        """Get all nodes that have at least one connection (incoming or outgoing)."""
        connected = set()
        for source, target in connections:
            connected.add(source)
            connected.add(target)
        return connected

    def _find_disconnected_nodes(self, nodes, connections):
        """Find nodes that have no connections (isolated nodes)."""
        connected = self._get_connected_nodes(connections)
        return [node for node in nodes if node not in connected]

    def test_simple_control_flow_connectivity(self):
        """Test that simple control flow creates a connected graph."""
        program = """
x = 10
y = 5

if (x > y) {
    result = "x is greater"
} else {
    result = "y is greater or equal"
}

output = "Result: ${result}"
return output
"""

        ast_tree = self.parser.parse_only(program)
        plan = compile_cy_program(ast_tree, source_file="<test>", validate_output=False)
        dot_output = format_plan_for_cli(plan, "graphviz")

        nodes, connections = self._parse_dot_graph(dot_output)

        # Should have nodes and connections
        assert len(nodes) > 0, "Graph should have nodes"
        assert len(connections) > 0, "Graph should have connections"

        # Find disconnected nodes
        disconnected = self._find_disconnected_nodes(nodes, connections)

        # For debugging if test fails
        if disconnected:
            print(f"Disconnected nodes: {disconnected}")
            print(f"All nodes: {nodes}")
            print(f"All connections: {connections}")

        # All nodes should be connected (no isolated nodes)
        assert len(disconnected) == 0, f"Found disconnected nodes: {disconnected}"

    def test_nested_while_loop_connectivity(self):
        """Test that nested while loops create proper connectivity."""
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
        dot_output = format_plan_for_cli(plan, "graphviz")

        nodes, connections = self._parse_dot_graph(dot_output)

        # Should have nodes and connections
        assert len(nodes) > 0, "Graph should have nodes"
        assert len(connections) > 0, "Graph should have connections"

        # Find while loop nodes in DOT output
        while_nodes = []
        for line in dot_output.split("\n"):
            if "while_loop" in line and "[label=" in line:
                match = re.match(r"^\s*(\w+)\s*\[", line)
                if match:
                    while_nodes.append(match.group(1))

        # Should have exactly 2 while loop nodes (outer and inner)
        assert len(while_nodes) == 2, (
            f"Expected 2 while loop nodes, found {len(while_nodes)}: {while_nodes}"
        )

        # Both while loop nodes should be distinct
        assert while_nodes[0] != while_nodes[1], (
            f"While loop nodes should have different IDs: {while_nodes}"
        )

        # Find disconnected nodes
        disconnected = self._find_disconnected_nodes(nodes, connections)

        # For debugging if test fails
        if disconnected:
            print(f"Disconnected nodes: {disconnected}")
            print(f"All nodes: {nodes}")
            print(f"While loop nodes: {while_nodes}")

        # All nodes should be connected
        assert len(disconnected) == 0, f"Found disconnected nodes: {disconnected}"

    def test_variable_assignment_connectivity(self):
        """Test that variable assignments properly connect to their usage."""
        program = """
x = 42
y = x + 10
output = "Value: ${y}"
return output
"""

        ast_tree = self.parser.parse_only(program)
        plan = compile_cy_program(ast_tree, source_file="<test>", validate_output=False)
        dot_output = format_plan_for_cli(plan, "graphviz")

        nodes, connections = self._parse_dot_graph(dot_output)

        # Find variable nodes in DOT output
        variable_nodes = []
        assignment_nodes = []

        for line in dot_output.split("\n"):
            if "variable" in line and "[label=" in line:
                match = re.match(r"^\s*(\w+)\s*\[", line)
                if match:
                    variable_nodes.append(match.group(1))
            elif "assign" in line and "[label=" in line:
                match = re.match(r"^\s*(\w+)\s*\[", line)
                if match:
                    assignment_nodes.append(match.group(1))

        # Should have both variable and assignment nodes
        assert len(variable_nodes) > 0, "Should have variable nodes"
        assert len(assignment_nodes) > 0, "Should have assignment nodes"

        # Check for "provides value" connections (variable usage)
        provides_value_connections = [
            (source, target)
            for source, target in connections
            if any(
                "provides value" in line
                for line in dot_output.split("\n")
                if f"{source} -> {target}" in line
            )
        ]

        # Should have variable-to-usage connections
        assert len(provides_value_connections) > 0, (
            "Should have 'provides value' connections from assignments to variable usage"
        )

        # All nodes should be connected
        disconnected = self._find_disconnected_nodes(nodes, connections)
        assert len(disconnected) == 0, f"Found disconnected nodes: {disconnected}"

    def test_complex_nested_structure_connectivity(self):
        """Test connectivity in complex nested structures with multiple control flow types."""
        program = """
counter = 1
total = 0

while (counter <= 5) {
    if (counter % 2 == 0) {
        total = total + counter
        if (total > 10) {
            return "Sum exceeded: ${total}"
        }
    } else {
        counter = counter + 1
    }
    counter = counter + 1
}

output = "Final sum: ${total}"
return output
"""

        ast_tree = self.parser.parse_only(program)
        plan = compile_cy_program(ast_tree, source_file="<test>", validate_output=False)
        dot_output = format_plan_for_cli(plan, "graphviz")

        nodes, connections = self._parse_dot_graph(dot_output)

        # Should have a substantial number of nodes for this complex structure
        assert len(nodes) >= 10, (
            f"Complex structure should have many nodes, found {len(nodes)}"
        )
        assert len(connections) >= 15, (
            f"Complex structure should have many connections, found {len(connections)}"
        )

        # Check for different control flow node types
        control_flow_types = []
        for line in dot_output.split("\n"):
            if (
                any(
                    cf_type in line
                    for cf_type in ["while_loop", "conditional", "return"]
                )
                and "[label=" in line
            ):
                if "while_loop" in line:
                    control_flow_types.append("while")
                elif "conditional" in line:
                    control_flow_types.append("conditional")
                elif "return" in line:
                    control_flow_types.append("return")

        # Should have all three types of control flow
        assert "while" in control_flow_types, "Should have while loop nodes"
        assert "conditional" in control_flow_types, "Should have conditional nodes"
        assert "return" in control_flow_types, "Should have return nodes"

        # All nodes should be connected
        disconnected = self._find_disconnected_nodes(nodes, connections)
        assert len(disconnected) == 0, f"Found disconnected nodes: {disconnected}"

    def test_graph_structure_consistency(self):
        """Test that graph structure is consistent and well-formed."""
        program = """
a = 1
b = 2

if (a < b) {
    while (a < 5) {
        a = a + 1
    }
}

output = "Result: ${a}"
return output
"""

        ast_tree = self.parser.parse_only(program)
        plan = compile_cy_program(ast_tree, source_file="<test>", validate_output=False)
        dot_output = format_plan_for_cli(plan, "graphviz")

        # Verify DOT format is valid
        assert dot_output.startswith("digraph ExecutionPlan {"), (
            "Should start with proper DOT header"
        )
        assert dot_output.endswith("}"), "Should end with closing brace"

        # Verify graph has proper structure
        lines = dot_output.split("\n")

        # Should have rankdir specification
        assert any("rankdir=" in line for line in lines), (
            "Should specify graph direction"
        )

        # Should have node and edge styling
        assert any("node [fontname=" in line for line in lines), (
            "Should have node styling"
        )
        assert any("edge [fontname=" in line for line in lines), (
            "Should have edge styling"
        )

        # Parse and verify connectivity
        nodes, connections = self._parse_dot_graph(dot_output)

        # Basic structure checks
        assert len(nodes) > 0, "Should have nodes"
        assert len(connections) > 0, "Should have connections"

        # All connection targets should be valid nodes
        all_connection_nodes = set()
        for source, target in connections:
            all_connection_nodes.add(source)
            all_connection_nodes.add(target)

        # All nodes referenced in connections should exist in node definitions
        undefined_nodes = all_connection_nodes - set(nodes)
        assert len(undefined_nodes) == 0, (
            f"Found connections to undefined nodes: {undefined_nodes}"
        )

        # All nodes should be connected
        disconnected = self._find_disconnected_nodes(nodes, connections)
        assert len(disconnected) == 0, f"Found disconnected nodes: {disconnected}"
