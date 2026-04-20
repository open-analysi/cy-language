"""Unit tests for enhanced TypeInferenceEngine with inline validation.

Tests verify that TypeInferenceEngine with check_types=True performs
inline validation during type inference in a single pass.

Following TDD: All tests should FAIL initially.
"""

import pytest

from cy_language.compiler import compile_cy_program
from cy_language.parser import Parser
from cy_language.tool_resolver import ToolResolver
from cy_language.type_inference_engine import TypeInferenceEngine


class TestSinglePassArchitecture:
    """Test single-pass architecture (inference + validation)."""

    def test_type_inference_engine_check_types_false(self):
        """Test that check_types=False behaves as before (no validation)."""
        code = """
result = 5 + "text"
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        # With check_types=False, should not raise even with invalid operations
        engine = TypeInferenceEngine(plan, tool_resolver, check_types=False)
        type_env = engine.infer_types()

        # Should complete without error
        assert type_env is not None

    def test_type_inference_engine_check_types_true_valid(self):
        """Test that check_types=True with valid code works."""
        code = """
a = 5
b = 3
result = a + b
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        # With check_types=True and valid code, should not raise
        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)
        type_env = engine.infer_types()

        assert type_env is not None

    def test_type_inference_engine_check_types_true_invalid(self):
        """Test that check_types=True with invalid code raises TypeError."""
        code = """
result = 5 + "text"
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        # With check_types=True and invalid code, should raise TypeError
        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError):
            engine.infer_types()

    def test_type_inference_engine_collects_errors(self):
        """Test that self.type_errors list accumulates errors."""
        code = """
e1 = 5 + "text"
e2 = "hello" - "world"
return e1
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        # Should have collected multiple errors
        error_msg = str(exc_info.value)
        # Verify it mentions multiple issues or contains multiple error indicators
        assert len(error_msg) > 50  # Multiple errors = longer message


class TestInlineValidation:
    """Test that inline validation works in infer_*() methods."""

    def test_infer_arithmetic_validates_inline(self):
        """Test that infer_arithmetic() validates when check_types=True."""
        code = """
invalid = 5 + "text"
return invalid
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert (
            "add" in str(exc_info.value).lower()
            or "cannot" in str(exc_info.value).lower()
        )

    def test_infer_comparison_validates_inline(self):
        """Test that infer_comparison() validates when check_types=True."""
        code = """
invalid = 5 < "text"
return invalid
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "compar" in str(exc_info.value).lower()

    def test_infer_boolean_op_truthy_falsy(self):
        """Test that boolean ops support truthy/falsy semantics (no validation)."""
        code = """
result = 5 and 10
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        # Should NOT raise - truthy/falsy semantics allowed
        type_env = engine.infer_types()
        assert type_env is not None

    def test_infer_field_access_validates_inline(self):
        """Test that infer_field_access() validates when check_types=True.

        Field access with safe navigation returns null for missing fields.
        Using nullable values in operations requires ?? operator.
        """
        code = """
val = null
# Cannot add null to number without ?? operator
invalid = val + 5
return invalid
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        # Error message suggests using ?? operator
        assert "nullable" in str(exc_info.value).lower() or "??" in str(exc_info.value)

    def test_infer_indexed_access_validates_inline(self):
        """Test that infer_indexed_access() validates when check_types=True."""
        code = """
items = ["a", "b"]
invalid = items["key"]
return invalid
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert (
            "index" in str(exc_info.value).lower()
            or "array" in str(exc_info.value).lower()
        )

    def test_infer_conditional_validates_inline(self):
        """Test that conditional inference validates condition types."""
        # Note: Python-like truthy/falsy should be allowed (any type is valid)
        code = """
if ("string") {
    result = "yes"
} else {
    result = "no"
}
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        # Truthy/falsy semantics: string in condition should be VALID
        type_env = engine.infer_types()
        assert type_env is not None


