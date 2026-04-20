"""
Unit tests for Task Execution Plan schema and data structures.
"""

import json

import pytest

from src.cy_language.execution_plan import (
    ArithmeticNode,
    AssignNode,
    BooleanOpNode,
    CatchClause,
    ComparisonNode,
    ConditionalNode,
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
    NodeType,
    ReturnNode,
    ToolCallNode,
    TryCatchNode,
    UnaryOpNode,
    VariableNode,
    WhileLoopNode,
)


class TestExecutionPlanSchema:
    """Test execution plan schema creation and basic operations."""

    def test_plan_creation(self):
        """Test ExecutionPlan can be created with proper metadata."""
        plan = ExecutionPlan(version="2.0", source_file="test.cy")

        assert plan.version == "2.0"
        assert plan.source_file == "test.cy"
        assert plan.nodes == []
        assert plan.metadata == {}

    def test_plan_creation_defaults(self):
        """Test ExecutionPlan creation with default values."""
        plan = ExecutionPlan()

        assert plan.version == "2.0"
        assert plan.source_file is None
        assert plan.nodes == []
        assert plan.metadata == {}

    def test_add_node(self):
        """Test adding nodes to execution plan."""
        plan = ExecutionPlan()
        node = LiteralNode("hello", 1, 1, "node_1")

        plan.add_node(node)

        assert len(plan.nodes) == 1
        assert plan.nodes[0] == node


class TestExecutionNodes:
    """Test individual execution node types."""

    def test_literal_node_creation(self):
        """Test LiteralNode creation."""
        node = LiteralNode("hello", 1, 5, "node_1")

        assert node.node_type == NodeType.LITERAL
        assert node.value == "hello"
        assert node.line_number == 1
        assert node.column == 5
        assert node.node_id == "node_1"

    def test_variable_node_creation(self):
        """Test VariableNode creation."""
        node = VariableNode("myvar", 2, 3, "node_2")

        assert node.node_type == NodeType.VARIABLE
        assert node.variable_name == "myvar"
        assert node.line_number == 2
        assert node.column == 3
        assert node.node_id == "node_2"

    def test_assign_node_creation(self):
        """Test AssignNode creation."""
        expr_node = LiteralNode("value", 1, 10, "node_1")
        assign_node = AssignNode("var", expr_node, 1, 1, "node_2")

        assert assign_node.node_type == NodeType.ASSIGN
        assert assign_node.variable_name == "var"
        assert assign_node.expression == expr_node
        assert assign_node.line_number == 1
        assert assign_node.column == 1
        assert assign_node.node_id == "node_2"

    def test_tool_call_node_creation(self):
        """Test ToolCallNode creation."""
        arg1 = LiteralNode(1, 1, 5, "node_1")
        arg2 = LiteralNode(2, 1, 8, "node_2")
        named_args = {"key": LiteralNode("value", 1, 15, "node_3")}

        tool_node = ToolCallNode("add", [arg1, arg2], named_args, 1, 1, "node_4")

        assert tool_node.node_type == NodeType.TOOL_CALL
        assert tool_node.tool_name == "add"
        assert tool_node.arguments == [arg1, arg2]
        assert tool_node.named_arguments == named_args

    def test_interpolation_node_creation(self):
        """Test InterpolationNode creation."""
        var_node = VariableNode("name", 1, 10, "node_1")
        hints = {"name": "csv"}

        interp_node = InterpolationNode(
            "Hello ${name}", [var_node], hints, 1, 1, "node_2"
        )

        assert interp_node.node_type == NodeType.INTERPOLATION
        assert interp_node.template == "Hello ${name}"
        assert interp_node.variables == [var_node]
        assert interp_node.printer_hints == hints


class TestNodeSerialization:
    """Test node serialization to/from dictionaries."""

    def test_node_to_dict(self):
        """Test ExecutionNode.to_dict() method."""
        node = LiteralNode("test", 1, 1, "node_1")
        result = node.to_dict()

        # Basic structure test - implementation will expand this
        assert "type" in result
        assert "line" in result
        assert result["type"] == "literal"
        assert result["line"] == 1

    def test_node_from_dict_implemented(self):
        """Test ExecutionNode.from_dict() works correctly."""
        data = {
            "type": "literal",
            "line": 1,
            "column": 5,
            "node_id": "node_1",
            "value": "hello",
        }

        node = ExecutionNode.from_dict(data)

        assert isinstance(node, LiteralNode)
        assert node.value == "hello"
        assert node.line_number == 1
        assert node.column == 5
        assert node.node_id == "node_1"


