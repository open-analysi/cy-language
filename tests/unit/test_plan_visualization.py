"""
Unit tests for Task Execution Plan visualization utilities.
"""

import pytest

from src.cy_language.execution_plan import (
    ArithmeticNode,
    AssignNode,
    BooleanOpNode,
    ComparisonNode,
    ConditionalNode,
    DictNode,
    ExecutionPlan,
    FieldAccessNode,
    IndexedAccessNode,
    InterpolationNode,
    ListNode,
    LiteralNode,
    ReturnNode,
    ToolCallNode,
    UnaryOpNode,
    VariableNode,
    WhileLoopNode,
)
from src.cy_language.plan_visualization import (
    _DEFAULT_STYLE,
    _NODE_LABEL_BUILDERS,
    _NODE_VISUAL_STYLES,
    PlanDebugger,
    PlanVisualizer,
    format_plan_for_cli,
)


class TestPlanVisualizer:
    """Test the PlanVisualizer class."""

    def test_visualizer_creation(self):
        """Test PlanVisualizer can be created."""
        visualizer = PlanVisualizer()
        assert visualizer is not None

    def test_pretty_print_empty_plan(self):
        """Test pretty printing an empty plan."""
        visualizer = PlanVisualizer()
        plan = ExecutionPlan(version="2.0", source_file="test.cy")

        result = visualizer.pretty_print(plan)

        assert "Execution Plan (v2.0)" in result
        assert "Source: test.cy" in result
        assert "Nodes: 0" in result

    def test_pretty_print_plan_with_nodes(self):
        """Test pretty printing a plan with nodes."""
        visualizer = PlanVisualizer()
        plan = ExecutionPlan(version="2.0")

        # Add some nodes
        node1 = LiteralNode("hello", 1, 1, "node_1")
        node2 = LiteralNode("world", 2, 1, "node_2")
        plan.add_node(node1)
        plan.add_node(node2)

        result = visualizer.pretty_print(plan)

        assert "Nodes: 2" in result
        assert "literal (line 1)" in result
        assert "literal (line 2)" in result

    def test_pretty_print_without_metadata(self):
        """Test pretty printing without metadata."""
        visualizer = PlanVisualizer()
        plan = ExecutionPlan()

        result = visualizer.pretty_print(plan, show_metadata=False)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_to_graphviz_empty_plan(self):
        """Test GraphViz export for empty plan."""
        visualizer = PlanVisualizer()
        plan = ExecutionPlan()

        result = visualizer.to_graphviz(plan)

        assert "digraph ExecutionPlan {" in result
        assert "rankdir=LR;" in result  # Updated to match enhanced visualization
        assert (
            'node [fontname="Helvetica"];' in result
        )  # Updated to match enhanced styling
        assert "}" in result

    def test_to_graphviz_plan_with_nodes(self):
        """Test GraphViz export for plan with nodes."""
        visualizer = PlanVisualizer()
        plan = ExecutionPlan()

        # Add nodes
        node1 = LiteralNode("test", 1, 1, "node_1")
        node2 = LiteralNode("test2", 2, 1, "node_2")
        plan.add_node(node1)
        plan.add_node(node2)

        result = visualizer.to_graphviz(plan)

        # Updated to match enhanced visualization format
        assert (
            "node_1 [label=\"'test'\\nliteral\", shape=box, style=filled, fillcolor=lightgreen];"
            in result
        )
        assert (
            "node_2 [label=\"'test2'\\nliteral\", shape=box, style=filled, fillcolor=lightgreen];"
            in result
        )
        # Note: Enhanced visualization doesn't automatically connect independent literal nodes

    def test_get_statistics_empty_plan(self):
        """Test getting statistics for empty plan."""
        visualizer = PlanVisualizer()
        plan = ExecutionPlan(version="2.0", source_file="test.cy")

        stats = visualizer.get_statistics(plan)

        assert stats["total_nodes"] == 0
        assert stats["node_types"] == {}
        assert stats["version"] == "2.0"
        assert stats["source_file"] == "test.cy"

    def test_get_statistics_with_nodes(self):
        """Test getting statistics for plan with nodes."""
        visualizer = PlanVisualizer()
        plan = ExecutionPlan()

        # Add different types of nodes
        literal_node = LiteralNode("test", 1, 1, "node_1")
        expr_node = LiteralNode("value", 1, 10, "node_2")
        assign_node = AssignNode("var", expr_node, 1, 1, "node_3")
        tool_node = ToolCallNode("add", [], {}, 2, 1, "node_4")

        plan.add_node(literal_node)
        plan.add_node(assign_node)
        plan.add_node(tool_node)

        stats = visualizer.get_statistics(plan)

        assert stats["total_nodes"] == 3
        assert "literal" in stats["node_types"]
        assert "assign" in stats["node_types"]
        assert "tool_call" in stats["node_types"]
        assert (
            stats["node_types"]["literal"] >= 1
        )  # Could be more due to expr_node in assign


