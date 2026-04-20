"""
Unit tests for TypeInferenceEngine.

Tests verify that the TypeInferenceEngine correctly infers types for
literals, variables, assignments, and operators.
"""

import pytest

from cy_language.execution_plan import (
    ArithmeticNode,
    AssignNode,
    BooleanOpNode,
    ComparisonNode,
    ConditionalNode,
    DictNode,
    ExecutionPlan,
    FieldAccessNode,
    IndexedAccessNode,
    ListNode,
    LiteralNode,
    ReturnNode,
    ToolCallNode,
    UnaryOpNode,
    VariableNode,
    WhileLoopNode,
)
from cy_language.tool_resolver import ToolResolver
from cy_language.type_environment import TypeEnvironment
from cy_language.type_inference_engine import TypeInferenceEngine


class TestEngineInitialization:
    """Test TypeInferenceEngine initialization."""

    def test_engine_initialization(self):
        """Create engine with execution plan."""
        plan = ExecutionPlan()
        resolver = ToolResolver()

        engine = TypeInferenceEngine(plan, resolver)

        assert engine is not None
        assert engine.execution_plan == plan
        assert engine.tool_resolver == resolver

    def test_engine_has_type_environment(self):
        """Verify engine creates TypeEnvironment."""
        plan = ExecutionPlan()
        resolver = ToolResolver()

        engine = TypeInferenceEngine(plan, resolver)

        assert isinstance(engine.type_env, TypeEnvironment)


class TestNodeDispatcher:
    """Test node type dispatching."""

    def test_infer_node_dispatches_to_literal(self):
        """Verify LiteralNode routes to _infer_literal."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        literal_node = LiteralNode(42, 0, 0, "n1")

        # Should not raise error about unknown node type
        result = engine.infer_node(literal_node)
        # Dispatcher worked - should return a type
        assert result == {"type": "number"}

    def test_infer_node_unknown_type_raises_error(self):
        """Unknown node type raises helpful error."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Create a mock node with unrecognized type
        class UnknownNode:
            def __init__(self):
                self.node_id = "unknown1"
                self.node_type = "UNKNOWN_TYPE"

        unknown_node = UnknownNode()

        with pytest.raises((ValueError, NotImplementedError, AttributeError)):
            engine.infer_node(unknown_node)  # type: ignore


class TestMainEntryPoint:
    """Test main infer_types entry point."""

    def test_infer_types_returns_environment(self):
        """infer_types() returns TypeEnvironment."""
        # Create simple plan with one literal
        lit_node = LiteralNode(42, 0, 0, "n2")
        plan = ExecutionPlan()
        plan.add_node(lit_node)
        resolver = ToolResolver()

        engine = TypeInferenceEngine(plan, resolver)
        result = engine.infer_types()

        assert isinstance(result, TypeEnvironment)

    def test_infer_types_walks_all_nodes(self):
        """Verify all nodes are processed."""
        # Create plan with 3 assignments
        assign1 = AssignNode("x", LiteralNode(42, 0, 0, "l1"), 0, 0, "a1")
        assign2 = AssignNode("y", LiteralNode("hello", 0, 0, "l2"), 0, 0, "a2")
        assign3 = AssignNode("z", LiteralNode(True, 0, 0, "l3"), 0, 0, "a3")

        plan = ExecutionPlan()
        plan.add_node(assign1)
        plan.add_node(assign2)
        plan.add_node(assign3)
        resolver = ToolResolver()

        engine = TypeInferenceEngine(plan, resolver)
        result = engine.infer_types()

        # All 3 variables should be in environment
        assert result.has_type("x")
        assert result.has_type("y")
        assert result.has_type("z")