class TestPlanSerialization:
    """Test execution plan JSON serialization."""

    def test_plan_to_json_basic(self):
        """Test ExecutionPlan.to_json() basic functionality."""
        plan = ExecutionPlan(version="2.0", source_file="test.cy")
        node = LiteralNode("hello", 1, 1, "node_1")
        plan.add_node(node)

        json_str = plan.to_json()
        data = json.loads(json_str)

        assert data["version"] == "2.0"
        assert data["source_file"] == "test.cy"
        assert "nodes" in data
        assert "metadata" in data
        assert len(data["nodes"]) == 1

    def test_plan_from_json_basic(self):
        """Test ExecutionPlan.from_json() basic functionality."""
        json_data = {
            "version": "2.0",
            "source_file": "test.cy",
            "nodes": [],
            "metadata": {},
        }
        json_str = json.dumps(json_data)

        plan = ExecutionPlan.from_json(json_str)

        assert plan.version == "2.0"
        assert plan.source_file == "test.cy"
        assert plan.nodes == []
        assert plan.metadata == {}

    def test_plan_serialization_roundtrip(self):
        """Test plan can be serialized and deserialized without loss."""
        # Create original plan
        original_plan = ExecutionPlan(version="2.0", source_file="test.cy")
        literal_node = LiteralNode("hello", 1, 1, "node_1")
        var_node = VariableNode("test_var", 2, 5, "node_2")
        assign_node = AssignNode("output", literal_node, 3, 1, "node_3")

        original_plan.add_node(literal_node)
        original_plan.add_node(var_node)
        original_plan.add_node(assign_node)
        original_plan.metadata["test"] = "value"

        # Serialize and deserialize
        json_str = original_plan.to_json()
        restored_plan = ExecutionPlan.from_json(json_str)

        # Verify structure
        assert restored_plan.version == original_plan.version
        assert restored_plan.source_file == original_plan.source_file
        assert len(restored_plan.nodes) == len(original_plan.nodes)
        assert restored_plan.metadata == original_plan.metadata

        # Verify nodes
        assert isinstance(restored_plan.nodes[0], LiteralNode)
        assert restored_plan.nodes[0].value == "hello"
        assert isinstance(restored_plan.nodes[1], VariableNode)
        assert restored_plan.nodes[1].variable_name == "test_var"
        assert isinstance(restored_plan.nodes[2], AssignNode)
        assert restored_plan.nodes[2].variable_name == "output"


class TestPlanValidation:
    """Test execution plan validation."""

    def test_empty_plan_validation(self):
        """Test validation catches empty plans."""
        plan = ExecutionPlan()
        errors = plan.validate()

        assert len(errors) > 0
        assert "Execution plan has no nodes" in errors

    def test_plan_without_output_validation(self):
        """Test validation catches plans without return statement."""
        plan = ExecutionPlan()
        node = LiteralNode("hello", 1, 1, "node_1")
        plan.add_node(node)

        errors = plan.validate()

        assert "Execution plan must have a return statement" in errors

    def test_valid_plan_validation(self):
        """Test validation passes for valid plans with return statement."""
        from src.cy_language.execution_plan import ReturnNode

        plan = ExecutionPlan()
        literal_node = LiteralNode("hello", 1, 1, "node_1")
        assign_node = AssignNode("output", literal_node, 2, 1, "node_2")
        var_node = VariableNode("output", 3, 1, "node_3")
        return_node = ReturnNode(var_node, 3, 1, "node_4")
        plan.add_node(literal_node)
        plan.add_node(assign_node)
        plan.add_node(return_node)

        errors = plan.validate()

        # Should have no errors for a valid plan
        assert len(errors) == 0

    def test_duplicate_node_id_validation(self):
        """Test validation catches duplicate node IDs."""
        plan = ExecutionPlan()
        node1 = LiteralNode("hello", 1, 1, "duplicate_id")
        node2 = LiteralNode("world", 2, 1, "duplicate_id")
        assign_node = AssignNode("output", node1, 3, 1, "node_3")

        plan.add_node(node1)
        plan.add_node(node2)
        plan.add_node(assign_node)

        errors = plan.validate()

        assert "Duplicate node ID: duplicate_id" in errors


