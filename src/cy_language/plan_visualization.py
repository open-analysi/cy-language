"""
Task Execution Plan visualization utilities.

This module provides tools for visualizing, debugging, and inspecting
execution plans.
"""

from typing import Any

from .execution_plan import (
    ArithmeticNode,
    AssignNode,
    BooleanOpNode,
    BreakNode,
    ComparisonNode,
    ConditionalNode,
    ContinueNode,
    DictNode,
    ExecutionNode,
    ExecutionPlan,
    FieldAccessNode,
    FieldAssignNode,
    IndexedAccessNode,
    IndexedAssignNode,
    InterpolationNode,
    ListComprehensionNode,
    ListNode,
    LiteralNode,
    ReturnNode,
    ToolCallNode,
    TryCatchNode,
    UnaryOpNode,
    VariableNode,
    WhileLoopNode,
)

# ---------------------------------------------------------------------------
# Data-driven visual styling for GraphViz node rendering.
#
# _NODE_VISUAL_STYLES: type → (type_name, shape, fillcolor)
#   Static properties that don't depend on the node instance.
#
# _NODE_LABEL_BUILDERS: type → callable(node) → raw_label_str
#   Computes the dynamic label text from the node instance.
#   Types not in this dict fall back to ``node.node_type.value``.
# ---------------------------------------------------------------------------

_NODE_VISUAL_STYLES: dict[type, tuple[str, str, str]] = {
    AssignNode: ("assign", "ellipse", "lightblue"),
    LiteralNode: ("literal", "box", "lightgreen"),
    VariableNode: ("variable", "diamond", "lightyellow"),
    ToolCallNode: ("tool_call", "hexagon", "orange"),
    InterpolationNode: ("interpolation", "note", "lightcyan"),
    FieldAccessNode: ("field_access", "triangle", "pink"),
    ListNode: ("list", "folder", "lightcoral"),
    DictNode: ("dict", "house", "lightgray"),
    IndexedAccessNode: ("indexed_access", "trapezium", "lightsteelblue"),
    ArithmeticNode: ("arithmetic", "oval", "lightgreen"),
    ComparisonNode: ("comparison", "diamond", "lightblue"),
    BooleanOpNode: ("boolean_op", "hexagon", "lavender"),
    UnaryOpNode: ("unary_op", "invtriangle", "lightyellow"),
    ConditionalNode: ("conditional", "diamond", "lightcyan"),
    WhileLoopNode: ("while_loop", "doublecircle", "lavender"),
    ReturnNode: ("return", "Msquare", "mistyrose"),
    BreakNode: ("break", "Msquare", "lightsalmon"),
    ContinueNode: ("continue", "Msquare", "lightsalmon"),
    ListComprehensionNode: ("list_comprehension", "folder", "palegreen"),
    TryCatchNode: ("try_catch", "octagon", "lightyellow"),
    FieldAssignNode: ("field_assign", "ellipse", "lightblue"),
    IndexedAssignNode: ("indexed_assign", "ellipse", "lightblue"),
}
_DEFAULT_STYLE: tuple[str, str, str] = ("unknown", "box", "white")


def _label_assign(node: AssignNode) -> str:
    return f"${node.variable_name}"


def _label_literal(node: LiteralNode) -> str:
    return repr(node.value) if isinstance(node.value, str) else str(node.value)


def _label_variable(node: VariableNode) -> str:
    return f"${node.variable_name}"


def _label_tool_call(node: ToolCallNode) -> str:
    args_summary = f"({len(node.arguments)} args)" if node.arguments else "()"
    return f"{node.tool_name}{args_summary}"


def _label_interpolation(node: InterpolationNode) -> str:
    preview = node.template[:20] + "..." if len(node.template) > 20 else node.template
    return f'"{preview}"'


def _label_field_access(node: FieldAccessNode) -> str:
    return f".{node.field_name}"


def _label_list(node: ListNode) -> str:
    return f"[{len(node.elements)} items]"


def _label_dict(node: DictNode) -> str:
    return f"{{{len(node.pairs)} pairs}}"


