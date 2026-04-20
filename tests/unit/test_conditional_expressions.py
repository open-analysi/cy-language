"""Tests for conditional expressions (ternary-like if/elif/else expressions).

Extension: Conditional expressions leverage the ConditionalNode
type inference to create union types when branches have different types.
"""

from cy_language.compiler import PlanCompiler
from cy_language.parser import Parser
from cy_language.tool_resolver import ToolResolver
from cy_language.type_inference_engine import TypeInferenceEngine


class TestConditionalExpressions:
    """Test conditional expressions with type inference."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = Parser()
        self.tool_resolver = ToolResolver()
        self.compiler = PlanCompiler(tool_resolver=self.tool_resolver)

    def test_simple_conditional_same_type(self):
        """Conditional expression with same type in both branches."""
        code = """
score = 85
grade = if (score >= 90) { "A" } else { "B" }
output = grade
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        grade_type = type_env.get_type("grade")
        assert grade_type == {"type": "string"}

    def test_conditional_with_union_type(self):
        """Conditional expression creates union type for different types."""
        code = """
flag = True
mixed = if (flag) { 42 } else { "text" }
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        mixed_type = type_env.get_type("mixed")
        assert "oneOf" in mixed_type
        types_in_union = [t.get("type") for t in mixed_type["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union

    def test_conditional_with_elif(self):
        """Conditional expression with elif creates union when needed."""
        code = """
score = 75
grade = if (score >= 90) { "A" } elif (score >= 80) { "B" } else { "C" }
output = grade
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        grade_type = type_env.get_type("grade")
        # All branches return strings, so no union needed
        assert grade_type == {"type": "string"}

    def test_conditional_elif_mixed_types(self):
        """Conditional with elif and mixed types creates union."""
        code = """
x = 5
result = if (x > 10) { "large" } elif (x > 5) { 100 } else { False }
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        result_type = type_env.get_type("result")
        assert "oneOf" in result_type
        types_in_union = [t.get("type") for t in result_type["oneOf"]]
        assert "string" in types_in_union
        assert "number" in types_in_union
        assert "boolean" in types_in_union

    def test_nested_conditional_expressions(self):
        """Nested conditional expressions work correctly."""
        code = """
x = 10
result = if (x > 5) { if (x > 8) { "large" } else { "medium" } } else { "small" }
output = result
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        result_type = type_env.get_type("result")
        # All nested branches return strings
        assert result_type == {"type": "string"}

    def test_conditional_in_assignment(self):
        """Conditional expression can be assigned to variable."""
        code = """
age = 25
status = if (age >= 18) { "adult" } else { "minor" }
output = status
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        status_type = type_env.get_type("status")
        assert status_type == {"type": "string"}

    def test_conditional_number_or_boolean(self):
        """Conditional with number or boolean creates union."""
        code = """
check = True
value = if (check) { 100 } else { False }
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        value_type = type_env.get_type("value")
        assert "oneOf" in value_type
        types_in_union = [t.get("type") for t in value_type["oneOf"]]
        assert "number" in types_in_union
        assert "boolean" in types_in_union

    def test_conditional_with_arrays(self):
        """Conditional returning arrays of same type."""
        code = """
flag = True
items = if (flag) { [1, 2, 3] } else { [4, 5, 6] }
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        items_type = type_env.get_type("items")
        # Both branches return array of numbers
        assert items_type == {"type": "array", "items": {"type": "number"}}

    def test_conditional_with_objects(self):
        """Conditional returning objects creates union if structures differ."""
        code = """
flag = True
obj = if (flag) { {"a": 1} } else { {"b": "text"} }
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        obj_type = type_env.get_type("obj")
        # Different object structures create union
        assert "oneOf" in obj_type

    def test_conditional_in_arithmetic(self):
        """Conditional expression can be used in arithmetic."""
        code = """
x = 5
result = (if (x > 3) { 10 } else { 20 }) + 5
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        result_type = type_env.get_type("result")
        # Number + number = number
        assert result_type == {"type": "number"}

    def test_conditional_all_branches_same_complex_type(self):
        """All branches with same object structure returns that structure."""
        code = """
x = 5
obj = if (x > 10) { {"name": "A", "value": 1} } elif (x > 5) { {"name": "B", "value": 2} } else { {"name": "C", "value": 3} }
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        obj_type = type_env.get_type("obj")
        # All have same structure: {"name": string, "value": number}
        assert obj_type["type"] == "object"
        assert "properties" in obj_type
        assert obj_type["properties"]["name"] == {"type": "string"}
        assert obj_type["properties"]["value"] == {"type": "number"}

    def test_conditional_multiple_elif_same_type(self):
        """Multiple elif branches with same type."""
        code = """
score = 75
grade = if (score >= 90) { "A" } elif (score >= 80) { "B" } elif (score >= 70) { "C" } elif (score >= 60) { "D" } else { "F" }
output = grade
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        grade_type = type_env.get_type("grade")
        # All branches return string
        assert grade_type == {"type": "string"}

    def test_conditional_expression_vs_statement(self):
        """Ensure conditional expression differs from conditional statement."""
        # Conditional EXPRESSION (returns value)
        expr_code = """
result = if (True) { 42 } else { 0 }
output = "done"
"""
        # Conditional STATEMENT (assigns in branches)
        stmt_code = """
result = 0
if (True) {
    result = 42
} else {
    result = 0
}
output = "done"
"""
        # Parse and compile both
        expr_ast = self.parser.parse_only(expr_code)
        expr_plan = self.compiler.compile(expr_ast)

        stmt_ast = self.parser.parse_only(stmt_code)
        stmt_plan = self.compiler.compile(stmt_ast)

        # Expression version should have fewer nodes (no separate assignments)
        # Expression: assign(result, ConditionalNode) = 1 node
        # Statement: assign(result, 0), ConditionalNode with 2 assigns = 3 nodes
        assert len(expr_plan.nodes) < len(stmt_plan.nodes)

    def test_conditional_empty_branches_not_allowed(self):
        """Conditional expression requires expressions in all branches."""
        # This should parse but we're testing the structure
        # (Empty branches would be a grammar error, not tested here)
        pass