class TestPlanDebugger:
    """Test the PlanDebugger class."""

    def test_debugger_creation(self):
        """Test PlanDebugger can be created."""
        debugger = PlanDebugger()
        assert debugger is not None
        assert debugger.breakpoints == set()

    def test_add_breakpoint(self):
        """Test adding a breakpoint."""
        debugger = PlanDebugger()

        debugger.add_breakpoint("node_1")

        assert "node_1" in debugger.breakpoints

    def test_remove_breakpoint(self):
        """Test removing a breakpoint."""
        debugger = PlanDebugger()
        debugger.add_breakpoint("node_1")

        debugger.remove_breakpoint("node_1")

        assert "node_1" not in debugger.breakpoints

    def test_remove_nonexistent_breakpoint(self):
        """Test removing a non-existent breakpoint doesn't crash."""
        debugger = PlanDebugger()

        # Should not raise an exception
        debugger.remove_breakpoint("nonexistent")

        assert len(debugger.breakpoints) == 0

    def test_inspect_node(self):
        """Test inspecting a node."""
        debugger = PlanDebugger()
        node = LiteralNode("test", 5, 10, "node_123")

        info = debugger.inspect_node(node)

        assert info["node_type"] == "literal"
        assert info["node_id"] == "node_123"
        assert info["line_number"] == 5
        assert info["column"] == 10

    def test_inspect_different_node_types(self):
        """Test inspecting different types of nodes."""
        debugger = PlanDebugger()

        expr_node = LiteralNode("value", 1, 10, "node_1")
        assign_node = AssignNode("var", expr_node, 2, 5, "node_2")

        assign_info = debugger.inspect_node(assign_node)

        assert assign_info["node_type"] == "assign"
        assert assign_info["node_id"] == "node_2"
        assert assign_info["line_number"] == 2
        assert assign_info["column"] == 5


class TestFormatPlanForCli:
    """Test the format_plan_for_cli convenience function."""

    def test_format_plan_pretty(self):
        """Test formatting plan in pretty format."""
        plan = ExecutionPlan(version="2.0")
        node = LiteralNode("test", 1, 1, "node_1")
        plan.add_node(node)

        result = format_plan_for_cli(plan, "pretty")

        assert "Execution Plan (v2.0)" in result
        assert "literal (line 1)" in result

    def test_format_plan_json(self):
        """Test formatting plan in JSON format."""
        plan = ExecutionPlan(version="2.0")

        result = format_plan_for_cli(plan, "json")

        # Should return JSON string
        assert '"version": "2.0"' in result

    def test_format_plan_graphviz(self):
        """Test formatting plan in GraphViz format."""
        plan = ExecutionPlan()

        result = format_plan_for_cli(plan, "graphviz")

        assert "digraph ExecutionPlan {" in result
        assert "}" in result

    def test_format_plan_default(self):
        """Test formatting plan with default format."""
        plan = ExecutionPlan()

        result = format_plan_for_cli(plan)

        # Should default to pretty format
        assert "Execution Plan" in result

    def test_format_plan_unknown_format(self):
        """Test formatting plan with unknown format defaults to pretty."""
        plan = ExecutionPlan()

        result = format_plan_for_cli(plan, "unknown_format")

        # Should default to pretty format
        assert "Execution Plan" in result