class TestNodeIdGeneration:
    """Test unique node ID generation."""

    def test_unique_node_ids(self):
        """Test that node IDs are unique."""
        node1 = LiteralNode("value1", 1, 1, "node_1")
        node2 = LiteralNode("value2", 1, 1, "node_2")

        assert node1.node_id != node2.node_id

    def test_node_id_format(self):
        """Test node ID format is reasonable."""
        node = LiteralNode("value", 1, 1, "node_1")

        assert isinstance(node.node_id, str)
        assert len(node.node_id) > 0


class TestLineColumnTracking:
    """Test line and column information preservation."""

    def test_line_column_preserved(self):
        """Test line and column information is preserved in nodes."""
        node = LiteralNode("value", 42, 15, "node_1")

        assert node.line_number == 42
        assert node.column == 15

    def test_line_column_in_nested_structures(self):
        """Test line/column info preserved in nested node structures."""
        expr_node = LiteralNode("value", 5, 10, "node_1")
        assign_node = AssignNode("var", expr_node, 5, 1, "node_2")

        assert assign_node.line_number == 5
        assert assign_node.column == 1
        assert assign_node.expression.line_number == 5
        assert assign_node.expression.column == 10


class TestListComprehensionRoundTrip:
    """Test LIST_COMPREHENSION serialization round-trip."""

    def test_list_comprehension_roundtrip_no_filter(self):
        """Test list comprehension without filter round-trips through JSON."""
        node = ListComprehensionNode(
            element_expr=VariableNode("x", 1, 2, "elem_1"),
            iterator_var="x",
            iterable_expr=VariableNode("items", 1, 15, "iter_1"),
            filter_expr=None,
            line_number=1,
            column=1,
            node_id="lc_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ListComprehensionNode)
        assert restored.iterator_var == "x"
        assert restored.filter_expr is None
        assert isinstance(restored.element_expr, VariableNode)
        assert restored.element_expr.variable_name == "x"
        assert isinstance(restored.iterable_expr, VariableNode)
        assert restored.iterable_expr.variable_name == "items"
        assert restored.node_id == "lc_1"

    def test_list_comprehension_roundtrip_with_filter(self):
        """Test list comprehension with filter round-trips through JSON."""
        from src.cy_language.execution_plan import ComparisonNode

        node = ListComprehensionNode(
            element_expr=VariableNode("x", 1, 2, "elem_1"),
            iterator_var="x",
            iterable_expr=VariableNode("items", 1, 15, "iter_1"),
            filter_expr=ComparisonNode(
                ">",
                VariableNode("x", 1, 30, "cmp_l"),
                LiteralNode(0, 1, 34, "cmp_r"),
                1,
                28,
                "filter_1",
            ),
            line_number=1,
            column=1,
            node_id="lc_2",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ListComprehensionNode)
        assert restored.filter_expr is not None
        assert isinstance(restored.filter_expr, ComparisonNode)
        assert restored.filter_expr.operator == ">"

    def test_list_comprehension_in_plan_roundtrip(self):
        """Test list comprehension node survives full plan JSON round-trip."""
        plan = ExecutionPlan(version="2.0", source_file="test.cy")
        lc_node = ListComprehensionNode(
            element_expr=VariableNode("x", 1, 2, "elem_1"),
            iterator_var="x",
            iterable_expr=VariableNode("items", 1, 15, "iter_1"),
            filter_expr=None,
            line_number=1,
            column=1,
            node_id="lc_1",
        )
        assign = AssignNode("result", lc_node, 1, 1, "assign_1")
        ret = ReturnNode(VariableNode("result", 2, 1, "ret_var"), 2, 1, "ret_1")
        plan.add_node(assign)
        plan.add_node(ret)

        json_str = plan.to_json()
        restored = ExecutionPlan.from_json(json_str)

        assert len(restored.nodes) == 2
        restored_assign = restored.nodes[0]
        assert isinstance(restored_assign, AssignNode)
        assert isinstance(restored_assign.expression, ListComprehensionNode)
        assert restored_assign.expression.iterator_var == "x"


class TestTryCatchRoundTrip:
    """Test TRY_CATCH serialization round-trip."""

    def test_try_catch_roundtrip_basic(self):
        """Test basic try/catch round-trips through JSON."""
        node = TryCatchNode(
            try_body=[
                AssignNode("x", LiteralNode(42, 2, 5, "lit_1"), 2, 1, "assign_1")
            ],
            catch_clauses=[
                CatchClause(
                    exception_var="e",
                    body=[
                        AssignNode("x", LiteralNode(0, 4, 5, "lit_2"), 4, 1, "assign_2")
                    ],
                )
            ],
            finally_body=None,
            line_number=1,
            column=1,
            node_id="tc_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, TryCatchNode)
        assert len(restored.try_body) == 1
        assert len(restored.catch_clauses) == 1
        assert restored.catch_clauses[0].exception_var == "e"
        assert len(restored.catch_clauses[0].body) == 1
        assert restored.finally_body is None
        assert restored.node_id == "tc_1"

    def test_try_catch_roundtrip_with_finally(self):
        """Test try/catch/finally round-trips through JSON."""
        node = TryCatchNode(
            try_body=[
                AssignNode("x", LiteralNode(42, 2, 5, "lit_1"), 2, 1, "assign_1")
            ],
            catch_clauses=[
                CatchClause(
                    exception_var="e",
                    body=[
                        AssignNode("x", LiteralNode(0, 4, 5, "lit_2"), 4, 1, "assign_2")
                    ],
                )
            ],
            finally_body=[
                AssignNode("done", LiteralNode(True, 6, 8, "lit_3"), 6, 1, "assign_3")
            ],
            line_number=1,
            column=1,
            node_id="tc_2",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, TryCatchNode)
        assert restored.finally_body is not None
        assert len(restored.finally_body) == 1
        assert isinstance(restored.finally_body[0], AssignNode)
        assert restored.finally_body[0].variable_name == "done"

    def test_try_catch_in_plan_roundtrip(self):
        """Test try/catch node survives full plan JSON round-trip."""
        plan = ExecutionPlan(version="2.0", source_file="test.cy")
        tc_node = TryCatchNode(
            try_body=[AssignNode("x", LiteralNode(1, 2, 5, "lit_1"), 2, 1, "assign_1")],
            catch_clauses=[
                CatchClause(
                    exception_var="err",
                    body=[
                        AssignNode(
                            "x", LiteralNode(-1, 4, 5, "lit_2"), 4, 1, "assign_2"
                        )
                    ],
                )
            ],
            finally_body=None,
            line_number=1,
            column=1,
            node_id="tc_1",
        )
        ret = ReturnNode(VariableNode("x", 5, 1, "ret_var"), 5, 1, "ret_1")
        plan.add_node(tc_node)
        plan.add_node(ret)

        json_str = plan.to_json()
        restored = ExecutionPlan.from_json(json_str)

        assert len(restored.nodes) == 2
        assert isinstance(restored.nodes[0], TryCatchNode)
        assert restored.nodes[0].catch_clauses[0].exception_var == "err"

    def test_catch_clause_from_dict(self):
        """Test CatchClause.from_dict() directly."""
        data = {
            "exception_var": "e",
            "body": [
                {
                    "type": "literal",
                    "value": 0,
                    "line": 1,
                    "column": 1,
                    "node_id": "n1",
                }
            ],
        }
        clause = CatchClause.from_dict(data)

        assert clause.exception_var == "e"
        assert len(clause.body) == 1
        assert isinstance(clause.body[0], LiteralNode)
        assert clause.body[0].value == 0


# ============================================================================
# Round-trip tests for every remaining node type (Area 4 coverage gap fix)
# ============================================================================


class TestIndexedAssignRoundTrip:
    """Test IndexedAssignNode serialization round-trip."""

    def test_indexed_assign_roundtrip(self):
        """Test indexed assignment ($dict[$key] = $value) round-trips."""
        target = IndexedAccessNode(
            VariableNode("data", 1, 1, "var_1"),
            LiteralNode("key", 1, 5, "lit_1"),
            1,
            1,
            "idx_1",
        )
        value = LiteralNode(42, 1, 15, "lit_2")
        node = IndexedAssignNode(target, value, 1, 1, "ia_1")

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, IndexedAssignNode)
        assert isinstance(restored.target, IndexedAccessNode)
        assert isinstance(restored.value, LiteralNode)
        assert restored.value.value == 42
        assert restored.node_id == "ia_1"


class TestFieldAssignRoundTrip:
    """Test FieldAssignNode serialization round-trip."""

    def test_field_assign_roundtrip(self):
        """Test field assignment (a.x = value) round-trips."""
        target = FieldAccessNode(
            VariableNode("obj", 1, 1, "var_1"),
            "name",
            1,
            1,
            "fa_1",
        )
        value = LiteralNode("Alice", 1, 12, "lit_1")
        node = FieldAssignNode(target, value, 1, 1, "fass_1")

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, FieldAssignNode)
        assert isinstance(restored.target, FieldAccessNode)
        assert restored.target.field_name == "name"
        assert isinstance(restored.value, LiteralNode)
        assert restored.value.value == "Alice"