class TestEdgeCases:
    """Test edge cases for inline validation."""

    def test_any_type_bypasses_validation(self):
        """Test that operations on Any type ({}) don't produce errors."""
        code = """
dynamic = input.unknown
result = dynamic + 5
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        # input.unknown without schema = Any type
        engine = TypeInferenceEngine(
            plan, tool_resolver, input_schema=None, check_types=True
        )

        # Should not raise - Any type allows all operations
        type_env = engine.infer_types()
        assert type_env is not None

    def test_empty_program_no_errors(self):
        """Test that empty program with check_types=True works."""
        code = """
return "empty"
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        # Should not raise
        type_env = engine.infer_types()
        assert type_env is not None

    def test_with_input_schema_validates_correctly(self):
        """Test that input_schema enables proper validation.

        Field access with safe navigation returns nullable types.
        Operations on nullable types require ?? operator.
        """
        code = """
name = input.name
age = input.age
# Use ?? operator to handle nullable field access
result = (name ?? "") + str((age ?? 0))
return result
"""
        input_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
        }
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(
            plan, tool_resolver, input_schema=input_schema, check_types=True
        )

        # With ?? operator, validation succeeds
        type_env = engine.infer_types()
        assert type_env is not None


class TestUndefinedVariableDetection:
    """Test that undefined variables are caught at compile time."""

    def test_simple_undefined_variable_raises_error(self):
        """Test that a simple undefined variable raises TypeError."""
        code = """
x = undefined_variable
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_variable" in str(exc_info.value).lower()
        assert "undefined" in str(exc_info.value).lower()

    def test_undefined_variable_in_expression_raises_error(self):
        """Test that undefined variable in expression raises TypeError."""
        code = """
a = 10
b = a + missing_var
return b
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "missing_var" in str(exc_info.value).lower()

    def test_multiple_undefined_variables_all_reported(self):
        """Test that multiple undefined variables are all reported."""
        code = """
x = first_undefined
y = second_undefined
z = third_undefined
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        error_msg = str(exc_info.value).lower()
        assert "first_undefined" in error_msg
        assert "second_undefined" in error_msg
        assert "third_undefined" in error_msg

    def test_defined_variable_no_error(self):
        """Test that defined variables do not raise errors."""
        code = """
my_var = 10
result = my_var + 5
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        # Should not raise - variable is defined before use
        type_env = engine.infer_types()
        assert type_env is not None

    def test_builtin_variables_no_error(self):
        """Test that built-in variables (true, false, null) do not raise errors."""
        code = """
a = true
b = false
c = null
return a
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        # Should not raise - built-in variables are pre-defined
        type_env = engine.infer_types()
        assert type_env is not None

    def test_input_variable_no_error(self):
        """Test that input variable does not raise error when schema provided."""
        code = """
name = input.name
return name
"""
        input_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(
            plan, tool_resolver, input_schema=input_schema, check_types=True
        )

        # Should not raise - input is bootstrapped when schema provided
        type_env = engine.infer_types()
        assert type_env is not None

    def test_undefined_with_check_types_false_no_error(self):
        """Test that undefined variables are NOT caught when check_types=False."""
        code = """
x = undefined_variable
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=False)

        # Should NOT raise when check_types=False (backward compatibility)
        type_env = engine.infer_types()
        assert type_env is not None

    def test_typo_in_variable_name_caught(self):
        """Test that typos in variable names are caught (common use case)."""
        code = """
source_ip = "192.168.1.1"
result = soure_ip
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        # Should catch the typo "soure_ip" (missing 'c')
        assert "soure_ip" in str(exc_info.value).lower()


class TestUndefinedVariableCornerCases:
    """Test corner cases for undefined variable detection."""

    def test_variable_used_before_definition_same_line(self):
        """Test x = x + 1 when x is not yet defined."""
        code = """
x = x + 1
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        # The 'x' on the right side is undefined
        assert "x" in str(exc_info.value).lower()

    def test_undefined_in_list_literal(self):
        """Test undefined variable inside a list literal."""
        code = """
a = 1
b = 2
items = [a, b, undefined_c]
return items
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_c" in str(exc_info.value).lower()

    def test_undefined_in_dict_literal(self):
        """Test undefined variable inside a dict literal value."""
        code = """