class TestVisualizationIntegration:
    """Test integration scenarios for visualization."""

    def test_visualizer_with_complex_plan(self):
        """Test visualizer with a complex plan structure."""
        visualizer = PlanVisualizer()
        plan = ExecutionPlan(version="2.0", source_file="complex.cy")

        # Create a more complex plan
        literal1 = LiteralNode("hello", 1, 1, "node_1")
        literal2 = LiteralNode("world", 1, 15, "node_2")
        assign1 = AssignNode("greeting", literal1, 1, 1, "node_3")
        assign2 = AssignNode("target", literal2, 2, 1, "node_4")
        tool_call = ToolCallNode("concat", [literal1, literal2], {}, 3, 1, "node_5")

        for node in [literal1, literal2, assign1, assign2, tool_call]:
            plan.add_node(node)

        # Test all visualization methods work
        pretty = visualizer.pretty_print(plan)
        graphviz = visualizer.to_graphviz(plan)
        stats = visualizer.get_statistics(plan)

        assert "Nodes: 5" in pretty
        assert "digraph ExecutionPlan" in graphviz
        assert stats["total_nodes"] == 5
        assert len(stats["node_types"]) >= 3  # At least 3 different node types

    def test_debugger_with_multiple_breakpoints(self):
        """Test debugger with multiple breakpoints."""
        debugger = PlanDebugger()

        nodes = ["node_1", "node_2", "node_3"]
        for node_id in nodes:
            debugger.add_breakpoint(node_id)

        assert len(debugger.breakpoints) == 3
        for node_id in nodes:
            assert node_id in debugger.breakpoints

        # Remove one and verify
        debugger.remove_breakpoint("node_2")
        assert len(debugger.breakpoints) == 2
        assert "node_2" not in debugger.breakpoints


# ============================================================================
# Tests for _get_node_visual_info() and data-driven styling registries
# ============================================================================