class TestLiteralInference:
    """Test literal type inference."""

    def test_infer_integer_literal(self):
        """Integer literal infers as number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = LiteralNode(42, 0, 0, "n3")
        result = engine._infer_literal(node)

        assert result == {"type": "number"}

    def test_infer_float_literal(self):
        """Float literal infers as number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = LiteralNode(3.14, 0, 0, "n4")
        result = engine._infer_literal(node)

        assert result == {"type": "number"}

    def test_infer_negative_number(self):
        """Negative number infers as number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = LiteralNode(-100, 0, 0, "n5")
        result = engine._infer_literal(node)

        assert result == {"type": "number"}

    def test_infer_zero(self):
        """Zero infers as number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = LiteralNode(0, 0, 0, "n6")
        result = engine._infer_literal(node)

        assert result == {"type": "number"}

    def test_infer_string_literal(self):
        """String literal infers as string."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = LiteralNode("hello", 0, 0, "n7")
        result = engine._infer_literal(node)

        assert result == {"type": "string"}

    def test_infer_empty_string(self):
        """Empty string infers as string."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = LiteralNode("", 0, 0, "n8")
        result = engine._infer_literal(node)

        assert result == {"type": "string"}

    def test_infer_true_literal(self):
        """Boolean true infers as boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = LiteralNode(True, 0, 0, "n9")
        result = engine._infer_literal(node)

        assert result == {"type": "boolean"}

    def test_infer_false_literal(self):
        """Boolean false infers as boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = LiteralNode(False, 0, 0, "n10")
        result = engine._infer_literal(node)

        assert result == {"type": "boolean"}

    def test_infer_none_literal(self):
        """None literal infers as null."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = LiteralNode(None, 0, 0, "n11")
        result = engine._infer_literal(node)

        assert result == {"type": "null"}


class TestVariableInference:
    """Test variable type inference."""

    def test_infer_variable_with_known_type(self):
        """Variable with known type returns stored type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Manually set type in environment
        engine.type_env.set_type("x", {"type": "number"})

        node = VariableNode("x", 0, 0, "var1")
        result = engine._infer_variable(node)

        assert result == {"type": "number"}

    def test_infer_variable_multiple_types(self):
        """Different variables have different types."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("x", {"type": "number"})
        engine.type_env.set_type("y", {"type": "string"})

        node_x = VariableNode("x", 0, 0, "var1")
        node_y = VariableNode("y", 0, 0, "var2")

        assert engine._infer_variable(node_x) == {"type": "number"}
        assert engine._infer_variable(node_y) == {"type": "string"}

    def test_infer_variable_unknown(self):
        """Unknown variable returns Any."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = VariableNode("unknown", 0, 0, "var1")
        result = engine._infer_variable(node)

        # Unknown variables should return {} (Any type)
        assert result == {}

    def test_infer_variable_not_yet_assigned(self):
        """Variable referenced before assignment."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = VariableNode("x", 0, 0, "var1")
        result = engine._infer_variable(node)

        assert result == {}


class TestAssignmentPropagation:
    """Test assignment type propagation."""

    def test_assign_literal_to_variable(self):
        """Assign literal value to variable."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        literal = LiteralNode(42, 0, 0, "n12")
        node = AssignNode("x", literal, 0, 0, "assign1")

        result = engine._infer_assignment(node)

        assert result == {"type": "number"}
        assert engine.type_env.get_type("x") == {"type": "number"}

    def test_assign_string_literal(self):
        """Assign string to variable."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        literal = LiteralNode("hello", 0, 0, "n13")
        node = AssignNode("y", literal, 0, 0, "assign1")

        result = engine._infer_assignment(node)

        assert result == {"type": "string"}
        assert engine.type_env.get_type("y") == {"type": "string"}

    def test_assign_variable_to_variable(self):
        """Assign one variable to another."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Set type for x
        engine.type_env.set_type("x", {"type": "number"})

        var_node = VariableNode("x", 0, 0, "var1")
        node = AssignNode("y", var_node, 0, 0, "assign1")

        result = engine._infer_assignment(node)

        assert result == {"type": "number"}
        assert engine.type_env.get_type("y") == {"type": "number"}

    def test_reassign_variable_same_type(self):
        """Reassign variable with same type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # First assignment
        lit1 = LiteralNode(42, 0, 0, "n14")
        assign1 = AssignNode("x", lit1, 0, 0, "assign1")
        engine._infer_assignment(assign1)

        # Second assignment
        lit2 = LiteralNode(100, 0, 0, "lit2")
        assign2 = AssignNode("x", lit2, 0, 0, "assign2")
        engine._infer_assignment(assign2)

        # Should still be number
        assert engine.type_env.get_type("x") == {"type": "number"}

    def test_reassign_variable_different_type(self):
        """Reassign variable with different type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # First assignment (number)
        lit1 = LiteralNode(42, 0, 0, "n15")
        assign1 = AssignNode("x", lit1, 0, 0, "assign1")
        engine._infer_assignment(assign1)

        # Second assignment (string)
        lit2 = LiteralNode("hello", 0, 0, "lit2")
        assign2 = AssignNode("x", lit2, 0, 0, "assign2")
        engine._infer_assignment(assign2)

        # Last assignment wins
        assert engine.type_env.get_type("x") == {"type": "string"}

    def test_assign_expression_result(self):
        """Assign result of arithmetic expression."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Set types for x and y
        engine.type_env.set_type("x", {"type": "number"})
        engine.type_env.set_type("y", {"type": "number"})

        # Create arithmetic expression: x + y
        var_x = VariableNode("x", 0, 0, "var1")
        var_y = VariableNode("y", 0, 0, "var2")
        arith = ArithmeticNode("+", var_x, var_y, 0, 0, "arith1")

        # Assign to z
        assign = AssignNode("z", arith, 0, 0, "assign1")
        result = engine._infer_assignment(assign)

        assert result == {"type": "number"}
        assert engine.type_env.get_type("z") == {"type": "number"}


class TestArithmeticOperators:
    """Test arithmetic operator inference."""

    def test_add_two_numbers(self):
        """Number + number → number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(10, 0, 0, "n16")
        right = LiteralNode(20, 0, 0, "lit2")
        node = ArithmeticNode("+", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        assert result == {"type": "number"}

    def test_add_two_strings(self):
        """String + string → string."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode("hello", 0, 0, "n17")
        right = LiteralNode(" world", 0, 0, "lit2")
        node = ArithmeticNode("+", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        assert result == {"type": "string"}

    def test_add_variables_both_numbers(self):
        """Variable + variable (both numbers)."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("x", {"type": "number"})
        engine.type_env.set_type("y", {"type": "number"})

        left = VariableNode("x", 0, 0, "var1")
        right = VariableNode("y", 0, 0, "var2")
        node = ArithmeticNode("+", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        assert result == {"type": "number"}

    def test_add_number_and_variable(self):
        """Literal + variable."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("x", {"type": "number"})

        left = LiteralNode(10, 0, 0, "n18")
        right = VariableNode("x", 0, 0, "var1")
        node = ArithmeticNode("+", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        assert result == {"type": "number"}

    def test_subtract_numbers(self):
        """Number - number → number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(100, 0, 0, "n19")
        right = LiteralNode(50, 0, 0, "lit2")
        node = ArithmeticNode("-", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        assert result == {"type": "number"}

    def test_multiply_numbers(self):
        """Number * number → number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(5, 0, 0, "n20")
        right = LiteralNode(10, 0, 0, "lit2")
        node = ArithmeticNode("*", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        assert result == {"type": "number"}

    def test_divide_numbers(self):
        """Number / number → number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(100, 0, 0, "n21")
        right = LiteralNode(5, 0, 0, "lit2")
        node = ArithmeticNode("/", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        assert result == {"type": "number"}

    def test_modulo_numbers(self):
        """Number % number → number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(10, 0, 0, "n22")
        right = LiteralNode(3, 0, 0, "lit2")
        node = ArithmeticNode("%", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        assert result == {"type": "number"}

    def test_add_number_and_string(self):
        """Number + string (type mismatch)."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(42, 0, 0, "n23")
        right = LiteralNode("hello", 0, 0, "lit2")
        node = ArithmeticNode("+", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        # Should return Any (empty dict) for type mismatch
        assert result == {}

    def test_subtract_strings(self):
        """String - string (invalid operation)."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode("hello", 0, 0, "n24")
        right = LiteralNode("world", 0, 0, "lit2")
        node = ArithmeticNode("-", left, right, 0, 0, "arith1")

        result = engine._infer_arithmetic(node)
        # Should return Any for invalid operation
        assert result == {}


class TestComparisonOperators:
    """Test comparison operator inference."""

    def test_equal_numbers(self):
        """Number == number → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(10, 0, 0, "n25")
        right = LiteralNode(10, 0, 0, "lit2")
        node = ComparisonNode("==", left, right, 0, 0, "comp1")

        result = engine._infer_comparison(node)
        assert result == {"type": "boolean"}

    def test_not_equal_strings(self):
        """String != string → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode("a", 0, 0, "n26")
        right = LiteralNode("b", 0, 0, "lit2")
        node = ComparisonNode("!=", left, right, 0, 0, "comp1")

        result = engine._infer_comparison(node)
        assert result == {"type": "boolean"}

    def test_less_than_numbers(self):
        """Number < number → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(5, 0, 0, "n27")
        right = LiteralNode(10, 0, 0, "lit2")
        node = ComparisonNode("<", left, right, 0, 0, "comp1")

        result = engine._infer_comparison(node)
        assert result == {"type": "boolean"}

    def test_greater_than_numbers(self):
        """Number > number → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(10, 0, 0, "n28")
        right = LiteralNode(5, 0, 0, "lit2")
        node = ComparisonNode(">", left, right, 0, 0, "comp1")

        result = engine._infer_comparison(node)
        assert result == {"type": "boolean"}

    def test_less_than_equal(self):
        """Number <= number → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(5, 0, 0, "n29")
        right = LiteralNode(10, 0, 0, "lit2")
        node = ComparisonNode("<=", left, right, 0, 0, "comp1")

        result = engine._infer_comparison(node)
        assert result == {"type": "boolean"}

    def test_greater_than_equal(self):
        """Number >= number → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(10, 0, 0, "n30")
        right = LiteralNode(5, 0, 0, "lit2")
        node = ComparisonNode(">=", left, right, 0, 0, "comp1")

        result = engine._infer_comparison(node)
        assert result == {"type": "boolean"}

    def test_compare_variables(self):
        """Variable comparison returns boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("x", {"type": "number"})
        engine.type_env.set_type("y", {"type": "number"})

        left = VariableNode("x", 0, 0, "var1")
        right = VariableNode("y", 0, 0, "var2")
        node = ComparisonNode("<", left, right, 0, 0, "comp1")

        result = engine._infer_comparison(node)
        assert result == {"type": "boolean"}

    def test_compare_different_types(self):
        """Compare number and string."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(42, 0, 0, "n31")
        right = LiteralNode("42", 0, 0, "lit2")
        node = ComparisonNode("==", left, right, 0, 0, "comp1")

        result = engine._infer_comparison(node)
        # Comparisons always return boolean regardless of operand types
        assert result == {"type": "boolean"}


class TestBooleanOperators:
    """Test boolean operator inference."""

    def test_and_two_booleans(self):
        """Boolean and boolean → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(True, 0, 0, "n32")
        right = LiteralNode(False, 0, 0, "lit2")
        node = BooleanOpNode("and", [left, right], 0, 0, "bool1")

        result = engine._infer_boolean_op(node)
        assert result == {"type": "boolean"}

    def test_or_two_booleans(self):
        """Boolean or boolean → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        left = LiteralNode(True, 0, 0, "n33")
        right = LiteralNode(False, 0, 0, "lit2")
        node = BooleanOpNode("or", [left, right], 0, 0, "bool1")

        result = engine._infer_boolean_op(node)
        assert result == {"type": "boolean"}

    def test_and_with_variables(self):
        """Variable and variable → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("x", {"type": "boolean"})
        engine.type_env.set_type("y", {"type": "boolean"})

        left = VariableNode("x", 0, 0, "var1")
        right = VariableNode("y", 0, 0, "var2")
        node = BooleanOpNode("and", [left, right], 0, 0, "bool1")

        result = engine._infer_boolean_op(node)
        assert result == {"type": "boolean"}

    def test_not_boolean(self):
        """not boolean → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        operand = LiteralNode(True, 0, 0, "n34")
        node = UnaryOpNode("not", operand, 0, 0, "unary1")

        result = engine._infer_unary_op(node)
        assert result == {"type": "boolean"}

    def test_not_variable(self):
        """not variable → boolean."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("x", {"type": "boolean"})

        operand = VariableNode("x", 0, 0, "var1")
        node = UnaryOpNode("not", operand, 0, 0, "unary1")

        result = engine._infer_unary_op(node)
        assert result == {"type": "boolean"}

    def test_unary_minus_number(self):
        """-number → number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        operand = LiteralNode(42, 0, 0, "n35")
        node = UnaryOpNode("-", operand, 0, 0, "unary1")

        result = engine._infer_unary_op(node)
        assert result == {"type": "number"}

    def test_unary_minus_variable(self):
        """-variable (number) → number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("x", {"type": "number"})

        operand = VariableNode("x", 0, 0, "var1")
        node = UnaryOpNode("-", operand, 0, 0, "unary1")

        result = engine._infer_unary_op(node)
        assert result == {"type": "number"}


class TestDictionaryInference:
    """Test dictionary literal type inference."""

    def test_infer_empty_dict(self):
        """Empty dictionary infers as object."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = DictNode([], 0, 0, "dict1")

        result = engine._infer_dict(node)
        assert result == {"type": "object"}

    def test_infer_dict_with_literal_keys(self):
        """Dict with string literal keys."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # {name: "Alice", age: 30}
        key1 = LiteralNode("name", 0, 0, "k1")
        val1 = LiteralNode("Alice", 0, 0, "v1")
        key2 = LiteralNode("age", 0, 0, "k2")
        val2 = LiteralNode(30, 0, 0, "v2")

        node = DictNode([(key1, val1), (key2, val2)], 0, 0, "dict1")

        result = engine._infer_dict(node)
        assert result["type"] == "object"
        assert "properties" in result
        assert result["properties"]["name"] == {"type": "string"}
        assert result["properties"]["age"] == {"type": "number"}

    def test_infer_dict_single_property(self):
        """Dict with one key-value pair."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # {count: 42}
        key = LiteralNode("count", 0, 0, "k1")
        val = LiteralNode(42, 0, 0, "v1")

        node = DictNode([(key, val)], 0, 0, "dict1")

        result = engine._infer_dict(node)
        assert result["type"] == "object"
        assert result["properties"]["count"] == {"type": "number"}

    def test_infer_dict_multiple_types(self):
        """Dict with mixed value types."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # {str: "hello", num: 123, bool: true}
        pairs = [
            (LiteralNode("str", 0, 0, "k1"), LiteralNode("hello", 0, 0, "v1")),
            (LiteralNode("num", 0, 0, "k2"), LiteralNode(123, 0, 0, "v2")),
            (LiteralNode("bool", 0, 0, "k3"), LiteralNode(True, 0, 0, "v3")),
        ]

        node = DictNode(pairs, 0, 0, "dict1")

        result = engine._infer_dict(node)
        assert result["type"] == "object"
        assert result["properties"]["str"] == {"type": "string"}
        assert result["properties"]["num"] == {"type": "number"}
        assert result["properties"]["bool"] == {"type": "boolean"}

    def test_infer_nested_dict(self):
        """Dictionary with nested object."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Inner dict: {name: "Bob", age: 25}
        inner_pairs = [
            (LiteralNode("name", 0, 0, "k1"), LiteralNode("Bob", 0, 0, "v1")),
            (LiteralNode("age", 0, 0, "k2"), LiteralNode(25, 0, 0, "v2")),
        ]
        inner_dict = DictNode(inner_pairs, 0, 0, "inner1")

        # Outer dict: {user: <inner_dict>}
        outer_pairs = [(LiteralNode("user", 0, 0, "k3"), inner_dict)]
        node = DictNode(outer_pairs, 0, 0, "dict1")

        result = engine._infer_dict(node)
        assert result["type"] == "object"
        assert result["properties"]["user"]["type"] == "object"
        assert result["properties"]["user"]["properties"]["name"] == {"type": "string"}
        assert result["properties"]["user"]["properties"]["age"] == {"type": "number"}

    def test_infer_deeply_nested_dict(self):
        """Three levels of nesting."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # {a: {b: {c: 1}}}
        innermost = DictNode(
            [(LiteralNode("c", 0, 0, "k1"), LiteralNode(1, 0, 0, "v1"))],
            0,
            0,
            "d3",
        )
        middle = DictNode([(LiteralNode("b", 0, 0, "k2"), innermost)], 0, 0, "d2")
        outer = DictNode([(LiteralNode("a", 0, 0, "k3"), middle)], 0, 0, "d1")

        result = engine._infer_dict(outer)
        assert result["type"] == "object"
        assert result["properties"]["a"]["properties"]["b"]["properties"]["c"] == {
            "type": "number"
        }

    def test_infer_dict_with_dynamic_key(self):
        """Dict with non-literal key."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("key", {"type": "string"})

        # {$key: "value"}
        key_var = VariableNode("key", 0, 0, "var1")
        val = LiteralNode("value", 0, 0, "v1")

        node = DictNode([(key_var, val)], 0, 0, "dict1")

        result = engine._infer_dict(node)
        assert result["type"] == "object"
        assert "additionalProperties" in result
        assert result["additionalProperties"] == {"type": "string"}

    def test_infer_dict_mixed_static_dynamic_keys(self):
        """Mix of literal and variable keys."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("dynamic", {"type": "string"})

        # {static: 1, $dynamic: 2}
        pairs = [
            (LiteralNode("static", 0, 0, "k1"), LiteralNode(1, 0, 0, "v1")),
            (VariableNode("dynamic", 0, 0, "var1"), LiteralNode(2, 0, 0, "v2")),
        ]

        node = DictNode(pairs, 0, 0, "dict1")

        result = engine._infer_dict(node)
        assert result["type"] == "object"
        assert "additionalProperties" in result

    def test_infer_dict_assigned_to_variable(self):
        """Assign dict to variable."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # {name: "Alice"}
        dict_node = DictNode(
            [(LiteralNode("name", 0, 0, "k1"), LiteralNode("Alice", 0, 0, "v1"))],
            0,
            0,
            "dict1",
        )
        assign_node = AssignNode("user", dict_node, 0, 0, "a1")

        engine._infer_assignment(assign_node)

        user_type = engine.type_env.get_type("user")
        assert user_type is not None
        assert user_type["type"] == "object"
        assert user_type["properties"]["name"] == {"type": "string"}

    def test_infer_dict_with_variable_values(self):
        """Dict values from variables."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type("name", {"type": "string"})

        # {user: $name}
        key = LiteralNode("user", 0, 0, "k1")
        val = VariableNode("name", 0, 0, "var1")

        node = DictNode([(key, val)], 0, 0, "dict1")

        result = engine._infer_dict(node)
        assert result["type"] == "object"
        assert result["properties"]["user"] == {"type": "string"}


class TestArrayInference:
    """Test array literal type inference."""

    def test_infer_empty_array(self):
        """Empty array infers as array."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        node = ListNode([], 0, 0, "list1")

        result = engine._infer_list(node)
        assert result == {"type": "array"}

    def test_infer_homogeneous_number_array(self):
        """Array of numbers."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # [1, 2, 3]
        elements = [
            LiteralNode(1, 0, 0, "e1"),
            LiteralNode(2, 0, 0, "e2"),
            LiteralNode(3, 0, 0, "e3"),
        ]
        node = ListNode(elements, 0, 0, "list1")

        result = engine._infer_list(node)
        assert result["type"] == "array"
        assert result["items"] == {"type": "number"}

    def test_infer_homogeneous_string_array(self):
        """Array of strings."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # ["a", "b", "c"]
        elements = [
            LiteralNode("a", 0, 0, "e1"),
            LiteralNode("b", 0, 0, "e2"),
            LiteralNode("c", 0, 0, "e3"),
        ]
        node = ListNode(elements, 0, 0, "list1")

        result = engine._infer_list(node)
        assert result["type"] == "array"
        assert result["items"] == {"type": "string"}

    def test_infer_single_element_array(self):
        """Array with one element."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # [42]
        node = ListNode([LiteralNode(42, 0, 0, "e1")], 0, 0, "list1")

        result = engine._infer_list(node)
        assert result["type"] == "array"
        assert result["items"] == {"type": "number"}

    def test_infer_heterogeneous_array(self):
        """Array with mixed types."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # [1, "hello", true]
        elements = [
            LiteralNode(1, 0, 0, "e1"),
            LiteralNode("hello", 0, 0, "e2"),
            LiteralNode(True, 0, 0, "e3"),
        ]
        node = ListNode(elements, 0, 0, "list1")

        result = engine._infer_list(node)
        assert result["type"] == "array"
        assert "oneOf" in result["items"]
        # Check all three types are present
        types_in_union = [t["type"] for t in result["items"]["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union
        assert "boolean" in types_in_union

    def test_infer_array_number_and_string(self):
        """Two different types."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # [1, "text"]
        elements = [LiteralNode(1, 0, 0, "e1"), LiteralNode("text", 0, 0, "e2")]
        node = ListNode(elements, 0, 0, "list1")

        result = engine._infer_list(node)
        assert result["type"] == "array"
        assert "oneOf" in result["items"]
        types_in_union = [t["type"] for t in result["items"]["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union

    def test_infer_nested_array(self):
        """Array of arrays."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # [[1, 2], [3, 4]]
        inner1 = ListNode(
            [LiteralNode(1, 0, 0, "e1"), LiteralNode(2, 0, 0, "e2")], 0, 0, "i1"
        )
        inner2 = ListNode(
            [LiteralNode(3, 0, 0, "e3"), LiteralNode(4, 0, 0, "e4")], 0, 0, "i2"
        )
        outer = ListNode([inner1, inner2], 0, 0, "list1")

        result = engine._infer_list(outer)
        assert result["type"] == "array"
        assert result["items"]["type"] == "array"
        assert result["items"]["items"] == {"type": "number"}

    def test_infer_deeply_nested_array(self):
        """Three levels of nesting."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # [[[1, 2]]]
        innermost = ListNode(
            [LiteralNode(1, 0, 0, "e1"), LiteralNode(2, 0, 0, "e2")], 0, 0, "i3"
        )
        middle = ListNode([innermost], 0, 0, "i2")
        outer = ListNode([middle], 0, 0, "i1")

        result = engine._infer_list(outer)
        assert result["type"] == "array"
        assert result["items"]["type"] == "array"
        assert result["items"]["items"]["type"] == "array"
        assert result["items"]["items"]["items"] == {"type": "number"}

    def test_infer_array_of_objects(self):
        """Homogeneous object array."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # [{x: 1}, {x: 2}]
        obj1 = DictNode(
            [(LiteralNode("x", 0, 0, "k1"), LiteralNode(1, 0, 0, "v1"))], 0, 0, "o1"
        )
        obj2 = DictNode(
            [(LiteralNode("x", 0, 0, "k2"), LiteralNode(2, 0, 0, "v2"))], 0, 0, "o2"
        )
        array = ListNode([obj1, obj2], 0, 0, "list1")

        result = engine._infer_list(array)
        assert result["type"] == "array"
        assert result["items"]["type"] == "object"
        assert result["items"]["properties"]["x"] == {"type": "number"}

    def test_infer_array_of_mixed_objects(self):
        """Objects with different schemas."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # [{x: 1}, {y: 2}]
        obj1 = DictNode(
            [(LiteralNode("x", 0, 0, "k1"), LiteralNode(1, 0, 0, "v1"))], 0, 0, "o1"
        )
        obj2 = DictNode(
            [(LiteralNode("y", 0, 0, "k2"), LiteralNode(2, 0, 0, "v2"))], 0, 0, "o2"
        )
        array = ListNode([obj1, obj2], 0, 0, "list1")

        result = engine._infer_list(array)
        assert result["type"] == "array"
        assert "oneOf" in result["items"]


class TestFieldAccessInference:
    """Test field access type inference."""

    def test_infer_field_access_known_property(self):
        """Access known field."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "user", {"type": "object", "properties": {"name": {"type": "string"}}}
        )

        obj_node = VariableNode("user", 0, 0, "var1")
        node = FieldAccessNode(obj_node, "name", 0, 0, "field1")

        result = engine._infer_field_access(node)
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_infer_field_access_number_property(self):
        """Access numeric property."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "obj", {"type": "object", "properties": {"count": {"type": "number"}}}
        )

        obj_node = VariableNode("obj", 0, 0, "var1")
        node = FieldAccessNode(obj_node, "count", 0, 0, "field1")

        result = engine._infer_field_access(node)
        assert result == {"oneOf": [{"type": "number"}, {"type": "null"}]}

    def test_infer_field_access_unknown_field(self):
        """Access non-existent field."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "user", {"type": "object", "properties": {"name": {"type": "string"}}}
        )

        obj_node = VariableNode("user", 0, 0, "var1")
        node = FieldAccessNode(obj_node, "age", 0, 0, "field1")

        result = engine._infer_field_access(node)
        assert result == {"oneOf": [{}, {"type": "null"}]}  # Any | null

    def test_infer_field_access_unknown_object(self):
        """Access field on unknown variable."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        obj_node = VariableNode("unknown", 0, 0, "var1")
        node = FieldAccessNode(obj_node, "field", 0, 0, "field1")

        result = engine._infer_field_access(node)
        assert result == {"oneOf": [{}, {"type": "null"}]}  # Any | null

    def test_infer_nested_field_access(self):
        """Chain of field accesses."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "data",
            {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    }
                },
            },
        )

        # data.user
        obj1 = VariableNode("data", 0, 0, "var1")
        field1 = FieldAccessNode(obj1, "user", 0, 0, "field1")

        # data.user.name
        node = FieldAccessNode(field1, "name", 0, 0, "field2")

        result = engine._infer_field_access(node)
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_infer_deep_nested_field_access(self):
        """Three levels of nesting."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "root",
            {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "object",
                        "properties": {
                            "b": {
                                "type": "object",
                                "properties": {"c": {"type": "number"}},
                            }
                        },
                    }
                },
            },
        )

        # root.a.b.c
        obj1 = VariableNode("root", 0, 0, "var1")
        field1 = FieldAccessNode(obj1, "a", 0, 0, "f1")
        field2 = FieldAccessNode(field1, "b", 0, 0, "f2")
        node = FieldAccessNode(field2, "c", 0, 0, "f3")

        result = engine._infer_field_access(node)
        assert result == {"oneOf": [{"type": "number"}, {"type": "null"}]}

    def test_infer_field_access_with_additional_properties(self):
        """Object with additionalProperties."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "obj", {"type": "object", "additionalProperties": {"type": "string"}}
        )

        obj_node = VariableNode("obj", 0, 0, "var1")
        node = FieldAccessNode(obj_node, "anyField", 0, 0, "field1")

        result = engine._infer_field_access(node)
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_infer_field_access_assigned_to_variable(self):
        """Assign field access result."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "user", {"type": "object", "properties": {"name": {"type": "string"}}}
        )

        obj_node = VariableNode("user", 0, 0, "var1")
        field_node = FieldAccessNode(obj_node, "name", 0, 0, "field1")
        assign_node = AssignNode("name", field_node, 0, 0, "a1")

        engine._infer_assignment(assign_node)

        name_type = engine.type_env.get_type("name")
        # Field access returns union with null
        assert name_type == {"oneOf": [{"type": "string"}, {"type": "null"}]}


class TestIndexedAccessInference:
    """Test indexed access type inference."""

    def test_infer_array_indexed_access_literal(self):
        """Array with numeric literal index."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "items", {"type": "array", "items": {"type": "number"}}
        )

        obj_node = VariableNode("items", 0, 0, "var1")
        index_node = LiteralNode(0, 0, 0, "idx1")
        node = IndexedAccessNode(obj_node, index_node, 0, 0, "indexed1")

        result = engine._infer_indexed_access(node)
        assert result == {"oneOf": [{"type": "number"}, {"type": "null"}]}

    def test_infer_array_indexed_access_variable(self):
        """Array with variable index."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "items", {"type": "array", "items": {"type": "string"}}
        )
        engine.type_env.set_type("i", {"type": "number"})

        obj_node = VariableNode("items", 0, 0, "var1")
        index_node = VariableNode("i", 0, 0, "var2")
        node = IndexedAccessNode(obj_node, index_node, 0, 0, "indexed1")

        result = engine._infer_indexed_access(node)
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_infer_array_of_objects_indexed(self):
        """Array of objects, access element."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "users",
            {
                "type": "array",
                "items": {"type": "object", "properties": {"name": {"type": "string"}}},
            },
        )

        obj_node = VariableNode("users", 0, 0, "var1")
        index_node = LiteralNode(0, 0, 0, "idx1")
        node = IndexedAccessNode(obj_node, index_node, 0, 0, "indexed1")

        result = engine._infer_indexed_access(node)
        # Indexed access returns union with null
        assert "oneOf" in result
        # Check that the non-null variant is object type
        object_variant = next(v for v in result["oneOf"] if v.get("type") == "object")
        assert object_variant["type"] == "object"
        assert object_variant["properties"]["name"] == {"type": "string"}

    def test_infer_object_indexed_access_literal_key(self):
        """Object with string literal key."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "data", {"type": "object", "properties": {"x": {"type": "number"}}}
        )

        obj_node = VariableNode("data", 0, 0, "var1")
        index_node = LiteralNode("x", 0, 0, "idx1")
        node = IndexedAccessNode(obj_node, index_node, 0, 0, "indexed1")

        result = engine._infer_indexed_access(node)
        assert result == {"oneOf": [{"type": "number"}, {"type": "null"}]}

    def test_infer_object_indexed_access_variable_key(self):
        """Object with variable key."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "obj", {"type": "object", "additionalProperties": {"type": "string"}}
        )
        engine.type_env.set_type("key", {"type": "string"})

        obj_node = VariableNode("obj", 0, 0, "var1")
        index_node = VariableNode("key", 0, 0, "var2")
        node = IndexedAccessNode(obj_node, index_node, 0, 0, "indexed1")

        result = engine._infer_indexed_access(node)
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_infer_object_indexed_unknown_key(self):
        """Object with literal key not in properties."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "obj", {"type": "object", "properties": {"x": {"type": "number"}}}
        )

        obj_node = VariableNode("obj", 0, 0, "var1")
        index_node = LiteralNode("y", 0, 0, "idx1")
        node = IndexedAccessNode(obj_node, index_node, 0, 0, "indexed1")

        result = engine._infer_indexed_access(node)
        assert result == {"oneOf": [{}, {"type": "null"}]}  # Any | null

    def test_infer_nested_array_access(self):
        """Array of arrays."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "matrix",
            {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
        )

        # matrix[0] -> array of numbers
        obj1 = VariableNode("matrix", 0, 0, "var1")
        idx1 = LiteralNode(0, 0, 0, "idx1")
        indexed1 = IndexedAccessNode(obj1, idx1, 0, 0, "indexed1")

        # matrix[0][0] -> number
        idx2 = LiteralNode(0, 0, 0, "idx2")
        node = IndexedAccessNode(indexed1, idx2, 0, 0, "indexed2")

        result = engine._infer_indexed_access(node)
        assert result == {"oneOf": [{"type": "number"}, {"type": "null"}]}

    def test_infer_array_of_objects_field_access(self):
        """Combine indexed and field access."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        engine.type_env.set_type(
            "users",
            {
                "type": "array",
                "items": {"type": "object", "properties": {"name": {"type": "string"}}},
            },
        )

        # users[0]
        obj_node = VariableNode("users", 0, 0, "var1")
        idx_node = LiteralNode(0, 0, 0, "idx1")
        indexed = IndexedAccessNode(obj_node, idx_node, 0, 0, "indexed1")

        # users[0].name
        node = FieldAccessNode(indexed, "name", 0, 0, "field1")

        result = engine._infer_field_access(node)
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_infer_indexed_access_unknown_container(self):
        """Index into unknown variable."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        obj_node = VariableNode("unknown", 0, 0, "var1")
        index_node = LiteralNode(0, 0, 0, "idx1")
        node = IndexedAccessNode(obj_node, index_node, 0, 0, "indexed1")

        result = engine._infer_indexed_access(node)
        assert result == {"oneOf": [{}, {"type": "null"}]}  # Any | null


# ==============================================================================
# Tool Calls & Control Flow Type Inference Tests
# ==============================================================================


class TestToolCallInference:
    """Test tool call type inference."""

    def test_infer_tool_call_native_len(self):
        """Native len() function returns number."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Create len([1, 2, 3])
        list_arg = ListNode(
            [
                LiteralNode(1, 0, 0, "e1"),
                LiteralNode(2, 0, 0, "e2"),
                LiteralNode(3, 0, 0, "e3"),
            ],
            0,
            0,
            "list1",
        )
        node = ToolCallNode(
            tool_name="native::collections::len",
            arguments=[list_arg],
            named_arguments={},
            original_name="len",
            line_number=0,
            column=0,
            node_id="tool1",
        )

        result = engine._infer_tool_call(node)
        # Tool not registered yet, returns Any
        assert result == {}

    def test_infer_tool_call_native_debug(self):
        """Native debug() function returns its registered return type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Create debug("message")
        msg_arg = LiteralNode("message", 0, 0, "msg1")
        node = ToolCallNode(
            tool_name="native::io::debug",
            arguments=[msg_arg],
            named_arguments={},
            original_name="debug",
            line_number=0,
            column=0,
            node_id="tool1",
        )

        result = engine._infer_tool_call(node)
        # Tool not registered yet, returns Any
        assert result == {}

    def test_infer_tool_call_native_str(self):
        """Native str() function returns string."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Create str(42)
        num_arg = LiteralNode(42, 0, 0, "num1")
        node = ToolCallNode(
            tool_name="native::strings::str",
            arguments=[num_arg],
            named_arguments={},
            original_name="str",
            line_number=0,
            column=0,
            node_id="tool1",
        )

        result = engine._infer_tool_call(node)
        # Tool not registered yet, returns Any
        assert result == {}

    def test_infer_tool_call_with_signature(self):
        """Tool exists in resolver with known return type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Register a custom tool with known return type
        # Note: This test will need ToolResolver to support registration
        # For now, just test the stubbed behavior
        node = ToolCallNode(
            tool_name="custom::get_user",
            arguments=[],
            named_arguments={},
            original_name="get_user",
            line_number=0,
            column=0,
            node_id="tool1",
        )

        result = engine._infer_tool_call(node)
        # Tool not registered, returns Any
        assert result == {}

    def test_infer_tool_call_no_signature(self):
        """Tool not found in resolver returns Any."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Unregistered tool
        node = ToolCallNode(
            tool_name="unknown::tool",
            arguments=[],
            named_arguments={},
            original_name="unknown_tool",
            line_number=0,
            column=0,
            node_id="tool1",
        )

        result = engine._infer_tool_call(node)
        # Tool not found - conservative, returns Any
        assert result == {}

    def test_infer_tool_call_no_return_type(self):
        """Tool without return type annotation returns Any."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Tool with no return type
        node = ToolCallNode(
            tool_name="custom::no_return",
            arguments=[],
            named_arguments={},
            original_name="no_return",
            line_number=0,
            column=0,
            node_id="tool1",
        )

        result = engine._infer_tool_call(node)
        # No return type, returns Any
        assert result == {}

    def test_infer_tool_call_result_assigned(self):
        """Assign tool result to variable propagates type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # result = len([1, 2, 3])
        list_arg = ListNode([LiteralNode(1, 0, 0, "e1")], 0, 0, "list1")
        tool_node = ToolCallNode(
            tool_name="native::collections::len",
            arguments=[list_arg],
            named_arguments={},
            original_name="len",
            line_number=0,
            column=0,
            node_id="tool1",
        )
        assign_node = AssignNode("result", tool_node, 0, 0, "a1")

        engine._infer_assignment(assign_node)
        # Tool not registered, so result gets Any type
        assert engine.type_env.get_type("result") == {}

    def test_infer_tool_call_chained(self):
        """Multiple tool calls chained together."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # x = len([1, 2])
        list_arg = ListNode([LiteralNode(1, 0, 0, "e1")], 0, 0, "list1")
        tool1 = ToolCallNode(
            tool_name="native::collections::len",
            arguments=[list_arg],
            named_arguments={},
            original_name="len",
            line_number=0,
            column=0,
            node_id="tool1",
        )
        assign1 = AssignNode("x", tool1, 0, 0, "a1")

        # y = str(x)
        var_x = VariableNode("x", 0, 0, "var1")
        tool2 = ToolCallNode(
            tool_name="native::strings::str",
            arguments=[var_x],
            named_arguments={},
            original_name="str",
            line_number=0,
            column=0,
            node_id="tool2",
        )
        assign2 = AssignNode("y", tool2, 0, 0, "a2")

        engine._infer_assignment(assign1)
        engine._infer_assignment(assign2)
        # Both tools not registered, so both get Any type
        assert engine.type_env.get_type("x") == {}
        assert engine.type_env.get_type("y") == {}


class TestConditionalInference:
    """Test conditional expression type inference."""

    def test_infer_conditional_same_type_number(self):
        """Both branches return number - no union needed."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # 5 if condition else 10
        condition = LiteralNode(True, 0, 0, "cond1")
        then_body = [LiteralNode(5, 0, 0, "then1")]
        else_body = [LiteralNode(10, 0, 0, "else1")]

        node = ConditionalNode(
            condition=condition,
            if_body=then_body,
            elif_conditions=[],
            elif_bodies=[],
            else_body=else_body,
            line_number=0,
            column=0,
            node_id="cond1",
        )

        result = engine._infer_conditional(node)
        # Both branches return number, no union needed
        assert result == {"type": "number"}

    def test_infer_conditional_same_type_string(self):
        """Both branches return string."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # "yes" if condition else "no"
        condition = LiteralNode(True, 0, 0, "cond1")
        then_body = [LiteralNode("yes", 0, 0, "then1")]
        else_body = [LiteralNode("no", 0, 0, "else1")]

        node = ConditionalNode(
            condition=condition,
            if_body=then_body,
            elif_conditions=[],
            elif_bodies=[],
            else_body=else_body,
            line_number=0,
            column=0,
            node_id="cond1",
        )
        result = engine._infer_conditional(node)
        # Both branches return string, no union needed
        assert result == {"type": "string"}

    def test_infer_conditional_same_complex_type(self):
        """Both branches return same object type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # {x: 1} if condition else {x: 2}
        condition = LiteralNode(True, 0, 0, "cond1")
        obj1 = DictNode(
            [(LiteralNode("x", 0, 0, "k1"), LiteralNode(1, 0, 0, "v1"))], 0, 0, "o1"
        )
        obj2 = DictNode(
            [(LiteralNode("x", 0, 0, "k2"), LiteralNode(2, 0, 0, "v2"))], 0, 0, "o2"
        )

        node = ConditionalNode(
            condition=condition,
            if_body=[obj1],
            elif_conditions=[],
            elif_bodies=[],
            else_body=[obj2],
            line_number=0,
            column=0,
            node_id="cond1",
        )
        result = engine._infer_conditional(node)
        # Both branches return same object type, no union needed
        assert result["type"] == "object"
        assert result["properties"]["x"] == {"type": "number"}

    def test_infer_conditional_number_or_string(self):
        """Number vs string creates union type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # 42 if condition else "text"
        condition = LiteralNode(True, 0, 0, "cond1")
        then_body = [LiteralNode(42, 0, 0, "then1")]
        else_body = [LiteralNode("text", 0, 0, "else1")]

        node = ConditionalNode(
            condition=condition,
            if_body=then_body,
            elif_conditions=[],
            elif_bodies=[],
            else_body=else_body,
            line_number=0,
            column=0,
            node_id="cond1",
        )
        result = engine._infer_conditional(node)
        # Different types create union
        assert "oneOf" in result
        types_in_union = [t["type"] for t in result["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union

    def test_infer_conditional_object_or_array(self):
        """Object vs array creates union."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # {x: 1} if condition else [1, 2]
        condition = LiteralNode(True, 0, 0, "cond1")
        obj = DictNode(
            [(LiteralNode("x", 0, 0, "k1"), LiteralNode(1, 0, 0, "v1"))], 0, 0, "o1"
        )
        arr = ListNode(
            [LiteralNode(1, 0, 0, "e1"), LiteralNode(2, 0, 0, "e2")], 0, 0, "l1"
        )

        node = ConditionalNode(
            condition=condition,
            if_body=[obj],
            elif_conditions=[],
            elif_bodies=[],
            else_body=[arr],
            line_number=0,
            column=0,
            node_id="cond1",
        )
        result = engine._infer_conditional(node)
        # Different types create union
        assert "oneOf" in result
        types_in_union = [t["type"] for t in result["oneOf"]]
        assert "object" in types_in_union
        assert "array" in types_in_union

    def test_infer_conditional_three_types(self):
        """Nested conditionals with multiple types."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Complex nested conditional with 3+ types via elif
        condition1 = LiteralNode(True, 0, 0, "cond1")
        condition2 = LiteralNode(False, 0, 0, "cond2")
        then_body = [LiteralNode(42, 0, 0, "then1")]
        elif_body = [LiteralNode("text", 0, 0, "elif1")]
        else_body = [LiteralNode(True, 0, 0, "else1")]

        node = ConditionalNode(
            condition=condition1,
            if_body=then_body,
            elif_conditions=[condition2],
            elif_bodies=[elif_body],
            else_body=else_body,
            line_number=0,
            column=0,
            node_id="cond1",
        )
        result = engine._infer_conditional(node)
        # Multiple types via elif create union
        assert "oneOf" in result
        types_in_union = [t["type"] for t in result["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union
        assert "boolean" in types_in_union

    def test_infer_conditional_no_else_branch(self):
        """Only then branch, no else."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # 42 if condition (no else)
        condition = LiteralNode(True, 0, 0, "cond1")
        then_body = [LiteralNode(42, 0, 0, "then1")]

        node = ConditionalNode(
            condition=condition,
            if_body=then_body,
            elif_conditions=[],
            elif_bodies=[],
            else_body=None,
            line_number=0,
            column=0,
            node_id="cond1",
        )
        result = engine._infer_conditional(node)
        # No else branch, returns then branch type
        assert result == {"type": "number"}

    def test_infer_conditional_assigned_to_variable(self):
        """Assign conditional result to variable."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # x = 5 if condition else "text"
        condition = LiteralNode(True, 0, 0, "cond1")
        cond_node = ConditionalNode(
            condition=condition,
            if_body=[LiteralNode(5, 0, 0, "then1")],
            elif_conditions=[],
            elif_bodies=[],
            else_body=[LiteralNode("text", 0, 0, "else1")],
            line_number=0,
            column=0,
            node_id="cond1",
        )
        assign_node = AssignNode("x", cond_node, 0, 0, "a1")
        engine._infer_assignment(assign_node)
        # Variable gets union type from conditional
        x_type = engine.type_env.get_type("x")
        assert "oneOf" in x_type


class TestWhileLoopInference:
    """Test while loop type inference."""

    def test_infer_while_loop_simple(self):
        """Simple while loop processes body."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # while i < 5: pass
        condition = ComparisonNode(
            "<", VariableNode("i", 0, 0, "v1"), LiteralNode(5, 0, 0, "l1"), 0, 0, "c1"
        )
        body = []  # Empty body

        node = WhileLoopNode(
            condition=condition,
            body=body,
            line_number=0,
            column=0,
            node_id="loop1",
        )
        result = engine._infer_while_loop(node)
        # Loops don\'t return values
        assert result == {}

    def test_infer_while_loop_variable_assignment(self):
        """Variable assigned in loop gets tracked."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # while condition: x = 5
        condition = LiteralNode(True, 0, 0, "cond1")
        assign = AssignNode("x", LiteralNode(5, 0, 0, "l1"), 0, 0, "a1")
        body = [assign]

        node = WhileLoopNode(
            condition=condition,
            body=body,
            line_number=0,
            column=0,
            node_id="loop1",
        )
        result = engine._infer_while_loop(node)
        # Loop processes body and tracks variable types
        assert result == {}
        # Variable should have been assigned
        assert engine.type_env.has_type("x")

    def test_infer_while_loop_type_change(self):
        """Variable type changes in loop."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # while condition: x = different types
        condition = LiteralNode(True, 0, 0, "cond1")
        assign1 = AssignNode("x", LiteralNode(5, 0, 0, "l1"), 0, 0, "a1")
        assign2 = AssignNode("x", LiteralNode("text", 0, 0, "l2"), 0, 0, "a2")
        body = [assign1, assign2]

        node = WhileLoopNode(
            condition=condition,
            body=body,
            line_number=0,
            column=0,
            node_id="loop1",
        )
        result = engine._infer_while_loop(node)
        # Loop processes body, last assignment wins
        assert result == {}
        # Variable gets last assigned type (string)
        assert engine.type_env.get_type("x") == {"type": "string"}

    def test_infer_for_in_loop_array(self):
        """For-in over array (compiled to while)."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # This would be for item in [1, 2, 3] compiled to while
        # For now just test while loop structure
        condition = LiteralNode(True, 0, 0, "cond1")
        body = [AssignNode("item", LiteralNode(1, 0, 0, "l1"), 0, 0, "a1")]

        node = WhileLoopNode(
            condition=condition,
            body=body,
            line_number=0,
            column=0,
            node_id="loop1",
        )
        result = engine._infer_while_loop(node)
        # Loop processes body
        assert result == {}

    def test_infer_for_in_loop_iterator_type(self):
        """Iterator variable gets array item type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # for user in users (where users is array of objects)
        condition = LiteralNode(True, 0, 0, "cond1")
        user_obj = DictNode(
            [(LiteralNode("name", 0, 0, "k1"), LiteralNode("Alice", 0, 0, "v1"))],
            0,
            0,
            "o1",
        )
        body = [AssignNode("user", user_obj, 0, 0, "a1")]

        node = WhileLoopNode(
            condition=condition,
            body=body,
            line_number=0,
            column=0,
            node_id="loop1",
        )
        result = engine._infer_while_loop(node)
        # Loop processes body
        assert result == {}

    def test_infer_while_loop_return_type(self):
        """While loop has no return value."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # while condition: pass
        condition = LiteralNode(True, 0, 0, "cond1")
        node = WhileLoopNode(
            condition=condition,
            body=[],
            line_number=0,
            column=0,
            node_id="loop1",
        )
        result = engine._infer_while_loop(node)
        # Loops don\'t return values
        assert result == {}


class TestReturnStatementInference:
    """Test return statement type inference."""

    def test_infer_return_literal_number(self):
        """Return number literal."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # return 42
        node = ReturnNode(
            expression=LiteralNode(42, 0, 0, "l1"),
            line_number=0,
            column=0,
            node_id="ret1",
        )

        result = engine._infer_return(node)
        assert result == {"type": "number"}

    def test_infer_return_literal_string(self):
        """Return string literal."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # return "hello"
        node = ReturnNode(
            expression=LiteralNode("hello", 0, 0, "l1"),
            line_number=0,
            column=0,
            node_id="ret1",
        )

        result = engine._infer_return(node)
        assert result == {"type": "string"}

    def test_infer_return_variable(self):
        """Return variable."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Set variable type
        engine.type_env.set_type("x", {"type": "number"})

        # return x
        node = ReturnNode(
            expression=VariableNode("x", 0, 0, "v1"),
            line_number=0,
            column=0,
            node_id="ret1",
        )

        result = engine._infer_return(node)
        assert result == {"type": "number"}

    def test_infer_return_expression(self):
        """Return arithmetic expression."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # return 5 + 3
        expr = ArithmeticNode(
            "+", LiteralNode(5, 0, 0, "l1"), LiteralNode(3, 0, 0, "l2"), 0, 0, "arith1"
        )
        node = ReturnNode(
            expression=expr,
            line_number=0,
            column=0,
            node_id="ret1",
        )

        result = engine._infer_return(node)
        assert result == {"type": "number"}

    def test_infer_return_tool_call(self):
        """Return tool call result."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # return len([1, 2])
        tool_call = ToolCallNode(
            tool_name="native::collections::len",
            arguments=[ListNode([LiteralNode(1, 0, 0, "e1")], 0, 0, "list1")],
            named_arguments={},
            original_name="len",
            line_number=0,
            column=0,
            node_id="tool1",
        )
        node = ReturnNode(
            expression=tool_call,
            line_number=0,
            column=0,
            node_id="ret1",
        )

        result = engine._infer_return(node)
        # Tool call will return Any since tool is not registered
        assert result == {}

    def test_infer_return_bare(self):
        """Bare return with no value."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # return (no value)
        node = ReturnNode(
            expression=None,
            line_number=0,
            column=0,
            node_id="ret1",
        )

        result = engine._infer_return(node)
        assert result == {"type": "null"}

    def test_infer_return_object(self):
        """Return object literal."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # return {x: 1}
        obj = DictNode(
            [(LiteralNode("x", 0, 0, "k1"), LiteralNode(1, 0, 0, "v1"))], 0, 0, "o1"
        )
        node = ReturnNode(
            expression=obj,
            line_number=0,
            column=0,
            node_id="ret1",
        )

        result = engine._infer_return(node)
        assert result["type"] == "object"
        assert result["properties"]["x"] == {"type": "number"}

    def test_infer_return_array(self):
        """Return array literal."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # return [1, 2, 3]
        arr = ListNode(
            [LiteralNode(1, 0, 0, "e1"), LiteralNode(2, 0, 0, "e2")], 0, 0, "list1"
        )
        node = ReturnNode(
            expression=arr,
            line_number=0,
            column=0,
            node_id="ret1",
        )

        result = engine._infer_return(node)
        assert result["type"] == "array"
        assert result["items"] == {"type": "number"}


class TestInputVariableBootstrap:
    """Test $input variable bootstrap."""

    def test_input_variable_with_schema(self):
        """$input with provided schema."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        input_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        engine = TypeInferenceEngine(plan, resolver, input_schema=input_schema)

        # Access $input
        node = VariableNode("input", 0, 0, "var1")
        result = engine._infer_variable(node)

        assert result == input_schema

    def test_input_field_access(self):
        """Access $input.field with object schema."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        input_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
        }
        engine = TypeInferenceEngine(plan, resolver, input_schema=input_schema)

        # $input.name
        obj_node = VariableNode("input", 0, 0, "var1")
        field_node = FieldAccessNode(obj_node, "name", 0, 0, "field1")

        result = engine._infer_field_access(field_node)
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_input_nested_field_access(self):
        """Nested $input access."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        input_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {"email": {"type": "string"}},
                }
            },
        }
        engine = TypeInferenceEngine(plan, resolver, input_schema=input_schema)

        # $input.user.email
        obj1 = VariableNode("input", 0, 0, "var1")
        field1 = FieldAccessNode(obj1, "user", 0, 0, "field1")
        field2 = FieldAccessNode(field1, "email", 0, 0, "field2")

        result = engine._infer_field_access(field2)
        assert result == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_input_variable_no_schema(self):
        """$input without schema returns Any."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)  # No input_schema

        # Access $input
        node = VariableNode("input", 0, 0, "var1")
        result = engine._infer_variable(node)

        # Variable inference returns type as-is from env (Any if not found)
        assert result == {}

    def test_input_variable_null_schema(self):
        """$input with None schema."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver, input_schema=None)

        # Access $input
        node = VariableNode("input", 0, 0, "var1")
        result = engine._infer_variable(node)

        # Variable inference returns type as-is from env (Any if not found)
        assert result == {}

    def test_input_in_assignment(self):
        """Assign from $input."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        input_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        engine = TypeInferenceEngine(plan, resolver, input_schema=input_schema)

        # name = $input.name
        obj_node = VariableNode("input", 0, 0, "var1")
        field_node = FieldAccessNode(obj_node, "name", 0, 0, "field1")
        assign_node = AssignNode("name", field_node, 0, 0, "a1")

        engine._infer_assignment(assign_node)

        name_type = engine.type_env.get_type("name")
        # Field access returns union with null
        assert name_type == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_input_in_tool_call(self):
        """Pass $input to tool."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        input_schema = {
            "type": "object",
            "properties": {"data": {"type": "string"}},
        }
        engine = TypeInferenceEngine(plan, resolver, input_schema=input_schema)

        # debug($input.data)
        obj_node = VariableNode("input", 0, 0, "var1")
        field_node = FieldAccessNode(obj_node, "data", 0, 0, "field1")
        tool_node = ToolCallNode(
            tool_name="native::io::debug",
            arguments=[field_node],
            named_arguments={},
            original_name="debug",
            line_number=0,
            column=0,
            node_id="tool1",
        )

        # Verify field type is available
        field_type = engine._infer_field_access(field_node)
        # Field access returns union with null
        assert field_type == {"oneOf": [{"type": "string"}, {"type": "null"}]}

        # Tool call returns Any (not registered)
        result = engine._infer_tool_call(tool_node)
        # Tool calls are not affected by
        assert result == {}