known = "value"
data = {"key1": known, "key2": undefined_value}
return data
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_value" in str(exc_info.value).lower()

    def test_undefined_in_string_interpolation(self):
        """Test undefined variable in string interpolation."""
        code = """
greeting = "Hello ${undefined_name}!"
return greeting
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_name" in str(exc_info.value).lower()

    def test_undefined_as_function_argument(self):
        """Test undefined variable passed as function argument."""
        code = """
result = str(undefined_arg)
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_arg" in str(exc_info.value).lower()

    def test_field_access_on_undefined_object(self):
        """Test field access on undefined object."""
        code = """
value = undefined_obj.some_field
return value
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_obj" in str(exc_info.value).lower()

    def test_index_access_on_undefined_array(self):
        """Test index access on undefined array."""
        code = """
item = undefined_arr[0]
return item
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_arr" in str(exc_info.value).lower()

    def test_undefined_in_condition(self):
        """Test undefined variable used in if condition."""
        code = """
if (undefined_flag) {
    result = "yes"
} else {
    result = "no"
}
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_flag" in str(exc_info.value).lower()

    def test_undefined_in_unary_not(self):
        """Test undefined variable with unary not operator."""
        code = """
result = not undefined_bool
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_bool" in str(exc_info.value).lower()

    def test_undefined_in_unary_minus(self):
        """Test undefined variable with unary minus operator."""
        code = """
result = -undefined_num
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_num" in str(exc_info.value).lower()

    def test_undefined_in_comparison(self):
        """Test undefined variable in comparison operation."""
        code = """
result = undefined_x > 5
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_x" in str(exc_info.value).lower()

    def test_undefined_in_boolean_and(self):
        """Test undefined variable in boolean AND operation."""
        code = """
result = true and undefined_var
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_var" in str(exc_info.value).lower()

    def test_undefined_in_boolean_or(self):
        """Test undefined variable in boolean OR operation."""
        code = """
result = false or undefined_var
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_var" in str(exc_info.value).lower()

    def test_undefined_in_null_coalesce(self):
        """Test undefined variable in null coalesce operation."""
        code = """
result = undefined_var ?? "default"
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_var" in str(exc_info.value).lower()

    def test_chained_field_access_on_undefined(self):
        """Test chained field access where base is undefined."""
        code = """
value = undefined_obj.level1.level2.level3
return value
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_obj" in str(exc_info.value).lower()

    def test_undefined_in_while_condition(self):
        """Test undefined variable in while loop condition."""
        code = """
while (undefined_condition) {
    x = 1
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_condition" in str(exc_info.value).lower()

    def test_undefined_in_while_body(self):
        """Test undefined variable inside while loop body."""
        code = """
counter = 0
while (counter < 5) {
    x = undefined_in_loop
    counter = counter + 1
}
return counter
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_in_loop" in str(exc_info.value).lower()

    def test_multiple_undefined_in_complex_expression(self):
        """Test multiple undefined variables in a complex expression."""
        code = """
result = (undefined_a + undefined_b) * undefined_c
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        error_msg = str(exc_info.value).lower()
        # All three should be reported
        assert "undefined_a" in error_msg
        assert "undefined_b" in error_msg
        assert "undefined_c" in error_msg

    def test_undefined_mixed_with_defined(self):
        """Test expression with both defined and undefined variables."""
        code = """
known_var = 10
result = known_var + missing_var + known_var
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        error_msg = str(exc_info.value).lower()
        # Only missing_var should be reported
        assert "missing_var" in error_msg
        # known_var should NOT be reported as undefined
        assert "known_var" not in error_msg

    def test_error_includes_line_number(self):
        """Test that error message includes correct line number."""
        code = """
a = 1
b = 2
c = undefined_on_line_4
return c
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        error_msg = str(exc_info.value)
        # Should include line number 4
        assert "4" in error_msg
        assert "undefined_on_line_4" in error_msg.lower()


class TestUndefinedVariableDeepNesting:
    """Test undefined variable detection in deeply nested structures."""

    def test_deeply_nested_conditionals(self):
        """Test undefined variable in deeply nested if statements."""
        code = """