def _label_indexed_access(_node: IndexedAccessNode) -> str:
    return "[index]"


def _label_arithmetic(node: ArithmeticNode) -> str:
    return node.operator


def _label_comparison(node: ComparisonNode) -> str:
    return node.operator


def _label_boolean_op(node: BooleanOpNode) -> str:
    return f"{node.operator} ({len(node.operands)} ops)"


def _label_unary_op(node: UnaryOpNode) -> str:
    return node.operator


def _label_conditional(node: ConditionalNode) -> str:
    elif_count = len(node.elif_conditions)
    has_else = node.else_body is not None
    else_text = ", else" if has_else else ""
    if elif_count > 0:
        return f"if+{elif_count}elif{else_text}"
    return f"if{else_text}"


def _label_while_loop(node: WhileLoopNode) -> str:
    return f"while ({len(node.body)} stmts)"


def _label_list_comprehension(node: ListComprehensionNode) -> str:
    has_filter = node.filter_expr is not None
    return f"[... for({node.iterator_var} in ...)]" + (" if(...)" if has_filter else "")


def _label_try_catch(node: TryCatchNode) -> str:
    catches = len(node.catch_clauses)
    has_finally = node.finally_body is not None
    parts = [f"try ({len(node.try_body)} stmts)"]
    parts.append(f"{catches} catch")
    if has_finally:
        parts.append("finally")
    return ", ".join(parts)


def _label_field_assign(node: FieldAssignNode) -> str:
    if isinstance(node.target, FieldAccessNode):
        return f".{node.target.field_name} ="
    return "field ="


def _label_indexed_assign(node: IndexedAssignNode) -> str:
    return "[...] ="


_NODE_LABEL_BUILDERS: dict[type, Any] = {
    AssignNode: _label_assign,
    LiteralNode: _label_literal,
    VariableNode: _label_variable,
    ToolCallNode: _label_tool_call,
    InterpolationNode: _label_interpolation,
    FieldAccessNode: _label_field_access,
    ListNode: _label_list,
    DictNode: _label_dict,
    IndexedAccessNode: _label_indexed_access,
    ArithmeticNode: _label_arithmetic,
    ComparisonNode: _label_comparison,
    BooleanOpNode: _label_boolean_op,
    UnaryOpNode: _label_unary_op,
    ConditionalNode: _label_conditional,
    WhileLoopNode: _label_while_loop,
    ListComprehensionNode: _label_list_comprehension,
    TryCatchNode: _label_try_catch,
    FieldAssignNode: _label_field_assign,
    IndexedAssignNode: _label_indexed_assign,
    # ReturnNode, BreakNode, ContinueNode omitted — the node_type.value
    # fallback produces identical labels ("return", "break", "continue").
}