class TestListNodeRoundTrip:
    """Test ListNode serialization round-trip."""

    def test_list_empty_roundtrip(self):
        """Test empty list round-trips."""
        node = ListNode([], 1, 1, "list_1")

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ListNode)
        assert restored.elements == []

    def test_list_with_elements_roundtrip(self):
        """Test list with mixed elements round-trips."""
        node = ListNode(
            [
                LiteralNode(1, 1, 2, "lit_1"),
                LiteralNode("two", 1, 5, "lit_2"),
                LiteralNode(True, 1, 11, "lit_3"),
            ],
            1,
            1,
            "list_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ListNode)
        assert len(restored.elements) == 3
        assert restored.elements[0].value == 1
        assert restored.elements[1].value == "two"
        assert restored.elements[2].value is True


class TestDictNodeRoundTrip:
    """Test DictNode serialization round-trip."""

    def test_dict_roundtrip(self):
        """Test dict node round-trips with key-value pairs."""
        node = DictNode(
            [
                (LiteralNode("a", 1, 2, "k1"), LiteralNode(1, 1, 6, "v1")),
                (LiteralNode("b", 1, 9, "k2"), LiteralNode(2, 1, 13, "v2")),
            ],
            1,
            1,
            "dict_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, DictNode)
        assert len(restored.pairs) == 2
        assert restored.pairs[0][0].value == "a"
        assert restored.pairs[0][1].value == 1
        assert restored.pairs[1][0].value == "b"
        assert restored.pairs[1][1].value == 2

    def test_dict_empty_roundtrip(self):
        """Test empty dict round-trips."""
        node = DictNode([], 1, 1, "dict_e")

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, DictNode)
        assert restored.pairs == []


class TestFieldAccessRoundTrip:
    """Test FieldAccessNode serialization round-trip."""

    def test_field_access_roundtrip(self):
        """Test field access (obj.field) round-trips."""
        node = FieldAccessNode(
            VariableNode("result", 1, 1, "var_1"),
            "status",
            1,
            1,
            "fa_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, FieldAccessNode)
        assert restored.field_name == "status"
        assert isinstance(restored.object_node, VariableNode)
        assert restored.object_node.variable_name == "result"

    def test_nested_field_access_roundtrip(self):
        """Test chained field access (a.b.c) round-trips."""
        inner = FieldAccessNode(VariableNode("a", 1, 1, "var_1"), "b", 1, 1, "fa_1")
        node = FieldAccessNode(inner, "c", 1, 1, "fa_2")

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, FieldAccessNode)
        assert restored.field_name == "c"
        assert isinstance(restored.object_node, FieldAccessNode)
        assert restored.object_node.field_name == "b"


class TestIndexedAccessRoundTrip:
    """Test IndexedAccessNode serialization round-trip."""

    def test_indexed_access_roundtrip(self):
        """Test indexed access (list[0]) round-trips."""
        node = IndexedAccessNode(
            VariableNode("items", 1, 1, "var_1"),
            LiteralNode(0, 1, 7, "lit_1"),
            1,
            1,
            "ia_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, IndexedAccessNode)
        assert isinstance(restored.object_node, VariableNode)
        assert isinstance(restored.index_node, LiteralNode)
        assert restored.index_node.value == 0


class TestArithmeticNodeRoundTrip:
    """Test ArithmeticNode serialization round-trip."""

    def test_arithmetic_roundtrip(self):
        """Test arithmetic (a + b) round-trips."""
        node = ArithmeticNode(
            "+",
            LiteralNode(3, 1, 1, "lit_1"),
            LiteralNode(4, 1, 5, "lit_2"),
            1,
            1,
            "arith_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ArithmeticNode)
        assert restored.operator == "+"
        assert restored.left.value == 3
        assert restored.right.value == 4

    def test_nested_arithmetic_roundtrip(self):
        """Test nested arithmetic ((a + b) * c) round-trips."""
        inner = ArithmeticNode(
            "+",
            LiteralNode(1, 1, 2, "l1"),
            LiteralNode(2, 1, 6, "l2"),
            1,
            2,
            "add_1",
        )
        node = ArithmeticNode("*", inner, LiteralNode(3, 1, 11, "l3"), 1, 1, "mul_1")

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ArithmeticNode)
        assert restored.operator == "*"
        assert isinstance(restored.left, ArithmeticNode)
        assert restored.left.operator == "+"


class TestComparisonNodeRoundTrip:
    """Test ComparisonNode serialization round-trip."""

    def test_comparison_roundtrip(self):
        """Test comparison (x > 10) round-trips."""
        node = ComparisonNode(
            ">",
            VariableNode("x", 1, 1, "var_1"),
            LiteralNode(10, 1, 5, "lit_1"),
            1,
            1,
            "cmp_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ComparisonNode)
        assert restored.operator == ">"
        assert isinstance(restored.left, VariableNode)
        assert restored.right.value == 10

    def test_all_comparison_operators_roundtrip(self):
        """Test all comparison operators preserve through round-trip."""
        for op in ("==", "!=", "<", ">", "<=", ">=", "in"):
            node = ComparisonNode(
                op,
                LiteralNode(1, 1, 1, "l"),
                LiteralNode(2, 1, 5, "r"),
                1,
                1,
                "cmp",
            )
            restored = ExecutionNode.from_dict(node.to_dict())
            assert restored.operator == op, f"Operator {op} not preserved"


class TestBooleanOpRoundTrip:
    """Test BooleanOpNode serialization round-trip."""

    def test_boolean_and_roundtrip(self):
        """Test boolean 'and' round-trips."""
        node = BooleanOpNode(
            "and",
            [LiteralNode(True, 1, 1, "l1"), LiteralNode(False, 1, 10, "l2")],
            1,
            1,
            "bool_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, BooleanOpNode)
        assert restored.operator == "and"
        assert len(restored.operands) == 2

    def test_boolean_or_multiple_operands_roundtrip(self):
        """Test boolean 'or' with 3+ operands round-trips."""
        node = BooleanOpNode(
            "or",
            [
                LiteralNode(False, 1, 1, "l1"),
                LiteralNode(True, 1, 5, "l2"),
                LiteralNode(False, 1, 10, "l3"),
            ],
            1,
            1,
            "bool_2",
        )

        restored = ExecutionNode.from_dict(node.to_dict())

        assert isinstance(restored, BooleanOpNode)
        assert restored.operator == "or"
        assert len(restored.operands) == 3


class TestUnaryOpRoundTrip:
    """Test UnaryOpNode serialization round-trip."""

    def test_unary_not_roundtrip(self):
        """Test unary 'not' round-trips."""
        node = UnaryOpNode("not", LiteralNode(True, 1, 5, "lit_1"), 1, 1, "unary_1")

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, UnaryOpNode)
        assert restored.operator == "not"
        assert isinstance(restored.operand, LiteralNode)
        assert restored.operand.value is True

    def test_unary_negation_roundtrip(self):
        """Test unary '-' round-trips."""
        node = UnaryOpNode("-", LiteralNode(42, 1, 2, "lit_1"), 1, 1, "unary_2")

        restored = ExecutionNode.from_dict(node.to_dict())

        assert isinstance(restored, UnaryOpNode)
        assert restored.operator == "-"
        assert restored.operand.value == 42


class TestConditionalRoundTrip:
    """Test ConditionalNode serialization round-trip."""

    def test_if_only_roundtrip(self):
        """Test if-only conditional round-trips."""
        node = ConditionalNode(
            condition=LiteralNode(True, 1, 5, "cond_1"),
            if_body=[AssignNode("x", LiteralNode(1, 2, 5, "lit_1"), 2, 1, "a_1")],
            elif_conditions=[],
            elif_bodies=[],
            else_body=None,
            line_number=1,
            column=1,
            node_id="if_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ConditionalNode)
        assert isinstance(restored.condition, LiteralNode)
        assert len(restored.if_body) == 1
        assert restored.elif_conditions == []
        assert restored.elif_bodies == []
        assert restored.else_body is None

    def test_if_elif_else_roundtrip(self):
        """Test full if/elif/else conditional round-trips."""
        node = ConditionalNode(
            condition=ComparisonNode(
                ">",
                VariableNode("x", 1, 5, "v1"),
                LiteralNode(10, 1, 9, "l1"),
                1,
                5,
                "cmp_1",
            ),
            if_body=[AssignNode("r", LiteralNode("big", 2, 5, "l2"), 2, 1, "a_1")],
            elif_conditions=[
                ComparisonNode(
                    ">",
                    VariableNode("x", 3, 9, "v2"),
                    LiteralNode(5, 3, 13, "l3"),
                    3,
                    9,
                    "cmp_2",
                ),
            ],
            elif_bodies=[
                [AssignNode("r", LiteralNode("mid", 4, 5, "l4"), 4, 1, "a_2")],
            ],
            else_body=[
                AssignNode("r", LiteralNode("small", 6, 5, "l5"), 6, 1, "a_3"),
            ],
            line_number=1,
            column=1,
            node_id="if_2",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ConditionalNode)
        assert len(restored.elif_conditions) == 1
        assert len(restored.elif_bodies) == 1
        assert restored.else_body is not None
        assert len(restored.else_body) == 1


class TestWhileLoopRoundTrip:
    """Test WhileLoopNode serialization round-trip."""

    def test_while_loop_roundtrip(self):
        """Test while loop round-trips."""
        node = WhileLoopNode(
            condition=ComparisonNode(
                "<",
                VariableNode("i", 1, 8, "v1"),
                LiteralNode(10, 1, 12, "l1"),
                1,
                8,
                "cmp_1",
            ),
            body=[
                AssignNode(
                    "i",
                    ArithmeticNode(
                        "+",
                        VariableNode("i", 2, 5, "v2"),
                        LiteralNode(1, 2, 9, "l2"),
                        2,
                        5,
                        "add_1",
                    ),
                    2,
                    1,
                    "a_1",
                ),
            ],
            line_number=1,
            column=1,
            node_id="while_1",
        )

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, WhileLoopNode)
        assert isinstance(restored.condition, ComparisonNode)
        assert len(restored.body) == 1
        assert isinstance(restored.body[0], AssignNode)

    def test_while_empty_body_roundtrip(self):
        """Test while loop with empty body round-trips."""
        node = WhileLoopNode(
            condition=LiteralNode(False, 1, 8, "lit_1"),
            body=[],
            line_number=1,
            column=1,
            node_id="while_e",
        )

        restored = ExecutionNode.from_dict(node.to_dict())

        assert isinstance(restored, WhileLoopNode)
        assert restored.body == []


class TestReturnNodeRoundTrip:
    """Test ReturnNode serialization round-trip."""

    def test_return_literal_roundtrip(self):
        """Test return with literal round-trips."""
        node = ReturnNode(LiteralNode("done", 1, 8, "lit_1"), 1, 1, "ret_1")

        data = node.to_dict()
        restored = ExecutionNode.from_dict(data)

        assert isinstance(restored, ReturnNode)
        assert isinstance(restored.expression, LiteralNode)
        assert restored.expression.value == "done"

    def test_return_complex_expr_roundtrip(self):
        """Test return with complex expression round-trips."""
        expr = ArithmeticNode(
            "+",
            VariableNode("a", 1, 8, "v1"),
            VariableNode("b", 1, 12, "v2"),
            1,
            8,
            "add_1",
        )
        node = ReturnNode(expr, 1, 1, "ret_2")

        restored = ExecutionNode.from_dict(node.to_dict())

        assert isinstance(restored, ReturnNode)
        assert isinstance(restored.expression, ArithmeticNode)


class TestFromDictEdgeCases:
    """Adversarial and edge-case tests for from_dict / to_dict."""

    def test_unknown_node_type_raises_valueerror(self):
        """Test from_dict raises ValueError for unknown node types."""
        data = {
            "type": "nonexistent_type",
            "line": 1,
            "column": 1,
            "node_id": "n1",
        }
        # The NodeType enum constructor raises ValueError before dispatch
        with pytest.raises(ValueError, match="not a valid NodeType"):
            ExecutionNode.from_dict(data)

    def test_literal_null_value_roundtrip(self):
        """Test literal with None value round-trips correctly."""
        node = LiteralNode(None, 1, 1, "lit_null")

        restored = ExecutionNode.from_dict(node.to_dict())

        assert isinstance(restored, LiteralNode)
        assert restored.value is None

    def test_literal_empty_string_roundtrip(self):
        """Test literal with empty string round-trips."""
        node = LiteralNode("", 1, 1, "lit_empty")

        restored = ExecutionNode.from_dict(node.to_dict())

        assert restored.value == ""

    def test_literal_zero_roundtrip(self):
        """Test literal with zero round-trips (falsy but valid)."""
        node = LiteralNode(0, 1, 1, "lit_zero")

        restored = ExecutionNode.from_dict(node.to_dict())

        assert restored.value == 0

    def test_literal_float_roundtrip(self):
        """Test literal with float round-trips."""
        node = LiteralNode(3.14159, 1, 1, "lit_pi")

        restored = ExecutionNode.from_dict(node.to_dict())

        assert restored.value == 3.14159

    def test_literal_negative_roundtrip(self):
        """Test literal with negative number round-trips."""
        node = LiteralNode(-42, 1, 1, "lit_neg")

        restored = ExecutionNode.from_dict(node.to_dict())

        assert restored.value == -42

    def test_deeply_nested_expression_roundtrip(self):
        """Test deeply nested expression tree round-trips without error."""
        # Build: ((1 + 2) * (3 - 4)) > 0
        add = ArithmeticNode(
            "+",
            LiteralNode(1, 1, 1, "l1"),
            LiteralNode(2, 1, 5, "l2"),
            1,
            1,
            "add",
        )
        sub = ArithmeticNode(
            "-",
            LiteralNode(3, 1, 11, "l3"),
            LiteralNode(4, 1, 15, "l4"),
            1,
            11,
            "sub",
        )
        mul = ArithmeticNode("*", add, sub, 1, 1, "mul")
        cmp = ComparisonNode(">", mul, LiteralNode(0, 1, 20, "l5"), 1, 1, "cmp")
        assign = AssignNode("result", cmp, 1, 1, "assign")
        ret = ReturnNode(VariableNode("result", 2, 1, "v1"), 2, 1, "ret")

        plan = ExecutionPlan(version="2.0")
        plan.add_node(assign)
        plan.add_node(ret)

        json_str = plan.to_json()
        restored = ExecutionPlan.from_json(json_str)

        assert len(restored.nodes) == 2
        restored_assign = restored.nodes[0]
        assert isinstance(restored_assign, AssignNode)
        assert isinstance(restored_assign.expression, ComparisonNode)
        inner_mul = restored_assign.expression.left
        assert isinstance(inner_mul, ArithmeticNode)
        assert inner_mul.operator == "*"

    def test_tool_call_empty_args_roundtrip(self):
        """Test tool call with no arguments round-trips."""
        node = ToolCallNode("now", [], {}, 1, 1, "tc_1")

        restored = ExecutionNode.from_dict(node.to_dict())

        assert isinstance(restored, ToolCallNode)
        assert restored.tool_name == "now"
        assert restored.arguments == []
        assert restored.named_arguments == {}

    def test_tool_call_original_name_preserved_roundtrip(self):
        """Test that original_name survives serialization round-trip.

        When the compiler resolves a short name (e.g. 'len') to an FQN
        (e.g. 'native::tools::len'), original_name preserves the source form.
        This must not be lost during from_dict deserialization.
        """
        node = ToolCallNode(
            "native::tools::len",
            [LiteralNode("hi", 1, 5, "l1")],
            {},
            1,
            1,
            "tc_orig",
            original_name="len",
        )
        assert node.original_name == "len"
        assert node.tool_name == "native::tools::len"

        restored = ExecutionNode.from_dict(node.to_dict())

        assert isinstance(restored, ToolCallNode)
        assert restored.tool_name == "native::tools::len"
        assert restored.original_name == "len"  # Must NOT fall back to tool_name

    def test_tool_call_named_only_args_roundtrip(self):
        """Test tool call with only named arguments round-trips."""
        node = ToolCallNode(
            "fetch",
            [],
            {"url": LiteralNode("https://example.com", 1, 10, "l1")},
            1,
            1,
            "tc_2",
        )

        restored = ExecutionNode.from_dict(node.to_dict())

        assert isinstance(restored, ToolCallNode)
        assert restored.arguments == []
        assert "url" in restored.named_arguments
        assert restored.named_arguments["url"].value == "https://example.com"

    def test_all_node_types_have_deserializer(self):
        """Verify every non-dead NodeType has a dispatch entry.

        This ensures new node types don't silently fail to deserialize.
        """
        from src.cy_language.execution_plan import _NODE_DESERIALIZERS

        # These are defined in the enum but intentionally dead (no node class)
        dead_types = {NodeType.FOR_IN, NodeType.EXPRESSION}

        for nt in NodeType:
            if nt in dead_types:
                continue
            assert nt in _NODE_DESERIALIZERS, (
                f"NodeType.{nt.name} has no entry in _NODE_DESERIALIZERS"
            )
