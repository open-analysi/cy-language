"""
Integration tests for Type Inference Engine.

Tests verify end-to-end type inference on complete Cy scripts,
focusing on literals, variables, assignments, and simple expressions.
"""

from cy_language.compiler import compile_cy_program
from cy_language.parser import Parser
from cy_language.tool_resolver import ToolResolver
from cy_language.type_inference_engine import TypeInferenceEngine


class TestSimpleScriptInference:
    """Test type inference on complete simple scripts."""

    def test_literal_only_script(self):
        """Infer types from script with literal assignments."""
        code = """
x = 42
y = "hello"
output = x
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Should have inferred all variables
        assert type_env.get_type("x") == {"type": "number"}
        assert type_env.get_type("y") == {"type": "string"}

    def test_assignment_chain_inference(self):
        """Infer types through chain of assignments."""
        code = """
        x = 42
        y = x
        z = y
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # All variables should be inferred as number
        assert type_env.get_type("x") == {"type": "number"}
        assert type_env.get_type("y") == {"type": "number"}
        assert type_env.get_type("z") == {"type": "number"}

    def test_arithmetic_expression_inference(self):
        """Infer types from arithmetic expressions."""
        code = """
        a = 10
        b = 20
        sum = a + b
        diff = a - b
        product = a * b
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # All should be inferred as number
        assert type_env.get_type("a") == {"type": "number"}
        assert type_env.get_type("b") == {"type": "number"}
        assert type_env.get_type("sum") == {"type": "number"}
        assert type_env.get_type("diff") == {"type": "number"}
        assert type_env.get_type("product") == {"type": "number"}

    def test_comparison_inference(self):
        """Infer boolean types from comparisons."""
        code = """
        x = 10
        y = 20
        is_equal = x == y
        is_less = x < y
        is_greater_equal = x >= y
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Numbers should be number, comparisons should be boolean
        assert type_env.get_type("x") == {"type": "number"}
        assert type_env.get_type("y") == {"type": "number"}
        assert type_env.get_type("is_equal") == {"type": "boolean"}
        assert type_env.get_type("is_less") == {"type": "boolean"}
        assert type_env.get_type("is_greater_equal") == {"type": "boolean"}

    def test_boolean_logic_inference(self):
        """Infer types from boolean operations."""
        code = """
x = 10
y = 20
is_less = x < y
is_greater = x > y
result_and = is_less and is_greater
result_or = is_less or is_greater
result_not = not is_less
output = result_not
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Comparisons and boolean operations should be boolean
        assert type_env.get_type("is_less") == {"type": "boolean"}
        assert type_env.get_type("is_greater") == {"type": "boolean"}
        assert type_env.get_type("result_and") == {"type": "boolean"}
        assert type_env.get_type("result_or") == {"type": "boolean"}
        assert type_env.get_type("result_not") == {"type": "boolean"}

    def test_mixed_types_inference(self):
        """Infer types from script with mixed types."""
        code = """
num = 42
text = "hello"
comparison = num > 10
result = num + 10
message = text
output = message
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify each type is correctly inferred
        assert type_env.get_type("num") == {"type": "number"}
        assert type_env.get_type("text") == {"type": "string"}
        assert type_env.get_type("comparison") == {"type": "boolean"}
        assert type_env.get_type("result") == {"type": "number"}
        assert type_env.get_type("message") == {"type": "string"}

    def test_string_concatenation_inference(self):
        """Infer string type from + operator on strings."""
        code = """
        first = "Hello"
        second = "World"
        greeting = first + " " + second
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # All should be string
        assert type_env.get_type("first") == {"type": "string"}
        assert type_env.get_type("second") == {"type": "string"}
        assert type_env.get_type("greeting") == {"type": "string"}

    def test_null_literal_inference(self):
        """Infer null type from null literal."""
        code = """
        empty = null
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Should be inferred as null
        assert type_env.get_type("empty") == {"type": "null"}

    def test_unary_minus_inference(self):
        """Infer number type from unary minus."""
        code = """
        x = 10
        negated = -x
        double_neg = -(-5)
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # All should be number
        assert type_env.get_type("x") == {"type": "number"}
        assert type_env.get_type("negated") == {"type": "number"}
        assert type_env.get_type("double_neg") == {"type": "number"}

    def test_complex_expression_inference(self):
        """Infer types from complex nested expressions."""
        code = """
        a = 10
        b = 20
        c = 30
        result = (a + b) * c - (a / 2)
        is_positive = result > 0
        final = is_positive and (a < b)
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Numbers and booleans
        assert type_env.get_type("a") == {"type": "number"}
        assert type_env.get_type("b") == {"type": "number"}
        assert type_env.get_type("c") == {"type": "number"}
        assert type_env.get_type("result") == {"type": "number"}
        assert type_env.get_type("is_positive") == {"type": "boolean"}
        assert type_env.get_type("final") == {"type": "boolean"}