class TestNodeVisualInfo:
    """Test that _get_node_visual_info returns correct styling for every node type."""

    def setup_method(self):
        self.vis = PlanVisualizer()

    def test_assign_node_style(self):
        node = AssignNode("x", LiteralNode(1, 1, 1, "l1"), 1, 1, "a1")
        label, shape, style, color = self.vis._get_node_visual_info(node)
        assert "assign" in label
        assert "$x" in label
        assert shape == "ellipse"
        assert color == "lightblue"
        assert style == "filled"

    def test_literal_node_string_style(self):
        node = LiteralNode("hello", 1, 1, "l1")
        label, shape, style, color = self.vis._get_node_visual_info(node)
        assert "literal" in label
        assert "hello" in label
        assert shape == "box"
        assert color == "lightgreen"

    def test_literal_node_number_style(self):
        node = LiteralNode(42, 1, 1, "l1")
        label, shape, _, _ = self.vis._get_node_visual_info(node)
        assert "42" in label
        assert "literal" in label

    def test_variable_node_style(self):
        node = VariableNode("result", 1, 1, "v1")
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert "$result" in label
        assert "variable" in label
        assert shape == "diamond"
        assert color == "lightyellow"

    def test_tool_call_node_style_with_args(self):
        node = ToolCallNode("fetch", [LiteralNode("url", 1, 1, "l1")], {}, 1, 1, "tc1")
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert "fetch" in label
        assert "(1 args)" in label
        assert "tool_call" in label
        assert shape == "hexagon"
        assert color == "orange"

    def test_tool_call_node_style_no_args(self):
        node = ToolCallNode("now", [], {}, 1, 1, "tc1")
        label, _, _, _ = self.vis._get_node_visual_info(node)
        assert "now()" in label

    def test_interpolation_node_style(self):
        node = InterpolationNode(
            "Hello ${name}",
            [VariableNode("name", 1, 1, "v1")],
            {},
            1,
            1,
            "i1",
        )
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert "interpolation" in label
        assert shape == "note"
        assert color == "lightcyan"

    def test_interpolation_long_template_truncated(self):
        long_template = "A" * 30 + "${x}"
        node = InterpolationNode(
            long_template, [VariableNode("x", 1, 1, "v1")], {}, 1, 1, "i1"
        )
        label, _, _, _ = self.vis._get_node_visual_info(node)
        assert "..." in label

    def test_field_access_style(self):
        node = FieldAccessNode(VariableNode("obj", 1, 1, "v1"), "name", 1, 1, "fa1")
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert ".name" in label
        assert "field_access" in label
        assert shape == "triangle"
        assert color == "pink"

    def test_list_node_style(self):
        node = ListNode(
            [LiteralNode(1, 1, 1, "l1"), LiteralNode(2, 1, 1, "l2")],
            1,
            1,
            "ln1",
        )
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert "[2 items]" in label
        assert "list" in label
        assert shape == "folder"

    def test_dict_node_style(self):
        node = DictNode(
            [(LiteralNode("a", 1, 1, "k"), LiteralNode(1, 1, 1, "v"))],
            1,
            1,
            "d1",
        )
        label, shape, _, _ = self.vis._get_node_visual_info(node)
        assert "1 pairs" in label
        assert "dict" in label
        assert shape == "house"

    def test_indexed_access_style(self):
        node = IndexedAccessNode(
            VariableNode("arr", 1, 1, "v1"),
            LiteralNode(0, 1, 1, "l1"),
            1,
            1,
            "ia1",
        )
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert "indexed_access" in label
        assert shape == "trapezium"
        assert color == "lightsteelblue"

    def test_arithmetic_node_style(self):
        node = ArithmeticNode(
            "+",
            LiteralNode(1, 1, 1, "l1"),
            LiteralNode(2, 1, 1, "l2"),
            1,
            1,
            "ar1",
        )
        label, shape, _, _ = self.vis._get_node_visual_info(node)
        assert "+" in label
        assert "arithmetic" in label
        assert shape == "oval"

    def test_comparison_node_style(self):
        node = ComparisonNode(
            ">=",
            VariableNode("x", 1, 1, "v1"),
            LiteralNode(10, 1, 1, "l1"),
            1,
            1,
            "cmp1",
        )
        label, shape, _, _ = self.vis._get_node_visual_info(node)
        assert ">=" in label
        assert "comparison" in label
        assert shape == "diamond"

    def test_boolean_op_style(self):
        node = BooleanOpNode(
            "and",
            [LiteralNode(True, 1, 1, "l1"), LiteralNode(False, 1, 1, "l2")],
            1,
            1,
            "b1",
        )
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert "and" in label
        assert "2 ops" in label
        assert "boolean_op" in label
        assert color == "lavender"

    def test_unary_op_style(self):
        node = UnaryOpNode("not", LiteralNode(True, 1, 1, "l1"), 1, 1, "u1")
        label, shape, _, _ = self.vis._get_node_visual_info(node)
        assert "not" in label
        assert "unary_op" in label
        assert shape == "invtriangle"

    def test_conditional_if_only_style(self):
        node = ConditionalNode(
            LiteralNode(True, 1, 1, "c1"),
            [LiteralNode(1, 1, 1, "l1")],
            [],
            [],
            None,
            1,
            1,
            "cond1",
        )
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert "if" in label
        assert "conditional" in label
        assert "elif" not in label
        assert color == "lightcyan"

    def test_conditional_if_elif_else_style(self):
        node = ConditionalNode(
            LiteralNode(True, 1, 1, "c1"),
            [LiteralNode(1, 1, 1, "l1")],
            [LiteralNode(False, 1, 1, "c2"), LiteralNode(False, 1, 1, "c3")],
            [[LiteralNode(2, 1, 1, "l2")], [LiteralNode(3, 1, 1, "l3")]],
            [LiteralNode(4, 1, 1, "l4")],
            1,
            1,
            "cond2",
        )
        label, _, _, _ = self.vis._get_node_visual_info(node)
        assert "2elif" in label
        assert "else" in label

    def test_while_loop_style(self):
        node = WhileLoopNode(
            LiteralNode(True, 1, 1, "c1"),
            [LiteralNode(1, 1, 1, "l1"), LiteralNode(2, 1, 1, "l2")],
            1,
            1,
            "wh1",
        )
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert "while" in label
        assert "2 stmts" in label
        assert "while_loop" in label
        assert shape == "doublecircle"
        assert color == "lavender"

    def test_return_node_style(self):
        node = ReturnNode(LiteralNode("done", 1, 1, "l1"), 1, 1, "r1")
        label, shape, _, color = self.vis._get_node_visual_info(node)
        assert "return" in label
        assert shape == "Msquare"
        assert color == "mistyrose"