class PlanVisualizer:
    """Visualizes execution plans in various formats."""

    def __init__(self) -> None:
        pass

    def pretty_print(self, plan: ExecutionPlan, show_metadata: bool = True) -> str:
        """Pretty print execution plan with indentation and colors."""
        lines = []
        lines.append(f"Execution Plan (v{plan.version})")
        if plan.source_file:
            lines.append(f"Source: {plan.source_file}")
        lines.append(f"Nodes: {len(plan.nodes)}")

        for i, node in enumerate(plan.nodes):
            lines.append(f"  {i + 1}. {node.node_type.value} (line {node.line_number})")

        return "\n".join(lines)

    def to_graphviz(self, plan: ExecutionPlan) -> str:
        """Export execution plan to GraphViz DOT format showing actual program logic."""
        dot_lines = [
            "digraph ExecutionPlan {",
            "  rankdir=LR;",  # Left to right for better data flow visualization
            '  node [fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
            "",
            "  // Node definitions with proper styling",
        ]

        # Keep track of all nodes we've seen to avoid duplicates
        all_nodes: set[str] = set()
        connections: list[str] = []

        # Build a map of variable assignments for dependency tracking
        variable_assignments: dict[
            str, list[str]
        ] = {}  # variable_name -> list of assign_node_ids

        # First pass: collect all assignments
        def collect_assignments(node: ExecutionNode) -> None:
            """Recursively collect all assignment nodes."""
            if isinstance(node, AssignNode):
                if node.variable_name not in variable_assignments:
                    variable_assignments[node.variable_name] = []
                variable_assignments[node.variable_name].append(node.node_id)

            # Recursively check nested nodes
            if isinstance(node, ConditionalNode):
                for stmt in node.if_body:
                    collect_assignments(stmt)
                for elif_body in node.elif_bodies:
                    for stmt in elif_body:
                        collect_assignments(stmt)
                if node.else_body:
                    for stmt in node.else_body:
                        collect_assignments(stmt)
            elif isinstance(node, WhileLoopNode):
                for stmt in node.body:
                    collect_assignments(stmt)
            elif isinstance(node, TryCatchNode):
                for stmt in node.try_body:
                    collect_assignments(stmt)
                for clause in node.catch_clauses:
                    for stmt in clause.body:
                        collect_assignments(stmt)
                if node.finally_body:
                    for stmt in node.finally_body:
                        collect_assignments(stmt)

        for plan_node in plan.nodes:
            collect_assignments(plan_node)

        # Process each top-level node in the execution plan
        for plan_node in plan.nodes:
            self._add_node_and_dependencies(
                plan_node, all_nodes, dot_lines, connections, variable_assignments
            )

        # Add connection definitions
        if connections:
            dot_lines.append("")
            dot_lines.append("  // Data flow connections")
            dot_lines.extend(connections)

        dot_lines.append("}")
        return "\n".join(dot_lines)

    def _add_node_and_dependencies(
        self,
        node: ExecutionNode,
        all_nodes: set[str],
        dot_lines: list[str],
        connections: list[str],
        variable_assignments: dict[str, list[str]],
    ) -> None:
        """Recursively add a node and its dependencies to the graph."""
        if node.node_id in all_nodes:
            return

        all_nodes.add(node.node_id)

        # Generate the visual representation for this node
        label, shape, style, fillcolor = self._get_node_visual_info(node)
        dot_lines.append(
            f'  {node.node_id} [label="{label}", shape={shape}, style={style}, fillcolor={fillcolor}];'
        )

        # Handle different node types and their dependencies
        if isinstance(node, AssignNode):
            # Add the expression node
            self._add_node_and_dependencies(
                node.expression, all_nodes, dot_lines, connections, variable_assignments
            )
            # Connect expression to the assignment
            connections.append(
                f'  {node.expression.node_id} -> {node.node_id} [label="assigns to"];'
            )

        elif isinstance(node, VariableNode):
            # Connect variable reference to all its possible assignments
            if node.variable_name in variable_assignments:
                for assign_node_id in variable_assignments[node.variable_name]:
                    connections.append(
                        f'  {assign_node_id} -> {node.node_id} [label="provides value", style="dashed"];'
                    )

        elif isinstance(node, ToolCallNode):
            # Add argument nodes
            for i, arg in enumerate(node.arguments):
                self._add_node_and_dependencies(
                    arg, all_nodes, dot_lines, connections, variable_assignments
                )
                connections.append(
                    f'  {arg.node_id} -> {node.node_id} [label="arg{i + 1}"];'
                )

            # Add named argument nodes
            for name, arg in node.named_arguments.items():
                self._add_node_and_dependencies(
                    arg, all_nodes, dot_lines, connections, variable_assignments
                )
                connections.append(
                    f'  {arg.node_id} -> {node.node_id} [label="{name}="];'
                )

        elif isinstance(node, InterpolationNode):
            # Add variable nodes used in interpolation
            for var in node.variables:
                self._add_node_and_dependencies(
                    var, all_nodes, dot_lines, connections, variable_assignments
                )
                connections.append(
                    f'  {var.node_id} -> {node.node_id} [label="interpolate"];'
                )

        elif isinstance(node, FieldAccessNode):
            # Add the object being accessed
            self._add_node_and_dependencies(
                node.object_node,
                all_nodes,
                dot_lines,
                connections,
                variable_assignments,
            )
            connections.append(
                f'  {node.object_node.node_id} -> {node.node_id} [label="access"];'
            )

        elif isinstance(node, ListNode):
            # Add element nodes
            for i, elem in enumerate(node.elements):
                self._add_node_and_dependencies(
                    elem, all_nodes, dot_lines, connections, variable_assignments
                )
                connections.append(
                    f'  {elem.node_id} -> {node.node_id} [label="elem{i}"];'
                )

        elif isinstance(node, DictNode):
            # Add key-value pair nodes
            for i, (key, value) in enumerate(node.pairs):
                self._add_node_and_dependencies(
                    key, all_nodes, dot_lines, connections, variable_assignments
                )
                self._add_node_and_dependencies(
                    value, all_nodes, dot_lines, connections, variable_assignments
                )
                connections.append(
                    f'  {key.node_id} -> {node.node_id} [label="key{i}"];'
                )
                connections.append(
                    f'  {value.node_id} -> {node.node_id} [label="val{i}"];'
                )

        elif isinstance(node, IndexedAccessNode):
            # Add the object and index being accessed
            self._add_node_and_dependencies(
                node.object_node,
                all_nodes,
                dot_lines,
                connections,
                variable_assignments,
            )
            self._add_node_and_dependencies(
                node.index_node, all_nodes, dot_lines, connections, variable_assignments
            )
            connections.append(
                f'  {node.object_node.node_id} -> {node.node_id} [label="object"];'
            )
            connections.append(
                f'  {node.index_node.node_id} -> {node.node_id} [label="index"];'
            )

        elif isinstance(node, ArithmeticNode):
            # Add left and right operands for arithmetic operations
            self._add_node_and_dependencies(
                node.left, all_nodes, dot_lines, connections, variable_assignments
            )
            self._add_node_and_dependencies(
                node.right, all_nodes, dot_lines, connections, variable_assignments
            )
            connections.append(
                f'  {node.left.node_id} -> {node.node_id} [label="left"];'
            )
            connections.append(
                f'  {node.right.node_id} -> {node.node_id} [label="right"];'
            )

        elif isinstance(node, ComparisonNode):
            # Add left and right operands for comparison operations
            self._add_node_and_dependencies(
                node.left, all_nodes, dot_lines, connections, variable_assignments
            )
            self._add_node_and_dependencies(
                node.right, all_nodes, dot_lines, connections, variable_assignments
            )
            connections.append(
                f'  {node.left.node_id} -> {node.node_id} [label="left"];'
            )
            connections.append(
                f'  {node.right.node_id} -> {node.node_id} [label="right"];'
            )

        elif isinstance(node, BooleanOpNode):
            # Add all operands for boolean operations
            for i, operand in enumerate(node.operands):
                self._add_node_and_dependencies(
                    operand, all_nodes, dot_lines, connections, variable_assignments
                )
                connections.append(
                    f'  {operand.node_id} -> {node.node_id} [label="op{i + 1}"];'
                )

        elif isinstance(node, UnaryOpNode):
            # Add the single operand for unary operations
            self._add_node_and_dependencies(
                node.operand, all_nodes, dot_lines, connections, variable_assignments
            )
            connections.append(
                f'  {node.operand.node_id} -> {node.node_id} [label="operand"];'
            )

        elif isinstance(node, ConditionalNode):
            # Add condition node
            self._add_node_and_dependencies(
                node.condition, all_nodes, dot_lines, connections, variable_assignments
            )
            connections.append(
                f'  {node.condition.node_id} -> {node.node_id} [label="condition", color="blue"];'
            )

            # Add if body nodes
            for i, stmt in enumerate(node.if_body):
                self._add_node_and_dependencies(
                    stmt, all_nodes, dot_lines, connections, variable_assignments
                )
                connections.append(
                    f'  {node.node_id} -> {stmt.node_id} [label="if[{i}]", color="green"];'
                )

            # Add elif conditions and bodies
            for elif_idx, elif_condition in enumerate(node.elif_conditions):
                self._add_node_and_dependencies(
                    elif_condition,
                    all_nodes,
                    dot_lines,
                    connections,
                    variable_assignments,
                )
                connections.append(
                    f'  {elif_condition.node_id} -> {node.node_id} [label="elif_cond[{elif_idx}]", color="blue"];'
                )

                elif_body = node.elif_bodies[elif_idx]
                for i, stmt in enumerate(elif_body):
                    self._add_node_and_dependencies(
                        stmt, all_nodes, dot_lines, connections, variable_assignments
                    )
                    connections.append(
                        f'  {node.node_id} -> {stmt.node_id} [label="elif[{elif_idx}][{i}]", color="orange"];'
                    )

            # Add else body nodes
            if node.else_body:
                for i, stmt in enumerate(node.else_body):
                    self._add_node_and_dependencies(
                        stmt, all_nodes, dot_lines, connections, variable_assignments
                    )
                    connections.append(
                        f'  {node.node_id} -> {stmt.node_id} [label="else[{i}]", color="red"];'
                    )

        elif isinstance(node, WhileLoopNode):
            # Add condition node
            self._add_node_and_dependencies(
                node.condition, all_nodes, dot_lines, connections, variable_assignments
            )
            connections.append(
                f'  {node.condition.node_id} -> {node.node_id} [label="condition", color="blue"];'
            )

            # Add body nodes
            for i, stmt in enumerate(node.body):
                self._add_node_and_dependencies(
                    stmt, all_nodes, dot_lines, connections, variable_assignments
                )
                connections.append(
                    f'  {node.node_id} -> {stmt.node_id} [label="body[{i}]", color="purple"];'
                )
                # Add loop-back edge to show iteration
                connections.append(
                    f'  {stmt.node_id} -> {node.condition.node_id} [label="loop", style="dashed", color="purple"];'
                )

        elif isinstance(node, ListComprehensionNode):
            # Add iterable expression
            self._add_node_and_dependencies(
                node.iterable_expr,
                all_nodes,
                dot_lines,
                connections,
                variable_assignments,
            )
            connections.append(
                f'  {node.iterable_expr.node_id} -> {node.node_id} [label="iterable"];'
            )
            # Add element expression
            self._add_node_and_dependencies(
                node.element_expr,
                all_nodes,
                dot_lines,
                connections,
                variable_assignments,
            )
            connections.append(
                f'  {node.element_expr.node_id} -> {node.node_id} [label="element"];'
            )
            # Add filter expression if present
            if node.filter_expr is not None:
                self._add_node_and_dependencies(
                    node.filter_expr,
                    all_nodes,
                    dot_lines,
                    connections,
                    variable_assignments,
                )
                connections.append(
                    f'  {node.filter_expr.node_id} -> {node.node_id} [label="filter", style="dashed"];'
                )

        elif isinstance(node, TryCatchNode):
            # Add try body
            for i, stmt in enumerate(node.try_body):
                self._add_node_and_dependencies(
                    stmt, all_nodes, dot_lines, connections, variable_assignments
                )
                connections.append(
                    f'  {node.node_id} -> {stmt.node_id} [label="try[{i}]", color="green"];'
                )
            # Add catch clauses
            for _ci, clause in enumerate(node.catch_clauses):
                for i, stmt in enumerate(clause.body):
                    self._add_node_and_dependencies(
                        stmt, all_nodes, dot_lines, connections, variable_assignments
                    )
                    connections.append(
                        f'  {node.node_id} -> {stmt.node_id} [label="catch({clause.exception_var})[{i}]", color="red"];'
                    )
            # Add finally body
            if node.finally_body:
                for i, stmt in enumerate(node.finally_body):
                    self._add_node_and_dependencies(
                        stmt, all_nodes, dot_lines, connections, variable_assignments
                    )
                    connections.append(
                        f'  {node.node_id} -> {stmt.node_id} [label="finally[{i}]", color="blue"];'
                    )

        elif isinstance(node, FieldAssignNode):
            # Add target (field access) and value
            self._add_node_and_dependencies(
                node.target, all_nodes, dot_lines, connections, variable_assignments
            )
            self._add_node_and_dependencies(
                node.value, all_nodes, dot_lines, connections, variable_assignments
            )
            connections.append(
                f'  {node.value.node_id} -> {node.node_id} [label="value"];'
            )
            connections.append(
                f'  {node.node_id} -> {node.target.node_id} [label="target"];'
            )

        elif isinstance(node, IndexedAssignNode):
            # Add target (indexed access) and value
            self._add_node_and_dependencies(
                node.target, all_nodes, dot_lines, connections, variable_assignments
            )
            self._add_node_and_dependencies(
                node.value, all_nodes, dot_lines, connections, variable_assignments
            )
            connections.append(
                f'  {node.value.node_id} -> {node.node_id} [label="value"];'
            )
            connections.append(
                f'  {node.node_id} -> {node.target.node_id} [label="target"];'
            )

        elif isinstance(node, ReturnNode):
            # Add the expression being returned
            self._add_node_and_dependencies(
                node.expression, all_nodes, dot_lines, connections, variable_assignments
            )
            connections.append(
                f'  {node.expression.node_id} -> {node.node_id} [label="returns", color="darkred"];'
            )

    def _escape_graphviz_label(self, text: str) -> str:
        """Escape special characters for GraphViz labels."""
        return (
            text.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("$", "\\$")
            .replace("|", "\\|")
            .replace("<", "\\<")
            .replace(">", "\\>")
            .replace("{", "\\{")
            .replace("}", "\\}")
        )

    def _get_node_visual_info(self, node: ExecutionNode) -> tuple[str, str, str, str]:
        """Get (label, shape, style, fillcolor) for a node.

        Uses ``_NODE_VISUAL_STYLES`` for static styling and
        ``_NODE_LABEL_BUILDERS`` for dynamic label computation.
        """
        node_type = type(node)
        label_builder = _NODE_LABEL_BUILDERS.get(node_type)
        if label_builder is not None:
            raw_label = label_builder(node)
        else:
            raw_label = node.node_type.value

        escaped_label = self._escape_graphviz_label(raw_label)
        style_info = _NODE_VISUAL_STYLES.get(node_type, _DEFAULT_STYLE)
        type_name = style_info[0]
        return (
            f"{escaped_label}\\n{type_name}",
            style_info[1],
            "filled",
            style_info[2],
        )

    def get_statistics(self, plan: ExecutionPlan) -> dict[str, Any]:
        """Get statistics about the execution plan."""
        node_types: dict[str, int] = {}
        for node in plan.nodes:
            node_type = node.node_type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1

        return {
            "total_nodes": len(plan.nodes),
            "node_types": node_types,
            "version": plan.version,
            "source_file": plan.source_file,
        }


class PlanDebugger:
    """Debugging utilities for execution plans."""

    def __init__(self) -> None:
        self.breakpoints: set[str] = set()

    def add_breakpoint(self, node_id: str) -> None:
        """Add a breakpoint at a specific node."""
        self.breakpoints.add(node_id)

    def remove_breakpoint(self, node_id: str) -> None:
        """Remove a breakpoint."""
        self.breakpoints.discard(node_id)

    def inspect_node(self, node: ExecutionNode) -> dict[str, Any]:
        """Inspect a specific node."""
        return {
            "node_type": node.node_type.value,
            "node_id": node.node_id,
            "line_number": node.line_number,
            "column": node.column,
        }


def format_plan_for_cli(plan: ExecutionPlan, format_type: str = "pretty") -> str:
    """Format execution plan for CLI output."""
    visualizer = PlanVisualizer()

    if format_type == "json":
        return plan.to_json()
    if format_type == "graphviz":
        return visualizer.to_graphviz(plan)
    # pretty
    return visualizer.pretty_print(plan)