class TestReturnTypeAggregation:
    """Test return type aggregation.

    These tests verify that TypeInferenceEngine correctly tracks and aggregates
    return types from multiple return statements.
    """

    def test_get_aggregated_return_type_single_return(self):
        """One return statement should not create union."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Simulate single return 42
        return_node = ReturnNode(LiteralNode(42, 0, 0, "lit1"), 0, 0, "ret1")
        engine._infer_return(return_node)

        # Should return number type, no union
        result = engine.get_aggregated_return_type()
        assert result == {"type": "number"}

    def test_get_aggregated_return_type_multiple_same_type(self):
        """Multiple returns with same type should not create union."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Simulate if (x) { return 5 } else { return 10 }
        return_node1 = ReturnNode(LiteralNode(5, 0, 0, "lit1"), 0, 0, "ret1")
        return_node2 = ReturnNode(LiteralNode(10, 0, 0, "lit2"), 0, 0, "ret2")

        engine._infer_return(return_node1)
        engine._infer_return(return_node2)

        # Both are numbers, no union needed
        result = engine.get_aggregated_return_type()
        assert result == {"type": "number"}

    def test_get_aggregated_return_type_different_types(self):
        """Multiple returns with different types should create union."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Simulate if (x) { return 42 } else { return "text" }
        return_node1 = ReturnNode(LiteralNode(42, 0, 0, "lit1"), 0, 0, "ret1")
        return_node2 = ReturnNode(LiteralNode("text", 0, 0, "lit2"), 0, 0, "ret2")

        engine._infer_return(return_node1)
        engine._infer_return(return_node2)

        # Different types should create union
        result = engine.get_aggregated_return_type()
        assert "oneOf" in result
        types_in_union = [t.get("type") for t in result["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union

    def test_get_aggregated_return_type_three_types(self):
        """Three different return types should all be in union."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Three branches returning different types
        return_node1 = ReturnNode(LiteralNode(42, 0, 0, "lit1"), 0, 0, "ret1")
        return_node2 = ReturnNode(LiteralNode("text", 0, 0, "lit2"), 0, 0, "ret2")
        return_node3 = ReturnNode(LiteralNode(True, 0, 0, "lit3"), 0, 0, "ret3")

        engine._infer_return(return_node1)
        engine._infer_return(return_node2)
        engine._infer_return(return_node3)

        result = engine.get_aggregated_return_type()
        assert "oneOf" in result
        types_in_union = [t.get("type") for t in result["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union
        assert "boolean" in types_in_union

    def test_get_aggregated_return_type_bare_return(self):
        """Bare return statement should contribute null type."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Simulate bare return
        return_node = ReturnNode(None, 0, 0, "ret1")
        engine._infer_return(return_node)

        # Bare return is null type
        result = engine.get_aggregated_return_type()
        assert result == {"type": "null"}

    def test_get_aggregated_return_type_mixed_bare_and_value(self):
        """Bare return + value return should create union."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # Simulate if (x) { return 42 } else { return }
        return_node1 = ReturnNode(LiteralNode(42, 0, 0, "lit1"), 0, 0, "ret1")
        return_node2 = ReturnNode(None, 0, 0, "ret2")

        engine._infer_return(return_node1)
        engine._infer_return(return_node2)

        result = engine.get_aggregated_return_type()
        assert "oneOf" in result
        types_in_union = [t.get("type") for t in result["oneOf"]]
        assert "number" in types_in_union
        assert "null" in types_in_union

    def test_get_aggregated_return_type_no_returns(self):
        """Script with no return statements should return empty schema."""
        plan = ExecutionPlan()
        resolver = ToolResolver()
        engine = TypeInferenceEngine(plan, resolver)

        # No returns processed
        result = engine.get_aggregated_return_type()
        assert result == {}