if (true) {
    if (true) {
        if (true) {
            if (true) {
                x = deeply_nested_undefined
            }
        }
    }
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "deeply_nested_undefined" in str(exc_info.value).lower()

    def test_undefined_at_different_nesting_levels(self):
        """Test multiple undefined variables at different nesting depths."""
        code = """
x = level_0_undefined
if (true) {
    y = level_1_undefined
    if (true) {
        z = level_2_undefined
    }
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        error_msg = str(exc_info.value).lower()
        assert "level_0_undefined" in error_msg
        assert "level_1_undefined" in error_msg
        assert "level_2_undefined" in error_msg

    def test_nested_loops_with_undefined(self):
        """Test undefined in nested while loops."""
        code = """
i = 0
while (i < 3) {
    j = 0
    while (j < 3) {
        x = inner_loop_undefined
        j = j + 1
    }
    i = i + 1
}
return i
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "inner_loop_undefined" in str(exc_info.value).lower()

    def test_loop_inside_conditional(self):
        """Test undefined in loop nested inside conditional."""
        code = """
flag = true
if (flag) {
    counter = 0
    while (counter < 5) {
        x = loop_in_if_undefined
        counter = counter + 1
    }
}
return flag
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "loop_in_if_undefined" in str(exc_info.value).lower()

    def test_conditional_inside_loop(self):
        """Test undefined in conditional nested inside loop."""
        code = """
counter = 0
while (counter < 5) {
    if (counter > 2) {
        x = if_in_loop_undefined
    }
    counter = counter + 1
}
return counter
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "if_in_loop_undefined" in str(exc_info.value).lower()


class TestUndefinedVariableTryCatch:
    """Test undefined variable detection in try/catch/finally blocks."""

    def test_undefined_in_try_block(self):
        """Test undefined variable in try block."""
        code = """
try {
    x = undefined_in_try
} catch (e) {
    x = "error"
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_in_try" in str(exc_info.value).lower()

    def test_undefined_in_catch_block(self):
        """Test undefined variable in catch block."""
        code = """
try {
    x = "success"
} catch (e) {
    x = undefined_in_catch
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_in_catch" in str(exc_info.value).lower()

    def test_undefined_in_finally_block(self):
        """Test undefined variable in finally block."""
        code = """
try {
    x = "success"
} catch (e) {
    x = "error"
} finally {
    cleanup = undefined_in_finally
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_in_finally" in str(exc_info.value).lower()

    def test_undefined_in_all_try_catch_blocks(self):
        """Test undefined variables in try, catch, and finally."""
        code = """
try {
    a = try_undefined
} catch (e) {
    b = catch_undefined
} finally {
    c = finally_undefined
}
return a
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        error_msg = str(exc_info.value).lower()
        assert "try_undefined" in error_msg
        assert "catch_undefined" in error_msg
        assert "finally_undefined" in error_msg

    def test_nested_try_catch(self):
        """Test undefined in nested try/catch blocks."""
        code = """
try {
    try {
        x = nested_try_undefined
    } catch (inner_e) {
        x = "inner error"
    }
} catch (outer_e) {
    x = "outer error"
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "nested_try_undefined" in str(exc_info.value).lower()

    def test_try_catch_inside_loop(self):
        """Test undefined in try/catch inside a loop."""
        code = """
counter = 0
while (counter < 3) {
    try {
        x = try_in_loop_undefined
    } catch (e) {
        x = "error"
    }
    counter = counter + 1
}
return counter
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "try_in_loop_undefined" in str(exc_info.value).lower()

    def test_loop_inside_try_catch(self):
        """Test undefined in loop inside try block."""
        code = """
try {
    counter = 0
    while (counter < 3) {
        x = loop_in_try_undefined
        counter = counter + 1
    }
} catch (e) {
    x = "error"
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "loop_in_try_undefined" in str(exc_info.value).lower()


class TestUndefinedVariableControlFlow:
    """Test undefined variable detection in various control flow scenarios."""

    def test_undefined_in_else_branch(self):
        """Test undefined variable only in else branch."""
        code = """
flag = false
if (flag) {
    x = "yes"
} else {
    x = else_branch_undefined
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "else_branch_undefined" in str(exc_info.value).lower()

    def test_undefined_in_both_branches(self):
        """Test undefined variables in both if and else branches."""
        code = """
flag = true
if (flag) {
    x = if_undefined
} else {
    x = else_undefined
}
return x
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        error_msg = str(exc_info.value).lower()
        assert "if_undefined" in error_msg
        assert "else_undefined" in error_msg

    def test_undefined_in_return_statement(self):
        """Test undefined variable directly in return."""
        code = """
x = 10
return undefined_return
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_return" in str(exc_info.value).lower()

    def test_undefined_in_return_expression(self):
        """Test undefined variable in return expression."""
        code = """
x = 10
return x + undefined_in_return_expr
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_in_return_expr" in str(exc_info.value).lower()

    def test_complex_boolean_chain_with_undefined(self):
        """Test undefined in complex boolean expression chain."""
        code = """
a = true
b = false
result = a and b or undefined_in_chain and true
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_in_chain" in str(exc_info.value).lower()

    def test_undefined_in_conditional_expression_result(self):
        """Test undefined in the result of a conditional."""
        code = """
flag = true
result = undefined_before_if
if (flag) {
    result = "updated"
}
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_before_if" in str(exc_info.value).lower()

    def test_undefined_in_multiple_sequential_blocks(self):
        """Test undefined in multiple sequential control blocks."""
        code = """
if (true) {
    a = if_block_undefined
}

counter = 0
while (counter < 1) {
    b = while_block_undefined
    counter = counter + 1
}

try {
    c = try_block_undefined
} catch (e) {
    c = "error"
}

return a
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        error_msg = str(exc_info.value).lower()
        assert "if_block_undefined" in error_msg
        assert "while_block_undefined" in error_msg
        assert "try_block_undefined" in error_msg


class TestUndefinedVariableComplexExpressions:
    """Test undefined variable detection in complex expressions."""

    def test_undefined_in_nested_field_access_chain(self):
        """Test undefined at start of long field access chain."""
        code = """
result = undefined_root.level1.level2.level3.level4
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_root" in str(exc_info.value).lower()

    def test_undefined_in_mixed_access_chain(self):
        """Test undefined in chain with field and index access."""
        code = """
result = undefined_obj["items"][0]["name"]
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_obj" in str(exc_info.value).lower()

    def test_undefined_in_nested_function_calls(self):
        """Test undefined in nested function calls."""
        code = """
result = str(len(uppercase(undefined_nested)))
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_nested" in str(exc_info.value).lower()

    def test_undefined_in_complex_arithmetic(self):
        """Test undefined in complex arithmetic expression."""
        code = """
a = 1
b = 2
c = 3
result = (a + b) * (c - undefined_arith) / 2
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_arith" in str(exc_info.value).lower()

    def test_undefined_in_dict_construction(self):
        """Test undefined in dict literal construction."""
        code = """
data = {
    "key1": "value1",
    "key2": undefined_dict_value,
    "key3": "value3"
}
return data
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_dict_value" in str(exc_info.value).lower()

    def test_undefined_in_list_construction(self):
        """Test undefined in list literal construction."""
        code = """
items = [1, 2, undefined_list_item, 4, 5]
return items
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_list_item" in str(exc_info.value).lower()

    def test_undefined_in_nested_data_structure(self):
        """Test undefined in nested dict/list construction."""
        code = """
data = {
    "outer": {
        "inner": [1, 2, {"deep": undefined_deep_nested}]
    }
}
return data
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        assert "undefined_deep_nested" in str(exc_info.value).lower()

    def test_multiple_undefined_in_single_expression(self):
        """Test multiple undefined vars in one complex expression."""
        code = """
result = undefined_a + (undefined_b * undefined_c) - undefined_d
return result
"""
        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, source_file="<test>")
        tool_resolver = ToolResolver.from_native_tools()

        engine = TypeInferenceEngine(plan, tool_resolver, check_types=True)

        with pytest.raises(TypeError) as exc_info:
            engine.infer_types()

        error_msg = str(exc_info.value).lower()
        assert "undefined_a" in error_msg
        assert "undefined_b" in error_msg
        assert "undefined_c" in error_msg
        assert "undefined_d" in error_msg