class TestVisualStyleRegistryConsistency:
    """Verify that _NODE_VISUAL_STYLES and _NODE_LABEL_BUILDERS are in sync."""

    def test_every_styled_type_has_label_builder_or_fallback(self):
        """Every type with visual style should have a label builder or use the node_type.value fallback.

        Leaf control flow nodes (return, break, continue) intentionally omit
        label builders because node_type.value already produces the correct label.
        """
        for node_type in _NODE_VISUAL_STYLES:
            if node_type not in _NODE_LABEL_BUILDERS:
                # Verify the fallback (node_type.value) produces a sensible label
                type_name = _NODE_VISUAL_STYLES[node_type][0]
                assert type_name in ("return", "break", "continue"), (
                    f"{node_type.__name__} has style but no label builder"
                )

    def test_every_label_builder_has_style(self):
        """Every type with a label builder should have visual style."""
        for node_type in _NODE_LABEL_BUILDERS:
            assert node_type in _NODE_VISUAL_STYLES, (
                f"{node_type.__name__} has label builder but no style"
            )

    def test_default_style_is_sensible(self):
        """Default style should render as unknown."""
        assert _DEFAULT_STYLE[0] == "unknown"
        assert _DEFAULT_STYLE[1] == "box"

    @pytest.mark.parametrize(
        "node_type",
        list(_NODE_VISUAL_STYLES.keys()),
        ids=lambda t: t.__name__,
    )
    def test_all_styles_have_three_elements(self, node_type):
        """Each style tuple must be (type_name, shape, fillcolor)."""
        style = _NODE_VISUAL_STYLES[node_type]
        assert len(style) == 3, f"{node_type.__name__} style has wrong length"
        assert all(isinstance(s, str) for s in style)


class TestGraphvizEscaping:
    """Test GraphViz label escaping handles special characters."""

    def setup_method(self):
        self.vis = PlanVisualizer()

    def test_escape_quotes(self):
        result = self.vis._escape_graphviz_label('say "hello"')
        # Quotes should be escaped for GraphViz DOT syntax
        assert '\\"' in result
        assert "say" in result

    def test_escape_braces(self):
        result = self.vis._escape_graphviz_label("{key: value}")
        assert "\\{" in result
        assert "\\}" in result

    def test_escape_angle_brackets(self):
        result = self.vis._escape_graphviz_label("<html>")
        assert "\\<" in result
        assert "\\>" in result

    def test_plain_text_unchanged(self):
        result = self.vis._escape_graphviz_label("hello_world_123")
        assert result == "hello_world_123"
